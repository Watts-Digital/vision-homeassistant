"""Data coordinator for Watts Vision integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from visionpluspython.visionpluspython import Device, WattsVisionClient

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WattsVisionCoordinator(DataUpdateCoordinator):
    """Class to fetch Watts Vision+ data."""

    def __init__(self, hass: HomeAssistant, client: WattsVisionClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.client = client
        self._devices: dict[str, Device] = {}
        self._is_initialized = False

    async def async_config_entry_first_refresh(self) -> None:
        """Perform initial discovery of devices."""
        try:
            devices_list = await self.client.discover_devices()
            self._devices = {device.device_id: device for device in devices_list}
            self._is_initialized = True
            _LOGGER.info(
                "Initial discovery completed with %d devices", len(self._devices)
            )

            self.async_set_updated_data(self._devices)

        except Exception as err:
            _LOGGER.error("Initial device discovery failed: %s", err)
            raise UpdateFailed(f"Initial discovery failed: {err}") from err

    async def async_refresh_device(self, device_id: str) -> None:
        """Refresh a specific device."""
        try:
            device = await self.client.get_device(device_id, refresh=True)
            if device:
                self._devices[device_id] = device
                self.async_set_updated_data(self._devices)
                _LOGGER.debug("Refreshed device %s", device_id)
        except (RuntimeError, ValueError, TypeError) as err:
            _LOGGER.error("Failed to refresh device %s: %s", device_id, err)

    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch data from Watts Vision API."""
        try:
            # If not initialized, perform discovery first
            if not self._is_initialized:
                await self.async_config_entry_first_refresh()
                return self._devices

            device_ids = list(self._devices.keys())

            if not device_ids:
                _LOGGER.warning("No devices to update")
                return self._devices

            updated_devices = await self.client.get_devices_report(device_ids)

            for device_id, device in updated_devices.items():
                self._devices[device_id] = device

            _LOGGER.debug("Updated %d devices", len(updated_devices))

        except Exception as err:
            if isinstance(err, UpdateFailed):
                raise
            raise UpdateFailed(f"API error during devices update: {err}") from err
        else:
            return self._devices

    @property
    def device_ids(self) -> list[str]:
        """Get list of all device IDs."""
        return list(self._devices.keys())
