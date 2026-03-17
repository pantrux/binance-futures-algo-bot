"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { formatNumber, formatPercent, formatDate, statusTone, toneClassName, timelineEntityLabel, renderRiskContext, reconcileTone } from "../lib/formatters";
import { getActualEntryPrice, type LivePriceEntry } from "../lib/trade-utils";
import { OperationDrillDown } from "./OperationDrillDown";

import { OrderBlotter } from "./OrderBlotter";

const LIVE_POLL_INTERVAL_MS = 4000;
const LIVE_STALE_WARN_MS = LIVE_POLL_INTERVAL_MS * 3;
const LIVE_STALE_DANGER_MS = LIVE_POLL_INTERVAL_MS * 8;
const LIVE_SCOPE_SECTION_IDS = ["desk", "operations", "drilldown"] as const;

type LiveScopeSectionId = (typeof LIVE_SCOPE_SECTION_IDS)[number];

function buildLivePricingUrl() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/$/, "");
  return apiBaseUrl ? `${apiBaseUrl}/dashboard/live-pricing` : null;
}

function formatElapsedMs(value: number) {
  if (value < 1_000) {
    return "ahora";
  }

  const totalSeconds = Math.floor(value / 1_000);
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds === 0 ? `${minutes}m` : `${minutes}m ${seconds}s`;
}

