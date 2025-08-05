"""Tests for the Watts Vision data coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from custom_components.watts.coordinator import WattsVisionCoordinator
import pytest
from pywattsvision.pywattsvision import (
    SwitchDevice,
    ThermostatDevice,
    WattsVisionClient,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_client():
    """Mock WattsVisionClient."""
    client = MagicMock(spec=WattsVisionClient)
    client.get_all_devices_data = AsyncMock()
    return client


@pytest.fixture
def mock_thermostat_device():
    """Mock thermostat device."""
    device = MagicMock(spec=ThermostatDevice)
    device.device_id = "thermostat_123"
    device.device_name = "Test Thermostat"
    device.current_temperature = 21.5
    device.setpoint = 23.0
    device.thermostat_mode = "Comfort"
    device.is_online = True
    device.device_type = "thermostat"
    return device


@pytest.fixture
def mock_switch_device():
    """Mock switch device."""
    device = MagicMock(spec=SwitchDevice)
    device.device_id = "switch_123"
    device.device_name = "Test Switch"
    device.is_turned_on = True
    device.is_online = True
    device.device_type = "switch"
    return device


@pytest.fixture
def coordinator(mock_hass, mock_client):
    """Create WattsVisionCoordinator instance."""
    return WattsVisionCoordinator(mock_hass, mock_client)


def test_coordinator_initialization(coordinator, mock_hass, mock_client) -> None:
    """Test coordinator initialization."""
    assert coordinator.hass == mock_hass
    assert coordinator.client == mock_client
    assert coordinator.name == "watts"
    assert coordinator.update_interval == timedelta(seconds=5)


def test_coordinator_inherits_from_data_update_coordinator(coordinator) -> None:
    """Test that coordinator inherits from DataUpdateCoordinator."""

    assert isinstance(coordinator, DataUpdateCoordinator)


@pytest.mark.asyncio
async def test_async_update_data_success(
    coordinator, mock_client, mock_thermostat_device, mock_switch_device
) -> None:
    """Test successful data update."""
    expected_data = {
        "thermostat_123": mock_thermostat_device,
        "switch_123": mock_switch_device,
    }
    mock_client.get_all_devices_data.return_value = expected_data

    result = await coordinator._async_update_data()

    assert result == expected_data
    mock_client.get_all_devices_data.assert_called_once()


@pytest.mark.asyncio
async def test_async_update_data_api_error(coordinator, mock_client) -> None:
    """Test data update with API error."""
    mock_client.get_all_devices_data.side_effect = Exception("API connection failed")

    with pytest.raises(UpdateFailed, match="API error: API connection failed"):
        await coordinator._async_update_data()

    mock_client.get_all_devices_data.assert_called_once()


@pytest.mark.asyncio
async def test_async_update_data_timeout_error(coordinator, mock_client) -> None:
    """Test data update with timeout error."""

    mock_client.get_all_devices_data.side_effect = TimeoutError("Request timeout")

    with pytest.raises(UpdateFailed, match="API error: Request timeout"):
        await coordinator._async_update_data()

    mock_client.get_all_devices_data.assert_called_once()


@pytest.mark.asyncio
async def test_async_update_data_only_thermostats(
    coordinator, mock_client, mock_thermostat_device
) -> None:
    """Test data update with thermostats."""
    expected_data = {"thermostat_123": mock_thermostat_device}
    mock_client.get_all_devices_data.return_value = expected_data

    result = await coordinator._async_update_data()

    assert result == expected_data
    assert len(result) == 1
    assert "thermostat_123" in result


@pytest.mark.asyncio
async def test_async_update_data_only_switches(
    coordinator, mock_client, mock_switch_device
) -> None:
    """Test data update with switches."""
    expected_data = {"switch_123": mock_switch_device}
    mock_client.get_all_devices_data.return_value = expected_data

    result = await coordinator._async_update_data()

    assert result == expected_data
    assert len(result) == 1
    assert "switch_123" in result


@pytest.mark.asyncio
async def test_async_update_data_multiple_devices_same_type(
    coordinator, mock_client
) -> None:
    """Test data update with multiple devices of the same type."""
    device1 = MagicMock(spec=ThermostatDevice)
    device1.device_id = "thermostat_1"
    device2 = MagicMock(spec=ThermostatDevice)
    device2.device_id = "thermostat_2"

    expected_data = {"thermostat_1": device1, "thermostat_2": device2}
    mock_client.get_all_devices_data.return_value = expected_data

    result = await coordinator._async_update_data()

    assert result == expected_data
    assert len(result) == 2
    assert "thermostat_1" in result
    assert "thermostat_2" in result


@pytest.mark.asyncio
async def test_async_update_data_mixed_devices(
    coordinator, mock_client, mock_thermostat_device, mock_switch_device
) -> None:
    """Test data update with mixed device types."""
    device3 = MagicMock(spec=ThermostatDevice)
    device3.device_id = "thermostat_456"
    device4 = MagicMock(spec=SwitchDevice)
    device4.device_id = "switch_456"

    expected_data = {
        "thermostat_123": mock_thermostat_device,
        "switch_123": mock_switch_device,
        "thermostat_456": device3,
        "switch_456": device4,
    }
    mock_client.get_all_devices_data.return_value = expected_data

    result = await coordinator._async_update_data()

    assert result == expected_data
    assert len(result) == 4


@pytest.mark.asyncio
async def test_async_update_data_keep_device_types(
    coordinator, mock_client, mock_thermostat_device, mock_switch_device
) -> None:
    """Test that data update keeps device type information."""
    expected_data = {
        "thermostat_123": mock_thermostat_device,
        "switch_123": mock_switch_device,
    }
    mock_client.get_all_devices_data.return_value = expected_data

    result = await coordinator._async_update_data()

    thermostat = result["thermostat_123"]
    switch = result["switch_123"]

    assert isinstance(thermostat, type(mock_thermostat_device))
    assert isinstance(switch, type(mock_switch_device))
    assert thermostat.device_type == "thermostat"
    assert switch.device_type == "switch"
