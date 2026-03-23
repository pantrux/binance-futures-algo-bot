import { notFound } from "next/navigation";
import { computeOperationMetrics, getOperationDetailHref } from "../../../lib/operation-metrics";

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
    return buildEmptyCommandCenter();
  }

  const res = await fetch(`${apiBaseUrl}/dashboard/command-center`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch command center data (${res.status})`);
  }
  return await res.json();
}

function getOperation(commandCenter: any, tradePlanId: string) {
  const id = Number(tradePlanId);
  return commandCenter.operation_snapshots.find((operation: any) => operation.trade_plan_id === id) ?? null;
}

export default async function OperationDetailPage({ params }: { params: { tradePlanId: string } }) {
  const { tradePlanId } = params;
  const commandCenter = await getCommandCenter();
  const operation = getOperation(commandCenter, tradePlanId);

  if (!operation) {
    notFound();
  }

  const metrics = computeOperationMetrics(operation);

  return (
    <main className="terminal-shell">
      <aside className="workspace-sidebar">
        <div className="workspace-brand">
          <span className="brand-mark">S</span>
          <div>
            <p className="eyebrow">Operation detail</p>
            <h2>#{operation.trade_plan_id} · {operation.symbol}</h2>
          </div>
        </div>
        <nav className="workspace-nav">
          <a href="/">Home</a>
          <a href="#summary">Resumen</a>
          <a href="#performance">Performance</a>
          <a href="#orders">Órdenes</a>
          <a href="#risk">Riesgo</a>
          <a href="#timeline">Timeline</a>
        </nav>
        <div className="sidebar-stack">
          <article className="sidebar-card">
            <span className={`badge ${operation.reconciliation_healthy ? "ok" : "warn"}`}>{operation.reconciliation_healthy ? "reconcile healthy" : "reconcile drift"}</span>
            <strong>{operation.status}</strong>
            <p>{operation.side} · {operation.timeframe} · leverage {metrics.leverage}x</p>
          </article>
          <article className="sidebar-card">
            <span className="badge subtle">PNL</span>
            <strong className={metrics.netPnl >= 0 ? "positive" : "negative"}>{metrics.netPnl >= 0 ? "+" : ""}{metrics.netPnl.toFixed(2)} USDT</strong>
            <p>Realizado + no realizado - fees estimadas</p>
          </article>
        </div>
      </aside>

      <div className="workspace-main">
        <section className="workspace-section" id="summary">
          <div className="section-head">
            <div>
              <p className="eyebrow">Operation cockpit</p>
              <h3>Vista extendida de la operación</h3>
            </div>
            <a className="action-link" href={getOperationDetailHref(operation)}>open detail URL</a>
          </div>
          <div className="command-grid">
            <article className="command-stage panel workstation-panel">
              <div className="command-stage-copy">
                <p className="eyebrow">Setup</p>
                <h2>{operation.symbol} · {operation.side} · {operation.market_regime}</h2>
                <p className="lead compact-lead">{operation.thesis}</p>
                <div className="command-chip-row">
                  <span className={`badge ${operation.reconciliation_healthy ? "ok" : "warn"}`}>{operation.reconciliation_healthy ? "healthy" : "drift"}</span>
                  <span className="badge subtle">risk {operation.applied_risk_pct.toFixed(2)}%</span>
                  <span className="badge subtle">max notional {operation.max_position_notional.toFixed(2)}</span>
                </div>
              </div>
              <div className="command-stage-summary">
                <div className="command-stage-stat">
                  <span>Entry / SL / TP</span>
                  <strong>{metrics.entry.toFixed(2)} / {metrics.stop.toFixed(2)} / {metrics.take.toFixed(2)}</strong>
                  <small>risk-reward {metrics.riskReward == null ? "—" : metrics.riskReward.toFixed(2)}x</small>
                </div>
                <div className="command-stage-stat">
                  <span>Leverage</span>
                  <strong>{metrics.leverage}x</strong>
                  <small>exposure estimada {metrics.exposure == null ? "—" : metrics.exposure.toFixed(3)}</small>
                </div>
                <div className="command-stage-stat">
                  <span>Win rate</span>
                  <strong>{metrics.winRatePct == null ? "—" : `${metrics.winRatePct.toFixed(1)}%`}</strong>
                  <small>closed trades {metrics.closedTrades} · wins {metrics.closedWins}</small>
                </div>
              </div>
            </article>

            <aside className="command-rail">
              <article className="rail-card rail-card--positive">
                <span>Realized PnL</span>
                <strong className={metrics.realizedPnl >= 0 ? "positive" : "negative"}>{metrics.realizedPnl.toFixed(2)}</strong>
                <small>posiciones cerradas</small>
              </article>
              <article className="rail-card">
                <span>Unrealized PnL</span>
                <strong className={metrics.unrealizedPnl >= 0 ? "positive" : "negative"}>{metrics.unrealizedPnl.toFixed(2)}</strong>
                <small>posición abierta</small>
              </article>
              <article className="rail-card">
                <span>Fees</span>
                <strong>{metrics.estimatedFees.toFixed(4)}</strong>
                <small>estimadas a 0.04%</small>
              </article>
            </aside>
          </div>
        </section>

        <section className="signal-wall" id="performance">
          <article className="signal-card signal-card--wide">
            <p className="eyebrow">Performance</p>
            <h3>{metrics.netPnl >= 0 ? "net positive" : "net negative"}</h3>
            <p>PNL neto, drawdown y riesgo-beneficio para evaluar la calidad de la operación sin ruido.</p>
            <div className="signal-meta-row">
              <span>net pnl {metrics.netPnl.toFixed(2)}</span>
              <span>drawdown {metrics.maxDrawdownPct == null ? "—" : `${metrics.maxDrawdownPct.toFixed(2)}%`}</span>
              <span>win rate {metrics.winRatePct == null ? "—" : `${metrics.winRatePct.toFixed(1)}%`}</span>
            </div>
          </article>
          <article className="signal-card"><p>Leverage</p><h3>{metrics.leverage}x</h3><small>posición / margen</small></article>
          <article className="signal-card"><p>Fees</p><h3>{metrics.estimatedFees.toFixed(4)}</h3><small>estimadas</small></article>
          <article className="signal-card"><p>Risk reward</p><h3>{metrics.riskReward == null ? "—" : `${metrics.riskReward.toFixed(2)}x`}</h3><small>TP vs SL</small></article>
          <article className="signal-card"><p>Realized</p><h3 className={metrics.realizedPnl >= 0 ? "positive" : "negative"}>{metrics.realizedPnl.toFixed(2)}</h3><small>cerrado</small></article>
        </section>

        <section id="orders" className="workspace-section workspace-two-up">
          <article className="panel workstation-panel">
            <div className="section-head"><div><p className="eyebrow">Orders</p><h3>Historial de órdenes</h3></div></div>
            <div className="compact-list">
              {(operation.order_history ?? []).length === 0 ? <p className="empty-state">Sin órdenes.</p> : operation.order_history.map((order: any) => (
                <article key={order.id} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${order.status === "filled" ? "ok" : order.status === "rejected" ? "danger" : "warn"}`}>{order.status}</span>
                    <small>#{order.id} · {order.venue}</small>
                  </div>
                  <p>Px {order.price.toFixed(2)} · exec {order.executed_quantity.toFixed(3)} / {order.quantity.toFixed(3)}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="panel workstation-panel">
            <div className="section-head"><div><p className="eyebrow">Position</p><h3>Historial de posiciones</h3></div></div>
            <div className="compact-list">
              {(operation.position_history ?? []).length === 0 ? <p className="empty-state">Sin posiciones.</p> : operation.position_history.map((position: any) => (
                <article key={position.id} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${position.status === "open" ? "ok" : "neutral"}`}>{position.status}</span>
                    <small>#{position.id}</small>
                  </div>
                  <p>Entry {position.entry_price.toFixed(2)} · Mark {position.mark_price.toFixed(2)} · PnL {position.unrealized_pnl.toFixed(2)}</p>
                </article>
              ))}
            </div>
          </article>
        </section>

        <section id="risk" className="workspace-section workspace-two-up">
          <article className="panel workstation-panel">
            <div className="section-head"><div><p className="eyebrow">Risk</p><h3>Eventos de riesgo</h3></div></div>
            <div className="compact-list">
              {(operation.risk_event_history ?? []).length === 0 ? <p className="empty-state">Sin eventos.</p> : operation.risk_event_history.map((event: any) => (
                <article key={event.id} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${event.severity === "critical" ? "danger" : event.severity === "warning" ? "warn" : "ok"}`}>{event.severity}</span>
                    <small>{event.event_type}</small>
                  </div>
                  <p>{event.message}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="panel workstation-panel">
            <div className="section-head"><div><p className="eyebrow">Timeline</p><h3>Timeline operacional</h3></div></div>
            <div className="compact-list">
              {(operation.timeline_history ?? []).length === 0 ? <p className="empty-state">Sin timeline.</p> : operation.timeline_history.map((item: any, index: number) => (
                <article key={`${item.event_kind}-${index}`} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${item.tone === "danger" ? "danger" : item.tone === "warn" ? "warn" : "ok"}`}>{item.entity_kind}</span>
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
