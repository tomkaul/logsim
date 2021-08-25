# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""


# %% Define Data Pool
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
pd.options.mode.chained_assignment = None


# Data base as pandas dataframe
class DataPool:
    """Class holding a DB (based on a Pandas DataFrame)"""

    def __init__(self, name, monthly=False):
        """ Constructor of a DB (based on a Pandas DataFrame) """
        self.name = name
        self.df = pd.DataFrame()
        self.ddiff = pd.DataFrame()
        self.dfeat = pd.DataFrame()
        self.monthly = monthly

    def put(self, data):
        """ Add a new entry to the DB """
        if self.df.empty:
            self.df = pd.DataFrame([data])
        else:
            self.df = self.df.append(data, ignore_index=True)

    def isEmpty(self):
        """ Check if DB is empty """
        return self.df.empty

    # Save DB as CSV
    def saveAsCSV(self, ver='00'):
        """ Save DB as a CSV file """
        self.df.to_csv(self.name + '_' + ver + '.csv')

    # Load DB from CSV
    def loadAsCSV(self, ver='00'):
        """ Load DB from a CSV file """
        # print('LOADING CSV FILE: ' + self.name)
        try:
            fname = self.name + '_' + ver + '.csv'
            self.df = pd.read_csv(fname, index_col=[0])
        except FileNotFoundError:
            print('No file: ' + fname)

    def clean_data(self):
        """ Create the silver buckets from RAW bronze data """
        # Sort by if and day
        self.df = self.df.sort_values(by=['id', 'power_cycle'])
        # Remove duplicates
        self.df.drop_duplicates(subset=['id', 'power_cycle'], inplace=True)

    def diff_data(self):
        """ Differentiate counters"""
        if self.ddiff.empty:
            # Clean data first
            self.clean_data()

            # Which columns to differentiate
            k_list = [x for x in list(self.df.keys())
                      if x not in ['id', 'power_cycle', 'time',
                                   'date', 'usage-at-time']]
            # Get list of ID's
            id_list = list(self.df['id'].unique())
            # Diff the relevant data
            self.ddiff = self.df.copy()
            self.ddiff.drop(
                self.ddiff.loc[self.ddiff['power_cycle'] == 0].index,
                inplace=True)

            # Loop over all ID's
            for id in id_list:
                self.ddiff.loc[self.ddiff['id'] == id, k_list] = \
                    self.df.loc[self.df['id'] == id, k_list]\
                        .diff().iloc[1:].astype(int)

    # Normalize dats
    def normalize_data(self):
        """ Normalize Data"""
        # Need diff'd data
        self.diff_data()
        # Check if already normalized
        if 'Usage' not in self.ddiff.keys():
            self.ddiff['Usage'] = self.ddiff['usage'] / 3600
            self.ddiff['Charge'] = self.ddiff['charge'] / 3600
            self.ddiff['Speech'] = 100.0 * self.ddiff['speech'] \
                / self.ddiff['usage']
            self.ddiff['OwnVoice'] = 100.0 * self.ddiff['ovd'] \
                / self.ddiff['usage']
            # OVD pr SNR?
            if 'ovd-snr-low' in self.ddiff.keys():
                self.ddiff['OVD-snr-low'] = 100.0 * self.ddiff['ovd-snr-low'] \
                    / self.ddiff['usage']
                self.ddiff['OVD-snr-med'] = 100.0 * self.ddiff['ovd-snr-med'] \
                    / self.ddiff['usage']
                self.ddiff['OVD-snr-high'] = 100.0 * self.ddiff['ovd-snr-high'] \
                    / self.ddiff['usage']

    # Prepare Plot data
    def prepare_plot_data(self):
        """ Prepare data for plotting """
        # Need normalized data
        self.normalize_data()
        # Prepare coloring of usage data based on threshold
        if 'Usage Low' not in self.ddiff.keys():
            self.ddiff['Usage Low'] = self.ddiff['Usage']
            self.ddiff['Usage OK'] = self.ddiff['Usage']
            self.ddiff['Threshold'] = np.ones(self.ddiff.shape[0]) * 5
            self.ddiff.loc[self.ddiff['Usage'] >= 5.0, 'Usage Low'] = 0.0
            self.ddiff.loc[self.ddiff['Usage'] < 5.0, 'Usage OK'] = 0.0

    # Plot daily data
    def plot_daily(self, user_id=0, days=31, last_day=-1):
        """ Plot most important Daily data """
        # Prepare coloring of usage data based on threshold
        self.prepare_plot_data()
        # Narrow scope for plot
        dp = self.ddiff[self.ddiff['id'] == user_id].iloc[last_day
                                                          - days:last_day]
        self.plot_data(dp, user_id)

    # Plot monthly data
    def plot_monthly(self, user_id=0, month=30):
        """ Plot most important Monthly data """
        # Prepare coloring of usage data based on threshold
        self.prepare_plot_data()
        # Narrow scope for plot
        dp = self.ddiff[self.ddiff['id'] == user_id].iloc[::month]

        self.plot_data(dp, user_id)

    # Plot data
    def plot_data(self, dp, user_id=0):
        # Check for date
        x_col = 'date'
        x_label = 'Date'
        if x_col not in dp.keys():
            x_col = 'power_cycle'
            x_label = 'Sessions'

        # Plot Voice Overview pr Day
        ax = dp.plot.bar(x=x_col, y=['OwnVoice', 'Speech'],
                         stacked=True,
                         color=['gold', 'darkgoldenrod'],
                         title='Speech Overview for HI #'
                         + str(user_id)
                         + ', Day view')
        ax.set_xlabel(x_label)
        ax.set_ylabel('Percentage (%)')

        # Plot OVD pr SNR pr Day
        if 'ovd-snr-low' in dp.keys():
            ax = dp.plot.bar(x=x_col,
                             y=['OVD-snr-low', 'OVD-snr-med', 'OVD-snr-high'],
                             stacked=True,
                             color=['orangered', 'orange', 'greenyellow'],
                             title='OVR pr SNR Overview for HI #'
                             + str(user_id) + ', Day view')
            ax.set_xlabel(x_label)
            ax.set_ylabel('Percentage (%)')

        # Plot Usage Overview pr Day
        ax = dp.plot.bar(x=x_col,
                         y=['Usage Low', 'Usage OK', 'Charge'],
                         stacked=True,
                         color=['red', 'limegreen', 'steelblue'],
                         title='Usage Overview for HI #' + str(user_id)
                         + ', Day view')
        dp.plot(x=x_col, y='Threshold', ax=ax, linestyle='dotted',
                color='black')
        ax.legend(loc="upper right")
        ax.set_xlabel(x_label)
        ax.set_ylabel('Hours')
        plt.xticks(rotation=90)

    # Create features for analytics
    def create_features(self):
        """ Create DataFrame for holding features"""
        self.dfeat = pd.DataFrame(data=sorted(self.df['id'].unique()),
                                  columns=['user_id'])

        # Prepare features
        features = ['usage-pr-day', 'ovd-inc', 'speech-inc', 'ovd-snr-low-inc']
        zeros = np.zeros((len(self.dfeat), len(features)))
        self.dfeat = self.dfeat.join(pd.DataFrame(data=zeros,
                                                  columns=features))
        self.dfeat.set_index('user_id', inplace=True)

        # Extract features for each client
        secPyear = 365 * 3600
        for i, row in self.dfeat.iterrows():
            di = self.df.loc[self.df['id'] == i]
            row['usage-pr-day'] = di.iloc[-1]['usage'] / secPyear
            # row['charge'] = di.iloc[-1]['charge'] / secPyear
            row['ovd-inc'] = \
                (di.iloc[-1]['ovd'] - di.iloc[0]['ovd']) / secPyear
            row['speech-inc'] = \
                (di.iloc[-1]['speech'] - di.iloc[0]['speech']) / secPyear
            row['ovd-snr-low-inc'] = \
                (di.iloc[-1]['ovd-snr-low'] - di.iloc[0]['ovd-snr-low'])\
                / secPyear

    # Plot features
    def plot_features(self):
        """ Plot features"""
        # Create features if not already done
        if self.dfeat.empty:
            self.create_features()
        # Create pairplot to analyze correlations
        sns.color_palette("tab10")
        sns.pairplot(self.dfeat, hue="ovd-inc")


