from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_USERNAME, CONF_PASSWORD, CONF_BASE_URL, CONF_DEVICE_ID, CONF_CLOUD_DEFAULT,
    CONF_TIMEZONE, CONF_LANG, CONF_TERMINAL, CONF_UPDATE_INTERVAL,
    DEFAULT_TZ, DEFAULT_LANG, DEFAULT_TERMINAL, DEFAULT_UPDATE_INTERVAL,
)

class HeyitechConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_BASE_URL].rstrip("/"))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Heyitech Alarm", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=CONF_CLOUD_DEFAULT): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_DEVICE_ID): str,
            vol.Optional(CONF_TIMEZONE, default=DEFAULT_TZ): str,
            vol.Optional(CONF_LANG, default=DEFAULT_LANG): str,
            vol.Optional(CONF_TERMINAL, default=DEFAULT_TERMINAL): str,
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HeyitechOptionsFlow(config_entry)


class HeyitechOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry):
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self._entry.options
        schema = vol.Schema({
            vol.Optional(CONF_UPDATE_INTERVAL, default=opts.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): int,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
