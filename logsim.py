# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Import essentials
import simpy
import logsim.ttime as tt
from logsim.hi import HI
from logsim.datapool import CDP

# %% Configure simulation
months = 12
d_array = 31
days = d_array * (months if months else 1)
sim_start = "2020-03-02 00:00:00"
verbosity = 0

plot = True
# plot = False

# Create Common Data Platform
cdp = CDP()

# Configure HI
HI_cfg0 = {
    'verbosity':   verbosity,
    'nvram_array': d_array,
    'nvram_month': months,
    'sim_start':   sim_start,
    'min_period': '6h',
    'max_period': '9h',
    'estimators':
    {'ovd':    {'interval': '30m', 'length': '2m', 'inc_m': '60s'},
     'speech': {'interval': '30m', 'length': '6m', 'inc_m': '30s'},
     'noise':  {'interval':  '7m', 'length':  '1m'},
     'snr-low':  {'interval': '10m', 'length': '1m', 'rand-off': True,
                  'inc_m': '1s'},
     'snr-med':  {'interval': '10m', 'length': '2m', 'rand-off': True},
     'snr-high': {'interval': '10m', 'length': '7m', 'rand-off': True,
                  'inc_m': '-1s'},
     'ovd-snr-low':  {'interval': '60m', 'length': '1m', 'inc_m': '10s'},
     'ovd-snr-med':  {'interval': '60m', 'length': '3m'},
     'ovd-snr-high': {'interval': '60m', 'length': '3m', 'inc_m': '2s'},
     # 'car':     {'interval': '15m', 'length': '3m'},
     # 'cafe':    {'interval':  '15m', 'length':  '2m'},
     # 'traffic': {'interval':  '5m', 'length':  '4m'},
     },
    'detectors': {'vcUp': '131m', 'vcDwn': '130m'},
    'app': {'on': True, 'diff': False, 'interval': '1h'},
    'fsw': {'visits': [1, 6, 12]},
    'times_pr_day': 1,
    }
HI_cfg1 = {
    'verbosity':   verbosity,
    'nvram_array': d_array,
    'nvram_month': months,
    'sim_start':   sim_start,
    'min_period': '4h',
    'max_period': '8h',
    'estimators':
    {'ovd':    {'interval': '45m', 'length': '2m', 'inc_m': '50s'},
     'speech': {'interval': '45m', 'length': '6m', 'inc_m': '25s'},
     'noise':  {'interval':  '15m', 'length':  '1m'},
     'ovd-snr-low':  {'interval': '60m', 'length': '1m', 'inc_m': '8s'},
     'ovd-snr-med':  {'interval': '60m', 'length': '3m'},
     'ovd-snr-high': {'interval': '60m', 'length': '3m', 'inc_m': '2s'},
     # 'car':     {'interval': '15m', 'length': '3m'},
     # 'cafe':    {'interval':  '15m', 'length':  '2m'},
     # 'traffic': {'interval':  '5m', 'length':  '4m'},
     },
    'detectors': {'vcUp': '131m', 'vcDwn': '130m'},
    'app': {'on': True, 'diff': True, 'interval': '1h'},
    'fsw': {'visits': [1, 6, 12]},
    'times_pr_day': 1,
    }
HI_cfg2 = {
    'verbosity':   verbosity,
    'nvram_array': d_array,
    'nvram_month': months,
    'sim_start':   sim_start,
    'min_period': '3h',
    'max_period': '6h',
    'estimators':
    {'ovd':    {'interval': '45m', 'length': '2m', 'inc_m': '30s'},
     'speech': {'interval': '45m', 'length': '6m', 'inc_m': '20s'},
     'noise':  {'interval':  '15m', 'length':  '1m'},
     'ovd-snr-low':  {'interval': '60m', 'length': '1m', 'inc_m': '6s'},
     'ovd-snr-med':  {'interval': '60m', 'length': '3m'},
     'ovd-snr-high': {'interval': '60m', 'length': '3m', 'inc_m': '1s'},
     # 'car':     {'interval': '15m', 'length': '3m'},
     # 'cafe':    {'interval':  '15m', 'length':  '2m'},
     # 'traffic': {'interval':  '5m', 'length':  '4m'},
     },
    'detectors': {'vcUp': '131m', 'vcDwn': '130m'},
    'app': {'on': True, 'diff': True, 'interval': '1h'},
    'fsw': {'visits': [1, 6, 12]},
    'times_pr_day': 1,
    }


# %% Define environment and HI(s)
env = simpy.Environment()
# User 0
hi = HI(0, env, cdp, HI_cfg0)


# %% More users?
users = {}
def more_users(users):
    for i in range(1, 8):
        users[i] = HI(i, env, cdp, HI_cfg0)
    for i in range(8, 15):
        users[i] = HI(i, env, cdp, HI_cfg1)
    for i in range(15, 20):
        users[i] = HI(i, env, cdp, HI_cfg2)

# Comment out if you want only one user
# more_users(users)

# %% Run simulation
print('Simulation started @ ' + sim_start)
env.run(until=tt.hms2sec('{}d:4h'.format(days)))
print('Simulation ended   @ ' + tt.time2str(tt.str2time(sim_start) + env.now))

cdp.saveAsCSV(ver='02')

# %% Test plot
if plot:
    cdp.plotDaily()
    hi.plotMonthlyData()
