import unittest
from unittest.mock import MagicMock

from src.services.stream_selector import StreamSelector


class TestAutoAddGames(unittest.TestCase):
    def setUp(self):
        self.selector = StreamSelector()
        self.settings = MagicMock()
        self.settings.auto_add_new_games = True
        self.settings.auto_add_only_active = True
        self.settings.auto_add_within_hours = 24
        self.settings.auto_add_max_new_per_refresh = 2
        self.settings.auto_add_require_wanted_benefits = True
        self.settings.games_to_watch = ["Game1"]
        self.settings.mining_benefits = {"BADGE": True, "DIRECT_ENTITLEMENT": True}

    def _campaign(self, game, *, eligible=True, active=True, can_earn=True, has_benefits=True):
        c = MagicMock()
        c.game.name = game
        c.eligible = eligible
        c.active = active
        c.can_earn_within.return_value = can_earn
        c.has_wanted_unclaimed_benefits.return_value = has_benefits
        return c

    def test_auto_add_respects_limits_and_dedup(self):
        campaigns = [
            self._campaign("Game1"),  # already in watchlist
            self._campaign("Game2"),
            self._campaign("Game3"),
            self._campaign("Game4"),
        ]
        out = self.selector.find_auto_add_game_names(self.settings, campaigns)
        self.assertEqual(out, ["Game2", "Game3"])

    def test_auto_add_active_only(self):
        campaigns = [self._campaign("Game2", active=False), self._campaign("Game3", active=True)]
        out = self.selector.find_auto_add_game_names(self.settings, campaigns)
        self.assertEqual(out, ["Game3"])

    def test_auto_add_requires_benefits(self):
        campaigns = [
            self._campaign("Game2", has_benefits=False),
            self._campaign("Game3", has_benefits=True),
        ]
        out = self.selector.find_auto_add_game_names(self.settings, campaigns)
        self.assertEqual(out, ["Game3"])


if __name__ == "__main__":
    unittest.main()
