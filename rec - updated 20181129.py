# Nov. 29 (20181012)
import pandas as pd
import numpy as np

# Establish the file names
eodc_file_name = 'eodc_20181012.csv'
source_file_name = 'source_20181012.csv'

# We first establish the mapping of decomp categories between the OpenLink source file and the EODc file
mapping_info = pd.read_excel('mapping_nov_26.xlsx')
decomp_mapping = {}  # the curly brackets represents a python dictionary
decomp_mapping_source_eodc = {}
i = 0
for category in mapping_info['EODC Measure Name']:
    decomp_mapping[category] = mapping_info['Openlink PNL'][i]
    i += 1
i = 0
for category in mapping_info['Openlink PNL']:
    decomp_mapping_source_eodc[category] = mapping_info['EODC Measure Name'][i]
    i += 1
# print(decomp_mapping)
# print(decomp_mapping_source_eodc)
# for decomp_mapping, the keys are the decomp categories in the EODc source file, and the values are
#   the decomp categories in the source file.

# # We start with the eodc file

eodc = pd.read_csv(eodc_file_name, low_memory=False)

eodc_headers = list(eodc.columns.values)
eodc_decomp = []

# Here we drop all the decomp categories that are in local currency
col_drop = []
for col_name in eodc_headers:
    if 'Local CCY' in col_name:
        col_drop.append(col_name)
eodc.drop(col_drop, 1, inplace=True)

# update the header list
eodc_headers = list(eodc.columns.values)

# eodc_decomp contains all the names of the decomp categories
for i in range(len(eodc_headers)):
    if 'PnL Decomp' in eodc_headers[i]:
        eodc_decomp.append(eodc_headers[i])
# print(eodc_decomp)

# We fill the empty cells with 0 in the decomp categories
for i in range(len(eodc_decomp)):
    temp_series = eodc[eodc_decomp[i]]
    temp_series.fillna(0, inplace=True)
    # print(temp_series.isnull())

# # # output a file that contains no local currency columns and has 0 in place of blank cells
# # eodc.to_csv('eodc_after_python.csv')

# eodc_portfolios is a list containing all portfolios
portfolio_series = eodc['Source_Book_Name']  # portfolio_series is a "series" object
eodc_portfolios = sorted(portfolio_series.unique().tolist())  # the .tolist() method makes a series into a python list


# sorted() is a built-in function that sorts a list. In this case, we sort the portfolio list alphabetically

# decomp_name(decomp_cate) consumes a string representing a decomp category and returns a cleaner string which
#   is essentially stripped off the useless stuff
def decomp_name(decomp_cate):
    answer = ''
    answer = decomp_cate.replace(' Reporting CCY', '')
    return answer


# We are now in a position to extract decomp information from the eodc file given any portfolio and any decomp category
#   We need to do the same with the OpenLink source file

source = pd.read_csv(source_file_name, low_memory=False)
source_headers = list(source.columns.values)
openlink_decomp = mapping_info['Openlink PNL'].tolist()
# openlink_decomp contains all the decomp categories that are supposed to be in the source file
source_decomp = []
for header in source_headers:
    if header in openlink_decomp:
        source_decomp.append(header)
source_portfolios = sorted(source['portfolio'].unique().tolist())
# we do not really need the portfolio list in the source file since it should have the same portfolios as the eodc file
# Nonetheless, we perform the following check to see whether the EODc file is missing any portfolios
missing_portfolios = []
if source_portfolios != eodc_portfolios:
    for portfolio in source_portfolios:
        if portfolio in eodc_portfolios is False:
            print(portfolio, "is missing in EODc")
            missing_portfolios.append(portfolio)

print('missing portfolio is', missing_portfolios)

# We are now in a position to extract decomp information from the source file given portfolio and decomp category


variances = []
# For the rec itself, we loop through the entire portfolio list (eodc_portfolio)
for portfolio in eodc_portfolios:
    # We have to deal with some exceptions. In particular, Delta is the sum of exotic options and delta; vega is the
    #   sum of vega atm and vega smile;
    for decomp in eodc_decomp:
        if decomp == 'PnL Decomp Commodity Delta Reporting CCY':
            source_delta = source.loc[source['portfolio'] == portfolio, 'impact_of_delta_commodity'].sum()
            source_exotic_opt = source.loc[source['portfolio'] == portfolio, 'exotic_option_pnl'].sum()
            source_sum = source_delta + source_exotic_opt
        elif decomp == 'PnL Decomp Commodity Vega Reporting CCY':
            source_vega_atm = source.loc[source['portfolio'] == portfolio, 'impact_of_vega_atm'].sum()
            source_vega_smile = source.loc[source['portfolio'] == portfolio, 'impact_of_vega_smile'].sum()
            source_sum = source_vega_atm + source_vega_smile
        else:
            source_sum = source.loc[source['portfolio'] == portfolio, decomp_mapping[decomp]].sum()
        eodc_sum = eodc.loc[eodc['Source_Book_Name'] == portfolio, decomp].sum()
        diff = int(round(source_sum - eodc_sum))
        if diff != 0:
            var = [portfolio, decomp_name(decomp), source_sum, eodc_sum, diff]
            variances.append(var)

