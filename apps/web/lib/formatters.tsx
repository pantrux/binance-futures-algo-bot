export function formatNumber(value: number | null | undefined, digits = 0) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("es-CL", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "short",
    timeStyle: "short",
    hour12: false,
  }).format(new Date(value));
}

export function formatPercent(value: number | null | undefined, digits = 2) {
  if (value == null || Number.isNaN(value)) return "—";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatNumber(value, digits)}%`;
}

export function statusTone(status: string) {
  const normalized = status?.toLowerCase() || "";
  if (["filled", "testnet_executed", "paper_executed", "approved", "open", "healthy"].includes(normalized)) return "ok";
  if (["warning", "partially_filled", "blocked", "draft", "new"].includes(normalized)) return "warn";
  if (["critical", "rejected", "cancelled", "canceled", "expired"].includes(normalized)) return "danger";
  return "neutral";
}

export function toneClassName(tone: string) {
  if (["ok", "warn", "danger", "neutral"].includes(tone)) return tone;
  return "neutral";
}

export function reconcileTone(healthy: boolean, severity: string | null) {
  if (healthy) return "ok";
  if (severity === "critical") return "danger";
  if (severity === "warning") return "warn";
  return "neutral";
}

export function timelineEntityLabel(entityKind: string) {
  switch (entityKind) {
    case "trade_plan": return "trade plan";
    case "order": return "orden";
    case "position": return "posición";
    case "risk_event": return "risk";
    case "reconciliation": return "reconcile";
    default: return entityKind;
  }
}

function contextLabel(key: string) {
  switch (key) {
    case "external_order_id": return "order";
    case "market_regime": return "régimen";
    case "regime_confidence": return "conf.";
    case "executed_quantity": return "exec";
    case "binance_side": return "side API";
    case "portfolio_risk_after": return "risk pf";
    case "cluster_risk_after": return "risk cluster";
    case "symbol_risk_after": return "risk sym";
    default: return key.replaceAll("_", " ");
  }
}

function formatContextValue(key: string, value: string | number | boolean | null) {
  if (value == null) return "—";
  if (typeof value === "number") {
    if (key.endsWith("_id")) return String(value);
    if (Number.isInteger(value)) return formatNumber(value, 0);
    return formatNumber(value, Math.abs(value) >= 100 ? 2 : 4);
  }
  if (typeof value === "boolean") return value ? "sí" : "no";
  return value;
}

export function renderRiskContext(context: Record<string, string | number | boolean | null> | null | undefined) {
  const entries = Object.entries(context ?? {}).filter(([, value]) => value !== null && value !== "").slice(0, 8);
  if (entries.length === 0) return null;

  return (
    <div className="context-list">
      {entries.map(([key, value]) => (
        <span key={`${key}-${String(value)}`} className="context-chip">
          <strong>{contextLabel(key)}:</strong> {formatContextValue(key, value)}
        </span>
      ))}
    </div>
  );
}
