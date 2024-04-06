import logging
from datetime import date

from levermann_share_value.database.models import ShareValue
from levermann_share_value.levermann import constants as cs

logger = logging.getLogger(__name__)


def to_dict(share_values: [ShareValue]) -> {}:
    result = {}
    for sv in share_values:
        if sv.name not in result:
            result[sv.name] = [sv]
        else:
            result[sv.name].append(sv)
    return result


def is_large_cap(market_cap: float):
    return market_cap >= 5_000_000_000


def per_points(value) -> int:
    point = 0
    if value < 12:
        point = 1
    if value > 16:
        point = -1
    return point


def is_valid_course(course):
    return course > -9999 and course != 0.0


def get_last_year_value(current_year: int, return_equity: [ShareValue]) -> (int, str):
    return_equity_year = {int: str}
    found_year = 0
    for r in return_equity:
        # all non estimated
        if not r.note.endswith('e'):
            related_date: date = r.related_date
            return_equity_year[int(related_date.year)] = r.value

    if current_year in return_equity_year:
        found_year = current_year
    elif current_year - 1 in return_equity_year:
        found_year = current_year - 1
    elif current_year - 2 in return_equity_year:
        found_year = current_year - 2
    return found_year, return_equity_year[found_year]


def calculate_last_balance_year(svs: [ShareValue]):
    year_now = date.today().year
    for r in range(year_now - 1, year_now - 3, -1):
        for s in svs:
            if s.related_date.year == r and not s.note.endswith('e'):
                logger.info(f'found last balance year {r} with note {s.note} - {s.name}')
                return r


def get_latest_value(svs: [ShareValue]) -> ShareValue:
    latest_value: ShareValue = svs[0]
    for sv in svs:
        if sv.fetch_date > latest_value.fetch_date:
            latest_value = sv
    return latest_value


