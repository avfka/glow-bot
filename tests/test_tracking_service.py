import unittest

from services.tracking import apply_tracking_toggle, calculate_streak


class CalculateStreakTest(unittest.TestCase):
    def test_starts_streak_when_both_routines_done(self):
        self.assertEqual(
            calculate_streak(
                morning_done=True,
                evening_done=True,
                current_streak=0,
                yesterday_streak=0,
                yesterday_complete=False,
            ),
            1,
        )

    def test_extends_yesterday_streak_when_today_complete(self):
        self.assertEqual(
            calculate_streak(
                morning_done=True,
                evening_done=True,
                current_streak=0,
                yesterday_streak=4,
                yesterday_complete=True,
            ),
            5,
        )

    def test_keeps_existing_today_streak_when_saving_again(self):
        self.assertEqual(
            calculate_streak(
                morning_done=True,
                evening_done=True,
                current_streak=3,
                yesterday_streak=0,
                yesterday_complete=False,
            ),
            3,
        )

    def test_keeps_streak_alive_until_day_is_incomplete_after_complete_yesterday(self):
        self.assertEqual(
            calculate_streak(
                morning_done=True,
                evening_done=False,
                current_streak=0,
                yesterday_streak=7,
                yesterday_complete=True,
            ),
            7,
        )

    def test_resets_when_today_and_yesterday_are_incomplete(self):
        self.assertEqual(
            calculate_streak(
                morning_done=True,
                evening_done=False,
                current_streak=2,
                yesterday_streak=0,
                yesterday_complete=False,
            ),
            0,
        )


class ApplyTrackingToggleTest(unittest.TestCase):
    def test_toggles_morning_without_losing_evening(self):
        self.assertEqual(
            apply_tracking_toggle(
                action="morning",
                morning_done=False,
                evening_done=True,
            ),
            (True, True),
        )

    def test_toggles_evening_without_losing_pending_morning(self):
        self.assertEqual(
            apply_tracking_toggle(
                action="evening",
                morning_done=True,
                evening_done=False,
            ),
            (True, True),
        )

    def test_ignores_unknown_action(self):
        self.assertEqual(
            apply_tracking_toggle(
                action="save",
                morning_done=True,
                evening_done=False,
            ),
            (True, False),
        )


if __name__ == "__main__":
    unittest.main()
