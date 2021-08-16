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
from logsim.client import HI
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

# Configure HI
HI_cfg = {
    'verbosity':   verbosity,
    'nvram_array': d_array,
    'nvram_month': months,
    'sim_start':   sim_start,
    'min_period': '8h',
    'max_period': '9h',
    'estimators':
    {'ovd':    {'interval': '30m', 'length': '2m', 'inc_m': '60s'},
     'speech': {'interval': '30m', 'length': '6m'},
     # 'noise':  {'interval':  '7m', 'length':  '1m'},
     # 'ovd-snr-low':  {'interval': '60m', 'length': '1m', 'inc_d': '1s'},
     # 'ovd-snr-med':  {'interval': '60m', 'length': '3m'},
     # 'ovd-snr-high': {'interval': '60m', 'length': '3m', 'inc_d': '0s'},
     # 'car':     {'interval': '15m', 'length': '3m'},
     # 'cafe':    {'interval':  '15m', 'length':  '2m'},
     # 'traffic': {'interval':  '5m', 'length':  '4m'},
     },
    'detectors':
        {'vcUp': '131m', 'vcDwn': '130m'},
    'app':
        {'on': True, 'diff': True, 'set_time': True, 'interval': '3h'},
    'times_pr_day': 1,
    }

# Define environment and HI(s)
env = simpy.Environment()
hi = HI(0, env, cdp, HI_cfg)
# for i in range(4): HI(i, env, dataPool, HI_cfg)


# %% Run simulation
# Run simulation
print('Simulation started @ ' + sim_start)
env.run(until=tt.hms2sec('{}d:4h'.format(days)))
print('Simulation ended   @ ' + tt.time2str(tt.str2time(sim_start) + env.now))

# %%
# Test plot
if plot:
    # Prepare daily data
    df = pd.DataFrame(hi.NVRAM)
    dd = df.loc[1:][:]
    dd['indx'] = np.arange(hi.nvram_array-1)
    # Diff the arrays
    for x in [x for x in list(df.keys()) if x not in [
            'id', 'power_cycle', 'time', 'date']]:
        dd[x] = df[x].diff().loc[1:][:].astype(int)
    dd['Usage'] = dd['usage'] / 3600
    dd['Usage Low'] = dd['Usage']
    dd['Usage OK'] = dd['Usage']
    dd['Threshold'] = np.ones(hi.nvram_array-1) * 5
    dd.loc[dd['Usage'] >= 5.0, 'Usage Low'] = 0.0
    dd.loc[dd['Usage'] < 5.0, 'Usage OK'] = 0.0
    dd['Charge'] = dd['charge'] / 3600
    dd['Speech'] = 100.0 * dd['speech'] / dd['usage']
    dd['OwnVoice'] = 100.0 * dd['ovd'] / dd['usage']

    # Plot Voice Overview pr Day
    ax = dd.plot.bar(x='date', y=['OwnVoice', 'Speech'], stacked=True,
                     color=['gold', 'darkgoldenrod'],
                     title='Speech Overview for HI #' + str(hi.id)
                     + ', Day view')
    ax.set_xlabel('Sessions')
    ax.set_ylabel('Percentage (%)')

    # Plot OVD pr SNR pr Day
    if 'ovd-snr-low' in dd.keys():
        dd['OVD-snr-low'] = 100.0 * dd['ovd-snr-low'] / dd['usage']
        dd['OVD-snr-med'] = 100.0 * dd['ovd-snr-med'] / dd['usage']
        dd['OVD-snr-high'] = 100.0 * dd['ovd-snr-high'] / dd['usage']
        ax = dd.plot.bar(x='date', y=[
            'OVD-snr-low', 'OVD-snr-med', 'OVD-snr-high'], stacked=True,
                         color=['orangered', 'orange', 'greenyellow'],
                         title='OVR pr SNR Overview for HI #' + str(hi.id)
                         + ', Day view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Percentage (%)')

    # Plot Usage Overview pr Day
    ax = dd.plot.bar(x='date', y=['Usage Low', 'Usage OK', 'Charge'],
                     stacked=True, color=['red', 'limegreen', 'steelblue'],
                     title='Usage Overview for HI #' + str(hi.id)
                     + ', Day view')
    dd.plot(x='date', y='Threshold', ax=ax, linestyle='dotted', color='black')
    ax.legend(loc="upper right")
    ax.set_xlabel('Sessions')
    ax.set_ylabel('Hours')
    plt.xticks(rotation=90)

    # Prepare monthly data
    if hi.nvram_month:
        dn = pd.DataFrame(hi.NVRAM_MONTH)
        dm = dn.loc[1:][:]
        dm['indx'] = np.arange(hi.nvram_month-1)
        # Diff the arrays
        for x in list(hi.estimators.keys())\
                + list(hi.detectors.keys()) + ['usage', 'charge']:
            dm[x] = dn[x].diff().loc[1:][:].astype(int)
        dm['Usage'] = dm['usage'] / 3600 / hi.nvram_array
        dm['Charge'] = dm['charge'] / 3600 / hi.nvram_array
        dm['Speech'] = 100.0 * dm['speech'] / dd['usage'] / hi.nvram_array
        dm['OwnVoice'] = 100.0 * dm['ovd'] / dd['usage'] / hi.nvram_array

        # Plot Voice Overview pr Month
        rr = None if hi.app and hi.app.set_time else 0
        ax = dm.plot.bar(x='date', y=['OwnVoice', 'Speech'], stacked=True,
                         color=['gold', 'darkgoldenrod'],
                         title='Speech Overview for HI #' + str(hi.id)
                         + ', Month view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Percentage (%)')

        # Plot OVD pr SNR pr Month
        if 'ovd-snr-low' in dd.keys():
            dm['OVD-snr-low'] = 100.0 * dm['ovd-snr-low'] / dd['usage']
            dm['OVD-snr-med'] = 100.0 * dm['ovd-snr-med'] / dd['usage']
            dm['OVD-snr-high'] = 100.0 * dm['ovd-snr-high'] / dd['usage']
            ax = dm.plot.bar(x='date', y=[
                        'OVD-snr-low', 'OVD-snr-med', 'OVD-snr-high'],
                        stacked=True,
                        color=['orangered', 'orange', 'greenyellow'],
                        title='OVR pr SNR Overview for HI #' + str(hi.id)
                        + ', Day view')
            ax.set_xlabel('Sessions')
            ax.set_ylabel('Percentage (%)')

        # Plot Usage Overview pr Month
        ax = dm.plot.bar(x='date', y=['Usage', 'Charge'], stacked=True,
                         color=['limegreen', 'steelblue'],
                         title='Usage Overview for HI #' + str(hi.id)
                         + ', Month view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Hours')
