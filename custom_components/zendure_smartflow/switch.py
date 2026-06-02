"""Switches for Zendure SmartFlow."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import SmartFlowCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartFlow switches."""
    coordinator: SmartFlowCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SmartFlowEnabledSwitch(coordinator, config_entry)])


class SmartFlowEnabledSwitch(CoordinatorEntity[SmartFlowCoordinator], SwitchEntity):
    """Switch to enable or disable regulation."""

    _attr_has_entity_name = True
    _attr_name = "Regulation"
    _attr_translation_key = "regulation"

    def __init__(
        self, coordinator: SmartFlowCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_regulation"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": NAME,
            "manufacturer": "Zendure SmartFlow",
        }

    @property
    def is_on(self) -> bool:
        """Return if regulation is enabled."""
        return self.coordinator.enabled

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable regulation."""
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable regulation."""
        await self.coordinator.async_set_enabled(False)
