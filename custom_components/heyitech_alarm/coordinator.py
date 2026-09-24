from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_USERNAME, CONF_PASSWORD, CONF_BASE_URL, CONF_DEVICE_ID,
    CONF_TIMEZONE, CONF_LANG, CONF_TERMINAL, CONF_TERMINAL_STATE_TYPES,
)
from .api import HeyitechClient, HeyitechApiError
from .const import DEFAULT_LANG, DEFAULT_TERMINAL, DEFAULT_TERMINAL_STATE_TYPES, DEFAULT_TZ
from .const import DEFAULT_UPDATE_INTERVAL, CONF_UPDATE_INTERVAL


_LOGGER = logging.getLogger(__name__)


def _parse_state_types(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or ["3"]


def _decode_bit_array(bit_string: Any) -> dict[str, bool]:
    if not isinstance(bit_string, str):
        return {}
    bits = bit_string.strip()
    if not bits or any(ch not in {"0", "1"} for ch in bits):
        return {}
    return {str(idx + 1): (ch == "1") for idx, ch in enumerate(bits)}


def _zone_reference_label(entry: dict[str, Any], fallback: str) -> str:
    for key in ("zoneRef", "zoneNO", "zoneName", "name", "stateName"):
        value = entry.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return fallback


class HeyitechCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator handling periodic updates from Heyitech cloud."""

    def __init__(self, hass: HomeAssistant, cfg: dict):
        self.hass = hass
        self.username = cfg[CONF_USERNAME]
        self.password = cfg[CONF_PASSWORD]
        self.base_url = cfg[CONF_BASE_URL]
        self.device_id = cfg[CONF_DEVICE_ID]
        self.lang = cfg.get(CONF_LANG, DEFAULT_LANG)
        self.terminal = cfg.get(CONF_TERMINAL, DEFAULT_TERMINAL)
        self.tz = cfg.get(CONF_TIMEZONE, DEFAULT_TZ)
        self.terminal_state_types = _parse_state_types(
            str(cfg.get(CONF_TERMINAL_STATE_TYPES, DEFAULT_TERMINAL_STATE_TYPES))
        )
        interval = max(5, int(cfg.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)))

        session = async_get_clientsession(hass)
        self.client = HeyitechClient(session, self.base_url)
        self.zone_reference_map: dict[str, str] = {}
        self._zone_info_attempted = False

        super().__init__(
            hass,
            _LOGGER,
            name="Heyitech Alarm Coordinator",
            update_interval=timedelta(seconds=interval),
        )

    async def async_load_zone_info_once(self) -> None:
        """Load zone reference names once during startup."""
        if self._zone_info_attempted:
            return

        self._zone_info_attempted = True
        try:
            payload = await self.client.get_zone_name_list(
                self.username,
                self.password,
                self.terminal,
                self.lang,
                self.tz,
                self.device_id,
            )
        except HeyitechApiError as err:
            _LOGGER.debug("get_zone_name_list failed for device %s: %s", self.device_id, err)
            return

        value = payload.get("value")
        if not isinstance(value, list):
            return

        resolved: dict[str, str] = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            zone_id = item.get("id")
            if zone_id is None:
                continue
            label = item.get("zn")
            if label is None:
                continue
            text = str(label).strip()
            if not text:
                continue
            resolved[str(zone_id)] = text

        self.zone_reference_map = resolved

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest status from Heyitech API."""
        await self.async_load_zone_info_once()

        try:
            status = await self.client.get_arm_status(
                self.username,
                self.password,
                self.terminal,
                self.lang,
                self.tz,
                self.device_id,
            )
            await self._enrich_with_device_snapshot(status)
            await self._enrich_with_terminal_status(status)
            return status
        except HeyitechApiError as err:
            _LOGGER.debug(
                "get_arm_status failed for device %s, trying find_device_list fallback: %s",
                self.device_id,
                err,
            )

            try:
                listing = await self.client.find_device_list(
                    self.username,
                    self.password,
                    self.terminal,
                    self.lang,
                    self.tz,
                )
                devices = listing.get("value")
                if not isinstance(devices, list):
                    raise UpdateFailed(
                        "find_device_list returned an unexpected payload shape"
                    )

                selected: dict[str, Any] | None = None
                for item in devices:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("deviceID")) == str(self.device_id):
                        selected = item
                        break

                if selected is None:
                    raise UpdateFailed(
                        f"Device {self.device_id} not found in find_device_list response"
                    )

                arm_state = selected.get("armState")
                if arm_state is None:
                    raise UpdateFailed(
                        f"Device {self.device_id} has no armState in find_device_list response"
                    )

                status = {
                    "value": arm_state,
                    "device_info": selected,
                    "source": "pdevfindDeviceList",
                }
                self._inject_decoded_bitfields(status, selected)
                await self._enrich_with_terminal_status(status)
                return status

            except (HeyitechApiError, UpdateFailed) as fallback_err:
                raise UpdateFailed(str(fallback_err)) from fallback_err

    async def _enrich_with_terminal_status(self, status: Dict[str, Any]) -> None:
        """Add zone-level state data when terminal status endpoint is available."""
        try:
            terminal_status = await self.client.get_terminal_status(
                self.username,
                self.password,
                self.terminal,
                self.lang,
                self.tz,
                self.device_id,
                state_types=self.terminal_state_types,
            )
        except HeyitechApiError as err:
            _LOGGER.debug("get_terminal_status failed for device %s: %s", self.device_id, err)
            return

        value = terminal_status.get("value")
        if not isinstance(value, dict):
            return

        zone_state_list = value.get("zoneStateList")
        if isinstance(zone_state_list, list):
            status["zone_state_list"] = zone_state_list
            status["zone_state_map"] = {
                str(item.get("stateID")): item.get("stateValue")
                for item in zone_state_list
                if isinstance(item, dict) and item.get("stateID") is not None
            }
            fallback_reference_map = {
                str(item.get("stateID")): _zone_reference_label(item, str(item.get("stateID")))
                for item in zone_state_list
                if isinstance(item, dict) and item.get("stateID") is not None
            }
            # Prefer explicit zone-name list labels; fall back to terminal status labels.
            status["zone_reference_map"] = {
                key: self.zone_reference_map.get(key, fallback_reference_map.get(key, key))
                for key in set(self.zone_reference_map) | set(fallback_reference_map)
            }

        status["terminal_status"] = value

        if "zone_reference_map" not in status and self.zone_reference_map:
            status["zone_reference_map"] = dict(self.zone_reference_map)

    async def _enrich_with_device_snapshot(self, status: Dict[str, Any]) -> None:
        """Attach device snapshot and decode bitfield state maps when available."""
        try:
            listing = await self.client.find_device_list(
                self.username,
                self.password,
                self.terminal,
                self.lang,
                self.tz,
            )
        except HeyitechApiError as err:
            _LOGGER.debug("find_device_list enrich failed for device %s: %s", self.device_id, err)
            return

        devices = listing.get("value")
        if not isinstance(devices, list):
            return

        for item in devices:
            if not isinstance(item, dict):
                continue
            if str(item.get("deviceID")) != str(self.device_id):
                continue
            status["device_info"] = item
            self._inject_decoded_bitfields(status, item)
            return

    def _inject_decoded_bitfields(self, status: Dict[str, Any], device_info: Dict[str, Any]) -> None:
        alarm_state_bits = device_info.get("alarmState")
        if isinstance(alarm_state_bits, str):
            status["alarm_state_bits"] = alarm_state_bits
            status["alarm_state_map"] = _decode_bit_array(alarm_state_bits)

        device_state_bits = device_info.get("deviceState")
        if isinstance(device_state_bits, str):
            status["device_state_bits"] = device_state_bits
            status["device_state_map"] = _decode_bit_array(device_state_bits)

        if self.zone_reference_map:
            status["zone_reference_map"] = dict(self.zone_reference_map)
