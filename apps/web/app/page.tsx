import { formatNumber, formatPercent, formatDate, statusTone, toneClassName, timelineEntityLabel, renderRiskContext, reconcileTone } from "../lib/formatters";
import { OperationDrillDown } from "../components/OperationDrillDown";

type CommandCenterResponse = {
  generated_at: string;
  summary: {
    trade_plans_total: number;
    approved_trade_plans: number;
    paper_executed_trade_plans: number;
    testnet_executed_trade_plans: number;
    open_positions: number;
    risk_events_total: number;
  };
  shadow_run: {
    shadow_run_duration_days: number;
    paper_executed_trade_plans: number;
    testnet_executed_trade_plans: number;
    compared_pairs: number;
    unmatched_paper: number;
    unmatched_testnet: number;
    testnet_orders_total: number;
    testnet_orders_filled: number;
    testnet_fill_rate_pct: number | null;
    avg_testnet_slippage_bps: number | null;
    critical_risk_events_7d: number;
    warning_risk_events_7d: number;
  };
  operation_snapshots: Array<{
    trade_plan_id: number;
    symbol: string;
    side: string;
    status: string;
    timeframe: string;
    market_regime: string;
    technical_score: number;
    fundamental_score: number;
    sentiment_score: number;
    confidence_score: number;
    aggregate_score: number;
    thesis: string;
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    applied_risk_pct: number;
    max_position_notional: number;
    latest_order_id: number | null;
    latest_order_status: string | null;
    latest_order_venue: string | null;
    latest_order_price: number | null;
    latest_order_executed_quantity: number | null;
    latest_position_id: number | null;
    latest_position_status: string | null;
    latest_position_quantity: number | null;
    latest_position_entry_price: number | null;
    latest_position_mark_price: number | null;
    latest_position_unrealized_pnl: number | null;
    reconciliation_healthy: boolean;
    reconciliation_primary_severity: string | null;
    reconciliation_primary_event: string | null;
    reconciliation_primary_message: string | null;
    reconciliation_order_count: number;
    reconciliation_open_position_count: number;
    reconciliation_filled_order_count: number;
    reconciliation_drift_events: Array<{
      event_type: string;
      severity: string;
      message: string;
    }>;
    reconciliation_recommended_actions: string[];
    risk_event_count: number;
    latest_risk_severity: string | null;
    latest_risk_event_type: string | null;
    latest_risk_message: string | null;
    latest_risk_context: Record<string, string | number | boolean | null>;
    order_history: Array<{
      id: number;
      trade_plan_id: number;
      symbol: string;
      side: string;
      venue: string;
      status: string;
      price: number;
      quantity: number;
      executed_quantity: number;
      created_at: string;
    }>;
    position_history: Array<{
      id: number;
      trade_plan_id: number | null;
      symbol: string;
      side: string;
      quantity: number;
      entry_price: number;
      mark_price: number;
      unrealized_pnl: number;
      leverage: number;
      status: string;
      opened_at: string;
    }>;
    risk_event_history: Array<{
      id: number;
      trade_plan_id: number | null;
      event_type: string;
      severity: string;
      message: string;
      context: Record<string, string | number | boolean | null>;
      created_at: string;
    }>;
    timeline_history: Array<{
      trade_plan_id: number | null;
      symbol: string | null;
      entity_kind: string;
      event_kind: string;
      tone: string;
      title: string;
      detail: string;
      occurred_at: string;
    }>;
    created_at: string;
  }>;
  timeline: Array<{
    trade_plan_id: number | null;
    symbol: string | null;
    entity_kind: string;
    event_kind: string;
    tone: string;
    title: string;
    detail: string;
    occurred_at: string;
  }>;
  recent_trade_plans: Array<{
    id: number;
    symbol: string;
    side: string;
    market_regime: string;
    aggregate_score: number;
    applied_risk_pct: number;
    max_position_notional: number;
    status: string;
    created_at: string;
  }>;
  recent_orders: Array<{
    id: number;
    trade_plan_id: number;
    symbol: string;
    side: string;
    venue: string;
    status: string;
    price: number;
    quantity: number;
    executed_quantity: number;
    created_at: string;
  }>;
  open_positions: Array<{
    id: number;
    trade_plan_id: number | null;
    symbol: string;
    side: string;
    quantity: number;
    entry_price: number;
    mark_price: number;
    unrealized_pnl: number;
    leverage: number;
    status: string;
    opened_at: string;
  }>;
  recent_risk_events: Array<{
    id: number;
    trade_plan_id: number | null;
    event_type: string;
    severity: string;
    message: string;
    context: Record<string, string | number | boolean | null>;
    created_at: string;
  }>;
};

