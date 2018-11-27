# -*- coding: utf-8 -*-
"""
Created on Mon Nov 26 21:53:26 2018

@author: Frank Shi
"""

import pandas as pd

ls = [['one', 1], ['two', 2], ['three', 3]]
headers = ['english', 'number']
f1 = pd.DataFrame(ls, columns = headers)
print(f1)