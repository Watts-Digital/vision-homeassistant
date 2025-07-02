"""Constants for the Watts Vision+ integration."""

from homeassistant.components.climate import HVACMode

DOMAIN = "watts"

OAUTH2_AUTHORIZE = "https://visionlogindev.b2clogin.com/visionlogindev.onmicrosoft.com/B2C_1A_VISION_UNIFIEDSIGNUPORSIGNIN/oauth2/v2.0/authorize"
OAUTH2_TOKEN = "https://visionlogindev.b2clogin.com/visionlogindev.onmicrosoft.com/B2C_1A_VISION_UNIFIEDSIGNUPORSIGNIN/oauth2/v2.0/token"

OAUTH2_SCOPES = [
    "openid",
    "offline_access",
    "https://visionlogindev.onmicrosoft.com/vision/vision.read",
]

# Update interval in seconds
UPDATE_INTERVAL = 15

# API endpoints
API_BASE_URL = "https://dev-vision.watts.io/api"

# Interface types
INTERFACE_THERMOSTAT = "action.devices.types.THERMOSTAT"
INTERFACE_SWITCH = "action.devices.types.SWITCH"

# Default allowed setpoints range
DEFAULT_MIN_SETPOINT = 5
DEFAULT_MAX_SETPOINT = 35

# Mode mappings
WATTS_MODE_TO_HVAC = {
    1: HVACMode.HEAT,  # comfort
    2: HVACMode.OFF,  # off
    3: HVACMode.HEAT,  # eco
    4: HVACMode.HEAT,  # defrost
    5: HVACMode.HEAT,  # timer
    6: HVACMode.AUTO,  # program
}

HVAC_TO_WATTS_MODE = {
    HVACMode.HEAT: 1,  # comfort
    HVACMode.OFF: 2,  # off
    HVACMode.AUTO: 6,  # program
}
