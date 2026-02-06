"use client";
import "../styles/globals.css";
import type { AppProps } from "next/app";
import { WagmiConfig, createConfig, configureChains } from "wagmi";
import { publicProvider } from "wagmi/providers/public";
import { jsonRpcProvider } from "wagmi/providers/jsonRpc";
import { InjectedConnector } from "@wagmi/connectors";

export default function App({ Component, pageProps }: AppProps) {
  const RPC_URL = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL;
  const { chains, publicClient } = configureChains(
    [{ id: Number(process.env.NEXT_PUBLIC_CHAIN_ID || 61999, 10), name: "GenLayer Studio" }],
    [jsonRpcProvider({ rpc: () => ({ http: RPC_URL }) }), publicProvider()]
  );

  const config = createConfig({
    autoConnect: true,
    connectors: [new InjectedConnector({ chains })],
    publicClient,
  });

  return (
    <WagmiConfig config={config}>
      <Component {...pageProps} />
    </WagmiConfig>
  );
}
