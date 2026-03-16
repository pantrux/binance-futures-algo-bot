export type ActualEntryOperation = {
  latest_position_entry_price: number | null;
  latest_order_price: number | null;
  latest_order_status: string | null;
  latest_order_executed_quantity: number | null;
};

export type LivePriceEntry = {
  markPrice: number | null;
  unrealizedPnl: number | null;
  positionAmt: number | null;
};

export const EXECUTED_ORDER_STATUSES = new Set([
  "filled",
  "partially_filled",
  "testnet_executed",
  "paper_executed",
]);

export function getActualEntryPrice(operation: ActualEntryOperation) {
  const normalizedOrderStatus = String(operation.latest_order_status ?? "").toLowerCase();
  const hasExecutedOrder =
    (operation.latest_order_executed_quantity ?? 0) > 0 ||
    EXECUTED_ORDER_STATUSES.has(normalizedOrderStatus);

  return operation.latest_position_entry_price ?? (hasExecutedOrder ? operation.latest_order_price : null);
}
