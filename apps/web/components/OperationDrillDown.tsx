"use client";
import { useState } from "react";
import { formatNumber, formatPercent, formatDate, statusTone, toneClassName, timelineEntityLabel, renderRiskContext, reconcileTone } from "../lib/formatters";

export function OperationDrillDown({ operation, index }: { operation: any, index: number }) {
  const [activeTab, setActiveTab] = useState("overview");

  const actualEntry = operation.latest_position_entry_price ?? operation.latest_order_price ?? operation.entry_price;
  const entryDiffPct = operation.entry_price > 0 ? ((actualEntry - operation.entry_price) / operation.entry_price) * 100 : null;

  return (
    <details className="operation-drawer" id={`drawer-${operation.trade_plan_id}`} open={index === 0}>
      <summary>
        <div className="drawer-summary-main">
          <strong>#{operation.trade_plan_id} · {operation.symbol}</strong>
          <small>{operation.timeframe} · {operation.side} · {operation.market_regime}</small>
        </div>
        <div className="drawer-summary-stats">
          <span>{formatNumber(actualEntry, 2)}</span>
          <span className={(operation.latest_position_unrealized_pnl ?? 0) >= 0 ? "positive" : "negative"}>{formatNumber(operation.latest_position_unrealized_pnl, 2)}</span>
          <span className={`status-pill ${statusTone(operation.status)}`}>{operation.status}</span>
        </div>
      </summary>
      
      <div className="drawer-tabs">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>Resumen</button>
        <button className={activeTab === 'orders' ? 'active' : ''} onClick={() => setActiveTab('orders')}>Órdenes</button>
        <button className={activeTab === 'positions' ? 'active' : ''} onClick={() => setActiveTab('positions')}>Posición</button>
        <button className={activeTab === 'risk' ? 'active' : ''} onClick={() => setActiveTab('risk')}>Riesgo</button>
        <button className={activeTab === 'timeline' ? 'active' : ''} onClick={() => setActiveTab('timeline')}>Timeline</button>
      </div>

      <div className="drawer-body">
        {activeTab === 'overview' && (
          <div className="drawer-grid">
            <section className="drawer-panel">
              <h4>Setup</h4>
              <ul className="metric-list">
                <li><span>Score</span><strong>{formatNumber(operation.aggregate_score, 2)}</strong></li>
                <li><span>Risk</span><strong>{formatNumber(operation.applied_risk_pct, 3)}%</strong></li>
                <li><span>Max</span><strong>{formatNumber(operation.max_position_notional, 2)}</strong></li>
                <li><span>Entry / SL / TP</span><strong>{formatNumber(operation.entry_price, 2)} / {formatNumber(operation.stop_loss, 2)} / {formatNumber(operation.take_profit, 2)}</strong></li>
                <li><span>Confidence</span><strong>{formatNumber(operation.confidence_score, 2)}</strong></li>
              </ul>
              <p className="drawer-copy">{operation.thesis || "Sin tesis persistida"}</p>
            </section>

            <section className="drawer-panel">
              <h4>Ejecución</h4>
              <ul className="metric-list">
                <li><span>Orden activa</span><strong>{operation.latest_order_id ? `#${operation.latest_order_id}` : "—"}</strong></li>
                <li><span>Venue</span><strong>{operation.latest_order_venue ?? "—"}</strong></li>
                <li><span>Estado orden</span><strong>{operation.latest_order_status ?? "—"}</strong></li>
                <li><span>Exec qty</span><strong>{formatNumber(operation.latest_order_executed_quantity, 3)}</strong></li>
                <li><span>Posición activa</span><strong>{operation.latest_position_id ? `#${operation.latest_position_id}` : "—"}</strong></li>
                <li><span>Entry real</span><strong>{formatNumber(actualEntry, 2)}</strong></li>
                <li><span>Δ vs plan</span><strong className={entryDiffPct == null ? "muted" : entryDiffPct >= 0 ? "positive" : "negative"}>{formatPercent(entryDiffPct, 3)}</strong></li>
              </ul>
            </section>

            <section className="drawer-panel">
              <h4>Riesgo & reconcile</h4>
              <ul className="metric-list">
                <li><span>Risk count</span><strong>{operation.risk_event_count}</strong></li>
                <li><span>Último risk</span><strong>{operation.latest_risk_event_type ?? "—"}</strong></li>
                <li><span>Healthy</span><strong>{operation.reconciliation_healthy ? "sí" : "no"}</strong></li>
                <li><span>Drifts detectados</span><strong>{operation.reconciliation_drift_events?.length || 0}</strong></li>
              </ul>
              {renderRiskContext(operation.latest_risk_context)}
            </section>
          </div>
        )}

        {activeTab === 'orders' && (
          <section className="drawer-panel compact-panel" style={{gridColumn: '1 / -1'}}>
            <h4>Historial de Órdenes</h4>
            <div className="compact-list">
              {operation.order_history.length === 0 ? <p className="empty-state">Sin órdenes.</p> : operation.order_history.map((order: any) => (
                <article key={order.id} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${statusTone(order.status)}`}>{order.status}</span>
                    <small>#{order.id} · {formatDate(order.created_at)}</small>
                  </div>
                  <p>{order.venue} · Px: {formatNumber(order.price, 2)} · Exec: {formatNumber(order.executed_quantity, 3)} / {formatNumber(order.quantity, 3)}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'positions' && (
          <section className="drawer-panel compact-panel" style={{gridColumn: '1 / -1'}}>
            <h4>Historial de Posiciones</h4>
            <div className="compact-list">
              {operation.position_history.length === 0 ? <p className="empty-state">Sin posiciones.</p> : operation.position_history.map((position: any) => (
                <article key={position.id} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${statusTone(position.status)}`}>{position.status}</span>
                    <small>#{position.id} · {formatDate(position.opened_at)}</small>
                  </div>
                  <p>Entry: {formatNumber(position.entry_price, 2)} / Mark: {formatNumber(position.mark_price, 2)} · PnL {formatNumber(position.unrealized_pnl, 2)}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'risk' && (
          <section className="drawer-panel compact-panel" style={{gridColumn: '1 / -1'}}>
            <h4>Eventos de Riesgo</h4>
            <div className="compact-list">
              {operation.risk_event_history?.length === 0 ? <p className="empty-state">Sin eventos de riesgo.</p> : operation.risk_event_history?.map((event: any) => (
                <article key={event.id} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${statusTone(event.severity)}`}>{event.severity}</span>
                    <small>{event.event_type} · {formatDate(event.created_at)}</small>
                  </div>
                  <p>{event.message}</p>
                  {renderRiskContext(event.context)}
                </article>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'timeline' && (
          <section className="drawer-panel compact-panel" style={{gridColumn: '1 / -1'}}>
            <h4>Línea de tiempo operativa</h4>
            <div className="compact-list">
              {operation.timeline_history.length === 0 ? <p className="empty-state">Sin timeline.</p> : operation.timeline_history.map((item: any, itemIndex: number) => (
                <article key={`${operation.trade_plan_id}-${itemIndex}`} className="compact-item">
                  <div className="feed-head">
                    <span className={`status-pill ${toneClassName(item.tone)}`}>{timelineEntityLabel(item.entity_kind)}</span>
                    <small>{formatDate(item.occurred_at)}</small>
                  </div>
                  <p>{item.title}</p>
                  <small className="muted">{item.detail}</small>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </details>
  );
}
