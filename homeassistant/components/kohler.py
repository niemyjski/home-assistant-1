"""
Support for KOHLER Shower.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/kohler/
"""
import asyncio
import logging
from datetime import timedelta

import requests
import aiohttp
from aiohttp.hdrs import CONTENT_TYPE
import async_timeout
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import CONF_IP_ADDRESS, CONTENT_TYPE_JSON, CONTENT_TYPE_TEXT_PLAIN
from homeassistant.util import Throttle

REQUIREMENTS = []

_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'kohler'

TIMEOUT = 10
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

NETWORK = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IP_ADDRESS): cv.string
    })
}, extra=vol.ALLOW_EXTRA)

class KohlerData:
    """Get the latest data and update the states."""

    def __init__(self, hass, config):
        """Init the Kohler data object."""
        self.data = dict()
        self.kohler = KohlerService(hass, config)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data from kohler api."""
        data = dict()

        # The following async methods catch and log the exception.
        # but this could result in each of these timing out...
        # Should look into raising the exception and bail early
        system = await self.kohler.async_get_system_info()
        if system is not None:
            data.update(system)

        values = await self.kohler.async_get_values()
        if values is not None:
            data.update(values)

        self.data = data
        _LOGGER.info("Kohler data updated successfully")


class KohlerService:
    """Talks to the kohler managed switch."""

    def __init__(self, hass, config):
        """Init the Kohler data object."""
        self._hass = hass
        self._config = config
        self._baseUrl = 'http://{}/'.format(config[DOMAIN].get(CONF_IP_ADDRESS))

    async def async_get_system_info(self):
        return await self._async_get(self._baseUrl + "system_info.cgi")

    async def async_get_values(self):
        return await self._async_get(self._baseUrl + "values.cgi")

    async def async_start_shower(self):
        return await self._async_get(self._baseUrl + "quick_shower.cgi?valve_num=2&valve2_outlet=0&valve2_massage=0&valve2_temp=100&valve1_temp=100&valve1_outlet=1&valve1_massage=0", CONTENT_TYPE_TEXT_PLAIN)

    async def async_stop_shower(self):
        return await self._async_get(self._baseUrl + "stop_shower.cgi", CONTENT_TYPE_TEXT_PLAIN)

    async def _async_get(self, url, content_type=CONTENT_TYPE_JSON):
        try:
            response = requests.get(url, headers={CONTENT_TYPE: content_type}, timeout=10)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as err:
            _LOGGER.exception("Error on %s : %s", url, err)
            return None

        if response.status_code != 200:
            _LOGGER.error("Error %s : %s", response.status_code, response.text())
            return None

        if content_type != CONTENT_TYPE_JSON:
            return response.text()

        return response.json()

    # https://github.com/aio-libs/aiohttp/issues/3402
    async def _async_get_fails(self, url, content_type=CONTENT_TYPE_JSON):
        try:
            client = async_get_clientsession(self._hass, verify_ssl=False)
            with async_timeout.timeout(TIMEOUT, loop=self._hass.loop):
                response = await client.get(url, headers={CONTENT_TYPE: content_type})

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.exception("Error on %s", url)
            return None

        if response.status != 200:
            await self.async_log_error(response)
            return None

        if content_type != CONTENT_TYPE_JSON:
            return await response.text()

        return await response.json()

    async def async_log_error(self, response):
        """Log error message."""
        _LOGGER.error(
            "Error %s : %s", response.status, await response.text())


async def async_setup(hass, config):
    """Set up the Kohler.

    Will automatically load shower and sensor components to support
    devices discovered on the network.
    """
    global NETWORK

    if 'kohler' in _CONFIGURING:
        return

    NETWORK = KohlerData(hass, config)
    await NETWORK.async_update()

    async def update_domain_interval(now):
        """Update the Kohler data."""
        await NETWORK.async_update()

    async_track_time_interval(hass, update_domain_interval, MIN_TIME_BETWEEN_UPDATES)

    setup_kohler(hass, config)
    return True


def setup_kohler(hass, config):
    """Set up the Kohler shower."""
    #discovery.load_platform(hass, 'binary_sensor', DOMAIN, {}, config) # presence, valves, temp,
    #discovery.load_platform(hass, 'sensor', DOMAIN, {}, config) # motion, version, status
    #discovery.load_platform(hass, 'switch', DOMAIN, {}, config) # current user
    discovery.load_platform(hass, 'water_heater', DOMAIN, {}, config)