import unittest
from levermann_share_value.levermann.mapper import get_last_year_value
from levermann_share_value.database.models import ShareValue


class MyTestCase(unittest.TestCase):
    def test_get_last_year_value(self):
        e1: ShareValue = ShareValue(name='return_equity', related_date='2021', value='21')
        e2: ShareValue = ShareValue(name='return_equity', related_date='2022', value='23')
        e3: ShareValue = ShareValue(name='return_equity', related_date='2023e', value='24')
        return_equity_all: [ShareValue] = [e1, e2, e3]
        year, value = get_last_year_value(2024, return_equity_all)
        self.assertEqual(year, 2022)
        self.assertEqual(value, '23')


if __name__ == '__main__':
    unittest.main()
