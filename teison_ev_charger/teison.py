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
from requests.exceptions import RequestException, SSLError


# Public key for password encryption
public_key_pem = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKzH8tu+lGYMkT61r7FCdBZ/ez
lLg22grOvvuQ76NtwGPeAUklREWJqArQgd4U6RCx0vVCT6gtBOtXUK2NkSJvKjUW
BhRp6in5VJikMp1+KxyO2vgjIrKMDWzucuoeozBQ89LhhyoB2Sp3jpxKpb83/Pqu
p0gQXJmL39hJ3O+HlwIDAQAB
-----END PUBLIC KEY-----"""

last_sent_states = {}


def debug_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)
def encrypt_password(password):
    rsa_key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted = cipher.encrypt(password.encode('utf-8'))
    return b64encode(encrypted).decode('utf-8')


# --- Header Helper (The 403 Fix) ---
def get_teison_headers(local_token=None):
    """Returns headers mimicking a real browser to bypass 403 blocks."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://cloud.teison.com',
        'Referer': 'https://cloud.teison.com/'
    }
    if local_token:
        headers['token'] = local_token
    return headers


# --- Load Options ---
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
isOnline = False

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


# Updated for Home Assistant Add-on Environment
if is_hassio():
    HA_BASE_URL = "http://supervisor/core/api/states/"
    # The supervisor provides this token automatically to the container
    HA_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
else:
    HA_BASE_URL = "http://homeassistant.local:8123/api/states/"
    HA_TOKEN = config.get('access_token')

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}
DEFAULT_EMPTY_RATES = {"bizData": {"rates": None, "currency": None}}
def post_login_teison_me(user_name, pass_word, app_option):
    headers = get_teison_headers()
    payload = {'language': 'en_US',
               'username': user_name,
               'password': pass_word}
    login_res = requests.post(
        f'{get_base_url(app_option)}cpAm2/login',
        data=payload,
        headers=headers
    )
    return login_res.json()
def post_login(user_name, pass_word, local_app_option):
    headers = get_teison_headers()
    encrypted_password = encrypt_password(pass_word)
    login_res = requests.post(
        f'{get_base_url(local_app_option)}api/v1/login/login',
        json={"username": user_name, "password": encrypted_password},
        headers=headers
    )
    return login_res.json()
def get_device_list(local_token, local_app_option):
    headers = get_teison_headers(local_token)
    device_res = requests.get(f'{get_base_url(local_app_option)}cpAm2/cp/deviceList', headers=headers)
    return device_res.json()


def get_device_details(local_token, local_app_option, local_device_id):
    headers = get_teison_headers(local_token)
    res = requests.get(f'{get_base_url(local_app_option)}cpAm2/cp/deviceDetail/{local_device_id}', headers=headers)
    return res.json()


def get_cp_config(local_token, local_app_option, local_device_id):
    headers = get_teison_headers(local_token)
    res = requests.get(f'{get_base_url(local_app_option)}cpAm2/cp/getCpConfig/{local_device_id}', headers=headers)
    return res.json()


def set_cp_config(local_token, local_app_option, local_device_id, key, value):
    headers = get_teison_headers(local_token)
    payload = {"key": key, "value": value}
    res = requests.post(f'{get_base_url(local_app_option)}cpAm2/cp/changeCpConfig/{local_device_id}', json=payload,
                        headers=headers)
    return res.json()


def get_rates(local_token, local_app_option, retries=3, retry_delay=2):
    headers = get_teison_headers(local_token)
    url = f'{get_base_url(local_app_option)}cpAm2/users/getRates'
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            return res.json()
        except (SSLError, RequestException) as err:
            debug_print(f"Error fetching rates (attempt {attempt}/{retries}): {err}")
            if attempt < retries:
                time.sleep(retry_delay)
            else:
                debug_print("Falling back to empty rates due to repeated failures")
                return {"bizData": {"rates": None, "currency": None}}
def set_rates(local_token,local_app_option,rates=None, currency=None):
    headers = get_teison_headers(local_token)
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
    headers = get_teison_headers(local_token)
    charge_record_list_res = requests.get(
        f'{get_base_url(local_app_option)}cpAm2/tran/chargeRecordList/{local_device_id}?from={from_date}&to={to_date}',
        headers=headers
    )
    return charge_record_list_res.json()
def start_charge(local_token, local_app_option, local_device_id):
    headers = get_teison_headers(local_token)
    r = requests.post(f'{get_base_url(local_app_option)}cpAm2/cp/startCharge/{local_device_id}', headers=headers)
    return r.json()
def stop_charge(local_token, local_app_option, local_device_id):
    headers = get_teison_headers(local_token)
    r = requests.get(f'{get_base_url(local_app_option)}cpAm2/cp/stopCharge/{local_device_id}', headers=headers)
    return r.json()
