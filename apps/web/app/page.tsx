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
    risk_event_count: number;
    latest_risk_severity: string | null;
    latest_risk_event_type: string | null;
    latest_risk_message: string | null;
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

function formatNumber(value: number | null | undefined, digits = 0) {
  if (value == null) return "—";
  return new Intl.NumberFormat("es-CL", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "short",
    timeStyle: "short",
    hour12: false,
  }).format(new Date(value));
}

function formatPercent(value: number | null | undefined, digits = 2) {
  if (value == null || Number.isNaN(value)) return "—";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatNumber(value, digits)}%`;
}


function statusTone(status: string) {
  const normalized = status.toLowerCase();
  if (["filled", "testnet_executed", "paper_executed", "approved", "open"].includes(normalized)) return "ok";
  if (["warning", "partially_filled", "blocked", "draft", "new"].includes(normalized)) return "warn";
  if (["critical", "rejected", "cancelled", "canceled", "expired"].includes(normalized)) return "danger";
  return "neutral";
}

function toneClassName(tone: string) {
  if (["ok", "warn", "danger", "neutral"].includes(tone)) return tone;
  return "neutral";
}

function timelineEntityLabel(entityKind: string) {
  switch (entityKind) {
    case "trade_plan":
      return "trade plan";
    case "risk_event":
      return "risk";
    case "reconciliation":
      return "reconcile";
    default:
      return entityKind;
  }
}

function reconcileTone(healthy: boolean, severity: string | null) {
  if (healthy) return "ok";
  if (severity === "critical") return "danger";
  if (severity === "warning") return "warn";
  return "neutral";
}

export default async function HomePage() {
  const commandCenter = await getCommandCenter();
  const { summary, shadow_run: shadowRun } = commandCenter;
  const timelineByTradePlan = new Map<number, typeof commandCenter.timeline>();
  for (const item of commandCenter.timeline) {
    if (item.trade_plan_id == null) continue;
    const current = timelineByTradePlan.get(item.trade_plan_id) ?? [];
    current.push(item);
    timelineByTradePlan.set(item.trade_plan_id, current);
  }

  const cards = [
    { title: "Trade plans", value: String(summary.trade_plans_total), hint: "Planes persistidos" },
    { title: "Aprobados", value: String(summary.approved_trade_plans), hint: "Listos para ejecución" },
    { title: "Paper ejecutados", value: String(summary.paper_executed_trade_plans), hint: "Simulación operativa" },
    { title: "Testnet ejecutados", value: String(summary.testnet_executed_trade_plans), hint: "Órdenes reales en testnet" },
    { title: "Posiciones abiertas", value: String(summary.open_positions), hint: "Inventario operativo vivo" },
    { title: "Fill rate testnet", value: `${formatNumber(shadowRun.testnet_fill_rate_pct, 1)}%`, hint: "Órdenes llenadas / órdenes testnet" },
  ];

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Binance USDⓈ-M Futures</p>
          <h1>Centro de mando del bot algorítmico</h1>
          <p className="lead">
            Visibilidad operativa unificada de planes, órdenes, posiciones, riesgo y shadow run testnet desde una sola pantalla.
          </p>
        </div>
        <div className="status-box">
          <span className="badge">Shadow run activo</span>
          <p>
            Generado: <strong>{formatDate(commandCenter.generated_at)}</strong>
          </p>
          <div className="status-metrics">
            <div>
              <span className="metric-label">Días observados</span>
              <strong>{formatNumber(shadowRun.shadow_run_duration_days, 2)}</strong>
            </div>
            <div>
              <span className="metric-label">Pares comparados</span>
              <strong>{shadowRun.compared_pairs}</strong>
            </div>
            <div>
              <span className="metric-label">Risk 7d</span>
              <strong>{shadowRun.critical_risk_events_7d}/{shadowRun.warning_risk_events_7d}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-six">
        {cards.map((card) => (
          <article key={card.title} className="card">
            <p className="card-title">{card.title}</p>
            <h2>{card.value}</h2>
            <p className="card-hint">{card.hint}</p>
          </article>
        ))}
      </section>

      <section className="panel panel-highlight">
        <div className="panel-header stacked">
          <div>
            <h3>Shadow run / readiness</h3>
            <p className="panel-copy">Snapshot operativo para seguir el avance real hacia el gate testnet.</p>
          </div>
          <div className="chip-row">
            <span className="badge subtle">Paper: {shadowRun.paper_executed_trade_plans}</span>
            <span className="badge subtle">Testnet: {shadowRun.testnet_executed_trade_plans}</span>
            <span className="badge subtle">Unmatched: {shadowRun.unmatched_paper}/{shadowRun.unmatched_testnet}</span>
          </div>
        </div>
        <div className="stats-grid">
          <article className="mini-stat"><span>Órdenes testnet</span><strong>{shadowRun.testnet_orders_total}</strong></article>
          <article className="mini-stat"><span>Órdenes filled</span><strong>{shadowRun.testnet_orders_filled}</strong></article>
          <article className="mini-stat"><span>Slippage promedio</span><strong>{formatNumber(shadowRun.avg_testnet_slippage_bps, 2)} bps</strong></article>
          <article className="mini-stat"><span>Risk events total</span><strong>{summary.risk_events_total}</strong></article>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Radar de operaciones</h3>
            <p className="panel-copy">Cada fila consolida plan, orden, posición, riesgo y reconciliación para seguimiento operativo real.</p>
          </div>
          <span className="badge subtle">últimas 12 ejecuciones / setups</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Plan</th>
                <th>Setup</th>
                <th>Orden</th>
                <th>Posición</th>
                <th>Reconcile</th>
                <th>Riesgo</th>
                <th>Creado</th>
              </tr>
            </thead>
            <tbody>
              {commandCenter.operation_snapshots.length === 0 ? (
                <tr><td colSpan={7} className="empty">Sin operaciones consolidadas.</td></tr>
              ) : commandCenter.operation_snapshots.map((operation) => (
                <tr key={operation.trade_plan_id}>
                  <td>
                    <a className="drill-link" href={`#trade-plan-${operation.trade_plan_id}`}>
                      <strong>#{operation.trade_plan_id}</strong>
                    </a><br />
                    {operation.symbol} · {operation.side}<br />
                    <span className={`status-pill ${statusTone(operation.status)}`}>{operation.status}</span>
                  </td>
                  <td>
                    Regime: {operation.market_regime}<br />
                    Entry/SL/TP: {formatNumber(operation.entry_price, 2)} / {formatNumber(operation.stop_loss, 2)} / {formatNumber(operation.take_profit, 2)}<br />
                    Score: {formatNumber(operation.aggregate_score, 2)} · Risk: {formatNumber(operation.applied_risk_pct, 3)}% · Max: {formatNumber(operation.max_position_notional, 2)}
                  </td>
                  <td>
                    {operation.latest_order_id ? (
                      <>
                        #{operation.latest_order_id} · {operation.latest_order_venue}<br />
                        <span className={`status-pill ${statusTone(operation.latest_order_status ?? "neutral")}`}>{operation.latest_order_status ?? "—"}</span><br />
                        Px/Exec: {formatNumber(operation.latest_order_price, 2)} / {formatNumber(operation.latest_order_executed_quantity, 3)}
                      </>
                    ) : "Sin orden"}
                  </td>
                  <td>
                    {operation.latest_position_id ? (
                      <>
                        #{operation.latest_position_id} · <span className={`status-pill ${statusTone(operation.latest_position_status ?? "neutral")}`}>{operation.latest_position_status ?? "—"}</span><br />
                        Qty: {formatNumber(operation.latest_position_quantity, 3)}<br />
                        Entry/Mark: {formatNumber(operation.latest_position_entry_price, 2)} / {formatNumber(operation.latest_position_mark_price, 2)}<br />
                        <span className={(operation.latest_position_unrealized_pnl ?? 0) >= 0 ? "positive" : "negative"}>PnL: {formatNumber(operation.latest_position_unrealized_pnl, 2)}</span>
                      </>
                    ) : "Sin posición"}
                  </td>
                  <td>
                    <span className={`status-pill ${reconcileTone(operation.reconciliation_healthy, operation.reconciliation_primary_severity)}`}>
                      {operation.reconciliation_healthy ? "healthy" : operation.reconciliation_primary_event ?? "drift"}
                    </span><br />
                    {operation.reconciliation_primary_message ?? "Sin drift detectado"}
                  </td>
                  <td>
                    {operation.latest_risk_event_type ? (
                      <>
                        <span className={`status-pill ${statusTone(operation.latest_risk_severity ?? "neutral")}`}>{operation.latest_risk_severity ?? "info"}</span><br />
                        {operation.latest_risk_event_type}<br />
                        <small>{operation.latest_risk_message}</small><br />
                        Count: {operation.risk_event_count}
                      </>
                    ) : `Sin eventos · Count: ${operation.risk_event_count}`}
                  </td>
                  <td>{formatDate(operation.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Detalle por trade plan</h3>
            <p className="panel-copy">Ficha operativa completa para las últimas operaciones visibles en el radar.</p>
          </div>
          <span className="badge subtle">drill-down operativo</span>
        </div>
        <div className="detail-grid">
          {commandCenter.operation_snapshots.length === 0 ? (
            <p className="empty">Sin detalles de operaciones recientes.</p>
          ) : commandCenter.operation_snapshots.slice(0, 6).map((operation) => {
            const relatedTimeline = (timelineByTradePlan.get(operation.trade_plan_id) ?? []).slice(0, 4);
            const actualEntry = operation.latest_position_entry_price ?? operation.latest_order_price ?? null;
            const entryDiffPct = actualEntry != null && operation.entry_price > 0
              ? ((actualEntry - operation.entry_price) / operation.entry_price) * 100
              : null;
            return (
              <article key={operation.trade_plan_id} id={`trade-plan-${operation.trade_plan_id}`} className="detail-card">
                <div className="detail-card-header">
                  <div>
                    <h4>Trade plan #{operation.trade_plan_id} · {operation.symbol}</h4>
                    <p>{operation.side} · {operation.market_regime} · creado {formatDate(operation.created_at)}</p>
                  </div>
                  <div className="chip-row">
                    <span className={`status-pill ${statusTone(operation.status)}`}>{operation.status}</span>
                    <span className={`status-pill ${reconcileTone(operation.reconciliation_healthy, operation.reconciliation_primary_severity)}`}>
                      {operation.reconciliation_healthy ? "healthy" : operation.reconciliation_primary_event ?? "drift"}
                    </span>
                    <span className="status-pill neutral">risk count: {operation.risk_event_count}</span>
                  </div>
                </div>
                <div className="detail-columns">
                  <section className="detail-box">
                    <h5>Setup</h5>
                    <ul className="detail-list">
                      <li><span>Score</span><strong>{formatNumber(operation.aggregate_score, 2)}</strong></li>
                      <li><span>Risk</span><strong>{formatNumber(operation.applied_risk_pct, 3)}%</strong></li>
                      <li><span>Max notional</span><strong>{formatNumber(operation.max_position_notional, 2)}</strong></li>
                      <li><span>Entry</span><strong>{formatNumber(operation.entry_price, 2)}</strong></li>
                      <li><span>Stop loss</span><strong>{formatNumber(operation.stop_loss, 2)}</strong></li>
                      <li><span>Take profit</span><strong>{formatNumber(operation.take_profit, 2)}</strong></li>
                    </ul>
                  </section>
                  <section className="detail-box">
                    <h5>Ejecución</h5>
                    <ul className="detail-list">
                      <li><span>Orden</span><strong>{operation.latest_order_id ? `#${operation.latest_order_id}` : '—'}</strong></li>
                      <li><span>Venue</span><strong>{operation.latest_order_venue ?? '—'}</strong></li>
                      <li><span>Estado orden</span><strong>{operation.latest_order_status ?? '—'}</strong></li>
                      <li><span>Px orden</span><strong>{formatNumber(operation.latest_order_price, 2)}</strong></li>
                      <li><span>Exec qty</span><strong>{formatNumber(operation.latest_order_executed_quantity, 3)}</strong></li>
                      <li><span>Posición</span><strong>{operation.latest_position_id ? `#${operation.latest_position_id}` : '—'}</strong></li>
                      <li><span>Estado posición</span><strong>{operation.latest_position_status ?? '—'}</strong></li>
                      <li><span>Qty posición</span><strong>{formatNumber(operation.latest_position_quantity, 3)}</strong></li>
                      <li><span>Entry real</span><strong>{formatNumber(actualEntry, 2)}</strong></li>
                      <li><span>Δ vs plan</span><strong className={entryDiffPct == null ? 'muted' : entryDiffPct >= 0 ? 'positive' : 'negative'}>{formatPercent(entryDiffPct, 3)}</strong></li>
                      <li><span>Mark</span><strong>{formatNumber(operation.latest_position_mark_price, 2)}</strong></li>
                      <li><span>PnL</span><strong className={(operation.latest_position_unrealized_pnl ?? 0) >= 0 ? 'positive' : 'negative'}>{formatNumber(operation.latest_position_unrealized_pnl, 2)}</strong></li>
                    </ul>
                  </section>
                  <section className="detail-box">
                    <h5>Justificación técnica</h5>
                    <ul className="detail-list">
                      <li><span>Technical</span><strong>{formatNumber(operation.technical_score, 2)}</strong></li>
                      <li><span>Fundamental</span><strong>{formatNumber(operation.fundamental_score, 2)}</strong></li>
                      <li><span>Sentiment</span><strong>{formatNumber(operation.sentiment_score, 2)}</strong></li>
                      <li><span>Confidence</span><strong>{formatNumber(operation.confidence_score, 2)}</strong></li>
                    </ul>
                    <div className="thesis-box">
                      <strong>Tesis persistida</strong>
                      <p>{operation.thesis || 'Sin tesis persistida'}</p>
                    </div>
                  </section>
                </div>
                <section className="detail-box detail-box-timeline">
                  <h5>Timeline asociada</h5>
                  <div className="detail-timeline">
                    {relatedTimeline.length === 0 ? (
                      <p className="empty">Sin eventos asociados en timeline.</p>
                    ) : relatedTimeline.map((item, index) => (
                      <div key={`${operation.trade_plan_id}-${item.entity_kind}-${index}`} className="detail-timeline-item">
                        <span className={`status-pill ${toneClassName(item.tone)}`}>{timelineEntityLabel(item.entity_kind)}</span>
                        <div>
                          <strong>{item.title}</strong>
                          <p>{item.detail}</p>
                          <small>{item.event_kind} · {formatDate(item.occurred_at)}</small>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </article>
            );
          })}
        </div>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-header">
            <h3>Línea de tiempo operativa</h3>
            <span className="badge subtle">últimos 20 eventos</span>
          </div>
          <div className="risk-feed timeline-feed">
            {commandCenter.timeline.length === 0 ? (
              <p className="empty">Sin eventos en timeline.</p>
            ) : commandCenter.timeline.map((item, index) => (
              <article key={`${item.entity_kind}-${item.trade_plan_id ?? 'na'}-${item.event_kind}-${index}`} className="risk-item timeline-item">
                <div className="risk-item-top">
                  <span className={`status-pill ${toneClassName(item.tone)}`}>{timelineEntityLabel(item.entity_kind)}</span>
                  <span className="risk-meta">{item.event_kind} · {formatDate(item.occurred_at)}</span>
                </div>
                <p>{item.title}</p>
                <small>{item.detail}</small>
                <small className="timeline-meta">
                  {item.trade_plan_id ? (
                    <a className="drill-link" href={`#trade-plan-${item.trade_plan_id}`}>
                      plan #{item.trade_plan_id} · {item.symbol ?? '—'}
                    </a>
                  ) : (
                    `plan #— · ${item.symbol ?? '—'}`
                  )}
                </small>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>Órdenes recientes</h3>
            <span className="badge subtle">exchange execution</span>
          </div>
          <div className="table-wrap">
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
                  <tr><td colSpan={7} className="empty">Sin órdenes recientes.</td></tr>
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
        </section>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-header">
            <h3>Posiciones abiertas</h3>
            <span className="badge subtle">inventory</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Posición</th>
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
                  <tr><td colSpan={7} className="empty">Sin posiciones abiertas.</td></tr>
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
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>Eventos de riesgo</h3>
            <span className="badge subtle">últimos 12</span>
          </div>
          <div className="risk-feed">
            {commandCenter.recent_risk_events.length === 0 ? (
              <p className="empty">Sin eventos recientes.</p>
            ) : commandCenter.recent_risk_events.map((event) => (
              <article key={event.id} className="risk-item">
                <div className="risk-item-top">
                  <span className={`status-pill ${statusTone(event.severity)}`}>{event.severity}</span>
                  <span className="risk-meta">{event.event_type} · {formatDate(event.created_at)}</span>
                </div>
                <p>{event.message}</p>
                <small>trade_plan_id: {event.trade_plan_id ?? "—"}</small>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
