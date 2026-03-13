from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.app.db.models import RiskEvent, TradePlan
from apps.api.app.schemas.production_reporting import AlertEvaluationResponse, AlertItem, DailyProductionSummary


class ProductionReportingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def daily_summary(self) -> DailyProductionSummary:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        trade_plan_counts = {
            str(status): int(count)
            for status, count in self.db.query(TradePlan.status, func.count(TradePlan.id))
            .group_by(TradePlan.status)
            .all()
        }
        recent_trade_plan_counts = {
            str(status): int(count)
            for status, count in self.db.query(TradePlan.status, func.count(TradePlan.id))
            .filter(TradePlan.created_at >= cutoff)
            .group_by(TradePlan.status)
            .all()
        }

        avg_score = self.db.query(func.avg(TradePlan.aggregate_score)).scalar()
        risk_event_counts_24h = {
            str(severity): int(count)
            for severity, count in self.db.query(RiskEvent.severity, func.count(RiskEvent.id))
            .filter(RiskEvent.created_at >= cutoff)
            .group_by(RiskEvent.severity)
            .all()
        }

        return DailyProductionSummary(
            total_trade_plans=sum(trade_plan_counts.values()),
            approved_trade_plans=trade_plan_counts.get("approved", 0),
            blocked_trade_plans=trade_plan_counts.get("blocked", 0),
            paper_executed_trade_plans=trade_plan_counts.get("paper_executed", 0),
            testnet_executed_trade_plans=trade_plan_counts.get("testnet_executed", 0),
            approved_trade_plans_24h=recent_trade_plan_counts.get("approved", 0),
            blocked_trade_plans_24h=recent_trade_plan_counts.get("blocked", 0),
            paper_executed_trade_plans_24h=recent_trade_plan_counts.get("paper_executed", 0),
            testnet_executed_trade_plans_24h=recent_trade_plan_counts.get("testnet_executed", 0),
            avg_aggregate_score=round(float(avg_score), 4) if avg_score is not None else None,
            critical_risk_events_24h=risk_event_counts_24h.get("critical", 0),
            warning_risk_events_24h=risk_event_counts_24h.get("warning", 0),
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

        recent_conversion_population = summary.approved_trade_plans_24h + summary.blocked_trade_plans_24h
        if summary.blocked_trade_plans_24h > summary.approved_trade_plans_24h and recent_conversion_population >= 5:
            alerts.append(
                AlertItem(
                    severity="warning",
                    category="trade_plan_conversion",
                    message="La tasa de bloqueo en las últimas 24h supera a las aprobaciones",
                )
            )

        if summary.testnet_executed_trade_plans_24h == 0 and summary.paper_executed_trade_plans_24h > 0:
            alerts.append(
                AlertItem(
                    severity="warning",
                    category="execution_mode",
                    message="Hay ejecuciones paper en las últimas 24h pero ninguna ejecución testnet",
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
