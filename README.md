# Teison EV Charger Add-on for Home Assistant

This Home Assistant add-on lets you control a Teison EV charger via the Teison cloud API.

## Features

- Start/stop charging via MQTT or REST
- Dynamic device selection (if multiple chargers)
- MQTT auto-discovery for UI integration
- REST API for scripting and automation

## Installation

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/volski/teison-ev-addon-repo)

1. Add this repo as a custom add-on repository in Home Assistant:
   ```
   https://github.com/volski/teison-ev-addon-repo
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
mqtt_user: "mqttuser"
mqtt_pass: "mqttpass"
device_index: 0  # Index of device in your account
access_token: "" # Long-lived access tokens from hassio
pull_interval: 10 # pulling interval in seconds
```

## REST Endpoints

- `POST /start` – Start charging
- `POST /stop` – Stop charging
- `GET /status` – Get current charger status

Runs on port `5000` (via ingress).

## License

MIT
