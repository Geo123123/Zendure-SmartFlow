"""Zendure SmartFlow integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_ENABLED,
    DOMAIN,
    PLATFORMS,
    SERVICE_FORCE_UPDATE,
    SERVICE_SET_ENABLED,
)
from .coordinator import SmartFlowCoordinator

_LOGGER = logging.getLogger(__name__)

_SERVICE_ENTRY_SCHEMA = vol.Schema(
    {vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Zendure SmartFlow services."""

    async def _get_coordinator(call: ServiceCall) -> SmartFlowCoordinator:
        entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
        if coordinator is None:
            raise ServiceValidationError(
                f"Zendure SmartFlow entry {entry_id} is not loaded"
            )
        return coordinator

    async def _force_update(call: ServiceCall) -> None:
        coordinator = await _get_coordinator(call)
        await coordinator.async_request_refresh()

    async def _set_enabled(call: ServiceCall) -> None:
        coordinator = await _get_coordinator(call)
        await coordinator.async_set_enabled(call.data[ATTR_ENABLED])

    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_UPDATE,
        _force_update,
        schema=_SERVICE_ENTRY_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ENABLED,
        _set_enabled,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
                vol.Required(ATTR_ENABLED): cv.boolean,
            }
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zendure SmartFlow from a config entry."""
    coordinator = SmartFlowCoordinator(hass, entry)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(platform) for platform in PLATFORMS]
    )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform(platform) for platform in PLATFORMS]
    )
    if unload_ok:
        coordinator: SmartFlowCoordinator | None = hass.data[DOMAIN].pop(
            entry.entry_id, None
        )
        if coordinator is not None and hasattr(coordinator, "async_shutdown"):
            coordinator.async_shutdown()

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
