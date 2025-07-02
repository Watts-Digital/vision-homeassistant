"""Data coordinator for Watts Vision integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WattsVisionAPI
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WattsVisionCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Watts Vision+ data."""

    def __init__(self, hass: HomeAssistant, api: WattsVisionAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from Watts Vision API."""
        try:
            data = await self.api.async_get_all_devices_data()
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
