export function isHexAddress(value: string) {
  return /^0x[a-fA-F0-9]{40}$/.test(value);
}
