from app.core.pricing import (
    AI_CACHED_INPUT_PRICE_PER_TOKEN,
    AI_INPUT_PRICE_PER_TOKEN,
    AI_OUTPUT_PRICE_PER_TOKEN,
)
from app.models import UsageEvent
from app.services.cost import CostService


def test_api_call_cost():
    event = UsageEvent(
        usage_type="API_CALL",
        quantity=10,
        idempotency_key="cost-api-1",
    )

    expected = (
        10 * 1_000
    )

    assert CostService.calculate_event_cost(event) == expected


def test_ai_token_cost():
    event = UsageEvent(
        usage_type="AI_TOKEN",
        quantity=3500,
        input_tokens=1500,
        cached_input_tokens=500,
        output_tokens=1000,
        reasoning_tokens=500,
        idempotency_key="cost-ai-1",
    )

    expected = (
        (1500 * AI_INPUT_PRICE_PER_TOKEN)
        + (500 * AI_CACHED_INPUT_PRICE_PER_TOKEN)
        + (1000 * AI_OUTPUT_PRICE_PER_TOKEN)
        + (500 * AI_OUTPUT_PRICE_PER_TOKEN)
    )

    assert CostService.calculate_event_cost(event) == expected


def test_cached_input_is_cheaper_than_fresh_input():
    assert (
        AI_CACHED_INPUT_PRICE_PER_TOKEN
        < AI_INPUT_PRICE_PER_TOKEN
    )


def test_reasoning_tokens_use_output_pricing():
    from app.core.pricing import (
        AI_REASONING_PRICE_PER_TOKEN,
    )

    assert (
        AI_REASONING_PRICE_PER_TOKEN
        == AI_OUTPUT_PRICE_PER_TOKEN
    )
    
def test_pinned_ai_cost():
    event = UsageEvent(
        usage_type="AI_TOKEN",
        quantity=1000,
        input_tokens=400,
        cached_input_tokens=200,
        output_tokens=300,
        reasoning_tokens=100,
        idempotency_key="pinned-cost-1",
    )

    # 400*2 + 200*1 + 300*8 + 100*8
    # = 4200 micro-dollars
    assert CostService.calculate_event_cost(event) == 4200  