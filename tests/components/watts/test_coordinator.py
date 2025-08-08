"""Tests for the Watts Vision coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from visionpluspython.visionpluspython import Device, WattsVisionClient

from homeassistant.components.watts.coordinator import WattsVisionCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_client():
    """Mock WattsVisionClient instance."""
    client = MagicMock(spec=WattsVisionClient)
    client.discover_devices = AsyncMock()
    client.get_device = AsyncMock()
    client.get_devices_report = AsyncMock()
    return client


@pytest.fixture
def mock_device():
    """Mock Device instance."""
    device = MagicMock(spec=Device)
    device.device_id = "device_123"
    device.device_name = "Test Device"
    return device


@pytest.fixture
def coordinator(mock_hass, mock_client):
    """Create a WattsVisionCoordinator instance."""
    return WattsVisionCoordinator(mock_hass, mock_client)


async def test_coordinator_initialization(coordinator, mock_hass, mock_client) -> None:
    """Test coordinator initialization."""
    assert coordinator.hass == mock_hass
    assert coordinator.client == mock_client
    assert coordinator.name == DOMAIN
    assert coordinator.update_interval.total_seconds() == UPDATE_INTERVAL
    assert coordinator._is_initialized is False
    assert coordinator._devices == {}


async def test_async_config_entry_first_refresh_success(
    coordinator, mock_client, mock_device
) -> None:
    """Test initial device discovery success."""
    mock_client.discover_devices.return_value = [mock_device]
    await coordinator.async_config_entry_first_refresh()

    mock_client.discover_devices.assert_called_once()
    assert coordinator._is_initialized is True
    assert coordinator._devices == {mock_device.device_id: mock_device}


async def test_async_config_entry_first_refresh_failure(
    coordinator, mock_client
) -> None:
    """Test initial device discovery failure."""
    mock_client.discover_devices.side_effect = RuntimeError("API error")

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator.async_config_entry_first_refresh()

    assert "Initial discovery failed: API error" in str(exc_info.value)
    assert coordinator._is_initialized is False
    assert coordinator._devices == {}


async def test_async_refresh_device_success(
    coordinator, mock_client, mock_device
) -> None:
    """Test refreshing a specific device successfully."""
    coordinator._devices = {mock_device.device_id: mock_device}
    coordinator._is_initialized = True
    mock_client.get_device.return_value = mock_device

    await coordinator.async_refresh_device(mock_device.device_id)

    mock_client.get_device.assert_called_once_with(mock_device.device_id, refresh=True)
    assert coordinator._devices[mock_device.device_id] == mock_device


async def test_async_refresh_device_failure(
    coordinator, mock_client, mock_device
) -> None:
    """Test refreshing a specific device with failure."""
    coordinator._devices = {mock_device.device_id: mock_device}
    coordinator._is_initialized = True
    mock_client.get_device.side_effect = RuntimeError("Refresh error")

    await coordinator.async_refresh_device(mock_device.device_id)

    mock_client.get_device.assert_called_once_with(mock_device.device_id, refresh=True)
    assert (
        coordinator._devices[mock_device.device_id] == mock_device
    )  # Device unchanged


async def test_async_update_data_not_initialized(
    coordinator, mock_client, mock_device
) -> None:
    """Test async_update_data when not initialized."""
    mock_client.discover_devices.return_value = [mock_device]

    result = await coordinator._async_update_data()

    mock_client.discover_devices.assert_called_once()
    assert coordinator._is_initialized is True
    assert result == {mock_device.device_id: mock_device}


async def test_async_update_data_no_devices(coordinator, mock_client) -> None:
    """Test async_update_data with no devices."""
    coordinator._is_initialized = True
    coordinator._devices = {}

    result = await coordinator._async_update_data()

    mock_client.get_devices_report.assert_not_called()
    assert result == {}


async def test_async_update_data_success(coordinator, mock_client, mock_device) -> None:
    """Test async_update_data with successful update."""
    coordinator._is_initialized = True
    coordinator._devices = {mock_device.device_id: mock_device}
    updated_device = MagicMock(spec=Device)
    updated_device.device_id = mock_device.device_id
    mock_client.get_devices_report.return_value = {
        mock_device.device_id: updated_device
    }

    result = await coordinator._async_update_data()

    mock_client.get_devices_report.assert_called_once_with([mock_device.device_id])
    assert coordinator._devices[mock_device.device_id] == updated_device
    assert result == {mock_device.device_id: updated_device}


async def test_async_update_data_failure(coordinator, mock_client, mock_device) -> None:
    """Test async_update_data with API failure."""
    coordinator._is_initialized = True
    coordinator._devices = {mock_device.device_id: mock_device}
    mock_client.get_devices_report.side_effect = RuntimeError("API error")

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert "API error during devices update: API error" in str(exc_info.value)
    assert (
        coordinator._devices[mock_device.device_id] == mock_device
    )  # Device unchanged
