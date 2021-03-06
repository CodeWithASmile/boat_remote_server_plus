import BV4111
import logging
import time
import threading

HEATER = 7
LIGHTS = 8

class Controller(object):
    """Provides functionality for controlling the GPIO board"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialising Relays...")
        sp = BV4111.sv3clV2_2.Connect("/dev/ttyAMA0",115200)
        self.devd = BV4111.bv4111(sp,'d')

        # Querying relay state always fails first time, returning an empty string. Get that out of the way here.
        self.devd.Send("i\r")
        self.devd.Read()

        self.logger.info("Relays initialised")
        self.reset_control()

    def reset_control(self):
        self.logger.info("Resetting Control")
        for i in range(1,8):
            self.devd.Rly(i,0,0)

    def get_relay_state(self, relay):
        """Takes a relay number (1-8) and returns current state (0 or 1)"""
        
        self.devd.Send("i\r")
        state = int(self.devd.Read())
        mask = 1 << (relay-1) 
        if mask & state > 0:
            return 1
        else:
            return 0

    def toggle_lights(self):
        current_state = self.get_relay_state(LIGHTS)
        if current_state == 1:
            self.devd.Rly(LIGHTS,0,0)
        else:
            self.devd.Rly(LIGHTS,1,0)

    def toggle_heater(self):
        current_state = self.get_relay_state(HEATER)
        if current_state == 1:
            self.devd.Rly(HEATER,0,0)
        else:
            self.devd.Rly(HEATER,1,0)

