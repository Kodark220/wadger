import os
import sys
import json
import requests
import asyncio
from typing import Optional

# ensure local package imports work when run from workspace root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prediction_wager import verifier


GENLAYER_RPC_URL = os.getenv('GENLAYER_RPC_URL')
GENLAYER_API_KEY = os.getenv('GENLAYER_API_KEY')
GENLAYER_RPC_METHOD = os.getenv('GENLAYER_RPC_METHOD', 'gen_call')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')


def send_genlayer_rpc(method: str, params: dict) -> dict:
    if not GENLAYER_RPC_URL:
        raise RuntimeError('GENLAYER_RPC_URL not configured')
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    headers = {"Content-Type": "application/json"}
    if GENLAYER_API_KEY:
        headers["Authorization"] = f"Bearer {GENLAYER_API_KEY}"
    r = requests.post(GENLAYER_RPC_URL, json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def call_contract_function(contract: str, fn_name: str, args: list):
    # Build a params dict — may need adapting to your GenLayer node's expected shape
    params = {"contract": contract, "method": fn_name, "args": args}
    return send_genlayer_rpc(GENLAYER_RPC_METHOD, params)


def aggregate_votes(prediction: str, verification_criteria: str, deadline, validators: int = 5):
    votes = {"YES": 0, "NO": 0}
    confidences = []
    evidences = []
    for _ in range(validators):
        # run local verifier (best-effort)
        try:
            v = asyncio.get_event_loop().run_until_complete(
                verifier.verify_prediction_logic(prediction=prediction, verification_criteria=verification_criteria, deadline=deadline, validators=1)
            )
        except Exception:
            v = {"outcome": "NO", "confidence": 0.5, "evidence": "verifier-failed"}
        outcome = v.get("outcome", "NO")
        votes[outcome] = votes.get(outcome, 0) + 1
        confidences.append(float(v.get("confidence", 0.0)))
        evidences.append(v.get("evidence", ""))

    outcome = "YES" if votes["YES"] > votes["NO"] else "NO"
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    evidence = evidences[0] if evidences else ""
    return {
        "outcome": outcome,
        "confidence": avg_conf,
        "evidence": evidence,
        "validators_used": validators,
    }


def aggregate_and_submit(wager_id: str, contract_address: Optional[str] = None, validators: int = 5, appeal: bool = False, current_date: Optional[str] = None):
    contract = contract_address or CONTRACT_ADDRESS
    if not contract:
        raise RuntimeError('CONTRACT_ADDRESS not provided (env CONTRACT_ADDRESS or pass contract_address)')

    # Fetch wager state to obtain prediction and criteria
    try:
        res = call_contract_function(contract, 'get_wager', [wager_id])
        # try common shapes
        data = res.get('result') or res.get('data') or res
        wager = data
        if isinstance(wager, dict) and 'id' in wager:
            prediction = wager.get('prediction')
            verification_criteria = wager.get('verification_criteria')
            deadline = __import__('datetime').datetime.fromisoformat(wager.get('deadline'))
        else:
            raise RuntimeError('Unexpected get_wager response')
    except Exception as e:
        raise RuntimeError(f'Failed to fetch wager from contract: {e}')

    verification = aggregate_votes(prediction, verification_criteria, deadline, validators=validators)
    # Use appeal path if requested
    fn = 'submit_verification'
    if appeal:
        fn = 'submit_appeal'

    # set is_final true for appeals or when validators meet a high quorum
    if appeal:
        verification['is_final'] = True

    # submit to GenLayer contract
    try:
        rpc_res = call_contract_function(contract, fn, [wager_id, verification, current_date])
        return {'rpc_result': rpc_res, 'verification': verification}
    except Exception as e:
        raise RuntimeError(f'Failed to submit verification to contract: {e}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--wager', required=True)
    parser.add_argument('--contract')
    parser.add_argument('--validators', type=int, default=5)
    parser.add_argument('--appeal', action='store_true')
    parser.add_argument('--date')
    args = parser.parse_args()
    out = aggregate_and_submit(args.wager, contract_address=args.contract, validators=args.validators, appeal=args.appeal, current_date=args.date)
    print(json.dumps(out, indent=2))
