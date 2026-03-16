"use client";

import { useMemo, useState } from "react";
import { formatNumber, formatDate, statusTone } from "../lib/formatters";

const ORDER_FILTERS = [
  { value: "ALL", label: "Todas" },
  { value: "NEW", label: "Nuevas" },
  { value: "FILLED", label: "Ejecutadas" },
  { value: "CANCELED", label: "Canceladas" },
] as const;

type OrderFilter = (typeof ORDER_FILTERS)[number]["value"];

export function OrderBlotter({ orders = [] }: { orders?: any[] }) {
  const [filter, setFilter] = useState<OrderFilter>("ALL");

  const filteredOrders = useMemo(() => {
    if (filter === "ALL") {
      return orders;
    }

    return orders.filter((order) => String(order.status ?? "").toUpperCase() === filter);
  }, [filter, orders]);

  const activeFilterLabel = ORDER_FILTERS.find((option) => option.value === filter)?.label ?? filter;

  return (
    <>
      <div style={{ padding: "0 1rem 1rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        {ORDER_FILTERS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setFilter(option.value)}
            className={`action-link ${filter === option.value ? "primary" : ""}`}
            style={{ minHeight: "28px", padding: "0 10px", fontSize: "0.8rem" }}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="table-shell" style={{ maxHeight: "350px", overflowY: "auto" }}>
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
            {filteredOrders.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">
                  Sin órdenes recientes ({activeFilterLabel}).
                </td>
              </tr>
            ) : (
              filteredOrders.map((order: any) => (
                <tr key={order.id}>
                  <td>#{order.id}</td>
                  <td>#{order.trade_plan_id}</td>
                  <td>
                    <strong>{order.symbol}</strong>
                  </td>
                  <td>{order.venue}</td>
                  <td>
                    {formatNumber(order.quantity, 3)} / {formatNumber(order.executed_quantity, 3)}
                  </td>
                  <td>
                    <span className={`status-pill ${statusTone(order.status)}`}>{order.status}</span>
                  </td>
                  <td>{formatDate(order.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
