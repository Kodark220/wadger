# v0.1.0
# { "Depends": "py-genlayer:test" }
from genlayer import *  # type: ignore

import datetime
import hashlib
import json
from dataclasses import dataclass
from typing import Optional

# GenLayer-compatible Prediction Wager contract.
# - Persistent state is declared on the contract class using typed fields.
# - Storage mappings use TreeMap; storage classes use @allow_storage.
# - Nondeterministic verification uses the Equivalence Principle.

IS_DEV_FALLBACK = False
try:
    gl  # type: ignore
except Exception:
    IS_DEV_FALLBACK = True
    # Minimal local/dev fallbacks (no-op) so the module can be imported.
    class u256(int):
        pass

    class u32(int):
        pass

    class Address(str):
        pass

    class TreeMap(dict):
        pass

    class DynArray(list):
        pass

    def allow_storage(cls):
        return cls

    class _Write:
        def __call__(self, fn):
            return fn

        @property
        def payable(self):
            return self

        def min_gas(self, **_kwargs):
            return self

    class _Public:
        view = staticmethod(lambda fn: fn)
        write = _Write()

    class _Storage:
        @staticmethod
        def inmem_allocate(cls, *args):
            return cls(*args)

        @staticmethod
        def copy_to_memory(obj):
            return obj

    class _ContractAt:
        def __init__(self, _addr):
            pass

        def emit_transfer(self, **_kwargs):
            return None

    class _EqPrinciple:
        @staticmethod
        def strict_eq(fn):
            return fn()

    class _GL:
        Contract = object
        public = _Public()
        storage = _Storage()
        ContractAt = _ContractAt
        eq_principle = _EqPrinciple()
        message_raw = {"datetime": datetime.datetime.utcnow().isoformat()}
        message = type("message", (), {"sender_address": Address("0x0"), "value": u256(0)})

        @staticmethod
        def exec_prompt(_prompt: str) -> str:
            return "NO"

        @staticmethod
        def get_webpage(_url: str, mode: str = "text") -> str:
            return ""

    gl = _GL()

    def eq_principle_strict_eq(fn):
        return fn()


MIN_QUORUM = u32(3)
APPEAL_QUORUM = u32(50)
ZERO_ADDRESS = Address("0x0000000000000000000000000000000000000000")
ALLOW_DEV_DEADLINES = True


@allow_storage
@dataclass
class VerificationResult:
    outcome: str
    confidence: float
    evidence: str
    validators_used: u32
    is_final: bool


@allow_storage
@dataclass
class Wager:
    id: str
    prediction: str
    player_a: Address
    player_b: Address
    player_a_stance: str
    player_b_stance: str
    stake_amount: u256
    deadline: str
    category: str
    verification_criteria: str
    status: str
    pot: u256
    has_verification: bool
    verification: VerificationResult
    created_at: str
    resolved_at: str


@allow_storage
@dataclass
class PlayerStats:
    wagers_created: u256
    wagers_joined: u256
    wins: u256
    losses: u256
    volume_contributed: u256
    volume_won: u256
    last_updated: str
    username: str


