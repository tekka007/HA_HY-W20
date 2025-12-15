from __future__ import annotations

from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.const import STATE_UNKNOWN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import async_get_current_platform
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    LEVEL_DISARMED,
    LEVEL_ARMED,
    LEVEL_HOME,
    CMD_DISARM,
    CMD_ARMED,
    CMD_HOME,
)
from .coordinator import HeyitechCoordinator


def _map_value_to_state(val: int) -> str:
    # 0 = disarmed, 1 = armed, 2 = home armed
    if val == LEVEL_DISARMED:
        return AlarmControlPanelState.DISARMED
    if val == LEVEL_ARMED:
        return AlarmControlPanelState.ARMED_AWAY
    if val == LEVEL_HOME:
        return AlarmControlPanelState.ARMED_HOME
    return STATE_UNKNOWN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coord: HeyitechCoordinator = hass.data[DOMAIN][entry.entry_id]
    ent = HeyitechAlarmEntity(coord, entry)
    async_add_entities([ent], True)

    # Register a raw pass-through service for testing/debugging
    # Note: 0 (status code) is intentionally excluded; only valid write commands 1, 2, 3 are allowed.
    platform = async_get_current_platform()
    platform.async_register_entity_service(
        "set_raw_state",
        {vol.Required("state"): vol.In([1, 2, 3])},
        "async_set_raw_state",
    )


class HeyitechAlarmEntity(CoordinatorEntity[HeyitechCoordinator], AlarmControlPanelEntity):
    _attr_has_entity_name = True
    _attr_name = "Alarm"
    # No code required to arm/disarm
    _attr_code_arm_required = False
    # DISARM feature flag doesn't exist; disarm still works
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    def __init__(self, coordinator: HeyitechCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_alarm"

    @property
    def icon(self) -> str | None:
        state = self.state

        if state == AlarmControlPanelState.DISARMED:
            return "mdi:shield-off"
        if state == AlarmControlPanelState.ARMED_HOME:
            return "mdi:shield-home"
        if state == AlarmControlPanelState.ARMED_AWAY:
            return "mdi:shield-lock"

        return "mdi:shield-alert"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device registry information."""
        device_id = self._entry.data.get("device_id")
        return {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": f"Heyitech Alarm {device_id}",
            "manufacturer": "Heyitech",
            "model": "Alarm Panel",
        }

    @property
    def code_format(self):
        # Returning None tells HA that no code is used at all
        return None

    @property
    def state(self) -> Optional[str]:
        d: Dict[str, Any] = self.coordinator.data or {}
        try:
            level = int(d.get("value"))
        except Exception:
            return STATE_UNKNOWN
        return _map_value_to_state(level)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        d = self.coordinator.data or {}
        return {
            "device_id": self._entry.data.get("device_id"),
            "arm_level_raw": d.get("value"),
            "raw": d,
        }

    async def _send(self, control_type: int) -> None:
        await self.coordinator.client.remote_control(
            username=self.coordinator.username,
            password=self.coordinator.password,
            terminal=self.coordinator.terminal,
            lang=self.coordinator.lang,
            tz=self.coordinator.tz,
            device_id=self._entry.data["device_id"],
            control_type=control_type,
        )
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: Optional[str] = None) -> None:
        await self._send(CMD_DISARM)

    async def async_alarm_arm_home(self, code: Optional[str] = None) -> None:
        await self._send(CMD_HOME)

    async def async_alarm_arm_away(self, code: Optional[str] = None) -> None:
        await self._send(CMD_ARMED)

    async def async_set_raw_state(self, state: int) -> None:
        await self._send(int(state))
