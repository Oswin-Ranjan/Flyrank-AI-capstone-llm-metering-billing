from app.core.pricing import (
    AI_CACHED_INPUT_PRICE_PER_TOKEN,
    AI_INPUT_PRICE_PER_TOKEN,
    AI_OUTPUT_PRICE_PER_TOKEN,
    AI_REASONING_PRICE_PER_TOKEN,
    API_CALL_PRICE,
)
from app.models import UsageEvent


class CostService:

    @staticmethod
    def calculate_event_cost(
        event: UsageEvent,
    ) -> int:
        if event.usage_type == "API_CALL":
            return event.quantity * API_CALL_PRICE

        if event.usage_type == "AI_TOKEN":
            input_cost = (
                event.input_tokens
                * AI_INPUT_PRICE_PER_TOKEN
            )

            cached_input_cost = (
                event.cached_input_tokens
                * AI_CACHED_INPUT_PRICE_PER_TOKEN
            )

            output_cost = (
                event.output_tokens
                * AI_OUTPUT_PRICE_PER_TOKEN
            )

            reasoning_cost = (
                event.reasoning_tokens
                * AI_REASONING_PRICE_PER_TOKEN
            )

            return (
                input_cost
                + cached_input_cost
                + output_cost
                + reasoning_cost
            )

        raise ValueError(
            f"Unsupported usage type: {event.usage_type}"
        )