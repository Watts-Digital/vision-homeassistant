"""Tests for the Watts Vision switch platform."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.watts.coordinator import WattsVisionCoordinator
from custom_components.watts.switch import WattsVisionSwitch, async_setup_entry
import pytest
from pywattsvision.pywattsvision import SwitchDevice, ThermostatDevice

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


@pytest.fixture
def mock_device():
    """Watts Vision switch mock."""
    device = MagicMock(spec=SwitchDevice)
    device.device_id = "switch_123"
    device.device_name = "Test Switch"
    device.is_turned_on = True
    device.is_online = True
    device.device_type = "switch"
    device.room_name = "Bedroom"
    return device


@pytest.fixture
def mock_coordinator(mock_device):
    """Mock coordinator with a single device."""
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.data = {mock_device.device_id: mock_device}
    coordinator.client = MagicMock()
    coordinator.client.set_switch_state = AsyncMock()
    return coordinator


@pytest.fixture
def switch_entity(mock_coordinator, mock_device):
    """Create a switch entity instance."""
    return WattsVisionSwitch(mock_coordinator, mock_device)


@pytest.mark.asyncio
async def test_turn_on(switch_entity, mock_coordinator, mock_device) -> None:
    """Test switch turn on."""
    await switch_entity.async_turn_on()
    mock_coordinator.client.set_switch_state.assert_called_once_with(
        mock_device.device_id, True
    )


@pytest.mark.asyncio
async def test_turn_off(switch_entity, mock_coordinator, mock_device) -> None:
    """Test switch turn off."""
    await switch_entity.async_turn_off()
    mock_coordinator.client.set_switch_state.assert_called_once_with(
        mock_device.device_id, False
    )


def test_is_on(switch_entity) -> None:
    """Test is_on property."""
    assert switch_entity.is_on is True


def test_extra_state_attributes(switch_entity) -> None:
    """Test extra state attributes."""
    attrs = switch_entity.extra_state_attributes
    assert attrs["device_type"] == "switch"
    assert attrs["room_name"] == "Bedroom"


@pytest.mark.asyncio
async def test_async_setup_entry_with_switch_devices() -> None:
    """Test setup entry with switch devices."""
    hass = MagicMock(spec=HomeAssistant)
    entry = MagicMock(spec=ConfigEntry)
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock()
    switch_device = MagicMock(spec=SwitchDevice)
    switch_device.device_id = "switch_1"
    switch_device.device_name = "Test Switch 1"
    switch_device.is_turned_on = True
    switch_device.is_online = True
    switch_device.device_type = "switch"
    switch_device.room_name = "Living Room"
    coordinator.data = {"switch_1": switch_device}
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WattsVisionSwitch)
    assert args[1]["update_before_add"] is True


@pytest.mark.asyncio
async def test_async_setup_entry_no_switch_devices() -> None:
    """Test setup entry with no switch devices (only thermostat devices)."""
    hass = MagicMock(spec=HomeAssistant)
    entry = MagicMock(spec=ConfigEntry)
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock()
    thermostat_device = MagicMock(spec=ThermostatDevice)
    thermostat_device.device_id = "thermostat_1"
    thermostat_device.device_name = "Test Thermostat"
    thermostat_device.current_temperature = 20.0
    thermostat_device.setpoint = 22.0
    thermostat_device.thermostat_mode = "Comfort"
    thermostat_device.min_allowed_temperature = 5.0
    thermostat_device.max_allowed_temperature = 30.0
    thermostat_device.temperature_unit = "C"
    thermostat_device.is_online = True
    thermostat_device.device_type = "thermostat"
    thermostat_device.room_name = "Kitchen"
    thermostat_device.available_thermostat_modes = ["Program", "Eco", "Comfort", "Off"]

    coordinator.data = {"thermostat_1": thermostat_device}
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


def test_switch_initialization(mock_coordinator, mock_device) -> None:
    """Test switch entity initialization."""
    switch = WattsVisionSwitch(mock_coordinator, mock_device)

    assert switch._device == mock_device
    assert switch._attr_unique_id == "switch_123"
    assert switch._attr_name == "Test Switch"
    assert switch._attr_device_info["identifiers"] == {("watts", "switch_123")}
    assert switch._attr_device_info["name"] == "Test Switch"
    assert switch._attr_device_info["manufacturer"] == "Watts"
    assert switch._attr_device_info["model"] == "Vision+ Switch"


@pytest.mark.asyncio
async def test_turn_on_error(switch_entity, mock_coordinator, mock_device) -> None:
    """Test turn on with error handling."""
    mock_coordinator.client.set_switch_state.side_effect = RuntimeError("API Error")

    with patch("custom_components.watts.switch._LOGGER") as mock_logger:
        await switch_entity.async_turn_on()
        mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_turn_off_error(switch_entity, mock_coordinator, mock_device) -> None:
    """Test turn off with error handling."""
    mock_coordinator.client.set_switch_state.side_effect = RuntimeError("API Error")

    with patch("custom_components.watts.switch._LOGGER") as mock_logger:
        await switch_entity.async_turn_off()
        mock_logger.error.assert_called_once()


def test_is_on_false(switch_entity, mock_coordinator, mock_device) -> None:
    """Test is_on property when switch is off."""
    mock_device.is_turned_on = False
    assert switch_entity.is_on is False


def test_is_on_device_not_found(switch_entity, mock_coordinator) -> None:
    """Test is_on property when device is not found."""
    mock_coordinator.data = {}
    assert switch_entity.is_on is None


def test_available_true(switch_entity) -> None:
    """Test available property when device is online."""
    assert switch_entity.available is True


def test_available_false(switch_entity, mock_coordinator, mock_device) -> None:
    """Test available property when device is offline."""
    mock_device.is_online = False
    assert switch_entity.available is False


def test_available_device_not_found(switch_entity, mock_coordinator) -> None:
    """Test available property when device is not found."""
    mock_coordinator.data = {}
    assert switch_entity.available is False