# Now we produce the dataframe containing all the portfolio-level variances
headers = ['Portfolio', 'Decomp Category', 'Source Value', 'EODc Vale', 'Variance']
output = pd.DataFrame(variances, columns=headers)
output.to_excel('portfolio_level_check.xlsx')

# The goal now is to produce a deal-level analysis to see which deals are missing from the EODc extract.
#   We only deal with the portfolios that have decomp differences.
bad_portfolios = {}
for entry in variances:
    if entry[0] not in bad_portfolios.keys():
        bad_portfolios[entry[0]] = []
        bad_portfolios[entry[0]].append(entry[1] + ' Reporting CCY')
    else:
        bad_portfolios[entry[0]].append(entry[1] + ' Reporting CCY')
# print(bad_portfolios.keys())
# print(bad_portfolios.values())

if bad_portfolios.keys() != []:

    print("There are disagreements with some portfolios.")
    print("Portfolio-level report generated.")
    print("Running deal-level check now...")

    # loop through all deals in the portfolios in bad_portfolios. In each loop, go through all the deals of that portfolio
    #   in the source file, and see if they are present in the EODc file.
    # note that some deals in the EODc file do not have deal numbers, but they could still represent a deal from source.
    # we only look at the missing deals that have a non-zero number in the relevant decomp category
    # At the time of writing, it is known that neither CallNot nor Cash is included in the EODc extract.

    deal_level_rec = []
    for portfolio in bad_portfolios.keys():
        print(portfolio)
        for decomp_cate in bad_portfolios[portfolio]:
            # Note that decomp_cate is from EODc
            #         print(decomp_cate)
            source_decomp_cate = decomp_mapping[decomp_cate]
            # we obtain the list of deals in the particular portfolio in both the source and eodc
            source_deal_list = source.loc[source['portfolio'] == portfolio, 'deal_num'].tolist()
            eodc_deal_list = eodc.loc[eodc['Source_Book_Name'] == portfolio, 'Source_Trade_ID'].unique().tolist()
            # print(portfolio, 'eodc_deal_list is', eodc_deal_list)
            for deal_num in source_deal_list:
                rows = source.loc[source['deal_num'] == deal_num].index.tolist()
                row_num = 0
                if len(rows) == 1:
                    row_num = rows[0]
                else:  # This means that a certain deal has been booked into multiple portfolios in OpenLink source
                    for i in range(len(rows)):
                        if source.loc[rows[i], 'portfolio'] == portfolio:
                            row_num = rows[i]
                # we deal with the special cases of delta and vega
                if decomp_cate == 'PnL Decomp Commodity Delta Reporting CCY':
                    source_decomp_value = source.loc[row_num, 'impact_of_delta_commodity'] + source.loc[
                        row_num, 'exotic_option_pnl']
                elif decomp_cate == 'PnL Decomp Commodity Vega Reporting CCY':
                    source_decomp_value = source.loc[row_num, 'impact_of_vega_atm'] + source.loc[
                        row_num, 'impact_of_vega_smile']
                else:
                    source_decomp_value = source.loc[row_num, source_decomp_cate]
                tool = source.loc[row_num, 'toolset']
                # we check if the decomp value in source for this deal is 0; if 0, move on
                if source_decomp_value != 0 and tool != 'ComFut':
                    # print(deal_num, 'has decomp_value of', source_decomp_value)
                    # check if this deal exists in eodc
                    if str(deal_num) in eodc_deal_list:
                        eodc_decomp_value = eodc.loc[eodc['Source_Trade_ID'] == str(deal_num), decomp_cate].sum()
                        if int(round(eodc_decomp_value - source_decomp_value)) != 0:
                            error_entry = [portfolio, decomp_cate, deal_num, tool, source_decomp_value,
                                           eodc_decomp_value]
                            deal_level_rec.append(error_entry)
                    else:
                        error_entry = [portfolio, decomp_cate, deal_num, tool, source_decomp_value, 'Missing in EODc']
                        deal_level_rec.append(error_entry)

    deal_level_header = ['Portfolio', 'Decomp', 'Deal Num', 'Toolset', 'Source Value', 'EODc Value']
    deal_level_output = pd.DataFrame(deal_level_rec, columns=deal_level_header)
    deal_level_output.to_excel('deal_level_rec.xlsx')

    print("Deal-level check complete.")
    print("Deal-level report generated.")

print('Check Complete.')





