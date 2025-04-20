import os
import json
import sys
import time
import requests
import threading
# import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from base64 import b64encode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
# Config
HA_BASE_URL = "http://homeassistant.local:8123/api/states/"
HA_TOKEN = os.getenv("SUPERVISOR_TOKEN")
if not HA_TOKEN:
    sys.exit("Error: SUPERVISOR_TOKEN is not set. This must be available in Hass.io add-ons.")
HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}
# Public key for password encryption
public_key_pem = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKzH8tu+lGYMkT61r7FCdBZ/ez
lLg22grOvvuQ76NtwGPeAUklREWJqArQgd4U6RCx0vVCT6gtBOtXUK2NkSJvKjUW
BhRp6in5VJikMp1+KxyO2vgjIrKMDWzucuoeozBQ89LhhyoB2Sp3jpxKpb83/Pqu
p0gQXJmL39hJ3O+HlwIDAQAB
-----END PUBLIC KEY-----"""

def encrypt_password(password):
    rsa_key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted = cipher.encrypt(password.encode('utf-8'))
    return b64encode(encrypted).decode('utf-8')

config_path = './data/options.json'
with open(config_path) as f:
    config = json.load(f)

username = config.get('username')
password = config.get('password')
mqtt_host = config.get('mqtt_host')
mqtt_port = config.get('mqtt_port')
mqtt_user = config.get('mqtt_user')
mqtt_pass = config.get('mqtt_pass')
device_index = config.get('device_index', 0)

token = None
device_id = None

def login_and_get_device():
    global token, device_id
    encrypted_password = encrypt_password(password)
    login_res = requests.post(
        'https://cloud.teison.com/api/v1/login/login',
        json={"username": username, "password": encrypted_password}
    )
    login_data = login_res.json()
    token = login_data['data']['token']

    headers = {'token': token}
    device_res = requests.get(
        'https://cloud.teison.com/cpAm2/cp/deviceList',
        headers=headers
    )
    device_list = device_res.json().get('bizData', [])
    device_list = device_list['deviceList']
    if len(device_list) > device_index:
        device_id = device_list[device_index]['id']
        print(f"Using device ID: {device_id}")
def post_sensor(sensor_id, state, attributes):
    try:
        url = f"{HA_BASE_URL}sensor.{sensor_id}"
        payload = {
            "state": state,
            "attributes": attributes
        }
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        print(f"Updated {sensor_id}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error updating {sensor_id}: {e}")

def mqtt_publish_status():
    while True:
        if token and device_id:
            headers = {'token': token}
            res = requests.get(
                f'https://cloud.teison.com/cpAm2/cp/deviceDetail/{device_id}',
                headers=headers
            )
            status = res.json()
            voltage = status.get("bizdata", {}).get("voltage")
            print("Voltage:", voltage)
            voltage2 = status.get("bizdata", {}).get("voltage2")
            print("Voltage2:", voltage2)
            voltage3 = status.get("bizdata", {}).get("voltage3")
            print("Voltage3:", voltage3)


            # Post each sensor
            post_sensor("ev_charger_status", voltage, {
                "friendly_name": "EV Charger Status",
                "icon": "mdi:ev-station"
            })

            post_sensor("ev_charger_power", voltage2, {
                "unit_of_measurement": "kW",
                "device_class": "power",
                "friendly_name": "EV Charger Power",
                "icon": "mdi:flash"
            })

            post_sensor("ev_charger_voltage", voltage3, {
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "friendly_name": "EV Charger Voltage",
                "icon": "mdi:flash-outline"
            })

            post_sensor("ev_charger_current", voltage, {
                "unit_of_measurement": "A",
                "device_class": "current",
                "friendly_name": "EV Charger Current",
                "icon": "mdi:current-ac"
            })
            # client.publish("teison/evcharger/status", json.dumps(status))
        time.sleep(30)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    # client.subscribe("teison/evcharger/command")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if token and device_id:
        headers = {'token': token}
        if payload == "start":
            requests.post(
                f'https://cloud.teison.com/cpAm2/cp/startCharge/{device_id}',
                headers=headers
            )
        elif payload == "stop":
            requests.post(
                f'https://cloud.teison.com/cpAm2/cp/stopCharge/{device_id}',
                headers=headers
            )

login_and_get_device()

# client = mqtt.Client()
# client.username_pw_set(mqtt_user, mqtt_pass)
# client.on_connect = on_connect
# client.on_message = on_message
# client.connect(mqtt_host, mqtt_port, 60)

# threading.Thread(target=client.loop_forever, daemon=True).start()
threading.Thread(target=mqtt_publish_status, daemon=True).start()

app = Flask(__name__)

@app.route('/start', methods=['POST'])
def start():
    if token and device_id:
        headers = {'token': token}
        r = requests.post(f'https://cloud.teison.com/cpAm2/cp/startCharge/{device_id}', headers=headers)
        return jsonify(r.json())
    return jsonify({"error": "Not ready"}), 400

@app.route('/stop', methods=['POST'])
def stop():
    if token and device_id:
        headers = {'token': token}
        r = requests.post(f'https://cloud.teison.com/cpAm2/cp/stopCharge/{device_id}', headers=headers)
        return jsonify(r.json())
    return jsonify({"error": "Not ready"}), 400

@app.route('/status', methods=['GET'])
def status():
    if token and device_id:
        headers = {'token': token}
        r = requests.get(f'https://cloud.teison.com/cpAm2/cp/deviceDetail/{device_id}', headers=headers)
        return jsonify(r.json())
    return jsonify({"error": "Not ready"}), 400

app.run(host='0.0.0.0', port=5000)
