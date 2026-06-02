"""Config flow for Zendure SmartFlow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CONTROL_PROTOCOL,
    CONF_DEADBAND,
    CONF_ENABLED,
    CONF_INTERVAL,
    CONF_MAX_CHARGE_PER_DEVICE,
    CONF_MIN_CHANGE,
    CONF_RESERVE_SOC,
    CONF_RESPONSE_FACTOR,
    CONF_SHELLY_POWER_ENTITY,
    CONF_TARGET_GRID_POWER,
    CONF_ZENDURE_DEVICES,
    CONTROL_PROTOCOL_HTTP,
    CONTROL_PROTOCOL_MQTT,
    DEFAULT_CONTROL_PROTOCOL,
    DEFAULT_DEADBAND,
    DEFAULT_ENABLED,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_CHARGE_PER_DEVICE,
    DEFAULT_MIN_CHANGE,
    DEFAULT_RESERVE_SOC,
    DEFAULT_RESPONSE_FACTOR,
    DEFAULT_TARGET_GRID_POWER,
    DOMAIN,
    NAME,
)


def _device_list(value: str | None, protocol: str) -> list[dict[str, str]]:
    """Normalize device lines for HTTP or MQTT control."""
    if not value:
        return []

    devices: list[dict[str, str]] = []
    for line in value.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        parts = [item.strip() for item in cleaned.split(",")]
        if protocol == CONTROL_PROTOCOL_MQTT:
            if len(parts) != 4 or not all(parts):
                return []
            devices.append(
                {
                    "host": parts[0],
                    "sn": parts[1],
                    "product_key": parts[2],
                    "device_id": parts[3],
                }
            )
            continue

        if len(parts) not in {2, 4} or not parts[0] or not parts[1]:
            return []
        device = {"host": parts[0], "sn": parts[1]}
        if len(parts) == 4 and parts[2] and parts[3]:
            device["product_key"] = parts[2]
            device["device_id"] = parts[3]
        devices.append(device)
    return devices


def _device_text(devices: list[dict[str, str]] | None) -> str:
    """Format configured devices for display in the options flow."""
    lines: list[str] = []
    for item in devices or []:
        if item.get("product_key") and item.get("device_id"):
            lines.append(
                f"{item['host']},{item['sn']},{item['product_key']},{item['device_id']}"
            )
        else:
            lines.append(f"{item['host']},{item['sn']}")
    return "\n".join(lines)


class SmartFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zendure SmartFlow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            protocol = user_input[CONF_CONTROL_PROTOCOL]
            devices = _device_list(user_input[CONF_ZENDURE_DEVICES], protocol)

            if len(devices) != 3:
                errors[CONF_ZENDURE_DEVICES] = "need_three_devices"
            else:
                await self.async_set_unique_id("zendure_smartflow")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=NAME,
                    data={
                        **user_input,
                        CONF_ZENDURE_DEVICES: devices,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONTROL_PROTOCOL, default=DEFAULT_CONTROL_PROTOCOL
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": CONTROL_PROTOCOL_HTTP, "label": "HTTP"},
                                {"value": CONTROL_PROTOCOL_MQTT, "label": "MQTT"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_SHELLY_POWER_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_ZENDURE_DEVICES): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                    vol.Optional(
                        CONF_TARGET_GRID_POWER, default=DEFAULT_TARGET_GRID_POWER
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=-500,
                            max=500,
                            step=5,
                            unit_of_measurement="W",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_DEADBAND, default=DEFAULT_DEADBAND
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=500,
                            step=5,
                            unit_of_measurement="W",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_INTERVAL, default=DEFAULT_INTERVAL
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=2,
                            max=120,
                            step=1,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_MAX_CHARGE_PER_DEVICE,
                        default=DEFAULT_MAX_CHARGE_PER_DEVICE,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=2400,
                            step=10,
                            unit_of_measurement="W",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_MIN_CHANGE, default=DEFAULT_MIN_CHANGE
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=500,
                            step=5,
                            unit_of_measurement="W",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_RESPONSE_FACTOR, default=DEFAULT_RESPONSE_FACTOR
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.05,
                            max=2.0,
                            step=0.05,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_RESERVE_SOC, default=DEFAULT_RESERVE_SOC
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=100,
                            step=1,
                            unit_of_measurement="%",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(CONF_ENABLED, default=DEFAULT_ENABLED): bool,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SmartFlowOptionsFlow(config_entry)


class SmartFlowOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Zendure SmartFlow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            protocol = user_input[CONF_CONTROL_PROTOCOL]
            devices = _device_list(user_input.pop(CONF_ZENDURE_DEVICES, ""), protocol)
            if len(devices) != 3:
                errors[CONF_ZENDURE_DEVICES] = "need_three_devices"
            else:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, CONF_ZENDURE_DEVICES: devices},
                )
                return self.async_create_entry(title="", data=user_input)

        options = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONTROL_PROTOCOL,
                        default=options.get(
                            CONF_CONTROL_PROTOCOL, DEFAULT_CONTROL_PROTOCOL
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": CONTROL_PROTOCOL_HTTP, "label": "HTTP"},
                                {"value": CONTROL_PROTOCOL_MQTT, "label": "MQTT"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_ZENDURE_DEVICES,
                        default=_device_text(self.config_entry.data[CONF_ZENDURE_DEVICES]),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                    vol.Optional(
                        CONF_TARGET_GRID_POWER,
                        default=options.get(
                            CONF_TARGET_GRID_POWER, DEFAULT_TARGET_GRID_POWER
                        ),
                    ): float,
                    vol.Optional(
                        CONF_DEADBAND,
                        default=options.get(CONF_DEADBAND, DEFAULT_DEADBAND),
                    ): float,
                    vol.Optional(
                        CONF_INTERVAL,
                        default=options.get(CONF_INTERVAL, DEFAULT_INTERVAL),
                    ): int,
                    vol.Optional(
                        CONF_MAX_CHARGE_PER_DEVICE,
                        default=options.get(
                            CONF_MAX_CHARGE_PER_DEVICE, DEFAULT_MAX_CHARGE_PER_DEVICE
                        ),
                    ): float,
                    vol.Optional(
                        CONF_MIN_CHANGE,
                        default=options.get(CONF_MIN_CHANGE, DEFAULT_MIN_CHANGE),
                    ): float,
                    vol.Optional(
                        CONF_RESPONSE_FACTOR,
                        default=options.get(
                            CONF_RESPONSE_FACTOR, DEFAULT_RESPONSE_FACTOR
                        ),
                    ): float,
                    vol.Optional(
                        CONF_RESERVE_SOC,
                        default=options.get(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC),
                    ): float,
                    vol.Optional(
                        CONF_ENABLED,
                        default=options.get(CONF_ENABLED, DEFAULT_ENABLED),
                    ): bool,
                }
            ),
            errors=errors,
        )
