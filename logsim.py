# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

#%% Define the time functions
import math
import time

def time2str(t=0):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t) if t else time.localtime())

def time2date(t=0):
    return time2str(t).split(' ')[0]

def str2time(s=''):
    return int(time.mktime(time.strptime(s if len(s) else time2str(), '%Y-%m-%d %H:%M:%S')))

def sec2hms(s):
    H = math.floor(s/3600)
    M = math.floor((s - H*3600)/60)
    S = math.floor(s - H*3600 - M*60)
    return '{}h:{}m:{}s'.format(H,M,S)

def hms2sec(hms):
    try:
        l = hms.split(':')
    except:
        print("hms2sec: Wrong input, use a string!")
        exit
    sec = 0
    for s in l:
        if s[-1] == 'd':
            sec = sec + 24*3600*int(s[0:-1])
        elif s[-1] == 'h':
            sec = sec + 3600*int(s[0:-1])
        elif s[-1] == 'm':
            sec = sec + 60*int(s[0:-1])
        elif s[-1] == 's':
            sec = sec + int(s[0:-1])
        else:
            sec = sec + int(s)
    return sec

#%% Define the Client event generators
import pprint
import simpy
import random
import matplotlib.pyplot as plt
import numpy as np
# %matplotlib inline


class Client:
    """
    Class for holding a clients HI with detctors and estimators and an App 
    that can sample the logging data from the HI
    Init Parameters
    ---------------
    id : numeric
         An identification number unique to this client
    env : Reference to a simpy environment object
    data : Reference to a DataPool object
    cfg : Reference to a Configuratin dict
    
    """
    def __init__(self, id, env, data, cfg):
        # Initialize variables
        self.id = id
        self.env = env
        self.last_updated_at = 0
        self.power_cycle = 0
        # Size of NVRAM arrays
        self.nvram_array = cfg['nvram_array']
        # Estimators -     name        interval           length
        self.estimators = cfg['estimators']
        # Detectors -     name     interval
        self.detectors = cfg['detectors']
        # App 
        self.app = cfg['app']
        self.min_period = hms2sec(cfg['min_period'])
        self.max_period = hms2sec(cfg['max_period'])
        self.times_pr_day = cfg['times_pr_day']
        self.nvram_str = cfg['nvram_str']
        self.verbosity = cfg['verbosity']
        self.sim_start = str2time(cfg['sim_start'])
        self.data = data
        self.pp = pprint.PrettyPrinter(indent=2, width=160)
        # Declare
        self.RAM = {}
        self.NVRAM = {}
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
        self.RAM['charge'] = 0
        self.RAM['usage'] = 0
        self.RAM['time'] = 0
        # Create NVRAM version of usage : cnt
        self.NVRAM['charge'] = [0] * self.nvram_array
        self.NVRAM['usage']  = [0] * self.nvram_array
        self.NVRAM['time']  = [0] * self.nvram_array
        self.NVRAM['date']  = [0] * self.nvram_array
        for d in self.estimators:
            # Create RAM version of all detectors: (State, cnt)
            self.RAM[d] = 0
            # Create NVRAM version of all detectors: cnt
            self.NVRAM[d] = [0] * self.nvram_array
        for d in self.detectors:
            # Create RAM version of all detectors: (State, cnt)
            self.RAM[d] = 0
            # Create NVRAM version of all detectors: cnt
            self.NVRAM[d] = [0] * self.nvram_array
            
    # Clear RAM
    def clear_ram(self):
        self.HI_running = True
        self.RAM['usage'] = 0
        self.RAM['time'] = 0
        for k in self.estimators:
            self.RAM[k] = 0
        for k in self.detectors:
            self.RAM[k] = 0

    # Print date and time
    def now2str(self):
        return time2str(self.sim_start + self.env.now)


    # Sessions
    def run_sessions(self):
        # Start in the morning...
        first_day = True
        while self.power_cycle < self.nvram_array:
            # Start by Charging
            cycle = int(24 / self.times_pr_day)
            tick = random.randint(self.min_period, self.max_period)
            chg = hms2sec('{}h'.format(cycle)) - tick + random.randint(0, 600) - 300
            if first_day:
                chg -= hms2sec('8h')
                first_day = False
            # Check for negative time...
            chg = max(chg, 300)
            self.last_updated_at = self.env.now
            yield self.env.timeout(chg)
            
            # Start session (HI removed from Charger)
            if self.verbosity > 0:
                # print('Session started @', sec2hms(self.env.now), ', Client: ', self.id)
                print('Usage started @', self.now2str(), ', Client: ', self.id)
            if self.nvram_str:
                self.NVRAM['charge'][self.power_cycle] = sec2hms(self.env.now - self.last_updated_at)
            else:
                self.NVRAM['charge'][self.power_cycle] = self.env.now - self.last_updated_at
            self.clear_ram()
            self.RAM['charge'] = self.NVRAM['charge'][self.power_cycle]
            self.last_updated_at = self.env.now
            yield self.env.timeout(tick)

            # End Session (HI into Charger)
            if self.verbosity > 0:
                print('Usage ended   @', self.now2str(), ', Client: ', self.id)
                # print('Session ended   @', sec2hms(self.env.now), ', Client: ', self.id)
            self.update_usage()
            self.HI_running = False
            # Write NVRAM
            if self.nvram_str:
                self.NVRAM['usage'][self.power_cycle] = sec2hms(int(self.RAM['usage']))
            else:
                self.NVRAM['usage'][self.power_cycle] = self.RAM['usage']
            for d in self.detectors:
                self.NVRAM[d][self.power_cycle] = self.RAM[d]
            for d in self.estimators:
                if self.nvram_str:
                    self.NVRAM[d][self.power_cycle] = "{:.2f}%".format(100.0 * self.RAM[d] / self.RAM['usage'])
                else:
                    self.NVRAM[d][self.power_cycle] = self.RAM[d]
            if self.RAM['time']:
                self.NVRAM['time'][self.power_cycle] = self.RAM['time']
                self.NVRAM['date'][self.power_cycle] = time2date(self.RAM['time'])
            else:
                self.NVRAM['time'][self.power_cycle] = self.power_cycle
                self.NVRAM['date'][self.power_cycle] = self.power_cycle
            if self.verbosity > 1:
                print('RAM:')
                self.pp.pprint(self.RAM)
                print('NVRAM:')
                self.pp.pprint(self.NVRAM)
            # self.power_cycle = (self.power_cycle + 1) % self.nvram_array
            self.power_cycle += 1
            # Test if completed
            if self.power_cycle == self.nvram_array:
                if self.verbosity > 0:
                    print('Simulation Completed!')
                # if self.plot:
                #     self.do_plot()
            
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
            yield self.env.timeout(hms2sec(self.detectors[d]))
            if self.HI_running:
                self.RAM[d] = self.RAM[d] + 1
                if self.verbosity > 3:
                    print('@ {}: {} fired, count = {}'.format(self.env.now, d, self.RAM[d]))

    # Start HI estimators
    def run_estimators(self, d):
        while True:
            # Start estimator
            yield self.env.timeout(hms2sec(self.estimators[d]['interval']))
            self.estimators[d]['last_updated'] = self.env.now
            if self.HI_running:
                if self.verbosity > 3:
                    print('@ {}: {} started'.format(self.env.now, d, self.RAM[d]))
            # End estimator
            length = hms2sec(self.estimators[d]['length']) 
            if d is 'ovd':
                length += self.power_cycle
            yield self.env.timeout(length)
            if self.HI_running:
                self.RAM[d] += self.env.now - self.estimators[d]['last_updated']
                if self.verbosity > 3:
                    print('@ {}: {} ended, count = {}'.format(self.env.now, d, self.RAM[d]))
                
    # Start App
    def run_app(self):
        app_tick = hms2sec(self.app['interval'])
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
                        app_data[e] = '{:.1f}%'.format(min(100.0, 100.0 * (app_data[e] - last_data[e]) / app_tick))
                    for e in self.detectors:
                        app_data[e] = app_data[e] - last_data[e]
                        
                app_data['time'] = time2str(self.sim_start + self.env.now)
                self.data.put(app_data)
                last_data = self.RAM.copy()
                if self.verbosity > 2:
                    print('@ {}: App: {}'.format(self.env.now, app_data))
            else:
                last_data = self.RAM


