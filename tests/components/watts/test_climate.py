from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.watts.climate import WattsVisionClimate, async_setup_entry
from custom_components.watts.coordinator import WattsVisionCoordinator
import pytest
from pywattsvision.pywattsvision import SwitchDevice, ThermostatDevice

from homeassistant.components.climate import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


@pytest.fixture
def mock_device():
    """Watts Vision thermostat mock."""
    device = MagicMock(spec=ThermostatDevice)
    device.device_id = "device_123"
    device.device_name = "Test Thermostat"
    device.current_temperature = 20.5
    device.setpoint = 22.0
    device.thermostat_mode = "Comfort"
    device.min_allowed_temperature = 5.0
    device.max_allowed_temperature = 30.0
    device.temperature_unit = "C"
    device.is_online = True
    device.device_type = "thermostat"
    device.room_name = "Living Room"
    device.available_thermostat_modes = [
        "Program",
        "Eco",
        "Comfort",
        "Off",
        "Defrost",
        "Timer",
    ]
    return device


@pytest.fixture
def mock_coordinator(mock_device):
    """Mock coordinator with a single device."""
    coordinator = MagicMock(spec=WattsVisionCoordinator)
    coordinator.data = {mock_device.device_id: mock_device}
    coordinator.client = AsyncMock()
    coordinator.client.set_thermostat_temperature = AsyncMock()
    coordinator.client.set_thermostat_mode = AsyncMock()
    return coordinator


@pytest.fixture
def climate_entity(mock_coordinator, mock_device):
    """Create a climate entity instance."""
    return WattsVisionClimate(mock_coordinator, mock_device)


@pytest.mark.asyncio
async def test_set_temperature(climate_entity, mock_coordinator, mock_device) -> None:
    """Test temperature setting."""
    await climate_entity.async_set_temperature(temperature=23.5)
    mock_coordinator.client.set_thermostat_temperature.assert_called_once_with(
        mock_device.device_id, 23.5
    )


@pytest.mark.asyncio
async def test_set_hvac_mode_heat(
    climate_entity, mock_coordinator, mock_device
) -> None:
    """Test HVAC mode setting to heat."""
    await climate_entity.async_set_hvac_mode(HVACMode.HEAT)
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_device.device_id, "Comfort"
    )


@pytest.mark.asyncio
async def test_set_hvac_mode_off(climate_entity, mock_coordinator, mock_device) -> None:
    """Test HVAC mode setting to off."""
    await climate_entity.async_set_hvac_mode(HVACMode.OFF)
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_device.device_id, "Off"
    )


@pytest.mark.asyncio
async def test_set_hvac_mode_auto(
    climate_entity, mock_coordinator, mock_device
) -> None:
    """Test HVAC mode setting to auto."""
    await climate_entity.async_set_hvac_mode(HVACMode.AUTO)
    mock_coordinator.client.set_thermostat_mode.assert_called_once_with(
        mock_device.device_id, "Program"
    )


def test_current_temperature(climate_entity) -> None:
    """Test current temperature property."""
    assert climate_entity.current_temperature == 20.5


def test_target_temperature(climate_entity) -> None:
    """Test target temperature property."""
    assert climate_entity.target_temperature == 22.0


def test_hvac_mode(climate_entity) -> None:
    """Test HVAC mode property."""
    assert climate_entity.hvac_mode == HVACMode.HEAT


def test_extra_state_attributes(climate_entity) -> None:
    """Test extra state attributes."""
    attrs = climate_entity.extra_state_attributes
    assert attrs["thermostat_mode"] == "Comfort"
    assert attrs["device_type"] == "thermostat"
    assert attrs["room_name"] == "Living Room"
    assert attrs["temperature_unit"] == "C"
    assert attrs["available_thermostat_modes"] == [
        "Program",
        "Eco",
        "Comfort",
        "Off",
        "Defrost",
        "Timer",
    ]


@pytest.mark.asyncio
async def test_async_setup_entry_with_thermostat_devices() -> None:
    """Test setup entry with thermostat devices."""
    hass = MagicMock(spec=HomeAssistant)
    entry = MagicMock(spec=ConfigEntry)
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock()
    thermostat_device = MagicMock(spec=ThermostatDevice)
    thermostat_device.device_id = "thermostat_1"
    thermostat_device.device_name = "Test Thermostat 1"
    thermostat_device.current_temperature = 21.0
    thermostat_device.setpoint = 23.0
    thermostat_device.thermostat_mode = "Program"
    thermostat_device.min_allowed_temperature = 5.0
    thermostat_device.max_allowed_temperature = 30.0
    thermostat_device.temperature_unit = "C"
    thermostat_device.is_online = True
    thermostat_device.device_type = "thermostat"
    thermostat_device.room_name = "Bedroom"
    thermostat_device.available_thermostat_modes = ["Program", "Eco", "Comfort", "Off"]
    coordinator.data = {"thermostat_1": thermostat_device}
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    args = async_add_entities.call_args
    entities = args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WattsVisionClimate)
    assert args[1]["update_before_add"] is True


