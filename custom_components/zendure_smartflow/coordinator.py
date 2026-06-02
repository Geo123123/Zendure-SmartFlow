"""Control loop for Zendure SmartFlow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEADBAND,
    CONF_ENABLED,
    CONF_INTERVAL,
    CONF_MAX_OUTPUT_PER_DEVICE,
    CONF_MIN_CHANGE,
    CONF_RESERVE_SOC,
    CONF_RESPONSE_FACTOR,
    CONF_SHELLY_POWER_ENTITY,
    CONF_TARGET_GRID_POWER,
    CONF_ZENDURE_OUTPUT_ENTITIES,
    CONF_ZENDURE_SOC_ENTITIES,
    DEFAULT_DEADBAND,
    DEFAULT_ENABLED,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_OUTPUT_PER_DEVICE,
    DEFAULT_MIN_CHANGE,
    DEFAULT_RESERVE_SOC,
    DEFAULT_RESPONSE_FACTOR,
    DEFAULT_TARGET_GRID_POWER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SmartFlowData:
    """Current SmartFlow state."""

    enabled: bool
    grid_power: float | None
    target_grid_power: float
    error: float | None
    requested_output: float
    applied_output: float
    available_devices: int
    mode: str
    last_action: str


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class SmartFlowCoordinator(DataUpdateCoordinator[SmartFlowData]):
    """Coordinator implementing the PV regulation loop."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry
        self._enabled = self._option(CONF_ENABLED, DEFAULT_ENABLED)
        self._last_action = "idle"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=max(2, int(self._option(CONF_INTERVAL, DEFAULT_INTERVAL)))
            ),
        )

    @property
    def shelly_power_entity(self) -> str:
        """Return the Shelly grid power entity."""
        return self.config_entry.data[CONF_SHELLY_POWER_ENTITY]

    @property
    def output_entities(self) -> list[str]:
        """Return the Zendure output number entities."""
        return list(self.config_entry.data[CONF_ZENDURE_OUTPUT_ENTITIES])

    @property
    def soc_entities(self) -> list[str]:
        """Return optional Zendure SOC sensor entities."""
        return list(self.config_entry.data.get(CONF_ZENDURE_SOC_ENTITIES, []))

    @property
    def enabled(self) -> bool:
        """Return whether regulation is enabled."""
        return self._enabled

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable or disable regulation."""
        self._enabled = enabled
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, CONF_ENABLED: enabled},
        )
        await self.async_request_refresh()

    async def async_set_option(self, key: str, value: float | int | bool) -> None:
        """Persist a tunable option and refresh."""
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, key: value},
        )
        await self.async_request_refresh()

    async def _async_update_data(self) -> SmartFlowData:
        """Run one regulation cycle."""
        grid_power = self._state_float(self.shelly_power_entity)
        if grid_power is None:
            raise UpdateFailed(
                f"Grid power entity {self.shelly_power_entity} is unavailable"
            )

        target_grid = float(
            self._option(CONF_TARGET_GRID_POWER, DEFAULT_TARGET_GRID_POWER)
        )
        deadband = float(self._option(CONF_DEADBAND, DEFAULT_DEADBAND))
        max_per_device = float(
            self._option(CONF_MAX_OUTPUT_PER_DEVICE, DEFAULT_MAX_OUTPUT_PER_DEVICE)
        )
        min_change = float(self._option(CONF_MIN_CHANGE, DEFAULT_MIN_CHANGE))
        response_factor = float(
            self._option(CONF_RESPONSE_FACTOR, DEFAULT_RESPONSE_FACTOR)
        )
        reserve_soc = float(self._option(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC))

        output_states = [self._state_float(entity_id) for entity_id in self.output_entities]
        current_total = sum(value or 0.0 for value in output_states)
        available = self._available_output_entities(reserve_soc)
        available_count = len(available)
        error = grid_power - target_grid

        if not self._enabled:
            self._last_action = "paused"
            return SmartFlowData(
                enabled=False,
                grid_power=grid_power,
                target_grid_power=target_grid,
                error=error,
                requested_output=current_total,
                applied_output=current_total,
                available_devices=available_count,
                mode="paused",
                last_action=self._last_action,
            )

        if available_count == 0:
            await self._set_outputs({entity_id: 0.0 for entity_id in self.output_entities})
            self._last_action = "all devices below reserve"
            return SmartFlowData(
                enabled=True,
                grid_power=grid_power,
                target_grid_power=target_grid,
                error=error,
                requested_output=0.0,
                applied_output=0.0,
                available_devices=0,
                mode="reserve",
                last_action=self._last_action,
            )

        if abs(error) <= deadband:
            self._last_action = "inside deadband"
            mode = "balanced"
            requested_total = current_total
        else:
            requested_total = current_total + (error * response_factor)
            requested_total = max(0.0, min(requested_total, max_per_device * available_count))
            mode = "discharging" if error > 0 else "reducing"

        targets = self._distribute(requested_total, available, max_per_device)
        for entity_id in self.output_entities:
            targets.setdefault(entity_id, 0.0)

        changed_targets = {
            entity_id: value
            for entity_id, value in targets.items()
            if abs(value - (self._state_float(entity_id) or 0.0)) >= min_change
        }
        if changed_targets:
            await self._set_outputs(changed_targets)
            self._last_action = f"set {len(changed_targets)} output entities"
        else:
            self._last_action = "change below minimum"

        applied_total = sum(targets.values())
        return SmartFlowData(
            enabled=True,
            grid_power=grid_power,
            target_grid_power=target_grid,
            error=error,
            requested_output=requested_total,
            applied_output=applied_total,
            available_devices=available_count,
            mode=mode,
            last_action=self._last_action,
        )

    def _available_output_entities(self, reserve_soc: float) -> list[str]:
        """Return output entities whose matching SOC is above reserve."""
        if not self.soc_entities:
            return self.output_entities

        available: list[str] = []
        for index, output_entity in enumerate(self.output_entities):
            soc_entity = self.soc_entities[index] if index < len(self.soc_entities) else None
            soc = self._state_float(soc_entity) if soc_entity else None
            if soc is None or soc > reserve_soc:
                available.append(output_entity)
        return available

    def _distribute(
        self, requested_total: float, available: list[str], max_per_device: float
    ) -> dict[str, float]:
        """Distribute requested watts evenly across available Zendure devices."""
        if not available:
            return {}

        per_device = max(0.0, min(requested_total / len(available), max_per_device))
        return {entity_id: round(per_device) for entity_id in available}

    async def _set_outputs(self, targets: dict[str, float]) -> None:
        """Set Zendure output number entities."""
        for entity_id, value in targets.items():
            await self.hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": entity_id, "value": round(value)},
                blocking=False,
            )

    def _state_float(self, entity_id: str | None) -> float | None:
        """Return an entity state as float."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable"}:
            return None
        return _as_float(state.state)

    def _option(self, key: str, default: Any) -> Any:
        """Return an option, falling back to config data and defaults."""
        return self.config_entry.options.get(key, self.config_entry.data.get(key, default))
