# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""

# %% Define the time functions
import math
import time
import random


# %% Time related functions
def time2str(t=0):
    """Convert time(secs) to string format"""
    return time.strftime('%Y-%m-%d %H:%M:%S',
                         time.localtime(t) if t else time.localtime())


def time2date(t=0):
    """Convert time(secs) to string format, data only"""
    return time2str(t).split(' ')[0]


def str2time(s=''):
    """Convert time from string to secs"""
    return int(time.mktime(
        time.strptime(s if len(s) else time2str(), '%Y-%m-%d %H:%M:%S')))


def sec2hms(s):
    """Converts time in secs to H:M:S format"""
    H = math.floor(s/3600)
    M = math.floor((s - H*3600)/60)
    S = math.floor(s - H*3600 - M*60)
    return '{}h:{}m:{}s'.format(H, M, S)


def hms2sec(hms):
    """Converts H:M:S format to secs"""
    try:
        ll = hms.split(':')
    except ValueError:
        print("hms2sec: Wrong input, use a string!")
        exit
    sec = 0
    for s in ll:
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


# %% Random functions
def intRndPct(n, pct=20):
    """
    Randomize an integer

    Parameters
    ----------
    n : int
    pct : int, optional
        Randomization factor in %. The default is 20.

    Returns
    -------
    int
        Randomized integer

    """
    return int(n * (100.0 + random.uniform(-pct, pct)) / 100.0)
