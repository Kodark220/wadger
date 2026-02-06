import { createClient, createAccount } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionStatus } from 'genlayer-js/types';

const RPC_URL = process.env.GENLAYER_RPC_URL;
const CONTRACT = process.env.CONTRACT_ADDRESS;
const PRIVATE_KEY = process.env.GENLAYER_PRIVATE_KEY;

if (!RPC_URL) throw new Error('GENLAYER_RPC_URL not set');
if (!CONTRACT) throw new Error('CONTRACT_ADDRESS not set');

const clientConfig = {
  chain: { ...studionet, rpcUrls: { default: { http: [RPC_URL] } } },
};

async function main() {
  const [cmd, ...args] = process.argv.slice(2);
  if (!cmd) throw new Error('Command required');

  const getArg = (flag, fallback = undefined) => {
    const i = args.indexOf(flag);
    if (i !== -1 && i + 1 < args.length) return args[i + 1];
    return fallback;
  };

  const toJson = (value) =>
    JSON.stringify(
      value,
      (_k, v) => (typeof v === 'bigint' ? v.toString() : v),
      2,
    );

  const parsePrivateKey = (pk) => {
    if (!pk) return pk;
    if (typeof pk !== 'string') return pk;
    const hex = pk.startsWith('0x') ? pk.slice(2) : pk;
    if (!/^[0-9a-fA-F]{64}$/.test(hex)) {
      throw new Error('GENLAYER_PRIVATE_KEY must be 32-byte hex (64 chars)');
    }
    return `0x${hex}`;
  };

  if (cmd === 'create') {
    if (!PRIVATE_KEY) throw new Error('GENLAYER_PRIVATE_KEY not set');
    const account = createAccount(parsePrivateKey(PRIVATE_KEY));
    const client = createClient({ ...clientConfig, account });
    const prediction = getArg('--prediction');
    const deadline = getArg('--deadline');
    const category = getArg('--category', '');
    const criteria = getArg('--criteria');
    const stake = BigInt(getArg('--stake', '0'));
    if (!prediction || !deadline || !criteria) throw new Error('Missing required args');

    const hash = await client.writeContract({
      address: CONTRACT,
      functionName: 'create_wager',
      args: [prediction, Number(stake), deadline, category, criteria],
      value: stake,
    });
    const receipt = await client.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.ACCEPTED,
      retries: 50,
      interval: 4000,
    });
    console.log(toJson({ hash, receipt }));
    return;
  }

  if (cmd === 'accept') {
    if (!PRIVATE_KEY) throw new Error('GENLAYER_PRIVATE_KEY not set');
    const account = createAccount(parsePrivateKey(PRIVATE_KEY));
    const client = createClient({ ...clientConfig, account });
    const wager = getArg('--wager');
    const stake = BigInt(getArg('--stake', '0'));
    if (!wager) throw new Error('Missing --wager');
    const hash = await client.writeContract({
      address: CONTRACT,
      functionName: 'accept_wager',
      args: [wager],
      value: stake,
    });
    const receipt = await client.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.ACCEPTED,
      retries: 50,
      interval: 4000,
    });
    console.log(toJson({ hash, receipt }));
    return;
  }

  if (cmd === 'verify') {
    if (!PRIVATE_KEY) throw new Error('GENLAYER_PRIVATE_KEY not set');
    const account = createAccount(parsePrivateKey(PRIVATE_KEY));
    const client = createClient({ ...clientConfig, account });
    const wager = getArg('--wager');
    const evidence = getArg('--evidence-url', '');
    if (!wager) throw new Error('Missing --wager');
    const hash = await client.writeContract({
      address: CONTRACT,
      functionName: 'submit_verification',
      args: [wager, evidence],
    });
    const receipt = await client.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.ACCEPTED,
      retries: 50,
      interval: 4000,
    });
    console.log(toJson({ hash, receipt }));
    return;
  }

  if (cmd === 'appeal') {
    if (!PRIVATE_KEY) throw new Error('GENLAYER_PRIVATE_KEY not set');
    const account = createAccount(parsePrivateKey(PRIVATE_KEY));
    const client = createClient({ ...clientConfig, account });
    const wager = getArg('--wager');
    const reason = getArg('--reason');
    const evidence = getArg('--evidence-url', '');
    if (!wager || !reason) throw new Error('Missing --wager or --reason');
    const hash = await client.writeContract({
      address: CONTRACT,
      functionName: 'submit_appeal',
      args: [wager, reason, evidence],
    });
    const receipt = await client.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.ACCEPTED,
      retries: 50,
      interval: 4000,
    });
    console.log(toJson({ hash, receipt }));
    return;
  }

  if (cmd === 'resolve') {
    if (!PRIVATE_KEY) throw new Error('GENLAYER_PRIVATE_KEY not set');
    const account = createAccount(parsePrivateKey(PRIVATE_KEY));
    const client = createClient({ ...clientConfig, account });
    const wager = getArg('--wager');
    if (!wager) throw new Error('Missing --wager');
    const hash = await client.writeContract({
      address: CONTRACT,
      functionName: 'resolve_wager',
      args: [wager],
    });
    const receipt = await client.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.ACCEPTED,
      retries: 50,
      interval: 4000,
    });
    console.log(toJson({ hash, receipt }));
    return;
  }

  if (cmd === 'get') {
    const client = createClient({ ...clientConfig });
    const wager = getArg('--wager');
    if (!wager) throw new Error('Missing --wager');
    const result = await client.readContract({
      address: CONTRACT,
      functionName: 'get_wager',
      args: [wager],
      jsonSafeReturn: true,
    });
    console.log(toJson({ result }));
    return;
  }

  if (cmd === 'getstatus') {
    const client = createClient({ ...clientConfig });
    const wager = getArg('--wager');
    if (!wager) throw new Error('Missing --wager');
    const result = await client.readContract({
      address: CONTRACT,
      functionName: 'get_status',
      args: [wager],
      jsonSafeReturn: true,
    });
    console.log(toJson({ result }));
    return;
  }

  if (cmd === 'getjson') {
    const client = createClient({ ...clientConfig });
    const wager = getArg('--wager');
    if (!wager) throw new Error('Missing --wager');
    const result = await client.readContract({
      address: CONTRACT,
      functionName: 'get_wager_json',
      args: [wager],
    });
    console.log(toJson({ result }));
    return;
  }

  if (cmd === 'getstatusjson') {
    const client = createClient({ ...clientConfig });
    const wager = getArg('--wager');
    if (!wager) throw new Error('Missing --wager');
    const result = await client.readContract({
      address: CONTRACT,
      functionName: 'get_status_json',
      args: [wager],
    });
    console.log(toJson({ result }));
    return;
  }

  if (cmd === 'getlast') {
    const client = createClient({ ...clientConfig });
    const result = await client.readContract({
      address: CONTRACT,
      functionName: 'get_last_wager_id',
      args: [],
    });
    console.log(toJson({ result }));
    return;
  }

  throw new Error(`Unknown command: ${cmd}`);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
