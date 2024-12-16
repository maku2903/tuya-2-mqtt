from env import CONFIG_PATH
import tinytuya
import paho.mqtt.client as mqtt
import json
import time
from models import Config
import yaml
from jinja2 import Template, TemplateError, Environment, meta
from log import setup_logger
import threading
import queue
import signal

logger = setup_logger()

# Queue of mqtt messages
mqtt_in_queue = queue.Queue()

event_thread_stop = threading.Event()


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


def render_mqtt_topic(template_str: str, device: dict) -> str:
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

def thread_mqtt_listener(config: Config, mqtt_in_queue: queue.Queue):
    """Thread: Listens for MQTT messages on specific topics and adds them to the queue."""

    def on_message(client, userdata, msg):
        """Callback of MQTT Client to check topic and put valid message into 'mqtt_in_queue' thread queue."""
        try:
            # Check if the topic matches the desired format: tele/tuya/cloud/<device_id>/command
            topic_parts = msg.topic.split("/")
            if len(topic_parts) == 5 and topic_parts[0] == "tele" and topic_parts[1] == "tuya" \
                    and topic_parts[2] == "cloud" and topic_parts[4] == "command":
                # Extract device_id and process the message
                device_id = topic_parts[3]
                payload = json.loads(msg.payload.decode())
                mqtt_in_queue.put({"topic": msg.topic, "device_id": device_id, "payload": payload})
                logger.info(f"MQTT message received: {msg.topic} -> {payload}")
            else:
                logger.debug(f"Ignored message with topic: {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    mqtt_client = mqtt.Client()
    try:
        mqtt_client.on_message = on_message
        if config.mqtt.user and config.mqtt.password:
            mqtt_client.username_pw_set(config.mqtt.user.get_secret_value(),
                                        config.mqtt.password.get_secret_value())

        # Connect to the MQTT broker
        mqtt_client.connect(config.mqtt.broker, config.mqtt.port)

        # Subscribe to the specific topic pattern
        topic_pattern = "tele/tuya/cloud/+/command"  # "+" wildcard for <device_id>
        mqtt_client.subscribe(topic_pattern)
        logger.info(f"Subscribed to topic pattern: {topic_pattern}")

        # Start MQTT processing loop in a non-blocking way
        mqtt_client.loop_start()
        logger.info("MQTT listener thread started.")

        # Wait until `event_thread_stop` is set
        while not event_thread_stop.is_set():
            time.sleep(1)  # Sleep to avoid tight loop

    except Exception as e:
        logger.error(f"Error in MQTT listener thread: {e}", exc_info=True)
    finally:
        # Perform cleanup if the thread needs to terminate
        try:
            mqtt_client.loop_stop()  # Stop the MQTT loop
            mqtt_client.disconnect()  # Disconnect from MQTT broker
            logger.info("MQTT listener thread stopped and disconnected.")
        except Exception as cleanup_error:
            logger.error(f"Error during MQTT cleanup: {cleanup_error}", exc_info=True)


def thread_mqtt_to_tuya_cloud(config: Config, mqtt_in_queue: queue.Queue):
    """Thread: Processes messages from queue and sends them to Tuya Cloud."""
    try:
        tuya_client = tinytuya.Cloud(
            apiRegion=config.tuya.region,
            apiKey=config.tuya.key.get_secret_value(),
            apiSecret=config.tuya.secret.get_secret_value(),
        )
    except Exception as e:
        logger.error(f"Error connecting to Tuya Cloud: {e}", exc_info=True)
        return

    while not event_thread_stop.is_set():
        try:
            mqtt_msg = mqtt_in_queue.get()  # Get message from queue
            mqtt_in_queue.task_done()  # Release message
            logger.debug(f"Processing MQTT message: {mqtt_msg}")

            # Tuya API - sending
            device_id = mqtt_msg["device_id"]  # todo: Handle not existent device_id?
            payload = mqtt_msg["payload"]
            logger.debug(f"Sending command to Tuya: {device_id} -> {payload}")
            response = tuya_client.sendcommand(deviceid=device_id, commands=payload)
            logger.debug(f"Command sent to Tuya: {device_id} -> {payload}, response: {response}")
            # todo: Somehow handle the response
        except queue.Empty:
            time.sleep(1)  # Sleep to avoid tight loop
            pass  # No message in queue, continue
        except Exception as e:
            logger.error(f"Error processing MQTT to Tuya message: {e}", exc_info=True)


def thread_tuya_cloud_to_mqtt(config: Config):
    """Thread: Periodically sync Tuya devices with MQTT, checking for stop event."""

    # Connect to MQTT Broker
    try:
        mqtt_client = mqtt.Client()
        mqtt_user = config.mqtt.user.get_secret_value()
        mqtt_password = config.mqtt.password.get_secret_value() if config.mqtt.password is not None else None
        if mqtt_user and mqtt_password:
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
        mqtt_client.connect(config.mqtt.broker, config.mqtt.port)
    except Exception as mqtt_error:
        logger.error(f"Error connecting to MQTT broker: {mqtt_error}", exc_info=True)
        event_thread_stop.set()
        return  # Exit thread if unable to connect

    # Connect to Tuya Cloud
    try:
        tuya_client = tinytuya.Cloud(
            apiRegion=config.tuya.region,
            apiKey=config.tuya.key.get_secret_value(),
            apiSecret=config.tuya.secret.get_secret_value()
        )
    except Exception as tuya_error:
        logger.error(f"Error connecting to Tuya Cloud: {tuya_error}", exc_info=True)
        return  # Exit thread if unable to connect

    try:
        # Periodic execution loop
        while not event_thread_stop.is_set():
            try:
                # Get the list of devices from Tuya Cloud
                devices = tuya_client.getdevices()
            except Exception as device_error:
                logger.error(f"Error fetching devices from Tuya Cloud: {device_error}", exc_info=True)
                time.sleep(config.app.period)  # Sleep before retrying
                continue

            # Synchronize each device's status
            for device in devices:
                try:
                    # Fetch device status
                    result = tuya_client.getstatus(device['id'])
                    data = {res["code"]: res["value"] for res in result["result"]}

                    # Render MQTT topic using Jinja template
                    topic_status_template = config.app.topic_status_template
                    topic = render_mqtt_topic(topic_status_template, device)
                    payload = json.dumps(data)

                    # Publish device status to MQTT
                    mqtt_client.publish(topic, payload)
                    logger.debug(f"Published to MQTT: {topic}, data: {payload}")
                except Exception as device_sync_error:
                    logger.error(f"Error syncing device {device['id']} to MQTT: {device_sync_error}", exc_info=True)
                    continue

            # Clean up MQTT connection on exit
            try:
                mqtt_client.disconnect()
                logger.info("Disconnected from MQTT broker.")
            except Exception as cleanup_error:
                logger.error(f"Error during MQTT disconnect: {cleanup_error}", exc_info=True)

            # Wait for the next period or stop event
            logger.debug(f"Waiting {config.app.period} seconds before the next sync...")
            for _ in range(int(config.app.period * 10)):  # 0.1s resolution sleep
                if event_thread_stop.is_set():
                    break
                time.sleep(0.1)

    except Exception as thread_error:
        logger.error(f"Unexpected error in Tuya-to-MQTT thread: {thread_error}", exc_info=True)
    finally:

        logger.info("Tuya-to-MQTT thread stopped.")


def cleanup_threads(threads):
    """Stop all threads gracefully."""
    logger.info("Stopping all threads...")
    # Trigger stop event for all threads
    event_thread_stop.set()

    # Wait for each thread to terminate
    for t in threads:
        logger.info(f"Waiting for thread {t.name} to finish...")
        t.join()
    logger.info("All threads terminated.")

def signal_handler(signal_received, frame):
    """Signal handling for Docker containers and proper cleanup"""
    logger.info(f"Signal {signal_received} received. Shutting down application...")
    cleanup_threads(threads)
    exit(0)

if __name__ == "__main__":
    logger.info("Starting application...")
    threads: list[threading.Thread] = []

    # Register signal handler (e.g., for SIGINT/SIGTERM in Docker)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        config = load_config()
        # Threads start
        t = threading.Thread(
            target=thread_mqtt_listener,
            args=(config, mqtt_in_queue), daemon=True,
            name="Thread_MQTT_Listener"
        )
        threads.append(t)
        t.start()

        t = threading.Thread(
            target=thread_mqtt_to_tuya_cloud,
            args=(config, mqtt_in_queue), daemon=True,
            name="Thread_MQTT_to_Tuya_Cloud"
        )
        threads.append(t)
        t.start()

        t = threading.Thread(
            target=thread_tuya_cloud_to_mqtt, args=(config,), daemon=True,
            name="Thread_Tuya_Cloud_to_MQTT"
        )
        threads.append(t)
        t.start()

        # Keep main thread alive
        while not event_thread_stop.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Program manually terminated by user.")
        event_thread_stop.set()

    except ConnectionError as ce:
        logger.error("Connection error occurred. Likely network misconfiguration.")
        logger.error(f"Details: {ce}", exc_info=True)
        event_thread_stop.set()

    except TimeoutError as te:
        logger.error("Timeout error occurred. Possible connectivity or latency issue.")
        logger.error(f"Details: {te}", exc_info=True)
        event_thread_stop.set()

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        event_thread_stop.set()

    finally:
        # Cleanup threads before exiting
        cleanup_threads(threads)
        logger.info("Application terminated.")
