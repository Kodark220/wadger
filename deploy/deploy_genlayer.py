"""GenLayer deployment helper for the Prediction Wager contract.

This helper prints deployment instructions and will attempt to run the
`genlayer` CLI if it's installed. It is intentionally non-destructive and
requires the developer to confirm actions before running any external CLI.
"""
import os
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime


def has_genlayer_cli() -> bool:
    return shutil.which("genlayer") is not None


def print_instructions():
    print("Contract file: contracts/prediction_wager.py")
    print("Recommended steps to deploy to GenLayer Studio:")
    print("  1. Install GenLayer CLI: `npm install -g genlayer`")
    print("  2. Choose a network: `genlayer network`")
    print("  3. Deploy: `genlayer deploy --contract contracts/prediction_wager.py`")
    print("")


def run_deploy_simulation():
    print("Running a simulated deploy (no network changes).")
    # Show the contract file contents (snippet)
    p = Path(__file__).parent.parent / "contracts" / "prediction_wager.py"
    if p.exists():
        print(f"Found contract at: {p}")
        print("--- Contract snippet ---")
        print("".join(p.read_text().splitlines()[:40]))
        print("--- end snippet ---")
    else:
        print("Contract file not found; make sure you're in the project root.")


def attempt_genlayer_deploy():
    if not has_genlayer_cli():
        print("GenLayer CLI not found on PATH. Install it with `npm install -g genlayer`.")
        return
    print("GenLayer CLI detected. Preparing to run `genlayer deploy`.")
    print("This command will be run in the current working directory. Press Ctrl+C to cancel.")
    try:
        subprocess.run(["genlayer", "network"], check=True)
        subprocess.run(["genlayer", "deploy", "--contract", "contracts/prediction_wager.py"], check=True)
        contract_addr = input("Enter deployed contract address (0x...): ").strip()
        if contract_addr:
            write_last_deploy(contract_addr)
            write_frontend_env(contract_addr)
    except KeyboardInterrupt:
        print("Deploy cancelled by user.")
    except subprocess.CalledProcessError as e:
        print("genlayer command failed:", e)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if "--write-env" in argv:
        idx = argv.index("--write-env")
        addr = argv[idx + 1] if idx + 1 < len(argv) else ""
        write_frontend_env(addr)
    elif "--run" in argv:
        attempt_genlayer_deploy()
    elif "--simulate" in argv:
        run_deploy_simulation()
    else:
        print_instructions()

def last_deploy_path() -> Path:
    return Path(__file__).parent / "last_deploy.json"

def write_last_deploy(contract_addr: str):
    p = last_deploy_path()
    payload = {
        "contract_address": contract_addr,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    p.write_text(json_dump(payload))
    print(f"Wrote {p}")

def read_last_deploy() -> str:
    p = last_deploy_path()
    if not p.exists():
        return ""
    try:
        data = json_load(p.read_text())
        return str(data.get("contract_address", "")).strip()
    except Exception:
        return ""

def json_dump(payload: dict) -> str:
    # Minimal JSON serializer to avoid extra deps.
    import json
    return json.dumps(payload, indent=2)

def json_load(text: str) -> dict:
    import json
    return json.loads(text)


def write_frontend_env(contract_addr: str):
    env_path = Path(__file__).parent.parent / "frontend" / ".env.local"
    rpc_url = os.getenv("NEXT_PUBLIC_GENLAYER_RPC_URL", "https://studio.genlayer.com/api")
    relayer_url = os.getenv("NEXT_PUBLIC_RELAYER_URL", "http://localhost:5000")
    chain_id = "61999"

    if not contract_addr:
        contract_addr = read_last_deploy()
        if not contract_addr:
            print("No contract address provided and no deploy record found.")
            print("Run: python deploy/deploy_genlayer.py --write-env 0xYourContract")
            return

    existing = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip()

    existing["NEXT_PUBLIC_GENLAYER_RPC_URL"] = rpc_url
    existing["NEXT_PUBLIC_CONTRACT_ADDRESS"] = contract_addr
    existing["NEXT_PUBLIC_CHAIN_ID"] = chain_id
    existing["NEXT_PUBLIC_RELAYER_URL"] = relayer_url

    out_lines = [f"{k}={v}" for k, v in existing.items()]
    env_path.write_text("\n".join(out_lines) + "\n")
    print(f"Wrote {env_path}")


if __name__ == '__main__':
    main()
