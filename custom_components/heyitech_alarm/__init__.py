from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .const import CONF_TERMINAL_STATE_TYPES, CONF_UPDATE_INTERVAL, DEFAULT_TERMINAL_STATE_TYPES
from .coordinator import HeyitechCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up integration via configuration.yaml (legacy, unused)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a Heyitech Alarm entry from config flow."""
    # Build the coordinator and fetch initial data.
    coord = HeyitechCoordinator(hass, entry.data | entry.options)
    await coord.async_config_entry_first_refresh()
    entry.runtime_data = coord

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_updated))

    return True


async def _updated(hass: HomeAssistant, entry: ConfigEntry):
    coord: HeyitechCoordinator = entry.runtime_data
    interval = entry.options.get(CONF_UPDATE_INTERVAL, coord.update_interval.total_seconds())
    coord.update_interval = timedelta(seconds=int(interval))
    state_types = entry.options.get(
        CONF_TERMINAL_STATE_TYPES,
        entry.data.get(CONF_TERMINAL_STATE_TYPES, DEFAULT_TERMINAL_STATE_TYPES),
    )
    coord.terminal_state_types = [chunk.strip() for chunk in str(state_types).split(",") if chunk.strip()] or ["3"]
    await coord.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return ok
