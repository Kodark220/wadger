import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests


GENLAYER_RPC_URL = os.getenv("GENLAYER_RPC_URL")
GENLAYER_RPC_METHOD = os.getenv("GENLAYER_RPC_METHOD", "gen_call")
GENLAYER_API_KEY = os.getenv("GENLAYER_API_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")


def rpc_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not GENLAYER_RPC_URL:
        raise RuntimeError("GENLAYER_RPC_URL not set")
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    headers = {"Content-Type": "application/json"}
    if GENLAYER_API_KEY:
        headers["Authorization"] = f"Bearer {GENLAYER_API_KEY}"
    r = requests.post(GENLAYER_RPC_URL, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def call_contract(contract: str, fn: str, args: List[Any], value: Optional[int] = None) -> Dict[str, Any]:
    def build_params(
        contract_key: str,
        method_key: str,
        args_key: str,
    ) -> Dict[str, Any]:
        p: Dict[str, Any] = {contract_key: contract, method_key: fn, args_key: args}
        if value is not None:
            p["value"] = value
        return p

    contract_keys = ["contract", "address", "contract_address"]
    method_keys = ["method", "function", "fn", "method_name", "entrypoint"]
    args_keys = ["args", "arguments", "params", "inputs"]

    # Try the most common first, then fall back across variants.
    attempts = [
        ("contract", "method", "args"),
    ]
    for ck in contract_keys:
        for mk in method_keys:
            for ak in args_keys:
                combo = (ck, mk, ak)
                if combo not in attempts:
                    attempts.append(combo)

    last_res: Dict[str, Any] = {}
    for ck, mk, ak in attempts:
        params = build_params(ck, mk, ak)
        res = rpc_call(GENLAYER_RPC_METHOD, params)
        last_res = res
        if "error" not in res:
            return res
        err = res.get("error", {})
        msg = (err.get("message") or "").lower()
        # If error is not about unexpected parameters, stop early.
        if "unexpected parameter" not in msg:
            return res

    # Fallback: try positional params (some RPCs expect arrays)
    positional_variants: List[List[Any]] = [
        [contract, fn, args],
        [contract, fn, args, value] if value is not None else [contract, fn, args],
    ]
    for params_list in positional_variants:
        payload = {"jsonrpc": "2.0", "id": 1, "method": GENLAYER_RPC_METHOD, "params": params_list}
        headers = {"Content-Type": "application/json"}
        if GENLAYER_API_KEY:
            headers["Authorization"] = f"Bearer {GENLAYER_API_KEY}"
        r = requests.post(GENLAYER_RPC_URL, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        res = r.json()
        last_res = res
        if "error" not in res:
            return res

    return last_res


def main(argv: List[str]) -> None:
    if len(argv) < 2:
        raise SystemExit(
            "Usage:\n"
            "  python tools/genlayer_interact.py create --prediction ... --stake 100 --deadline ...\n"
            "  python tools/genlayer_interact.py accept --wager ... --stake 100 --stance agree|disagree\n"
            "  python tools/genlayer_interact.py verify --wager ... --evidence-url ...\n"
            "  python tools/genlayer_interact.py appeal --wager ... --reason ... --evidence-url ...\n"
            "  python tools/genlayer_interact.py resolve --wager ...\n"
            "  python tools/genlayer_interact.py get --wager ...\n"
        )

    if not CONTRACT_ADDRESS:
        raise SystemExit("CONTRACT_ADDRESS not set")

    cmd = argv[1]
    args = argv[2:]

    def get_arg(flag: str, default: Optional[str] = None) -> Optional[str]:
        if flag in args:
            i = args.index(flag)
            if i + 1 < len(args):
                return args[i + 1]
        return default

    if cmd == "create":
        prediction = get_arg("--prediction")
        deadline = get_arg("--deadline")
        category = get_arg("--category", "")
        criteria = get_arg("--criteria")
        stake = int(get_arg("--stake", "0") or "0")
        if not prediction or not deadline or not criteria:
            raise SystemExit("Missing --prediction, --deadline, or --criteria")
        res = call_contract(
            CONTRACT_ADDRESS,
            "create_wager",
            [prediction, stake, deadline, category, criteria],
            value=stake,
        )
    elif cmd == "accept":
        wager_id = get_arg("--wager")
        stance = get_arg("--stance", "disagree")
        stake = int(get_arg("--stake", "0") or "0")
        if not wager_id:
            raise SystemExit("Missing --wager")
        res = call_contract(CONTRACT_ADDRESS, "accept_wager", [wager_id, stance], value=stake)
    elif cmd == "verify":
        wager_id = get_arg("--wager")
        evidence_url = get_arg("--evidence-url", "")
        if not wager_id:
            raise SystemExit("Missing --wager")
        res = call_contract(CONTRACT_ADDRESS, "submit_verification", [wager_id, evidence_url])
    elif cmd == "appeal":
        wager_id = get_arg("--wager")
        reason = get_arg("--reason")
        evidence_url = get_arg("--evidence-url", "")
        if not wager_id or not reason:
            raise SystemExit("Missing --wager or --reason")
        res = call_contract(CONTRACT_ADDRESS, "submit_appeal", [wager_id, reason, evidence_url])
    elif cmd == "resolve":
        wager_id = get_arg("--wager")
        if not wager_id:
            raise SystemExit("Missing --wager")
        res = call_contract(CONTRACT_ADDRESS, "resolve_wager", [wager_id])
    elif cmd == "get":
        wager_id = get_arg("--wager")
        if not wager_id:
            raise SystemExit("Missing --wager")
        res = call_contract(CONTRACT_ADDRESS, "get_wager", [wager_id])
    elif cmd == "getstatus":
        wager_id = get_arg("--wager")
        if not wager_id:
            raise SystemExit("Missing --wager")
        res = call_contract(CONTRACT_ADDRESS, "get_status", [wager_id])
    else:
        raise SystemExit(f"Unknown command: {cmd}")

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main(sys.argv)
