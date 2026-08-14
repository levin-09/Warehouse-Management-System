// Helper to pick a chip class for a status value.
export function statusChip(status?: string): string {
  if (!status) return "chip-neutral";
  const map: Record<string, string> = {
    // orders
    pending: "chip-warning", picking: "chip-warning", packed: "chip-warning",
    shipped: "chip-success", received: "chip-success", completed: "chip-success",
    labeled: "chip-neutral", cancelled: "chip-neutral", draft: "chip-warning",
    awaiting_seller: "chip-neutral", disposed: "chip-neutral",
    sent: "chip-success",
  };
  return map[status] ?? "chip-neutral";
}

export function formatNumber(n?: number): string {
  return (n ?? 0).toLocaleString("en-US");
}

export function formatCurrency(n?: number): string {
  const v = Number(n) || 0;
  return "$" + v.toFixed(2);
}

export function formatDate(s?: string | null): string {
  if (!s) return "—";
  return new Date(s).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}
