from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeyitechCoordinator

_MAX_ZONES = 32


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coord: HeyitechCoordinator = entry.runtime_data
    entities = [HeyitechZoneStateSensor(coord, entry, zone_id) for zone_id in range(1, _MAX_ZONES + 1)]
    async_add_entities(entities)


class HeyitechZoneStateSensor(CoordinatorEntity[HeyitechCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: HeyitechCoordinator, entry: ConfigEntry, zone_id: int) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone_id}_state"
        self._attr_icon = "mdi:shield-home"

    def _zone_reference(self) -> str:
        data = self.coordinator.data or {}
        reference_map = data.get("zone_reference_map")
        if isinstance(reference_map, dict):
            value = reference_map.get(str(self._zone_id))
            if value is not None:
                text = str(value).strip()
                if text:
                    return text
        return str(self._zone_id)

    @property
    def name(self) -> str:
        return f"Zone {self._zone_reference()}"

    @property
    def native_value(self) -> int | None:
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
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "zone_id": self._zone_id,
            "zone_reference": self._zone_reference(),
            "raw_value": None if self.native_value is None else str(self.native_value),
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