def export_excel(local_token, local_app_option, local_device_id, from_date, to_date):
    headers = get_teison_headers(local_token)
    r = requests.get(f'{get_base_url(local_app_option)}cpAm2/tran/exportExcel/{local_device_id}?from={from_date}&to={to_date}', headers=headers)
    if r.status_code == 200:
        return Response(
            r.content
        )
    else:
        return {"error": "Failed to fetch file"}, 500


def login_and_get_device():
    global token, device_id
    debug_print(f"🔄 Attempting login for user: {username} via {app_option}...")

    try:
        # 1. Perform Login based on selected App Option
        if app_option == "MyTeison":
            login_data = post_login(username, password, app_option)
            # MyTeison nesting: data -> token
            if login_data.get('code') == 200 and 'data' in login_data:
                token = login_data['data'].get('token')
            else:
                debug_print(f"❌ MyTeison login failed: {login_data.get('message', 'Unknown Error')}")
                token = None
        else:
            # Teison.me / M3 nesting: direct token in root
            login_data = post_login_teison_me(username, password, app_option)
            if login_data.get('code') == 200 or 'token' in login_data:
                token = login_data.get('token')
            else:
                debug_print(f"❌ Teison.me login failed: {login_data.get('message', 'Unknown Error')}")
                token = None

        # 2. Stop if no token was retrieved
        if not token:
            debug_print("🚫 No token acquired. verify credentials or appOption.")
            return

        debug_print("✅ Login successful. Fetching device list...")

        # 3. Fetch Device List
        device_response = get_device_list(token, app_option)
        device_list_data = device_response.get('bizData', {})

        if not device_list_data or 'deviceList' not in device_list_data:
            debug_print(f"⚠️ Device list empty or failed. Response: {device_response.get('message', 'No message')}")
            # We keep the token, but we can't set a device_id yet
            device_id = None
            return

        device_list = device_list_data['deviceList']

        # 4. Select Device by Index
        if len(device_list) > device_index:
            device_id = device_list[device_index].get('id')
            debug_print(f"📱 Using Device: {device_list[device_index].get('chargePointId')} (ID: {device_id})")
        else:
            debug_print(f"❌ Device index {device_index} out of range. Found {len(device_list)} devices.")
            device_id = None

    except Exception as e:
        debug_print(f"💥 Critical error during login/device fetch: {e}")
        token = None
        device_id = None


def post_sensor(sensor_id, state, attributes, sensor_type="sensor"):
    global last_sent_states

    # 1. Convert state to string for consistent comparison and HA compatibility
    current_state = str(state)

    # 2. Check if the value has actually changed
    if last_sent_states.get(sensor_id) == current_state:
        # If the state is the same, skip the API call to avoid "API spam"
        debug_print(f"Info: state not changed {sensor_id}")
        return
    try:
        # 1. Dynamically get the token every time to ensure it's never empty
        # In HA Add-ons, the SUPERVISOR_TOKEN is the only one that works with the 'supervisor' URL
        token = os.environ.get("SUPERVISOR_TOKEN") or config.get('access_token')

        if not token:
            debug_print(f"❌ Error: No token found for {sensor_id}")
            return

        # 2. Match the URL to the token type
        if os.environ.get("SUPERVISOR_TOKEN"):
            url = f"http://supervisor/core/api/states/{sensor_type}.{sensor_id}"
        else:
            url = f"{HA_BASE_URL}{sensor_type}.{sensor_id}"

        # 3. Construct headers on-the-fly
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "state": state,
            "attributes": attributes
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code in [200, 201]: # Added 201 to successful status codes
            debug_print(f"✅ Updated {sensor_id}")
        else:
            # This will show us EXACTLY what the supervisor is complaining about
            debug_print(f"❌ {sensor_id} Error: {response.status_code} - {response.text}")

    except Exception as e:
        debug_print(f"💥 Critical Error updating {sensor_id}: {e}")


