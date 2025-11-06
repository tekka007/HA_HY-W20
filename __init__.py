from __future__ import annotations
import importlib
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import HeyitechCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True


async def _preload_platforms(hass: HomeAssistant) -> None:
    """Preload platform modules off the event loop to avoid blocking import warnings."""
    def _load(name: str) -> None:
        importlib.import_module(f"{__package__}.{name}")
    for name in PLATFORMS:
        await hass.async_add_executor_job(_load, name)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Preload platform modules to avoid importlib.import_module within event loop
    await _preload_platforms(hass)

    coord = HeyitechCoordinator(hass, entry.data | entry.options)
    await coord.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord

    # Forward setup to platforms safely
    for platform in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))

    entry.async_on_unload(entry.add_update_listener(_updated))
    return True


async def _updated(hass: HomeAssistant, entry: ConfigEntry):
    coord = hass.data[DOMAIN][entry.entry_id]
    await coord.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
