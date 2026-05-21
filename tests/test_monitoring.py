from datetime import datetime
import unittest
from unittest.mock import patch

from flight_alert.monitoring import (
    PriceHistory,
    monitor_certain_dates,
    monitor_two_month_weekends,
)
from flight_alert.runner import seconds_until, weekend_dates


class MonitoringTest(unittest.TestCase):
    def test_monitor_certain_dates_tracks_history_and_price_step(self):
        history = PriceHistory(prev_leav=500, prev_back=600, min_leav=480, min_back=590)

        message = monitor_certain_dates(
            {"20260601": 450, "20260602": 700},
            {"20260605": 620},
            20,
            ["20260601", "20260602"],
            ["20260605"],
            history,
            ("SHA", "BJS"),
        )

        self.assertTrue(message.should_send)
        self.assertEqual(history.prev_leav, 450)
        self.assertEqual(history.prev_back, 620)
        self.assertEqual(history.min_leav, 450)
        self.assertEqual(history.min_back, 590)
        self.assertIn("06-01: 450", message.content)

    def test_monitor_two_month_weekends_filters_weekdays_and_threshold(self):
        message = monitor_two_month_weekends(
            {
                "20260601": 300,
                "20260604": 420,
                "20260605": 380,
                "20260608": 200,
            },
            {
                "20260601": 300,
                "20260604": 450,
                "20260605": 360,
                "20260608": 200,
            },
            target_price=400,
            cities=("SHA", "BJS"),
            today=datetime(2026, 5, 21),
        )

        self.assertTrue(message.should_send)
        self.assertNotIn("06-01", message.content)
        self.assertIn("06-04(4)", message.content)
        self.assertIn("06-05(5)", message.content)

    def test_seconds_until_rolls_to_tomorrow_when_target_has_passed(self):
        class FakeDateTime(datetime):
            @classmethod
            def now(cls):
                return cls(2026, 5, 21, 10, 0, 1)

        with patch("flight_alert.runner.datetime", FakeDateTime):
            self.assertEqual(seconds_until("10:00:00"), 86399)

    def test_weekend_dates_uses_thursday_through_sunday(self):
        dates = weekend_dates(datetime(2026, 5, 21).date(), days=7)

        self.assertEqual(
            [item.strftime("%Y%m%d") for item in dates],
            ["20260521", "20260522", "20260523", "20260524"],
        )


if __name__ == "__main__":
    unittest.main()
