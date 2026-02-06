type SignMessageAsync = (args: { message: string }) => Promise<string>;

function relayerUrl() {
  return process.env.NEXT_PUBLIC_RELAYER_URL || "http://localhost:5000";
}

export async function getNonce(address: string) {
  const res = await fetch(`${relayerUrl()}/relay/nonce`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Nonce error");
  return data as { nonce: string; timestamp: number };
}

export async function relayAction(
  action: "create" | "accept" | "verify" | "appeal" | "resolve",
  payload: Record<string, any>,
  address: string,
  signMessageAsync: SignMessageAsync
) {
  const { nonce, timestamp } = await getNonce(address);
  const message = `GenLayer Wager Relayer\nAction: ${action}\nAddress: ${address}\nNonce: ${nonce}\nTimestamp: ${timestamp}`;
  const signature = await signMessageAsync({ message });

  const res = await fetch(`${relayerUrl()}/relay/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      address,
      signature,
      nonce,
      timestamp,
      ...payload,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Relayer error");
  return data;
}
