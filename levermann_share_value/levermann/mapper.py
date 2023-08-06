import logging
from datetime import date

from levermann_share_value.database.models import ShareValue
from levermann_share_value.levermann import constants


class ShareDataMapper:
    logger = logging.getLogger(__name__)

    perCalc = []
    per_now = -1
    per_ny = -1
    share_data = {}

    def __init__(self, share_values: [ShareValue]):
        self.share_values = share_values

    def calculate(self) -> [{}]:

        for sv in self.share_values:
            self.__get_large_cap(self.share_data, sv)
        for sv in self.share_values:
            self.__get_ebit_marge(self.share_data, sv)
            self.__get_equity_ratio(self.share_data, sv)
            self.__get_return_equity(self.share_data, sv)
            self.__get_per(self.share_data, sv)
        self.__calculate_per(self.share_data)

    def __calculate_per(self, share_data):
        """
        TODO - scrape again
        constants.price_earnings_ratio is new than I can calculate this one
        :param share_data:
        :return:
        """
        if len(self.perCalc) == 5:
            share_data[constants.price_earnings_ratio]['value'] = sum(self.perCalc) / 5
        if self.per_ny > -1 and self.per_now > -1:
            # share_data[constants.profit_grow]['value']=
            pass

    def __get_per(self, share_data: {}, sv: ShareValue):
        year_now: int = date.today().year
        if sv.name == constants.price_earnings_ratio:
            value = float(sv.value)
            if year_now == sv.related_date.year:
                self.per_now = value
            if year_now + 1 == sv.related_date.year:
                self.per_ny = value
            if year_now - 3 <= sv.related_date.year <= year_now + 1:
                self.perCalc.append(value)

    def __get_large_cap(self, share_data: {}, sv: ShareValue):
        if sv.name == constants.market_capitalization:
            share_data[constants.large_cap] = self.is_large_cap(float(sv.value))
            share_data[constants.market_capitalization] = float(sv.value)

    def __get_return_equity(self, share_data: {}, sv) -> {}:
        if sv.name == constants.return_equity and self.is_date_last_year(sv.related_date):
            share_data[constants.return_equity] = {}
            value = float(sv.value)
            share_data[constants.return_equity]['value'] = value
            if value > 20:
                share_data[constants.return_equity]['point'] = 1
            elif value < 10:
                share_data[constants.return_equity]['point'] = -1
            else:
                share_data[constants.return_equity]['point'] = 0

    def __get_ebit_marge(self, share_data: {}, sv: ShareValue):
        if sv.name == constants.ebit_margin and self.is_date_last_year(sv.related_date):
            share_data[constants.ebit_margin] = {}
            value = float(sv.value)
            share_data[constants.ebit_margin]['value'] = value
            if value > 20:
                share_data[constants.ebit_margin]['point'] = 1
            elif value < 10:
                share_data[constants.ebit_margin]['point'] = -1
            else:
                share_data[constants.ebit_margin]['point'] = 0

    def __get_equity_ratio(self, share_data, sv):
        if sv.name == constants.equity_ratio_in_percent and self.is_date_last_year(sv.related_date):
            share_data[constants.equity_ratio_in_percent] = {}
            value = float(sv.value)
            share_data[constants.equity_ratio_in_percent]['value'] = value
            if value > 25:
                share_data[constants.equity_ratio_in_percent]['point'] = 1
            elif value < 15:
                share_data[constants.equity_ratio_in_percent]['point'] = -1
            else:
                share_data[constants.equity_ratio_in_percent]['point'] = 0

    def __is_large_cap(self, market_cap: float):
        return market_cap >= 5_000_000_000

    def __is_date_last_year(self, to_check: date):
        return (date.today().year - to_check.year) == 1
