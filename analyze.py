# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 09:03:45 2021

@author: thka
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from logsim.datapool import CDP
pd.options.mode.chained_assignment = None

# %% Reload data
cdp0 = CDP()
cdp0.loadAsCSV(ver='02')

# %% Plot daily stuff
user=
cdp0.plotDaily(user_id=user)

# %% Plot daily stuff
cdp0.plotMonthly(user_id=user)

# %% Analyze client proporties
# Get all Id's
df = cdp0.getAppDaily().df
da = pd.DataFrame(data=sorted(df['id'].unique()),
                  columns=['user_id'])

# Prepare features
features = ['usage', 'charge', 'ovd-inc', 'speech-inc', 'ovd-snr-low-inc']
zeros = np.zeros((len(da), len(features)))
da = da.join(pd.DataFrame(data=zeros, columns=features))
da.set_index('user_id', inplace=True)
# print(da)

# Extract features for each client
for i, row in da.iterrows():
    di = df.loc[df['id'] == i]
    row['usage'] = di.iloc[-1]['usage']
    row['charge'] = di.iloc[-1]['charge']
    row['ovd-inc'] = di.iloc[-1]['ovd'] - di.iloc[0]['ovd']
    row['speech-inc'] = di.iloc[-1]['speech'] - di.iloc[0]['speech']
    row['ovd-snr-low-inc'] = di.iloc[-1]['ovd-snr-low']
    - di.iloc[0]['ovd-snr-low']

# print(da)
# penguins = sns.load_dataset("penguins")
sns.color_palette("tab10")
sns.pairplot(da, hue="ovd-inc")
# sns.color_palette("coolwarm", as_cmap=True)