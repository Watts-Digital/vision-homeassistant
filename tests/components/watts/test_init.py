"""Test the Watts Vision integration initialization."""

from unittest.mock import AsyncMock, patch

from aiohttp import ClientError, ClientResponseError
from visionpluspython.visionpluspython import WattsVisionClient
from visionpluspython.visionpluspython.auth import WattsVisionAuth

from homeassistant.components.watts import async_unload_entry
from homeassistant.components.watts.coordinator import WattsVisionCoordinator
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from tests.common import MockConfigEntry


async def test_setup_entry_success(hass: HomeAssistant) -> None:
    """Test successful setup and unload of entry."""
    config_entry = MockConfigEntry(
        domain="watts",  # Fixed: Changed from "olarm" to "watts"
        data={
            "user_id": "test-user-id",
            "device_id": "test-device-id",
            "load_zones_bypass_entities": False,
            "auth_implementation": "watts",  # Fixed: Changed from "olarm" to "watts"
            "token": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 9999999999,
            },
        },
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
        ) as mock_get_implementation,
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session"
        ) as mock_session,
        patch(
            "homeassistant.components.watts.WattsVisionCoordinator.async_config_entry_first_refresh"
        ) as mock_first_refresh,
        patch("homeassistant.components.watts.WattsVisionClient") as mock_client_class,
        patch("homeassistant.components.watts.WattsVisionAuth") as mock_auth_class,
    ):
        # Mock the OAuth implementation
        mock_implementation = AsyncMock()
        mock_implementation.client_id = "test-client-id"
        mock_implementation.client_secret = "test-client-secret"
        mock_get_implementation.return_value = mock_implementation

        # Mock the OAuth session
        mock_session_instance = AsyncMock()
        mock_session_instance.token = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_at": 9999999999,
        }
        mock_session_instance.async_ensure_token_valid = AsyncMock()
        mock_session.return_value = mock_session_instance

        # Mock the WattsVisionAuth
        mock_auth_instance = AsyncMock()
        mock_auth_class.return_value = mock_auth_instance

        # Mock the WattsVisionClient
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Mock the coordinator's first refresh to succeed
        mock_first_refresh.return_value = None

        # Setup entry
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert result is True
        assert config_entry.state is ConfigEntryState.LOADED
        mock_first_refresh.assert_called_once()

        # Test unload
        unload_result = await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()

        assert unload_result is True
        assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_entry_auth_failed(hass: HomeAssistant) -> None:
    """Test setup with authentication failure."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={
            "auth_implementation": "watts",
            "token": {
                "access_token": "invalid-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 9999999999,
            },
        },
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
        ) as mock_get_implementation,
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session"
        ) as mock_session,
    ):
        # Mock the OAuth implementation
        mock_implementation = AsyncMock()
        mock_implementation.client_id = "test-client-id"
        mock_implementation.client_secret = "test-client-secret"
        mock_get_implementation.return_value = mock_implementation

        # Mock OAuth session to raise 401 error
        mock_session_instance = AsyncMock()
        mock_session_instance.async_ensure_token_valid.side_effect = (
            ClientResponseError(None, None, status=401, message="Unauthorized")
        )
        mock_session_instance.token = {
            "refresh_token": "test-refresh-token",
            "expires_at": 9999999999,
        }
        mock_session.return_value = mock_session_instance

        # Setup entry - should fail with auth error
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert result is False
        assert config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_entry_not_ready(hass: HomeAssistant) -> None:
    """Test setup when network is temporarily unavailable."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={
            "auth_implementation": "watts",
            "token": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 9999999999,
            },
        },
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
        ) as mock_get_implementation,
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session"
        ) as mock_session,
    ):
        # Mock the OAuth implementation
        mock_implementation = AsyncMock()
        mock_implementation.client_id = "test-client-id"
        mock_implementation.client_secret = "test-client-secret"
        mock_get_implementation.return_value = mock_implementation

        # Mock OAuth session to raise network error
        mock_session_instance = AsyncMock()
        mock_session_instance.async_ensure_token_valid.side_effect = ClientError(
            "Connection timeout"
        )
        mock_session_instance.token = {
            "refresh_token": "test-refresh-token",
            "expires_at": 9999999999,
        }
        mock_session.return_value = mock_session_instance

        # Setup entry - should fail and retry
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert result is False
        assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_entry_coordinator_update_failed(hass: HomeAssistant) -> None:
    """Test setup when coordinator update fails."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={
            "auth_implementation": "watts",
            "token": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 9999999999,
            },
        },
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
        ) as mock_get_implementation,
        patch(
            "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session"
        ) as mock_session,
        patch("homeassistant.components.watts.WattsVisionClient") as mock_client_class,
        patch("homeassistant.components.watts.WattsVisionAuth") as mock_auth_class,
        patch(
            "homeassistant.components.watts.WattsVisionCoordinator.async_config_entry_first_refresh"
        ) as mock_first_refresh,
    ):
        # Mock the OAuth implementation
        mock_implementation = AsyncMock()
        mock_implementation.client_id = "test-client-id"
        mock_implementation.client_secret = "test-client-secret"
        mock_get_implementation.return_value = mock_implementation

        # Mock the OAuth session
        mock_session_instance = AsyncMock()
        mock_session_instance.token = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_at": 9999999999,
        }
        mock_session_instance.async_ensure_token_valid = AsyncMock()
        mock_session.return_value = mock_session_instance

        # Mock the WattsVisionAuth and Client
        mock_auth_instance = AsyncMock()
        mock_auth_class.return_value = mock_auth_instance
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Mock coordinator first refresh to fail
        mock_first_refresh.side_effect = UpdateFailed("Coordinator update failed")

        # Setup entry - should fail due to coordinator error
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert result is False
        assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry_client_error(hass: HomeAssistant) -> None:
    """Test unload when client close raises OSError."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={},
    )
    config_entry.add_to_hass(hass)

    # Mock the runtime data
    mock_client = AsyncMock(spec=WattsVisionClient)
    mock_client.close.side_effect = OSError("Connection error")
    mock_auth = AsyncMock(spec=WattsVisionAuth)
    mock_coordinator = AsyncMock(spec=WattsVisionCoordinator)

    config_entry.runtime_data = {
        "client": mock_client,
        "auth": mock_auth,
        "coordinator": mock_coordinator,
    }

    with (
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ),
        patch("homeassistant.components.watts._LOGGER") as mock_logger,
    ):
        result = await async_unload_entry(hass, config_entry)

        assert result is True
        mock_client.close.assert_called_once()
        mock_auth.close.assert_called_once()
        # Check that warning was logged for client error
        mock_logger.warning.assert_any_call(
            "Error closing client: %s", mock_client.close.side_effect
        )


