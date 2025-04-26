import os
import json
import sys
import time
import requests
import threading
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request,Response, send_from_directory
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
def debug_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)
def encrypt_password(password):
    rsa_key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted = cipher.encrypt(password.encode('utf-8'))
    return b64encode(encrypted).decode('utf-8')

config_path = './data/options.json'
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    debug_print("⚠️ options.json not found, using defaults.")
    config = {}

username = config.get('username')
password = config.get('password')
mqtt_host = config.get('mqtt_host')
mqtt_port = config.get('mqtt_port')
mqtt_user = config.get('mqtt_user')
mqtt_pass = config.get('mqtt_pass')
device_index = config.get('device_index', 0)
HA_TOKEN = config.get('access_token')
pull_interval = config.get('pull_interval',10)
debug = config.get('is_debug',True)
app_option = config.get("appOption",'MyTeison')

token = None
device_id = None

def is_hassio():
    return (
        os.environ.get("SUPERVISOR_TOKEN") is not None or
        os.path.exists("/assets")
    )
def get_base_url(selected_app_option):
    if selected_app_option == "MyTeison":
        return "https://cloud.teison.com/"
    else:
        return "https://teison-m3.x-cheng.com/"


# Set the file path based on the environment (Windows vs Docker)
if is_hassio():
    # Absolute path in Docker container
    config_path = "assets/currency.json"  # Adjust this to the path inside the container
else:
    # Relative path on Windows or local development environment
    config_path = "./assets/currency.json"  # Adjust this to the path on your host machine

# Check if the file exists before opening
if os.path.exists(config_path):
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            currency_list = data.get("currencyList", [])
    except json.JSONDecodeError as e:
        debug_print(f"Error decoding JSON: {e}")
else:
    debug_print(f"File not found: {config_path}")


HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}
def post_login_teison_me(user_name, pass_word, app_option):
    payload = {'language': 'en_US',
               'username': user_name,
               'password': pass_word}
    login_res = requests.post(
        f'{get_base_url(app_option)}cpAm2/login',
        data=payload
    )
    return login_res.json()
def post_login(user_name, pass_word, local_app_option):
    encrypted_password = encrypt_password(pass_word)
    login_res = requests.post(
        f'{get_base_url(local_app_option)}api/v1/login/login',
        json={"username": user_name, "password": encrypted_password}
    )
    return login_res.json()
def get_device_list(local_token, local_app_option):
    headers = {'token': local_token}
    device_res = requests.get(
        f'{get_base_url(local_app_option)}cpAm2/cp/deviceList',
        headers=headers
    )
    return device_res.json()
def get_device_details(local_token, local_app_option, local_device_id):
    headers = {'token': local_token}
    res = requests.get(
        f'{get_base_url(local_app_option)}cpAm2/cp/deviceDetail/{local_device_id}',
        headers=headers
    )
    return res.json()
def get_cp_config(local_token,local_app_option, local_device_id):
    headers = {'token': local_token}
    res = requests.get(
        f'{get_base_url(local_app_option)}cpAm2/cp/getCpConfig/{local_device_id}',
        headers=headers
    )
    return res.json()
def set_cp_config(local_token,local_app_option, local_device_id,value):
    headers = {'token': local_token}
    payload = {
        "key": "VendorMaxWorkCurrent",
        "value": value,
    }
    res = requests.post(
        f'{get_base_url(local_app_option)}cpAm2/cp/changeCpConfig/{local_device_id}',
        json=payload,
        headers=headers
    )
    return res.json()
def get_rates(local_token,local_app_option):
    headers = {'token': local_token}
    res = requests.get(
        f'{get_base_url(local_app_option)}cpAm2/users/getRates',
        headers=headers
    )
    return res.json()
def set_rates(local_token,local_app_option,rates=None, currency=None):
    headers = {'token': local_token}
    if rates is not None and currency is not None:
        payload = {
            "rates": rates,
            "currency": currency
        }
    elif rates is not None:
        payload = {
            "rates": rates
        }
    elif currency is not None:
        payload = {
            "currency": currency
        }
    else:
        payload = {}
    res = requests.post(
        f'{get_base_url(local_app_option)}cpAm2/users/setRates',
        json=payload,
        headers=headers
    )
    return res.json()
