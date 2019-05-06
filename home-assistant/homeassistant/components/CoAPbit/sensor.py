"""Support for the CoAPbit system."""
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

import json


_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

CONF_SERVER_URI = 'server_uri'
DEFAULT_SERVER_URI = "coap://[aaaa::c30c:0:0:2]:5683/steps"

CONF_BR_URI = 'br_uri'
DEFAULT_BR_URI = "http://[aaaa::201:1:1:1]/.well-known"

CONF_COAP_PORT = 'port'
DEFAULT_COAP_PORT = 5683

CONF_MONITORED_RESOURCES = 'monitored_resources'
DEFAULT_MONITORED_RESOURCES = ['activities/steps',
                             'activities/calories',
                             'devices/battery',
                             'activities/heart']

SCAN_INTERVAL = datetime.timedelta(seconds=1)

# [name, unit of measurement, icon, default state]
CoAPBIT_RESOURCES_LIST = {
    'activities/steps': ['Steps', 'steps', 'mdi:shoe-print', '0'],
    'activities/calories': ['Calories', 'cal', 'mdi:fire', '0'],
    'devices/battery': ['Battery', '%', None, '100'],
    'activities/heart': ['Heart', 'bpm', 'mdi:heart-pulse', '0'],
}

CoAPBIT_MEASUREMENTS = {
    'metric': {
        'distance': 'kilometers',
    }
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SERVER_URI, default=DEFAULT_SERVER_URI): cv.string,
    vol.Optional(CONF_BR_URI, default=DEFAULT_BR_URI): cv.string,
    vol.Optional(CONF_COAP_PORT, default=DEFAULT_COAP_PORT): int,
    vol.Optional(CONF_MONITORED_RESOURCES, default=DEFAULT_MONITORED_RESOURCES):
        vol.All(cv.ensure_list, [vol.In(CoAPBIT_RESOURCES_LIST)])
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the CoAPbit sensor."""
    dev = [] 
    resource_addr_list = []

    retrieve_nodes(DEFAULT_BR_URI, resource_addr_list)
    
    # create a coap client for each node
    for addr in resource_addr_list:
        #for each client create one entity for each sensor
        for resource in config.get(CONF_MONITORED_RESOURCES):
            coap_client = HelperClient(server=(addr, config.get(CONF_COAP_PORT)))
            dev.append(CoAPbitSensor(coap_client, resource))

    async_add_entities(dev, True)
    return True


class CoAPbitSensor(Entity):
    """Implementation of a CoAPbit sensor."""

    def __init__(self, client, resource_type):
        """Initialize the CoAPbit """
        self._client = client
        self._resource_type = resource_type
        self._state = CoAPBIT_RESOURCES_LIST[self._resource_type][3]
        self._name = CoAPBIT_RESOURCES_LIST[self._resource_type][0]
        self._unit_of_measurement = CoAPBIT_RESOURCES_LIST[self._resource_type][1]
        self._msg = {}
        self._last_response = None

        if self._name != 'devices/battery':
            self._icon = CoAPBIT_RESOURCES_LIST[self._resource_type][2]
        else:
            if self._state == 100:
                self._icon = 'mdi:battery'
            else:
                self._icon = 'mdi:battery-' + self._state

        self._client.observe(self._name, self.client_callback_observe)



    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state


    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {}


    def client_callback_observe(self, response): 
        if response is not None:
            try:
                self._msg = json.loads(response.payload)
                self._last_response = response
            except:
                print(response.payload)
                return
            try:
                self._state = int(self._msg["e"]["v"])
                print(self._msg)
            except KeyError:
                pass


    def update(self):
        """Get the latest data from the Fitbit API and update the states."""
        #response = self.client.get(self.path)


def retrieve_nodes(br_uri, resource_addr_list):
        # http-get to BR router
        r = requests.get(br_uri)
        html_doc = r.text
        #retrieve nodes addresses
        soup = BeautifulSoup(html_doc, 'html.parser')
        addr_list = soup.find_all('pre')[1]


        for string in addr_list.stripped_strings:
            # split single addresses    
            addrs = string.split('\n')
            for addr in addrs:
                tmp = addr.split('/')
                resource_addr_list.append(tmp[0])


        





