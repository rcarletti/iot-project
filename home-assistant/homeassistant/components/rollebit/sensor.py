"""Support for the Rollebit system."""
import os
import logging
import datetime
import time
import getopt
import socket
import sys

from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri

from bs4 import BeautifulSoup

import requests

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.const import CONF_UNIT_SYSTEM
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
import homeassistant.helpers.config_validation as cv
from homeassistant.util.json import load_json, save_json


_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

CONF_SERVER_URI = 'server_uri'
DEFAULT_SERVER_URI = "coap://[aaaa::c30c:0:0:2]:5683/steps"

CONF_BR_URI = 'br_uri'
DEFAULT_BR_URI = "http://[aaaa::c30c:0:0:1]/.well-known"

ROLLEBIT_DEFAULT_RESOURCES = ['activities/steps']

SCAN_INTERVAL = datetime.timedelta(seconds=1)

ROLLEBIT_RESOURCES_LIST = {
    'activities/steps': ['Steps', 'steps', 'walk'],
}

ICON = 'mdi:chart-line'

ROLLEBIT_MEASUREMENTS = {
    'metric': {
        'distance': 'kilometers',
    }
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SERVER_URI, default=DEFAULT_SERVER_URI): cv.string,
    vol.Optional(CONF_BR_URI, default=DEFAULT_BR_URI): cv.string

})

global dev

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Rollebit sensor."""
    global dev 

    #creazione client coap
    host, port, path = parse_uri(config.get(CONF_SERVER_URI))

    coap_client = HelperClient(server=(host, port))

    #istanzio l'entità 
    dev = RollebitSensor(coap_client, path)

    async_add_entities([dev])
    return True


class RollebitSensor(Entity):
    """Implementation of a Rollebit sensor."""

    def __init__(self, client, path):
        """Initialize the Rollebit sensor."""
        self.client = client
        self.path = path
        self._name = 'Steps'
        self._unit_of_measurement = 'steps'
        self._state = None
        self._resource_addr_list = []

        self.client.observe(self.path, self.client_callback_observe)
        self.retrieve_nodes(DEFAULT_BR_URI)
        

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {}

    def retrieve_nodes(self, br_uri):
        # http-get to BR router
        r = requests.get(br_uri)
        html_doc = r.text
        #retrieve nodes addresses
        soup = BeautifulSoup(html_doc, 'html.parser')
        print('************************************')
        addr_list = soup.find_all('pre')[1]

        print('************************************')


        for string in addr_list.stripped_strings:
            # split single addresses    
            addrs = string.split('\n')
            for addr in addrs:
                tmp = addr.split('/')
                self._resource_addr_list.append('coap://['+ tmp[0] + ']:5683')

        
        print('************************************')
        print(*self._resource_addr_list)


    def client_callback_observe(self, response): 
        if response is not None:
            self._state = response.payload
    

    def update(self):
        """Get the latest data from the Fitbit API and update the states."""
        #response = self.client.get(self.path)
        







