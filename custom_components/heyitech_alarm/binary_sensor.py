from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeyitechCoordinator

_MAX_ZONES = 32


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coord: HeyitechCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for zone_id in range(1, _MAX_ZONES + 1):
        entities.append(HeyitechZoneOpenBinarySensor(coord, entry, zone_id))
        entities.append(HeyitechZoneAlarmCauseBinarySensor(coord, entry, zone_id))
    async_add_entities(entities)


class _HeyitechZoneBinaryBase(CoordinatorEntity[HeyitechCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: HeyitechCoordinator, entry: ConfigEntry, zone_id: int) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id

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

    def _bit_map_bool(self, field: str) -> bool | None:
        data = self.coordinator.data or {}
        bit_map = data.get(field)
        if not isinstance(bit_map, dict):
            return None

        raw = bit_map.get(str(self._zone_id))
        if isinstance(raw, bool):
            return raw
        if raw is None:
            return None
        return bool(raw)

    @property
    def device_info(self) -> dict[str, Any]:
        device_id = self._entry.data.get("device_id")
        return {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": f"Heyitech Alarm {device_id}",
            "manufacturer": "Heyitech",
            "model": "Alarm Panel",
        }


class HeyitechZoneOpenBinarySensor(_HeyitechZoneBinaryBase):
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(self, coordinator: HeyitechCoordinator, entry: ConfigEntry, zone_id: int) -> None:
        super().__init__(coordinator, entry, zone_id)
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone_id}_open"
        self._attr_icon = "mdi:door-open"

    @property
    def name(self) -> str:
        return f"Zone {self._zone_reference()} Open"

    @property
    def is_on(self) -> bool | None:
        # deviceState bit = True means sensor open.
        return self._bit_map_bool("device_state_map")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.is_on
        return {
            "zone_id": self._zone_id,
            "zone_reference": self._zone_reference(),
            "state": None if state is None else ("open" if state else "closed"),
            "source": "deviceState bit array",
        }


class HeyitechZoneAlarmCauseBinarySensor(_HeyitechZoneBinaryBase):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: HeyitechCoordinator, entry: ConfigEntry, zone_id: int) -> None:
        super().__init__(coordinator, entry, zone_id)
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone_id}_alarm_cause"
        self._attr_icon = "mdi:alert-circle"

    @property
    def name(self) -> str:
        return f"Zone {self._zone_reference()} Alarm Cause"

    @property
    def is_on(self) -> bool | None:
        # alarmState bit = True means this zone is marked as an alarm source.
        return self._bit_map_bool("alarm_state_map")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.is_on
        return {
            "zone_id": self._zone_id,
            "zone_reference": self._zone_reference(),
            "state": None if state is None else ("alarm_source" if state else "normal"),
            "source": "alarmState bit array",
        }