#%% Define Data Pool
import pandas as pd

class DataPool:
    def __init__(self):
        self.empty = True
        self.df = False
    def put(self, data):
        if self.empty:
            self.df = pd.DataFrame([data])
            self.empty = False
        else:
            self.df = self.df.append(data, ignore_index=True)
    

#%% Setup environment and run simulation
days = 16
verbosity = 1
sim_start = "2020-03-18 00:00:00"


plot = True
# plot = False
dataPool = DataPool()

# Configure client
client_cfg = {
    'verbosity'    : verbosity,
    'nvram_array'  : days,
    'sim_start'    : sim_start,
    'min_period'   : '6h', 
    'max_period'   : '9h', 
    'nvram_str'    : not plot,
    'estimators'   : {'ovd'   : {'interval': '10m', 'length': '30s', 'last_updated': 0},
                      'vad'   : {'interval':  '5m', 'length': '40s', 'last_updated': 0},
                      'noise' : {'interval':  '7m', 'length':  '1m', 'last_updated': 0},
                       'music' : {'interval': '10m', 'length': '3m', 'last_updated': 0},
                       'car' : {'interval': '15m', 'length': '3m', 'last_updated': 0},
                       'restaurant' : {'interval':  '15m', 'length':  '2m', 'last_updated': 0},
                       'traffic' : {'interval':  '5m', 'length':  '4m', 'last_updated': 0},
                     },
    'detectors'    : {'vcUp'  : '31m',
                      'vcDwn' : '30m',
                     },
    'app'          : {'on': True, 'diff': True, 'set_time': True, 'interval': '120m'},
    'times_pr_day' : 1 }

# Define environment and client(s)
env = simpy.Environment()
usr = Client(0, env, dataPool, client_cfg)
# for i in range(4): Client(i, env, dataPool, client_cfg)


#%% Run simulation
# Run simulation
env.run(until=hms2sec('{}d'.format(days+1)))

# Test plot
if plot:
    # Prepare data
    dd=pd.DataFrame(usr.NVRAM)
    dd['indx'] = np.arange(days)
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
