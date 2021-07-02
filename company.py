import logging
from yahooquery import Ticker
from requests.adapters import RetryError, MaxRetryError
import pandas as pd
from math import isnan


class Company(object):
    def __init__(self, ticker: str):
        logging.info(f'Initializing ticker {ticker}')
        self.name = ticker
        company_ticker = Ticker(ticker)
        try:
            self.all_financial_data = company_ticker.all_financial_data().set_index('asOfDate')
            self.df_price_day_history = self._set_df(company_ticker.history(period='max', interval='1d'))
        except AttributeError as e:
            logging.error(f'Error getting valuation for {self.name}')
            logging.error(e)
            self.valuation_measures = pd.DataFrame()
            raise e
        except (RetryError, MaxRetryError) as e:
            logging.error(f"Error connecting yahoo in {ticker}")
            logging.error(e)
            raise e
        try:
            self.df_price_day_history['dividends']
        except KeyError:
            self.df_price_day_history['dividends'] = 0
        try:
            self.all_financial_data['NetIncome']
            self.all_financial_data['StockholdersEquity']
        except KeyError as e:
            logging.error("Failed getting netincome or StockholdersEquity")
            raise e

    @classmethod
    def _set_df(cls, df):
        df = df.reset_index()
        df = df.set_index('date')
        df.index = pd.to_datetime(df.index)
        return df.sort_index()

    def get_average_roe(self) -> float:
        self.all_financial_data['Return on equity'] = \
            self.all_financial_data['NetIncome'] / self.all_financial_data['StockholdersEquity']
        four_year_roe = self.all_financial_data['Return on equity'].mean()
        return four_year_roe

    def get_dividend_by_year(self) -> pd.Series:
        return self.df_price_day_history.groupby(lambda x: x.year)['dividends'].agg('sum')

    def get_dividend(self) -> pd.Series:
        return self.df_price_day_history[self.df_price_day_history['dividends'] > 0]['dividends']

    def get_revenue(self) -> pd.Series:
        return self.all_financial_data['TotalRevenue']

    def get_operating_profit(self) -> pd.Series:
        try:
            profit = self.all_financial_data['OperatingIncome']
        except KeyError:
            profit = self.all_financial_data['NetIncome']
        return profit

    def get_net_profit_margin(self) -> pd.Series:
        return self.all_financial_data['NetIncome'] / self.all_financial_data['TotalRevenue']

    def get_stock_price(self, duration: str = None) -> pd.Series:
        if duration:
            return self.df_price_day_history['adjclose'].last(duration)
        else:
            return self.df_price_day_history['adjclose']

    def get_company_age(self) -> float:
        return (pd.Timestamp.now() - self.df_price_day_history.sort_index().index[0]).days/365.25

    def get_quick_ratio(self) -> float:
        try:
            ratio = ((self.all_financial_data['CurrentAssets'] - self.all_financial_data['Inventory'])
               / self.all_financial_data['CurrentLiabilities']).iloc[-1]
            if isnan(ratio):
                return 'N/A'
        except (KeyError, IndexError):
            return 'N/A'
        return ratio


if __name__ == "__main__":
    test = Company('7751.T')
    test.get_average_roe()
    test.get_dividend_by_year()
    test.get_dividend()
    test.get_revenue()
    test.get_operating_profit()
    test.get_net_profit_margin()
    test.get_stock_price()
    test.get_company_age()
    result = test.get_quick_ratio()