# Class holding all databases
class CDP:
    """Class holding a number of DBs - Common Data Platform """

    def __init__(self):
        """ CDP Constructor """
        self.app_daily = DataPool('app_daily')
        self.app_hourly = DataPool('app_hourly')
        self.fsw_daily = DataPool('fsw_daily')
        self.fsw_monthly = DataPool('fsw_monthly')

    # Save all DB as CSV
    def saveAsCSV(self, ver='00'):
        """ Save all DB's as CSV files"""
        self.app_daily.saveAsCSV(ver)
        self.app_hourly.saveAsCSV(ver)
        self.fsw_daily.saveAsCSV(ver)
        self.fsw_monthly.saveAsCSV(ver)

    # Load all DB from CSV
    def loadAsCSV(self, ver='00'):
        """ Load all DB's from CSV files"""
        self.app_daily.loadAsCSV(ver)
        self.app_hourly.loadAsCSV(ver)
        self.fsw_daily.saveAsCSV(ver)
        self.fsw_monthly.loadAsCSV(ver)

    def getAppDaily(self):
        """ Get Daily App DB """
        return self.app_daily

    def getAppHourly(self):
        """ Get Hourly App DB """
        return self.app_hourly

    def getFswDaily(self):
        """ Get Daily FSW DB """
        return self.fsw_daily

    def getFswMonthly(self):
        """ Get Monthly FSW DB """
        return self.fsw_monthly