def mqtt_publish_status():
    global token, device_id, isOnline
    getCpConfig = None
    getRates = None
    slow_poll_counter = 0
    SLOW_POLL_EVERY = 12  # Refresh config/rates every 12 cycles (~2 mins at 10s interval)

    while True:
        # 1. AUTHENTICATION CHECK: Ensure we have a session before doing anything
        if not token or not device_id:
            debug_print("🔑 Authentication missing. Attempting login...")
            isOnline = False
            try:
                login_and_get_device()
                if not token:
                    debug_print("❌ Login failed. Retrying next cycle.")
                    time.sleep(30)
                    continue
            except Exception as e:
                debug_print(f"❌ Login Error: {e}")
                time.sleep(30)
                continue

        try:
            # 2. FETCH STATUS
            status = get_device_details(token, app_option, device_id)

            # 3. TOKEN VALIDATION: Check if the session is still valid
            # Teison API usually returns a 'code' or a specific message on 401/403
            if status.get("code") in [401, 403] or status.get("message") == "token invalid":
                debug_print("⚠️ Token expired or invalid. Resetting for re-login...")
                token = None
                isOnline = False
                continue

            biz_data = status.get("bizData", {})
            if not biz_data:
                debug_print("⚠️ Received empty bizData. Skipping this cycle.")
                isOnline = False
                time.sleep(pull_interval)
                continue
            
            # Extract connStatus here to use it for isOnline logic
            connStatus = biz_data.get("connStatus")

            # Update isOnline based on connStatus
            if connStatus == 7: # 7 means "Unavailable"
                isOnline = False
                debug_print("⚠️ Device is unavailable (connStatus 7). Setting isOnline to False.")
            else:
                isOnline = True # Set to True if biz_data is present and not unavailable

            # 4. DATA EXTRACTION
            voltage = biz_data.get("voltage")
            voltage2 = biz_data.get("voltage2")
            voltage3 = biz_data.get("voltage3")
            current = biz_data.get("current")
            current2 = biz_data.get("current2")
            current3 = biz_data.get("current3")
            # connStatus is already extracted above
            energy = biz_data.get("energy")
            temperature = biz_data.get("temperature")
            spendTime = biz_data.get("spendTime")
            accEnergy = biz_data.get("accEnergy")
            power = biz_data.get("power")

            # 5. SLOW POLL LOGIC (Config & Rates)
            if getCpConfig is None or slow_poll_counter >= SLOW_POLL_EVERY:
                debug_print("🔄 Refreshing CP Config and Rates...")
                getCpConfig = get_cp_config(token, app_option, device_id)
                getRates = get_rates(token, app_option)
                slow_poll_counter = 0

            slow_poll_counter += 1

            # Extract config values safely
            config_data = getCpConfig.get("bizData", {})
            maxCurrent = config_data.get("maxCurrent")
            householdCurrent = config_data.get("directlyScheduleConstraintInfo")

            rates_data = getRates.get("bizData", {})
            rates = rates_data.get("rates")
            currency = rates_data.get("currency")

            # 6. MQTT PUBLISH (Binary State)
            state_payload = "stop" if connStatus == 0 else "start"
            client.publish("teison/charger/state", state_payload, retain=True)

            # 7. HOME ASSISTANT SENSOR UPDATES
            # Standard Status
            post_sensor("ev_charger_status", get_device_status(connStatus), {
                "friendly_name": "EV Charger Status",
                "icon": "mdi:ev-station"
            })

            # Online Status
            post_sensor("ev_charger_online_status", "on" if isOnline else "off", {
                "friendly_name": "EV Charger Online Status",
                "device_class": "connectivity"
            }, sensor_type="binary_sensor")

            # Power and Energy
            post_sensor("ev_charger_power", power, {
                "unit_of_measurement": "W",
                "device_class": "power",
                "state_class": "measurement",
                "friendly_name": "EV Charger Power"
            })
            post_sensor("ev_charger_accEnergy", accEnergy, {
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
                "friendly_name": "EV Charger Total Energy"
            })

            # Environment and Time
            post_sensor("ev_charger_spendTime", ms_to_hms(spendTime), {
                "friendly_name": "EV Charger Duration",
                "icon": "mdi:timer-outline"
            })
            post_sensor("ev_charger_temperature", temperature, {
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "friendly_name": "EV Charger Temperature"
            })

            # Electrical (3-Phase Support)
            post_sensor("ev_charger_voltage", voltage,
                        {"unit_of_measurement": "V", "device_class": "voltage", "friendly_name": "L1 Voltage"})
            post_sensor("ev_charger_voltage2", voltage2,
                        {"unit_of_measurement": "V", "device_class": "voltage", "friendly_name": "L2 Voltage"})
            post_sensor("ev_charger_voltage3", voltage3,
                        {"unit_of_measurement": "V", "device_class": "voltage", "friendly_name": "L3 Voltage"})

            post_sensor("ev_charger_current", current,
                        {"unit_of_measurement": "A", "device_class": "current", "friendly_name": "L1 Current"})
            post_sensor("ev_charger_current2", current2,
                        {"unit_of_measurement": "A", "device_class": "current", "friendly_name": "L2 Current"})
            post_sensor("ev_charger_current3", current3,
                        {"unit_of_measurement": "A", "device_class": "current", "friendly_name": "L3 Current"})

            # Configuration States (to keep UI sliders in sync)
            if maxCurrent is not None:
                client.publish("teison/charger/current/state", maxCurrent, retain=True)
            if householdCurrent is not None:
                client.publish("teison/charger/householdCurrent/state", householdCurrent, retain=True)
            if rates is not None:
                client.publish("teison/power_rate/state", rates, retain=True)
            if currency is not None:
                client.publish("teison/currency/state", currency, retain=True)

        except Exception as err:
            debug_print(f"❌ Error in MQTT loop: {err}")
            isOnline = False
            # If we get a connection error, we don't clear the token, just wait

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

