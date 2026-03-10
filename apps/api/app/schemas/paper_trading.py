from pydantic import BaseModel


class PaperExecutionResponse(BaseModel):
    executed: bool
    order_id: int | None = None
    position_id: int | None = None
    reason: str | None = None
