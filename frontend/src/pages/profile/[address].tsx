"use client";
import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../../components/Layout";
import { getReadClient } from "../../lib/genlayerClient";
import { useToast } from "../../components/ToastProvider";
import { formatError } from "../../lib/errorFormat";
import { isHexAddress } from "../../lib/address";
import { useAccount } from "wagmi";

const CONTRACT = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";

export default function ProfilePage() {
  const router = useRouter();
  const routeAddress = useMemo(() => (router.query.address ? String(router.query.address) : ""), [router.query.address]);
  const { address: connectedAddress, isConnected } = useAccount();
  const targetAddress = routeAddress === "me" ? (connectedAddress || "") : routeAddress;

  const [wagers, setWagers] = useState<any[]>([]);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(8);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "resolved" | "waiting" | "verified">("all");
  const { pushToast } = useToast();

  async function withBusy<T>(label: string, fn: () => Promise<T>) {
    setBusy(label);
    setError(null);
    try {
      return await fn();
    } catch (e: any) {
      const msg = formatError(e);
      setError(msg);
      pushToast({ title: "Action failed", description: msg, variant: "error" });
      throw e;
    } finally {
      setBusy(null);
    }
  }

  async function loadPage(nextOffset = 0) {
    if (!CONTRACT || !targetAddress) return;
    if (!isHexAddress(targetAddress)) {
      const msg = "Invalid address. Use a 0x… Ethereum-style address.";
      setError(msg);
      pushToast({ title: "Invalid address", description: msg, variant: "error" });
      return;
    }
    await withBusy("Loading profile", async () => {
      const client = getReadClient();
      try {
        const statsResult = await client.readContract({
          address: CONTRACT,
          functionName: "get_player_stats_json",
          args: [targetAddress],
        });
        setStats(JSON.parse(statsResult as string));
      } catch (e) {
        setStats(null);
      }

      const result = await client.readContract({
        address: CONTRACT,
        functionName: "list_wagers_json",
        args: [nextOffset, limit],
      });
      const ids = JSON.parse(result as string) as string[];
      const fetched: any[] = [];
      for (const id of ids) {
        const w = await client.readContract({
          address: CONTRACT,
          functionName: "get_wager_json",
          args: [id],
        });
        const parsed = JSON.parse(w as string);
        const addr = targetAddress.toLowerCase();
        if (
          parsed.player_a?.toLowerCase() === addr ||
          parsed.player_b?.toLowerCase() === addr
        ) {
          fetched.push(parsed);
        }
      }
      setOffset(nextOffset);
      setWagers(fetched);
    });
  }

  useEffect(() => {
    if (!targetAddress) return;
    loadPage(0);
  }, [targetAddress]);

  return (
    <Layout>
      <section className="hero">
        <div>
          <div className="eyebrow">Profile</div>
          <h1>Player Dashboard</h1>
          <p className="muted">Your wager activity and stats.</p>
        </div>
        <div className="card">
          <div className="muted">Wallet status</div>
          <div className="mono">
            {isConnected ? "Connected" : "Not connected"}
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Player Stats</h2>
        <div className="codeblock">
          <pre>{stats ? JSON.stringify(stats, null, 2) : "No stats yet."}</pre>
        </div>
      </section>

      <section className="card">
        <h2>Wager History</h2>
        <div className="row">
          <button onClick={() => setStatusFilter("all")} className={statusFilter === "all" ? "primary" : ""}>All</button>
          <button onClick={() => setStatusFilter("active")} className={statusFilter === "active" ? "primary" : ""}>Active</button>
          <button onClick={() => setStatusFilter("resolved")} className={statusFilter === "resolved" ? "primary" : ""}>Resolved</button>
          <button onClick={() => setStatusFilter("waiting")} className={statusFilter === "waiting" ? "primary" : ""}>Waiting</button>
          <button onClick={() => setStatusFilter("verified")} className={statusFilter === "verified" ? "primary" : ""}>Verified</button>
        </div>
        <div className="row">
          <button onClick={() => loadPage(0)} disabled={!!busy}>
            {busy === "Loading profile" ? "Loading..." : "Refresh"}
          </button>
          <div className="row">
            <button onClick={() => loadPage(Math.max(0, offset - limit))}>Prev</button>
            <button onClick={() => loadPage(offset + limit)}>Next</button>
          </div>
        </div>
        {error ? <div className="error">{error}</div> : null}
        <div className="list">
          {wagers.filter((w) => statusFilter === "all" || w.status === statusFilter).length === 0 ? (
            <div className="muted">No wagers found in this page.</div>
          ) : (
            wagers
              .filter((w) => statusFilter === "all" || w.status === statusFilter)
              .map((w) => (
                <div key={w.id} className="list-item">
                  <div>
                    <div className="mono">{w.id}</div>
                    <div className="muted">{w.prediction}</div>
                  </div>
                  <div className="muted">{w.status} • pot {w.pot}</div>
                </div>
              ))
          )}
        </div>
      </section>
    </Layout>
  );
}
