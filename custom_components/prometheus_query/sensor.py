import logging
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from datetime import timedelta
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_DEVICE_CLASS,
    CONF_UNIQUE_ID,
    STATE_UNKNOWN,
)
from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA,
)

CONF_PROMETHEUS_URL = 'prometheus_url'
CONF_PROMETHEUS_QUERY = 'prometheus_query'
SCAN_INTERVAL = timedelta(seconds=600)

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PROMETHEUS_URL): cv.string,
    vol.Required(CONF_PROMETHEUS_QUERY): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
    vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    prom_data = {
        'url': str(config.get(CONF_PROMETHEUS_URL)) + "/api/v1/query",
        'query': str(config.get(CONF_PROMETHEUS_QUERY)),
        'name': str(config.get(CONF_NAME)),
        'unit': str(config.get(CONF_UNIT_OF_MEASUREMENT)),
        'state_class': str(config.get(CONF_STATE_CLASS)),
        'device_class': str(config.get(CONF_DEVICE_CLASS)),
        'unique_id': str(config.get(CONF_UNIQUE_ID)),
    }

    add_entities([PrometheusQuery(prom_data)], True)


class PrometheusQuery(SensorEntity):
    """Representation of a Sensor based on Prometheus"""

    def __init__(self, prom_data):
        """Initialize the sensor."""
        self._url = prom_data["url"]
        self._query = prom_data["query"]
        self._attr_name = prom_data["name"]
        self._state = None
        self._attr_native_unit_of_measurement = prom_data["unit"]
        self._attr_state_class = prom_data["state_class"]
        self._attr_device_class = prom_data["device_class"]
        self._attr_unique_id = f"${prom_data['url']}$${prom_data['query']}"
        if prom_data["unique_id"] is not None:
            self._attr_unique_id = prom_data["unique_id"]

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        response_value = STATE_UNKNOWN
        try:
            response = requests.get(self._url, params={'query': self._query})
        except requests.RequestException:
            _LOGGER.exception("Error when querying Prometheus")
        else:
            if response.ok:
                try:
                    json = response.json()
                except requests.exceptions.JSONDecodeError:
                    _LOGGER.exception("Unable to decode response from Prometheus")
                else:
                    if 'data' in json and 'result' in json['data']:
                        if len(json['data']['result']):
                            self._attr_native_value = json['data']['result'][0]['value'][1]

        # Update attributes
        self._attr_native_value = response_value
        self._attr_state = self._attr_native_value
