from asyncio import run_coroutine_threadsafe

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow


class ConfigEntryAuth:
    """Provide Watts Vision+ authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize Watts Vision+ Auth."""
        self.hass = hass
        self.session = oauth_session
        self.token = self.session.token

    def refresh_tokens(self) -> str:
        """Refresh and return new Watts Vision+ tokens using Home Assistant OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.hass.loop
        ).result()
        return self.session.token["access_token"]
