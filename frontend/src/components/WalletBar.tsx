"use client";
import React, { useEffect, useState } from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";
import { injected } from "wagmi/connectors";

export default function WalletBar() {
  const [mounted, setMounted] = useState(false);
  const { address, isConnected } = useAccount();
  const { connect, isLoading } = useConnect();
  const { disconnect } = useDisconnect();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="wallet" />;
  }

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
            onClick={() => connect({ connector: injected() })}
            disabled={isLoading}
          >
            {isLoading ? "Connecting..." : "Connect Wallet"}
          </button>
        </>
      )}
    </div>
  );
}
