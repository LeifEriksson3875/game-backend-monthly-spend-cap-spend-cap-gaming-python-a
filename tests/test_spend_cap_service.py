import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.spend_cap_service import Workload, decide_spend


def test_moderation_queue_is_rejected_when_the_combined_plan_crosses_cap():
    plan = decide_spend(
        Workload(player_assets=1000, live_events=10, moderation_items=100),
        hard_cap_usd=12.0,
    )

    assert plan.estimated_usd == 13.8
    assert plan.allowed is False
    assert plan.reason == "monthly hard cap would be exceeded"
