"""Tests for the Watts Vision climate platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from visionpluspython.visionpluspython import SwitchDevice, ThermostatDevice

from homeassistant.components.climate import HVACMode
from homeassistant.components.watts.climate import WattsVisionClimate, async_setup_entry
from homeassistant.components.watts.coordinator import WattsVisionCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from tests.common import MockConfigEntry


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(domain="watts")


@pytest.fixture
def mock_thermostat_device():
    """Mock Watts Vision thermostat device."""
    device = MagicMock(spec=ThermostatDevice)
    device.device_id = "thermostat_123"
    device.device_name = "Test Thermostat"
    device.current_temperature = 20.5
    device.setpoint = 22.0
    device.thermostat_mode = "Comfort"
    device.min_allowed_temperature = 5.0
    device.max_allowed_temperature = 30.0
    device.temperature_unit = "C"
    device.is_online = True
    device.device_type = "thermostat"
    device.room_name = "Living Room"
    device.available_thermostat_modes = [
        "Program",
        "Eco",
        "Comfort",
        "Off",
        "Defrost",
        "Timer",
    ]
    return device


@pytest.fixture
def mock_switch_device():
    """Mock Watts Vision switch device."""
    device = MagicMock(spec=SwitchDevice)
    device.device_id = "switch_123"
    device.device_name = "Test Switch"
    device.is_turned_on = True
    device.is_online = True
    device.device_type = "switch"
    device.room_name = "Kitchen"
    return device


@pytest.fixture
def mock_coordinator(mock_thermostat_device):
    """Mock coordinator with a single thermostat device."""
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.data = {mock_thermostat_device.device_id: mock_thermostat_device}
    coordinator.client = MagicMock()
    coordinator.client.set_thermostat_temperature = AsyncMock()
    coordinator.client.set_thermostat_mode = AsyncMock()
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def climate_entity(mock_coordinator, mock_thermostat_device):
    """Create a climate entity instance."""
    return WattsVisionClimate(mock_coordinator, mock_thermostat_device)


async def test_climate_initialization(mock_coordinator, mock_thermostat_device) -> None:
    """Test climate entity initialization."""
    # Ensure coordinator.data is properly set before creating the entity
    mock_coordinator.data = {mock_thermostat_device.device_id: mock_thermostat_device}
    climate = WattsVisionClimate(mock_coordinator, mock_thermostat_device)

    assert climate._device == mock_thermostat_device
    assert climate._attr_unique_id == "thermostat_123"

    # Check device_info property directly to ensure it's not None
    device_info = climate.device_info
    assert device_info is not None
    assert device_info["identifiers"] == {("watts", "thermostat_123")}
    assert device_info["name"] == "Test Thermostat"
    assert device_info["manufacturer"] == "Watts"
    assert device_info["model"] == "Vision+ thermostat"

    # Check temperature limits and unit
    assert climate._attr_min_temp == 5.0
    assert climate._attr_max_temp == 30.0
    assert climate._attr_temperature_unit == "°C"


def test_current_temperature(climate_entity) -> None:
    """Test current temperature property."""
    assert climate_entity.current_temperature == 20.5


def test_current_temperature_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test current temperature when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.current_temperature is None


def test_target_temperature(climate_entity) -> None:
    """Test target temperature property."""
    assert climate_entity.target_temperature == 22.0


def test_target_temperature_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test target temperature when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.target_temperature is None


def test_hvac_mode_comfort(climate_entity) -> None:
    """Test HVAC mode property for Comfort mode."""
    assert climate_entity.hvac_mode == HVACMode.HEAT


def test_hvac_mode_eco(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode mapping for Eco mode."""
    mock_thermostat_device.thermostat_mode = "Eco"
    assert climate_entity.hvac_mode == HVACMode.HEAT


