from pydantic import BaseModel


class TestnetExecutionResponse(BaseModel):
    executed: bool
    order_id: int | None = None
    position_id: int | None = None
    external_order_id: str | None = None
    stop_order_id: int | None = None
    take_profit_order_id: int | None = None
    reason: str | None = None
