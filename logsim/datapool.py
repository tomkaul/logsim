# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""


# %% Define Data Pool
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data base as pandas dataframe
class DataPool:
    def __init__(self, name):
        self.empty = True
        self.df = False
        self.name = name

    def put(self, data):
        if self.empty:
            self.df = pd.DataFrame([data])
            self.empty = False
        else:
            self.df = self.df.append(data, ignore_index=True)

    def isNotEmpty(self):
        return not self.empty

    # Save DB as CSV
    def saveAsCSV(self, ver='00'):
        self.df.to_csv(self.name + '_' + ver + '.csv')

    # Load DB from CSV
    def loadAsCSV(self, ver='00'):
        self.df = pd.read_csv(self.name + '_' + ver + '.csv')
        self.empty = False


# Class holding all databases
class CDP:
    def __init__(self):
        self.app_daily = DataPool('app_daily')
        self.app_hourly = DataPool('app_hourly')
        self.fsw_daily = DataPool('fsw_daily')

    # Save all DB as CSV
    def saveAsCSV(self, ver='00'):
        self.app_daily.saveAsCSV(ver)
        self.app_hourly.saveAsCSV(ver)
        self.fsw_daily.saveAsCSV(ver)

    # Load all DB from CSV
    def loadAsCSV(self, ver='00'):
        self.app_daily.loadAsCSV(ver)
        self.app_hourly.loadAsCSV(ver)
        self.fsw_daily.loadAsCSV(ver)

    def getAppDaily(self):
        return self.app_daily

    def getAppHourly(self):
        return self.app_hourly

    def getFswDaily(self):
        return self.fsw_daily

    # Plot daily data
    def plotDaily(self, days=31, user_id=0):
        # Prepare daily data
        # df = pd.DataFrame(hi.NVRAM)
        df = self.getAppDaily().df if self.getAppDaily().isNotEmpty() \
            else self.getFswDaily().df
        df = df.loc[df['id'] == user_id]
        dd = df.iloc[-days:][:]
        dd['indx'] = np.arange(days)
        # Diff the arrays
        for x in [x for x in list(self.app_daily.df.keys()) if x not in [
                'id', 'power_cycle', 'time', 'date', 'usage-at-time']]:
            dd[x] = df[x].diff().loc[1:][-days:].astype(int)
        dd['Usage'] = dd['usage'] / 3600
        dd['Usage Low'] = dd['Usage']
        dd['Usage OK'] = dd['Usage']
        dd['Threshold'] = np.ones(days) * 5
        dd.loc[dd['Usage'] >= 5.0, 'Usage Low'] = 0.0
        dd.loc[dd['Usage'] < 5.0, 'Usage OK'] = 0.0
        dd['Charge'] = dd['charge'] / 3600
        dd['Speech'] = 100.0 * dd['speech'] / dd['usage']
        dd['OwnVoice'] = 100.0 * dd['ovd'] / dd['usage']

        # Plot Voice Overview pr Day
        ax = dd.plot.bar(x='date', y=['OwnVoice', 'Speech'], stacked=True,
                         color=['gold', 'darkgoldenrod'],
                         title='Speech Overview for HI #' + str(user_id)
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
                             title='OVR pr SNR Overview for HI #'
                             + str(user_id) + ', Day view')
            ax.set_xlabel('Sessions')
            ax.set_ylabel('Percentage (%)')

        # Plot Usage Overview pr Day
        ax = dd.plot.bar(x='date', y=['Usage Low', 'Usage OK', 'Charge'],
                         stacked=True, color=['red', 'limegreen', 'steelblue'],
                         title='Usage Overview for HI #' + str(user_id)
                         + ', Day view')
        dd.plot(x='date', y='Threshold', ax=ax, linestyle='dotted',
                color='black')
        ax.legend(loc="upper right")
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Hours')
        plt.xticks(rotation=90)

    # Plot monthly data
    def plotMonthly(self, user_id=0, month=30):
        # Prepare monthly data
        df = self.getAppDaily().df
        df = df.loc[df['id'] == user_id]
        dd = df.iloc[::month, 1:]
        dd['indx'] = np.arange(len(dd))
        dd.set_index('indx', inplace=True)
        dm = dd.iloc[1:, :]
        # Diff the arrays
        for x in [x for x in list(dm.keys()) if x not in [
                'id', 'indx', 'power_cycle', 'time', 'date', 'usage-at-time']]:
            dm[x] = dd[x].diff().loc[1:].astype(int)
        dm['Usage'] = dm['usage'] / 3600 / month
        dm['Charge'] = dm['charge'] / 3600 / month
        dm['Speech'] = 100.0 * dm['speech'] / dm['usage']
        dm['OwnVoice'] = 100.0 * dm['ovd'] / dm['usage']

        # Plot Voice Overview pr Month
        ax = dm.plot.bar(x='date', y=['OwnVoice', 'Speech'],
                         stacked=True, color=['gold', 'darkgoldenrod'],
                         title='Speech Overview for HI #' + str(user_id)
                         + ', Month view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Percentage (%)')

        # Plot OVD pr SNR pr Month
        if 'ovd-snr-low' in dd.keys():
            dm['OVD-snr-low'] = 100.0 * dm['ovd-snr-low'] / dm['usage']
            dm['OVD-snr-med'] = 100.0 * dm['ovd-snr-med'] / dm['usage']
            dm['OVD-snr-high'] = 100.0 * dm['ovd-snr-high'] / dm['usage']
            ax = dm.plot.bar(x='date', y=[
                        'OVD-snr-low', 'OVD-snr-med', 'OVD-snr-high'],
                        stacked=True,
                        color=['orangered', 'orange', 'greenyellow'],
                        title='OVR pr SNR Overview for HI #' + str(user_id)
                        + ', Day view')
            ax.set_xlabel('Sessions')
            ax.set_ylabel('Percentage (%)')

        # Plot Usage Overview pr Month
        ax = dm.plot.bar(x='date', y=['Usage', 'Charge'],
                         stacked=True, color=['limegreen', 'steelblue'],
                         title='Usage Overview for HI #' + str(user_id)
                         + ', Month view')
        ax.set_xlabel('Sessions')
        ax.set_ylabel('Hours')