def get_charge_record_list(local_token,local_app_option, local_device_id,from_date, to_date):
    headers = {'token': local_token}
    charge_record_list_res = requests.get(
        f'{get_base_url(local_app_option)}cpAm2/tran/chargeRecordList/{local_device_id}?from={from_date}&to={to_date}',
        headers=headers
    )
    return charge_record_list_res.json()
def start_charge(local_token, local_app_option, local_device_id):
    headers = {'token': local_token}
    r = requests.post(f'{get_base_url(local_app_option)}cpAm2/cp/startCharge/{local_device_id}', headers=headers)
    return r.json()
def stop_charge(local_token, local_app_option, local_device_id):
    headers = {'token': local_token}
    r = requests.get(f'{get_base_url(local_app_option)}cpAm2/cp/stopCharge/{local_device_id}', headers=headers)
    return r.json()
def export_excel(local_token, local_app_option, local_device_id, from_date, to_date):
    headers = {'token': local_token}
    r = requests.get(f'{get_base_url(local_app_option)}cpAm2/tran/exportExcel/{local_device_id}?from={from_date}&to={to_date}', headers=headers)
    if r.status_code == 200:
        return Response(
            r.content
        )
    else:
        return {"error": "Failed to fetch file"}, 500

def login_and_get_device():
    global token, device_id
    if(app_option == "MyTeison"):
        login_data = post_login(username, password, app_option)
        token = login_data['data']['token']
    else:
        login_data = post_login_teison_me(username, password, app_option)
        token = login_data['token']

    device_list = get_device_list(token,app_option).get('bizData', [])
    device_list = device_list['deviceList']
    if len(device_list) > device_index:
        device_id = device_list[device_index]['id']
        debug_print(f"Using device ID: {device_id}")

def post_sensor(sensor_id, state, attributes):
    try:
        url = f"{HA_BASE_URL}sensor.{sensor_id}"
        payload = {
            "state": state,
            "attributes": attributes
        }
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        debug_print(f"Updated {sensor_id}: {response.status_code} - {response.text}")
    except Exception as e:
        debug_print(f"Error updating {sensor_id}: {e}")

def mqtt_publish_status():
    while True:
        if token and device_id:
            status = get_device_details(token, app_option, device_id)
            voltage = status.get("bizData", {}).get("voltage")
            debug_print("Voltage:", voltage)
            voltage2 = status.get("bizData", {}).get("voltage2")
            debug_print("Voltage2:", voltage2)
            voltage3 = status.get("bizData", {}).get("voltage3")
            debug_print("Voltage3:", voltage3)

            current = status.get("bizData", {}).get("current")
            debug_print("Current:", current)
            current2 = status.get("bizData", {}).get("current2")
            debug_print("Current2:", current2)
            current3 = status.get("bizData", {}).get("current3")
            debug_print("Current3:", current3)

            connStatus = status.get("bizData", {}).get("connStatus")
            debug_print("connStatus:", connStatus)

            energy = status.get("bizData", {}).get("energy")
            debug_print("energy:", energy)

            temperature = status.get("bizData", {}).get("temperature")
            debug_print("temperature:", temperature)

            spendTime = status.get("bizData", {}).get("spendTime") #convert milisecond to HH:MM:ss
            debug_print("spendTime:", spendTime)
            accEnergy = status.get("bizData", {}).get("accEnergy") #energy in kWh
            debug_print("accEnergy:", accEnergy)
            power = status.get("bizData", {}).get("power")  # power in w
            debug_print("accEnergy:", power)


            getCpConfig = get_cp_config(token,app_option,device_id)
            maxCurrent = getCpConfig.get("bizData", {}).get("maxCurrent")


            getRates = get_rates(token, app_option)
            rates = getRates.get("bizData", {}).get("rates")
            currency = getRates.get("bizData", {}).get("currency")

            if connStatus == 0:
                client.publish("teison/charger/state", "stop")
            else:
                client.publish("teison/charger/state", "start")

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
    debug_print("Connected to MQTT")
    client.subscribe("teison/evcharger/command")
    debug_print("subscribe - teison/evcharger/command")
    client.subscribe("teison/charger/set")
    debug_print("subscribe - teison/charger/set")
    client.subscribe("teison/charger/current/set")
    debug_print("subscribe - teison/charger/current/set")
    client.subscribe("teison/power_rate/set")
    debug_print("subscribe - teison/power_rate/set")
    client.subscribe("teison/currency/set")
    debug_print("subscribe - teison/currency/set")

