# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Import essentials
import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logsim.ttime as tt
from logsim.client import Client
from logsim.datapool import DataPool


# %% Setup environment and run simulation
months = 12
d_array = 31
days = d_array * (months if months else 1)
sim_start = "2020-03-02 00:00:00"
verbosity = 0

plot = True
# plot = False
cdp = DataPool()

# Configure client
client_cfg = {
    'verbosity':   verbosity,
    'nvram_array': d_array,
    'nvram_month': months,
    'sim_start':   sim_start,
    'min_period': '3h',
    'max_period': '9h',
    'estimators':
    {'ovd':    {'interval': '30m', 'length': '2m', 'last_updated': 0},
     'speech': {'interval': '15m', 'length': '3m', 'last_updated': 0},
     # 'noise':  {'interval':  '7m', 'length':  '1m', 'last_updated': 0},
     # 'ovd-snr-low':  {'interval': '10m', 'length': '15s', 'last_updated': 0},
     # 'ovd-snr-med':  {'interval': '20m', 'length': '10s', 'last_updated': 0},
     # 'ovd-snr-high': {'interval': '30m', 'length': '5s', 'last_updated': 0},
     # 'car':     {'interval': '15m', 'length': '3m', 'last_updated': 0},
     # 'cafe':    {'interval':  '15m', 'length':  '2m', 'last_updated': 0},
     # 'traffic': {'interval':  '5m', 'length':  '4m', 'last_updated': 0},
     },
    'detectors':
        {'vcUp': '131m', 'vcDwn': '130m'},
    'app':
        {'on': True, 'diff': True, 'set_time': True, 'interval': '1h'},
    'times_pr_day': 1,
    }

# Define environment and client(s)
env = simpy.Environment()
usr = Client(0, env, cdp, client_cfg)
# for i in range(4): Client(i, env, dataPool, client_cfg)


# %% Run simulation
# Run simulation
print('Simulation started @ ' + sim_start)
env.run(until=tt.hms2sec('{}d:4h'.format(days)))
print('Simulation ended   @ ' + tt.time2str(tt.str2time(sim_start) + env.now))

# %%
# Test plot
if plot:
    # Prepare daily data
    df = pd.DataFrame(usr.NVRAM)
    dd = df.loc[1:][:]
    dd['indx'] = np.arange(usr.nvram_array-1)
    # Diff the arrays
    for x in list(usr.estimators.keys()) + list(
            usr.detectors.keys()) + ['usage', 'charge']:
        dd[x] = df[x].diff().loc[1:][:].astype(int)
    dd['Usage'] = dd['usage'] / 3600
    dd['Usage Low'] = dd['Usage']
    dd['Usage OK'] = dd['Usage']
    dd.loc[dd['Usage'] >= 5.0, 'Usage Low'] = 0.0
    dd.loc[dd['Usage'] < 5.0, 'Usage OK'] = 0.0
    dd['Charge'] = dd['charge'] / 3600
    dd['Speech'] = 100.0 * dd['speech'] / dd['usage']
    dd['OwnVoice'] = 100.0 * dd['ovd'] / dd['usage']
    dd['Threshold'] = np.ones(usr.nvram_array-1) * 5

    # Plot Voice Overview pr Day
    ax = dd.plot.bar(x='date', y=['OwnVoice', 'Speech'], stacked=True,
                     color=['gold', 'darkgoldenrod'],
                     title='Speech Overview for Client #' + str(usr.id)
                     + ', Day view')
    ax.set_xlabel('Sessions')
    ax.set_ylabel('Percentage (%)')

    # Plot Usage Overview pr Day
    ax = dd.plot.bar(x='date', y=['Usage Low', 'Usage OK', 'Charge'],
                     stacked=True, color=['red', 'limegreen', 'steelblue'],
                     title='Usage Overview for Client #' + str(usr.id)
                     + ', Day view')
    dd.plot(x='date', y='Threshold', ax=ax, linestyle='dotted', color='black')
    ax.legend(loc="upper right")
    ax.set_xlabel('Sessions')
    ax.set_ylabel('Hours')
    plt.xticks(rotation=90)

    # Prepare monthly data
    if usr.nvram_month:
        dn = pd.DataFrame(usr.NVRAM_MONTH)
        dm = dn.loc[1:][:]
        dm['indx'] = np.arange(usr.nvram_month-1)
        # Diff the arrays
        for x in list(usr.estimators.keys())\
                + list(usr.detectors.keys()) + ['usage', 'charge']:
            dm[x] = dn[x].diff().loc[1:][:].astype(int)
        dm['Usage'] = dm['usage'] / 3600 / usr.nvram_array
        dm['Charge'] = dm['charge'] / 3600 / usr.nvram_array
        dm['Speech'] = 100.0 * dm['speech'] / dd['usage'] / usr.nvram_array
        dm['OwnVoice'] = 100.0 * dm['ovd'] / dd['usage'] / usr.nvram_array

        # Plot Voice Overview pr Month
        rr = None if usr.app and usr.app.set_time else 0
        ax = dm.plot.bar(x='date', y=['OwnVoice', 'Speech'], stacked=True,
                         color=['gold', 'darkgoldenrod'],
                         title='Speech Overview for Client #' + str(usr.id)
                         + ', Month view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Percentage (%)')

        # Plot Usage Overview pr Month
        ax = dm.plot.bar(x='date', y=['Usage', 'Charge'], stacked=True,
                         color=['limegreen', 'steelblue'],
                         title='Usage Overview for Client #' + str(usr.id)
                         + ', Month view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Hours')