export function LiveWorkstation({ initialData, initialTape, initialOpenPnl }: any) {
  const data = initialData;
  const [livePrices, setLivePrices] = useState<Record<string, LivePriceEntry>>({});
  const [isPolling, setIsPolling] = useState(true);
  const [lastLiveUpdateAt, setLastLiveUpdateAt] = useState<string | null>(null);
  const [livePollingError, setLivePollingError] = useState<string | null>(null);
  const [isLiveRefreshing, setIsLiveRefreshing] = useState(false);
  const [liveRefreshNote, setLiveRefreshNote] = useState<string | null>(null);
  const [liveClockMs, setLiveClockMs] = useState(() => Date.now());
  const [visibleSectionIds, setVisibleSectionIds] = useState<LiveScopeSectionId[]>([...LIVE_SCOPE_SECTION_IDS]);
  const livePricingUrl = buildLivePricingUrl();
  const livePricingRequestUrlRef = useRef<string | null>(null);
  const visibleSymbols = useMemo(() => {
    const scopedSymbols = new Set<string>(data.open_positions.map((position: any) => position.symbol));
    const visibleSectionSet = new Set(visibleSectionIds);

    if (visibleSectionSet.has("desk")) {
      initialTape
        .filter((item: any) => ["open", "testnet_executed", "partially_filled"].includes(String(item.status ?? "").toLowerCase()))
        .forEach((item: any) => scopedSymbols.add(item.symbol));
    }

    if (visibleSectionSet.has("operations") || visibleSectionSet.has("drilldown")) {
      data.operation_snapshots.forEach((operation: any) => scopedSymbols.add(operation.symbol));
    }

    return Array.from(scopedSymbols).sort();
  }, [data.open_positions, data.operation_snapshots, initialTape, visibleSectionIds]);
  const livePricingRequestUrl = useMemo(() => {
    if (!livePricingUrl) {
      return null;
    }

    if (visibleSymbols.length === 0) {
      return null;
    }

    const params = new URLSearchParams();
    visibleSymbols.forEach((symbol) => params.append("symbols", symbol));
    return `${livePricingUrl}?${params.toString()}`;
  }, [livePricingUrl, visibleSymbols]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleSectionIds((current) => {
          const next = new Set(current);

          entries.forEach((entry) => {
            const sectionId = entry.target.id as LiveScopeSectionId;
            if (entry.isIntersecting) {
              next.add(sectionId);
            } else {
              next.delete(sectionId);
            }
          });

          return LIVE_SCOPE_SECTION_IDS.filter((sectionId) => next.has(sectionId));
        });
      },
      { rootMargin: "0px 0px -35% 0px", threshold: 0.2 },
    );

    LIVE_SCOPE_SECTION_IDS.forEach((sectionId) => {
      const element = document.getElementById(sectionId);
      if (element) {
        observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    livePricingRequestUrlRef.current = livePricingRequestUrl;
  }, [livePricingRequestUrl]);

  const refreshLivePricing = useCallback(
    async (mode: "interval" | "manual" = "interval") => {
      const requestUrl = livePricingRequestUrlRef.current;
      if (!requestUrl) {
        setLivePollingError(null);
        if (mode === "manual") {
          setLiveRefreshNote("scope idle: no hay símbolos activos para refrescar");
        }
        return;
      }

      if (mode === "manual") {
        setIsLiveRefreshing(true);
        setLiveRefreshNote(null);
      }

      try {
        const res = await fetch(requestUrl, { cache: "no-store" });
        if (!res.ok) {
          throw new Error(`Live pricing poll failed (${res.status})`);
        }

        const result = await res.json();
        const pricesMap: Record<string, LivePriceEntry> = {};
        (result.positions ?? []).forEach((position: any) => {
          pricesMap[position.symbol] = {
            markPrice: position.mark_price,
            unrealizedPnl: position.unrealized_pnl,
            positionAmt: position.position_amt,
          };
        });

        setLivePrices(pricesMap);
        setLastLiveUpdateAt(new Date().toISOString());
        setLivePollingError(null);
        if (mode === "manual") {
          setLiveRefreshNote(`refresh manual OK · ${Object.keys(pricesMap).length} símbolos live`);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Live pricing poll failed";
        setLivePollingError(message);
        if (mode === "manual") {
          setLiveRefreshNote(`refresh manual falló · ${message}`);
        }
        console.error("Live pricing poll failed:", err);
      } finally {
        if (mode === "manual") {
          setIsLiveRefreshing(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    if (!isPolling || !livePricingUrl) return;

    void refreshLivePricing("interval");
    const interval = setInterval(() => {
      void refreshLivePricing("interval");
    }, LIVE_POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [isPolling, livePricingUrl, refreshLivePricing]);

  useEffect(() => {
    if (!liveRefreshNote) {
      return;
    }

    const timeout = setTimeout(() => {
      setLiveRefreshNote(null);
    }, 5_000);

    return () => clearTimeout(timeout);
  }, [liveRefreshNote]);

  useEffect(() => {
    if (!lastLiveUpdateAt || !isPolling) {
      return;
    }

    const interval = setInterval(() => {
      setLiveClockMs(Date.now());
    }, 1_000);

    return () => clearInterval(interval);
  }, [lastLiveUpdateAt, isPolling]);

  const positions = useMemo(
    () =>
      data.open_positions.map((pos: any) => {
        const live = livePrices[pos.symbol];
        const currentPnl = live ? live.unrealizedPnl : pos.unrealized_pnl;
        const currentMark = live ? live.markPrice : pos.mark_price;

        return { ...pos, unrealized_pnl: currentPnl, mark_price: currentMark };
      }),
    [data.open_positions, livePrices],
  );
  const liveOpenPnl = useMemo(() => {
    if (Object.keys(livePrices).length === 0) {
      return initialOpenPnl;
    }

    return positions.reduce((acc: number, position: any) => acc + (position.unrealized_pnl ?? 0), 0);
  }, [initialOpenPnl, livePrices, positions]);

  // Update tape with live prices
  const tape = initialTape.map((item: any) => {
    const live = livePrices[item.symbol];
    if (live && ["open", "testnet_executed", "partially_filled"].includes(item.status.toLowerCase())) {
      return { ...item, price: live.markPrice, pnl: live.unrealizedPnl };
    }
    return item;
  });

  const summary = data.summary;
  const shadowRun = data.shadow_run;
  const hasLivePrices = Object.keys(livePrices).length > 0;
  const isLivePaused = !isPolling;
  const liveAgeMs = lastLiveUpdateAt ? Math.max(0, liveClockMs - Date.parse(lastLiveUpdateAt)) : null;
  const isLiveStaleDanger = liveAgeMs != null && liveAgeMs >= LIVE_STALE_DANGER_MS;
  const isLiveStaleWarn = liveAgeMs != null && liveAgeMs >= LIVE_STALE_WARN_MS && !isLiveStaleDanger;
  const liveFreshnessValue = liveAgeMs == null ? "—" : formatElapsedMs(liveAgeMs);
  const liveFreshnessHint = isLivePaused
    ? "polling pausado"
    : livePollingError
      ? hasLivePrices ? "error activo con último tick cacheado" : "polling con error"
      : liveAgeMs == null
        ? "sin tick live todavía"
        : isLiveStaleDanger
          ? "feed demasiado viejo"
          : isLiveStaleWarn
            ? "feed envejeciendo"
            : "dentro de ventana fresca";
  const liveBadgeClassName = isLivePaused
    ? hasLivePrices ? "badge warn" : "badge neutral"
    : livePollingError
      ? isLiveStaleDanger ? "badge danger" : hasLivePrices ? "badge warn" : "badge danger"
      : isLiveStaleDanger
        ? "badge danger"
        : isLiveStaleWarn
          ? "badge warn"
          : hasLivePrices ? "badge ok pulse" : livePricingUrl ? "badge warn" : "badge neutral";
  const liveBadgeLabel = isLivePaused
    ? "live pausado"
    : livePollingError
      ? isLiveStaleDanger ? "live crítico" : "live degradado"
      : isLiveStaleDanger
        ? "live vencido"
        : isLiveStaleWarn
          ? "live envejeciendo"
          : hasLivePrices ? "live pricing" : livePricingUrl ? "snapshot data" : "snapshot only";
  const liveScopeLabel = visibleSectionIds.length === 0 ? "idle" : visibleSectionIds.join("+");
  const liveStatusCopy = isLivePaused
    ? lastLiveUpdateAt
      ? `polling pausado · último tick ${formatDate(lastLiveUpdateAt)} · hace ${formatElapsedMs(liveAgeMs ?? 0)}`
      : "polling pausado"
    : livePollingError
      ? lastLiveUpdateAt
        ? `${livePollingError} · último tick ${formatDate(lastLiveUpdateAt)} · hace ${formatElapsedMs(liveAgeMs ?? 0)}`
        : livePollingError
      : isLiveStaleDanger || isLiveStaleWarn
        ? `último tick ${formatDate(lastLiveUpdateAt!)} · feed con ${formatElapsedMs(liveAgeMs ?? 0)} de antigüedad`
        : lastLiveUpdateAt
          ? `último live ${formatDate(lastLiveUpdateAt)} · hace ${formatElapsedMs(liveAgeMs ?? 0)}`
          : livePricingUrl
            ? "esperando primer tick live"
            : "live pricing deshabilitado: falta NEXT_PUBLIC_API_URL";
  const liveCoveredPositions = positions.filter((position: any) => livePrices[position.symbol]).length;
  const liveCoveredOperations = data.operation_snapshots.filter((operation: any) => livePrices[operation.symbol]).length;

  const defaultSnapshotLiveState = useMemo(
    () => ({
      label: "snapshot",
      tone: livePricingUrl ? "warn" : "neutral",
      hint: livePricingUrl ? "sin cobertura live para este símbolo" : "live pricing deshabilitado",
    }),
    [livePricingUrl],
  );

  const symbolLiveStates = useMemo(() => {
    const symbols = new Set<string>([
      ...positions.map((position: any) => position.symbol),
      ...data.operation_snapshots.map((operation: any) => operation.symbol),
    ]);
    const states: Record<string, { label: string; tone: string; hint: string }> = {};

    symbols.forEach((symbol) => {
      const hasSymbolLivePrice = Boolean(livePrices[symbol]);

      if (!hasSymbolLivePrice) {
        states[symbol] = defaultSnapshotLiveState;
        return;
      }

      if (isLivePaused) {
        states[symbol] = {
          label: "live pausado",
          tone: "warn",
          hint: lastLiveUpdateAt ? `último tick hace ${formatElapsedMs(liveAgeMs ?? 0)}` : "polling pausado",
        };
        return;
      }

      if (livePollingError) {
        states[symbol] = {
          label: isLiveStaleDanger ? "live crítico" : "live degradado",
          tone: isLiveStaleDanger ? "danger" : "warn",
          hint: "error activo con último tick cacheado",
        };
        return;
      }

      if (isLiveStaleDanger) {
        states[symbol] = {
          label: "live vencido",
          tone: "danger",
          hint: `último tick hace ${formatElapsedMs(liveAgeMs ?? 0)}`,
        };
        return;
      }

      if (isLiveStaleWarn) {
        states[symbol] = {
          label: "live envejeciendo",
          tone: "warn",
          hint: `último tick hace ${formatElapsedMs(liveAgeMs ?? 0)}`,
        };
        return;
      }

      states[symbol] = {
        label: "live fresco",
        tone: "ok",
        hint: lastLiveUpdateAt ? `último tick hace ${formatElapsedMs(liveAgeMs ?? 0)}` : "live pricing activo",
      };
    });

    return states;
  }, [data.operation_snapshots, defaultSnapshotLiveState, isLivePaused, isLiveStaleDanger, isLiveStaleWarn, lastLiveUpdateAt, liveAgeMs, livePollingError, livePrices, positions]);

  const summaryCards = [
    { title: "PnL abierto", value: formatNumber(liveOpenPnl, 2), hint: "mark-to-market actual", tone: liveOpenPnl >= 0 ? "ok" : "danger" },
    { title: "Open positions", value: String(summary.open_positions), hint: "inventario vivo", tone: summary.open_positions > 0 ? "ok" : "neutral" },
    { title: "Fill rate testnet", value: `${formatNumber(shadowRun.testnet_fill_rate_pct, 1)}%`, hint: "órdenes ejecutadas / enviadas", tone: (shadowRun.testnet_fill_rate_pct ?? 0) >= 80 ? "ok" : "warn" },
    { title: "Pairs parity", value: String(shadowRun.compared_pairs), hint: "paper ↔ testnet comparados", tone: shadowRun.compared_pairs > 0 ? "ok" : "neutral" },
    { title: "Risk 7d", value: `${shadowRun.critical_risk_events_7d}/${shadowRun.warning_risk_events_7d}`, hint: "critical / warning", tone: shadowRun.critical_risk_events_7d > 0 ? "danger" : shadowRun.warning_risk_events_7d > 0 ? "warn" : "ok" },
    { title: "Live freshness", value: liveFreshnessValue, hint: liveFreshnessHint, tone: isLivePaused ? "warn" : isLiveStaleDanger ? "danger" : isLiveStaleWarn || !!livePollingError ? "warn" : hasLivePrices ? "ok" : "neutral" },
    { title: "Live coverage", value: `${liveCoveredPositions}/${positions.length}`, hint: `posiciones con mark live · ${liveCoveredOperations}/${data.operation_snapshots.length} operaciones`, tone: liveCoveredPositions === positions.length && positions.length > 0 ? "ok" : liveCoveredPositions > 0 ? "warn" : "neutral" },
    { title: "Trade plans", value: String(summary.trade_plans_total), hint: "universo persistido", tone: "neutral" },
  ];

  return (
    <>
      <header className="workspace-header" id="overview">
        <div>
          <p className="eyebrow">Binance USDⓈ-M Futures · Testnet Desk</p>
          <h1>Trading workstation del bot</h1>
          <p className="lead">
            Vista modular para operar el command center como una mesa real: overview corto arriba, paneles especializados al medio y cockpit profundo por operación abajo.
          </p>
        </div>
        <div className="header-status-panel">
          <span className={liveBadgeClassName}>{liveBadgeLabel}</span>
          <strong>{formatDate(data.generated_at)}</strong>
          <p>{liveStatusCopy}</p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button type="button" className="action-link" onClick={() => void refreshLivePricing("manual")} disabled={isLiveRefreshing}>
              {isLiveRefreshing ? "refrescando..." : "refresh now"}
            </button>
            <button type="button" className="action-link" onClick={() => setIsPolling((current) => !current)}>
              {isPolling ? "pausar live" : "reanudar live"}
            </button>
          </div>
          <small className="muted">poll cada {LIVE_POLL_INTERVAL_MS / 1000}s · scope {visibleSymbols.length || "idle"} símbolos ({liveScopeLabel}) · warn ≥ {LIVE_STALE_WARN_MS / 1000}s · danger ≥ {LIVE_STALE_DANGER_MS / 1000}s</small>
          {liveRefreshNote && <small className="muted">{liveRefreshNote}</small>}
        </div>
      </header>

      <section className="ticker-strip" aria-label="market tape">
        {tape.length === 0 ? (
          <div className="ticker-empty">Sin símbolos activos en el snapshot actual.</div>
        ) : tape.map((item: any) => (
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
            {data.recent_trade_plans.length === 0 ? (
              <p className="empty-state">Sin trade plans recientes.</p>
            ) : data.recent_trade_plans.slice(0, 6).map((plan: any) => (
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
          {data.operation_snapshots.length === 0 ? (
            <p className="empty-state">Sin operaciones consolidadas.</p>
          ) : data.operation_snapshots.slice(0, 8).map((operation: any) => {
            const live = livePrices[operation.symbol];
            const liveState = symbolLiveStates[operation.symbol] ?? defaultSnapshotLiveState;
            let latestPnl = operation.latest_position_unrealized_pnl;
            const actualEntry = getActualEntryPrice(operation);

            if (live && ["open", "testnet_executed", "partially_filled"].includes(operation.status.toLowerCase())) {
              latestPnl = live.unrealizedPnl;
            }

            const entryDiffPct = actualEntry != null && operation.entry_price > 0
              ? ((actualEntry - operation.entry_price) / operation.entry_price) * 100
              : null;
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
                    <span>entry real</span>
                    <strong>{formatNumber(actualEntry, 2)}</strong>
                  </div>
                  <div>
                    <span>Δ plan</span>
                    <strong className={entryDiffPct == null ? "muted" : entryDiffPct >= 0 ? "positive" : "negative"}>{formatPercent(entryDiffPct, 3)}</strong>
                  </div>
                  <div>
                    <span>PnL vivo</span>
                    <strong className={(latestPnl ?? 0) >= 0 ? "positive" : "negative"}>{formatNumber(latestPnl, 2)}</strong>
                  </div>
                </div>
                <div className="operation-tags">
                  <span className={`status-pill ${toneClassName(liveState.tone)}`} title={liveState.hint}>{liveState.label}</span>
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
                {positions.length === 0 ? (
                  <tr><td colSpan={7} className="empty-state">Sin posiciones abiertas.</td></tr>
                ) : positions.map((position: any) => (
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
          <OrderBlotter orders={data.recent_orders} />
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
            {data.recent_risk_events.length === 0 ? (
              <p className="empty-state">Sin eventos recientes.</p>
            ) : data.recent_risk_events.map((event: any) => (
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
            {data.timeline.length === 0 ? (
              <p className="empty-state">Sin eventos en timeline.</p>
            ) : data.timeline.map((item: any, index: number) => (
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
          {data.operation_snapshots.length === 0 ? (
            <p className="empty-state">Sin operaciones para drill-down.</p>
          ) : data.operation_snapshots.slice(0, 8).map((operation: any, index: number) => (
            <OperationDrillDown
              key={operation.trade_plan_id}
              operation={operation}
              index={index}
              livePrice={livePrices[operation.symbol]}
              liveState={symbolLiveStates[operation.symbol] ?? defaultSnapshotLiveState}
              onToggleOpen={(tradePlanId, isOpen) => {
                setOpenDrilldownTradePlanIds((current) => {
                  const next = new Set(current);
                  if (isOpen) {
                    next.add(tradePlanId);
                  } else {
                    next.delete(tradePlanId);
                  }
                  return Array.from(next).sort((a, b) => a - b);
                });
              }}
            />
          ))}
        </div>
      </section>
    </>
  );
}
