"""Switch platform for Watts Vision integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pywattsvision.pywattsvision import SwitchDevice

from .coordinator import WattsVisionCoordinator
from .entity import WattsVisionEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Watts Vision switch entities from a config entry."""
    coordinator: WattsVisionCoordinator = entry.runtime_data["coordinator"]

    # Create switch entities
    entities = []
    for device in coordinator.data.values():
        if isinstance(device, SwitchDevice):
            entities.append(WattsVisionSwitch(coordinator, device))
            _LOGGER.debug("Created switch entity for device %s", device.device_id)

    if entities:
        async_add_entities(entities, update_before_add=True)
        _LOGGER.info("Added %d switch entities", len(entities))


class WattsVisionSwitch(WattsVisionEntity, SwitchEntity):
    """Watts Vision switch device as a switch entity."""

    _entity_name = "Switch"

    def __init__(
        self,
        coordinator: WattsVisionCoordinator,
        device: SwitchDevice,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator, device.device_id)
        self._device = device

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        device = self.coordinator.data.get(self._device.device_id)
        if isinstance(device, SwitchDevice):
            return device.is_turned_on
        return None

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
            _LOGGER.debug("Successfully turned on switch %s", self._attr_name)
        except RuntimeError as err:
            _LOGGER.error("Error turning on switch %s: %s", self._attr_name, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.coordinator.client.set_switch_state(
                self._device.device_id, False
            )
            _LOGGER.debug("Successfully turned off switch %s", self._attr_name)
        except RuntimeError as err:
            _LOGGER.error("Error turning off switch %s: %s", self._attr_name, err)
