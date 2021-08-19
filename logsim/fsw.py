# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Define the Client event generators
# import matplotlib.pyplot as plt
# import logsim.hi as HI
import logsim.ttime as tt


class FSW:
    """
    Class for holding the Fitting SW interfacing to the HI
    Can call and get HI counters
    """

    # Constructor
    def __init__(self, HI, env, cdp, cfg, verbosity):
        self.HI = HI
        self.env = env
        self.cdp_fsw_daily = cdp.getFswDaily()
        self.visits = cfg['visits']
        self.verbosity = verbosity
        # Start the FSW
        self.env.process(self.run())

    # Run the Fsw
    def run(self):
        month_in_sec = tt.hms2sec('24h') * 30
        last_visit = 0
        for visit in self.visits:
            yield self.env.timeout(month_in_sec * (visit - last_visit))
            last_visit = visit
            # Get current NVRAM counters and store in DB
            NVRAM_MONTH = self.HI.get_counters_NVRAM_MONTH()
            for nv in NVRAM_MONTH:
                # Store in Daily DB if data is valid
                if nv['usage']:
                    self.cdp_fsw_daily.put(nv)
            NVRAM = self.HI.get_counters_NVRAM()
            for nv in NVRAM:
                # Store in Daily DB
                if nv['usage']:
                    self.cdp_fsw_daily.put(nv)
            # Log the visit
            if self.verbosity > 0:
                print('HCP visit     @', self.HI.now2str(),
                      ', HI: ', self.HI.id, ', month: ', visit)
