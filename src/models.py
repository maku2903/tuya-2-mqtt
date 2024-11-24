from pydantic import BaseModel, SecretStr
from typing import Optional


class MQTTConfig(BaseModel):
    broker: str
    port: Optional[int] = 1883
    user: SecretStr
    password: Optional[SecretStr] = None


class TuyaConfig(BaseModel):
    region: str
    key: SecretStr
    secret: SecretStr


class AppConfig(BaseModel):
    period: int = 900
    topic_status_template: Optional[str] = "tele/tuya/{{ name }}/status"


class Config(BaseModel):
    mqtt: MQTTConfig
    tuya: TuyaConfig
    app: AppConfig
