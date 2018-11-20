"""
Kohler platform that offers a kohler water_heater device to help control the shower.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/kohler/
"""

from homeassistant.components import kohler

from homeassistant.components.water_heater import (
    WaterHeaterDevice,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_OPERATION_MODE)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

STATE_ON = 'On'
STATE_OFF = 'Off'
STATE_PAUSED = 'Paused'

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Kohler water_heater devices."""

    add_entities([
        KohlerWaterHeater('Kohler DTV+ Shower', kohler.NETWORK)
    ])


class KohlerWaterHeater(WaterHeaterDevice):
    """Representation of a demo water_heater device."""

    def __init__(self, name, network):
        """Initialize the water_heater device."""
        self._name = name
        self._network = network

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the water_heater device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._network.data.degree_symbol == "&degF":
            return TEMP_FAHRENHEIT

        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._network.data.valve1Setpoint

    @property
    def current_operation(self):
        """Return current operation ie. Off, On, Paused."""
        return self._network.data.valve1_Currentstatus

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_OFF, STATE_ON, STATE_PAUSED]

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return None

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        return None

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        return None

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self.temperature_unit == TEMP_FAHRENHEIT:
            return 86

        return 30

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._network.data.max_temp