async def test_unload_entry_auth_error(hass: HomeAssistant) -> None:
    """Test unload when auth close raises OSError."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={},
    )
    config_entry.add_to_hass(hass)

    # Mock the runtime data
    mock_client = AsyncMock(spec=WattsVisionClient)
    mock_auth = AsyncMock(spec=WattsVisionAuth)
    mock_auth.close.side_effect = OSError("Auth error")
    mock_coordinator = AsyncMock(spec=WattsVisionCoordinator)

    config_entry.runtime_data = {
        "client": mock_client,
        "auth": mock_auth,
        "coordinator": mock_coordinator,
    }

    with (
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ),
        patch("homeassistant.components.watts._LOGGER") as mock_logger,
    ):
        result = await async_unload_entry(hass, config_entry)

        assert result is True
        mock_client.close.assert_called_once()
        mock_auth.close.assert_called_once()
        # Check that warning was logged for auth error
        mock_logger.warning.assert_any_call(
            "Error closing auth: %s", mock_auth.close.side_effect
        )


async def test_unload_entry_coordinator_error(hass: HomeAssistant) -> None:
    """Test unload when coordinator close raises OSError."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={},
    )
    config_entry.add_to_hass(hass)

    # Mock the runtime data
    mock_client = AsyncMock(spec=WattsVisionClient)
    mock_auth = AsyncMock(spec=WattsVisionAuth)
    mock_coordinator = AsyncMock(spec=WattsVisionCoordinator)
    mock_coordinator.async_shutdown.side_effect = OSError("Coordinator error")

    config_entry.runtime_data = {
        "client": mock_client,
        "auth": mock_auth,
        "coordinator": mock_coordinator,
    }

    with (
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ),
        patch("homeassistant.components.watts._LOGGER") as mock_logger,
    ):
        result = await async_unload_entry(hass, config_entry)

        assert result is True
        mock_client.close.assert_called_once()
        mock_auth.close.assert_called_once()
        # Check that warning was logged for coordinator error
        mock_logger.warning.assert_any_call(
            "Error closing coordinator: %s", mock_coordinator.async_shutdown.side_effect
        )


async def test_unload_entry_platform_unload_fails(hass: HomeAssistant) -> None:
    """Test unload when platform unload fails."""
    config_entry = MockConfigEntry(
        domain="watts",
        data={},
    )
    config_entry.add_to_hass(hass)

    # Mock the runtime data
    mock_client = AsyncMock(spec=WattsVisionClient)
    mock_auth = AsyncMock(spec=WattsVisionAuth)
    mock_coordinator = AsyncMock(spec=WattsVisionCoordinator)

    config_entry.runtime_data = {
        "client": mock_client,
        "auth": mock_auth,
        "coordinator": mock_coordinator,
    }

    with (
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=False,
        ),
        patch("homeassistant.components.watts._LOGGER") as mock_logger,
    ):
        result = await async_unload_entry(hass, config_entry)

        assert result is False
        mock_client.close.assert_called_once()
        mock_auth.close.assert_called_once()
        mock_logger.error.assert_called_once_with(
            "Failed to unload platforms for Watts Vision + integration"
        )
