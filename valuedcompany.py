from company import Company
from numpy import polyfit
import pandas as pd
import matplotlib.dates as mdates
import logging, sys
from autologging import TRACE, traced
from math import isnan
'''
age: max 0
quick ratio max 0

trend: max 30
roe: max 30
profit margin: max 10
dividend: max 10
revenue: max 10
profit: max 10
'''


@traced()
class ValuedCompany(Company):
    def calculate_trend_score(self):
        trend_5_y_max_score = 14
        trend_2_y_max_score = 9
        trend_1_y_max_score = 7
        trend_max_target = 0.3  # yearly ROI for max score
        score = 0
        trend_5y = self._calculate_price_trend(self.get_stock_price('1825D'))
        trend_2y = self._calculate_price_trend(self.get_stock_price('730D'))
        trend_1y = self._calculate_price_trend(self.get_stock_price('365D'))
        score += self._normalize_score(trend_5y, trend_max_target, trend_5_y_max_score)
        score += self._normalize_score(trend_2y, trend_max_target, trend_2_y_max_score)
        score += self._normalize_score(trend_1y, trend_max_target, trend_1_y_max_score)
        return score

    def calculate_age_score(self):
        age = self.get_company_age()
        age_dq_threshold = 5
        dq_score = -100
        good_score = 0
        age_full_grown_threshold = 10
        age_penalty_per_year = 3
        if age < age_dq_threshold:
            return dq_score
        elif age < age_full_grown_threshold:
            return (age - age_full_grown_threshold) * age_penalty_per_year
        else:
            return good_score

    def calculate_roe_score(self):
        roe_max_score = 30
        target_roe = 0.3
        return self._normalize_score(self.get_average_roe(), target_roe, roe_max_score)

    def calculate_profit_margin_score(self):
        profit_margin_max_score = 10
        target_roe = 0.2
        base_roe = 0.05
        target_roe_above_base = target_roe - base_roe
        roe_above_base = self.get_average_roe() - base_roe
        return self._normalize_score(roe_above_base, target_roe_above_base, profit_margin_max_score)

    # TODO only count this year if no pending dividend remaining, now just ignore most recent year
    def calculate_dividend_score(self):
        target_avg_growth = 0.3
        dividend_max_score = 10
        growth = self.get_dividend_by_year()[-6:-1].pct_change().mean()
        if isnan(growth):
            growth = 0
        return self._normalize_score(growth, target_avg_growth, dividend_max_score)

    def calculate_revenue_score(self):
        target_revenue_growth = 0.3
        revenue_max_scoure = 10
        growth = self.get_revenue()[-5:].pct_change().mean()
        return self._normalize_score(growth, target_revenue_growth, revenue_max_scoure)

    def calculate_profit_score(self):
        target_profit_growth = 0.3
        profit_max_score = 10
        growth = self.get_operating_profit()[-5:].pct_change().mean()
        return self._normalize_score(growth, target_profit_growth, profit_max_score)

    def score_company(self):
        score = {}
        score['trend'] = self.calculate_trend_score()
        score['roe'] = self.calculate_roe_score()
        score['age'] = self.calculate_age_score()
        score['margin'] = self.calculate_profit_margin_score()
        score['dividend'] = self.calculate_dividend_score()
        score['profit'] = self.calculate_profit_score()
        score['revenue'] = self.calculate_revenue_score()
        score['total'] = sum(score.values())
        score['quick ratio'] = self.get_quick_ratio()
        return score

    @staticmethod
    def _normalize_score(score, target, max_score):
        ratio = score / target
        return max(min(ratio * max_score, max_score), 0)

    @staticmethod
    def _calculate_price_trend(price_series: pd.Series):
        price_series = price_series
        date = mdates.date2num(price_series.index)
        price = price_series.values
        z = polyfit(date, price, 1)
        if (z[0] * date[0] + z[1]) < 0:
            if price[0] < 0:
                raise ValueError("Stock price at start and regression line both negative")
            else:
                return z[0] * 365 / (price[0]) # use starting stock price as divisor
        else:
            return z[0] * 365 / (z[0] * date[0] + z[1])  # yearly percent return by linear regression


if __name__ == "__main__":
    logging.basicConfig(level=TRACE, stream=sys.stdout,
                        format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")
    test = ValuedCompany('4369.T')
    test.score_company()

