import { LiveWorkstation } from "../components/LiveWorkstation";

export const dynamic = "force-dynamic";

function buildEmptyCommandCenter() {
  return {
    generated_at: new Date().toISOString(),
    summary: {
      open_positions: 0,
      trade_plans_total: 0,
      approved_trade_plans: 0,
      paper_executed_trade_plans: 0,
      testnet_executed_trade_plans: 0,
      risk_events_total: 0,
    },
    shadow_run: {
      shadow_run_duration_days: 0,
      compared_pairs: 0,
      unmatched_paper: 0,
      unmatched_testnet: 0,
      testnet_fill_rate_pct: 0,
      critical_risk_events_7d: 0,
      warning_risk_events_7d: 0,
      testnet_orders_total: 0,
      testnet_orders_filled: 0,
      avg_testnet_slippage_bps: 0,
    },
    recent_trade_plans: [],
    recent_orders: [],
    open_positions: [],
    recent_risk_events: [],
    timeline: [],
    operation_snapshots: [],
  };
}

function normalizeBaseUrl(value: string | undefined) {
  return value?.trim().replace(/\/$/, "") || null;
}

async function getCommandCenter() {
  const apiBaseUrl =
    normalizeBaseUrl(process.env.SYNOLOGY_API_BASE_URL) ??
    normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL);

  if (!apiBaseUrl) {
    console.warn("[workstation] command center disabled: missing SYNOLOGY_API_BASE_URL/NEXT_PUBLIC_API_URL");
    return buildEmptyCommandCenter();
  }

  try {
    const res = await fetch(`${apiBaseUrl}/dashboard/command-center`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`Failed to fetch command center data (${res.status})`);
    }
    return await res.json();
  } catch (error) {
    console.error("[workstation] command center fallback to empty snapshot", error);
    return buildEmptyCommandCenter();
  }
}

function buildTape(commandCenter: any) {
  const map = new Map();

  for (const operation of commandCenter.operation_snapshots ?? []) {
    const key = `${operation.symbol}-${operation.timeframe}`;
    if (!map.has(key)) {
      map.set(key, {
        key,
        symbol: operation.symbol,
        timeframe: operation.timeframe,
        side: operation.side,
        status: operation.status,
        price: operation.latest_position_mark_price ?? operation.latest_order_price ?? operation.entry_price,
        pnl: operation.latest_position_unrealized_pnl,
        regime: operation.market_regime,
      });
    }
  }

  for (const position of commandCenter.open_positions ?? []) {
    const key = `${position.symbol}-live`;
    if (!map.has(key)) {
      map.set(key, {
        key,
        symbol: position.symbol,
        timeframe: "live",
        side: position.side,
        status: position.status,
        price: position.mark_price,
        pnl: position.unrealized_pnl,
        regime: null,
      });
    }
  }

  return Array.from(map.values()).slice(0, 10);
}

export default async function HomePage() {
  const commandCenter = await getCommandCenter();
  const tape = buildTape(commandCenter);
  const totalOpenPnl = (commandCenter.open_positions ?? []).reduce(
    (acc: number, position: any) => acc + (position.unrealized_pnl ?? 0),
    0,
  );

  return (
    <main className="terminal-shell">
      <aside className="workspace-sidebar">
        <div className="workspace-brand">
          <span className="brand-mark">S</span>
          <div>
            <p className="eyebrow">Skynet Desk</p>
            <h2>Command Center</h2>
          </div>
        </div>

        <nav className="workspace-nav">
          <a href="#overview">Overview</a>
          <a href="#desk">Desk</a>
          <a href="#operations">Operations</a>
          <a href="#book">Book</a>
          <a href="#risk">Risk</a>
          <a href="#drilldown">Drill-down</a>
        </nav>

        <div className="sidebar-stack">
          <article className="sidebar-card">
            <span className="badge ok">shadow run</span>
            <strong>{commandCenter.shadow_run.shadow_run_duration_days?.toFixed(2) ?? "0.00"} días</strong>
            <p>
              Comparados: {commandCenter.shadow_run.compared_pairs} · Unmatched: {commandCenter.shadow_run.unmatched_paper}/
              {commandCenter.shadow_run.unmatched_testnet}
            </p>
          </article>
          <article className="sidebar-card">
            <span
              className={`badge ${commandCenter.recent_risk_events.some((event: any) => event.severity === "critical") ? "danger" : "ok"}`}
            >
              risk feed
            </span>
            <strong>{commandCenter.summary.risk_events_total} eventos</strong>
            <p>Critical recientes: {commandCenter.recent_risk_events.filter((event: any) => event.severity === "critical").length}</p>
          </article>
        </div>
      </aside>

      <div className="workspace-main">
        <LiveWorkstation initialData={commandCenter} initialTape={tape} initialOpenPnl={totalOpenPnl} />
      </div>
    </main>
  );
}