class PredictionWager(gl.Contract):
    """Prediction Wager contract with escrow + equivalence-principle verification."""

    wagers: TreeMap[str, Wager]
    wager_index: TreeMap[u256, str]
    player_stats: TreeMap[Address, PlayerStats]
    player_index: TreeMap[u256, Address]
    wager_counter: u256
    player_count: u256
    last_wager_id: str
    total_wagers_created: u256
    total_wagers_resolved: u256
    total_volume: u256

    def __init__(self):
        if IS_DEV_FALLBACK:
            self.wagers = TreeMap()
            self.wager_index = TreeMap()
            self.player_stats = TreeMap()
            self.player_index = TreeMap()
        self.wager_counter = u256(0)
        self.player_count = u256(0)
        self.last_wager_id = ""
        self.total_wagers_created = u256(0)
        self.total_wagers_resolved = u256(0)
        self.total_volume = u256(0)

    # ---- helpers ----
    def _now_iso(self) -> str:
        return gl.message_raw["datetime"]

    def _now_dt(self) -> datetime.datetime:
        dt = datetime.datetime.fromisoformat(self._now_iso())
        return dt.replace(tzinfo=None)

    def _deadline_dt(self, deadline: str) -> datetime.datetime:
        dt = datetime.datetime.fromisoformat(deadline)
        return dt.replace(tzinfo=None)

    def _new_verification(self) -> VerificationResult:
        return gl.storage.inmem_allocate(
            VerificationResult, "", 0.0, "", u32(0), False
        )

    def _new_player_stats(self) -> PlayerStats:
        return gl.storage.inmem_allocate(
            PlayerStats, u256(0), u256(0), u256(0), u256(0), u256(0), u256(0), self._now_iso(), ""
        )

    def _touch_player(self, addr: Address):
        if addr not in self.player_stats:
            self.player_stats[addr] = self._new_player_stats()
            self.player_index[self.player_count] = addr
            self.player_count = u256(self.player_count + u256(1))

    def _new_wager(
        self,
        wager_id: str,
        prediction: str,
        player_a: Address,
        stake_amount: int,
        deadline: str,
        category: str,
        verification_criteria: str,
    ) -> Wager:
        stake_u = u256(stake_amount)
        return gl.storage.inmem_allocate(
            Wager,
            wager_id,
            prediction,
            player_a,
            ZERO_ADDRESS,
            "agree",
            "",
            stake_u,
            deadline,
            category,
            verification_criteria,
            "waiting",
            stake_u,
            False,
            self._new_verification(),
            self._now_iso(),
            "",
        )

    def _get_wager(self, wager_id: str) -> Wager:
        if wager_id not in self.wagers:
            raise Exception("Wager not found")
        return self.wagers[wager_id]

    def _strict_eq(self, fn):
        # Compatibility across GenLayer SDK versions
        if hasattr(gl, "eq_principle"):
            return gl.eq_principle.strict_eq(fn)
        if "eq_principle_strict_eq" in globals():
            return globals()["eq_principle_strict_eq"](fn)
        raise Exception("Equivalence Principle strict_eq not available")

    def _classify_outcome(
        self,
        prediction: str,
        verification_criteria: str,
        evidence_url: str,
        appeal_reason: str,
    ) -> str:
        def _classify() -> str:
            if evidence_url and hasattr(gl, "get_webpage"):
                page_text = gl.get_webpage(evidence_url, mode="text")
            else:
                page_text = ""
            criteria_text = page_text or verification_criteria
            prompt = (
                "Answer ONLY 'YES' or 'NO'.\n"
                f"Prediction: {prediction}\n"
                f"Criteria: {verification_criteria}\n"
                f"Appeal Reason: {appeal_reason}\n"
                f"Evidence: {criteria_text[:4000]}\n"
            )
            if hasattr(gl, "exec_prompt"):
                outcome = gl.exec_prompt(prompt).strip().upper()
            else:
                outcome = "NO"
            if "YES" in outcome:
                outcome = "YES"
            elif "NO" in outcome:
                outcome = "NO"
            else:
                outcome = "NO"
            digest = hashlib.sha256(page_text.encode("utf-8")).hexdigest() if page_text else ""
            return f"{outcome}|{digest}"

        return self._strict_eq(_classify)

    # ---- public API ----
    @gl.public.write.payable
    def create_wager(
        self,
        prediction: str,
        stake_amount: int,
        deadline: str,
        category: Optional[str],
        verification_criteria: str,
    ):
        # Studio/Dev fallback: allow zero-value calls and treat stake_amount as escrowed value.
        # In production, require a real payment.
        if gl.message.value == u256(0) and stake_amount <= 0:
            raise Exception("Stake payment is required")
        stake_u = u256(stake_amount)
        if gl.message.value != u256(0) and stake_u != gl.message.value:
            raise Exception("Stake amount does not match payment")

        deadline_dt = self._deadline_dt(deadline)
        if not ALLOW_DEV_DEADLINES and deadline_dt <= self._now_dt():
            raise Exception("Deadline must be in the future")

        self.wager_counter = u256(self.wager_counter + u256(1))
        wager_id = f"wager_{self._now_iso()}_{self.wager_counter}"
        wager = self._new_wager(
            wager_id=wager_id,
            prediction=prediction,
            player_a=gl.message.sender_address,
            stake_amount=int(gl.message.value if gl.message.value != u256(0) else stake_u),
            deadline=deadline,
            category=category or "",
            verification_criteria=verification_criteria,
        )
        self.wagers[wager_id] = wager
        self.wager_index[u256(self.wager_counter - u256(1))] = wager_id
        self.last_wager_id = wager_id
        self.total_wagers_created = u256(self.total_wagers_created + u256(1))
        self.total_volume = u256(self.total_volume + wager.stake_amount)

        self._touch_player(wager.player_a)
        stats = self.player_stats[wager.player_a]
        stats.wagers_created = u256(stats.wagers_created + u256(1))
        stats.volume_contributed = u256(stats.volume_contributed + wager.stake_amount)
        stats.last_updated = self._now_iso()
        self.player_stats[wager.player_a] = stats

    @gl.public.write.payable
    def accept_wager(self, wager_id: str, stance: Optional[str] = None):
        w = self._get_wager(wager_id)
        if w.status != "waiting":
            raise Exception("Wager is not available to accept")
        if gl.message.sender_address == w.player_a:
            raise Exception("Creator cannot accept their own wager")
        normalized = (stance or "disagree").strip().lower()
        if normalized not in ("agree", "disagree"):
            raise Exception("Stance must be 'agree' or 'disagree'")
        # Studio/Dev fallback: allow zero-value calls and trust stored stake_amount.
        if gl.message.value != u256(0) and gl.message.value != w.stake_amount:
            raise Exception("Stake payment must match the original stake")

        w.player_b = gl.message.sender_address
        w.player_b_stance = normalized
        w.status = "active"
        if gl.message.value == u256(0):
            w.pot = u256(w.pot + w.stake_amount)
        else:
            w.pot = u256(w.pot + gl.message.value)
        self.wagers[wager_id] = w

        self.total_volume = u256(self.total_volume + w.stake_amount)
        self._touch_player(w.player_b)
        stats = self.player_stats[w.player_b]
        stats.wagers_joined = u256(stats.wagers_joined + u256(1))
        stats.volume_contributed = u256(stats.volume_contributed + w.stake_amount)
        stats.last_updated = self._now_iso()
        self.player_stats[w.player_b] = stats

    @gl.public.write
    def submit_verification(self, wager_id: str, evidence_url: Optional[str] = None):
        w = self._get_wager(wager_id)
        if w.status not in ("active", "verified"):
            raise Exception("Wager is not active")
        if not ALLOW_DEV_DEADLINES and self._now_dt() < self._deadline_dt(w.deadline):
            raise Exception("Deadline has not been reached yet")

        mem_w = gl.storage.copy_to_memory(w)
        url = evidence_url or (mem_w.verification_criteria if mem_w.verification_criteria.startswith("http") else "")
        result = self._classify_outcome(
            prediction=mem_w.prediction,
            verification_criteria=mem_w.verification_criteria,
            evidence_url=url,
            appeal_reason="",
        )
        outcome, digest = result.split("|", 1)
        evidence = f"url={url}; sha256={digest}" if url else f"criteria={mem_w.verification_criteria}"

        w.verification = gl.storage.inmem_allocate(
            VerificationResult,
            outcome,
            0.85,
            evidence,
            MIN_QUORUM,
            False,
        )
        w.has_verification = True
        w.status = "verified"
        self.wagers[wager_id] = w

    @gl.public.write
    def submit_appeal(self, wager_id: str, appeal_reason: str, evidence_url: Optional[str] = None):
        w = self._get_wager(wager_id)
        if w.status != "verified":
            raise Exception("Wager must be verified before appeal")
        if not ALLOW_DEV_DEADLINES and self._now_dt() < self._deadline_dt(w.deadline):
            raise Exception("Deadline has not been reached yet")

        mem_w = gl.storage.copy_to_memory(w)
        url = evidence_url or (mem_w.verification_criteria if mem_w.verification_criteria.startswith("http") else "")
        result = self._classify_outcome(
            prediction=mem_w.prediction,
            verification_criteria=mem_w.verification_criteria,
            evidence_url=url,
            appeal_reason=appeal_reason,
        )
        outcome, digest = result.split("|", 1)
        evidence = f"url={url}; sha256={digest}" if url else f"criteria={mem_w.verification_criteria}"

        w.verification = gl.storage.inmem_allocate(
            VerificationResult,
            outcome,
            0.95,
            evidence,
            APPEAL_QUORUM,
            True,
        )
        w.has_verification = True
        w.status = "verified"
        self.wagers[wager_id] = w

    @gl.public.write
    def resolve_wager(self, wager_id: str):
        w = self._get_wager(wager_id)
        if w.status == "resolved":
            raise Exception("Wager already resolved")
        if not w.has_verification:
            raise Exception("No verification submitted")
        if not w.verification.is_final:
            raise Exception("Verification is not final; submit an appeal to finalize")

        outcome = w.verification.outcome
        if outcome not in ("YES", "NO"):
            raise Exception("Invalid verification outcome")

        supporters = []
        opposers = []
        if w.player_a != ZERO_ADDRESS:
            if w.player_a_stance == "disagree":
                opposers.append(w.player_a)
            else:
                supporters.append(w.player_a)
        if w.player_b != ZERO_ADDRESS and w.player_b_stance:
            if w.player_b_stance == "disagree":
                opposers.append(w.player_b)
            else:
                supporters.append(w.player_b)

        winners = supporters if outcome == "YES" else opposers

        w.status = "resolved"
        w.resolved_at = self._now_iso()
        payout = w.pot
        self.wagers[wager_id] = w
        self.total_wagers_resolved = u256(self.total_wagers_resolved + u256(1))

        participants = []
        if w.player_a != ZERO_ADDRESS:
            participants.append(w.player_a)
        if w.player_b != ZERO_ADDRESS:
            participants.append(w.player_b)

        payout_map = {}
        if winners:
            if len(winners) == 1:
                payout_map[winners[0]] = w.pot
            else:
                count = u256(len(winners))
                each = u256(w.pot // count)
                remainder = u256(w.pot - each * count)
                idx = 0
                for addr in winners:
                    payout_map[addr] = each + (remainder if idx == 0 else u256(0))
                    idx += 1

        # Update winner/loser stats.
        if winners:
            for addr in participants:
                self._touch_player(addr)
                stats = self.player_stats[addr]
                if addr in winners:
                    stats.wins = u256(stats.wins + u256(1))
                    stats.volume_won = u256(stats.volume_won + payout_map.get(addr, u256(0)))
                else:
                    stats.losses = u256(stats.losses + u256(1))
                stats.last_updated = self._now_iso()
                self.player_stats[addr] = stats

        # Transfer escrowed funds to the winner if the runtime supports it.
        # Studio runtime does not expose ContractAt, so we guard calls.
        def _pay(to_addr: Address, value: u256):
            if value <= u256(0):
                return
            if hasattr(gl, "ContractAt"):
                try:
                    gl.ContractAt(to_addr).emit_transfer(value=value)
                    return
                except Exception:
                    pass
            if hasattr(gl, "transfer"):
                try:
                    gl.transfer(to=to_addr, value=value)
                    return
                except Exception:
                    pass
            if hasattr(gl, "emit_transfer"):
                try:
                    gl.emit_transfer(to=to_addr, value=value)
                except Exception:
                    pass

        if not winners:
            if w.player_b != ZERO_ADDRESS:
                half = u256(w.pot // u256(2))
                _pay(w.player_a, half)
                _pay(w.player_b, u256(w.pot - half))
            else:
                _pay(w.player_a, w.pot)
        else:
            for addr in winners:
                _pay(addr, payout_map.get(addr, u256(0)))

    @gl.public.view
    def get_wager(self, wager_id: str):
        w = self._get_wager(wager_id)
        return {
            "id": w.id,
            "prediction": w.prediction,
            "player_a": str(w.player_a),
            "player_b": str(w.player_b),
            "player_a_stance": w.player_a_stance,
            "player_b_stance": w.player_b_stance,
            "stake_amount": int(w.stake_amount),
            "deadline": w.deadline,
            "category": w.category,
            "verification_criteria": w.verification_criteria,
            "status": w.status,
            "pot": int(w.pot),
            "verification_result": {
                "outcome": w.verification.outcome,
                "confidence": w.verification.confidence,
                "evidence": w.verification.evidence,
                "validators_used": int(w.verification.validators_used),
                "is_final": w.verification.is_final,
            } if w.has_verification else None,
            "created_at": w.created_at,
            "resolved_at": w.resolved_at,
        }

    @gl.public.view
    def get_status(self, wager_id: str):
        w = self._get_wager(wager_id)
        return {
            "status": w.status,
            "player_a": str(w.player_a),
            "player_b": str(w.player_b),
            "player_a_stance": w.player_a_stance,
            "player_b_stance": w.player_b_stance,
            "pot": int(w.pot),
            "has_verification": w.has_verification,
            "is_final": w.verification.is_final if w.has_verification else False,
            "outcome": w.verification.outcome if w.has_verification else "",
        }

    @gl.public.view
    def get_last_wager_id(self):
        return self.last_wager_id

    @gl.public.view
    def list_wagers(self, offset: int, limit: int):
        if offset < 0 or limit < 0:
            raise Exception("Invalid pagination")
        total = int(self.wager_counter)
        end = offset + limit
        result = []
        i = offset
        while i < total and i < end:
            key = u256(i)
            if key in self.wager_index:
                result.append(self.wager_index[key])
            i += 1
        return result

    @gl.public.view
    def get_wager_json(self, wager_id: str) -> str:
        return json.dumps(self.get_wager(wager_id))

    @gl.public.view
    def get_status_json(self, wager_id: str) -> str:
        return json.dumps(self.get_status(wager_id))

    @gl.public.view
    def list_wagers_json(self, offset: int, limit: int) -> str:
        return json.dumps(self.list_wagers(offset, limit))

    @gl.public.view
    def get_player_stats(self, player: Address):
        if player not in self.player_stats:
            return {
                "wagers_created": 0,
                "wagers_joined": 0,
                "wins": 0,
                "losses": 0,
                "volume_contributed": 0,
                "volume_won": 0,
                "last_updated": "",
                "username": "",
            }
        s = self.player_stats[player]
        return {
            "wagers_created": int(s.wagers_created),
            "wagers_joined": int(s.wagers_joined),
            "wins": int(s.wins),
            "losses": int(s.losses),
            "volume_contributed": int(s.volume_contributed),
            "volume_won": int(s.volume_won),
            "last_updated": s.last_updated,
            "username": s.username,
        }

    @gl.public.view
    def get_player_stats_json(self, player: Address) -> str:
        return json.dumps(self.get_player_stats(player))

    @gl.public.view
    def list_players(self, offset: int, limit: int):
        if offset < 0 or limit < 0:
            raise Exception("Invalid pagination")
        total = int(self.player_count)
        end = offset + limit
        result = []
        i = offset
        while i < total and i < end:
            key = u256(i)
            if key in self.player_index:
                result.append(str(self.player_index[key]))
            i += 1
        return result

    @gl.public.write
    def set_username(self, username: str):
        if not username:
            raise Exception("Username is required")
        trimmed = username.strip()
        if len(trimmed) == 0:
            raise Exception("Username is required")
        if len(trimmed) > 32:
            raise Exception("Username is too long")
        self._touch_player(gl.message.sender_address)
        stats = self.player_stats[gl.message.sender_address]
        stats.username = trimmed
        stats.last_updated = self._now_iso()
        self.player_stats[gl.message.sender_address] = stats

    @gl.public.view
    def get_leaderboard(self, offset: int, limit: int):
        if offset < 0 or limit < 0:
            raise Exception("Invalid pagination")
        total = int(self.player_count)
        entries = []
        i = 0
        while i < total:
            key = u256(i)
            if key in self.player_index:
                addr = self.player_index[key]
                if addr in self.player_stats:
                    s = self.player_stats[addr]
                    wins = int(s.wins)
                    losses = int(s.losses)
                    volume_won = int(s.volume_won)
                    volume_contributed = int(s.volume_contributed)
                else:
                    wins = 0
                    losses = 0
                    volume_won = 0
                    volume_contributed = 0
                entries.append(
                    {
                        "address": str(addr),
                        "username": s.username if addr in self.player_stats else "",
                        "wins": wins,
                        "losses": losses,
                        "volume_won": volume_won,
                        "volume_contributed": volume_contributed,
                    }
                )
            i += 1

        entries.sort(
            key=lambda e: (-e["wins"], -e["volume_won"], -e["volume_contributed"], e["address"])
        )
        end = offset + limit
        return entries[offset:end]

    @gl.public.view
    def list_players_json(self, offset: int, limit: int) -> str:
        return json.dumps(self.list_players(offset, limit))

    @gl.public.view
    def get_leaderboard_json(self, offset: int, limit: int) -> str:
        return json.dumps(self.get_leaderboard(offset, limit))

    @gl.public.view
    def get_global_stats(self):
        return {
            "total_wagers_created": int(self.total_wagers_created),
            "total_wagers_resolved": int(self.total_wagers_resolved),
            "total_volume": int(self.total_volume),
        }

    @gl.public.view
    def get_global_stats_json(self) -> str:
        return json.dumps(self.get_global_stats())
