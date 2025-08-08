"""Tests for the Watts Vision switch platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from visionpluspython.visionpluspython import SwitchDevice, ThermostatDevice

from homeassistant.components.watts.coordinator import WattsVisionCoordinator
from homeassistant.components.watts.switch import WattsVisionSwitch, async_setup_entry
from homeassistant.config_entries import ConfigEntry
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
def mock_switch_device():
    """Mock Watts Vision switch device."""
    device = MagicMock(spec=SwitchDevice)
    device.device_id = "switch_123"
    device.device_name = "Test Switch"
    device.is_turned_on = True
    device.is_online = True
    device.device_type = "switch"
    device.room_name = "Bedroom"
    return device


@pytest.fixture
def mock_thermostat_device():
    """Mock Watts Vision thermostat device."""
    device = MagicMock(spec=ThermostatDevice)
    device.device_id = "thermostat_123"
    device.device_name = "Test Thermostat"
    device.current_temperature = 20.0
    device.setpoint = 22.0
    device.thermostat_mode = "Comfort"
    device.min_allowed_temperature = 5.0
    device.max_allowed_temperature = 30.0
    device.temperature_unit = "C"
    device.is_online = True
    device.device_type = "thermostat"
    device.room_name = "Kitchen"
    device.available_thermostat_modes = ["Program", "Eco", "Comfort", "Off"]
    return device


@pytest.fixture
def mock_coordinator(mock_switch_device):
    """Mock coordinator with a single switch device."""
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.data = {mock_switch_device.device_id: mock_switch_device}
    coordinator.client = MagicMock()
    coordinator.client.set_switch_state = AsyncMock()
    coordinator.last_update_success = True
    coordinator._devices = {mock_switch_device.device_id: mock_switch_device}
    coordinator._is_initialized = True
    return coordinator


@pytest.fixture
def switch_entity(mock_coordinator, mock_switch_device):
    """Create a switch entity instance."""
    return WattsVisionSwitch(mock_coordinator, mock_switch_device)


async def test_switch_initialization(mock_coordinator, mock_switch_device) -> None:
    """Test switch entity initialization."""

    mock_coordinator.data = {mock_switch_device.device_id: mock_switch_device}
    switch = WattsVisionSwitch(mock_coordinator, mock_switch_device)

    assert switch._device == mock_switch_device
    assert switch._attr_unique_id == "switch_123"

    device_info = switch.device_info
    assert device_info is not None
    assert device_info["identifiers"] == {("watts", "switch_123")}
    assert device_info["name"] == "Test Switch"
    assert device_info["manufacturer"] == "Watts"
    assert device_info["model"] == "Vision+ switch"


async def test_switch_is_on_true(switch_entity) -> None:
    """Test is_on property when switch is on."""
    assert switch_entity.is_on is True


async def test_switch_is_on_false(
    switch_entity, mock_coordinator, mock_switch_device
) -> None:
    """Test is_on property when switch is off."""
    mock_switch_device.is_turned_on = False
    assert switch_entity.is_on is False


async def test_switch_is_on_device_not_found(switch_entity, mock_coordinator) -> None:
    """Test is_on property when device is not found."""
    mock_coordinator.data = {}
    assert switch_entity.is_on is None


async def test_switch_extra_state_attributes(switch_entity) -> None:
    """Test extra state attributes."""
    attrs = switch_entity.extra_state_attributes
    assert attrs["device_type"] == "switch"
    assert attrs["room_name"] == "Bedroom"


async def test_switch_extra_state_attributes_device_not_found(
    switch_entity, mock_coordinator
) -> None:
    """Test extra state attributes when device is not found."""
    mock_coordinator.data = {}
    attrs = switch_entity.extra_state_attributes
    assert attrs == {}


async def test_switch_available_true(switch_entity, mock_coordinator) -> None:
    """Test available property when device is online."""
    mock_coordinator.last_update_success = True
    assert switch_entity.available is True


async def test_switch_available_false_offline(
    switch_entity, mock_coordinator, mock_switch_device
) -> None:
    """Test available property when device is offline."""
    mock_coordinator.last_update_success = True
    mock_switch_device.is_online = False
    assert switch_entity.available is False


async def test_switch_available_false_device_not_found(
    switch_entity, mock_coordinator
) -> None:
    """Test available property when device is not found."""
    mock_coordinator.last_update_success = True
    mock_coordinator.data = {}
    assert switch_entity.available is False


async def test_switch_turn_on_success(
    switch_entity, mock_coordinator, mock_switch_device
) -> None:
    """Test switch turn on success."""
    await switch_entity.async_turn_on()
    mock_coordinator.client.set_switch_state.assert_called_once_with(
        mock_switch_device.device_id, True
    )


async def test_switch_turn_off_success(
    switch_entity, mock_coordinator, mock_switch_device
) -> None:
    """Test switch turn off success."""
    await switch_entity.async_turn_off()
    mock_coordinator.client.set_switch_state.assert_called_once_with(
        mock_switch_device.device_id, False
    )


async def test_switch_turn_on_error(
    switch_entity, mock_coordinator, mock_switch_device
) -> None:
    """Test turn on with error handling."""
    mock_coordinator.client.set_switch_state.side_effect = RuntimeError("API Error")

    with patch("homeassistant.components.watts.switch._LOGGER") as mock_logger:
        await switch_entity.async_turn_on()
        assert mock_logger.error.called


async def test_switch_turn_off_error(
    switch_entity, mock_coordinator, mock_switch_device
) -> None:
    """Test turn off with error handling."""
    mock_coordinator.client.set_switch_state.side_effect = RuntimeError("API Error")

    with patch("homeassistant.components.watts.switch._LOGGER") as mock_logger:
        await switch_entity.async_turn_off()
        assert mock_logger.error.called


async def test_async_setup_entry_with_switch_devices(
    mock_hass, mock_config_entry
) -> None:
    """Test setup entry with switch devices."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator._is_initialized = True

    switch_device = MagicMock(spec=SwitchDevice)
    switch_device.device_id = "switch_1"
    switch_device.device_name = "Test Switch 1"
    switch_device.is_turned_on = True
    switch_device.is_online = True
    switch_device.device_type = "switch"
    switch_device.room_name = "Living Room"

    coordinator.data = {"switch_1": switch_device}
    coordinator._devices = {"switch_1": switch_device}

    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WattsVisionSwitch)
    assert args[1]["update_before_add"] is True


