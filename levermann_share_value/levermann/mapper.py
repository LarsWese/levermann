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
        self.course_y1_ago = -1
        self.course_m6_ago = -1
        self.share_data = {}
        self.total_points = 0

    def calculate(self, share_values: [ShareValue]) -> [{}]:
        self.eps_calc = []
        self.eps_now = -9999
        self.eps_ny = -9999
        self.share_data = {}
        self.course_today = -9999
        self.course_m6_ago = -9999
        self.course_y1_ago = -9999
        self.total_points = 0
        for sv in share_values:
            self.__get_large_cap(sv)
        for sv in share_values:
            self.__get_ebit_marge(sv)
            self.__get_equity_ratio(sv)
            self.__get_return_equity(sv)
            self.__get_eps(sv)
            self.__get_course(sv)
        self.__calculate_per()
        self.__calculate_momentum()
        return self.share_data

    def __calculate_momentum(self):
        point_m6 = self.__calculate_course_diff_and_points(self.course_m6_ago, constants.course_m6_comparison)
        point_y1 = self.__calculate_course_diff_and_points(self.course_y1_ago, constants.course_y1_comparison)

        # course momentum compare the two courses comparison
        course_momentum = 0
        if point_m6 == 1 and (point_y1 == 0 or point_y1 == -1):
            course_momentum = 1
        elif point_m6 == -1 and (point_y1 == 0 or point_y1 == 1):
            course_momentum = -1
        self.total_points += point_m6 + point_y1 + course_momentum
        self.share_data[constants.course_momentum] = {'value': f'{point_m6}; {point_y1}',
                                                      'point': course_momentum}

    def __is_valid_course(self, course):
        return course > -9999 and course != 0.0

    def __calculate_course_diff_and_points(self, course, constant):
        """
        :param course: The current course value.
        :param constant: The constant value used for calculating points.
        :return: The calculated point for the given course.

        This private method calculates the difference and points for a given course. It takes in a course value and a constant value as parameters. The method first checks if the course value
        * is valid using the private method __is_valid_course().

        If the course value is valid, it then calculates the difference between the current course value (self.course_today) and the given course value.

        If the difference is within the range -0.05 and 0.05, the point is set to 0. If the current course value is greater than the given course value, the point is set to 1. If the current
        * course value is less than the given course value, the point is set to -1.

        Finally, the share_data dictionary is updated with the course and point values. The point value is then returned.

        """
        point = 0
        if self.__is_valid_course(course):
            diff = 1 - self.course_today / course
            point = 0
            if -0.05 < diff < 0.05:
                point = 0
            elif self.course_today > course:
                point = 1
            elif self.course_today < course:
                point = -1
            self.share_data[constant] = {'value': f'{self.course_today}; {course}',
                                         'point': point}
        return point

    def __get_course(self, sv: ShareValue):
        if sv.name == constants.course_m6_ago:
            self.course_m6_ago = float(sv.value)
        elif sv.name == constants.course_y1_ago:
            self.course_y1_ago = float(sv.value)
        elif sv.name == constants.course_today:
            self.course_today = float(sv.value)

    def __calculate_per(self):
        """
        constants.earnings_per_share needs to be scraped again
        :param share_data:
        :return:
        """
        # price earnings ratio total over last 3, this and next year
        if len(self.eps_calc) == 5:
            value = self.course_today / (sum(self.eps_calc) / 5)
            point = self.__per_points(value)
            self.share_data[constants.price_earnings_ratio_5y] = {'value': value, 'point': point}

        # price earnings ratio now
        if self.eps_now > -9999 and self.eps_now != 0:
            value = self.course_today / self.eps_now
            point = self.__per_points(value)
            self.share_data[constants.price_earnings_ratio_ay] = {'value': value, 'point': point}

        # profit growth
        if self.eps_now > -9999 and self.eps_now != 0 and self.eps_ny > -9999 and self.eps_ny != 0:
            point = 0
            diff = 1 - self.eps_now / self.eps_ny
            if -0.05 < diff < 0.05:
                point = 0
            if self.eps_now < self.eps_ny:
                point = 1
            elif self.eps_now > self.eps_ny:
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
