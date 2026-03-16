"use client";

import { useState } from "react";
import { formatNumber, formatPercent, formatDate, statusTone, toneClassName, timelineEntityLabel, renderRiskContext } from "../lib/formatters";
import { getActualEntryPrice, type ActualEntryOperation, type LivePriceEntry } from "../lib/trade-utils";

type RiskContext = Record<string, string | number | boolean | null> | null | undefined;

type OrderHistoryItem = {
  id: number;
  status: string;
  created_at: string;
  venue: string | null;
  price: number | null;
  executed_quantity: number | null;
  quantity: number | null;
};

type PositionHistoryItem = {
  id: number;
  status: string;
  opened_at: string;
  entry_price: number | null;
  mark_price: number | null;
  unrealized_pnl: number | null;
};

type RiskEventHistoryItem = {
  id: number;
  severity: string;
  event_type: string;
  created_at: string;
  message: string;
  context?: RiskContext;
};

type TimelineHistoryItem = {
  entity_kind: string;
  tone: string;
  occurred_at: string;
  title: string;
  detail: string;
};

type OperationSnapshot = {
  trade_plan_id: number;
  symbol: string;
  timeframe: string;
  side: string;
  market_regime: string;
  status: string;
  latest_position_entry_price: number | null;
  latest_order_price: number | null;
  latest_order_status: string | null;
  latest_order_executed_quantity: number | null;
  latest_position_unrealized_pnl: number | null;
  aggregate_score: number | null;
  applied_risk_pct: number | null;
  max_position_notional: number | null;
  entry_price: number;
  stop_loss: number | null;
  take_profit: number | null;
  confidence_score: number | null;
  thesis: string | null;
  latest_order_id: number | null;
  latest_order_venue: string | null;
  latest_position_id: number | null;
  risk_event_count: number;
  latest_risk_event_type: string | null;
  reconciliation_healthy: boolean;
  reconciliation_drift_events?: unknown[];
  latest_risk_context?: RiskContext;
  order_history?: OrderHistoryItem[];
  position_history?: PositionHistoryItem[];
  risk_event_history?: RiskEventHistoryItem[];
  timeline_history?: TimelineHistoryItem[];
};

type OperationLiveState = {
  label: string;
  tone: string;
  hint: string;
};

type OperationDrillDownProps = {
  operation: OperationSnapshot;
  index: number;
  livePrice?: LivePriceEntry;
  liveState: OperationLiveState;
};

export function OperationDrillDown({ operation, index, livePrice, liveState }: OperationDrillDownProps) {
  const [activeTab, setActiveTab] = useState("overview");

  const actualEntry = getActualEntryPrice(operation);
  const latestPnl = livePrice && ["open", "testnet_executed", "partially_filled"].includes(operation.status.toLowerCase())
    ? livePrice.unrealizedPnl
    : operation.latest_position_unrealized_pnl;
  const entryDiffPct = actualEntry != null && operation.entry_price > 0
    ? ((actualEntry - operation.entry_price) / operation.entry_price) * 100
    : null;

  const orderHistory = operation.order_history ?? [];
  const positionHistory = operation.position_history ?? [];
  const riskEventHistory = operation.risk_event_history ?? [];
  const timelineHistory = (operation.timeline_history ?? []).slice(0, 12);

  return (
    <details className="operation-drawer" id={`drawer-${operation.trade_plan_id}`} open={index === 0}>
      <summary>
        <div className="drawer-summary-main">
          <strong>#{operation.trade_plan_id} · {operation.symbol}</strong>
          <small>{operation.timeframe} · {operation.side} · {operation.market_regime}</small>
        </div>
        <div className="drawer-summary-stats">
          <span>{formatNumber(actualEntry, 2)}</span>
          <span className={(latestPnl ?? 0) >= 0 ? "positive" : "negative"}>{formatNumber(latestPnl, 2)}</span>
          <span className={`status-pill ${statusTone(operation.status)}`}>{operation.status}</span>
        </div>
      </summary>

      <div className="drawer-tabs">
        <button type="button" aria-pressed={activeTab === "overview"} className={activeTab === "overview" ? "active" : ""} onClick={() => setActiveTab("overview")}>Resumen</button>
        <button type="button" aria-pressed={activeTab === "orders"} className={activeTab === "orders" ? "active" : ""} onClick={() => setActiveTab("orders")}>Órdenes</button>
        <button type="button" aria-pressed={activeTab === "positions"} className={activeTab === "positions" ? "active" : ""} onClick={() => setActiveTab("positions")}>Posición</button>
        <button type="button" aria-pressed={activeTab === "risk"} className={activeTab === "risk" ? "active" : ""} onClick={() => setActiveTab("risk")}>Riesgo</button>
        <button type="button" aria-pressed={activeTab === "timeline"} className={activeTab === "timeline" ? "active" : ""} onClick={() => setActiveTab("timeline")}>Timeline</button>
      </div>

      <div className="drawer-body">
        {activeTab === "overview" && (
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
                <li><span>Feed live</span><strong>{liveState.label}</strong></li>
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

        {activeTab === "orders" && (
          <section className="drawer-panel compact-panel" style={{ gridColumn: "1 / -1" }}>
            <h4>Historial de Órdenes</h4>
            <div className="compact-list">
              {orderHistory.length === 0 ? <p className="empty-state">Sin órdenes.</p> : orderHistory.map((order) => (
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

        {activeTab === "positions" && (
          <section className="drawer-panel compact-panel" style={{ gridColumn: "1 / -1" }}>
            <h4>Historial de Posiciones</h4>
            <div className="compact-list">
              {positionHistory.length === 0 ? <p className="empty-state">Sin posiciones.</p> : positionHistory.map((position) => (
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

        {activeTab === "risk" && (
          <section className="drawer-panel compact-panel" style={{ gridColumn: "1 / -1" }}>
            <h4>Eventos de Riesgo</h4>
            <div className="compact-list">
              {riskEventHistory.length === 0 ? <p className="empty-state">Sin eventos de riesgo.</p> : riskEventHistory.map((event) => (
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

        {activeTab === "timeline" && (
          <section className="drawer-panel compact-panel" style={{ gridColumn: "1 / -1" }}>
            <h4>Línea de tiempo operativa</h4>
            <div className="compact-list">
              {timelineHistory.length === 0 ? <p className="empty-state">Sin timeline.</p> : (
                <>
                  {timelineHistory.map((item, itemIndex) => (
                    <article key={`${operation.trade_plan_id}-${itemIndex}`} className="compact-item">
                      <div className="feed-head">
                        <span className={`status-pill ${toneClassName(item.tone)}`}>{timelineEntityLabel(item.entity_kind)}</span>
                        <small>{formatDate(item.occurred_at)}</small>
                      </div>
                      <p>{item.title}</p>
                      <small className="muted">{item.detail}</small>
                    </article>
                  ))}
                  {(operation.timeline_history?.length ?? 0) > 12 && (
                    <p className="muted">{(operation.timeline_history?.length ?? 0) - 12} entradas adicionales omitidas.</p>
                  )}
                </>
              )}
            </div>
          </section>
        )}
      </div>
    </details>
  );
}