def on_message(client, userdata, msg):

    payload = msg.payload.decode()
    debug_print(f"on_message - {payload}")
    if token and device_id:
        if msg.topic == "teison/charger/current/set":
            value = int(msg.payload.decode())
            debug_print(f"New current limit: {value}A")
            set_cp_config(token, app_option, device_id, value)
        elif msg.topic == "teison/power_rate/set":
            value = float(msg.payload.decode())
            debug_print(f"New power rate: {value}kwh")
            set_rates(token, app_option, value, None)
        elif msg.topic == "teison/currency/set":
            value = msg.payload.decode()
            debug_print(f"New currency: {value}")
            set_rates(token,app_option,None,value)
        elif payload == "start":
            start_charge(token,app_option,device_id)
            client.publish("teison/charger/state", "start")
        elif payload == "stop":
            stop_charge(token,app_option,device_id)
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
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/start', methods=['POST'])
def start():
    if token and device_id:
        return start_charge(token,app_option,device_id)
    return jsonify({"error": "Not ready"}), 400

@app.route('/stop', methods=['POST'])
def stop():
    if token and device_id:
        return stop_charge(token,app_option,device_id)
    return jsonify({"error": "Not ready"}), 400

@app.route('/status', methods=['GET'])
def status():
    if token and device_id:
        return get_device_details(token,app_option,device_id)
    return jsonify({"error": "Not ready"}), 400
@app.route('/token', methods=['GET'])
def get_token():
    if token and device_id:
        json_string = f'{{"token": "{token}", "device_id": "{device_id}", "appOption": "{app_option}"}}'
        data = json.loads(json_string)
        return jsonify(data)
    return jsonify({"error": "Not ready"}), 400
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get("appOption") == "MyTeison":
        return jsonify(post_login(data.get("username"), data.get("password"),data.get("appOption")))
    else:
        return jsonify(post_login_teison_me(data.get("username"), data.get("password"), data.get("appOption")))

@app.route('/chargeRecordList',methods=['GET'])
def charge_record_list():
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    local_device_id = request.args.get('deviceId')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    return get_charge_record_list(local_token,local_app_option,local_device_id,from_date,to_date)
@app.route('/deviceList',methods=['GET'])
def device_list():
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    return get_device_list(local_token,local_app_option)
@app.route('/deviceDetail/<local_device_id>',methods=['GET'])
def device_detail(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    return get_device_details(local_token,local_app_option,local_device_id)
@app.route('/startCharge/<local_device_id>',methods=['POST'])
def post_start_charge(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    return start_charge(local_token,local_app_option,local_device_id)
@app.route('/stopCharge/<local_device_id>',methods=['GET'])
def get_stop_charge(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    return stop_charge(local_token,local_app_option,local_device_id)
@app.route('/getRates',methods=['GET'])
def flask_get_rates():
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    return get_rates(local_token,local_app_option)
@app.route('/setRates',methods=['POST'])
def flask_set_rates():
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    data = request.get_json()
    return set_rates(local_token,local_app_option,data.get("rates"),data.get("currency"))
@app.route('/getCpConfig/<local_device_id>',methods=['GET'])
def flask_get_cp_config(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    return get_cp_config(local_token,local_app_option,local_device_id)
@app.route('/changeCpConfig/<local_device_id>',methods=['POST'])
def flask_set_cp_config(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    data = request.get_json()
    return set_cp_config(local_token,local_app_option,local_device_id,data.get("value"))



@app.route('/exportExcel/<local_device_id>',methods=['GET'])
def flask_export_excel(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    return export_excel(local_token,local_app_option,local_device_id,from_date,to_date)
app.run(host='0.0.0.0', port=5000)
