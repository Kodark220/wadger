import asyncio
import dataclasses
import datetime
import uuid
from typing import Dict, Optional


@dataclasses.dataclass
class Wager:
    id: str
    prediction: str
    player_a: str
    player_b: Optional[str]
    player_a_stance: str
    player_b_stance: str
    stake_amount: float
    deadline: datetime.datetime
    category: Optional[str]
    verification_criteria: str
    status: str = "waiting"
    pot: float = 0.0
    verification_result: Optional[dict] = None


class PredictionWagerContract:
    """Lightweight, local implementation of the Prediction Wager game.

    This is a runnable, easily testable scaffold that mirrors the API you
    described. It intentionally keeps validator logic pluggable (mockable)
    so you can later replace the verifier with real GenLayer validator calls.
    """

    def __init__(self):
        self.wagers: Dict[str, Wager] = {}

    async def create_wager(self, *, prediction: str, player_a: str, stake_amount: float,
                           deadline: str, category: Optional[str], verification_criteria: str) -> dict:
        wid = "wager_" + uuid.uuid4().hex[:8]
        deadline_dt = datetime.datetime.fromisoformat(deadline)
        w = Wager(
            id=wid,
            prediction=prediction,
            player_a=player_a,
            player_b=None,
            player_a_stance="agree",
            player_b_stance="",
            stake_amount=stake_amount,
            deadline=deadline_dt,
            category=category,
            verification_criteria=verification_criteria,
        )
        self.wagers[wid] = w
        return {"wager_id": wid, "waiting_for_opponent": True}

    async def accept_wager(self, *, wager_id: str, player_b: str, stance: Optional[str] = None) -> dict:
        w = self._get_wager(wager_id)
        if w.status != "waiting":
            raise ValueError("Wager is not available to accept")
        normalized = (stance or "disagree").strip().lower()
        if normalized not in ("agree", "disagree"):
            raise ValueError("Stance must be 'agree' or 'disagree'")
        w.player_b = player_b
        w.player_b_stance = normalized
        w.status = "active"
        w.pot = w.stake_amount * 2
        return {"total_pot": w.pot, "status": w.status}

    async def verify_prediction(self, *, wager_id: str, current_date: Optional[str] = None,
                                validators: int = 5, mock_outcome: Optional[str] = None,
                                mock_evidence: Optional[str] = None) -> dict:
        """Perform verification. For now this supports a `mock_outcome` override
        which is useful for deterministic tests and demos.
        """
        w = self._get_wager(wager_id)
        now = datetime.datetime.fromisoformat(current_date) if current_date else datetime.datetime.utcnow()
        if now < w.deadline:
            raise ValueError("Deadline has not been reached yet")

        # If test/demo supplies a mock outcome, use it (deterministic).
        if mock_outcome is not None:
            outcome = mock_outcome  # expected values: 'YES' or 'NO'
            confidence = 0.95
            evidence = mock_evidence or f"Mock evidence for: {w.verification_criteria}"
        else:
            # Use the local verifier module which contains simple web/LLM stubs.
            try:
                from prediction_wager import verifier

                vres = await verifier.verify_prediction_logic(
                    prediction=w.prediction,
                    verification_criteria=w.verification_criteria,
                    deadline=w.deadline,
                    validators=validators,
                )
                outcome = vres.get("outcome", "NO")
                confidence = vres.get("confidence", 0.6)
                evidence = vres.get("evidence", "No evidence returned by verifier")
            except Exception:
                outcome = "NO"
                confidence = 0.6
                evidence = "Verifier failure — replace with GenLayer validators"

        if outcome == "YES":
            winner = w.player_a if w.player_a_stance != "disagree" else w.player_b
        else:
            winner = w.player_b if w.player_b_stance == "disagree" else w.player_a
        can_appeal = confidence < 0.8
        res = {
            "outcome": outcome,
            "winner": winner,
            "confidence": confidence,
            "evidence": evidence,
            "can_appeal": can_appeal,
            "validators_used": validators,
        }
        w.verification_result = res
        return res

    async def appeal_verification(self, *, wager_id: str, appealing_player: str,
                                  appeal_reason: str, current_date: Optional[str] = None,
                                  validators: int = 50, mock_outcome: Optional[str] = None,
                                  mock_evidence: Optional[str] = None) -> dict:
        w = self._get_wager(wager_id)
        now = datetime.datetime.fromisoformat(current_date) if current_date else datetime.datetime.utcnow()
        if now < w.deadline:
            raise ValueError("Deadline has not been reached yet")

        # Use the mock outcome if provided, otherwise default to a stronger NO with high confidence
        if mock_outcome is not None:
            outcome = mock_outcome
            confidence = 0.98
            evidence = mock_evidence or f"Mock deep-evidence for: {w.verification_criteria}"
        else:
            try:
                from prediction_wager import verifier

                vres = await verifier.appeal_verification_logic(
                    prediction=w.prediction,
                    verification_criteria=w.verification_criteria,
                    appeal_reason=appeal_reason,
                    validators=validators,
                )
                outcome = vres.get("outcome", "NO")
                confidence = vres.get("confidence", 0.9)
                evidence = vres.get("evidence", "No evidence returned by verifier (appeal)")
            except Exception:
                outcome = "NO"
                confidence = 0.9
                evidence = "Deep-check mock evidence (replace with real validator appeal flow)"

        final_winner = w.player_a if outcome == "YES" else w.player_b
        res = {
            "outcome": outcome,
            "final_winner": final_winner,
            "confidence": confidence,
            "validators_used": validators,
            "is_final": True,
            "evidence": evidence,
        }
        w.verification_result = res
        return res

    async def resolve_wager(self, *, wager_id: str, outcome: str, winner: str, verification_data: dict) -> dict:
        w = self._get_wager(wager_id)
        if w.status == "resolved":
            raise ValueError("Wager already resolved")
        w.status = "resolved"
        payout = w.pot
        # In a real GenLayer contract you'd transfer funds; here we just return the payout info.
        return {"winner": winner, "payout": payout}

    def _get_wager(self, wager_id: str) -> Wager:
        if wager_id not in self.wagers:
            raise KeyError("Wager not found")
        return self.wagers[wager_id]


# Simple demo helper for synchronous scripts
async def demo_flow():
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
    await c.accept_wager(wager_id=wid, player_b="0xBob...")
    verification = await c.verify_prediction(wager_id=wid, current_date="2027-01-01", mock_outcome="YES",
                                             mock_evidence="CoinMarketCap shows BTC at $105,432 on 2026-12-28")
    resolved = await c.resolve_wager(wager_id=wid, outcome=verification["outcome"], winner=verification["winner"], verification_data=verification)
    return created, verification, resolved


if __name__ == "__main__":
    res = asyncio.run(demo_flow())
    print(res)
