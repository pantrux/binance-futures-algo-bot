from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.app.db.models import RiskEvent, TradePlan
from apps.api.app.schemas.production_reporting import AlertEvaluationResponse, AlertItem, DailyProductionSummary


class ProductionReportingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def daily_summary(self) -> DailyProductionSummary:
        total = self.db.query(func.count(TradePlan.id)).scalar() or 0
        approved = self.db.query(func.count(TradePlan.id)).filter(TradePlan.status == "approved").scalar() or 0
        blocked = self.db.query(func.count(TradePlan.id)).filter(TradePlan.status == "blocked").scalar() or 0
        paper_executed = self.db.query(func.count(TradePlan.id)).filter(TradePlan.status == "paper_executed").scalar() or 0
        testnet_executed = self.db.query(func.count(TradePlan.id)).filter(TradePlan.status == "testnet_executed").scalar() or 0

        avg_score = self.db.query(func.avg(TradePlan.aggregate_score)).scalar()
        avg_score_rounded = round(float(avg_score), 4) if avg_score is not None else None

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        critical_24h = (
            self.db.query(func.count(RiskEvent.id))
            .filter(RiskEvent.created_at >= cutoff)
            .filter(RiskEvent.severity == "critical")
            .scalar()
            or 0
        )
        warning_24h = (
            self.db.query(func.count(RiskEvent.id))
            .filter(RiskEvent.created_at >= cutoff)
            .filter(RiskEvent.severity == "warning")
            .scalar()
            or 0
        )

        return DailyProductionSummary(
            total_trade_plans=int(total),
            approved_trade_plans=int(approved),
            blocked_trade_plans=int(blocked),
            paper_executed_trade_plans=int(paper_executed),
            testnet_executed_trade_plans=int(testnet_executed),
            avg_aggregate_score=avg_score_rounded,
            critical_risk_events_24h=int(critical_24h),
            warning_risk_events_24h=int(warning_24h),
        )

    def evaluate_alerts(self) -> AlertEvaluationResponse:
        summary = self.daily_summary()
        alerts: list[AlertItem] = []

        if summary.critical_risk_events_24h >= 5:
            alerts.append(
                AlertItem(
                    severity="critical",
                    category="risk_events",
                    message=f"Se detectaron {summary.critical_risk_events_24h} eventos críticos en las últimas 24h",
                )
            )

        if summary.blocked_trade_plans > summary.approved_trade_plans and summary.total_trade_plans >= 5:
            alerts.append(
                AlertItem(
                    severity="warning",
                    category="trade_plan_conversion",
                    message="La tasa de bloqueo supera aprobaciones en el período observado",
                )
            )

        if summary.testnet_executed_trade_plans == 0 and summary.paper_executed_trade_plans > 0:
            alerts.append(
                AlertItem(
                    severity="warning",
                    category="execution_mode",
                    message="Hay ejecuciones paper pero ninguna ejecución testnet",
                )
            )

        if summary.avg_aggregate_score is not None and summary.avg_aggregate_score < 55:
            alerts.append(
                AlertItem(
                    severity="warning",
                    category="signal_quality",
                    message=f"Score promedio bajo ({summary.avg_aggregate_score})",
                )
            )

        return AlertEvaluationResponse(alerts=alerts, healthy=len(alerts) == 0)
