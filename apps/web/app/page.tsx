import { getOperationStatusBucket, getOperationDetailHref } from "../lib/operation-metrics";

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

function groupOperations(commandCenter: any) {
  const active: any[] = [];
  const closed: any[] = [];
  for (const operation of commandCenter.operation_snapshots ?? []) {
    const bucket = getOperationStatusBucket(operation);
    if (bucket === "closed") {
      closed.push(operation);
    } else {
      active.push(operation);
    }
  }
  return { active, closed };
}

export default async function HomePage() {
  const commandCenter = await getCommandCenter();
  const { active, closed } = groupOperations(commandCenter);
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
          <a href="#overview">Resumen</a>
          <a href="#active">Activas</a>
          <a href="#closed">Cerradas</a>
          <a href="#risk">Riesgo</a>
          <a href="#timeline">Timeline</a>
        </nav>

        <div className="sidebar-stack">
          <article className="sidebar-card">
            <span className="badge ok">shadow run</span>
            <strong>{commandCenter.shadow_run.shadow_run_duration_days?.toFixed(2) ?? "0.00"} días</strong>
            <p>
              {commandCenter.summary.approved_trade_plans} aprobadas · {commandCenter.summary.testnet_executed_trade_plans} ejecutadas · {commandCenter.summary.open_positions} abiertas
            </p>
          </article>
          <article className="sidebar-card">
            <span className={`badge ${commandCenter.recent_risk_events.some((event: any) => event.severity === "critical") ? "danger" : "ok"}`}>risk feed</span>
            <strong>{commandCenter.summary.risk_events_total} eventos</strong>
            <p>Critical recientes: {commandCenter.recent_risk_events.filter((event: any) => event.severity === "critical").length}</p>
          </article>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-header" id="overview">
          <div>
            <p className="eyebrow">Binance USDⓈ-M Futures · Testnet Desk</p>
            <h1>Resumen operativo</h1>
            <p className="lead">
              Home simplificado: el estado general arriba, las operaciones activas y cerradas debajo, y el detalle de cada operación en su propia página.
            </p>
          </div>
          <div className="header-status-panel">
            <span className="badge ok">live data</span>
            <strong>{commandCenter.summary.open_positions} abiertas · {closed.length} cerradas</strong>
            <small className="muted">PnL abierto {totalOpenPnl.toFixed(2)} USDT</small>
          </div>
        </header>

        <section className="signal-wall">
          <article className="signal-card signal-card--wide">
            <p className="eyebrow">Snapshot</p>
            <h3>{commandCenter.summary.trade_plans_total} trade plans</h3>
            <p>{commandCenter.summary.approved_trade_plans} aprobadas · {commandCenter.summary.testnet_executed_trade_plans} ejecutadas · {commandCenter.summary.risk_events_total} eventos de riesgo</p>
          </article>
          <article className="signal-card"><p>Activas</p><h3>{active.length}</h3><small>operaciones en seguimiento</small></article>
          <article className="signal-card"><p>Cerradas</p><h3>{closed.length}</h3><small>operaciones terminales</small></article>
          <article className="signal-card"><p>Open PnL</p><h3 className={totalOpenPnl >= 0 ? "positive" : "negative"}>{totalOpenPnl.toFixed(2)}</h3><small>mark-to-market total</small></article>
          <article className="signal-card"><p>Win rate</p><h3>—</h3><small>se ve en el detalle de cada operación</small></article>
        </section>

        <section id="active" className="workspace-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Activas</p>
              <h3>Operaciones en curso</h3>
            </div>
            <a className="action-link" href="#closed">ver cerradas</a>
          </div>
          <div className="operation-rail">
            {active.length === 0 ? <p className="empty-state">Sin operaciones activas.</p> : active.slice(0, 6).map((operation: any) => (
              <article key={operation.trade_plan_id} className="operation-card">
                <div className="operation-head">
                  <div>
                    <p className="operation-symbol">{operation.symbol}</p>
                    <small>{operation.timeframe} · {operation.side} · {operation.market_regime}</small>
                  </div>
                  <span className={`status-pill ${operation.reconciliation_healthy ? "ok" : "warn"}`}>{operation.status}</span>
                </div>
                <div className="operation-strip">
                  <div><span>score</span><strong>{operation.aggregate_score.toFixed(2)}</strong></div>
                  <div><span>risk</span><strong>{operation.applied_risk_pct.toFixed(2)}%</strong></div>
                  <div><span>entry</span><strong>{operation.entry_price.toFixed(2)}</strong></div>
                </div>
                <div className="operation-actions">
                  <a className="action-link primary" href={getOperationDetailHref(operation)}>ver detalle</a>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="closed" className="workspace-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Cerradas</p>
              <h3>Operaciones finalizadas</h3>
            </div>
          </div>
          <div className="operation-rail">
            {closed.length === 0 ? <p className="empty-state">Sin operaciones cerradas.</p> : closed.slice(0, 6).map((operation: any) => (
              <article key={operation.trade_plan_id} className="operation-card">
                <div className="operation-head">
                  <div>
                    <p className="operation-symbol">{operation.symbol}</p>
                    <small>{operation.timeframe} · {operation.side} · {operation.market_regime}</small>
                  </div>
                  <span className="status-pill neutral">{operation.status}</span>
                </div>
                <div className="operation-strip">
                  <div><span>entry</span><strong>{operation.entry_price.toFixed(2)}</strong></div>
                  <div><span>pnl</span><strong className={(operation.latest_position_unrealized_pnl ?? 0) >= 0 ? "positive" : "negative"}>{(operation.latest_position_unrealized_pnl ?? 0).toFixed(2)}</strong></div>
                  <div><span>risk</span><strong>{operation.applied_risk_pct.toFixed(2)}%</strong></div>
                </div>
                <div className="operation-actions">
                  <a className="action-link" href={getOperationDetailHref(operation)}>ver análisis</a>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="risk" className="workspace-section workspace-two-up">
          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Risk feed</p>
                <h3>Eventos recientes</h3>
              </div>
            </div>
            <div className="feed-list">
              {commandCenter.recent_risk_events.length === 0 ? <p className="empty-state">Sin eventos recientes.</p> : commandCenter.recent_risk_events.slice(0, 6).map((event: any) => (
                <article key={event.id} className="feed-card">
                  <div className="feed-head">
                    <span className={`status-pill ${event.severity === "critical" ? "danger" : event.severity === "warning" ? "warn" : "ok"}`}>{event.severity}</span>
                    <small>{event.event_type}</small>
                  </div>
                  <p>{event.message}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="panel workstation-panel" id="timeline">
            <div className="section-head">
              <div>
                <p className="eyebrow">Timeline</p>
                <h3>Eventos operativos</h3>
              </div>
            </div>
            <div className="feed-list">
              {commandCenter.timeline.length === 0 ? <p className="empty-state">Sin eventos en timeline.</p> : commandCenter.timeline.slice(0, 8).map((item: any, index: number) => (
                <article key={`${item.entity_kind}-${item.trade_plan_id ?? "na"}-${index}`} className="feed-card">
                  <div className="feed-head">
                    <span className="status-pill neutral">{item.entity_kind}</span>
                    <small>{item.event_kind}</small>
                  </div>
                  <p>{item.title}</p>
                  <small className="muted">{item.detail}</small>
                </article>
              ))}
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}
