# Tuya to MQTT Bridge

This project bridges Tuya smart devices to an MQTT broker, enabling real-time monitoring and control of Tuya devices via MQTT. The bridge fetches device statuses from Tuya Cloud and publishes them as JSON payloads to configured MQTT topics.

---

## Features

- Fetches device statuses from Tuya Cloud using `tinytuya`.
- Publishes data to an MQTT broker with `paho-mqtt`.
- Configurable via a `config.json` file.
- Designed to run in a Docker container for easy deployment.

---

## Prerequisites

- A Tuya Cloud account and API credentials.
- An MQTT broker (e.g., Mosquitto) running and accessible.
- Docker or Podman installed on your system.

---

## Configuration

Create a `config.json` file with the following structure:

```json
{
    "mqtt": {
        "broker": "192.168.1.250",
        "port": 1883,
        "user": "tuya",
        "password": null
    },
    "tuya": {
        "region": "us",
        "key": "your-tuya-api-key",
        "secret": "your-tuya-api-secret",
        "device_id": "your-device-id"
    }
}
```

## Docker run
