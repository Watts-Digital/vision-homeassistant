"""Tests for the Watts Vision authentication module."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.watts.auth import ConfigEntryAuth
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.loop = MagicMock()
    return hass


@pytest.fixture
def mock_oauth_session():
    """Mock OAuth2 session."""
    session = MagicMock(spec=config_entry_oauth2_flow.OAuth2Session)
    session.token = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
    }
    session.async_ensure_token_valid = AsyncMock()
    return session


@pytest.fixture
def config_entry_auth(mock_hass, mock_oauth_session):
    """Create ConfigEntryAuth instance."""
    return ConfigEntryAuth(mock_hass, mock_oauth_session)


def test_config_entry_auth_initialization(
    config_entry_auth, mock_hass, mock_oauth_session
) -> None:
    """Test ConfigEntryAuth initialization."""
    assert config_entry_auth.hass == mock_hass
    assert config_entry_auth.session == mock_oauth_session
    assert config_entry_auth.token == mock_oauth_session.token


def test_refresh_tokens_returns_current_access_token(config_entry_auth) -> None:
    """Test that refresh_tokens returns the current access token."""
    with patch("custom_components.watts.auth.run_coroutine_threadsafe") as mock_run:
        mock_future = MagicMock()
        mock_future.result.return_value = None
        mock_run.return_value = mock_future

        result = config_entry_auth.refresh_tokens()

        assert result == "test_access_token"


def test_refresh_tokens_with_exception(config_entry_auth, mock_oauth_session) -> None:
    """Test refresh_tokens when run_coroutine_threadsafe raises an exception."""
    with patch("custom_components.watts.auth.run_coroutine_threadsafe") as mock_run:
        mock_future = MagicMock()
        mock_future.result.side_effect = RuntimeError("Token refresh failed")
        mock_run.return_value = mock_future

        with pytest.raises(RuntimeError, match="Token refresh failed"):
            config_entry_auth.refresh_tokens()
