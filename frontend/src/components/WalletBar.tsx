"use client";
import React from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";

export default function WalletBar() {
  const { address, isConnected } = useAccount();
  const { connect, connectors, isLoading } = useConnect();
  const { disconnect } = useDisconnect();

  return (
    <div className="wallet">
      {isConnected ? (
        <>
          <div className="wallet-addr">
            {address?.slice(0, 6)}...{address?.slice(-4)}
          </div>
          <button className="btn ghost" onClick={() => disconnect()}>
            Disconnect
          </button>
        </>
      ) : (
        <>
          <div className="wallet-addr muted">Not connected</div>
          <button
            className="btn"
            onClick={() => connect({ connector: connectors[0] })}
            disabled={isLoading}
          >
            {isLoading ? "Connecting..." : "Connect Wallet"}
          </button>
        </>
      )}
    </div>
  );
}
