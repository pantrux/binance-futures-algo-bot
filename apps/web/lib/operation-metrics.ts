type AnyOperation = any;

function normalizeStatus(value: string | undefined | null) {
  return String(value ?? "").toLowerCase();
}

function normalizeSide(value: string | undefined | null) {
  return String(value ?? "").toLowerCase();
}

function absNumber(value: any) {
  const num = Number(value ?? 0);
  return Number.isFinite(num) ? Math.abs(num) : 0;
}

function toNumber(value: any, fallback = 0) {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

export function getOperationStatusBucket(operation: AnyOperation): "active" | "closed" | "watching" {
  const status = normalizeStatus(operation.status);
  const latestPositionStatus = normalizeStatus(operation.latest_position_status);

  if (["closed", "cancelled", "canceled", "rejected", "expired"].includes(status) || latestPositionStatus === "closed") {
    return "closed";
  }

  if (["approved", "testnet_executed", "paper_executed", "open", "partially_filled"].includes(status) || latestPositionStatus === "open") {
    return "active";
  }

  return "watching";
}

export function getOperationDetailHref(operation: AnyOperation) {
  return `/operations/${operation.trade_plan_id}`;
}

export function computeOperationMetrics(operation: AnyOperation) {
  const side = normalizeSide(operation.side);
  const entry = toNumber(operation.entry_price, 0);
  const stop = toNumber(operation.stop_loss, 0);
  const take = toNumber(operation.take_profit, 0);
  const leverage = Math.max(
    toNumber(operation.latest_position_leverage, 0),
    ...(operation.position_history ?? []).map((position: any) => toNumber(position.leverage, 0)),
    0,
  );

  const positionHistory = [...(operation.position_history ?? [])].sort(
    (a: any, b: any) => new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime(),
  );

  const closedPositions = positionHistory.filter((position: any) => normalizeStatus(position.status) !== "open");
  const realizedPnl = closedPositions.reduce((acc: number, position: any) => acc + toNumber(position.unrealized_pnl, 0), 0);
  const unrealizedPnl = toNumber(operation.latest_position_unrealized_pnl, 0);
  const closedWins = closedPositions.filter((position: any) => toNumber(position.unrealized_pnl, 0) > 0).length;
  const winRatePct = closedPositions.length > 0 ? (closedWins / closedPositions.length) * 100 : null;

  const pnlSeries = positionHistory.map((position: any) => toNumber(position.unrealized_pnl, 0));
  let peak = pnlSeries.length > 0 ? pnlSeries[0] : 0;
  let maxDrawdown = 0;
  for (const pnl of pnlSeries) {
    peak = Math.max(peak, pnl);
    const drawdown = peak - pnl;
    maxDrawdown = Math.max(maxDrawdown, drawdown);
  }
  const maxDrawdownPct = peak > 0 ? (maxDrawdown / peak) * 100 : null;

  const riskPerUnit = side === "short" ? stop - entry : entry - stop;
  const rewardPerUnit = side === "short" ? entry - take : take - entry;
  const riskReward = riskPerUnit !== 0 ? rewardPerUnit / Math.abs(riskPerUnit) : null;

  const filledOrders = (operation.order_history ?? []).filter((order: any) => ["filled", "partially_filled"].includes(normalizeStatus(order.status)));
  const estimatedFees = filledOrders.reduce(
    (acc: number, order: any) => acc + absNumber(order.executed_quantity) * absNumber(order.price) * 0.0004,
    0,
  );

  const netPnl = realizedPnl + unrealizedPnl - estimatedFees;
  const exposure = entry > 0 ? absNumber(operation.max_position_notional) / entry : null;

  return {
    leverage,
    closedTrades: closedPositions.length,
    closedWins,
    winRatePct,
    maxDrawdownPct,
    riskReward,
    realizedPnl,
    unrealizedPnl,
    estimatedFees,
    netPnl,
    exposure,
    entry,
    stop,
    take,
  };
}
