"""Support for the CoAPbit system."""
import os
import logging
import datetime
import time
import getopt
import socket
import sys
import pint
import threading

from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri
from pint import UnitRegistry

from bs4 import BeautifulSoup

import requests
import voluptuous as vol
import json

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

CONF_NODE_URI = 'node_uri'
DEFAULT_NODE_URI = "aaaa::202:2:2:2"

CONF_BR_URI = 'br_uri'
DEFAULT_BR_URI = "http://[aaaa::201:1:1:1]/.well-known"

CONF_COAP_PORT = 'port'
DEFAULT_COAP_PORT = 5683

CONF_MONITORED_RESOURCES = 'monitored_resources'
DEFAULT_MONITORED_RESOURCES = ['activities/steps',
                             'activities/calories',
                             'devices/battery',
                             'activities/heart',
                             'activities/distance',
                             'calendar'
                             ]

SCAN_INTERVAL = datetime.timedelta(seconds=10)

# [name, unit of measurement, icon, default state]
CoAPBIT_RESOURCES_LIST = {
    'activities/steps': ['Steps', 'steps', 'mdi:shoe-print', 0],
    'activities/calories': ['Calories', 'kcal', 'mdi:fire', 0],
    'devices/battery': ['Battery', '%', None, '100'],
    'activities/heart': ['Heart', 'bpm', 'mdi:heart-pulse', 0],
    'activities/distance': ['Distance', 'km', 'mdi:map-marker', 0],
    'calendar': ['Calendar' , None, 'mdi:calendar', 'calendar not set'],

}

CoAPBIT_MEASUREMENTS = {
    'metric': {
        'distance': 'kilometers',
    }
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NODE_URI, default=DEFAULT_NODE_URI): cv.string,
    vol.Optional(CONF_BR_URI, default=DEFAULT_BR_URI): cv.string,
    vol.Optional(CONF_COAP_PORT, default=DEFAULT_COAP_PORT): int,
    vol.Optional(CONF_MONITORED_RESOURCES, default=DEFAULT_MONITORED_RESOURCES):
        vol.All(cv.ensure_list, [vol.In(CoAPBIT_RESOURCES_LIST)])
})

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the CoAPbit platform."""
    ureg = UnitRegistry()
    dev = []

    node_addr_list = []
    retrieve_nodes(DEFAULT_BR_URI, node_addr_list)

    for addr in node_addr_list:
        if addr == config.get(CONF_NODE_URI):
            calendar_client = HelperClient(server=(addr, config.get(CONF_COAP_PORT)))
            set_datetime(calendar_client,"Calendar")
            #for each client create one entity for each sensor
            for resource in config.get(CONF_MONITORED_RESOURCES):
                coap_client = HelperClient(server=(addr, config.get(CONF_COAP_PORT)))
                dev.append(CoAPbitSensor(coap_client, resource, ureg))
        else:
            print('Device not found')
            return False

    async_add_entities(dev, True)
    return True


class CoAPbitSensor(Entity):
    """Implementation of a CoAPbit sensor."""

    def __init__(self, client, resource_type, ureg):
        """Initialize the CoAPbit """
        self._client = client
        self._resource_type = resource_type
        self._state = CoAPBIT_RESOURCES_LIST[self._resource_type][3]
        self._name = CoAPBIT_RESOURCES_LIST[self._resource_type][0]
        self._unit_of_measurement = CoAPBIT_RESOURCES_LIST[self._resource_type][1]
        self._msg = {}
        self._last_response = None
        self._icon = CoAPBIT_RESOURCES_LIST[self._resource_type][2]
        self._ureg = ureg
        self._prev_time = datetime.datetime.now()

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
        if response is None:
            return

        try:
            self._msg = json.loads(response.payload)
            self._last_response = response
        except:
            print(response.payload)
            return

        try:
            if self._name is not 'Calendar':
                # check the unit of measurement
                unit = self._msg["e"]["u"]
                if unit == self._unit_of_measurement:
                    raw_state = self._msg["e"]["v"]
                else:
                    # convert to the desired u.of m.
                    data = self._msg["e"]["v"] * self._ureg.parse_expression(unit)
                    raw_state = data.to(self._ureg.parse_expression(self._unit_of_measurement)).magnitude

                if self._name == 'Distance':
                    self._state = format(float(raw_state), '.2f')
                else:
                    self._state = format(float(raw_state), '.0f')
            else:
                mins = self._msg["min"]
                hour = self._msg["hour"]
                day = self._msg["day"]
                month = self._msg["month"]
                year = self._msg["year"]

                self._state = '{}/{}/{} \n {:02}:{:02}'.format(day, month, year, hour, mins)
        except KeyError:
            pass

    def update(self):
        if self._name == 'Calendar':
            now = datetime.datetime.now()
            now_delta = datetime.timedelta(hours=now.hour,\
                        minutes=now.minute,\
                        seconds=now.second)
            prev_delta = datetime.timedelta(hours=self._prev_time.hour,\
                        minutes = self._prev_time.minute, \
                        seconds = self._prev_time.second)
            delta = now_delta - prev_delta
            if(delta > datetime.timedelta(minutes = 1)):
                self._prev_time = now
                set_datetime(self._client, self._resource_type)
                print('set time')


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


def set_datetime(client, path):
    currentDT = datetime.datetime.now()
    year = currentDT.year
    month = currentDT.month
    day = currentDT.day
    hour = currentDT.hour
    minute = currentDT.minute
    second = currentDT.second

    payload = "day=" + str(day) + "&" + \
                "month=" + str(month) + '&' + \
                "year=" + str(year) + '&' + \
                "sec=" + str(second) + '&' + \
                "min=" + str(minute) + '&' + \
                "hour=" + str(hour)

    client.post(path, payload)
