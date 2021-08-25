# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 09:03:45 2021

@author: thka
"""
# import matplotlib.pyplot as plt
# import numpy as np
import pandas as pd
# import seaborn as sns
from logsim.datapool import CDP
pd.options.mode.chained_assignment = None

# %% Reload data
bronze = CDP()
bronze.loadAsCSV(ver='05')

# %% Cleanse data
# bronze.create_silver_buckets()

# %% Plot daily stuff
user = 0
# bronze.plotDaily(user_id=user)

# %% Plot monthly stuff
# bronze.plotMonthly(user_id=user)

# %% Bronze analysis
# bronze.getFswDaily().plot_features()
# bronze.getAppDaily().plot_daily(user_id=0)
# bronze.getAppDaily().plot_monthly(user_id=0)
bronze.getAppDaily().plot_features()
