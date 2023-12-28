import logging
from datetime import date

from levermann_share_value.database.models import ShareValue
from levermann_share_value.levermann import constants


class ShareDataMapper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.eps_calc = []
        self.eps_now = -1
        self.eps_ny = -1
        self.course_today = -1
        self.share_data = {}

    def calculate(self, share_values: [ShareValue]) -> [{}]:
        self.eps_calc = []
        self.eps_now = -9999
        self.eps_ny = -9999
        self.share_data = {}
        self.course_today = -9999
        for sv in share_values:
            self.__get_large_cap(sv)
        for sv in share_values:
            self.__get_ebit_marge(sv)
            self.__get_equity_ratio(sv)
            self.__get_return_equity(sv)
            self.__course_today(sv)
            self.__get_eps(sv)
        self.__calculate_per()
        return self.share_data

    def __course_today(self, sv: ShareValue):
        if sv.name == constants.course_today:
            self.course_today = float(sv.value)

    def __calculate_per(self):
        """
        TODO - scrape again
        constants.earnings_per_share needs to be scraped again
        :param share_data:
        :return:
        """
        if len(self.eps_calc) == 5:
            value = self.course_today / (sum(self.eps_calc) / 5)
            point = self.__per_points(value)
            self.share_data[constants.price_earnings_ratio_5y] = {'value': value, 'point': point}

        if self.eps_now > -9999 and self.eps_now != 0:
            value = self.course_today / self.eps_now
            point = self.__per_points(value)
            self.share_data[constants.price_earnings_ratio_ay] = {'value': value, 'point': point}

        if self.eps_now > -9999 and self.eps_now != 0 and self.eps_ny > -9999 and self.eps_ny != 0:
            eps_ay =  self.eps_now
            eps_ny = self.eps_ny
            point = 0
            if self.eps_now < self.eps_ny:
                point = 1
            if self.eps_now > self.eps_ny:
                point = -1
            self.share_data[constants.profit_growth] = {'value': f'{self.eps_now}; {self.eps_ny}', 'point': point}

    def __per_points(self, value):
        point = 0
        if value < 12:
            point = 1
        if value > 16:
            point = -1
        return point

    def __get_eps(self, sv: ShareValue):
        year_now: int = date.today().year
        if sv.name == constants.earnings_per_share:
            value = float(sv.value)
            if year_now == sv.related_date.year:
                self.eps_now = value
            if year_now + 1 == sv.related_date.year:
                self.eps_ny = value
            if year_now - 3 <= sv.related_date.year <= year_now + 1:
                self.eps_calc.append(value)

    def __get_large_cap(self, sv: ShareValue):
        if sv.name == constants.market_capitalization:
            self.share_data[constants.large_cap] = self.__is_large_cap(float(sv.value))
            self.share_data[constants.market_capitalization] = float(sv.value)

    def __get_return_equity(self, sv: ShareValue):
        if sv.name == constants.return_equity and self.__is_date_last_year(sv.related_date):
            self.__calculate_points(constants.return_equity, float(sv.value), 10, 20)

    def __get_ebit_marge(self, sv: ShareValue):
        if sv.name == constants.ebit_margin and self.__is_date_last_year(sv.related_date):
            self.__calculate_points(constants.ebit_margin, float(sv.value), 6, 12)

    def __get_equity_ratio(self, sv: ShareValue):
        if sv.name == constants.equity_ratio_in_percent and self.__is_date_last_year(sv.related_date):
            self.__calculate_points(constants.equity_ratio_in_percent, float(sv.value), 15, 25)

    def __calculate_points(self, constant, value, low_val, high_val):
        self.share_data[constant] = {'value': value, 'point': 0}
        if value < low_val:
            self.share_data[constant]['point'] = -1
        elif value > high_val:
            self.share_data[constant]['point'] = 1

    def __is_large_cap(self, market_cap: float):
        return market_cap >= 5_000_000_000

    def __is_date_last_year(self, to_check: date):
        return (date.today().year - to_check.year) == 1
