# tuya-2-mqtt

`tuya-2-mqtt` is a Python-based Docker application designed to synchronize Tuya IoT devices with an MQTT broker. It bridges Tuya cloud device states to MQTT topics, allowing seamless integration with home automation systems.

## Features

- **Configuration Management**: YAML-based configuration file.
- **Dynamic Topic Rendering**: Utilizes Jinja templates for customizable MQTT topics.
- **Tuya Cloud Integration**: Fetches device statuses from the Tuya IoT Cloud.
- **MQTT Messaging**: Publishes device states to specified MQTT topics.
- **Logging**: Comprehensive logging for debugging and monitoring.
- **Docker Image**: supporting amd64, arm64, arm/v7 platforms.

---

## How It Works

1. **Load Configuration**: The application reads a YAML configuration file to set up the MQTT broker and Tuya Cloud API credentials.
2. **Connect to MQTT Broker**: Establishes a connection to the specified MQTT broker, optionally using authentication.
3. **Fetch Devices**: Retrieves a list of devices linked to the Tuya Cloud account.
4. **Publish Device States**: Converts device states to JSON and publishes them to the MQTT broker using Jinja-rendered topics.
5. **Loop Execution**: Runs the bridge at a configurable interval.

---

## Prerequisites

- A Tuya Cloud account and API credentials. ([Tutorial](https://github.com/jasonacox/tinytuya/files/12836816/Tuya.IoT.API.Setup.v2.pdf))
- An MQTT broker (e.g., Mosquitto, NanoMQ) running and accessible.
- Configuration File
- Docker or Podman installed on your system.

---
## Configuration Model

The `tuya-2-mqtt` application uses Pydantic models to validate and structure its configuration. Below are the details of the configuration model used:

#### `MQTTConfig`
Defines the MQTT broker settings:
- **`broker` (str)**: The hostname or IP address of the MQTT broker. (Required)
- **`port` (int)**: The port for the MQTT broker. Defaults to `1883`.
- **`user` (SecretStr)**: The username for MQTT authentication. (Required)
- **`password` (SecretStr)**: The password for MQTT authentication. (Optional)

#### `TuyaConfig`
Defines the Tuya IoT Cloud API settings:
- **`region` (str)**: The Tuya Cloud region (e.g., `us`, `eu`). (Required)
- **`key` (SecretStr)**: The API key from Tuya IoT Cloud. (Required)
- **`secret` (SecretStr)**: The API secret from Tuya IoT Cloud. (Required)

#### `AppConfig`
Defines application-specific settings:
- **`period` (int)**: Interval (in seconds) between successive device state synchronizations. Defaults to `900` (15 minutes).
- **`topic_status_template` (str)**: Jinja template for MQTT topics. Defaults to `"tele/tuya/{{ name }}/status"`.

#### `Config`
The root configuration model, combining all sub-models:
- **`mqtt` (MQTTConfig)**: Contains MQTT broker details.
- **`tuya` (TuyaConfig)**: Contains Tuya IoT Cloud API credentials.
- **`app` (AppConfig)**: Contains application-specific settings.

---

### Configuration File Example

Below is a YAML example that adheres to the above models:

```yaml
mqtt:
  broker: "mqtt.example.com"
  port: 1883
  user: "mqtt_user"
  password: "mqtt_password"

tuya:
  region: "eu"
  key: "your_tuya_api_key"
  secret: "your_tuya_api_secret"

app:
  period: 900
  topic_status_template: "tele/tuya/{{ name }}/status"
```

### Configuration File

The configuration file (specified by `CONFIG_PATH`) should be a YAML file containing the following sections:

- **mqtt**: Broker details, port, username, and password.
- **tuya**: API credentials and region.
- **app**:
  - `topic_status_template`: Jinja template for MQTT topics.
  - `period`: Interval in seconds for refreshing device states.

### Keys in topic template

`topic_status_template` defaults to `tele/tuya/{{ name }}/status` so it uses `name` parameter of `device`.

Usable keys in topic are:

| Parameter name 	|   Type  	|                                 Description                                 	|
|:--------------:	|:-------:	|:---------------------------------------------------------------------------:	|
| id             	| String  	| The device ID.                                                              	|
| category       	| String  	| The product category of the specified device.                               	|
| icon           	| String  	| The icon of the specified device.                                           	|
| ip             	| String  	| The IP address of the specified device.                                     	|
| lat            	| String  	| The latitude where the device is located.                                   	|
| lon            	| String  	| The longitude where the device is located.                                  	|
| name           	| String  	| The name of the specified device.                                           	|
| sub            	| Boolean 	| Indicates whether the specified device is a sub-device.                     	|
| uuid           	| String  	| The universally unique identifier (UUID) of the specified device.           	|
| activeTime     	| Long    	| The timestamp when the device was activated. Unit: seconds.                 	|
| createTime     	| Long    	| The timestamp when the device was paired for the first time. Unit: seconds. 	|
| updateTime     	| Long    	| The timestamp when the device was updated. Unit: seconds.                   	|
| customName     	| String  	| The custom name of the specified device.                                    	|
| isOnline       	| Boolean 	| Indicates whether the specified device is online.                           	|
| localKey       	| String  	| The unique encrypted key of the specified device over LAN.                  	|
| productId      	| String  	| The product ID of the specified device.                                     	|
| productName    	| String  	| The product name of the specified device.                                   	|
| timeZone       	| String  	| The time zone in which the specified device is located.                     	|

---

### Environment Variables

The `tuya-2-mqtt` application uses environment variables to configure file paths and logging behavior. Below are the details of the environment variables:

#### Available Variables

- **`LOG_LEVEL`**: Sets the log level for the application. Acceptable values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Defaults to `INFO`.
- **`LOG_FILE_PATH`**: Specifies the file path for the application logs. Defaults to `/app/logs/app.log` when running in Docker.
- **`CONFIG_PATH`**: Specifies the file path for the YAML configuration file. Defaults to `/app/config.yaml` when running in Docker.

#### Example `.env` File

You can create a `.env` file to set the environment variables as You wish, example:

```env
LOG_LEVEL=DEBUG
LOG_FILE_PATH=/var/log/tuya-2-mqtt.log
CONFIG_PATH=/etc/tuya-2-mqtt/config.yaml
```
or keep them default.

---

## Deploying with Docker Compose

To simplify the deployment of `tuya-2-mqtt` alongside a NanoMQ MQTT broker, you can use the following `docker-compose.yml` configuration. This setup ensures that both services are running in a coordinated manner and persist across restarts.

#### `docker-compose.yml`:

```yaml
version: '3'

services:
  nanomq:
    image: emqx/nanomq:latest
    hostname: nanomq
    ports:
      - "1883:1883"
      - "8883:8883"
    restart: unless-stopped

  tuya-2-mqtt:
    image: makuuu2903/tuya-2-mqtt:latest
    volumes:
      - ${PWD}/tuya2mqtt.yaml:/app/config.yaml:ro
      - ${PWD}/logs:/app/logs
    environment:
      LOG_LEVEL: DEBUG
      LOG_FILE_PATH: /app/logs/app.log
      CONFIG_PATH: /app/config.yaml
    depends_on:
      - nanomq
    restart: unless-stopped
```
#### `tuya2mqtt.yaml`:
```yaml
mqtt:
  broker: "nanomq"
  port: 1883
  user: "tuya"
  password: null
  topic_status_template: "tele/tuya/{{ name }}/status"

tuya:
  region: "your_tuya_region"
  key: "your_tuya_api_key"
  secret: "your_tuya_api_secret"
  device_id: "optional_device_id"

app:
  period: 450
```
---

## Key Functions

### `load_config()`
Loads and validates the YAML configuration file.

### `render_topic(template_str: str, device: dict) -> str`
Renders MQTT topics using Jinja templates and validates device keys.

### `tuya_to_mqtt(config: Config)`
Main function that:
- Connects to the MQTT broker and Tuya Cloud.
- Retrieves device states and publishes them to MQTT topics.

---

## License

This project is licensed under the MIT License.

