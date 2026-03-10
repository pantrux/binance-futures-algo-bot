async function getSummary() {
  const apiUrl = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${apiUrl}/dashboard/summary`, { cache: "no-store" });
    if (!response.ok) throw new Error("summary failed");
    return await response.json();
  } catch {
    return {
      trade_plans_total: 0,
      approved_trade_plans: 0,
      paper_executed_trade_plans: 0,
      open_positions: 0,
      risk_events_total: 0,
    };
  }
}

async function getTradePlans() {
  const apiUrl = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${apiUrl}/trade-plans?limit=5`, { cache: "no-store" });
    if (!response.ok) throw new Error("trade plans failed");
    return await response.json();
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const [summary, tradePlans] = await Promise.all([getSummary(), getTradePlans()]);

  const cards = [
    { title: "Trade plans", value: String(summary.trade_plans_total), hint: "Planes persistidos" },
    { title: "Aprobados", value: String(summary.approved_trade_plans), hint: "Listos para paper trading" },
    { title: "Paper ejecutados", value: String(summary.paper_executed_trade_plans), hint: "Órdenes simuladas creadas" },
    { title: "Posiciones abiertas", value: String(summary.open_positions), hint: "Inventario operativo" },
  ];

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Binance USDⓈ-M Futures</p>
          <h1>Centro de mando del bot algorítmico</h1>
          <p className="lead">
            Arquitectura auditable con persistencia de trade plans, paper trading controlado, base Synology-first y documentación viva en Outline.
          </p>
        </div>
        <div className="status-box">
          <span className="badge">Fase operativa inicial</span>
          <p>Persistencia + Binance Testnet base + paper trading skeleton + dashboard conectado a la API.</p>
        </div>
      </section>

      <section className="grid">
        {cards.map((card) => (
          <article key={card.title} className="card">
            <p className="card-title">{card.title}</p>
            <h2>{card.value}</h2>
            <p className="card-hint">{card.hint}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Últimos trade plans</h3>
          <span className="badge subtle">Risk events: {summary.risk_events_total}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Símbolo</th>
                <th>Lado</th>
                <th>Régimen</th>
                <th>Score</th>
                <th>Riesgo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {tradePlans.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty">Sin datos todavía. El dashboard está listo para leer desde la API.</td>
                </tr>
              ) : (
                tradePlans.map((plan: any) => (
                  <tr key={plan.id}>
                    <td>{plan.id}</td>
                    <td>{plan.symbol}</td>
                    <td>{plan.side}</td>
                    <td>{plan.market_regime}</td>
                    <td>{plan.aggregate_score}</td>
                    <td>{plan.applied_risk_pct}%</td>
                    <td>{plan.status}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
