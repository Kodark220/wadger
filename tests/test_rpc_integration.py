import os
import asyncio
import pytest

from prediction_wager import verifier


@pytest.mark.skipif(not os.getenv('GENLAYER_RPC_URL'), reason='GENLAYER_RPC_URL not set')
def test_genlayer_rpc_integration():
    """Integration test that calls the GenLayer RPC via the verifier helper.

    Requires environment variables:
      - GENLAYER_RPC_URL
      - (optional) GENLAYER_API_KEY

    The test is skipped when `GENLAYER_RPC_URL` is not present so it can
    safely live in CI but only run when configured.
    """
    rpc = os.getenv('GENLAYER_RPC_URL')
    assert rpc

    prediction = "Bitcoin will reach $100,000 by December 31, 2026"
    verification_criteria = "Check coinmarketcap.com for BTC price"
    deadline = "2026-12-31T23:59:59"

    res = asyncio.run(verifier.verify_prediction_logic(
        prediction=prediction,
        verification_criteria=verification_criteria,
        deadline=__import__('datetime').datetime.fromisoformat(deadline),
        validators=5,
    ))

    # Basic assertions
    assert isinstance(res, dict)
    assert 'outcome' in res
    assert 'confidence' in res
