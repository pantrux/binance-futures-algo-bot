"use client";

import { useState } from "react";
import { formatNumber, formatDate, statusTone } from "../lib/formatters";

export function OrderBlotter({ orders }: { orders: any[] }) {
  const [filter, setFilter] = useState("ALL");

  const filteredOrders = filter === "ALL" 
    ? orders 
    : orders.filter((o) => o.status.toUpperCase() === filter);

  return (
    <>
      <div style={{ padding: "0 1rem 1rem", display: "flex", gap: "0.5rem" }}>
        <button 
          onClick={() => setFilter("ALL")} 
          className={`action-link ${filter === "ALL" ? "primary" : ""}`}
          style={{ minHeight: "28px", padding: "0 10px", fontSize: "0.8rem" }}>
          ALL
        </button>
        <button 
          onClick={() => setFilter("NEW")} 
          className={`action-link ${filter === "NEW" ? "primary" : ""}`}
          style={{ minHeight: "28px", padding: "0 10px", fontSize: "0.8rem" }}>
          NEW
        </button>
        <button 
          onClick={() => setFilter("FILLED")} 
          className={`action-link ${filter === "FILLED" ? "primary" : ""}`}
          style={{ minHeight: "28px", padding: "0 10px", fontSize: "0.8rem" }}>
          FILLED
        </button>
        <button 
          onClick={() => setFilter("CANCELED")} 
          className={`action-link ${filter === "CANCELED" ? "primary" : ""}`}
          style={{ minHeight: "28px", padding: "0 10px", fontSize: "0.8rem" }}>
          CANCELED
        </button>
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
              <tr><td colSpan={7} className="empty-state">Sin órdenes recientes ({filter}).</td></tr>
            ) : filteredOrders.map((order: any) => (
              <tr key={order.id}>
                <td>#{order.id}</td>
                <td>#{order.trade_plan_id}</td>
                <td><strong>{order.symbol}</strong></td>
                <td>{order.venue}</td>
                <td>{formatNumber(order.quantity, 3)} / {formatNumber(order.executed_quantity, 3)}</td>
                <td><span className={`status-pill ${statusTone(order.status)}`}>{order.status}</span></td>
                <td>{formatDate(order.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
