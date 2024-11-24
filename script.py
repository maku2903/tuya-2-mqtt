import tinytuya
import paho.mqtt.client as mqtt
import json
import time
import os


def load_config():
    """Load configuration from a JSON file."""
    config_path = os.getenv("CONFIG_PATH", "/app/config.json")  # Default path in Docker
    try:
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
        print("Configuration loaded successfully.")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        raise


def tuya_to_mqtt(config):
    """Sync Tuya devices with MQTT."""
    # MQTT Configuration
    mqtt_broker = config["mqtt"]["broker"]
    mqtt_port = config["mqtt"].get("port", 1883)
    mqtt_user = config["mqtt"].get("user", None)
    mqtt_password = config["mqtt"].get("password", None)

    # Connect to MQTT Broker
    client = mqtt.Client()
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
    client.connect(mqtt_broker, mqtt_port)

    # Connect to Tuya Cloud
    tuya_config = config["tuya"]
    c = tinytuya.Cloud(
        apiRegion=tuya_config["region"],
        apiKey=tuya_config["key"],
        apiSecret=tuya_config["secret"],
        apiDeviceID=tuya_config.get("device_id", "")
    )

    # Display list of devices
    devices = c.getdevices()
    print("Device List: %r" % devices)

    # Iterate over devices
    for device in devices:
        device_id = device["id"]
        device_name = device["name"]

        # Get properties of the device
        result = c.getstatus(device_id)
        print(f"Status of device {device_name}:\n", result)
        data = {}
        for res in result["result"]:
            data[res["code"]] = res["value"]
        topic = f"tele/tuya/{device_name}/status"
        print(data)
        payload = json.dumps(data)  # Convert the result dictionary to JSON string
        client.publish(topic, payload)
        print(f"Published to topic: {topic}")

    # Disconnect from MQTT Broker
    client.disconnect()


if __name__ == "__main__":
    try:
        config = load_config()
        while True:
            tuya_to_mqtt(config)
            time.sleep(900)  # 15 minutes (900 seconds)
    except Exception as e:
        print(f"Script encountered an error: {e}")
