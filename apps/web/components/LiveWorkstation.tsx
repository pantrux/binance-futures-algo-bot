"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { formatNumber, formatPercent, formatDate, statusTone, toneClassName, timelineEntityLabel, renderRiskContext, reconcileTone } from "../lib/formatters";
import { buildLiveStateLabel, LIVE_STALE_DANGER_MS, LIVE_STALE_WARN_MS } from "../lib/time-format";
import { getActualEntryPrice, type LivePriceEntry } from "../lib/trade-utils";
import { OperationDrillDown } from "./OperationDrillDown";
import { OrderBlotter } from "./OrderBlotter";

function liveEntrySide(positionAmt: number | null | undefined) {
  if (positionAmt == null || positionAmt === 0) {
    return null;
  }
  return positionAmt > 0 ? "LONG" : "SHORT";
}

const LIVE_POLL_INTERVAL_MS = 4000;
const LIVE_SCOPE_SECTION_IDS = ["desk", "operations", "drilldown"] as const;

type LiveScopeSectionId = (typeof LIVE_SCOPE_SECTION_IDS)[number];

function collectVisibleSymbols(data: any, initialTape: any[], visibleSectionIds: LiveScopeSectionId[], openDrilldownTradePlanIds: number[]) {
  const scopedSymbols = new Set<string>(data.open_positions.map((position: any) => position.symbol));
  const visibleSectionSet = new Set(visibleSectionIds);

  if (visibleSectionSet.has("desk")) {
    initialTape
      .filter((item: any) => ["open", "testnet_executed", "partially_filled"].includes(String(item.status ?? "").toLowerCase()))
      .forEach((item: any) => scopedSymbols.add(item.symbol));
  }

  if (visibleSectionSet.has("operations")) {
    data.operation_snapshots.forEach((operation: any) => scopedSymbols.add(operation.symbol));
  }

  if (visibleSectionSet.has("drilldown")) {
    const scopedDrilldownOperations = openDrilldownTradePlanIds.length > 0
      ? data.operation_snapshots.filter((operation: any) => openDrilldownTradePlanIds.includes(operation.trade_plan_id))
      : data.operation_snapshots;
    scopedDrilldownOperations.forEach((operation: any) => scopedSymbols.add(operation.symbol));
  }

  return Array.from(scopedSymbols).sort();
}

function buildLivePricingUrl(symbols: string[]) {
  const params = new URLSearchParams();
  symbols.forEach((symbol) => params.append("symbols", symbol));
  const query = params.toString();
  return query ? `/api/live-pricing?${query}` : "/api/live-pricing";
}

function buildLivePricingStreamUrl(symbols: string[]) {
  const params = new URLSearchParams();
  symbols.forEach((symbol) => params.append("symbols", symbol));
  const query = params.toString();
  return query ? `/api/live-pricing/stream?${query}` : "/api/live-pricing/stream";
}

