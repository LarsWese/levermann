import warnings
from datetime import date

import pandas as pd
from yahooquery import Ticker

from levermann_share_value.scraper import get_weekdays_m6_nearest_today_y1_y5, nearest_coming_weekday_date
from levermann_share_value.scraper.raw_data import RawData

warnings.simplefilter(action='ignore', category=FutureWarning)


def recommendation_trend(symbol: str) -> [RawData]:
    print('\n\nRecommendation_trend')
    ticker = Ticker(symbol)
    print(ticker.recommendation_trend)


if __name__ == '__main__':
    recommendation_trend('crm')
    # symbol = 'ce2.de'
    # crm = Ticker(symbol)
    #
    # # print(crm)
    # # print(crm.financial_data)
    # # print('balance_sheet\n')
    # # print(crm.balance_sheet())
    # # print('cash_flow\n')
    # # print(crm.cash_flow())
    # print('income_statement')
    # flow: pd.DataFrame = crm.all_financial_data()
    # flow = flow.set_index('asOfDate')
    # price_data = crm.price[symbol]
    #
    # print(f'\n\nCoorperate Events')
    # print(f'\nCalendar Events')
    # print(f'{crm.calendar_events}')
    # print(f'\nCooperate Events')
    # print(f'{crm.corporate_events}')
    #
    # try:
    #     print(f'\n\n market cap {price_data["marketCap"]}')
    # except KeyError:
    #     pass
    # print('\n\nEigenkapitalrendite (Roe)')
    # flow['RoE'] = (flow['NetIncome'] / flow['StockholdersEquity']) * 100
    # print(flow.filter(items=['asOfDate', 'NetIncome', 'StockholdersEquity', 'RoE']))
    #
    # print('\n\nEigenkapitalquote (equity ratio)')
    # flow['equityRatio'] = (flow['StockholdersEquity'] / flow['TotalAssets']) * 100
    # print(flow.filter(items=['asOfDate', 'StockholdersEquity', 'TotalAssets', 'equityRatio']))
    #
    # print('\n\nEBIT-Marge (ebit margin)')
    # flow['EBITMargin'] = (flow['EBIT'] / flow['TotalRevenue']) * 100
    # print(flow.filter(items=['asOfDate', 'EBIT', 'TotalRevenue', 'EBITMargin']))
    #
    # # P/E Ratio = Stock Price / Earnings Per Share (EPS)
    # print('\n\nKGV (PE-Ratio)')
    # m6, nearest_weekday, y1, y5 = get_weekdays_m6_nearest_today_y1_y5(date.today())
    # history_daily = crm.history(start=y5)
    # print(history_daily.loc[symbol].loc[[m6]]['close'])
    # print(history_daily.loc[symbol].loc[[y1]]['close'])
    # try:
    #     print(history_daily.loc[symbol].loc[[y5]]['close'])
    # except KeyError:
    #     pass
    # print(history_daily.loc[symbol].loc[[nearest_weekday]]['close'])
    #
    # # KGV 5 Jahre von onvista. Wenn onvista keine DAten dann KGV 4 Jahre von yahoo
    # # print('\n\n Some Calculations')
    # # for index in flow.index:
    # #     d = nearest_coming_weekday_date(index.date())
    # #     flow.at[index, 'PeRatio'] = history_daily.loc[symbol].at[d, "close"] / flow.at[index, 'BasicEPS']
    # # print(f"{flow.filter(items=['asOfDate', 'PeRatio'])} mean={flow.filter(items=['asOfDate', 'PeRatio']).mean()}")
    #
    # print('\n\nCurrent PE-Ratio (KGV aktuell)')
    # print(price_data)
    # eps_current = flow.iloc[-1]['NetIncome'] / price_data['regularMarketVolume']
    # print(f"eps: {eps_current} = {flow.iloc[-1]['NetIncome'] } / {price_data['regularMarketVolume']}")
    # pe_ratio_current = price_data['regularMarketPrice'] / eps_current
    # print(f"pe-ratio current: {pe_ratio_current} = {price_data['regularMarketPrice']} / {eps_current}")
    #
    # # print('\n\nCooperate events')
    # # print(crm.corporate_events)
    #
    # print('\n\nCalendar events')
    # print(crm.calendar_events)
    #
    # print('\n\nRecommendation')
    # print(crm.recommendations)
    #
    # print('\n\nRecommendation_trend')
    # print(crm.recommendation_trend)
