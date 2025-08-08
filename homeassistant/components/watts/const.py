"""Constants for the Watts Vision+ integration."""

DOMAIN = "watts"

OAUTH2_AUTHORIZE = "https://visionlogindev.b2clogin.com/visionlogindev.onmicrosoft.com/B2C_1A_VISION_UNIFIEDSIGNUPORSIGNIN/oauth2/v2.0/authorize"
OAUTH2_TOKEN = "https://visionlogindev.b2clogin.com/visionlogindev.onmicrosoft.com/B2C_1A_VISION_UNIFIEDSIGNUPORSIGNIN/oauth2/v2.0/token"

OAUTH2_SCOPES = [
    "openid",
    "offline_access",
    "https://visionlogindev.onmicrosoft.com/vision/vision.read",
]

UPDATE_INTERVAL = 30
