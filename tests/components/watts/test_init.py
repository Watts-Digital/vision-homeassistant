"""Tests for the Watts Vision integration initialization."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.watts import async_setup_entry, async_unload_entry
from custom_components.watts.coordinator import WattsVisionCoordinator
import pytest
from pywattsvision.pywattsvision import WattsVisionClient
from pywattsvision.pywattsvision.auth import WattsVisionAuth

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.runtime_data = {}
    return entry


@pytest.fixture
def mock_implementation():
    """Mock OAuth2 implementation."""
    implementation = MagicMock()
    implementation.client_id = "test_client_id"
    implementation.client_secret = "test_client_secret"
    return implementation


@pytest.fixture
def mock_oauth_session():
    """Mock OAuth2 session."""
    session = MagicMock(spec=config_entry_oauth2_flow.OAuth2Session)
    session.token = {"refresh_token": "test_refresh_token"}
    return session


@pytest.fixture
def mock_auth():
    """Mock WattsVisionAuth."""
    auth = MagicMock(spec=WattsVisionAuth)
    auth.close = AsyncMock()
    return auth


@pytest.fixture
def mock_client():
    """Mock WattsVisionClient."""
    client = MagicMock(spec=WattsVisionClient)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_coordinator():
    """Mock WattsVisionCoordinator."""
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_shutdown = AsyncMock()
    coordinator.close = AsyncMock()
    return coordinator


@pytest.mark.asyncio
async def test_async_setup_entry_success(
    mock_hass,
    mock_config_entry,
    mock_implementation,
    mock_oauth_session,
    mock_auth,
    mock_client,
    mock_coordinator,
) -> None:
    """Test successful setup of config entry."""
    with (
        patch(
            "custom_components.watts.config_entry_oauth2_flow.async_get_config_entry_implementation",
            return_value=mock_implementation,
        ),
        patch(
            "custom_components.watts.config_entry_oauth2_flow.OAuth2Session",
            return_value=mock_oauth_session,
        ),
        patch("custom_components.watts.aiohttp_client.async_get_clientsession"),
        patch("custom_components.watts.WattsVisionAuth", return_value=mock_auth),
        patch("custom_components.watts.WattsVisionClient", return_value=mock_client),
        patch(
            "custom_components.watts.WattsVisionCoordinator",
            return_value=mock_coordinator,
        ),
    ):
        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once()

        # Check runtime_data is set properly
        assert "auth" in mock_config_entry.runtime_data
        assert "coordinator" in mock_config_entry.runtime_data
        assert "client" in mock_config_entry.runtime_data


@pytest.mark.asyncio
async def test_async_setup_entry_coordinator_refresh_fails(
    mock_hass,
    mock_config_entry,
    mock_implementation,
    mock_oauth_session,
    mock_auth,
    mock_client,
    mock_coordinator,
) -> None:
    """Test setup when coordinator refresh fails."""
    mock_coordinator.async_config_entry_first_refresh.side_effect = Exception(
        "Refresh failed"
    )

    with (
        patch(
            "custom_components.watts.config_entry_oauth2_flow.async_get_config_entry_implementation",
            return_value=mock_implementation,
        ),
        patch(
            "custom_components.watts.config_entry_oauth2_flow.OAuth2Session",
            return_value=mock_oauth_session,
        ),
        patch("custom_components.watts.aiohttp_client.async_get_clientsession"),
        patch("custom_components.watts.WattsVisionAuth", return_value=mock_auth),
        patch("custom_components.watts.WattsVisionClient", return_value=mock_client),
        patch(
            "custom_components.watts.WattsVisionCoordinator",
            return_value=mock_coordinator,
        ),
    ):
        with pytest.raises(Exception, match="Refresh failed"):
            await async_setup_entry(mock_hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_unload_entry_success(mock_hass, mock_config_entry) -> None:
    """Test successful unload of config entry."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()

    mock_auth = MagicMock()
    mock_auth.close = AsyncMock()

    mock_coordinator = MagicMock()
    mock_coordinator.async_shutdown = AsyncMock()

    mock_config_entry.runtime_data = {
        "client": mock_client,
        "auth": mock_auth,
        "coordinator": mock_coordinator,
    }

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    mock_client.close.assert_called_once()
    mock_auth.close.assert_called_once()
    mock_coordinator.async_shutdown.assert_called_once()
    mock_hass.config_entries.async_unload_platforms.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry_with_client_error(
    mock_hass, mock_config_entry
) -> None:
    """Test unload when client close raises OSError."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock(side_effect=OSError("Connection error"))

    mock_config_entry.runtime_data = {"client": mock_client}

    with patch("custom_components.watts._LOGGER") as mock_logger:
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        mock_logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry_with_coordinator_error(
    mock_hass, mock_config_entry
) -> None:
    """Test unload when coordinator close raises error."""
    mock_coordinator = MagicMock()
    mock_coordinator.async_shutdown = AsyncMock(
        side_effect=OSError("Coordinator error")
    )

    mock_config_entry.runtime_data = {"coordinator": mock_coordinator}

    with patch("custom_components.watts._LOGGER") as mock_logger:
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        mock_logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry_platform_unload_fails(
    mock_hass, mock_config_entry
) -> None:
    """Test unload when platform unload fails."""
    mock_hass.config_entries.async_unload_platforms.return_value = False

    with patch("custom_components.watts._LOGGER") as mock_logger:
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is False
        mock_logger.error.assert_called_once()
