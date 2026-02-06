# Prediction Wager Game

Lightweight scaffold for a two-player prediction wager game (mockable verifier).

Quick start

1. Create a virtual environment and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run tests:

```bash
pytest -q
```

3. Run demo:

```bash
python -m prediction_wager.contract
```

Notes
- This project is a local scaffold. Replace `verify_prediction` and
  `appeal_verification` internals with actual GenLayer validator calls
  (LLM/web evidence) when integrating with the GenLayer runtime.

Deploying to GenLayer Studio / Network
-------------------------------------

1. Install the GenLayer CLI (if you haven't):

```bash
npm install -g genlayer
```

2. Choose a network (studio/local/testnet):

```bash
genlayer network
```

3. Deploy the contract (example):

```bash
genlayer deploy --contract contracts/prediction_wager.py
```

4. Manifest/metadata: `contracts/prediction_wager.manifest.json` contains
   basic metadata used by Studio and CLI deployment helpers.

Helper script
-------------

Use the deploy helper to print instructions or attempt a CLI deploy:

```bash
python deploy/deploy_genlayer.py      # prints instructions
python deploy/deploy_genlayer.py --simulate
python deploy/deploy_genlayer.py --run   # will try to run `genlayer` if installed
```

Notes on integration
- To use real GenLayer validators in `verify_prediction`, replace the
  verifier stubs in `prediction_wager/verifier.py` with calls to the
  GenLayer runtime or SDK (GenLayer Studio provides local runtime APIs).
- After deploying, you can interact with the contract via the GenLayer
  CLI, Studio UI, or by adapting `server.py` to call into the deployed
  contract via the GenLayer node API.

GenLayer RPC integration
- `prediction_wager/verifier.py` will try to call a GenLayer JSON-RPC
  endpoint if `GENLAYER_RPC_URL` is set in your environment. Example
  environment variables:

```bash
export GENLAYER_RPC_URL=https://studio.genlayer.com/rpc
export GENLAYER_API_KEY=your_api_key_here
export GENLAYER_RPC_METHOD=gen_call
```

The verifier expects the RPC to return a JSON object with an `outcome`,
`confidence`, and `evidence` fields (the helper will fall back to a
local CoinGecko-based check if the RPC call fails).

Running the integration test (StudioNet)
--------------------------------------

If you have a working StudioNet RPC, set the environment variables and run the integration test:

Windows (PowerShell):

```powershell
$env:GENLAYER_RPC_URL = 'https://your-studionet-rpc.example'
$env:GENLAYER_API_KEY = 'your_api_key'  # optional
pytest -q tests/test_rpc_integration.py
```

Linux/macOS:

```bash
export GENLAYER_RPC_URL=https://your-studionet-rpc.example
export GENLAYER_API_KEY=your_api_key  # optional
pytest -q tests/test_rpc_integration.py
```

The test will be skipped if `GENLAYER_RPC_URL` is not set.