class ShareDataMapper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.eps_calc = []
        self.eps_now = -1
        self.eps_ny = -1
        self.share_price_today = -1
        self.share_price_y1_ago = -1
        self.share_price_m6_ago = -1
        self.share_data = {}
        self.total_points = 0

    def calculate(self, share_values: [ShareValue]) -> [{}]:
        self.eps_calc = []
        self.eps_now = -9999
        self.eps_ny = -9999
        self.share_data = {}
        self.share_price_today = -9999
        self.share_price_m6_ago = -9999
        self.share_price_y1_ago = -9999
        self.total_points = 0

        svs = to_dict(share_values)

        last_balance_year: int = 0
        if cs.last_balance_year in svs:
            last_balance_year = int(svs[cs.last_balance_year][0].value)
        else:
            if cs.ebit_margin in svs:
                last_balance_year = calculate_last_balance_year(svs[cs.ebit_margin])
        if last_balance_year == 0:
            logger.debug(f'no last_balance_year - take default year - 1; {share_values}')
            last_balance_year = date.today().year - 1
        self.share_data[cs.last_balance_year] = last_balance_year
        self.__get_large_cap(svs)
        self.__get_ebit_marge(svs, last_balance_year)
        self.__get_equity_ratio(svs, last_balance_year)
        self.__get_return_equity_ly(svs, last_balance_year)
        self.__get_eps(svs, last_balance_year)
        self.__get_share_price(svs)
        self.__get_analysts(svs)
        self.__calculate_per()
        self.__calculate_momentum()

        self.__calculate_total_points()
        return self.share_data

    def __get_analysts(self, svs: {str: [ShareValue]}) -> None:
        num_buy = 0
        num_sell = 0
        num_hold = 0
        num_total = 0
        if cs.numBuy in svs:
            num_buy = int(svs[cs.numBuy][0].value)
        if cs.numSell in svs:
            num_sell = int(svs[cs.numSell][0].value)
        if cs.numHold in svs:
            num_hold = int(svs[cs.numHold][0].value)
        if cs.numTotal in svs:
            num_total = int(svs[cs.numTotal][0].value)
        point = 0
        if num_buy > num_hold and num_buy > num_sell:
            point = 1
        if num_sell > num_hold and num_sell > num_buy:
            point = -1
        self.share_data[cs.analyzer_recommendation] = {'value': f'{num_buy}; {num_hold}; {num_sell}',
                                                       'point': point}

    def __get_large_cap(self, svs: {str: [ShareValue]}) -> None:
        if cs.market_capitalization in svs:
            market_cap: ShareValue = svs[cs.market_capitalization][0]
            self.share_data[cs.large_cap] = is_large_cap(float(market_cap.value))
            self.share_data[cs.market_capitalization] = float(market_cap.value)

    def __get_return_equity_ly(self, svs: {str: [ShareValue]}, last_balance_year: int) -> None:
        if cs.return_equity in svs:
            return_equity: [ShareValue] = svs[cs.return_equity]
            if last_balance_year > 0:
                for re in return_equity:
                    if re.related_date.year == last_balance_year:
                        self.__calculate_points(cs.return_equity, float(re.value), 10, 20)
                        break

    def __get_ebit_marge(self, svs: {str: [ShareValue]}, last_balance_year: int) -> None:
        if cs.ebit_margin in svs:
            ebit_margin: [ShareValue] = svs[cs.ebit_margin]
            if last_balance_year and last_balance_year > 0:
                for em in ebit_margin:
                    if em.related_date.year == last_balance_year:
                        self.__calculate_points(cs.ebit_margin, float(em.value), 6, 12)
                        break

    def __get_equity_ratio(self, svs: {str: [ShareValue]}, last_balance_year: int) -> None:
        if cs.equity_ratio_in_percent in svs:
            equity_ratio: [ShareValue] = svs[cs.equity_ratio_in_percent]
            if last_balance_year and last_balance_year > 0:
                for em in equity_ratio:
                    if em.related_date.year == last_balance_year:
                        self.__calculate_points(cs.equity_ratio_in_percent, float(em.value), 15, 25)
                        break

    def __get_eps(self, svs: {str: [ShareValue]}, last_balance_year: int) -> None:
        if cs.earnings_per_share in svs:
            eps: [ShareValue] = svs[cs.earnings_per_share]
            year_now: int = date.today().year
            for e in eps:
                value = float(e.value)
                if year_now == e.related_date.year:
                    self.eps_now = value
                if year_now + 1 == e.related_date.year:
                    self.eps_ny = value
                if year_now - 3 <= e.related_date.year <= year_now + 1:
                    self.eps_calc.append(value)

    def __calculate_momentum(self):
        point_m6 = self.__calculate_share_price_diff_and_points(self.share_price_m6_ago, cs.share_price_m6_comparison)
        point_y1 = self.__calculate_share_price_diff_and_points(self.share_price_y1_ago, cs.share_price_y1_comparison)

        # course momentum compare the two courses comparison
        share_price_momentum = 0
        if point_m6 == 1 and (point_y1 == 0 or point_y1 == -1):
            share_price_momentum = 1
        elif point_m6 == -1 and (point_y1 == 0 or point_y1 == 1):
            share_price_momentum = -1
        self.total_points += point_m6 + point_y1 + share_price_momentum
        self.share_data[cs.share_price_momentum] = {'value': f'{point_m6}; {point_y1}',
                                                    'point': share_price_momentum}

    def __calculate_share_price_diff_and_points(self, course, constant):
        """
        :param course: The current course value.
        :param constant: The constant value used for calculating points.
        :return: The calculated point for the given course.

        This private method calculates the difference and points for a given course. It takes in a course value and a constant value as parameters. The method first checks if the course value
        * is valid using the private method __is_valid_course().

        If the course value is valid, it then calculates the difference between the current course value (self.share_price_today) and the given course value.

        If the difference is within the range -0.05 and 0.05, the point is set to 0. If the current course value is greater than the given course value, the point is set to 1. If the current
        * course value is less than the given course value, the point is set to -1.

        Finally, the share_data dictionary is updated with the course and point values. The point value is then returned.

        """
        point = 0
        if is_valid_course(course):
            diff = 1 - self.share_price_today / course
            point = 0
            if -0.05 < diff < 0.05:
                point = 0
            elif self.share_price_today > course:
                point = 1
            elif self.share_price_today < course:
                point = -1
            self.share_data[constant] = {'value': f'{self.share_price_today}; {course}',
                                         'point': point}
        return point

    def __get_share_price(self, svs: {str: [ShareValue]}):
        if cs.share_price_m6_ago in svs:
            m6_ago = svs[cs.share_price_m6_ago][0]
            self.share_price_m6_ago = float(m6_ago.value)
        if cs.share_price_y1_ago in svs:
            y1_ago = svs[cs.share_price_y1_ago][0]
            self.share_price_y1_ago = float(y1_ago.value)
        if cs.share_price_today in svs:
            today = svs[cs.share_price_today][0]
            self.share_price_today = float(today.value)

    def __calculate_per(self):
        """
        cs.earnings_per_share needs to be scraped again
        :param share_data:
        :return:
        """
        # price earnings ratio total over last 3, this and next year
        if len(self.eps_calc) == 5 and sum(self.eps_calc) > 0:
            value = self.share_price_today / (sum(self.eps_calc) / 5)
            point = per_points(value)
            self.share_data[cs.price_earnings_ratio_5y] = {'value': value, 'point': point}

        # price earnings ratio now
        if self.eps_now > -9999 and self.eps_now != 0:
            value = self.share_price_today / self.eps_now
            point = per_points(value)
            self.share_data[cs.price_earnings_ratio_ay] = {'value': value, 'point': point}

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
            self.share_data[cs.profit_growth] = {'value': f'{self.eps_now}; {self.eps_ny}', 'point': point}

    def __calculate_points(self, constant, value, low_val, high_val):
        self.share_data[constant] = {'value': value, 'point': 0}
        if value < low_val:
            self.share_data[constant]['point'] = -1
        elif value > high_val:
            self.share_data[constant]['point'] = 1

    def __calculate_total_points(self):
        total_points = 0
        total_values = 0
        for s in self.share_data:
            if type(self.share_data[s]) is dict:
                total_values += 1
                total_points += self.share_data[s]['point']
        self.share_data['total_points'] = {'point': total_points, 'value': total_values}
