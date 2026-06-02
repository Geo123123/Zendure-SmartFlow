"""Config flow for Zendure SmartFlow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DEADBAND,
    CONF_ENABLED,
    CONF_INTERVAL,
    CONF_MAX_CHARGE_PER_DEVICE,
    CONF_MIN_CHANGE,
    CONF_RESERVE_SOC,
    CONF_RESPONSE_FACTOR,
    CONF_SHELLY_POWER_ENTITY,
    CONF_TARGET_GRID_POWER,
    CONF_ZENDURE_CHARGE_ENTITIES,
    CONF_ZENDURE_OUTPUT_ENTITIES,
    CONF_ZENDURE_SOC_ENTITIES,
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


def _entity_list(value: str | list[str] | None) -> list[str]:
    """Normalize a comma or newline separated entity list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if item.strip()]
    return [
        item.strip()
        for chunk in value.splitlines()
        for item in chunk.split(",")
        if item.strip()
    ]


class SmartFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zendure SmartFlow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            output_entities = _entity_list(user_input[CONF_ZENDURE_OUTPUT_ENTITIES])
            charge_entities = _entity_list(user_input[CONF_ZENDURE_CHARGE_ENTITIES])
            soc_entities = _entity_list(user_input.get(CONF_ZENDURE_SOC_ENTITIES))

            if len(output_entities) != 3:
                errors[CONF_ZENDURE_OUTPUT_ENTITIES] = "need_three_outputs"
            elif len(charge_entities) != 3:
                errors[CONF_ZENDURE_CHARGE_ENTITIES] = "need_three_charges"
            elif soc_entities and len(soc_entities) != 3:
                errors[CONF_ZENDURE_SOC_ENTITIES] = "need_three_soc"
            else:
                await self.async_set_unique_id("zendure_smartflow")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=NAME,
                    data={
                        **user_input,
                        CONF_ZENDURE_OUTPUT_ENTITIES: output_entities,
                        CONF_ZENDURE_CHARGE_ENTITIES: charge_entities,
                        CONF_ZENDURE_SOC_ENTITIES: soc_entities,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SHELLY_POWER_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_ZENDURE_OUTPUT_ENTITIES): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                    vol.Required(CONF_ZENDURE_CHARGE_ENTITIES): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                    vol.Optional(CONF_ZENDURE_SOC_ENTITIES): selector.TextSelector(
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
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
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
        )
