# -*- coding: utf-8 -*-
"""
Created on Thu May 13 09:01:13 2021

@author: thka
"""


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
    
