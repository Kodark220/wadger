import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const RPC_URL = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "";

export function normalizePrivateKey(pk: string) {
  const hex = pk.trim().startsWith("0x") ? pk.trim().slice(2) : pk.trim();
  if (!/^[0-9a-fA-F]{64}$/.test(hex)) {
    throw new Error("Private key must be 64 hex chars.");
  }
  return `0x${hex}`;
}

function getChainConfig() {
  if (!RPC_URL) throw new Error("NEXT_PUBLIC_GENLAYER_RPC_URL not set");
  return {
    chain: { ...studionet, rpcUrls: { default: { http: [RPC_URL] } } },
  };
}

export function getReadClient() {
  const config = getChainConfig();
  return createClient({ ...config });
}

export function getWriteClient(privateKey: string) {
  const config = getChainConfig();
  const account = createAccount(normalizePrivateKey(privateKey));
  return createClient({ ...config, account });
}
