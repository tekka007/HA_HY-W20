from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeyitechCoordinator

_MAX_ZONES = 32
_NORMAL_ZONE_VALUE = 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coord: HeyitechCoordinator = entry.runtime_data
    entities = [HeyitechZoneTriggeredBinarySensor(coord, entry, zone_id) for zone_id in range(1, _MAX_ZONES + 1)]
    async_add_entities(entities)


class HeyitechZoneTriggeredBinarySensor(CoordinatorEntity[HeyitechCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: HeyitechCoordinator, entry: ConfigEntry, zone_id: int) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id
        self._attr_name = f"Zone {zone_id} Triggered"
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone_id}_triggered"
        self._attr_icon = "mdi:alert-circle"

    def _raw_value(self) -> int | None:
        data = self.coordinator.data or {}
        zone_map = data.get("zone_state_map")
        if not isinstance(zone_map, dict):
            return None

        raw = zone_map.get(str(self._zone_id))
        if raw is None:
            return None

        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    @property
    def is_on(self) -> bool | None:
        raw = self._raw_value()
        if raw is None:
            return None
        return raw != _NORMAL_ZONE_VALUE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        raw = self._raw_value()
        return {
            "zone_id": self._zone_id,
            "raw_value": None if raw is None else str(raw),
            "normal_value": str(_NORMAL_ZONE_VALUE),
            "source": "pdevgetTerminalStatus.zoneStateList",
        }

    @property
    def device_info(self) -> dict[str, Any]:
        device_id = self._entry.data.get("device_id")
        return {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": f"Heyitech Alarm {device_id}",
            "manufacturer": "Heyitech",
            "model": "Alarm Panel",
        }
