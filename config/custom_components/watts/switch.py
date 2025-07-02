"""Switch platform for Watts Vision integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WattsVisionAPI
from .const import DOMAIN, INTERFACE_SWITCH
from .coordinator import WattsVisionCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Watts Vision switch entities from a config entry."""
    auth = entry.runtime_data
    api = WattsVisionAPI(auth)

    # Create coordinator
    coordinator_key = f"{DOMAIN}_coordinator"

    if coordinator_key not in hass.data:
        coordinator = WattsVisionCoordinator(hass, api)
        await coordinator.async_config_entry_first_refresh()
        hass.data[coordinator_key] = coordinator
        _LOGGER.debug("Created new coordinator")
    else:
        coordinator = hass.data[coordinator_key]
        _LOGGER.debug("Using existing coordinator")

    # Create switch entities for ON/OFF devices
    entities = []
    for device_id, device_data in coordinator.data.items():
        if device_data.get("interface") == INTERFACE_SWITCH:
            entities.append(WattsVisionSwitch(coordinator, device_id, device_data))
            _LOGGER.debug("Created switch entity for device %s", device_id)

    if entities:
        async_add_entities(entities, update_before_add=True)
        _LOGGER.info("Added %d switch entities", len(entities))


class WattsVisionSwitch(CoordinatorEntity, SwitchEntity):
    """Watts Vision ON/OFF device as a switch entity."""

    def __init__(
        self,
        coordinator: WattsVisionCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = device_id
        self._attr_name = device_data["friendlyName"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_data["friendlyName"],
            "manufacturer": "Watts",
            "model": "Vision+ Switch",
        }
        # Store API reference for write operations
        self._api = coordinator.api

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        device_data = self.coordinator.data.get(self._device_id)
        if device_data:
            _LOGGER.debug("SWITCH STATE: %s", device_data.get("isTurnedOn", False))
            return device_data.get("isTurnedOn", False)
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        device_data = self.coordinator.data.get(self._device_id)
        if device_data:
            return device_data.get("isOnline", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device_data = self.coordinator.data.get(self._device_id)
        if not device_data:
            return {}

        return {
            "device_type": device_data.get("deviceType"),
            "room_name": device_data.get("roomName"),
            "description": device_data.get("description"),
            "supports_proactive_reporting": device_data.get(
                "supportsProactiveReporting"
            ),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self._api.async_set_switch_state(self._device_id, True)
            _LOGGER.debug("Successfully turned on switch %s", self.name)
            # Force refresh
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning on switch %s: %s", self.name, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self._api.async_set_switch_state(self._device_id, False)
            _LOGGER.debug("Successfully turned off switch %s", self.name)
            # Force refresh
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning off switch %s: %s", self.name, err)
