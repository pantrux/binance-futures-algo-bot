from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, RiskEvent, TradePlan
from apps.api.app.schemas.shadow_run_reporting import ShadowRunSummary, ShadowRunSymbolSummary

MAX_PAIRING_DELTA_SECONDS = 86_400


class ShadowRunReportingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _pct_diff(lhs: float, rhs: float) -> float:
        if lhs == 0 and rhs == 0:
            return 0.0
        if lhs == 0 or rhs == 0:
            return 100.0
        baseline = abs(lhs)
        return round(abs(lhs - rhs) / baseline * 100, 4)

    def _pair_plans(self, plans: list[TradePlan]) -> dict:
        paper_queue = deque(plan for plan in plans if plan.status == "paper_executed")
        testnet_queue = [plan for plan in plans if plan.status == "testnet_executed"]

        entry_diffs: list[float] = []
        risk_diffs: list[float] = []
        notional_diffs: list[float] = []
        compared_pairs = 0
        unmatched_paper = 0

        while paper_queue and testnet_queue:
            paper = paper_queue.popleft()

            candidates: list[tuple[int, float]] = []
            for idx, candidate in enumerate(testnet_queue):
                if candidate.side != paper.side:
                    continue
                delta_seconds = abs((candidate.created_at - paper.created_at).total_seconds())
                if delta_seconds > MAX_PAIRING_DELTA_SECONDS:
                    continue
                candidates.append((idx, delta_seconds))

            if not candidates:
                unmatched_paper += 1
                continue

            match_index = min(candidates, key=lambda item: item[1])[0]
            testnet = testnet_queue.pop(match_index)
            compared_pairs += 1
            entry_diffs.append(self._pct_diff(paper.entry_price, testnet.entry_price))
            risk_diffs.append(self._pct_diff(paper.applied_risk_pct, testnet.applied_risk_pct))
            notional_diffs.append(self._pct_diff(paper.max_position_notional, testnet.max_position_notional))

        unmatched_paper += len(paper_queue)
        unmatched_testnet = len(testnet_queue)

        return {
            "paper_executed_trade_plans": sum(1 for plan in plans if plan.status == "paper_executed"),
            "testnet_executed_trade_plans": sum(1 for plan in plans if plan.status == "testnet_executed"),
            "compared_pairs": compared_pairs,
            "unmatched_paper": unmatched_paper,
            "unmatched_testnet": unmatched_testnet,
            "entry_diffs": entry_diffs,
            "risk_diffs": risk_diffs,
            "notional_diffs": notional_diffs,
        }

    def _build_symbol_summary(self, *, symbol: str, plans: list[TradePlan]) -> tuple[ShadowRunSymbolSummary, dict]:
        paired = self._pair_plans(plans)
        return (
            ShadowRunSymbolSummary(
                symbol=symbol,
                paper_executed_trade_plans=paired["paper_executed_trade_plans"],
                testnet_executed_trade_plans=paired["testnet_executed_trade_plans"],
                compared_pairs=paired["compared_pairs"],
                unmatched_paper=paired["unmatched_paper"],
                unmatched_testnet=paired["unmatched_testnet"],
                avg_entry_price_diff_pct=round(sum(paired["entry_diffs"]) / len(paired["entry_diffs"]), 4)
                if paired["entry_diffs"]
                else None,
                avg_applied_risk_diff_pct=round(sum(paired["risk_diffs"]) / len(paired["risk_diffs"]), 4)
                if paired["risk_diffs"]
                else None,
                avg_max_notional_diff_pct=round(sum(paired["notional_diffs"]) / len(paired["notional_diffs"]), 4)
                if paired["notional_diffs"]
                else None,
            ),
            paired,
        )

    def build_summary(self, *, window_days: int = 30) -> ShadowRunSummary:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=window_days)
        risk_cutoff_7d = now - timedelta(days=7)
        risk_cutoff_30d = now - timedelta(days=30)

        plans = (
            self.db.query(TradePlan)
            .filter(TradePlan.status.in_(["paper_executed", "testnet_executed"]))
            .filter(TradePlan.created_at >= cutoff)
            .order_by(TradePlan.symbol.asc(), TradePlan.created_at.asc())
            .all()
        )

        plans_by_symbol: dict[str, list[TradePlan]] = defaultdict(list)
        for plan in plans:
            plans_by_symbol[plan.symbol].append(plan)

        symbol_summaries: list[ShadowRunSymbolSummary] = []
        all_entry_diffs: list[float] = []
        all_risk_diffs: list[float] = []
        all_notional_diffs: list[float] = []
        for symbol, symbol_plans in sorted(plans_by_symbol.items()):
            symbol_summary, paired = self._build_symbol_summary(symbol=symbol, plans=symbol_plans)
            symbol_summaries.append(symbol_summary)
            all_entry_diffs.extend(paired["entry_diffs"])
            all_risk_diffs.extend(paired["risk_diffs"])
            all_notional_diffs.extend(paired["notional_diffs"])

        testnet_orders = (
            self.db.query(Order, TradePlan.entry_price)
            .join(TradePlan, TradePlan.id == Order.trade_plan_id)
            .filter(Order.is_testnet.is_(True))
            .filter(Order.venue == "binance_futures_testnet")
            .filter(TradePlan.status == "testnet_executed")
            .filter(Order.created_at >= cutoff)
            .all()
        )
        testnet_orders_total = len(testnet_orders)
        testnet_orders_filled = sum(1 for order, _ in testnet_orders if order.status == "filled")
        testnet_fill_rate_pct = (
            round(testnet_orders_filled / testnet_orders_total * 100, 4) if testnet_orders_total > 0 else None
        )

        slippage_bps: list[float] = []
        for order, planned_entry_price in testnet_orders:
            if order.status != "filled" or planned_entry_price == 0:
                continue
            slippage_bps.append(round(abs(order.price - planned_entry_price) / planned_entry_price * 10000, 4))

        risk_events_7d = (
            self.db.query(RiskEvent)
            .filter(RiskEvent.created_at >= risk_cutoff_7d)
            .filter(RiskEvent.severity.in_(["warning", "critical"]))
            .all()
        )
        risk_events_30d = (
            self.db.query(RiskEvent)
            .filter(RiskEvent.created_at >= risk_cutoff_30d)
            .filter(RiskEvent.severity.in_(["warning", "critical"]))
            .all()
        )

        shadow_run_start_at = min((plan.created_at for plan in plans), default=None)
        shadow_run_end_at = max((plan.created_at for plan in plans), default=None)
        shadow_run_duration_days = 0.0
        if shadow_run_start_at is not None and shadow_run_end_at is not None:
            shadow_run_duration_days = round((shadow_run_end_at - shadow_run_start_at).total_seconds() / 86400, 4)

        return ShadowRunSummary(
            evaluated_at=now,
            window_days=window_days,
            shadow_run_start_at=shadow_run_start_at,
            shadow_run_end_at=shadow_run_end_at,
            shadow_run_duration_days=shadow_run_duration_days,
            paper_executed_trade_plans=sum(summary.paper_executed_trade_plans for summary in symbol_summaries),
            testnet_executed_trade_plans=sum(summary.testnet_executed_trade_plans for summary in symbol_summaries),
            compared_pairs=sum(summary.compared_pairs for summary in symbol_summaries),
            unmatched_paper=sum(summary.unmatched_paper for summary in symbol_summaries),
            unmatched_testnet=sum(summary.unmatched_testnet for summary in symbol_summaries),
            avg_entry_price_diff_pct=round(sum(all_entry_diffs) / len(all_entry_diffs), 4) if all_entry_diffs else None,
            avg_applied_risk_diff_pct=round(sum(all_risk_diffs) / len(all_risk_diffs), 4) if all_risk_diffs else None,
            avg_max_notional_diff_pct=round(sum(all_notional_diffs) / len(all_notional_diffs), 4) if all_notional_diffs else None,
            testnet_orders_total=testnet_orders_total,
            testnet_orders_filled=testnet_orders_filled,
            testnet_fill_rate_pct=testnet_fill_rate_pct,
            avg_testnet_slippage_bps=round(sum(slippage_bps) / len(slippage_bps), 4) if slippage_bps else None,
            critical_risk_events_7d=sum(1 for event in risk_events_7d if event.severity == "critical"),
            warning_risk_events_7d=sum(1 for event in risk_events_7d if event.severity == "warning"),
            total_risk_events_30d=len(risk_events_30d),
            avg_risk_events_per_day_30d=round(len(risk_events_30d) / 30, 4),
            symbols=symbol_summaries,
        )
