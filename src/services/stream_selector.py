from datetime import datetime, timedelta, timezone

from src.config.settings import Settings
from src.models.campaign import DropsCampaign
from src.models.game import Game


class StreamSelector:
    def _get_wanted_game_tree(
        self, settings: Settings, campaigns: list[DropsCampaign]
    ) -> list[dict]:
        """
        Get the hierarchical tree of wanted items (Games -> Campaigns -> Drops -> Benefits).
        Ignoring 'can earn within' time constraint.
        """
        wanted_games = []
        games_to_watch = settings.games_to_watch
        mining_benefits = settings.mining_benefits
        next_hour = datetime.now(timezone.utc) + timedelta(hours=1)

        for game_name in games_to_watch:
            wanted_campaigns = []
            game_obj = None
            game_name_lower = game_name.lower()

            # Find all campaigns for this game
            for campaign in campaigns:
                if campaign.game.name.lower() != game_name_lower:
                    continue

                if game_obj is None:
                    game_obj = campaign.game

                if not campaign.can_earn_within(next_hour):
                    continue

                wanted_drops = []
                for drop in campaign.drops:
                    if drop.is_claimed:
                        continue

                    filtered_benefits = drop.get_wanted_unclaimed_benefits(mining_benefits)

                    if len(filtered_benefits) > 0:
                        wanted_drops.append({"name": drop.name, "benefits": filtered_benefits})

                if len(wanted_drops) > 0:
                    wanted_campaigns.append(
                        {
                            "id": campaign.id,
                            "name": campaign.name,
                            "url": campaign.campaign_url,
                            "drops": wanted_drops,
                        }
                    )

            if len(wanted_campaigns) > 0:
                wanted_games.append(
                    {
                        "game_id": game_obj.id if game_obj else None,
                        "game_name": game_name,
                        "game_icon": game_obj.box_art_url if game_obj else None,
                        "game_obj": game_obj,
                        "campaigns": wanted_campaigns,
                    }
                )

        return wanted_games

    def get_wanted_game_tree(
        self, settings: Settings, campaigns: list[DropsCampaign]
    ) -> list[dict]:
        return [
            {**game, "game_obj": None} for game in self._get_wanted_game_tree(settings, campaigns)
        ]

    def get_wanted_games(self, settings: Settings, campaigns: list[DropsCampaign]) -> list[Game]:
        return [game["game_obj"] for game in self._get_wanted_game_tree(settings, campaigns)]


    def find_auto_add_game_names(
        self, settings: Settings, campaigns: list[DropsCampaign]
    ) -> list[str]:
        """Find game names that should be auto-added to games_to_watch."""
        if not getattr(settings, "auto_add_new_games", False):
            return []

        within_hours = max(1, int(getattr(settings, "auto_add_within_hours", 24)))
        max_new = max(0, int(getattr(settings, "auto_add_max_new_per_refresh", 3)))
        if max_new == 0:
            return []

        existing = {g.lower() for g in settings.games_to_watch}
        require_benefits = bool(getattr(settings, "auto_add_require_wanted_benefits", True))
        only_active = bool(getattr(settings, "auto_add_only_active", True))
        mining_benefits = settings.mining_benefits
        deadline = datetime.now(timezone.utc) + timedelta(hours=within_hours)

        candidates: list[str] = []
        for campaign in campaigns:
            game_name = campaign.game.name
            if game_name.lower() in existing:
                continue
            if not campaign.eligible:
                continue
            if only_active and not campaign.active:
                continue
            if not campaign.can_earn_within(deadline):
                continue
            if require_benefits and not campaign.has_wanted_unclaimed_benefits(mining_benefits):
                continue

            candidates.append(game_name)
            existing.add(game_name.lower())
            if len(candidates) >= max_new:
                break

        return candidates
