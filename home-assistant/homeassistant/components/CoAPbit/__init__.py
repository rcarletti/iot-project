# """The CoAPbit component."""
# import logging

# import voluptuous as vol

# from coapthon.client.helperclient import HelperClient

# from pint import UnitRegistry

# from homeassistant import config_entries
# from homeassistant.const import (
#     CONF_BINARY_SENSORS, CONF_FILENAME, CONF_MONITORED_CONDITIONS,
#     CONF_SENSORS, CONF_STRUCTURE, EVENT_HOMEASSISTANT_START,
#     EVENT_HOMEASSISTANT_STOP)
# from homeassistant.helpers import config_validation as cv
# from homeassistant.helpers.entity import Entity

# from .const import DOMAIN

# _CONFIGURING = {}
# _LOGGER = logging.getLogger(__name__)

# DATA_COAPBIT = 'coapbit'
# DATA_COAPBIT_CONFIG = 'coapbit_config'

# CONF_IP_ADDRESS = 'address'
# CONF_COAP_PORT = 'port'

# DEFAULT_COAP_PORT = 5683

# COAPBIT_RESOURCES_LIST = {
#     'activities/steps': ['Steps', 'steps', 'mdi:shoe-print', 0],
#     'activities/calories': ['Calories', 'cal', 'mdi:fire', 0],
#     'devices/battery': ['Battery', '%', None, '100'],
#     'activities/heart': ['Heart', 'bpm', 'mdi:heart-pulse', 0],
#     'activities/distance': ['Distance', 'km', 'mdi:map-marker', 0],
# }

# CONFIG_SCHEMA = vol.Schema({
#     DOMAIN: vol.Schema({
#         vol.Required(CONF_IP_ADDRESS): cv.string,
#         vol.Optional(CONF_COAP_PORT, default=DEFAULT_COAP_PORT): int,
#     })
# }, extra=vol.ALLOW_EXTRA)

# async def async_setup(hass, config):
#     """Set up CoAPbit components."""
#     print("async_setup")

#     if DOMAIN not in config:
#         return True

#     conf = config[DOMAIN]

#     hass.async_create_task(hass.config_entries.flow.async_init(
#         DOMAIN,
#         context={'source': config_entries.SOURCE_IMPORT},
#         data={}
#     ))

#     # Store config to be used during entry setup
#     hass.data[DATA_COAPBIT_CONFIG] = conf

#     return True

# async def async_setup_entry(hass, entry, async_add_entities):
#     """Set up CoAPbit from a config entry."""
#     print("async_setup_entry")

#     ureg = UnitRegistry()
#     ureg.load_definitions('/home/rossella/home-assistant/homeassistant/components/CoAPbit/unit_def.txt')

#     conf = hass.data.get(DATA_COAPBIT_CONFIG, {})

#     hass.data[DATA_COAPBIT] = CoAPbitDevice(conf)

#     dev = []
#     for resource in COAPBIT_RESOURCES_LIST:
#         client = HelperClient(server=(conf[CONF_IP_ADDRESS], conf[CONF_COAP_PORT]))
#         dev.append(CoAPbitSensor(client, resource, ureg))

#     async_add_entities(dev, True)
#     return True


# class CoAPbitDevice:
#     """The CoAPbit device."""

#     def __init__(self, conf):
#         print("coapbit device")


# class CoAPbitSensor(Entity):
#     """Implementation of a CoAPbit sensor."""

#     def __init__(self, client, resource_type, ureg):
#         """Initialize the CoAPbit """
#         print("sensor")

#         self._client = client
#         self._resource_type = resource_type
#         self._state = COAPBIT_RESOURCES_LIST[self._resource_type][3]
#         self._name = COAPBIT_RESOURCES_LIST[self._resource_type][0]
#         self._unit_of_measurement = COAPBIT_RESOURCES_LIST[self._resource_type][1]
#         self._msg = {}
#         self._last_response = None
#         self._icon = COAPBIT_RESOURCES_LIST[self._resource_type][2]
#         self._ureg = ureg

#         self._client.observe(self._name, self.client_callback_observe)

#     @property
#     def name(self):
#         """Return the name of the sensor."""
#         return self._name

#     @property
#     def unit_of_measurement(self):
#         """Return the unit of measurement of this entity, if any."""
#         return self._unit_of_measurement

#     @property
#     def state(self):
#         """Return the state of the sensor."""
#         return self._state


#     @property
#     def icon(self):
#         """Icon to use in the frontend, if any."""
#         return self._icon

#     @property
#     def device_state_attributes(self):
#         """Return the state attributes."""
#         return {}

#     def set_alarm(self, **kwargs):
#         print(" **** mannagg' a soreta ****")
#         print("  and whoever is most dead to you  ")

#     def client_callback_observe(self, response):
#         if response is not None:
#             try:
#                 self._msg = json.loads(response.payload)
#                 self._last_response = response
#             except:
#                 print(response.payload)
#                 return
#             try:
#                 # check the unit of measurement
#                 unit = self._msg["e"]["u"]
#                 if unit == self._unit_of_measurement:
#                     raw_state = self._msg["e"]["v"]
#                 else:
#                     # convert to the desired u.of m.
#                     data = self._msg["e"]["v"] * self._ureg.parse_expression(unit)
#                     raw_state = data.to(self._ureg.parse_expression(self._unit_of_measurement)).magnitude

#                 if self._name == 'Distance':
#                     self._state = format(float(raw_state), '.2f')
#                 else:
#                     self._state = format(float(raw_state), '.0f')


#             except KeyError:
#                 pass

#     def update(self):
#         """Get the latest data from the Fitbit API and update the states."""
