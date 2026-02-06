"use client";
import "../styles/globals.css";
import type { AppProps } from "next/app";
import { WagmiConfig, createConfig, http } from "wagmi";
import { injected } from "wagmi/connectors";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export default function App({ Component, pageProps }: AppProps) {
  const RPC_URL = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "https://studio.genlayer.com/api";
  const CHAIN_ID = Number(process.env.NEXT_PUBLIC_CHAIN_ID || 61999, 10);
  const queryClient = new QueryClient();

  const config = createConfig({
    chains: [
      {
        id: CHAIN_ID,
        name: "GenLayer Studio",
        network: "studionet",
        nativeCurrency: { name: "GL", symbol: "GL", decimals: 18 },
        rpcUrls: {
          default: { http: [RPC_URL] },
          public: { http: [RPC_URL] },
        },
      },
    ],
    connectors: [injected()],
    transports: {
      [CHAIN_ID]: http(RPC_URL),
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <WagmiConfig config={config}>
        <Component {...pageProps} />
      </WagmiConfig>
    </QueryClientProvider>
  );
}
