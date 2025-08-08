"""Test the Watts Vision config flow."""

from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.components.watts.const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator


@pytest.mark.usefixtures("current_request_with_host")
async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the full OAuth2 config flow."""
    # Initiate user flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert "url" in result
    assert OAUTH2_AUTHORIZE in result["url"]
    assert "response_type=code" in result["url"]
    assert "scope=" in result["url"]

    # Simulate OAuth callback
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Mock successful token response
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    # Mock coordinator to avoid network calls
    with patch(
        "homeassistant.components.watts.WattsVisionCoordinator.async_config_entry_first_refresh"
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert result2["title"] == "Watts"
        assert "token" in result2["data"]
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1


@pytest.mark.usefixtures("current_request_with_host")
async def test_oauth_error(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test OAuth error handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200

    # Mock OAuth error response
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={"error": "invalid_grant"},
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "oauth_error"


@pytest.mark.usefixtures("current_request_with_host")
async def test_oauth_timeout(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test OAuth timeout handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200

    # Mock timeout error
    aioclient_mock.post(OAUTH2_TOKEN, exc=TimeoutError())

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "oauth_timeout"


@pytest.mark.usefixtures("current_request_with_host")
async def test_oauth_invalid_response(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test OAuth invalid response handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200

    # Mock invalid response
    aioclient_mock.post(OAUTH2_TOKEN, status=500, text="invalid json")

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "oauth_failed"


async def test_unique_config_entry(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that duplicate config entries are not allowed."""
    # Create a mock config entry with all required parameters
    mock_entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Watts",
        data={"token": {"refresh_token": "mock-refresh-token"}},
        source=config_entries.SOURCE_USER,
        unique_id="watts_vision",
        entry_id="test_entry",
        options={},
        discovery_keys={},
        subentries_data={},
    )
    await hass.config_entries.async_add(mock_entry)

    # Try to initiate a new flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    # Verify no new config entries were created
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


@pytest.mark.usefixtures("current_request_with_host")
async def test_unique_config_entry_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that a full flow after an existing entry aborts due to uniqueness."""
    # Ensure no existing entries
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0

    # Create a config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.WattsVisionCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    # Try to create another config entry
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