def test_hvac_mode_program(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode mapping for Program mode."""
    mock_thermostat_device.thermostat_mode = "Program"
    assert climate_entity.hvac_mode == HVACMode.AUTO


def test_hvac_mode_off(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode mapping for Off mode."""
    mock_thermostat_device.thermostat_mode = "Off"
    assert climate_entity.hvac_mode == HVACMode.OFF


def test_hvac_mode_unknown(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode mapping for unknown mode."""
    mock_thermostat_device.thermostat_mode = "Unknown"
    assert climate_entity.hvac_mode is None


def test_hvac_mode_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test HVAC mode when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.hvac_mode is None


def test_extra_state_attributes(climate_entity) -> None:
    """Test extra state attributes."""
    attrs = climate_entity.extra_state_attributes
    assert attrs["thermostat_mode"] == "Comfort"
    assert attrs["device_type"] == "thermostat"
    assert attrs["room_name"] == "Living Room"
    assert attrs["temperature_unit"] == "C"
    assert attrs["available_thermostat_modes"] == [
        "Program",
        "Eco",
        "Comfort",
        "Off",
        "Defrost",
        "Timer",
    ]


def test_extra_state_attributes_device_not_found(
    climate_entity, mock_coordinator
) -> None:
    """Test extra state attributes when device is not found."""
    mock_coordinator.data = {}
    attrs = climate_entity.extra_state_attributes
    assert attrs == {}


def test_available_true(climate_entity, mock_coordinator) -> None:
    """Test available property when device is online."""
    mock_coordinator.last_update_success = True
    assert climate_entity.available is True


def test_available_false_offline(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test available property when device is offline."""
    mock_coordinator.last_update_success = True
    mock_thermostat_device.is_online = False
    assert climate_entity.available is False


def test_available_false_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test available property when device is not found."""
    mock_coordinator.last_update_success = True
    mock_coordinator.data = {}
    assert climate_entity.available is False


async def test_set_temperature_success(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test temperature setting success."""
    await climate_entity.async_set_temperature(temperature=23.5)
    mock_coordinator.client.set_thermostat_temperature.assert_called_once_with(
        mock_thermostat_device.device_id, 23.5
    )


async def test_set_temperature_with_attr_temperature(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test temperature setting using ATTR_TEMPERATURE."""
    await climate_entity.async_set_temperature(**{ATTR_TEMPERATURE: 24.0})
    mock_coordinator.client.set_thermostat_temperature.assert_called_once_with(
        mock_thermostat_device.device_id, 24.0
    )


async def test_set_temperature_no_temperature(climate_entity, mock_coordinator) -> None:
    """Test temperature setting without temperature parameter."""
    await climate_entity.async_set_temperature()
    mock_coordinator.client.set_thermostat_temperature.assert_not_called()


async def test_set_temperature_error(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test temperature setting with error handling."""
    mock_coordinator.client.set_thermostat_temperature.side_effect = RuntimeError(
        "API Error"
    )

    # Test that the method doesn't raise an exception (error is handled internally)
    await climate_entity.async_set_temperature(temperature=25.0)

    # Verify the API was called despite the error
    mock_coordinator.client.set_thermostat_temperature.assert_called_once_with(
        mock_thermostat_device.device_id, 25.0
    )


async def test_set_hvac_mode_heat_success(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode setting to heat."""
    await climate_entity.async_set_hvac_mode(HVACMode.HEAT)
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_thermostat_device.device_id, "Comfort"
    )


async def test_set_hvac_mode_off_success(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode setting to off."""
    await climate_entity.async_set_hvac_mode(HVACMode.OFF)
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_thermostat_device.device_id, "Off"
    )


async def test_set_hvac_mode_auto_success(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode setting to auto."""
    await climate_entity.async_set_hvac_mode(HVACMode.AUTO)
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_thermostat_device.device_id, "Program"
    )


async def test_set_hvac_mode_unsupported(climate_entity, mock_coordinator) -> None:
    """Test setting unsupported HVAC mode."""
    # Test that the method doesn't raise an exception (error is handled internally)
    await climate_entity.async_set_hvac_mode(HVACMode.COOL)

    # Verify the API was not called for unsupported mode
    mock_coordinator.client.set_thermostat_mode.assert_not_called()


async def test_set_hvac_mode_error(
    climate_entity, mock_coordinator, mock_thermostat_device
) -> None:
    """Test HVAC mode setting with error handling."""
    mock_coordinator.client.set_thermostat_mode.side_effect = RuntimeError("API Error")

    # Test that the method doesn't raise an exception (error is handled internally)
    await climate_entity.async_set_hvac_mode(HVACMode.HEAT)

    # Verify the API was called despite the error
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_thermostat_device.device_id, "Comfort"
    )


async def test_async_setup_entry_with_thermostat_devices(
    mock_hass, mock_config_entry
) -> None:
    """Test setup entry with thermostat devices."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    # Create mock coordinator with thermostat device
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True

    thermostat_device = MagicMock(spec=ThermostatDevice)
    thermostat_device.device_id = "thermostat_1"
    thermostat_device.device_name = "Test Thermostat 1"
    thermostat_device.current_temperature = 21.0
    thermostat_device.setpoint = 23.0
    thermostat_device.thermostat_mode = "Program"
    thermostat_device.min_allowed_temperature = 5.0
    thermostat_device.max_allowed_temperature = 30.0
    thermostat_device.temperature_unit = "C"
    thermostat_device.is_online = True
    thermostat_device.device_type = "thermostat"
    thermostat_device.room_name = "Bedroom"
    thermostat_device.available_thermostat_modes = ["Program", "Eco", "Comfort", "Off"]

    coordinator.data = {"thermostat_1": thermostat_device}

    # Create mock config entry with runtime data
    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WattsVisionClimate)
    assert args[1]["update_before_add"] is True


async def test_async_setup_entry_no_thermostat_devices(
    mock_hass, mock_config_entry, mock_switch_device
) -> None:
    """Test setup entry with no thermostat devices (only switch devices)."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    # Create mock coordinator with only switch device
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator.data = {"switch_1": mock_switch_device}

    # Create mock config entry with runtime data
    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


async def test_async_setup_entry_empty_data(mock_hass, mock_config_entry) -> None:
    """Test setup entry with empty coordinator data."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    # Create mock coordinator with empty data
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator.data = {}

    # Create mock config entry with runtime data
    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


async def test_async_setup_entry_multiple_thermostat_devices(
    mock_hass, mock_config_entry
) -> None:
    """Test setup entry with multiple thermostat devices."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    # Create mock coordinator with multiple thermostat devices
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True

    thermostat1 = MagicMock(spec=ThermostatDevice)
    thermostat1.device_id = "thermostat_1"
    thermostat1.device_name = "Thermostat 1"

    thermostat2 = MagicMock(spec=ThermostatDevice)
    thermostat2.device_id = "thermostat_2"
    thermostat2.device_name = "Thermostat 2"

    coordinator.data = {"thermostat_1": thermostat1, "thermostat_2": thermostat2}

    # Create mock config entry with runtime data
    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 2
    assert all(isinstance(entity, WattsVisionClimate) for entity in entities)
    assert args[1]["update_before_add"] is True


async def test_async_setup_entry_mixed_devices(
    mock_hass, mock_config_entry, mock_switch_device
) -> None:
    """Test setup entry with mixed device types."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    # Create mock coordinator with mixed devices
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True

    thermostat_device = MagicMock(spec=ThermostatDevice)
    thermostat_device.device_id = "thermostat_1"
    thermostat_device.device_name = "Test Thermostat"

    coordinator.data = {
        "thermostat_1": thermostat_device,
        "switch_1": mock_switch_device,
    }

    # Create mock config entry with runtime data
    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    # Only thermostat entities should be created
    assert len(entities) == 1
    assert isinstance(entities[0], WattsVisionClimate)
    assert args[1]["update_before_add"] is True