@pytest.mark.asyncio
async def test_async_setup_entry_no_thermostat_devices() -> None:
    """Test setup entry with no thermostat devices (only switch devices)."""
    hass = MagicMock(spec=HomeAssistant)
    entry = MagicMock(spec=ConfigEntry)
    async_add_entities = MagicMock(spec=AddEntitiesCallback)

    coordinator = MagicMock()
    switch_device = MagicMock(spec=SwitchDevice)
    switch_device.device_id = "switch_1"
    switch_device.device_name = "Test Switch"
    switch_device.is_turned_on = True
    switch_device.is_online = True
    switch_device.device_type = "switch"
    switch_device.room_name = "Kitchen"

    coordinator.data = {"switch_1": switch_device}
    entry.runtime_data = {"coordinator": coordinator}

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


def test_climate_initialization(mock_coordinator, mock_device) -> None:
    """Test climate entity initialization."""
    climate = WattsVisionClimate(mock_coordinator, mock_device)

    assert climate._device == mock_device
    assert climate._attr_unique_id == "device_123"
    assert climate._attr_name == "Test Thermostat"
    assert climate._attr_device_info["identifiers"] == {("watts", "device_123")}
    assert climate._attr_device_info["name"] == "Test Thermostat"
    assert climate._attr_device_info["manufacturer"] == "Watts"
    assert climate._attr_device_info["model"] == "Vision+ Thermostat"
    assert climate._attr_min_temp == 5.0
    assert climate._attr_max_temp == 30.0
    assert climate._attr_temperature_unit == "°C"


@pytest.mark.asyncio
async def test_set_temperature_error(
    climate_entity, mock_coordinator, mock_device
) -> None:
    """Test temperature setting with error handling."""
    mock_coordinator.client.set_thermostat_temperature.side_effect = RuntimeError(
        "API Error"
    )

    with patch("custom_components.watts.climate._LOGGER") as mock_logger:
        await climate_entity.async_set_temperature(temperature=25.0)
        mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_set_hvac_mode_error(
    climate_entity, mock_coordinator, mock_device
) -> None:
    """Test HVAC mode setting with error handling."""
    mock_coordinator.client.set_thermostat_mode.side_effect = RuntimeError("API Error")

    with patch("custom_components.watts.climate._LOGGER") as mock_logger:
        await climate_entity.async_set_hvac_mode(HVACMode.HEAT)
        mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_set_temperature_no_temperature() -> None:
    """Test temperature setting without temperature parameter."""
    mock_coordinator = MagicMock()
    mock_device = MagicMock()
    climate = WattsVisionClimate(mock_coordinator, mock_device)

    await climate.async_set_temperature()
    mock_coordinator.client.set_thermostat_temperature.assert_not_called()


@pytest.mark.asyncio
async def test_set_hvac_mode_unsupported(climate_entity, mock_coordinator) -> None:
    """Test setting unsupported HVAC mode."""
    with patch("custom_components.watts.climate._LOGGER") as mock_logger:
        await climate_entity.async_set_hvac_mode(HVACMode.COOL)
        mock_logger.error.assert_called_once()
        mock_coordinator.client.set_thermostat_mode.assert_not_called()


def test_current_temperature_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test current temperature when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.current_temperature is None


def test_target_temperature_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test target temperature when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.target_temperature is None


def test_hvac_mode_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test HVAC mode when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.hvac_mode is None


def test_hvac_mode_eco(climate_entity, mock_coordinator, mock_device) -> None:
    """Test HVAC mode mapping for Eco mode."""
    mock_device.thermostat_mode = "Eco"
    assert climate_entity.hvac_mode == HVACMode.HEAT


def test_hvac_mode_program(climate_entity, mock_coordinator, mock_device) -> None:
    """Test HVAC mode mapping for Program mode."""
    mock_device.thermostat_mode = "Program"
    assert climate_entity.hvac_mode == HVACMode.AUTO


def test_hvac_mode_off(climate_entity, mock_coordinator, mock_device) -> None:
    """Test HVAC mode mapping for Off mode."""
    mock_device.thermostat_mode = "Off"
    assert climate_entity.hvac_mode == HVACMode.OFF


def test_hvac_mode_unknown(climate_entity, mock_coordinator, mock_device) -> None:
    """Test HVAC mode mapping for unknown mode."""
    mock_device.thermostat_mode = "Unknown"
    assert climate_entity.hvac_mode is None


def test_available_true(climate_entity) -> None:
    """Test available property when device is online."""
    assert climate_entity.available is True


def test_available_false(climate_entity, mock_coordinator, mock_device) -> None:
    """Test available property when device is offline."""
    mock_device.is_online = False
    assert climate_entity.available is False


def test_available_device_not_found(climate_entity, mock_coordinator) -> None:
    """Test available property when device is not found."""
    mock_coordinator.data = {}
    assert climate_entity.available is False


def test_extra_state_attributes_device_not_found(
    climate_entity, mock_coordinator
) -> None:
    """Test extra state attributes when device is not found."""
    mock_coordinator.data = {}
    attrs = climate_entity.extra_state_attributes
    assert attrs == {}


@pytest.mark.asyncio
async def test_set_temperature_with_attr_temperature(
    climate_entity, mock_coordinator, mock_device
) -> None:
    """Test temperature setting using ATTR_TEMPERATURE."""
    await climate_entity.async_set_temperature(**{ATTR_TEMPERATURE: 24.0})
    mock_coordinator.client.set_thermostat_temperature.assert_called_once_with(
        mock_device.device_id, 24.0
    )
