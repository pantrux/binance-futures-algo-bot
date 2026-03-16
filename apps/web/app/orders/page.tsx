export default function Page() {
  return (
    <div className="compact-home">
      <h1 className="page-title" style={{textTransform:'uppercase'}}>orders MODULE</h1>
      <div className="kpi-card">
        <span className="kpi-label">Status</span>
        <span className="kpi-value">IN DEVELOPMENT</span>
      </div>
      <p style={{marginTop: '2rem', color: 'var(--muted)'}}>
        Detailed view for orders will be implemented in subsequent PRs (PR-92+).
      </p>
    </div>
  );
}