def on_connect(client, userdata, flags, rc, properties):
    debug_print("Connected to MQTT")
    client.subscribe("teison/evcharger/command")
    debug_print("subscribe - teison/evcharger/command")
    client.subscribe("teison/charger/set")
    debug_print("subscribe - teison/charger/set")
    client.subscribe("teison/charger/current/set")
    debug_print("subscribe - teison/charger/current/set")
    client.subscribe("teison/charger/householdCurrent/set")
    debug_print("subscribe - teison/charger/householdCurrent/set")
    client.subscribe("teison/power_rate/set")
    debug_print("subscribe - teison/power_rate/set")
    client.subscribe("teison/currency/set")
    debug_print("subscribe - teison/currency/set")

def on_message(client, userdata, msg):

    payload = msg.payload.decode()
    debug_print(f"on_message - {payload}")
    # Check for token BEFORE processing any commands
    if not token or not device_id:
        debug_print("🚫 Command received but token is missing. Ignoring.")
        return

    debug_print(f"on_message - {payload}")
    if token and device_id:
        if msg.topic == "teison/charger/current/set":
            value = int(msg.payload.decode())
            debug_print(f"New current limit: {value}A")
            result = set_cp_config(token, app_option, device_id, "VendorMaxWorkCurrent",value)
            # 1. Send to Teison Cloud
            # 2. Check if Teison accepted it (Success is usually code 200 or status 'ok')
            if result.get("code") == 200 or result.get("success"):
                debug_print(f"✅ Teison Cloud Updated: {value}A")

                # 3. FORCE Home Assistant to update the sensor IMMEDIATELY
                # We bypass the cache here because we know the value changed
                post_sensor("ev_charger_current_limit", value, {"unit_of_measurement": "A"})

                # 4. Clear the cache so the next polling loop doesn't get confused
                last_sent_states["ev_charger_current_limit"] = str(value)
            else:
                debug_print(f"⚠️ Teison rejected command: {result}")
        elif msg.topic == "teison/charger/householdCurrent/set":
            value = int(msg.payload.decode())
            debug_print(f"New household current limit: {value}A")
            result = set_cp_config(token, app_option, device_id, "DirectlyScheduleConstraintInfo", value)
            # 1. Send to Teison Cloud
            # 2. Check if Teison accepted it (Success is usually code 200 or status 'ok')
            if result.get("code") == 200 or result.get("success"):
                debug_print(f"✅ Teison Cloud Updated: {value}A")

                # 3. FORCE Home Assistant to update the sensor IMMEDIATELY
                # We bypass the cache here because we know the value changed
                post_sensor("ev_charger_household_limit", value, {"unit_of_measurement": "A"})

                # 4. Clear the cache so the next polling loop doesn't get confused
                last_sent_states["ev_charger_household_limit"] = str(value)
            else:
                debug_print(f"⚠️ Teison rejected command: {result}")
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

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.enable_logger()
client.username_pw_set(mqtt_user, mqtt_pass)
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_host, mqtt_port, 60)

# 1. Start the MQTT background networking engine
# This replaces: threading.Thread(target=client.loop_forever...).start()
client.loop_start()

# 2. Start your status polling loop in a background thread
status_thread = threading.Thread(target=mqtt_publish_status, daemon=True)
status_thread.start()

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
    "homeassistant/binary_sensor/teison_charger_online/config",
    json.dumps({
        "name": "Teison Charger Online",
        "unique_id": "teison_charger_online",
        "state_topic": "teison/charger/online/state",
        "payload_on": "on",
        "payload_off": "off",
        "device_class": "connectivity"
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
    "homeassistant/number/teison_charger_household_current/config",
    json.dumps({
        "name": "Charging Household Current",
        "unique_id": "teison_charger_household_current",
        "command_topic": "teison/charger/householdCurrent/set",
        "state_topic": "teison/charger/householdCurrent/state",
        "min": 6,
        "max": 200,
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
    return set_cp_config(local_token,local_app_option,local_device_id,data.get("key"),data.get("value"))



@app.route('/exportExcel/<local_device_id>',methods=['GET'])
def flask_export_excel(local_device_id):
    local_token = request.headers.get('token')
    local_app_option = request.headers.get('appOption')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    return export_excel(local_token,local_app_option,local_device_id,from_date,to_date)

# Move this OUTSIDE of any loops
if __name__ == "__main__":
    # Start threads...
    app.run(host='0.0.0.0', port=5000)