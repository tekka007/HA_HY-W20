from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_USERNAME, CONF_PASSWORD, CONF_BASE_URL, CONF_DEVICE_ID, CONF_CLOUD_DEFAULT,
    CONF_TIMEZONE, CONF_LANG, CONF_TERMINAL, CONF_UPDATE_INTERVAL, CONF_TERMINAL_STATE_TYPES,
    DEFAULT_TZ, DEFAULT_LANG, DEFAULT_TERMINAL, DEFAULT_UPDATE_INTERVAL, DEFAULT_TERMINAL_STATE_TYPES,
)


def _normalize_base_url(value: str) -> str:
    return value.strip().rstrip("/")


POLL_INTERVAL_VALIDATOR = vol.All(vol.Coerce(int), vol.Range(min=5, max=3600))


def _normalize_state_types(value: str) -> str:
    chunks = [part.strip() for part in value.split(",") if part.strip()]
    if not chunks:
        return DEFAULT_TERMINAL_STATE_TYPES
    return ",".join(chunks)

@config_entries.HANDLERS.register(DOMAIN)
class HeyitechConfigFlow(config_entries.ConfigFlow):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            user_input[CONF_BASE_URL] = _normalize_base_url(user_input[CONF_BASE_URL])
            await self.async_set_unique_id(user_input[CONF_BASE_URL])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Heyitech Alarm", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=CONF_CLOUD_DEFAULT): vol.All(str, _normalize_base_url),
            vol.Required(CONF_USERNAME): vol.All(str, vol.Length(min=1)),
            vol.Required(CONF_PASSWORD): vol.All(str, vol.Length(min=1)),
            vol.Required(CONF_DEVICE_ID): vol.All(str, vol.Length(min=1)),
            vol.Optional(CONF_TIMEZONE, default=DEFAULT_TZ): str,
            vol.Optional(CONF_LANG, default=DEFAULT_LANG): str,
            vol.Optional(CONF_TERMINAL, default=DEFAULT_TERMINAL): str,
            vol.Optional(
                CONF_TERMINAL_STATE_TYPES,
                default=DEFAULT_TERMINAL_STATE_TYPES,
            ): vol.All(str, _normalize_state_types),
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): POLL_INTERVAL_VALIDATOR,
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
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=opts.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): POLL_INTERVAL_VALIDATOR,
            vol.Optional(
                CONF_TERMINAL_STATE_TYPES,
                default=opts.get(CONF_TERMINAL_STATE_TYPES, self._entry.data.get(CONF_TERMINAL_STATE_TYPES, DEFAULT_TERMINAL_STATE_TYPES)),
            ): vol.All(str, _normalize_state_types),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
