from enum import Enum

from pydantic import BaseModel, Field, model_validator


class UsageType(str, Enum):
    API_CALL = "API_CALL"
    AI_TOKEN = "AI_TOKEN"


class GenerateRequest(BaseModel):
    usage_type: UsageType

    quantity: int = Field(
        gt=0,
    )

    input_tokens: int = Field(
        default=0,
        ge=0,
    )

    cached_input_tokens: int = Field(
        default=0,
        ge=0,
    )

    output_tokens: int = Field(
        default=0,
        ge=0,
    )

    reasoning_tokens: int = Field(
        default=0,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_token_data(self):
        if self.usage_type == UsageType.API_CALL:
            if any(
                value > 0
                for value in (
                    self.input_tokens,
                    self.cached_input_tokens,
                    self.output_tokens,
                    self.reasoning_tokens,
                )
            ):
                raise ValueError(
                    "Token fields must be zero for API_CALL."
                )

        if self.usage_type == UsageType.AI_TOKEN:
            token_total = (
                self.input_tokens
                + self.cached_input_tokens
                + self.output_tokens
                + self.reasoning_tokens
            )

            if token_total and token_total != self.quantity:
                raise ValueError(
                    "For AI_TOKEN, quantity must equal the sum "
                    "of token fields."
                )

        return self


class GenerateResponse(BaseModel):
    usage_event_id: int
    tenant_id: int
    usage_type: str
    quantity: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    idempotency_key: str
    status: str


class UsageSummaryItem(BaseModel):
    used: int
    limit: int


class UsageResponse(BaseModel):
    api_calls: UsageSummaryItem
    ai_tokens: UsageSummaryItem
    cost: int