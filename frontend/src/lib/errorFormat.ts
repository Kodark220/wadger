export function formatError(err: any): string {
  if (!err) return "Unknown error";
  if (typeof err === "string") return err;
  if (err.message) return err.message;
  if (err.error) return err.error;
  if (err?.cause?.message) return err.cause.message;
  try {
    return JSON.stringify(err);
  } catch {
    return "Unknown error";
  }
}
