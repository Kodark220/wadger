"use client";
import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../../components/Layout";
import { getReadClient } from "../../lib/genlayerClient";
import { relayAction } from "../../lib/relayer";
import { useAccount, useSignMessage } from "wagmi";
import { useToast } from "../../components/ToastProvider";
import { formatError } from "../../lib/errorFormat";

const CONTRACT = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";

export default function WagerPage() {
  const router = useRouter();
  const wagerId = useMemo(() => (router.query.id ? String(router.query.id) : ""), [router.query.id]);
  const { address, isConnected } = useAccount();
  const { signMessageAsync } = useSignMessage();
  const { pushToast } = useToast();

  const [wager, setWager] = useState<any | null>(null);
  const [status, setStatus] = useState<any | null>(null);
  const [evidenceUrl, setEvidenceUrl] = useState("https://coinmarketcap.com/currencies/bitcoin/");
  const [appealReason, setAppealReason] = useState("finalize");
  const [stake, setStake] = useState(100);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  async function loadWager() {
    if (!wagerId || !CONTRACT) return;
    await withBusy("Loading wager", async () => {
      const client = getReadClient();
      const result = await client.readContract({
        address: CONTRACT,
        functionName: "get_wager_json",
        args: [wagerId],
      });
      setWager(JSON.parse(result as string));
    });
  }

  async function loadStatus() {
    if (!wagerId || !CONTRACT) return;
    await withBusy("Loading status", async () => {
      const client = getReadClient();
      const result = await client.readContract({
        address: CONTRACT,
        functionName: "get_status_json",
        args: [wagerId],
      });
      setStatus(JSON.parse(result as string));
    });
  }

  async function acceptWager() {
    if (!address) return setError("Connect wallet first");
    await withBusy("Accepting wager", async () => {
      await relayAction(
        "accept",
        { wager_id: wagerId, stake_amount: Number(stake) },
        address,
        signMessageAsync
      );
      await loadStatus();
    });
  }

  async function submitVerification() {
    if (!address) return setError("Connect wallet first");
    await withBusy("Verifying", async () => {
      await relayAction(
        "verify",
        { wager_id: wagerId, evidence_url: evidenceUrl },
        address,
        signMessageAsync
      );
      await loadStatus();
    });
  }

  async function submitAppeal() {
    if (!address) return setError("Connect wallet first");
    await withBusy("Appealing", async () => {
      await relayAction(
        "appeal",
        { wager_id: wagerId, appeal_reason: appealReason, evidence_url: evidenceUrl },
        address,
        signMessageAsync
      );
      await loadStatus();
    });
  }

  async function resolveWager() {
    if (!address) return setError("Connect wallet first");
    await withBusy("Resolving", async () => {
      await relayAction(
        "resolve",
        { wager_id: wagerId },
        address,
        signMessageAsync
      );
      await loadStatus();
    });
  }

  useEffect(() => {
    if (!wagerId) return;
    loadWager();
    loadStatus();
  }, [wagerId]);

  return (
    <Layout>
      <section className="hero">
        <div>
          <div className="eyebrow">Wager</div>
          <h1>{wagerId || "Loading..."}</h1>
          <p>Manage this wager: accept, verify, appeal, resolve.</p>
        </div>
        <div className="card">
          <div className="muted">Contract</div>
          <div className="mono">{CONTRACT}</div>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Wager Details</h2>
          <button onClick={loadWager} disabled={!!busy}>
            {busy === "Loading wager" ? "Loading..." : "Refresh"}
          </button>
          <div className="codeblock">
            <pre>{wager ? JSON.stringify(wager, null, 2) : "No data yet."}</pre>
          </div>
        </div>

        <div className="card">
          <h2>Status</h2>
          <button onClick={loadStatus} disabled={!!busy}>
            {busy === "Loading status" ? "Loading..." : "Refresh"}
          </button>
          <div className="codeblock">
            <pre>{status ? JSON.stringify(status, null, 2) : "No status yet."}</pre>
          </div>
        </div>

        <div className="card">
          <h2>Actions</h2>
          <label>Stake (for accept)</label>
          <input type="number" value={stake} onChange={(e) => setStake(Number(e.target.value))} />
          <label>Evidence URL</label>
          <input value={evidenceUrl} onChange={(e) => setEvidenceUrl(e.target.value)} />
          <label>Appeal Reason</label>
          <input value={appealReason} onChange={(e) => setAppealReason(e.target.value)} />
          <div className="row">
            <button onClick={acceptWager} disabled={!!busy || !isConnected}>
              {busy === "Accepting wager" ? "Accepting..." : "Accept"}
            </button>
            <button onClick={submitVerification} disabled={!!busy || !isConnected}>
              {busy === "Verifying" ? "Verifying..." : "Verify"}
            </button>
          </div>
          <div className="row">
            <button onClick={submitAppeal} disabled={!!busy || !isConnected}>
              {busy === "Appealing" ? "Appealing..." : "Appeal"}
            </button>
            <button className="primary" onClick={resolveWager} disabled={!!busy || !isConnected}>
              {busy === "Resolving" ? "Resolving..." : "Resolve"}
            </button>
          </div>
        </div>

        {error ? (
          <div className="card">
            <h2>Error</h2>
            <div className="error">{error}</div>
          </div>
        ) : null}
      </section>
    </Layout>
  );
}
