# authenticate
import gspread
from gspread_dataframe import set_with_dataframe
import logging, sys
import pandas as pd
from valuedcompany import ValuedCompany
from requests.adapters import RetryError, MaxRetryError
import time

gc = gspread.oauth()
target_sheet = 'Stock list'
sheet = gc.open(target_sheet).get_worksheet(0)
company_list = sheet.col_values(1)
# company_list = company_list[3638:]
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")
logging.debug(f'Reading sheet {target_sheet}')
logging.debug(company_list)
result = {}
for company in company_list:
    try:
        time.sleep(1)
        test = ValuedCompany(company)
        result[company] = test.score_company()
    except (RetryError, MaxRetryError, AttributeError, KeyError) as e:
        logging.error(f'Fail getting info for stock {company}')
    except ValueError:
        logging.error(f'Fail valuing for stock {company}')
df_result = pd.DataFrame(result).T.sort_values('total', ascending=False)

try:
    result_worksheet = gc.open(target_sheet).add_worksheet(title="Result", rows="3000", cols="20")
except gspread.exceptions.APIError:
    result_worksheet = gc.open(target_sheet).worksheet("Result")
set_with_dataframe(result_worksheet, df_result, include_index=True, include_column_header=True)