const EMPTY_COMMAND_CENTER: CommandCenterResponse = {
  generated_at: new Date(0).toISOString(),
  summary: {
    trade_plans_total: 0,
    approved_trade_plans: 0,
    paper_executed_trade_plans: 0,
    testnet_executed_trade_plans: 0,
    open_positions: 0,
    risk_events_total: 0,
  },
  shadow_run: {
    shadow_run_duration_days: 0,
    paper_executed_trade_plans: 0,
    testnet_executed_trade_plans: 0,
    compared_pairs: 0,
    unmatched_paper: 0,
    unmatched_testnet: 0,
    testnet_orders_total: 0,
    testnet_orders_filled: 0,
    testnet_fill_rate_pct: null,
    avg_testnet_slippage_bps: null,
    critical_risk_events_7d: 0,
    warning_risk_events_7d: 0,
  },
  operation_snapshots: [],
  timeline: [],
  recent_trade_plans: [],
  recent_orders: [],
  open_positions: [],
  recent_risk_events: [],
};

async function getCommandCenter(): Promise<CommandCenterResponse> {
  const apiUrl = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${apiUrl}/dashboard/command-center`, { cache: "no-store" });
    if (!response.ok) throw new Error("command-center failed");
    return await response.json();
  } catch {
    return EMPTY_COMMAND_CENTER;
  }
}


type TapeItem = {
  key: string;
  symbol: string;
  timeframe: string;
  side: string;
  status: string;
  price: number | null;
  pnl: number | null;
  regime: string | null;
};

function buildTape(commandCenter: CommandCenterResponse): TapeItem[] {
  const map = new Map<string, TapeItem>();

  for (const operation of commandCenter.operation_snapshots) {
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

  for (const position of commandCenter.open_positions) {
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
  const summary = commandCenter.summary;
  const shadowRun = commandCenter.shadow_run;
  const tape = buildTape(commandCenter);
  const totalOpenPnl = commandCenter.open_positions.reduce((acc, position) => acc + position.unrealized_pnl, 0);
  const criticalRisks = commandCenter.recent_risk_events.filter((event) => event.severity === "critical").length;

  const summaryCards = [
    { title: "PnL abierto", value: formatNumber(totalOpenPnl, 2), hint: "mark-to-market actual", tone: totalOpenPnl >= 0 ? "ok" : "danger" },
    { title: "Open positions", value: String(summary.open_positions), hint: "inventario vivo", tone: summary.open_positions > 0 ? "ok" : "neutral" },
    { title: "Fill rate testnet", value: `${formatNumber(shadowRun.testnet_fill_rate_pct, 1)}%`, hint: "órdenes ejecutadas / enviadas", tone: (shadowRun.testnet_fill_rate_pct ?? 0) >= 80 ? "ok" : "warn" },
    { title: "Pairs parity", value: String(shadowRun.compared_pairs), hint: "paper ↔ testnet comparados", tone: shadowRun.compared_pairs > 0 ? "ok" : "neutral" },
    { title: "Risk 7d", value: `${shadowRun.critical_risk_events_7d}/${shadowRun.warning_risk_events_7d}`, hint: "critical / warning", tone: shadowRun.critical_risk_events_7d > 0 ? "danger" : shadowRun.warning_risk_events_7d > 0 ? "warn" : "ok" },
    { title: "Trade plans", value: String(summary.trade_plans_total), hint: "universo persistido", tone: "neutral" },
  ];

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
            <strong>{formatNumber(shadowRun.shadow_run_duration_days, 2)} días</strong>
            <p>Comparados: {shadowRun.compared_pairs} · Unmatched: {shadowRun.unmatched_paper}/{shadowRun.unmatched_testnet}</p>
          </article>
          <article className="sidebar-card">
            <span className={`badge ${criticalRisks > 0 ? "danger" : "ok"}`}>risk feed</span>
            <strong>{summary.risk_events_total} eventos</strong>
            <p>Critical recientes: {criticalRisks}</p>
          </article>
          <article className="sidebar-card subtle-card">
            <span className="badge neutral">snapshot</span>
            <strong>{formatDate(commandCenter.generated_at)}</strong>
            <p>Refresh server-side no-store. Realtime duro queda para el siguiente PR.</p>
          </article>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-header" id="overview">
          <div>
            <p className="eyebrow">Binance USDⓈ-M Futures · Testnet Desk</p>
            <h1>Trading workstation del bot</h1>
            <p className="lead">
              Vista modular para operar el command center como una mesa real: overview corto arriba, paneles especializados al medio y cockpit profundo por operación abajo.
            </p>
          </div>
          <div className="header-status-panel">
            <span className="badge ok pulse">desk online</span>
            <strong>{formatDate(commandCenter.generated_at)}</strong>
            <p>Paper/testnet/risk/reconcile unificados en una sola shell operativa.</p>
          </div>
        </header>

        <section className="ticker-strip" aria-label="market tape">
          {tape.length === 0 ? (
            <div className="ticker-empty">Sin símbolos activos en el snapshot actual.</div>
          ) : tape.map((item) => (
            <article key={item.key} className="ticker-card">
              <div className="ticker-topline">
                <strong>{item.symbol}</strong>
                <span className={`status-pill ${statusTone(item.status)}`}>{item.status}</span>
              </div>
              <div className="ticker-midline">
                <span>{item.timeframe}</span>
                <span>{item.side}</span>
                <span>{item.regime ?? "desk"}</span>
              </div>
              <div className="ticker-bottomline">
                <strong>{formatNumber(item.price, 2)}</strong>
                <span className={item.pnl == null ? "muted" : item.pnl >= 0 ? "positive" : "negative"}>
                  {item.pnl == null ? "—" : formatNumber(item.pnl, 2)}
                </span>
              </div>
            </article>
          ))}
        </section>

        <section className="metric-grid">
          {summaryCards.map((card) => (
            <article key={card.title} className="metric-card">
              <p>{card.title}</p>
              <h3 className={card.tone === "danger" ? "negative" : card.tone === "ok" ? "positive" : undefined}>{card.value}</h3>
              <small>{card.hint}</small>
            </article>
          ))}
        </section>

        <section id="desk" className="workspace-section workspace-two-up">
          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Desk pulse</p>
                <h3>Overview ejecutivo</h3>
              </div>
              <span className="badge subtle">modular shell</span>
            </div>
            <div className="desk-hero-grid">
              <div className="desk-hero-block accent-block">
                <span>Testnet orders</span>
                <strong>{shadowRun.testnet_orders_total}</strong>
                <small>filled {shadowRun.testnet_orders_filled} · slippage {formatNumber(shadowRun.avg_testnet_slippage_bps, 2)} bps</small>
              </div>
              <div className="desk-hero-block">
                <span>Approved queue</span>
                <strong>{summary.approved_trade_plans}</strong>
                <small>planes listos para ejecución / vigilancia</small>
              </div>
              <div className="desk-hero-block">
                <span>Paper / Testnet</span>
                <strong>{summary.paper_executed_trade_plans} / {summary.testnet_executed_trade_plans}</strong>
                <small>baseline parity del snapshot</small>
              </div>
            </div>
          </article>

          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Watchlist</p>
                <h3>Queue operativa</h3>
              </div>
              <span className="badge subtle">últimos setups</span>
            </div>
            <div className="watchlist-grid">
              {commandCenter.recent_trade_plans.length === 0 ? (
                <p className="empty-state">Sin trade plans recientes.</p>
              ) : commandCenter.recent_trade_plans.slice(0, 6).map((plan) => (
                <article key={plan.id} className="watchlist-card">
                  <div className="watchlist-head">
                    <strong>{plan.symbol}</strong>
                    <span className={`status-pill ${statusTone(plan.status)}`}>{plan.status}</span>
                  </div>
                  <p>{plan.side} · {plan.market_regime}</p>
                  <small>score {formatNumber(plan.aggregate_score, 2)} · risk {formatNumber(plan.applied_risk_pct, 3)}%</small>
                  <a className="action-link" href={`#operation-${plan.id}`}>abrir cockpit</a>
                </article>
              ))}
            </div>
          </article>
        </section>

        <section id="operations" className="workspace-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Operations rail</p>
              <h3>Radar modular por operación</h3>
            </div>
            <span className="badge subtle">sin texto estático innecesario</span>
          </div>
          <div className="operation-rail">
            {commandCenter.operation_snapshots.length === 0 ? (
              <p className="empty-state">Sin operaciones consolidadas.</p>
            ) : commandCenter.operation_snapshots.slice(0, 8).map((operation) => {
              const actualEntry = operation.latest_position_entry_price ?? operation.latest_order_price ?? operation.entry_price;
              const entryDiffPct = operation.entry_price > 0 ? ((actualEntry - operation.entry_price) / operation.entry_price) * 100 : null;
              return (
                <article key={operation.trade_plan_id} className="operation-card" id={`operation-${operation.trade_plan_id}`}>
                  <div className="operation-head">
                    <div>
                      <p className="operation-symbol">{operation.symbol}</p>
                      <small>{operation.timeframe} · {operation.side} · {operation.market_regime}</small>
                    </div>
                    <span className={`status-pill ${statusTone(operation.status)}`}>{operation.status}</span>
                  </div>
                  <div className="operation-strip">
                    <div>
                      <span>entry</span>
                      <strong>{formatNumber(actualEntry, 2)}</strong>
                    </div>
                    <div>
                      <span>Δ plan</span>
                      <strong className={entryDiffPct == null ? "muted" : entryDiffPct >= 0 ? "positive" : "negative"}>{formatPercent(entryDiffPct, 3)}</strong>
                    </div>
                    <div>
                      <span>PnL</span>
                      <strong className={(operation.latest_position_unrealized_pnl ?? 0) >= 0 ? "positive" : "negative"}>{formatNumber(operation.latest_position_unrealized_pnl, 2)}</strong>
                    </div>
                  </div>
                  <div className="operation-tags">
                    <span className={`status-pill ${reconcileTone(operation.reconciliation_healthy, operation.reconciliation_primary_severity)}`}>
                      {operation.reconciliation_healthy ? "healthy" : operation.reconciliation_primary_event ?? "drift"}
                    </span>
                    <span className={`status-pill ${statusTone(operation.latest_risk_severity ?? "neutral")}`}>
                      {operation.latest_risk_event_type ?? `risk ${operation.risk_event_count}`}
                    </span>
                  </div>
                  {renderRiskContext(operation.latest_risk_context)}
                  <div className="operation-actions">
                    <a className="action-link primary" href={`#drawer-${operation.trade_plan_id}`}>abrir drill-down</a>
                    <a className="action-link" href="#book">ver book</a>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section id="book" className="workspace-section workspace-two-up">
          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Positions board</p>
                <h3>Posiciones abiertas</h3>
              </div>
              <span className="badge subtle">inventory</span>
            </div>
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Símbolo</th>
                    <th>Lado</th>
                    <th>Qty</th>
                    <th>Entry / Mark</th>
                    <th>PnL</th>
                    <th>Lev</th>
                  </tr>
                </thead>
                <tbody>
                  {commandCenter.open_positions.length === 0 ? (
                    <tr><td colSpan={7} className="empty-state">Sin posiciones abiertas.</td></tr>
                  ) : commandCenter.open_positions.map((position) => (
                    <tr key={position.id}>
                      <td>#{position.id}</td>
                      <td>{position.symbol}</td>
                      <td>{position.side}</td>
                      <td>{formatNumber(position.quantity, 3)}</td>
                      <td>{formatNumber(position.entry_price, 2)} / {formatNumber(position.mark_price, 2)}</td>
                      <td className={position.unrealized_pnl >= 0 ? "positive" : "negative"}>{formatNumber(position.unrealized_pnl, 2)}</td>
                      <td>{position.leverage}x</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Order blotter</p>
                <h3>Órdenes recientes</h3>
              </div>
              <span className="badge subtle">execution feed</span>
            </div>
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Plan</th>
                    <th>Símbolo</th>
                    <th>Venue</th>
                    <th>Qty / Exec</th>
                    <th>Estado</th>
                    <th>Hora</th>
                  </tr>
                </thead>
                <tbody>
                  {commandCenter.recent_orders.length === 0 ? (
                    <tr><td colSpan={7} className="empty-state">Sin órdenes recientes.</td></tr>
                  ) : commandCenter.recent_orders.map((order) => (
                    <tr key={order.id}>
                      <td>#{order.id}</td>
                      <td>#{order.trade_plan_id}</td>
                      <td>{order.symbol}</td>
                      <td>{order.venue}</td>
                      <td>{formatNumber(order.quantity, 3)} / {formatNumber(order.executed_quantity, 3)}</td>
                      <td><span className={`status-pill ${statusTone(order.status)}`}>{order.status}</span></td>
                      <td>{formatDate(order.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        </section>

        <section id="risk" className="workspace-section workspace-two-up">
          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Risk feed</p>
                <h3>Eventos recientes</h3>
              </div>
              <span className="badge subtle">últimos 12</span>
            </div>
            <div className="feed-list">
              {commandCenter.recent_risk_events.length === 0 ? (
                <p className="empty-state">Sin eventos recientes.</p>
              ) : commandCenter.recent_risk_events.map((event) => (
                <article key={event.id} className="feed-card">
                  <div className="feed-head">
                    <span className={`status-pill ${statusTone(event.severity)}`}>{event.severity}</span>
                    <small>{event.event_type} · {formatDate(event.created_at)}</small>
                  </div>
                  <p>{event.message}</p>
                  {renderRiskContext(event.context)}
                </article>
              ))}
            </div>
          </article>

          <article className="panel workstation-panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Timeline</p>
                <h3>Eventos operativos</h3>
              </div>
              <span className="badge subtle">últimos 20</span>
            </div>
            <div className="feed-list">
              {commandCenter.timeline.length === 0 ? (
                <p className="empty-state">Sin eventos en timeline.</p>
              ) : commandCenter.timeline.map((item, index) => (
                <article key={`${item.entity_kind}-${item.trade_plan_id ?? "na"}-${index}`} className="feed-card">
                  <div className="feed-head">
                    <span className={`status-pill ${toneClassName(item.tone)}`}>{timelineEntityLabel(item.entity_kind)}</span>
                    <small>{item.event_kind} · {formatDate(item.occurred_at)}</small>
                  </div>
                  <p>{item.title}</p>
                  <small className="muted">{item.detail}</small>
                </article>
              ))}
            </div>
          </article>
        </section>

        <section id="drilldown" className="workspace-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Cockpit</p>
              <h3>Drill-down por operación</h3>
            </div>
            <span className="badge subtle">plegable / operativo</span>
          </div>
          <div className="drawer-stack">
            {commandCenter.operation_snapshots.length === 0 ? (
              <p className="empty-state">Sin operaciones para drill-down.</p>
            ) : commandCenter.operation_snapshots.slice(0, 8).map((operation, index) => {
              const actualEntry = operation.latest_position_entry_price ?? operation.latest_order_price ?? operation.entry_price;
              const entryDiffPct = operation.entry_price > 0 ? ((actualEntry - operation.entry_price) / operation.entry_price) * 100 : null;
              return (
                <OperationDrillDown key={operation.trade_plan_id} operation={operation} index={index} />
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
}
