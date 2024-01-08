import unittest
from datetime import date

from levermann_share_value.database.models import ShareValue
from levermann_share_value.levermann.mapper import get_last_year_value


class MyTestCase(unittest.TestCase):
    def test_get_last_year_value(self):
        e1: ShareValue = ShareValue(name='return_equity', related_date=date(2021, 1, 1), value='21', note='2021')
        e2: ShareValue = ShareValue(name='return_equity', related_date=date(2022, 1, 1), value='23', note='2022')
        e3: ShareValue = ShareValue(name='return_equity', related_date=date(2023, 1, 1), value='24', note='2023e')
        e3: ShareValue = ShareValue(name='return_equity', related_date=date(2024, 1, 1), value='24', note='2024e')
        return_equity_all: [ShareValue] = [e1, e2, e3]
        year, value = get_last_year_value(2024, return_equity_all)
        self.assertEqual(year, 2022)
        self.assertEqual(value, '23')


if __name__ == '__main__':
    unittest.main()
