"use client";
import React, { useMemo, useState } from "react";
import Link from "next/link";
import Layout from "../components/Layout";
import { getReadClient } from "../lib/genlayerClient";
import { useAccount, useSignMessage } from "wagmi";
import { relayAction } from "../lib/relayer";
import { useToast } from "../components/ToastProvider";
import { formatError } from "../lib/errorFormat";
import { isHexAddress } from "../lib/address";

const CONTRACT = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";

type StatusMap = Record<string, any>;

export default function LobbyPage() {
  const { address, isConnected } = useAccount();
  const { signMessageAsync } = useSignMessage();
  const { pushToast } = useToast();
  const [prediction, setPrediction] = useState(
    "BTC will be above $100,000 on Dec 31 2026"
  );
  const [stake, setStake] = useState(100);
  const [deadline, setDeadline] = useState("2026-12-31T23:59:59");
  const [category, setCategory] = useState("crypto");
  const [criteria, setCriteria] = useState("https://coinmarketcap.com/currencies/bitcoin/");
  const [criteriaPreset, setCriteriaPreset] = useState("coinmarketcap_btc");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [wagerIds, setWagerIds] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(8);
  const [statusMap, setStatusMap] = useState<StatusMap>({});
  const [wagerIdInput, setWagerIdInput] = useState("");
  const [players, setPlayers] = useState<string[]>([]);
  const [playerStats, setPlayerStats] = useState<Record<string, any>>({});
  const [globalStats, setGlobalStats] = useState<any | null>(null);
  const [playerOffset, setPlayerOffset] = useState(0);
  const [playerLimit, setPlayerLimit] = useState(8);
  const [wagerFilter, setWagerFilter] = useState<"all" | "active" | "resolved" | "waiting" | "verified">("all");

  const canWrite = useMemo(() => isConnected && !!CONTRACT, [isConnected]);

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

  async function loadWagers(nextOffset = 0) {
    if (!CONTRACT) return setError("Set NEXT_PUBLIC_CONTRACT_ADDRESS");
    await withBusy("Loading lobby", async () => {
      const client = getReadClient();
      const result = await client.readContract({
        address: CONTRACT,
        functionName: "list_wagers_json",
        args: [nextOffset, limit],
      });
      const ids = JSON.parse(result as string) as string[];
      setOffset(nextOffset);
      setWagerIds(ids);
    });
  }

  async function loadStatus(wagerId: string) {
    if (!CONTRACT) return setError("Set NEXT_PUBLIC_CONTRACT_ADDRESS");
    await withBusy("Loading status", async () => {
      const client = getReadClient();
      const result = await client.readContract({
        address: CONTRACT,
        functionName: "get_status_json",
        args: [wagerId],
      });
      const parsed = JSON.parse(result as string);
      setStatusMap((m) => ({ ...m, [wagerId]: parsed }));
    });
  }

  function filteredWagers() {
    if (wagerFilter === "all") return wagerIds;
    return wagerIds.filter((id) => {
      const s = statusMap[id]?.status;
      return s === wagerFilter;
    });
  }

  async function loadGlobalStats() {
    if (!CONTRACT) return setError("Set NEXT_PUBLIC_CONTRACT_ADDRESS");
    await withBusy("Loading global stats", async () => {
      const client = getReadClient();
      const result = await client.readContract({
        address: CONTRACT,
        functionName: "get_global_stats_json",
        args: [],
      });
      setGlobalStats(JSON.parse(result as string));
    });
  }

  async function loadPlayers(nextOffset = 0) {
    if (!CONTRACT) return setError("Set NEXT_PUBLIC_CONTRACT_ADDRESS");
    await withBusy("Loading leaderboard", async () => {
      const client = getReadClient();
      const result = await client.readContract({
        address: CONTRACT,
        functionName: "list_players_json",
        args: [nextOffset, playerLimit],
      });
      const list = JSON.parse(result as string) as string[];
      setPlayers(list);
      setPlayerOffset(nextOffset);

      const stats: Record<string, any> = {};
      for (const addr of list) {
        if (!isHexAddress(addr)) {
          continue;
        }
        try {
          const s = await client.readContract({
            address: CONTRACT,
            functionName: "get_player_stats_json",
            args: [addr],
          });
          stats[addr] = JSON.parse(s as string);
        } catch (e) {
          stats[addr] = {
            wins: 0,
            losses: 0,
            volume_won: 0,
          };
        }
      }
      const sorted = [...list].sort((a, b) => {
        const aw = Number(stats[a]?.wins ?? 0);
        const bw = Number(stats[b]?.wins ?? 0);
        if (bw !== aw) return bw - aw;
        const av = Number(stats[a]?.volume_won ?? 0);
        const bv = Number(stats[b]?.volume_won ?? 0);
        return bv - av;
      });
      setPlayers(sorted);
      setPlayerStats(stats);
    });
  }

  async function createWager() {
    if (!address) return setError("Connect wallet first");
    if (!CONTRACT) return setError("Set NEXT_PUBLIC_CONTRACT_ADDRESS");
    await withBusy("Creating wager", async () => {
      await relayAction(
        "create",
        {
        prediction,
        deadline,
        category,
        verification_criteria: criteria,
        stake_amount: Number(stake),
        },
        address,
        signMessageAsync
      );
      await loadWagers(offset);
    });
  }

  return (
    <Layout>
      <section className="hero">
        <div>
          <div className="eyebrow">Lobby</div>
          <h1>Find a wager or create a new one.</h1>
          <p>
            This frontend reads on-chain with GenLayer JS and uses a relayer for writes,
            so users only connect a wallet to sign a message.
          </p>
        </div>
        <div className="card">
          <div className="muted">Connect Wallet (Identity)</div>
          <div className="muted">
            {isConnected && address ? `Connected: ${address}` : "Use the Connect Wallet button in the header."}
          </div>
          <Link className="link" href={address ? `/profile/${address}` : "/profile/me"}>
            Open profile
          </Link>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Create Wager</h2>
          <label>Prediction</label>
          <textarea value={prediction} onChange={(e) => setPrediction(e.target.value)} />
          <div className="row">
            <div className="col">
              <label>Stake</label>
              <input type="number" value={stake} onChange={(e) => setStake(Number(e.target.value))} />
            </div>
            <div className="col">
              <label>Category</label>
              <input value={category} onChange={(e) => setCategory(e.target.value)} />
            </div>
          </div>
          <label>Deadline (ISO)</label>
          <input
            type="datetime-local"
            value={deadline.replace("Z", "")}
            onChange={(e) => {
              const v = e.target.value;
              setDeadline(v ? `${v}` : "");
            }}
          />
          <label>Verification Criteria</label>
          <select
            value={criteriaPreset}
            onChange={(e) => {
              const v = e.target.value;
              setCriteriaPreset(v);
              if (v === "coinmarketcap_btc") {
                setCriteria("https://coinmarketcap.com/currencies/bitcoin/");
              } else if (v === "coingecko_btc") {
                setCriteria("https://www.coingecko.com/en/coins/bitcoin");
              } else if (v === "binance_btc") {
                setCriteria("https://www.binance.com/en/price/bitcoin");
              } else if (v === "football_fifa") {
                setCriteria("https://www.fifa.com/");
              } else if (v === "football_premier_league") {
                setCriteria("https://www.premierleague.com/");
              } else if (v === "football_uefa") {
                setCriteria("https://www.uefa.com/");
              } else if (v === "news_reuters") {
                setCriteria("https://www.reuters.com/");
              } else if (v === "news_ap") {
                setCriteria("https://apnews.com/");
              } else if (v === "news_bbc") {
                setCriteria("https://www.bbc.com/news");
              } else if (v === "weather_weather_com") {
                setCriteria("https://weather.com/");
              } else if (v === "weather_noaa") {
                setCriteria("https://www.weather.gov/");
              } else if (v === "weather_met") {
                setCriteria("https://www.metoffice.gov.uk/");
              } else if (v === "custom") {
                setCriteria("");
              }
            }}
          >
            <option value="coinmarketcap_btc">CoinMarketCap BTC</option>
            <option value="coingecko_btc">CoinGecko BTC</option>
            <option value="binance_btc">Binance BTC</option>
            <option value="football_fifa">Football: FIFA</option>
            <option value="football_premier_league">Football: Premier League</option>
            <option value="football_uefa">Football: UEFA</option>
            <option value="news_reuters">News: Reuters</option>
            <option value="news_ap">News: AP</option>
            <option value="news_bbc">News: BBC News</option>
            <option value="weather_weather_com">Weather: The Weather Channel</option>
            <option value="weather_noaa">Weather: NOAA</option>
            <option value="weather_met">Weather: Met Office (UK)</option>
            <option value="custom">Custom URL</option>
          </select>
          <input
            placeholder="https://..."
            value={criteria}
            onChange={(e) => setCriteria(e.target.value)}
            disabled={criteriaPreset !== "custom"}
          />
          <button className="primary" onClick={createWager} disabled={!canWrite || !!busy}>
            {busy === "Creating wager" ? "Creating..." : "Create"}
          </button>
        </div>

        <div className="card">
          <h2>Wager List</h2>
          <div className="row">
            <button onClick={() => loadWagers(0)} disabled={!!busy}>
              {busy === "Loading lobby" ? "Loading..." : "Refresh"}
            </button>
            <div className="row">
              <button onClick={() => loadWagers(Math.max(0, offset - limit))}>Prev</button>
              <button onClick={() => loadWagers(offset + limit)}>Next</button>
            </div>
          </div>
          <div className="row">
            <button onClick={() => setWagerFilter("all")} className={wagerFilter === "all" ? "primary" : ""}>All</button>
            <button onClick={() => setWagerFilter("active")} className={wagerFilter === "active" ? "primary" : ""}>Active</button>
            <button onClick={() => setWagerFilter("resolved")} className={wagerFilter === "resolved" ? "primary" : ""}>Resolved</button>
            <button onClick={() => setWagerFilter("waiting")} className={wagerFilter === "waiting" ? "primary" : ""}>Waiting</button>
            <button onClick={() => setWagerFilter("verified")} className={wagerFilter === "verified" ? "primary" : ""}>Verified</button>
          </div>
          <div className="list">
            {filteredWagers().length === 0 ? (
              <div className="muted">No wagers loaded yet.</div>
            ) : (
              filteredWagers().map((id) => (
                <div key={id} className="list-item">
                  <div>
                    <div className="mono">{id}</div>
                    {statusMap[id] ? (
                      <div className="muted">
                        {statusMap[id].status} • pot {statusMap[id].pot} • {statusMap[id].outcome || "pending"}
                      </div>
                    ) : (
                      <div className="muted">status not loaded</div>
                    )}
                  </div>
                  <div className="row">
                    <button onClick={() => loadStatus(id)} disabled={!!busy}>
                      Status
                    </button>
                    <Link className="link" href={`/wager/${encodeURIComponent(id)}`}>
                      Open
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <h2>Global Stats</h2>
          <button onClick={loadGlobalStats} disabled={!!busy}>
            {busy === "Loading global stats" ? "Loading..." : "Refresh"}
          </button>
          <div className="codeblock">
            <pre>
              {globalStats ? JSON.stringify(globalStats, null, 2) : "No stats loaded."}
            </pre>
          </div>
        </div>

        <div className="card">
          <h2>Leaderboard</h2>
          <div className="row">
            <button onClick={() => loadPlayers(0)} disabled={!!busy}>
              {busy === "Loading leaderboard" ? "Loading..." : "Refresh"}
            </button>
            <div className="row">
              <button onClick={() => loadPlayers(Math.max(0, playerOffset - playerLimit))}>Prev</button>
              <button onClick={() => loadPlayers(playerOffset + playerLimit)}>Next</button>
            </div>
          </div>
          <div className="list">
            {players.length === 0 ? (
              <div className="muted">No players loaded yet.</div>
            ) : (
              players.map((addr) => {
                const s = playerStats[addr];
                return (
                  <div key={addr} className="list-item">
                    <div>
                      <div className="mono">{addr}</div>
                      <div className="muted">
                        W {s?.wins ?? 0} • L {s?.losses ?? 0} • Vol {s?.volume_won ?? 0}
                      </div>
                    </div>
                    <div className="row">
                      <Link className="link" href={`/profile/${addr}`}>
                        Profile
                      </Link>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="card">
          <h2>Open by ID</h2>
          <label>Wager ID</label>
          <input value={wagerIdInput} onChange={(e) => setWagerIdInput(e.target.value)} />
          <Link className="link" href={wagerIdInput ? `/wager/${encodeURIComponent(wagerIdInput)}` : "#"}>
            Go to wager
          </Link>
          <div className="spacer" />
          {error ? <div className="error">{error}</div> : null}
        </div>
      </section>
    </Layout>
  );
}
