"""API for Watts Vision+."""

from __future__ import annotations

from typing import Any

import aiohttp

from homeassistant.helpers import config_entry_oauth2_flow

from .const import API_BASE_URL


class AsyncConfigEntryAuth:
    """Provide Watts Vision+ APIs authentication."""

    def __init__(
        self,
        websession: aiohttp.ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize Watts Vision+ auth."""
        self._websession = websession
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        await self._oauth_session.async_ensure_token_valid()
        return self._oauth_session.token["access_token"]


class WattsVisionAPI:
    """Watts Vision API client."""

    def __init__(self, auth: AsyncConfigEntryAuth) -> None:
        """Initialize the API client."""
        self._auth = auth

    async def make_request(
        self, method: str, url: str, json_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to the API."""
        token = await self._auth.async_get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with self._auth._websession.request(
            method, url, headers=headers, json=json_data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def async_discover_devices(self) -> list[dict[str, Any]]:
        """Discover all devices."""
        url = f"{API_BASE_URL}/voice-control/discover/Google"
        data = await self.make_request("GET", url)
        return data.get("devices", [])

    async def async_get_device_report(self, device_id: str) -> dict[str, Any]:
        """Get device report data."""
        url = f"{API_BASE_URL}/voice-control/report/Google/{device_id}"
        return await self.make_request("GET", url)

    async def async_get_all_devices_data(self) -> dict:
        """Fetches all devices and subdevices data."""
        devices_data = {}
        devices = await self.async_discover_devices()

        for device in devices:
            device_id = device["deviceId"]
            report = await self.async_get_device_report(device_id)
            devices_data[device_id] = {**device, **report}

        return devices_data

    async def async_set_thermostat_temperature(
        self, device_id: str, temperature: float
    ) -> dict[str, Any]:
        """Set thermostat setpoint."""
        url = f"{API_BASE_URL}/voice-control/control/thermostat/Google/{device_id}/set-temperature"
        payload = {"targetTemperature": temperature}
        return await self.make_request("POST", url, payload)

    async def async_set_thermostat_mode(
        self, device_id: str, mode: int
    ) -> dict[str, Any]:
        """Set thermostat mode."""
        url = f"{API_BASE_URL}/voice-control/control/thermostat/Google/{device_id}/set-mode"
        payload = {"mode": mode}
        return await self.make_request("POST", url, payload)

    async def async_set_switch_state(
        self, device_id: str, is_on: bool
    ) -> dict[str, Any]:
        """Set on/off state."""
        url = f"{API_BASE_URL}/voice-control/control/on-off/Google/{device_id}/change-state"
        payload = {"isTurnedOn": is_on}
        return await self.make_request("POST", url, payload)
