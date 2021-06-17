# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Define the Client event generators
import pprint
import random
import logsim.ttime as tt


# class Estimator:
#     """
#     Class for holding an estimator used in the HI
#     """

#     def __init__(self, name, RAM, NVRAM, cfg):
#         self.name = name
#         self.count = 0
class Client:
    """
    Class for holding a clients HI with detctors and estimators and an App
    that can sample the logging data from the HI
    Init Parameters
    ---------------
    id: numeric
         An identification number unique to this client

    env: Reference to a simpy environment object

    data: Reference to a DataPool object

    cfg: Reference to a Configuration dict
    """

    def __init__(self, id, env, data, cfg):
        # Initialize variables
        self.id = id
        self.env = env
        self.last_updated_at = 0
        # self.power_cycle = 0
        # Size of NVRAM arrays
        self.nvram_array = cfg['nvram_array']
        self.nvram_month = cfg['nvram_month']
        # Estimators -     name        interval           length
        self.estimators = cfg['estimators']
        # Detectors -     name     interval
        self.detectors = cfg['detectors']
        # App
        self.app = cfg['app']
        self.min_period = tt.hms2sec(cfg['min_period'])
        self.max_period = tt.hms2sec(cfg['max_period'])
        self.times_pr_day = cfg['times_pr_day']
        self.verbosity = cfg['verbosity']
        self.sim_start = tt.str2time(cfg['sim_start'])
        self.data = data
        self.pp = pprint.PrettyPrinter(indent=2, width=170)
        # Declare
        self.RAM = {}
        self.NVRAM = []
        self.NVRAM_MONTH = []
        self.HI_running = False
        # Init memory
        self.init_memory()
        # Start the sessions and the detectors and estimators
        self.env.process(self.run_sessions())
        for d in self.detectors:
            self.env.process(self.run_detectors(d))
        for d in self.estimators:
            self.env.process(self.run_estimators(d))
        if self.app['on']:
            self.env.process(self.run_app())

    # Init Memory
    def init_memory(self):
        # Create RAM version of client-ID and usage
        self.RAM['id'] = self.id
        self.RAM['power_cycle'] = 0
        self.RAM['charge'] = 0
        self.RAM['usage'] = 0
        self.RAM['time'] = 0
        self.RAM['date'] = 0
        # Create RAM version of all detectors: (State, cnt)
        for d in self.estimators:
            self.RAM[d] = 0
        # Create RAM version of all detectors: (State, cnt)
        for d in self.detectors:
            self.RAM[d] = 0
        # Allocate NVRAM
        for k in range(self.nvram_array):
            self.NVRAM.append(self.RAM.copy())
        self.NVRAM_MONTH = [0] * self.nvram_month

    # Print date and time
    def now2str(self):
        return tt.time2str(self.sim_start + self.env.now)

    # Sessions
    def run_sessions(self):
        # Start in the morning...
        first_day = True
        pwr_cycle = 0
        month_cycle = 0
        while True:
            # Create index for RAM and MVRAM arrays
            pwr_cycle = self.RAM['power_cycle'] % self.nvram_array
            # Start by Charging
            cycle = int(24 / self.times_pr_day)
            tick = random.randint(self.min_period, self.max_period)
            chg = tt.hms2sec(
                '{}h'.format(cycle)) - tick + random.randint(0, 600) - 300
            if first_day:
                chg -= tt.hms2sec('8h')
                first_day = False
            # Check for negative time...
            chg = max(chg, 300)
            self.last_updated_at = self.env.now
            yield self.env.timeout(chg)

            # Start session (HI removed from Charger)
            self.HI_running = True
            if self.verbosity > 0:
                print('Usage started @', self.now2str(), ', Client: ', self.id)
            self.RAM['charge'] += self.env.now - self.last_updated_at
            self.RAM['time'] = 0
            self.last_updated_at = self.env.now
            yield self.env.timeout(tick)

            # End usage session (HI into Charger)
            self.HI_running = False
            self.update_usage()
            # Write date if set by App
            if self.RAM['time']:
                self.RAM['date'] = tt.time2date(self.RAM['time'])
            else:
                self.RAM['date'] = self.RAM['power_cycle']
            # Copy RAM to NVRAM
            for k in self.RAM.keys():
                self.NVRAM[pwr_cycle][k] = self.RAM[k]
            # Check if time to store monthly counters
            if self.nvram_month > 0 and pwr_cycle == 0:
                self.NVRAM_MONTH[month_cycle] = self.NVRAM[pwr_cycle].copy()
                month_cycle = (month_cycle + 1) % self.nvram_month
            # Usage ended
            if self.verbosity > 0:
                print('Usage ended   @',
                      self.now2str(), ', Client: ', self.id)
            # Show memory content
            if self.verbosity > 1:
                print('RAM:')
                self.pp.pprint(self.RAM)
                print('NVRAM:')
                self.pp.pprint(self.NVRAM)
            # inc power_cycle to prepare for next session
            self.RAM['power_cycle'] += 1

    # Update usage counter
    def update_usage(self):
        self.RAM['usage'] += self.env.now - self.last_updated_at
        self.last_updated_at = self.env.now

    # Pretty print RAM, NVRAM etc
    def pprint(self, dct):
        self.pp.pprint(dct)

    # Start HI detectors
    def run_detectors(self, d):
        while True:
            yield self.env.timeout(tt.hms2sec(self.detectors[d]))
            if self.HI_running:
                self.RAM[d] = self.RAM[d] + 1
                if self.verbosity > 3:
                    print('@ {}: {} fired, count = {}'.format(
                        self.env.now, d, self.RAM[d]))

    # Start HI estimators
    def run_estimators(self, d):
        while True:
            # Start estimator
            yield self.env.timeout(tt.hms2sec(self.estimators[d]['interval']))
            self.estimators[d]['last_updated'] = self.env.now
            if self.HI_running:
                if self.verbosity > 3:
                    print('@ {}: {} started'.format(self.env.now, d))
            # End estimator
            length = tt.hms2sec(self.estimators[d]['length'])
            if d == 'ovd':
                l2 = 6 * length
                length += self.RAM['power_cycle']
                length = min(l2, length)
            yield self.env.timeout(length)
            if self.HI_running:
                self.RAM[d] += (
                    self.env.now - self.estimators[d]['last_updated'])
                if self.verbosity > 3:
                    print('@ {}: {} ended, count = {}'.format(
                        self.env.now, d, self.RAM[d]))

    # Start App
    def run_app(self):
        app_tick = tt.hms2sec(self.app['interval'])
        app_data = {}
        last_data = {}
        while True:
            yield self.env.timeout(app_tick)
            if self.HI_running:
                self.update_usage()
                if self.RAM['time'] == 0 and self.app['set_time']:
                    self.RAM['time'] = self.sim_start + self.env.now
                app_data = self.RAM.copy()
                if (self.app['diff'] and (len(last_data) > 0)):
                    for e in self.estimators:
                        app_data[e] = '{:.1f}%'.format(
                            min(100.0, 100.0 * (
                                app_data[e] - last_data[e]) / app_tick))
                    for e in self.detectors:
                        app_data[e] = app_data[e] - last_data[e]
                # Set app time
                app_data['time'] = tt.time2str(self.sim_start + self.env.now)
                self.data.put(app_data)
                last_data = self.RAM.copy()
                if self.verbosity > 2:
                    print('@ {}: App: {}'.format(app_data['time'], app_data))
            else:
                last_data = self.RAM
