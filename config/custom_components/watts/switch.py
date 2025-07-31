"""Switch platform for Watts Vision integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pywattsvision.pywattsvision import SwitchDevice

from .const import DOMAIN
from .coordinator import WattsVisionCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Watts Vision switch entities from a config entry."""
    coordinator = entry.runtime_data["coordinator"]

    # Create switch entities
    entities = []
    for device in coordinator.data.values():
        if isinstance(device, SwitchDevice):
            entities.append(WattsVisionSwitch(coordinator, device))
            _LOGGER.debug("Created switch entity for device %s", device.device_id)

    if entities:
        async_add_entities(entities, update_before_add=True)
        _LOGGER.info("Added %d switch entities", len(entities))


class WattsVisionSwitch(CoordinatorEntity, SwitchEntity):
    """Watts Vision switch device as a switch entity."""

    def __init__(
        self,
        coordinator: WattsVisionCoordinator,
        device: SwitchDevice,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = device.device_id
        self._attr_name = device.device_name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.device_id)},
            "name": device.device_name,
            "manufacturer": "Watts",
            "model": "Vision+ Switch",
        }

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        device = self.coordinator.data.get(self._device.device_id)
        if isinstance(device, SwitchDevice):
            return device.is_turned_on
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is online."""
        device = self.coordinator.data.get(self._device.device_id)
        if device:
            return device.is_online
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.data.get(self._device.device_id)
        if not isinstance(device, SwitchDevice):
            return {}
        return {"device_type": device.device_type, "room_name": device.room_name}

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.coordinator.client.set_switch_state(self._device.device_id, True)
        except RuntimeError as err:
            _LOGGER.error("Error turning on switch %s: %s", self.name, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.coordinator.client.set_switch_state(
                self._device.device_id, False
            )
            _LOGGER.debug("Successfully turned off switch %s", self.name)
        except RuntimeError as err:
            _LOGGER.error("Error turning off switch %s: %s", self.name, err)
