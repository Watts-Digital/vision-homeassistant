"""The Watts Vision integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from pywattsvision.pywattsvision import WattsVisionClient
from pywattsvision.pywattsvision.auth import WattsVisionAuth

from .coordinator import WattsVisionCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SWITCH]

type WattsVisionConfigEntry = ConfigEntry[WattsVisionAuth]


async def async_setup_entry(hass: HomeAssistant, entry: WattsVisionConfigEntry) -> bool:
    """Set up Watts Vision from a config entry."""
    _LOGGER.debug("Setting up Watts Vision integration")

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    auth = WattsVisionAuth(
        client_id=implementation.client_id,
        client_secret=implementation.client_secret,
        refresh_token=oauth_session.token.get("refresh_token"),
        session=aiohttp_client.async_get_clientsession(hass),
    )

    client = WattsVisionClient(auth)
    coordinator = WattsVisionCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = {"auth": auth, "coordinator": coordinator, "client": client}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: WattsVisionConfigEntry
) -> bool:
    """Unload a config entry."""

    _LOGGER.debug("Unloading Watts Vision + integration")
    runtime_data = entry.runtime_data

    client = runtime_data.get("client")
    if client:
        try:
            await client.close()
            _LOGGER.debug("Client closed successfully")
        except OSError as e:
            _LOGGER.warning("Error closing client: %s", e)

    auth = runtime_data.get("auth")
    if auth:
        try:
            await auth.close()
            _LOGGER.debug("Auth closed successfully")
        except OSError as e:
            _LOGGER.warning("Error closing auth: %s", e)

    coordinator = runtime_data.get("coordinator")
    if coordinator:
        try:
            if hasattr(coordinator, "async_shutdown"):
                await coordinator.async_shutdown()
            else:
                await coordinator.close()
            _LOGGER.debug("Coordinator closed successfully")
        except (OSError, AttributeError) as e:
            _LOGGER.warning("Error closing coordinator: %s", e)

    unload_result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unload_result:
        _LOGGER.error("Failed to unload platforms for Watts Vision + integration")
    else:
        _LOGGER.debug("Successfully unloaded platforms for Watts Vision + integration")

    return unload_result
