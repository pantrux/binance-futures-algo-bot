const cards = [
  { title: "Régimen actual", value: "Tendencia alcista moderada", hint: "BTCUSDT · M15/H1" },
  { title: "Riesgo consumido", value: "1.8% / 5%", hint: "Hard cap global activo" },
  { title: "Score compuesto", value: "74/100", hint: "Técnico 78 · Fundamental 61 · Sentimiento 83" },
  { title: "Estado operativo", value: "Paper trading", hint: "Modo seguro antes de producción" },
];

export default function HomePage() {
  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Binance USDⓈ-M Futures</p>
          <h1>Centro de mando del bot algorítmico</h1>
          <p className="lead">
            Motor multi-factor con análisis técnico, fundamental y de sentimiento, documentado en Outline y protegido por un Risk Engine con regla de oro del 5%.
          </p>
        </div>
        <div className="status-box">
          <span className="badge">MVP fundacional</span>
          <p>Arquitectura inicial, motor de riesgo, dashboard base y pipeline CI/CD.</p>
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
        <h3>Flujo operativo previsto</h3>
        <ol>
          <li>Captura de mercado y contexto externo.</li>
          <li>Agregación de señales técnico/fundamental/sentimiento.</li>
          <li>Clasificación de régimen de mercado.</li>
          <li>Generación del plan operativo y validación de riesgo.</li>
          <li>Ejecución controlada + documentación automática en Outline.</li>
        </ol>
      </section>
    </main>
  );
}
