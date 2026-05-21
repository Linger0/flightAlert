import unittest

from flight_alert.city_codes import normalize_city


class CityCodesTest(unittest.TestCase):
    def test_normalize_city_accepts_city_name_and_code(self):
        self.assertEqual(normalize_city("上海", {"上海": "SHA"}), "SHA")
        self.assertEqual(normalize_city("sha", {}), "SHA")

    def test_normalize_city_rejects_unknown_value(self):
        with self.assertRaises(ValueError):
            normalize_city("不存在的城市", {})


if __name__ == "__main__":
    unittest.main()
