# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Define the Client event generators
# import matplotlib.pyplot as plt
# import logsim.hi as HI
import logsim.ttime as tt


class App:
    """
    Class for holding an App connected with HI
    Can call and get HI counters
    """

    # Constructor
    def __init__(self, HI, env, cdp, cfg, verbosity, sim_start):
        """
        Constructor of an App

        Parameters
        ----------
        HI : HI
        env : simpy.env
        cdp : CDP, Common Data Platform
        cfg : JSON, Configuration parameters
        verbosity : int
        sim_start : int (start-time in secs)

        Returns
        -------
        None.

        """
        self.HI = HI
        self.env = env
        self.cdp_app_hourly = cdp.getAppHourly()
        self.cdp_app_daily = cdp.getAppDaily()
        self.interval = cfg['interval']
        self.diff = cfg['diff']
        self.verbosity = verbosity
        self.sim_start = sim_start
        self.timelog = {}
        # Start the App
        self.env.process(self.run())

    def time2str(self):
        """Return current date and time as string"""
        return tt.time2str(self.sim_start + self.env.now)

    def date2str(self):
        """Return current date as string"""
        return tt.time2date(self.sim_start + self.env.now)

    def run(self):
        """Run the App"""
        app_tick = tt.hms2sec(self.interval)
        app_data = {}
        last_data = {}
        yesterday_data = {}
        yesterday_stored = False
        while True:
            yield self.env.timeout(app_tick)
            if self.HI.is_running():
                # Get current RAM counters
                RAM = self.HI.get_counters_RAM()
                for k in RAM.keys():
                    app_data[k] = RAM[k]
                # Update to app time
                app_data['time'] = self.time2str()
                app_data['date'] = self.date2str()
                # Update timelog
                if app_data['power_cycle'] not in self.timelog.keys():
                    self.timelog[app_data['power_cycle']] = (
                        app_data['time'], app_data['usage'])
                # Detectors/Estimators in diff/percentage?
                if (self.diff and (len(last_data) > 0)):
                    for e in self.HI.detectors:
                        app_data[e] = app_data[e] - last_data[e]
                    for e in self.HI.estimators:
                        app_data[e] = '{:.1f}%'.format(
                            100.0 * (app_data[e] - last_data[e]) / app_tick)

                # Store in hourly DB
                self.cdp_app_hourly.put(app_data)
                for k in RAM.keys():
                    last_data[k] = RAM[k]

                # Store in daily DB
                if not yesterday_stored and self.HI.get_yesterdays_counters():
                    # Get yesterdays counters
                    y_cnt = self.HI.get_yesterdays_counters()
                    for k in y_cnt.keys():
                        yesterday_data[k] = y_cnt[k]
                    # Get yesterdays power_cycle
                    pwr_cyc = yesterday_data['power_cycle']
                    yesterday_data['time'] = self.timelog[pwr_cyc][0]
                    yesterday_data['date'] = \
                        yesterday_data['time'].split(' ')[0]
                    yesterday_data['usage-at-time'] = self.timelog[pwr_cyc][1]
                    self.cdp_app_daily.put(yesterday_data)
                    yesterday_stored = True
                # Log
                if self.verbosity > 2:
                    print('@ {}: App: {}'.format(app_data['time'], app_data))
            else:
                # Prepare next day
                yesterday_stored = False
