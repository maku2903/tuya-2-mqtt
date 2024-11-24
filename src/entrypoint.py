from env import CONFIG_PATH
import tinytuya
import paho.mqtt.client as mqtt
import json
import time
from models import Config
import yaml
from jinja2 import Template, TemplateError, Environment, meta
from log import setup_logger


logger = setup_logger()


def load_config() -> Config:
    """Load configuration from a JSON file."""
    try:
        with open(CONFIG_PATH, "r") as file:
            config_data = yaml.safe_load(file)  # Parse the YAML file
        config = Config(**config_data)
        logger.debug("Configuration loaded successfully.")
        return config  # Validate and create the Pydantic model

    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        raise


def render_topic(template_str: str, device: dict) -> str:
    """Render the MQTT topic using a Jinja template and validate keys."""
    try:
        # Parse the template to find undeclared variables
        env = Environment()
        parsed_content = env.parse(template_str)
        required_keys = meta.find_undeclared_variables(parsed_content)
        logger.debug(f"Required keys for template: {required_keys}")

        # Check if all required keys exist in the device dictionary
        missing_keys = [key for key in required_keys if key not in device]
        if missing_keys:
            raise KeyError(f"Missing keys in device data for template: {missing_keys}")

        # Render the template with the device dictionary
        template = Template(template_str)
        return template.render(**device)

    except TemplateError as te:
        logger.error(f"Error rendering topic template: {te}", exc_info=True)
        raise
    except KeyError as ke:
        logger.error(f"Error with device keys: {ke}", exc_info=True)
        raise

def tuya_to_mqtt(config: Config):
    """Sync Tuya devices with MQTT."""
    # MQTT Configuration
    mqtt_broker = config.mqtt.broker
    mqtt_port = config.mqtt.port
    mqtt_user = config.mqtt.user.get_secret_value()
    mqtt_password = config.mqtt.password.get_secret_value() \
        if config.mqtt.password is not None else None

    # Connect to MQTT Broker
    try:
        mqtt_client = mqtt.Client()
        if mqtt_user and mqtt_password:
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
        mqtt_client.connect(mqtt_broker, mqtt_port)
    except:
        logger.error(f"Error with connecting to MQTT broker", exc_info=True)
        raise

    # Connect to Tuya Cloud
    try:
        c = tinytuya.Cloud(
            apiRegion=config.tuya.region,
            apiKey=config.tuya.key.get_secret_value(),
            apiSecret=config.tuya.secret.get_secret_value()
        )
    except:
        logger.error(f"Error with connecting to TUYA API", exc_info=True)
        raise

    # Get list of devices
    try:
        devices = c.getdevices()
    except:
        logger.error(f"Error with getting devices", exc_info=True)
        raise


    # Get Jinja template for the MQTT topic
    topic_status_template = config.app.topic_status_template

    # Iterate over devices
    for device in devices:
        # Get properties of the device
        result = c.getstatus(device['id'])
        data = {}
        for res in result["result"]:
            data[res["code"]] = res["value"]

        # Render Jinja template for the MQTT topic and publish to MQTT
        try:
            topic = render_topic(topic_status_template, device)
            logger.debug(f'Rendered MQTT topic: {topic}')
            payload = json.dumps(data)  # Convert the result dictionary to JSON string
            logger.debug(f'Data for MQTT topic {topic}: {payload}')
            mqtt_client.publish(topic, payload)
            logger.debug(f"Published to MQTT {topic} data {payload}")
        except Exception as e:
            logger.error(f"Failed to publish to MQTT: {e}", exc_info=True)
            continue

    # Disconnect from MQTT Broker
    mqtt_client.disconnect()
    logger.debug("Disconnected from MQTT")


if __name__ == "__main__":
    logger.info("Starting the application...")
    try:
        logger.info("Loading config...")
        config = load_config()
        logger.debug(f"Loaded config: {config.model_dump_json()}")
        while True:
            logger.info("Running bridge...")
            tuya_to_mqtt(config)
            logger.debug(f"Waiting for period: {config.app.period}s")
            time.sleep(config.app.period)
    except Exception as e:
        logger.error(f"Program encountered an error: {e}", exc_info=True)
