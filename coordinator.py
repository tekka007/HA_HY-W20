from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_UPDATE_INTERVAL,
    CONF_USERNAME, CONF_PASSWORD, CONF_BASE_URL, CONF_DEVICE_ID,
    CONF_TIMEZONE, CONF_LANG, CONF_TERMINAL, CONF_UPDATE_INTERVAL,
)
from .api import HeyitechClient, HeyitechApiError

_LOGGER = logging.getLogger(__name__)


class HeyitechCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator handling periodic updates from Heyitech cloud."""

    def __init__(self, hass: HomeAssistant, cfg: dict):
        self.hass = hass
        self.username = cfg[CONF_USERNAME]
        self.password = cfg[CONF_PASSWORD]
        self.base_url = cfg[CONF_BASE_URL]
        self.device_id = cfg[CONF_DEVICE_ID]
        self.lang = cfg.get(CONF_LANG)
        self.terminal = cfg.get(CONF_TERMINAL)
        self.tz = cfg.get(CONF_TIMEZONE)
        interval = cfg.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        session = async_get_clientsession(hass)
        self.client = HeyitechClient(session, self.base_url)

        super().__init__(
            hass,
            _LOGGER,
            name="Heyitech Alarm Coordinator",
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest status from Heyitech API."""
        try:
            return await self.client.get_arm_status(
                self.username,
                self.password,
                self.terminal,
                self.lang,
                self.tz,
                self.device_id,
            )
        except HeyitechApiError as err:
            raise UpdateFailed(str(err)) from err
