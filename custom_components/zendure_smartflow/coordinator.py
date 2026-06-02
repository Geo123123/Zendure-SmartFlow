"""Control loop for Zendure SmartFlow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError, ClientTimeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
    CONF_ZENDURE_DEVICES,
    DEFAULT_DEADBAND,
    DEFAULT_ENABLED,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_CHARGE_PER_DEVICE,
    DEFAULT_MIN_CHANGE,
    DEFAULT_RESERVE_SOC,
    DEFAULT_RESPONSE_FACTOR,
    DEFAULT_TARGET_GRID_POWER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ZendureDevice:
    """Configured Zendure device."""

    host: str
    sn: str


@dataclass(slots=True)
class DeviceReport:
    """Relevant properties from a Zendure device report."""

    device: ZendureDevice
    soc: float | None
    ac_mode: int | None
    grid_input_power: float
    output_home_power: float
    solar_input_power: float


@dataclass(slots=True)
class SmartFlowData:
    """Current SmartFlow state."""

    enabled: bool
    grid_power: float | None
    target_grid_power: float
    error: float | None
    requested_charge: float
    applied_charge: float
    available_devices: int
    mode: str
    last_action: str


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class SmartFlowCoordinator(DataUpdateCoordinator[SmartFlowData]):
    """Coordinator implementing ZenSDK surplus charging with inverter bypass."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry
        self._enabled = self._option(CONF_ENABLED, DEFAULT_ENABLED)
        self._last_action = "idle"
        self._last_targets: dict[str, tuple[int, int, int]] = {}
        self._session = async_get_clientsession(hass)

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
    def devices(self) -> list[ZendureDevice]:
        """Return configured Zendure devices."""
        return [
            ZendureDevice(host=item["host"], sn=item["sn"])
            for item in self.config_entry.data[CONF_ZENDURE_DEVICES]
        ]

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
        max_charge_per_device = float(
            self._option(CONF_MAX_CHARGE_PER_DEVICE, DEFAULT_MAX_CHARGE_PER_DEVICE)
        )
        min_change = float(self._option(CONF_MIN_CHANGE, DEFAULT_MIN_CHANGE))
        response_factor = float(
            self._option(CONF_RESPONSE_FACTOR, DEFAULT_RESPONSE_FACTOR)
        )
        reserve_soc = float(self._option(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC))

        reports = await self._read_reports()
        current_charge_total = sum(report.grid_input_power for report in reports)
        available_reports = self._available_reports(reports, reserve_soc)
        available_count = len(available_reports)
        error = target_grid - grid_power

        if not self._enabled:
            self._last_action = "paused"
            return SmartFlowData(
                enabled=False,
                grid_power=grid_power,
                target_grid_power=target_grid,
                error=error,
                requested_charge=current_charge_total,
                applied_charge=current_charge_total,
                available_devices=available_count,
                mode="paused",
                last_action=self._last_action,
            )

        if available_count == 0:
            changed = await self._command_all_off(reports, min_change)
            self._last_action = (
                f"set {changed} devices off" if changed else "all devices full/off"
            )
            return SmartFlowData(
                enabled=True,
                grid_power=grid_power,
                target_grid_power=target_grid,
                error=error,
                requested_charge=0.0,
                applied_charge=0.0,
                available_devices=0,
                mode="full",
                last_action=self._last_action,
            )

        if grid_power >= -deadband:
            requested_charge = 0.0
            mode = "bypass"
        else:
            requested_charge = current_charge_total + (error * response_factor)
            requested_charge = max(
                0.0,
                min(requested_charge, max_charge_per_device * available_count),
            )
            mode = "charging"

        targets = self._build_targets(
            requested_charge, available_reports, reports, max_charge_per_device
        )
        changed = await self._write_targets(targets, reports, min_change)
        self._last_action = (
            f"set {changed} devices via ZenSDK"
            if changed
            else "change below minimum"
        )

        applied_charge = sum(target[2] for target in targets.values())
        return SmartFlowData(
            enabled=True,
            grid_power=grid_power,
            target_grid_power=target_grid,
            error=error,
            requested_charge=requested_charge,
            applied_charge=applied_charge,
            available_devices=available_count,
            mode=mode,
            last_action=self._last_action,
        )

    async def _read_reports(self) -> list[DeviceReport]:
        """Read relevant properties from all Zendure devices."""
        reports: list[DeviceReport] = []
        for device in self.devices:
            url = f"http://{device.host}/properties/report"
            try:
                async with self._session.get(
                    url, timeout=ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    payload = await response.json()
            except (ClientError, TimeoutError, ValueError) as err:
                raise UpdateFailed(f"Failed to read {device.host}: {err}") from err

            if payload.get("sn") not in {None, device.sn}:
                raise UpdateFailed(
                    f"Serial mismatch for {device.host}: got {payload.get('sn')}"
                )

            properties = payload.get("properties", {})
            reports.append(
                DeviceReport(
                    device=device,
                    soc=_as_float(properties.get("electricLevel")),
                    ac_mode=_as_int(properties.get("acMode")),
                    grid_input_power=_as_float(properties.get("gridInputPower")) or 0.0,
                    output_home_power=_as_float(properties.get("outputHomePower"))
                    or 0.0,
                    solar_input_power=_as_float(properties.get("solarInputPower"))
                    or 0.0,
                )
            )
        return reports

    def _available_reports(
        self, reports: list[DeviceReport], reserve_soc: float
    ) -> list[DeviceReport]:
        """Return devices that can still accept charge."""
        full_threshold = 100.0 - reserve_soc
        return [
            report
            for report in reports
            if report.soc is None or report.soc < full_threshold
        ]

    def _build_targets(
        self,
        requested_charge: float,
        available_reports: list[DeviceReport],
        reports: list[DeviceReport],
        max_charge_per_device: float,
    ) -> dict[str, tuple[int, int, int]]:
        """Build acMode/outputLimit/inputLimit targets for every device."""
        targets = {report.device.sn: (2, 0, 0) for report in reports}
        if requested_charge <= 0 or not available_reports:
            return targets

        per_device = round(
            max(0.0, min(requested_charge / len(available_reports), max_charge_per_device))
        )
        for report in available_reports:
            targets[report.device.sn] = (1, 0, per_device)
        return targets

    async def _command_all_off(
        self, reports: list[DeviceReport], min_change: float
    ) -> int:
        """Set all devices to no charge and no discharge."""
        return await self._write_targets(
            {report.device.sn: (2, 0, 0) for report in reports}, reports, min_change
        )

    async def _write_targets(
        self,
        targets: dict[str, tuple[int, int, int]],
        reports: list[DeviceReport],
        min_change: float,
    ) -> int:
        """Write changed targets via ZenSDK /properties/write."""
        report_by_sn = {report.device.sn: report for report in reports}
        changed = 0
        for sn, target in targets.items():
            report = report_by_sn[sn]
            ac_mode, output_limit, input_limit = target
            previous = self._last_targets.get(sn)
            current_input = report.grid_input_power if report.ac_mode == 1 else 0.0
            current_output = report.output_home_power if report.ac_mode == 2 else 0.0

            if (
                previous == target
                and abs(input_limit - current_input) < min_change
                and abs(output_limit - current_output) < min_change
            ):
                continue

            await self._write_device(report.device, ac_mode, output_limit, input_limit)
            self._last_targets[sn] = target
            changed += 1
        return changed

    async def _write_device(
        self, device: ZendureDevice, ac_mode: int, output_limit: int, input_limit: int
    ) -> None:
        """Write one Zendure device command via local ZenSDK HTTP API."""
        url = f"http://{device.host}/properties/write"
        payload = {
            "sn": device.sn,
            "properties": {
                "smartMode": 1,
                "acMode": ac_mode,
                "outputLimit": output_limit,
                "inputLimit": input_limit,
            },
        }
        try:
            async with self._session.post(
                url, json=payload, timeout=ClientTimeout(total=5)
            ) as response:
                response.raise_for_status()
        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Failed to write {device.host}: {err}") from err

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
