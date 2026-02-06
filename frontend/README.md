# Frontend (Next.js) — Prediction Wager Demo

This is a minimal Next.js frontend scaffold to interact with the Prediction Wager contract.

Environment

- Copy `.env.example` to `.env.local` and set:

```
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_CONTRACT_ADDRESS=0xYourContractAddress
NEXT_PUBLIC_CHAIN_ID=61999
```

Run locally

```bash
cd frontend
npm install
npm run dev
```

Notes

- This demo uses `genlayer-js` for reads and writes.
- For write actions, the app expects a local signer private key (dev-only).
