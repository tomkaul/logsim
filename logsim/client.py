# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Define the Client event generators
import pprint
import random
import logsim.ttime as tt


class App:
    """
    Class for holding an App connected with HI
    Can call and get HI counters
    Can set the time (date) in the HI
    """

    # Constructor
    def __init__(self, HI, env, cdp, cfg, verbosity=3):
        self.HI = HI
        self.env = env
        self.cdp = cdp
        self.interval = cfg['interval']
        self.diff = cfg['diff']
        self.set_time = cfg['set_time']
        self.verbosity = verbosity
        self.timelog = {}
        # Start the App
        self.env.process(self.run())

    # Run the App
    def run(self):
        app_tick = tt.hms2sec(self.interval)
        app_data = {}
        last_data = {}
        while True:
            yield self.env.timeout(app_tick)
            if self.HI.is_running():
                # Set timestamp in HI (TE31d)
                if self.set_time:
                    self.HI.set_time(self.env.now)
                # Get counters
                RAM = self.HI.get_counters_RAM()
                for k in RAM.keys():
                    app_data[k] = RAM[k]
                # Update timelog
                if app_data['power_cycle'] not in self.timelog.keys():
                    self.timelog[app_data['power_cycle']] = (
                        self.HI.now2str(), app_data['usage'])
                if (self.diff and (len(last_data) > 0)):
                    for e in self.HI.estimators:
                        app_data[e] = '{:.1f}%'.format(
                            100.0 * (app_data[e] - last_data[e]) / app_tick)
                    for e in self.HI.detectors:
                        app_data[e] = app_data[e] - last_data[e]
                # Update to app time
                app_data['time'] = self.HI.now2str()
                self.cdp.put(app_data)
                for k in RAM.keys():
                    last_data[k] = RAM[k]
                if self.verbosity > 2:
                    print('@ {}: App: {}'.format(app_data['time'], app_data))
            # else:
            #     last_data = self.HI.get_counters_RAM()


class Estimator:
    """
    Class for holding an estimator used in the HI
    """

    # Constructor
    def __init__(self, name, HI, env, RAM, cfg, parent_running, verbosity):
        self.name = name
        self.HI = HI
        self.env = env
        self.RAM = RAM
        self.count = 0
        self.last_updated = 0
        self.interval = tt.hms2sec(cfg['interval'])
        self.length = tt.hms2sec(cfg['length'])
        self.org_length = self.length
        self.running = False
        self.parent_running = parent_running
        self.verbosity = verbosity
        self.inc_d = tt.hms2sec(cfg['inc_d']) if 'inc_d' in cfg else 0
        self.inc_m = tt.hms2sec(cfg['inc_m']) if 'inc_m' in cfg else 0
        # Start the estimator
        self.env.process(self.run())

    # Update counter
    def update_counter(self):
        if self.running:
            self.RAM[self.name] += self.env.now - self.last_updated
            self.last_updated = self.env.now

    # Set parent
    def set_parent(self, parent):
        self.parent_running = parent

    # Inc length
    def increase_daily(self):
        # Pick-up on length?
        if self.inc_d:
            # Max 3 times initial length
            self.length = min(3*self.org_length, self.length + self.inc_d)

    # Inc length
    def increase_monthly(self):
        # Pick-up on length?
        if self.inc_m:
            # Max 3 times initial length
            self.length = min(4*self.org_length, self.length + self.inc_m)

    # Run the Estimator
    def run(self):
        # Default length
        length = 0
        while True:
            # Depend on HI running
            if self.parent_running():
                # Start estimator
                yield self.env.timeout(self.interval-length)
                self.running = True
                self.last_updated = self.env.now
                if self.verbosity > 3:
                    print('@ {}: {} started'.format(
                        self.HI.now2str(), self.name))
                # End estimator
                yield self.env.timeout(self.length)
                # Update counter
                self.update_counter()
                if self.verbosity > 3:
                    print('@ {}: {} ended, count = {}'.format(
                        self.HI.now2str(), self.name, self.RAM[self.name]))
                self.running = False
            else:
                # Kill time
                yield self.env.timeout(self.interval)