async def test_async_setup_entry_no_switch_devices(
    mock_hass, mock_config_entry, mock_thermostat_device
) -> None:
    """Test setup entry with no switch devices (only thermostat devices)."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator._is_initialized = True
    coordinator.data = {"thermostat_1": mock_thermostat_device}
    coordinator._devices = {"thermostat_1": mock_thermostat_device}

    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


async def test_async_setup_entry_empty_data(mock_hass, mock_config_entry) -> None:
    """Test setup entry with empty coordinator data."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator._is_initialized = True
    coordinator.data = {}
    coordinator._devices = {}

    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


async def test_async_setup_entry_multiple_switch_devices(
    mock_hass, mock_config_entry
) -> None:
    """Test setup entry with multiple switch devices."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator._is_initialized = True

    switch1 = MagicMock(spec=SwitchDevice)
    switch1.device_id = "switch_1"
    switch1.device_name = "Switch 1"

    switch2 = MagicMock(spec=SwitchDevice)
    switch2.device_id = "switch_2"
    switch2.device_name = "Switch 2"

    devices_dict = {"switch_1": switch1, "switch_2": switch2}
    coordinator.data = devices_dict
    coordinator._devices = devices_dict

    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 2
    assert all(isinstance(entity, WattsVisionSwitch) for entity in entities)
    assert args[1]["update_before_add"] is True


async def test_async_setup_entry_mixed_devices(
    mock_hass, mock_config_entry, mock_thermostat_device
) -> None:
    """Test setup entry with mixed device types."""
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.last_update_success = True
    coordinator._is_initialized = True

    switch_device = MagicMock(spec=SwitchDevice)
    switch_device.device_id = "switch_1"
    switch_device.device_name = "Test Switch"

    devices_dict = {
        "switch_1": switch_device,
        "thermostat_1": mock_thermostat_device,
    }
    coordinator.data = devices_dict
    coordinator._devices = devices_dict

    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(mock_hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WattsVisionSwitch)
    assert args[1]["update_before_add"] is True
