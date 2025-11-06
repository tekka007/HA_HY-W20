from __future__ import annotations

import json
import logging
from typing import Any, Dict

import aiohttp
import async_timeout

from .const import LOGIN_PATH, GET_ARM_STATUS_PATH, REMOTE_CONTROL_PATH

_LOGGER = logging.getLogger(__name__)


class HeyitechApiError(Exception):
    """Base API error."""


class HeyitechAuthError(HeyitechApiError):
    """Authentication/authorization error."""


class HeyitechClient:
    """Thin async client for Heyitech cloud (token-per-request)."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str) -> None:
        self._session = session
        self._base = base_url.rstrip("/")

    async def _login(self, username: str, password: str, terminal: str, lang: str, tz: str) -> str:
        url = f"{self._base}{LOGIN_PATH}"
        payload = {
            "loginName": username,
            "terminalType": terminal,
            "languageType": lang,
            "loginPwd": password,
            "timeZone": tz,
        }
        data = {"requestJson": json.dumps(payload)}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _LOGGER.debug("Heyitech login POST %s", url)
        try:
            async with async_timeout.timeout(15):
                async with self._session.post(url, data=data, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise HeyitechAuthError(f"HTTP {resp.status}: {text}")
                    body = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise HeyitechApiError(f"Network error during login: {err}") from err

        token = body.get("tokenId")
        if not token:
            raise HeyitechAuthError(f"Login succeeded but no tokenId returned: {body}")
        return token

    async def get_arm_status(
        self,
        username: str,
        password: str,
        terminal: str,
        lang: str,
        tz: str,
        device_id: str,
    ) -> Dict[str, Any]:
        token = await self._login(username, password, terminal, lang, tz)

        url = f"{self._base}{GET_ARM_STATUS_PATH}"
        req = {"tokenId": token, "deviceID": device_id}
        data = {"requestJson": json.dumps(req)}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _LOGGER.debug("Heyitech get_arm_status POST %s (device %s)", url, device_id)
        try:
            async with async_timeout.timeout(15):
                async with self._session.post(url, data=data, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise HeyitechApiError(f"HTTP {resp.status}: {text}")
                    return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise HeyitechApiError(f"Network error during get_arm_status: {err}") from err

    async def remote_control(
        self,
        username: str,
        password: str,
        terminal: str,
        lang: str,
        tz: str,
        device_id: str,
        control_type: int,
        order_no: str = "0",
    ) -> Dict[str, Any]:
        token = await self._login(username, password, terminal, lang, tz)

        url = f"{self._base}{REMOTE_CONTROL_PATH}"
        req = {
            "tokenId": token,
            "orderNO": str(order_no),
            "deviceID": device_id,
            "controlType": int(control_type),
        }
        data = {"requestJson": json.dumps(req)}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _LOGGER.debug(
            "Heyitech remote_control POST %s (device %s, controlType %s)",
            url, device_id, control_type
        )
        try:
            async with async_timeout.timeout(15):
                async with self._session.post(url, data=data, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise HeyitechApiError(f"HTTP {resp.status}: {text}")
                    return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise HeyitechApiError(f"Network error during remote_control: {err}") from err
