"""Constants for Zendure SmartFlow."""

from __future__ import annotations

DOMAIN = "zendure_smartflow"
NAME = "Zendure SmartFlow"

PLATFORMS = ["sensor", "switch", "number"]

CONF_SHELLY_POWER_ENTITY = "shelly_power_entity"
CONF_ZENDURE_DEVICES = "zendure_devices"
CONF_CONTROL_PROTOCOL = "control_protocol"
CONF_MQTT_HOST = "mqtt_host"
CONF_MQTT_PORT = "mqtt_port"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_MQTT_TLS = "mqtt_tls"
CONF_TARGET_GRID_POWER = "target_grid_power"
CONF_DEADBAND = "deadband"
CONF_INTERVAL = "interval"
CONF_MAX_CHARGE_PER_DEVICE = "max_charge_per_device"
CONF_MIN_CHANGE = "min_change"
CONF_RESPONSE_FACTOR = "response_factor"
CONF_RESERVE_SOC = "reserve_soc"
CONF_ENABLED = "enabled"

DEFAULT_TARGET_GRID_POWER = 30.0
DEFAULT_DEADBAND = 40.0
DEFAULT_INTERVAL = 10
DEFAULT_MAX_CHARGE_PER_DEVICE = 800.0
DEFAULT_MIN_CHANGE = 25.0
DEFAULT_RESPONSE_FACTOR = 0.55
DEFAULT_RESERVE_SOC = 15.0
DEFAULT_ENABLED = True
DEFAULT_CONTROL_PROTOCOL = "http"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TLS = False
CONTROL_PROTOCOL_HTTP = "http"
CONTROL_PROTOCOL_MQTT = "mqtt"

SERVICE_FORCE_UPDATE = "force_update"
SERVICE_SET_ENABLED = "set_enabled"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_ENABLED = "enabled"