class HI:
    """
    Class for holding a HI with detctors and estimators and an App
    that can sample the logging data from the HI
    Init Parameters
    ---------------
    id: numeric
         An identification number unique to this HI

    env: Reference to a simpy environment object

    data: Reference to a DataPool object

    cfg: Reference to a Configuration dict
    """

    # Constructor
    def __init__(self, id, env, cdp, cfg):
        # Initialize variables
        self.HI_running = False
        self.id = id
        self.env = env
        self.last_updated_at = 0
        # self.power_cycle = 0
        # Size of NVRAM arrays
        self.nvram_array = cfg['nvram_array']
        self.nvram_month = cfg['nvram_month']
        # Estimators
        self.estimators = {}
        # Detectors
        self.detectors = cfg['detectors']
        # App
        self.app = 0
        self.min_period = tt.hms2sec(cfg['min_period'])
        self.max_period = tt.hms2sec(cfg['max_period'])
        self.times_pr_day = cfg['times_pr_day']
        self.verbosity = cfg['verbosity']
        self.sim_start = tt.str2time(cfg['sim_start'])
        # self.data = data
        self.pp = pprint.PrettyPrinter(indent=2, width=170)
        # Declare
        self.RAM = {}
        self.NVRAM = []
        self.NVRAM_MONTH = []
        # Init memory
        self.init_memory(cfg)
        # Start daily ticks
        self.env.process(self.run_daily())
        # Start the sessions and the detectors and estimators
        self.env.process(self.run_sessions())
        for d in self.detectors:
            self.env.process(self.run_detectors(d))
        for d in cfg['estimators']:
            # Start estimators
            self.estimators[d] = Estimator(
                d, self, self.env, self.RAM, cfg['estimators'][d],
                self.is_running, self.verbosity)
        if cfg['app']['on']:
            self.app = App(self, self.env, cdp, cfg['app'], self.verbosity)

    # Check if running
    def is_running(self):
        return self.HI_running

    # Return RAM
    def get_counters_RAM(self):
        self.update_usage()
        self.update_estimators()
        return self.RAM

    # Return NVRAM
    def get_counters_NVRAM(self):
        return self.NVRAM

    # Update usage counter
    def update_usage(self):
        if (self.HI_running and (self.env.now > self.last_updated_at)):
            self.RAM['usage'] += self.env.now - self.last_updated_at
            self.last_updated_at = self.env.now

    # Update estimator counters
    def update_estimators(self):
        if (self.HI_running):
            for e in self.estimators.keys():
                self.estimators[e].update_counter()

    # Set time from App
    def set_time(self, time_stamp):
        if self.RAM['time'] == 0:
            self.RAM['time'] = self.sim_start + time_stamp
            self.RAM['date'] = tt.time2date(self.RAM['time'])

    # Init Memory
    def init_memory(self, cfg):
        # Create RAM version of HI-ID and usage
        self.RAM['id'] = self.id
        self.RAM['power_cycle'] = 0
        self.RAM['charge'] = 0
        self.RAM['usage'] = 0
        self.RAM['time'] = 0
        self.RAM['date'] = 0
        # Create RAM version of all detectors: (State, cnt)
        for d in cfg['estimators']:
            self.RAM[d] = 0
        # Create RAM version of all detectors: (State, cnt)
        for d in cfg['detectors']:
            self.RAM[d] = 0
        # Allocate NVRAM
        for k in range(self.nvram_array):
            self.NVRAM.append(self.RAM.copy())
        for k in range(self.nvram_month):
            self.NVRAM_MONTH.append(self.RAM.copy())

    # Print date and time
    def now2str(self):
        return tt.time2str(self.sim_start + self.env.now)

    # Run daily
    def run_daily(self):
        t_24h = tt.hms2sec('24h')
        cnt = 0
        while True:
            yield self.env.timeout(t_24h)
            # Inc daily counter
            cnt += 1
            # Increase estimators
            for e in self.estimators.keys():
                self.estimators[e].increase_daily()
            if self.verbosity > 0:
                print('Daily tick    @', self.now2str(),
                      ', HI: ', self.id, ', day:   ', cnt)
            if (cnt % 30 == 0):
                # Increase estimators
                for e in self.estimators.keys():
                    self.estimators[e].increase_monthly()
                if self.verbosity > 0:
                    print('Monthly tick  @', self.now2str(),
                          ', HI: ', self.id, ', month: ', int(cnt/30))

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
                print('Usage started @', self.now2str(), ', HI: ', self.id)
            self.RAM['charge'] += self.env.now - self.last_updated_at
            self.RAM['time'] = 0
            self.last_updated_at = self.env.now
            yield self.env.timeout(tick)

            # End usage session (HI into Charger)
            self.HI_running = False
            self.update_usage()
            # Write date if set by App
            if self.RAM['time'] == 0:
                self.RAM['date'] = self.RAM['power_cycle']
            # Copy RAM to NVRAM
            for k in self.RAM.keys():
                self.NVRAM[pwr_cycle][k] = self.RAM[k]
            # Check if time to store monthly counters
            if self.nvram_month > 0 and pwr_cycle == 0:
                for k in self.NVRAM[pwr_cycle]:
                    self.NVRAM_MONTH[month_cycle][k] = self.NVRAM[pwr_cycle][k]
                month_cycle = (month_cycle + 1) % self.nvram_month
            # Usage ended
            if self.verbosity > 0:
                print('Usage ended   @',
                      self.now2str(), ', HI: ', self.id)
            # Show memory content
            if self.verbosity > 1:
                print('RAM:')
                self.pp.pprint(self.RAM)
                print('NVRAM:')
                self.pp.pprint(self.NVRAM)
            # inc power_cycle to prepare for next session
            self.RAM['power_cycle'] += 1

    # Pretty print RAM, NVRAM etc
    def pprint(self, dct):
        self.pp.pprint(dct)

    # Start HI detectors
    def run_detectors(self, d):
        while True:
            yield self.env.timeout(tt.hms2sec(self.detectors[d]))
            if self.is_running():
                self.RAM[d] = self.RAM[d] + 1
                if self.verbosity > 3:
                    print('@ {}: {} fired, count = {}'.format(
                        self.env.now, d, self.RAM[d]))
