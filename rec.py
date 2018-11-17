import pandas as pd
import numpy as np

eodc = pd.read_csv('eodc_20181031.csv', low_memory=False)
# source = pd.read_csv('source_20181031.csv', low_memory=False)

# print(eodc.describe())

header_list = list(eodc.columns.values)
decomp_list = []
for i in range(len(header_list)):
    if 'PnL Decomp' in header_list[i] and header_list[i][-9:] != 'Local CCY':
        decomp_list.append(header_list[i])
for i in range(len(decomp_list)):
    temp_series = eodc[decomp_list[i]]
    temp_series.fillna(0, inplace=True)
    # print(temp_series.isnull())

col_drop = []
for col_name in header_list:
    if 'Local CCY' in col_name:
        # print(col_name)
        col_drop.append(col_name)
eodc.drop(col_drop, 1, inplace=True)
header_list = list(eodc.columns.values)
print(header_list)

# eodc.to_csv('eodc_after_python.csv')

for col in header_list:
    if 'Book' in col:
        print(col)

portfolio_series = eodc['Source_Book_Name']
portfolio_list = portfolio_series.unique().tolist()
print(portfolio_list)
print(decomp_list)

bookname = 'Source_Book_Name'

# We now create a "master table" which includes every portfolio and every decomp category

# We start with a function that cleans up the decomp category names


def decomp_name(decomp_cate):
    answer = ''
    answer = decomp_cate.replace('PnL Decomp', '')
    answer = answer.replace('Reporting CCY', '')
    return answer


ports_sorted = sorted(portfolio_list)
master_table = pd.DataFrame(columns=ports_sorted)
temp_dict = {}
for decomp in decomp_list:
    for port in ports_sorted:
        temp_dict[port] = int(round(eodc.loc[eodc[bookname] == port, decomp].sum()))
    master_table.loc[decomp_name(decomp)] = list(temp_dict.values())
# print(master_table)

# Note that a pivot table would give you the same effect, but this method can work very fast with very large files,
#   whereas Excel will be very slow. Also, this method is way cooler.

# We now attempt to do the same with the OpenLink source, which is 183MB large and a handful for Excel
source = pd.read_csv('source_20181031.csv', low_memory=False)



