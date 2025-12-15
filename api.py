from __future__ import annotations
import asyncio
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
    @staticmethod
    def _validate_response(body: Any, context: str) -> None:
        """Raise HeyitechApiError when the API body clearly indicates failure."""
        if not isinstance(body, dict):
            return
        # Common patterns across similar cloud APIs
        if body.get("success") is False:
            raise HeyitechApiError(f"{context} failed: {body.get('msg') or body.get('message') or body}")

        for key in ("code", "resultCode", "ret", "status"):
            if key not in body:
                continue
            val = body.get(key)
            # Treat 0/200/"0"/"200"/True as success.
            if val in (0, 200, "0", "200", True):
                return
            # If it looks like an error code, raise with best-effort message.
            if val is not None and str(val) not in ("0", "200", "True"):
                msg = body.get("msg") or body.get("message") or body.get("resultMsg") or body.get("error") or body
                raise HeyitechApiError(f"{context} failed ({key}={val}): {msg}")
 
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
        context = "login"
        try:
            async with async_timeout.timeout(15):
                async with self._session.post(url, data=data, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise HeyitechAuthError(f"HTTP {resp.status}: {text}")
                    body = await resp.json(content_type=None)
                    self._validate_response(body, context)
        except asyncio.TimeoutError as err:
            raise HeyitechApiError(f"Timeout during {context}: {err}") from err
        except aiohttp.ClientError as err:
            raise HeyitechApiError(f"Network error during {context}: {err}") from err
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
        context = "get_arm_status"
        try:
            async with async_timeout.timeout(15):
                async with self._session.post(url, data=data, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise HeyitechApiError(f"HTTP {resp.status}: {text}")
                    body = await resp.json(content_type=None)
                    self._validate_response(body, context)
                    return body
        except asyncio.TimeoutError as err:
            raise HeyitechApiError(f"Timeout during {context}: {err}") from err
        except aiohttp.ClientError as err:
            raise HeyitechApiError(f"Network error during {context}: {err}") from err

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
        context = "remote_control"
        try:
            async with async_timeout.timeout(15):
                async with self._session.post(url, data=data, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise HeyitechApiError(f"HTTP {resp.status}: {text}")
                    body = await resp.json(content_type=None)
                    self._validate_response(body, context)
                    return body
        except asyncio.TimeoutError as err:
            raise HeyitechApiError(f"Timeout during {context}: {err}") from err
        except aiohttp.ClientError as err:
            raise HeyitechApiError(f"Network error during {context}: {err}") from err
