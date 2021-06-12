# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

#%% Import essentials
import simpy
from logsim.ttime import *
from logsim.client import *
from logsim.datapool import *
   

#%% Setup environment and run simulation
days = 16
verbosity = 2
sim_start = "2020-03-18 00:00:00"


plot = True
# plot = False
cdp = DataPool()

# Configure client
client_cfg = {
    'verbosity'    : verbosity,
    'nvram_array'  : days,
    'sim_start'    : sim_start,
    'min_period'   : '6h', 
    'max_period'   : '9h', 
    'nvram_str'    : not plot,
    'estimators'   : {'ovd'      : {'interval': '10m', 'length': '30s', 'last_updated': 0},
                      'vad'      : {'interval':  '5m', 'length': '40s', 'last_updated': 0},
                      'noise'    : {'interval':  '7m', 'length':  '1m', 'last_updated': 0},
                      'ovd-snr-low'  : {'interval': '10m', 'length': '15s', 'last_updated': 0},
                      'ovd-snr-med'  : {'interval': '20m', 'length': '10s', 'last_updated': 0},
                      'ovd-snr-high' : {'interval': '30m', 'length': '5s', 'last_updated': 0},
                      # 'car'   : {'interval': '15m', 'length': '3m', 'last_updated': 0},
                      # 'restaurant' : {'interval':  '15m', 'length':  '2m', 'last_updated': 0},
                      # 'traffic'    : {'interval':  '5m', 'length':  '4m', 'last_updated': 0},
                     },
    'detectors'    : {'vcUp'  : '31m',
                      'vcDwn' : '30m',
                     },
    'app'          : {'on': True, 'diff': True, 'set_time': False, 'interval': '5h'},
    'times_pr_day' : 1 }

# Define environment and client(s)
env = simpy.Environment()
usr = Client(0, env, cdp, client_cfg)
# for i in range(4): Client(i, env, dataPool, client_cfg)


#%% Run simulation
# Run simulation
env.run(until=hms2sec('{}d:4h'.format(16)))

#%%
# Test plot
if plot:
    # Prepare data
    dd=pd.DataFrame(usr.NVRAM)
    dd['indx'] = np.arange(days)
    # Diff the arrays
    for x in list(usr.estimators.keys()) + list(usr.detectors.keys()) + ['usage', 'charge']:
        dd[x][1:] = dd[x].diff()[1:].astype(int)
    dd['Usage'] = dd['usage'] / 3600
    dd['Charge'] = dd['charge'] / 3600
    dd['Speech'] = 100.0 * dd['vad'] / dd['usage']
    dd['OwnVoice'] = 100.0 * dd['ovd'] / dd['usage']
    
    # Plot Own Voice Pickup
    # plt.figure()
    # dd.plot()
    
    # Plot Voice Overview
    rr = None if usr.app['set_time'] else 0
    ax = dd.plot.bar(x='date', y=['OwnVoice', 'Speech'], stacked=True, rot=rr,
                     color=['gold', 'darkgoldenrod'],
                     title='Speech Overview for Client #' + str(usr.id))
    ax.set_xlabel('Sessions')
    ax.set_ylabel('Percentage (%)')
    
    # Plot Usage Overview
    ax = dd.plot.bar(x='date', y=['Usage', 'Charge'], stacked=True, rot=rr,
                     color=['limegreen', 'steelblue'],
                     title='Usage Overview for Client #' + str(usr.id))

    ax.set_xlabel('Sessions')
    ax.set_ylabel('Hours')

# plt.figure()
# ax = plt.subplot()
# p1 = ax.bar(dd['indx'], dd['Usage'], color='limegreen', width=0.4)
# p2 = ax.bar(dd['indx'], dd['Charge'], bottom = dd['Usage'], width=0.4)
# ax.legend((p1,p2), ('Usage', 'Charge'), shadow=True, fancybox=True)
# ax.set_xlabel('Days')
# ax.set_ylabel('Hours')
# ax.set_title('Usage Overview for X Client ' + str(usr.id))
