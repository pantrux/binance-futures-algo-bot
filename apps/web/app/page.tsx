import { LiveWorkstation } from "../components/LiveWorkstation";

export const dynamic = 'force-dynamic';

async function getCommandCenter() {
  const url = process.env.SYNOLOGY_API_BASE_URL
    ? `${process.env.SYNOLOGY_API_BASE_URL}/dashboard/command-center`
    : 'http://192.168.0.8:8010/dashboard/command-center';

  const res = await fetch(url, { next: { revalidate: 5 } });
  if (!res.ok) throw new Error('Failed to fetch command center data');
  return res.json();
}

function buildTape(commandCenter: any) {
  const map = new Map();
  for (const operation of commandCenter.operation_snapshots) {
    const key = `${operation.symbol}-${operation.timeframe}`;
    if (!map.has(key)) {
      map.set(key, {
        key, symbol: operation.symbol, timeframe: operation.timeframe, side: operation.side, status: operation.status,
        price: operation.latest_position_mark_price ?? operation.latest_order_price ?? operation.entry_price,
        pnl: operation.latest_position_unrealized_pnl, regime: operation.market_regime,
      });
    }
  }
  for (const position of commandCenter.open_positions) {
    const key = `${position.symbol}-live`;
    if (!map.has(key)) {
      map.set(key, {
        key, symbol: position.symbol, timeframe: "live", side: position.side, status: position.status,
        price: position.mark_price, pnl: position.unrealized_pnl, regime: null,
      });
    }
  }
  return Array.from(map.values()).slice(0, 10);
}

export default async function HomePage() {
  const commandCenter = await getCommandCenter();
  const tape = buildTape(commandCenter);
  const totalOpenPnl = commandCenter.open_positions.reduce((acc: any, position: any) => acc + position.unrealized_pnl, 0);

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
            <p>Comparados: {commandCenter.shadow_run.compared_pairs} · Unmatched: {commandCenter.shadow_run.unmatched_paper}/{commandCenter.shadow_run.unmatched_testnet}</p>
          </article>
          <article className="sidebar-card">
            <span className={`badge ${commandCenter.recent_risk_events.some((e:any) => e.severity === 'critical') ? "danger" : "ok"}`}>risk feed</span>
            <strong>{commandCenter.summary.risk_events_total} eventos</strong>
            <p>Critical recientes: {commandCenter.recent_risk_events.filter((e:any) => e.severity === 'critical').length}</p>
          </article>
        </div>
      </aside>

      <div className="workspace-main">
        <LiveWorkstation initialData={commandCenter} initialTape={tape} initialOpenPnl={totalOpenPnl} />
      </div>
    </main>
  );
}
