# Teison EV Charger Add-on for Home Assistant

This Home Assistant add-on lets you control a Teison EV charger via the Teison cloud API.

## Features

- Start/stop charging via MQTT or REST
- Dynamic device selection (if multiple chargers)
- MQTT auto-discovery for UI integration
- REST API for scripting and automation

## Installation

1. Add this repo as a custom add-on repository in Home Assistant:
   ```
   https://github.com/<your-username>/hassio-teison-addon
   ```

2. Install `Teison EV Charger` from the add-on store.
3. Configure your login credentials and MQTT settings.
4. Start the add-on.

## Configuration

Example `config`:

```yaml
username: "your_teison_user"
password: "your_teison_password"
mqtt_host: "core-mosquitto"
mqtt_port: 1883
mqtt_user: "homeassistant"
mqtt_pass: "mqtt_password"
device_index: 0  # Index of device in your account
```

## REST Endpoints

- `POST /start` – Start charging
- `POST /stop` – Stop charging
- `GET /status` – Get current charger status

Runs on port `5000` (via ingress).

## License

MIT
