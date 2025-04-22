import os
import json
import sys
import time
import requests
import threading
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
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
pull_interval = config.get('pull_interval',10)

token = None
device_id = None

def is_hassio():
    return (
        os.environ.get("SUPERVISOR_TOKEN") is not None or
        os.path.exists("/data") and os.path.exists("/config")
    )


# Set the file path based on the environment (Windows vs Docker)
if is_hassio():
    # Absolute path in Docker container
    config_path = "/data/currency.json"  # Adjust this to the path inside the container
else:
    # Relative path on Windows or local development environment
    config_path = "/data/currency.json"  # Adjust this to the path on your host machine

# Check if the file exists before opening
if os.path.exists(config_path):
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            currency_list = data.get("currencyList", [])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
else:
    print(f"File not found: {config_path}")


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

            spendTime = status.get("bizData", {}).get("spendTime") #convert milisecond to HH:MM:ss
            print("spendTime:", spendTime)
            accEnergy = status.get("bizData", {}).get("accEnergy") #energy in kWh
            print("accEnergy:", accEnergy)
            power = status.get("bizData", {}).get("power")  # power in w
            print("accEnergy:", power)

            res2 = requests.get(
                f'https://cloud.teison.com/cpAm2/cp/getCpConfig/{device_id}',
                headers=headers
            )
            getCpConfig = res2.json()
            maxCurrent = getCpConfig.get("bizData", {}).get("maxCurrent")

            res3 = requests.get(
                f'https://cloud.teison.com/cpAm2/users/getRates',
                headers=headers
            )
            getRates = res3.json()
            rates = getRates.get("bizData", {}).get("rates")
            currency = getRates.get("bizData", {}).get("currency")


            # Post each sensor
            post_sensor("ev_charger_status", get_device_status(connStatus), {
                "friendly_name": "EV Charger Status",
                "icon": "mdi:ev-station"
            })

            post_sensor("ev_charger_power", power, {
                "unit_of_measurement": "w",
                "device_class": "power",
                "friendly_name": "EV Charger Power",
                "icon": "mdi:flash"
            })
            post_sensor("ev_charger_accEnergy", accEnergy, {
                "unit_of_measurement": "kWh",
                "device_class": "power",
                "friendly_name": "EV Charger Energy",
                "icon": "mdi:flash"
            })

            post_sensor("ev_charger_spendTime", ms_to_hms(spendTime), {
                "unit_of_measurement": "",
                "device_class": "power",
                "friendly_name": "EV Charger Duration",
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
            client.publish("teison/charger/current/state", maxCurrent, retain=True)
            client.publish("teison/power_rate/state", rates, retain=True)
            client.publish("teison/currency/state", currency, retain=True)
            # client.publish("teison/evcharger/status", json.dumps(status))
        time.sleep(pull_interval)
def ms_to_hms(ms_string):
    if ms_string is not None:
        milliseconds = int(ms_string)
    else:
        milliseconds = 0
    seconds = milliseconds // 1000
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe("teison/evcharger/command")
    print("subscribe - teison/evcharger/command")
    client.subscribe("teison/charger/set")
    print("subscribe - teison/charger/set")
    client.subscribe("teison/charger/current/set")
    print("subscribe - teison/charger/current/set")
    client.subscribe("teison/power_rate/set")
    print("subscribe - teison/power_rate/set")
    client.subscribe("teison/currency/set")
    print("subscribe - teison/currency/set")

def on_message(client, userdata, msg):

    payload = msg.payload.decode()
    print(f"on_message - {payload}")
    if token and device_id:
        headers = {'token': token}
        if msg.topic == "teison/charger/current/set":
            value = int(msg.payload.decode())
            print(f"New current limit: {value}A")
            payload = {
                "key": "VendorMaxWorkCurrent",
                "value": value,
            }
            requests.post(
                f'https://cloud.teison.com/cpAm2/cp/changeCpConfig/{device_id}',
                json=payload,
                headers=headers
            )
        elif msg.topic == "teison/power_rate/set":
            value = float(msg.payload.decode())
            print(f"New power rate: {value}kwh")
            payload = {
                "rates": value,
            }
            requests.post(
                f'https://cloud.teison.com/cpAm2/users/setRates',
                json=payload,
                headers=headers
            )
        elif msg.topic == "teison/currency/set":
            value = msg.payload.decode()
            print(f"New currency: {value}")
            payload = {
                "currency": value,
            }
            requests.post(
                f'https://cloud.teison.com/cpAm2/users/setRates',
                json=payload,
                headers=headers
            )
        elif payload == "start":
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
client.publish(
    "homeassistant/number/teison_charger_current/config",
    json.dumps({
        "name": "Charging Max Current",
        "unique_id": "teison_charger_max_current",
        "command_topic": "teison/charger/current/set",
        "state_topic": "teison/charger/current/state",
        "min": 6,
        "max": 32,
        "step": 1,
        "unit_of_measurement": "A",
        "mode": "slider",
        "retain": True
    }),
    retain=True
)

client.publish(
    "homeassistant/select/teison_currency/config",
    json.dumps({
        "name": "Teison Currency",
        "unique_id": "teison_currency_selector",
        "command_topic": "teison/currency/set",
        "state_topic": "teison/currency/state",
        "options": currency_list,
        "retain": True
    }),
    retain=True
)
client.publish(
    "homeassistant/number/teison_power_limit/config",
    json.dumps({
        "name": "Teison Power Rate",
        "unique_id": "teison_power_rate",
        "command_topic": "teison/power_rate/set",
        "state_topic": "teison/power_rate/state",
        "min": 0.0,
        "max": 9999999.0,
        "step": 0.01,
        "unit_of_measurement": "kwh",
        "mode": "box",
        "retain": True
    }),
    retain=True
)

app = Flask(__name__, static_folder='frontend')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

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
@app.route('/token', methods=['GET'])
def get_token():
    if token and device_id:
        json_string = f'{{"token": "{token}", "device_id": {device_id}}}'
        data = json.loads(json_string)
        return jsonify(data)
    return jsonify({"error": "Not ready"}), 400
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    encrypted_password = encrypt_password(data.get("password"))
    login_res = requests.post(
        'https://cloud.teison.com/api/v1/login/login',
        json={"username": data.get("username"), "password": encrypted_password}
    )
    return jsonify(login_res.json())

app.run(host='0.0.0.0', port=5000)
