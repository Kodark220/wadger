import asyncio
import pytest
import sys
import os

# Ensure project root is on sys.path so tests can import local package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prediction_wager.contract import PredictionWagerContract


@pytest.mark.asyncio
async def test_full_flow_with_mock_outcome():
    c = PredictionWagerContract()

    created = await c.create_wager(
        prediction="Bitcoin will reach $100,000 by December 31, 2026",
        player_a="0xAlice...",
        stake_amount=100,
        deadline="2026-12-31T23:59:59",
        category="crypto",
        verification_criteria="Check coinmarketcap.com for BTC price",
    )

    wid = created["wager_id"]
    accept = await c.accept_wager(wager_id=wid, player_b="0xBob...")
    assert accept["status"] == "active"
    assert accept["total_pot"] == 200

    verification = await c.verify_prediction(wager_id=wid, current_date="2027-01-01", mock_outcome="YES",
                                             mock_evidence="CoinMarketCap shows BTC at $105,432 on 2026-12-28")
    assert verification["outcome"] == "YES"
    assert verification["winner"] == "0xAlice..."

    resolved = await c.resolve_wager(wager_id=wid, outcome=verification["outcome"], winner=verification["winner"], verification_data=verification)
    assert resolved["winner"] == "0xAlice..."
    assert resolved["payout"] == 200