export function LiveWorkstation({ initialData, initialTape, initialOpenPnl }: any) {
  const data = initialData;
  const [livePrices, setLivePrices] = useState<Record<string, Array<LivePriceEntry & { side: string | null }>>>({});
  const [liveQuotes, setLiveQuotes] = useState<Record<string, { markPrice: number }>>({});
  const [isPolling, setIsPolling] = useState(true);
  const [lastLiveUpdateAt, setLastLiveUpdateAt] = useState<string | null>(null);
  const [livePollingError, setLivePollingError] = useState<string | null>(null);
  const [isLiveRefreshing, setIsLiveRefreshing] = useState(false);
  const [liveRefreshNote, setLiveRefreshNote] = useState<string | null>(null);
  const [liveScopeNote, setLiveScopeNote] = useState<string | null>(null);
  const [visibleSectionIds, setVisibleSectionIds] = useState<LiveScopeSectionId[]>([...LIVE_SCOPE_SECTION_IDS]);
  const [openDrilldownTradePlanIds, setOpenDrilldownTradePlanIds] = useState<number[]>(() =>
    initialData?.operation_snapshots?.[0]?.trade_plan_id ? [initialData.operation_snapshots[0].trade_plan_id] : [],
  );
  const livePricingRequestUrlRef = useRef<string | null>(null);
  const visibleSymbols = useMemo(
    () => collectVisibleSymbols(data, initialTape, visibleSectionIds, openDrilldownTradePlanIds),
    [data, initialTape, openDrilldownTradePlanIds, visibleSectionIds],
  );
  const livePricingRequestUrl = useMemo(() => buildLivePricingUrl(visibleSymbols), [visibleSymbols]);
  const livePricingStreamUrl = useMemo(() => buildLivePricingStreamUrl(visibleSymbols), [visibleSymbols]);

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

  const applyLivePayload = useCallback((result: any) => {
    const pricesMap: Record<string, Array<LivePriceEntry & { side: string | null }>> = {};
    const quotesMap: Record<string, { markPrice: number }> = {};

    (result.quotes ?? []).forEach((quote: any) => {
      if (!quote?.symbol) {
        return;
      }
      quotesMap[quote.symbol] = {
        markPrice: quote.mark_price,
      };
    });

    (result.positions ?? []).forEach((position: any) => {
      if (!position?.symbol) {
        return;
      }
      if (!pricesMap[position.symbol]) {
        pricesMap[position.symbol] = [];
      }
      pricesMap[position.symbol].push({
        markPrice: position.mark_price,
        unrealizedPnl: position.unrealized_pnl,
        positionAmt: position.position_amt,
        side: liveEntrySide(position.position_amt),
      });
      if (!quotesMap[position.symbol]) {
        quotesMap[position.symbol] = {
          markPrice: position.mark_price,
        };
      }
    });

    setLivePrices(pricesMap);
    setLiveQuotes(quotesMap);
    setLastLiveUpdateAt(typeof result.timestamp === "string" && !Number.isNaN(Date.parse(result.timestamp)) ? result.timestamp : new Date().toISOString());
    setLivePollingError(null);
  }, []);

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
        applyLivePayload(result);
        if (mode === "manual") {
          const liveCount = Array.isArray(result.quotes) ? result.quotes.length : Array.isArray(result.positions) ? result.positions.length : 0;
          setLiveRefreshNote(`refresh manual OK · ${liveCount} símbolos live`);
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
    [applyLivePayload],
  );

  useEffect(() => {
    if (!isPolling || !livePricingStreamUrl) {
      return;
    }

    const eventSource = new EventSource(livePricingStreamUrl);

    eventSource.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (!message?.ok) {
          setLivePollingError(message?.error ?? "Live pricing stream failed");
          return;
        }
        applyLivePayload(message.payload);
      } catch (error) {
        setLivePollingError(error instanceof Error ? error.message : "Live pricing stream parse failed");
      }
    };

    eventSource.onerror = () => {
      setLivePollingError((current) => current ?? "Live pricing stream disconnected");
    };

    return () => {
      eventSource.close();
    };
  }, [applyLivePayload, isPolling, livePricingStreamUrl]);

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
    if (!liveScopeNote) {
      return;
    }

    const timeout = setTimeout(() => {
      setLiveScopeNote(null);
    }, 5_000);

    return () => clearTimeout(timeout);
  }, [liveScopeNote]);


  const positions = useMemo(
    () =>
      data.open_positions.map((pos: any) => {
        const liveRows = livePrices[pos.symbol] ?? [];
        const live = liveRows.find((entry) => entry.side === String(pos.side ?? "").toUpperCase()) ?? liveRows[0];
        const liveQuote = liveQuotes[pos.symbol];
        const currentPnl = live ? live.unrealizedPnl : pos.unrealized_pnl;
        const currentMark = liveQuote ? liveQuote.markPrice : live ? live.markPrice : pos.mark_price;

        return { ...pos, unrealized_pnl: currentPnl, mark_price: currentMark };
      }),
    [data.open_positions, livePrices, liveQuotes],
  );
  const liveOpenPnl = useMemo(() => {
    if (Object.keys(livePrices).length === 0) {
      return initialOpenPnl;
    }

    return positions.reduce((acc: number, position: any) => acc + (position.unrealized_pnl ?? 0), 0);
  }, [initialOpenPnl, livePrices, positions]);

  // Update tape with live prices
  const tape = initialTape.map((item: any) => {
    const liveRows = livePrices[item.symbol] ?? [];
    const live = liveRows.find((entry) => entry.side === String(item.side ?? "").toUpperCase()) ?? liveRows[0];
    const liveQuote = liveQuotes[item.symbol];
    if (liveQuote && ["open", "testnet_executed", "partially_filled"].includes(item.status.toLowerCase())) {
      return { ...item, price: liveQuote.markPrice, pnl: live ? live.unrealizedPnl : item.pnl };
    }
    return item;
  });

  const summary = data.summary;
  const shadowRun = data.shadow_run;
  const hasLivePrices = Object.keys(liveQuotes).length > 0;
  const isLivePaused = !isPolling;
  const liveAgeMs = lastLiveUpdateAt ? Math.max(0, Date.now() - Date.parse(lastLiveUpdateAt)) : null;
  const isLiveStaleDanger = liveAgeMs != null && liveAgeMs >= LIVE_STALE_DANGER_MS;
  const isLiveStaleWarn = liveAgeMs != null && liveAgeMs >= LIVE_STALE_WARN_MS && !isLiveStaleDanger;
  const liveFreshnessValue = lastLiveUpdateAt ? formatDate(lastLiveUpdateAt) : "—";
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
            : "último tick reciente";
  const liveBadgeClassName = isLivePaused
    ? hasLivePrices ? "badge warn" : "badge neutral"
    : livePollingError
      ? isLiveStaleDanger ? "badge danger" : hasLivePrices ? "badge warn" : "badge danger"
      : isLiveStaleDanger
        ? "badge danger"
        : isLiveStaleWarn
          ? "badge warn"
          : hasLivePrices ? "badge ok pulse" : "badge warn";
  const liveBadgeLabel = isLivePaused
    ? buildLiveStateLabel("live pausado", liveAgeMs)
    : livePollingError
      ? buildLiveStateLabel(isLiveStaleDanger ? "live crítico" : "live degradado", liveAgeMs)
      : isLiveStaleDanger
        ? buildLiveStateLabel("live vencido", liveAgeMs)
        : isLiveStaleWarn
          ? buildLiveStateLabel("live envejeciendo", liveAgeMs)
          : hasLivePrices ? buildLiveStateLabel("live pricing", liveAgeMs) : "snapshot data";
  const liveScopeLabel = visibleSectionIds.length === 0 ? "idle" : visibleSectionIds.join("+");
  const liveScopeSymbolsLabel = visibleSymbols.length === 0 ? "sin símbolos en scope" : `scope symbols: ${visibleSymbols.join(", ")}`;
  const openDrilldownOperations = useMemo(
    () => data.operation_snapshots.filter((operation: any) => openDrilldownTradePlanIds.includes(operation.trade_plan_id)),
    [data.operation_snapshots, openDrilldownTradePlanIds],
  );
  const liveScopeDriverLabel = !visibleSectionIds.includes("drilldown")
    ? "driver: scope guiado por secciones visibles"
    : openDrilldownTradePlanIds.length === 0
      ? "driver: drill-down visible sin drawers abiertos; fallback a todas las operaciones"
      : `driver: drill-down aporta ${openDrilldownOperations.length} drawer(s) abierto(s) al scope → ${openDrilldownOperations.map((operation: any) => `#${operation.trade_plan_id} ${operation.symbol}`).join(", ")}`;
  const liveStatusCopy = isLivePaused
    ? lastLiveUpdateAt
      ? `polling pausado · último tick ${formatDate(lastLiveUpdateAt)}`
      : "polling pausado"
    : livePollingError
      ? lastLiveUpdateAt
        ? `${livePollingError} · último tick ${formatDate(lastLiveUpdateAt)}`
        : livePollingError
      : isLiveStaleDanger || isLiveStaleWarn
        ? `último tick ${formatDate(lastLiveUpdateAt!)} · feed desfasado`
        : lastLiveUpdateAt
          ? `último live ${formatDate(lastLiveUpdateAt)}`
          : "esperando primer tick live";
  const liveCoveredPositions = positions.filter((position: any) => liveQuotes[position.symbol]).length;
  const liveCoveredOperations = data.operation_snapshots.filter((operation: any) => liveQuotes[operation.symbol]).length;
  const snapshotRelativeAgeLabel = null;
  const lastLiveTickLabel = lastLiveUpdateAt ? formatDate(lastLiveUpdateAt) : "—";
  const lastLiveTickHint = lastLiveUpdateAt
    ? `timestamp backend de /dashboard/live-pricing · ${liveFreshnessHint}`
    : `${liveFreshnessHint} · esperando timestamp backend del feed`;

  const defaultSnapshotLiveState = useMemo(
    () => ({
      label: "snapshot",
      tone: "warn",
      hint: "sin cobertura live para este símbolo",
    }),
    [],
  );

  const symbolLiveStates = useMemo(() => {
    const symbols = new Set<string>([
      ...positions.map((position: any) => position.symbol),
      ...data.operation_snapshots.map((operation: any) => operation.symbol),
    ]);
    const states: Record<string, { label: string; tone: string; hint: string }> = {};

    symbols.forEach((symbol) => {
      const hasSymbolLivePrice = Boolean(liveQuotes[symbol]);

      if (!hasSymbolLivePrice) {
        states[symbol] = defaultSnapshotLiveState;
        return;
      }

      if (isLivePaused) {
        states[symbol] = {
          label: buildLiveStateLabel("live pausado", liveAgeMs),
          tone: "warn",
          hint: lastLiveUpdateAt ? `último tick ${formatDate(lastLiveUpdateAt)}` : "polling pausado",
        };
        return;
      }

      if (livePollingError) {
        states[symbol] = {
          label: buildLiveStateLabel(isLiveStaleDanger ? "live crítico" : "live degradado", liveAgeMs),
          tone: isLiveStaleDanger ? "danger" : "warn",
          hint: "error activo con último tick cacheado",
        };
        return;
      }

      if (isLiveStaleDanger) {
        states[symbol] = {
          label: buildLiveStateLabel("live vencido", liveAgeMs),
          tone: "danger",
          hint: lastLiveTickLabel,
        };
        return;
      }

      if (isLiveStaleWarn) {
        states[symbol] = {
          label: buildLiveStateLabel("live envejeciendo", liveAgeMs),
          tone: "warn",
          hint: lastLiveTickLabel,
        };
        return;
      }

      states[symbol] = {
        label: buildLiveStateLabel("live fresco", liveAgeMs),
        tone: "ok",
        hint: lastLiveUpdateAt ? lastLiveTickLabel : "live pricing activo",
      };
    });

    return states;
  }, [data.operation_snapshots, defaultSnapshotLiveState, isLivePaused, isLiveStaleDanger, isLiveStaleWarn, lastLiveTickLabel, lastLiveUpdateAt, liveAgeMs, livePollingError, liveQuotes, positions]);

  const summaryCards = [
    { title: "PnL abierto", value: formatNumber(liveOpenPnl, 2), hint: "mark-to-market actual", tone: liveOpenPnl >= 0 ? "ok" : "danger" },
    { title: "Open positions", value: String(summary.open_positions), hint: "inventario vivo", tone: summary.open_positions > 0 ? "ok" : "neutral" },
    { title: "Fill rate testnet", value: `${formatNumber(shadowRun.testnet_fill_rate_pct, 1)}%`, hint: "órdenes ejecutadas / enviadas", tone: (shadowRun.testnet_fill_rate_pct ?? 0) >= 80 ? "ok" : "warn" },
    { title: "Pairs parity", value: String(shadowRun.compared_pairs), hint: "paper ↔ testnet comparados", tone: shadowRun.compared_pairs > 0 ? "ok" : "neutral" },
    { title: "Risk 7d", value: `${shadowRun.critical_risk_events_7d}/${shadowRun.warning_risk_events_7d}`, hint: "critical / warning", tone: shadowRun.critical_risk_events_7d > 0 ? "danger" : shadowRun.warning_risk_events_7d > 0 ? "warn" : "ok" },
    { title: "Live freshness", value: liveFreshnessValue, hint: liveFreshnessHint, tone: isLivePaused ? "warn" : isLiveStaleDanger ? "danger" : isLiveStaleWarn || !!livePollingError ? "warn" : hasLivePrices ? "ok" : "neutral" },
  ];

  const commandBoard = {
    marketTone: isLivePaused ? (hasLivePrices ? "warn" : "neutral") : livePollingError ? (isLiveStaleDanger ? "danger" : hasLivePrices ? "warn" : "danger") : isLiveStaleDanger ? "danger" : isLiveStaleWarn ? "warn" : hasLivePrices ? "ok" : "warn",
    coveragePercent: positions.length > 0 ? Math.round((liveCoveredPositions / positions.length) * 100) : 0,
    freshnessPercent: liveAgeMs == null ? 0 : isLiveStaleDanger ? 100 : isLiveStaleWarn ? 65 : 18,
    riskPercent: Math.min(100, (shadowRun.critical_risk_events_7d * 22) + (shadowRun.warning_risk_events_7d * 6)),
    fillPercent: Math.max(0, Math.min(100, Number(shadowRun.testnet_fill_rate_pct ?? 0))),
  };

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
          <strong>{formatDate(data.generated_at)}{snapshotRelativeAgeLabel ? ` · ${snapshotRelativeAgeLabel}` : ""}</strong>
          <p>{liveStatusCopy}</p>
          <small className="muted">poll cada {LIVE_POLL_INTERVAL_MS / 1000}s · scope {visibleSymbols.length || "idle"} símbolos ({liveScopeLabel}) · warn ≥ {LIVE_STALE_WARN_MS / 1000}s · danger ≥ {LIVE_STALE_DANGER_MS / 1000}s</small>
          <small className="muted">{liveScopeSymbolsLabel}</small>
          <small className="muted">{liveScopeDriverLabel}</small>
          {liveScopeNote && <small className="muted">{liveScopeNote}</small>}
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

      <section className="command-grid" aria-label="command pulse">
        <article className="command-stage panel workstation-panel">
          <div className="command-stage-copy">
            <p className="eyebrow">Command pulse</p>
            <h2>Panel de decisión</h2>
            <p className="lead compact-lead">
              Una lectura compacta del estado real: qué está vivo, qué está cubierto, qué está envejeciendo y qué exige atención ahora mismo.
            </p>
            <div className="command-chip-row">
              <span className={`badge ${commandBoard.marketTone}`}>{liveBadgeLabel}</span>
              <span className="badge subtle">{liveScopeSymbolsLabel}</span>
              <span className="badge subtle">{liveScopeDriverLabel}</span>
            </div>
            <p className="command-hero-copyline">{liveStatusCopy}</p>
            <div className="command-actions">
              <button type="button" className="action-link primary" onClick={() => void refreshLivePricing("manual")} disabled={isLiveRefreshing}>
                {isLiveRefreshing ? "refrescando..." : "refresh now"}
              </button>
              <button type="button" className="action-link" onClick={() => setIsPolling((current) => !current)}>
                {isPolling ? "pausar live" : "reanudar live"}
              </button>
            </div>
          </div>

          <div className="command-stage-summary">
            <div className="command-stage-stat">
              <span>Live coverage</span>
              <strong>{liveCoveredPositions}/{positions.length || 0}</strong>
              <small>{liveCoveredOperations}/{data.operation_snapshots.length} operaciones con mark live</small>
            </div>
            <div className="command-stage-stat">
              <span>Freshness</span>
              <strong>{liveFreshnessValue}</strong>
              <small>{lastLiveTickHint}</small>
            </div>
            <div className="command-stage-stat">
              <span>Risk load</span>
              <strong>{shadowRun.critical_risk_events_7d + shadowRun.warning_risk_events_7d}</strong>
              <small>{shadowRun.critical_risk_events_7d} critical · {shadowRun.warning_risk_events_7d} warning</small>
            </div>
          </div>
        </article>

        <aside className="command-rail">
          <article className="rail-card rail-card--positive">
            <span>Execution</span>
            <strong>{formatNumber(commandBoard.fillPercent, 1)}%</strong>
            <small>testnet fill rate · {shadowRun.testnet_orders_filled}/{shadowRun.testnet_orders_total} fills</small>
            <div className="progress-track"><span className="progress-fill ok" style={{ width: `${commandBoard.fillPercent}%` }} /></div>
          </article>
          <article className="rail-card">
            <span>Operational tone</span>
            <strong>{commandBoard.marketTone === "danger" ? "hot" : commandBoard.marketTone === "warn" ? "watch" : "calm"}</strong>
            <small>{summary.approved_trade_plans} approved · {summary.open_positions} open</small>
            <div className="progress-track"><span className={`progress-fill ${commandBoard.marketTone}`} style={{ width: `${commandBoard.coveragePercent}%` }} /></div>
          </article>
          <article className="rail-card">
            <span>Scope</span>
            <strong>{visibleSymbols.length || 0}</strong>
            <small>{liveScopeLabel} · {LIVE_SCOPE_SECTION_IDS.join(" / ")}</small>
          </article>
          <article className="rail-card rail-card--compact">
            <span>Control notes</span>
            <small className="muted">{liveScopeNote || liveRefreshNote || "sin notas activas"}</small>
          </article>
        </aside>
      </section>

      <section className="signal-wall" aria-label="signal wall">
        <article className="signal-card signal-card--wide">
          <p className="eyebrow">Market thesis</p>
          <h3>{liveBadgeLabel}</h3>
          <p>{liveStatusCopy}</p>
          <div className="signal-meta-row">
            <span>coverage {commandBoard.coveragePercent}%</span>
            <span>freshness {commandBoard.freshnessPercent}%</span>
            <span>risk {commandBoard.riskPercent}%</span>
          </div>
        </article>
        {summaryCards.map((card) => (
          <article key={card.title} className="signal-card">
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
            const liveRows = livePrices[operation.symbol] ?? [];
            const live = liveRows.find((entry) => entry.side === String(operation.side ?? "").toUpperCase()) ?? liveRows[0];
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
          ) : data.operation_snapshots.slice(0, 8).map((operation: any, index: number) => {
            const liveRows = livePrices[operation.symbol] ?? [];
            const operationLivePrice = liveRows.find((entry) => entry.side === String(operation.side ?? "").toUpperCase()) ?? liveRows[0];
            return (
            <OperationDrillDown
              key={operation.trade_plan_id}
              operation={operation}
              index={index}
              livePrice={operationLivePrice}
              liveState={symbolLiveStates[operation.symbol] ?? defaultSnapshotLiveState}
              snapshotGeneratedAt={data.generated_at}
              lastLiveUpdateAt={lastLiveUpdateAt}
              onToggleOpen={(tradePlanId, isOpen) => {
                const previousIds = openDrilldownTradePlanIds;
                const next = new Set(previousIds);
                if (isOpen) {
                  next.add(tradePlanId);
                } else {
                  next.delete(tradePlanId);
                }

                const nextIds = Array.from(next).sort((a, b) => a - b);
                const previousSymbols = collectVisibleSymbols(data, initialTape, visibleSectionIds, previousIds);
                const nextSymbols = collectVisibleSymbols(data, initialTape, visibleSectionIds, nextIds);
                const previousScopeKey = previousSymbols.join("|");
                const nextScopeKey = nextSymbols.join("|");

                setOpenDrilldownTradePlanIds(nextIds);
                if (previousScopeKey !== nextScopeKey) {
                  setLiveScopeNote(
                    nextIds.length === 0
                      ? `scope live actualizado: se cerró #${tradePlanId} ${operation.symbol} y drill-down volvió al fallback (${nextSymbols.length} símbolos en scope)`
                      : `scope live actualizado: ${isOpen ? "abierto" : "cerrado"} #${tradePlanId} ${operation.symbol} · ${nextSymbols.length} símbolos en scope · drawers activos ${nextIds.join(", ")}`,
                  );
                }
              }}
            />
            );
          })}
        </div>
      </section>
    </>
  );
}
