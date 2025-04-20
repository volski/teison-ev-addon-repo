import os
import json
import sys
import time
import requests
import threading
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from base64 import b64encode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
# Config
HA_BASE_URL = "http://homeassistant.local:8123/api/states/"


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
HA_TOKEN = config.get('access_token')

token = None
device_id = None

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

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
            voltage = status.get("bizData", {}).get("voltage")
            print("Voltage:", voltage)
            voltage2 = status.get("bizData", {}).get("voltage2")
            print("Voltage2:", voltage2)
            voltage3 = status.get("bizData", {}).get("voltage3")
            print("Voltage3:", voltage3)

            current = status.get("bizData", {}).get("current")
            print("Current:", current)
            current2 = status.get("bizData", {}).get("current2")
            print("Current2:", current2)
            current3 = status.get("bizData", {}).get("current3")
            print("Current3:", current3)

            connStatus = status.get("bizData", {}).get("connStatus")
            print("connStatus:", connStatus)

            energy = status.get("bizData", {}).get("energy")
            print("energy:", energy)

            temperature = status.get("bizData", {}).get("temperature")
            print("temperature:", temperature)


            # Post each sensor
            post_sensor("ev_charger_status", get_device_status(connStatus), {
                "friendly_name": "EV Charger Status",
                "icon": "mdi:ev-station"
            })

            post_sensor("ev_charger_power", energy, {
                "unit_of_measurement": "kW",
                "device_class": "power",
                "friendly_name": "EV Charger Power",
                "icon": "mdi:flash"
            })

            post_sensor("ev_charger_temperature", temperature, {
                "unit_of_measurement": "C",
                "device_class": "power",
                "friendly_name": "EV Charger Temperature",
                "icon": "mdi:temperature-celsius"
            })

            post_sensor("ev_charger_voltage", voltage, {
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "friendly_name": "EV Charger Voltage",
                "icon": "mdi:flash-outline"
            })
            post_sensor("ev_charger_voltage2", voltage2, {
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "friendly_name": "EV Charger Voltage2",
                "icon": "mdi:flash-outline"
            })
            post_sensor("ev_charger_voltage3", voltage3, {
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "friendly_name": "EV Charger Voltage3",
                "icon": "mdi:flash-outline"
            })

            post_sensor("ev_charger_current", current, {
                "unit_of_measurement": "A",
                "device_class": "current",
                "friendly_name": "EV Charger Current",
                "icon": "mdi:current-ac"
            })
            post_sensor("ev_charger_current2", current2, {
                "unit_of_measurement": "A",
                "device_class": "current",
                "friendly_name": "EV Charger Current2",
                "icon": "mdi:current-ac"
            })
            post_sensor("ev_charger_current3", current3, {
                "unit_of_measurement": "A",
                "device_class": "current",
                "friendly_name": "EV Charger Current3",
                "icon": "mdi:current-ac"
            })
            # client.publish("teison/evcharger/status", json.dumps(status))
        time.sleep(10)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe("teison/evcharger/command")
    print("subscribe - teison/evcharger/command")
    client.subscribe("teison/charger/set")
    print("subscribe - teison/charger/set")

def on_message(client, userdata, msg):

    payload = msg.payload.decode()
    print(f"on_message - {payload}")
    if token and device_id:
        headers = {'token': token}
        if payload == "start":
            requests.post(
                f'https://cloud.teison.com/cpAm2/cp/startCharge/{device_id}',
                headers=headers
            )
            client.publish("teison/charger/state", "start")
        elif payload == "stop":
            requests.get(
                f'https://cloud.teison.com/cpAm2/cp/stopCharge/{device_id}',
                headers=headers
            )
            client.publish("teison/charger/state", "stop")
def get_device_status(status: int) -> str:
    if status == 88:
        return "Faulted"

    status_map = {
        0: "Available",
        1: "Preparing",
        2: "Charging",
        3: "SuspendedEVSE",
        4: "SuspendedEV",
        5: "Finished",
        6: "Reserved",
        7: "Unavailable",
        8: "Faulted",
    }

    return status_map.get(status, "")

login_and_get_device()

client = mqtt.Client(protocol=mqtt.MQTTv311)
client.enable_logger()
client.username_pw_set(mqtt_user, mqtt_pass)
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_host, mqtt_port, 60)

threading.Thread(target=client.loop_forever, daemon=True).start()
threading.Thread(target=mqtt_publish_status, daemon=True).start()

# Publish discovery config
client.publish(
    "homeassistant/switch/teison_charger/config",
    json.dumps({
        "name": "Teison Charger",
        "unique_id": "teison_charger_switch",
        "command_topic": "teison/charger/set",
        "state_topic": "teison/charger/state",
        "payload_on": "start",
        "payload_off": "stop"
    }),
    retain=True
)

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
