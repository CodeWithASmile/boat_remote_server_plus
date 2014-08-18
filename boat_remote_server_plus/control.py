import BV4111
import logging
import time
import threading

WATERMAKER_FLUSH = 5 #should not run without 6
WATERMAKER = 8 #6 Set to lights for testing purposes
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
        self.watermaker_timer = None
        self.reset_control()

    def reset_control(self):
        self.logger.info("Resetting Control")
        cancel_watermaker_timer()
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

    def turn_water_maker_on(self, mins):
        current_state = self.get_relay_state(WATERMAKER)
        if current_state == 1:
            self.logger.info("Watermaker already running")
            if (mins == 0):
                self.logger.info("Watermaker running indefinitely")
                self.cancel_watermaker_timer()
            else:
                self.logger.info("Ignoring command")
        else:
            self.devd.Rly(WATERMAKER,1,0)
            if (mins == 0):
                self.logger.info("Watermaker running indefinitely")
            else:
                self.logger.info("Watermaker running for %d mins" % mins)
                self.set_watermaker_timer(mins)


    def turn_water_maker_off(self):
        current_state = self.get_relay_state(WATERMAKER)
        if current_state == 0:
            self.logger.info("Watermaker already off")
        else:
            self.logger.info("Turning watermaker off")
            self.devd.Rly(WATERMAKER,0,0)
        self.cancel_watermaker_timer()

    def set_watermaker_timer(self, mins):
        self.watermaker_timer = Timer(mins, self.turn_water_maker_off)
        self.watermaker_timer.start()

    def cancel_watermaker_timer(self):
        if (self.watermaker_timer is not None):
            self.watermaker_timer.cancel()
        self.watermaker_timer = None

    def get_watermaker_status(self):
        current_state = self.get_relay_state(WATERMAKER)
        if current_state == 0:
            return "off"
        else:
            if self.watermaker_timer:
                return self.watermaker_timer.get_time_left()
            else:
                return "on"
        
class Timer(threading.Thread):

    def __init__(self, mins, function):
        self.duration = mins*60
        self.function = function
        self.active = False
        super(Timer, self).__init__()

    def start(self):
        self.target = time.time() + self.duration
        self.active = True
        super(Timer, self).start()

    def get_time_left(self):
        return (int(self.target-time.time()) % 60)

    def cancel(self):
        self.target = time.time()
        self.active=False

    def run(self):
        while (self.active):
            if (self.target < time.time()):
                self.active = False
                self.function()


