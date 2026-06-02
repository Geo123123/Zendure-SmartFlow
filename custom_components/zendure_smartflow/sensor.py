"""Sensors for Zendure SmartFlow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import SmartFlowCoordinator, SmartFlowData


@dataclass(frozen=True, slots=True)
class SensorDescription:
    """SmartFlow sensor description."""

    key: str
    name: str
    native_unit_of_measurement: str | None
    device_class: SensorDeviceClass | None
    state_class: SensorStateClass | None
    value_fn: Callable[[SmartFlowData], str | float | int | None]


SENSORS = (
    SensorDescription(
        "grid_power",
        "Grid power",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        lambda data: data.grid_power,
    ),
    SensorDescription(
        "target_grid_power",
        "Target grid power",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        lambda data: data.target_grid_power,
    ),
    SensorDescription(
        "error",
        "Control error",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        lambda data: data.error,
    ),
    SensorDescription(
        "requested_output",
        "Requested output",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        lambda data: data.requested_output,
    ),
    SensorDescription(
        "applied_output",
        "Applied output",
        UnitOfPower.WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        lambda data: data.applied_output,
    ),
    SensorDescription(
        "available_devices",
        "Available devices",
        None,
        None,
        SensorStateClass.MEASUREMENT,
        lambda data: data.available_devices,
    ),
    SensorDescription(
        "mode",
        "Mode",
        None,
        None,
        None,
        lambda data: data.mode,
    ),
    SensorDescription(
        "last_action",
        "Last action",
        None,
        None,
        None,
        lambda data: data.last_action,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartFlow sensors."""
    coordinator: SmartFlowCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SmartFlowSensor(coordinator, config_entry, description) for description in SENSORS
    )


class SmartFlowSensor(CoordinatorEntity[SmartFlowCoordinator], SensorEntity):
    """Zendure SmartFlow sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartFlowCoordinator,
        config_entry: ConfigEntry,
        description: SensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": NAME,
            "manufacturer": "Zendure SmartFlow",
        }

    @property
    def native_value(self) -> str | float | int | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
