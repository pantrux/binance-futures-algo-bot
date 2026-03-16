export const dynamic = 'force-dynamic';

type CommandCenterResponse = {
  generated_at: string;
  summary: {
    trade_plans_total: number;
    approved_trade_plans: number;
    paper_executed_trade_plans: number;
    testnet_executed_trade_plans: number;
    open_positions: number;
    risk_events_total: number;
  };
  shadow_run: {
    shadow_run_duration_days: number;
    paper_executed_trade_plans: number;
    testnet_executed_trade_plans: number;
    compared_pairs: number;
    unmatched_paper: number;
    unmatched_testnet: number;
    testnet_orders_total: number;
    testnet_orders_filled: number;
    testnet_fill_rate_pct: number | null;
    avg_testnet_slippage_bps: number | null;
    critical_risk_events_7d: number;
    warning_risk_events_7d: number;
  };
};

async function getCommandCenter(): Promise<CommandCenterResponse> {
  const url = process.env.SYNOLOGY_API_BASE_URL
    ? `${process.env.SYNOLOGY_API_BASE_URL}/dashboard/command-center`
    : 'http://192.168.0.8:8010/dashboard/command-center';

  const res = await fetch(url, { next: { revalidate: 5 } });
  if (!res.ok) {
    throw new Error('Failed to fetch command center data');
  }
  return res.json();
}

function formatNumber(num: number | null | undefined, decimals = 2) {
  if (num === null || num === undefined) return '—';
  return num.toLocaleString('es-CL', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('es-CL', {
    timeZone: 'UTC',
    dateStyle: 'short',
    timeStyle: 'medium',
  }) + ' UTC';
}

export default async function HomePage() {
  const commandCenter = await getCommandCenter();
  const { summary, shadow_run: shadowRun } = commandCenter;

  const cards = [
    { title: "Planes persistidos", value: String(summary.trade_plans_total) },
    { title: "Listos ejecución", value: String(summary.approved_trade_plans) },
    { title: "Paper ejecutados", value: String(summary.paper_executed_trade_plans) },
    { title: "Testnet ejecutados", value: String(summary.testnet_executed_trade_plans) },
    { title: "Posiciones abiertas", value: String(summary.open_positions), warn: summary.open_positions > 0 },
    { title: "Fill rate testnet", value: `${formatNumber(shadowRun.testnet_fill_rate_pct, 1)}%` },
  ];

  return (
    <div className="compact-home">
      <h1 className="page-title">SYSTEM STATUS <span style={{fontSize:'0.6em', color:'var(--muted)', float:'right', fontWeight:'normal'}}>Last Update: {formatDate(commandCenter.generated_at)}</span></h1>
      
      <h2 className="section-title">GLOBAL PERFORMANCE</h2>
      <div className="kpi-grid">
        {cards.map((card, i) => (
          <div key={i} className={`kpi-card ${card.warn ? 'kpi-warn' : ''}`}>
            <span className="kpi-label">{card.title}</span>
            <span className="kpi-value">{card.value}</span>
          </div>
        ))}
      </div>
      
      <h2 className="section-title" style={{ marginTop: '2rem' }}>SHADOW RUN TESTNET</h2>
      <div className="kpi-grid">
         <div className="kpi-card">
           <span className="kpi-label">Testnet Orders</span>
           <span className="kpi-value">{shadowRun.testnet_orders_total}</span>
         </div>
         <div className="kpi-card">
           <span className="kpi-label">Avg Slippage (bps)</span>
           <span className="kpi-value">{formatNumber(shadowRun.avg_testnet_slippage_bps, 2)}</span>
         </div>
         <div className="kpi-card">
           <span className="kpi-label">Warning Risks (7d)</span>
           <span className="kpi-value" style={{color: shadowRun.warning_risk_events_7d > 0 ? 'var(--warn)' : 'inherit'}}>{shadowRun.warning_risk_events_7d}</span>
         </div>
         <div className="kpi-card">
           <span className="kpi-label">Critical Risks (7d)</span>
           <span className="kpi-value" style={{color: shadowRun.critical_risk_events_7d > 0 ? 'var(--danger)' : 'inherit'}}>{shadowRun.critical_risk_events_7d}</span>
         </div>
      </div>
    </div>
  );
}
