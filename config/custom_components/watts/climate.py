"""Climate platform for Watts Vision integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WattsVisionAPI
from .const import (
    DEFAULT_MAX_SETPOINT,
    DEFAULT_MIN_SETPOINT,
    DOMAIN,
    INTERFACE_THERMOSTAT,
)
from .coordinator import WattsVisionCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Watts Vision climate entities from a config entry."""
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

    # Create climate entities for thermostat devices
    entities = []
    for device_id, device_data in coordinator.data.items():
        if device_data.get("interface") == INTERFACE_THERMOSTAT:
            entities.append(WattsVisionClimate(coordinator, device_id, device_data))
            _LOGGER.debug("Created climate entity for device %s", device_id)

    if entities:
        async_add_entities(entities, update_before_add=True)
        _LOGGER.info("Added %d climate entities", len(entities))


class WattsVisionClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Watts Vision heater as a climate entity."""

    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]

    def __init__(
        self,
        coordinator: WattsVisionCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = device_id
        self._attr_name = device_data["friendlyName"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_data["friendlyName"],
            "manufacturer": "Watts",
            "model": "Vision+ Thermostat",
        }

        # Set temperature limits from device data
        self._attr_min_temp = device_data.get(
            "minAllowedTemperature", DEFAULT_MIN_SETPOINT
        )
        self._attr_max_temp = device_data.get(
            "maxAllowedTemperature", DEFAULT_MAX_SETPOINT
        )

        # Store API reference for write operations
        self._api = coordinator.api

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        device_data = self.coordinator.data.get(self._device_id)
        if device_data:
            return device_data.get("currentTemperature")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        device_data = self.coordinator.data.get(self._device_id)
        if device_data:
            return device_data.get("setpoint")
        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        device_data = self.coordinator.data.get(self._device_id)
        if device_data:
            thermostat_mode = device_data.get("thermostatMode")

            mode_mapping = {
                "Program": HVACMode.AUTO,
                "Eco": HVACMode.HEAT,
                "Comfort": HVACMode.HEAT,
                "Off": HVACMode.OFF,
            }

            return mode_mapping.get(thermostat_mode)
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
            "thermostat_mode": device_data.get("thermostatMode"),
            "device_type": device_data.get("deviceType"),
            "room_name": device_data.get("roomName"),
            "description": device_data.get("description"),
            "temperature_unit": device_data.get("temperatureUnit"),
            "available_thermostat_modes": device_data.get(
                "availableThermostatModes", []
            ),
            "supports_proactive_reporting": device_data.get(
                "supportsProactiveReporting"
            ),
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            await self._api.async_set_thermostat_temperature(
                self._device_id, temperature
            )
            _LOGGER.debug(
                "Successfully set temperature to %s for %s", temperature, self.name
            )
            # Force refresh
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting temperature for %s: %s", self.name, err)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""

        hvac_to_mode_number = {
            HVACMode.HEAT: 1,  # Comfort
            HVACMode.OFF: 2,  # Off
            HVACMode.AUTO: 6,  # Program
        }

        mode_number = hvac_to_mode_number.get(hvac_mode)
        if mode_number is None:
            _LOGGER.error("Unsupported HVAC mode %s for %s", hvac_mode, self.name)
            return

        try:
            await self._api.async_set_thermostat_mode(self._device_id, mode_number)
            _LOGGER.debug(
                "Successfully set HVAC mode to %s for %s", hvac_mode, self.name
            )
            # Force refresh
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting HVAC mode for %s: %s", self.name, err)
