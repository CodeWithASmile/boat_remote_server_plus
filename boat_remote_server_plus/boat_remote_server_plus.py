#!/usr/bin/python
# -*- coding: utf-8 -*-

## Web server for providing NMEA data to a Pebble watch
# Teresa Roberts (c) 2014
# http://www.codewithasmile.co.uk
#
# Based on the excellent work of Mike Holden
# http://www.holdentechnology.com/

from socket import *
from select import *
import time, sys
import json
import BaseHTTPServer
import urlparse
import os
import logging.config

import pynmea2

from helper_functions import *
from nmea_data_source import NmeaDataSource
from config import *

def setup_logging(default_path='logging.json', default_level=logging.INFO,
    env_key='LOG_CFG'):
    path = basePath + "/" + default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            loggingConfig = json.load(f)
        logging.config.dictConfig(loggingConfig)
    else:
        logging.basicConfig(level=default_level)

def set_anchor_watch():
    awf = nmeaDataSource.getWatchField("drift")
    awf.__class__ = AnchorWatchField
    awf.setAnchor()

def set_anchor_watch_loc(lat,lon):
    awf = nmeaDataSource.getWatchField("drift")
    awf.__class__ = AnchorWatchField
    awf.setAnchorLoc(lat,lon)

def reset_anchor_watch():
    awf = nmeaDataSource.getWatchField("drift")
    awf.__class__ = AnchorWatchField
    awf.resetAnchor()

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        """Respond to a GET request."""
        # Send response headers
        logger.debug("GET: %s" % self.path)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        path = self.path.lstrip('/')
        if (path == "watch"):
            if test:
                # Get mocked up data from helper_functions
                data = json.dumps(testWatchData)
            else:
                # Get the latest data from the nmeaDataSource
                logger.debug("Printing watch data")
                data = nmeaDataSource.printWatchData()
        elif (path=="NMEA"):
            logger.debug("Printing all sentences")
            data = nmeaDataSource.printAllSentences() 
        else:
            data = ""    
        self.wfile.write(data)

    def do_POST(self):
        """Respond to a POST request."""
        # Send response headers
        logger.debug("POST: %s" % self.path)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        path = self.path.lstrip('/')
        if (path == "toggle_lights"):
            logger.debug("Toggling Lights!")
            controller.toggle_lights()
        if (path == "set_anchor_watch"):
            logger.debug("Setting Anchor Watch")
            params = getParams(["lat","lon"])
            if len(params) == 2:
                set_anchor_watch_loc(params["lat"],params["lon"])
            else:
                set_anchor_watch()
        if (path == "reset_anchor_watch"):
            logger.debug("Resetting Anchor Watch")
            reset_anchor_watch()
        if (path == "water_maker_on"):
            logger.debug("Turning Watermaker On")
            params = getParams(["mins"])
            if len(params) == 1:
                turn_watermaker_on(params["mins"])
            else:
                logger.error("No time for turning watermaker on")
        if (path == "watermaker_off"):
            logger.debug("Turning Watermaker Off")
            turn_water_maker_off()

    def getParams(self, params):
            parsed_params = {}
            length = int(self.headers['Content-Length'])
            post_data = urlparse.parse_qs(self.rfile.read(length).decode('utf-8'))
            logger.debug("Parameters received: %s" % post_data)
            for p in params:
                if (post_data.has_key(p)):
                    parsed_params[p] = post_data[p][0]
            return parsed_params
            
        

if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger(__name__)
    if control:
        from control import Controller
        controller = Controller()
    # initialize tcp port
    nmeaDataSource = NmeaDataSource(NMEA_HOST, NMEA_PORT, watchFields)
    if not test:
        nmeaDataSource.connect()
        nmeaDataSource.start()

    httpd = BaseHTTPServer.HTTPServer((HTTP_HOST, HTTP_PORT), MyHandler)
    logger.info(time.asctime() + " Server Starts - %s:%s" % (HTTP_HOST, HTTP_PORT))
    try:
        logger.info("Serving Forever")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Interrupted By Keyboard")
    try:
        controller.reset_control()
    except:
        pass
    nmeaDataSource.close()
    nmeaDataSource.join()
    httpd.server_close()
    logger.info(time.asctime(), "Server Stops - %s:%s" % (HTTP_HOST, HTTP_PORT))

    ##===================================
