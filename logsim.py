# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

#%% Init
import simpy
import random


#%% Define the time functions
import math
# import time
# time.gmtime(0)
# def get_time():
#     t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
#     print(t)
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
class Client:
    def __init__(self, id, env, 
                 nvram_array = 16, 
                 min_period = '7h', 
                 max_period = '9h', 
                 times_pr_day = 1,
                 nvram_str = True,
                 verbosity = 1):
        # Set simulation variables
        # Size of NVRAM arrays
        self.nvram_array = nvram_array
        # Estimators -     name        interval           length
        self.estimators = {'ovd'  : {'interval': '10m', 'length': '30s', 'last_updated': 0},
                           'vad'  : {'interval':  '5m', 'length': '40s', 'last_updated': 0}}
        # Detectors -     name     interval
        self.detectors = {'vcUp' :  '30m',
                          'vcDwn' : '10m'}
        # Initialize variables
        self.id = id
        self.env = env
        self._last_updated_at = 0
        self._power_cycle = 0
        self._min_period = hms2sec(min_period)
        self._max_period = hms2sec(max_period)
        self._times_pr_day = times_pr_day
        self._nvram_str = nvram_str
        self._verbosity = verbosity
        self.RAM = {}
        self.NVRAM = {}
        # Init memory
        self.init_memory()
        # Start the sessions and the detectors and estimators
        self.env.process(self.run_sessions())
        for d in self.detectors:
            self.env.process(self.run_detectors(d))
        for d in self.estimators:
            self.env.process(self.run_estimators(d))
        
    # Init Memory
    def init_memory(self):
        # Create RAM version of usage: (State, cnt)
        self.RAM['usage'] = {'val': False, 'cnt': 0}
        # Create NVRAM version of usage : cnt
        self.NVRAM['usage']  = [0] * self.nvram_array
        self.NVRAM['charge'] = [0] * self.nvram_array
        for d in self.estimators:
            # Create RAM version of all detectors: (State, cnt)
            self.RAM[d] = {'cnt': 0}
            # Create NVRAM version of all detectors: cnt
            self.NVRAM[d] = [0] * self.nvram_array
        for d in self.detectors:
            # Create RAM version of all detectors: (State, cnt)
            self.RAM[d] = {'cnt': 0}
            # Create NVRAM version of all detectors: cnt
            self.NVRAM[d] = [0] * self.nvram_array
            
    # Clear RAM
    def clear_ram(self):
        self.RAM['usage']['val'] = True
        self.RAM['usage']['cnt'] = 0
        for k in self.estimators:
            self.RAM[k]['cnt'] = 0
        for k in self.detectors:
            self.RAM[k]['cnt'] = 0

    # Sessions
    def run_sessions(self):
        # Start in the morning...
        # morn = hms2sec('7h:58m')
        # yield self.env.timeout(morn)
        while self._power_cycle < self.nvram_array:
            # Start by Charging
            cycle = int(24 / self._times_pr_day)
            tick = random.randint(self._min_period, self._max_period)
            chg = hms2sec('{}h'.format(cycle)) - tick + random.randint(0, 600) - 300
            self._last_updated_at = self.env.now
            yield self.env.timeout(chg)
            
            # Start session (HI removed from Charger)
            if self._verbosity > 0:
                print('Session started @', sec2hms(self.env.now), ', Client: ', self.id)
            if self._nvram_str:
                self.NVRAM['charge'][self._power_cycle] = sec2hms(self.env.now - self._last_updated_at)
            else:
                self.NVRAM['charge'][self._power_cycle] = self.env.now - self._last_updated_at
            self.clear_ram()
            self._last_updated_at = self.env.now
            yield self.env.timeout(tick)

            # End Session (HI into Charger)
            if self._verbosity > 0:
                print('Session ended   @', sec2hms(self.env.now), ', Client: ', self.id)
            self.RAM['usage']['cnt'] += self.env.now - self._last_updated_at
            self._last_updated_at = self.env.now
            self.RAM['usage']['val'] = False
            # Write NVRAM
            if self._nvram_str:
                self.NVRAM['usage'][self._power_cycle] = sec2hms(int(self.RAM['usage']['cnt']))
            else:
                self.NVRAM['usage'][self._power_cycle] = self.RAM['usage']['cnt']
            for d in self.detectors:
                self.NVRAM[d][self._power_cycle] = self.RAM[d]['cnt']
            for d in self.estimators:
                if self._nvram_str:
                    self.NVRAM[d][self._power_cycle] = "{:.2f}%".format(100.0 * self.RAM[d]['cnt'] / self.RAM['usage']['cnt'])
                else:
                    self.NVRAM[d][self._power_cycle] = self.RAM[d]['cnt']

            if self._verbosity > 1:
                print('RAM:   ' + str(self.RAM))
                print('NVRAM: ' + str(self.NVRAM))
            # self._power_cycle = (self._power_cycle + 1) % self.nvram_array
            self._power_cycle += 1
            # Test if completed
            if self._verbosity > 0:
                if self._power_cycle == self.nvram_array:
                    print('Simulation Completed!')
            
    # Start HI detectors
    def run_detectors(self, d):
        while True:
            yield self.env.timeout(hms2sec(self.detectors[d]))
            if self.RAM['usage']['val']:
                self.RAM[d]['cnt'] = self.RAM[d]['cnt'] + 1
                if self._verbosity > 2:
                    print('@ {}: {} fired, count = {}'.format(self.env.now, d, self.RAM[d]['cnt']))

    # Start HI estimators
    def run_estimators(self, d):
        while True:
            # Start estimator
            yield self.env.timeout(hms2sec(self.estimators[d]['interval']))
            self.estimators[d]['last_updated'] = self.env.now
            if self.RAM['usage']['val']:
                if self._verbosity > 2:
                    print('@ {}: {} started'.format(self.env.now, d, self.RAM[d]['cnt']))
            # End estimator
            length = hms2sec(self.estimators[d]['length']) 
            if d is 'ovd':
                length += self._power_cycle
            yield self.env.timeout(length)
            if self.RAM['usage']['val']:
                self.RAM[d]['cnt'] += self.env.now - self.estimators[d]['last_updated']
                if self._verbosity > 2:
                    print('@ {}: {} ended, count = {}'.format(self.env.now, d, self.RAM[d]['cnt']))
                
    def do_plot(self):
        import matplotlib.pyplot as plt
        import numpy as np
        %matplotlib inline
        
        # Prep x axis
        x1 = [x-0.1 for x in np.arange(days)]
        x2 = [x+0.1 for x in np.arange(days)]
    
        # PLot OVD + VAD
        plt.figure()
        y1 = [i / j * 100 for i, j in zip(self.NVRAM['vad'], self.NVRAM['usage'])]
        y2 = [i / j * 100 for i, j in zip(self.NVRAM['ovd'], self.NVRAM['usage'])]
        # x = range(days)
        plt.bar(x1, y1, color = 'r', width = 0.2)
        plt.bar(x2, y2, color = 'm', width = 0.2)
        # plt.bar(x, y, 0.3) 
        plt.ylabel('Percentage (%)')
        plt.xlabel('Sessions');    
        plt.legend(['VAD', 'OVD'])
        plt.title('Voice Activity')
    
        # Plot Usage
        plt.figure()
        y1 = [int(x) / 3600.0 for x in self.NVRAM['charge']]
        y2 = [int(x) / 3600.0 for x in self.NVRAM['usage']]
        plt.bar(x1, y1, color = 'b', width = 0.2, label='Charging')
        plt.bar(x2, y2, color = 'g', width = 0.2)
        # plt.bar(x, y, 0.3) 
        plt.ylabel('Hours')
        plt.xlabel('Sessions');    
        plt.legend(['Charging', 'Usage'])
        plt.title('Usage Overview')

        
        
#%% Setup environment and run simulation
days = 16
verbosity = 1
plot = True
# plot = False
env = simpy.Environment()
usr = Client(0, env, nvram_array = days, verbosity = verbosity, nvram_str = not plot)
# usr = Client(1, env, nvram_array = days, verbosity = verbosity, nvram_str = not plot, min_period = '3h', max_period = '4h', times_pr_day = 2)

env.run(until=hms2sec('{}d'.format(days+3)))

if plot:
    usr.do_plot()
