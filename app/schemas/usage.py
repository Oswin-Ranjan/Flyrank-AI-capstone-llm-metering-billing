from enum import Enum

from pydantic import BaseModel, Field


class UsageType(str, Enum):
    API_CALL = "API_CALL"
    AI_TOKEN = "AI_TOKEN"


class GenerateRequest(BaseModel):
    usage_type: UsageType
    quantity: int = Field(gt=0)


class GenerateResponse(BaseModel):
    usage_event_id: int
    tenant_id: int
    usage_type: str
    quantity: int
    idempotency_key: str
    status: str
    
class UsageSummaryItem(BaseModel):
    used: int
    limit: int


class UsageResponse(BaseModel):
    api_calls: UsageSummaryItem
    ai_tokens: UsageSummaryItem
    cost: int    