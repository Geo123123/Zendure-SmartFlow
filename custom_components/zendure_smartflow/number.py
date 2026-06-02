"""Numbers for Zendure SmartFlow tuning."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEADBAND,
    CONF_INTERVAL,
    CONF_MAX_OUTPUT_PER_DEVICE,
    CONF_MIN_CHANGE,
    CONF_RESERVE_SOC,
    CONF_RESPONSE_FACTOR,
    CONF_TARGET_GRID_POWER,
    DEFAULT_DEADBAND,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_OUTPUT_PER_DEVICE,
    DEFAULT_MIN_CHANGE,
    DEFAULT_RESERVE_SOC,
    DEFAULT_RESPONSE_FACTOR,
    DEFAULT_TARGET_GRID_POWER,
    DOMAIN,
    NAME,
)
from .coordinator import SmartFlowCoordinator


@dataclass(frozen=True, slots=True)
class NumberDescription:
    """SmartFlow number description."""

    key: str
    name: str
    native_min_value: float
    native_max_value: float
    native_step: float
    native_unit_of_measurement: str | None
    default: float


NUMBERS = (
    NumberDescription(
        CONF_TARGET_GRID_POWER,
        "Target grid power",
        -500,
        500,
        5,
        UnitOfPower.WATT,
        DEFAULT_TARGET_GRID_POWER,
    ),
    NumberDescription(
        CONF_DEADBAND,
        "Deadband",
        0,
        500,
        5,
        UnitOfPower.WATT,
        DEFAULT_DEADBAND,
    ),
    NumberDescription(
        CONF_MAX_OUTPUT_PER_DEVICE,
        "Max output per device",
        0,
        2400,
        10,
        UnitOfPower.WATT,
        DEFAULT_MAX_OUTPUT_PER_DEVICE,
    ),
    NumberDescription(
        CONF_MIN_CHANGE,
        "Minimum change",
        0,
        500,
        5,
        UnitOfPower.WATT,
        DEFAULT_MIN_CHANGE,
    ),
    NumberDescription(
        CONF_RESPONSE_FACTOR,
        "Response factor",
        0.05,
        2.0,
        0.05,
        None,
        DEFAULT_RESPONSE_FACTOR,
    ),
    NumberDescription(
        CONF_RESERVE_SOC,
        "Reserve SOC",
        0,
        100,
        1,
        PERCENTAGE,
        DEFAULT_RESERVE_SOC,
    ),
    NumberDescription(
        CONF_INTERVAL,
        "Interval",
        2,
        120,
        1,
        UnitOfTime.SECONDS,
        DEFAULT_INTERVAL,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartFlow number entities."""
    coordinator: SmartFlowCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SmartFlowNumber(coordinator, config_entry, description) for description in NUMBERS
    )


class SmartFlowNumber(NumberEntity):
    """Number entity for SmartFlow tuning."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: SmartFlowCoordinator,
        config_entry: ConfigEntry,
        description: NumberDescription,
    ) -> None:
        """Initialize the number."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_name = description.name
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": NAME,
            "manufacturer": "Zendure SmartFlow",
        }

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return float(
            self.config_entry.options.get(
                self.entity_description.key,
                self.config_entry.data.get(
                    self.entity_description.key, self.entity_description.default
                ),
            )
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set a new tuning value."""
        await self.coordinator.async_set_option(self.entity_description.key, value)
