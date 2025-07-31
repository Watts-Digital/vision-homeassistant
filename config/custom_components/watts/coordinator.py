"""Data coordinator for Watts Vision integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import pywattsvision

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WattsVisionCoordinator(DataUpdateCoordinator):
    """Class to fetch Watts Vision+ data."""

    def __init__(
        self, hass: HomeAssistant, client: pywattsvision.WattsVisionClient
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, pywattsvision.Device]:
        """Fetch data from Watts Vision API."""
        try:
            return await self.client.get_all_devices_data()
        except Exception as err:
            raise UpdateFailed(f"API error: {err}") from err
