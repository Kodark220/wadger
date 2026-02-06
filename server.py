from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
import asyncio
import os
import subprocess
import time
from typing import Dict

from eth_account import Account
from eth_account.messages import encode_defunct

from prediction_wager.contract import PredictionWagerContract

app = Flask(__name__)
# Allow browser calls to the relayer endpoints.
CORS(app, resources={r"/relay/*": {"origins": "*"}, r"/health": {"origins": "*"}})

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify({"error": e.description}), e.code
    return jsonify({"error": str(e)}), 500
contract = PredictionWagerContract()
nonces: Dict[str, str] = {}


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

def _relayer_env():
    env = os.environ.copy()
    env["GENLAYER_RPC_URL"] = os.getenv("GENLAYER_RPC_URL", "https://studio.genlayer.com/api")
    env["CONTRACT_ADDRESS"] = os.getenv("CONTRACT_ADDRESS", "")
    env["GENLAYER_PRIVATE_KEY"] = os.getenv("RELAYER_PRIVATE_KEY", "")
    return env

def _require_relayer_env():
    if not os.getenv("CONTRACT_ADDRESS"):
        raise Exception("CONTRACT_ADDRESS env not set")
    if not os.getenv("RELAYER_PRIVATE_KEY"):
        raise Exception("RELAYER_PRIVATE_KEY env not set")

def _message(action: str, address: str, nonce: str, ts: int) -> str:
    return f"GenLayer Wager Relayer\nAction: {action}\nAddress: {address}\nNonce: {nonce}\nTimestamp: {ts}"

def _verify_signature(data, action: str):
    require_sig = os.getenv("RELAYER_REQUIRE_SIGNATURE", "1") == "1"
    if not require_sig:
        return

    address = data.get("address", "")
    signature = data.get("signature", "")
    nonce = data.get("nonce", "")
    ts = int(data.get("timestamp", 0))

    if not address or not signature or not nonce or not ts:
        raise Exception("Missing signature fields")

    # basic replay protection
    if nonces.get(address) != nonce:
        raise Exception("Invalid nonce")
    if abs(int(time.time()) - ts) > 300:
        raise Exception("Signature expired")

    msg = _message(action, address, nonce, ts)
    recovered = Account.recover_message(encode_defunct(text=msg), signature=signature)
    if recovered.lower() != address.lower():
        raise Exception("Invalid signature")

    # consume nonce
    nonces.pop(address, None)

def _run_node(cmd: str, args: list):
    _require_relayer_env()
    proc = subprocess.run(
        ["node", "tools/genlayer_interact.mjs", cmd, *args],
        capture_output=True,
        text=True,
        env=_relayer_env(),
        check=False,
    )
    if proc.returncode != 0:
        raise Exception(proc.stderr.strip() or proc.stdout.strip() or "Relayer failed")
    return proc.stdout.strip()


@app.route('/relay/nonce', methods=['POST'])
def relay_nonce():
    data = request.json or {}
    address = data.get("address", "")
    if not address:
        return jsonify({"error": "address required"}), 400
    nonce = os.urandom(8).hex()
    nonces[address] = nonce
    return jsonify({"nonce": nonce, "timestamp": int(time.time())})

@app.route('/health', methods=['GET', 'HEAD'])
def health():
    return jsonify({"ok": True}), 200


@app.route('/create', methods=['POST'])
def create():
    data = request.json
    res = run_async(contract.create_wager(
        prediction=data['prediction'],
        player_a=data['player_a'],
        stake_amount=float(data.get('stake_amount', 0)),
        deadline=data['deadline'],
        category=data.get('category'),
        verification_criteria=data.get('verification_criteria', ''),
    ))
    return jsonify(res)


@app.route('/accept', methods=['POST'])
def accept():
    data = request.json
    res = run_async(contract.accept_wager(wager_id=data['wager_id'], player_b=data['player_b']))
    return jsonify(res)


@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    res = run_async(contract.verify_prediction(
        wager_id=data['wager_id'],
        current_date=data.get('current_date'),
        mock_outcome=data.get('mock_outcome'),
    ))
    return jsonify(res)


@app.route('/appeal', methods=['POST'])
def appeal():
    data = request.json
    res = run_async(contract.appeal_verification(
        wager_id=data['wager_id'],
        appealing_player=data['appealing_player'],
        appeal_reason=data.get('appeal_reason', ''),
        current_date=data.get('current_date'),
        mock_outcome=data.get('mock_outcome'),
    ))
    return jsonify(res)


@app.route('/resolve', methods=['POST'])
def resolve():
    data = request.json
    res = run_async(contract.resolve_wager(
        wager_id=data['wager_id'],
        outcome=data['outcome'],
        winner=data['winner'],
        verification_data=data.get('verification_data', {}),
    ))
    return jsonify(res)

@app.route('/relay/create', methods=['POST'])
def relay_create():
    data = request.json or {}
    _verify_signature(data, "create")
    args = [
        "--prediction", data["prediction"],
        "--deadline", data["deadline"],
        "--category", data.get("category", ""),
        "--criteria", data["verification_criteria"],
        "--stake", str(data.get("stake_amount", 0)),
    ]
    out = _run_node("create", args)
    return jsonify({"result": out})

@app.route('/relay/accept', methods=['POST'])
def relay_accept():
    data = request.json or {}
    _verify_signature(data, "accept")
    args = ["--wager", data["wager_id"], "--stake", str(data.get("stake_amount", 0))]
    out = _run_node("accept", args)
    return jsonify({"result": out})

@app.route('/relay/verify', methods=['POST'])
def relay_verify():
    data = request.json or {}
    _verify_signature(data, "verify")
    args = ["--wager", data["wager_id"], "--evidence-url", data.get("evidence_url", "")]
    out = _run_node("verify", args)
    return jsonify({"result": out})

@app.route('/relay/appeal', methods=['POST'])
def relay_appeal():
    data = request.json or {}
    _verify_signature(data, "appeal")
    args = [
        "--wager", data["wager_id"],
        "--reason", data.get("appeal_reason", ""),
        "--evidence-url", data.get("evidence_url", ""),
    ]
    out = _run_node("appeal", args)
    return jsonify({"result": out})

@app.route('/relay/resolve', methods=['POST'])
def relay_resolve():
    data = request.json or {}
    _verify_signature(data, "resolve")
    args = ["--wager", data["wager_id"]]
    out = _run_node("resolve", args)
    return jsonify({"result": out})


@app.route('/aggregate_and_submit', methods=['POST'])
def aggregate_and_submit_endpoint():
    """Aggregate validator votes (off-chain) and submit verification payload
    to the deployed contract via GenLayer RPC. Expects JSON:
      {"wager_id": "wager_123", "validators": 5, "appeal": false, "contract": "0x...", "current_date": "..."}
    Requires environment variables: `GENLAYER_RPC_URL` and `CONTRACT_ADDRESS` or pass `contract` in body.
    """
    data = request.json
    wager_id = data['wager_id']
    validators_count = int(data.get('validators', 5))
    appeal = bool(data.get('appeal', False))
    contract_addr = data.get('contract')
    current_date = data.get('current_date')

    # lazy import of aggregator to avoid heavy deps at server startup
    from tools.aggregator import aggregate_and_submit

    try:
        res = aggregate_and_submit(wager_id=wager_id, contract_address=contract_addr, validators=validators_count, appeal=appeal, current_date=current_date)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
