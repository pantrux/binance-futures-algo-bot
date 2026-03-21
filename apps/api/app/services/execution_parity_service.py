from collections import deque

from sqlalchemy.orm import Session

from apps.api.app.db.models import TradePlan
from apps.api.app.schemas.execution_parity import ExecutionParityReport, ParityPairDiff
from apps.api.app.services.shadow_run_reporting_service import MAX_PAIRING_DELTA_SECONDS


class ExecutionParityService:
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

    def build_report(self, *, symbol: str, timeframe: str | None = None, limit: int = 50) -> ExecutionParityReport:
        query = (
            self.db.query(TradePlan)
            .filter(TradePlan.symbol == symbol)
            .filter(TradePlan.status.in_(["paper_executed", "testnet_executed"]))
        )
        if timeframe is not None:
            query = query.filter(TradePlan.timeframe == timeframe)

        plans = list(reversed(query.order_by(TradePlan.created_at.desc()).limit(limit).all()))

        paper_queue = deque(plan for plan in plans if plan.status == "paper_executed")
        testnet_queue = [plan for plan in plans if plan.status == "testnet_executed"]

        pairs: list[ParityPairDiff] = []
        unmatched_paper = 0
        unmatched_testnet = 0

        while paper_queue and testnet_queue:
            paper = paper_queue.popleft()

            candidates: list[tuple[int, float]] = []
            for idx, candidate in enumerate(testnet_queue):
                if candidate.side != paper.side:
                    continue
                if candidate.timeframe != paper.timeframe:
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
            pairs.append(
                ParityPairDiff(
                    paper_trade_plan_id=paper.id,
                    testnet_trade_plan_id=testnet.id,
                    side=paper.side,
                    entry_price_diff_pct=self._pct_diff(paper.entry_price, testnet.entry_price),
                    applied_risk_diff_pct=self._pct_diff(paper.applied_risk_pct, testnet.applied_risk_pct),
                    max_notional_diff_pct=self._pct_diff(paper.max_position_notional, testnet.max_position_notional),
                )
            )

        unmatched_paper += len(paper_queue)
        unmatched_testnet += len(testnet_queue)

        if not pairs:
            return ExecutionParityReport(
                symbol=symbol,
                timeframe=timeframe,
                compared_pairs=0,
                unmatched_paper=unmatched_paper,
                unmatched_testnet=unmatched_testnet,
                pairs=[],
            )

        avg_entry = round(sum(pair.entry_price_diff_pct for pair in pairs) / len(pairs), 4)
        avg_risk = round(sum(pair.applied_risk_diff_pct for pair in pairs) / len(pairs), 4)
        avg_notional = round(sum(pair.max_notional_diff_pct for pair in pairs) / len(pairs), 4)

        return ExecutionParityReport(
            symbol=symbol,
            timeframe=timeframe,
            compared_pairs=len(pairs),
            unmatched_paper=unmatched_paper,
            unmatched_testnet=unmatched_testnet,
            avg_entry_price_diff_pct=avg_entry,
            avg_applied_risk_diff_pct=avg_risk,
            avg_max_notional_diff_pct=avg_notional,
            pairs=pairs,
        )
