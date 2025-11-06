from __future__ import annotations
import importlib
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import HeyitechCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up integration via configuration.yaml (legacy, unused)."""
    return True


async def _preload_platforms(hass: HomeAssistant) -> None:
    """Preload platform modules off the event loop to avoid blocking import warnings."""
    def _load(name: str) -> None:
        importlib.import_module(f"{__package__}.{name}")
    for name in PLATFORMS:
        await hass.async_add_executor_job(_load, name)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a Heyitech Alarm entry from config flow."""
    # Optional: preload platform modules to prevent import warnings
    await _preload_platforms(hass)

    # Build the coordinator and fetch initial data
    coord = HeyitechCoordinator(hass, entry.data | entry.options)
    await coord.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord

    # Proper, awaited setup of all platforms (2025-safe)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(_updated))
    return True


async def _updated(hass: HomeAssistant, entry: ConfigEntry):
    """Handle updated config entry options."""
    coord = hass.data[DOMAIN][entry.entry_id]
    await coord.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
