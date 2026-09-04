import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import PaymentEvent, Plan, Subscription


router = APIRouter(
    tags=["webhooks"],
)


def verify_signature(
    payload: bytes,
    signature: str,
) -> bool:
    expected_signature = hmac.new(
        settings.razorpay_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )


def get_subscription_from_event(data: dict) -> dict | None:
    try:
        return data["payload"]["subscription"]["entity"]
    except (KeyError, TypeError):
        return None


def update_subscription(
    db: Session,
    razorpay_subscription: dict,
) -> None:
    provider_subscription_id = razorpay_subscription.get("id")
    provider_customer_id = razorpay_subscription.get("customer_id")
    provider_plan_id = razorpay_subscription.get("plan_id")
    razorpay_status = razorpay_subscription.get("status")

    if not provider_subscription_id:
        return

    subscription = db.scalar(
        select(Subscription).where(
            Subscription.provider_subscription_id
            == provider_subscription_id
        )
    )

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail="Local subscription not found.",
        )

    subscription.provider_customer_id = provider_customer_id

    plan = None

    if provider_plan_id:
        plan = db.scalar(
            select(Plan).where(
                Plan.provider_plan_id == provider_plan_id
            )
        )

    if razorpay_status == "active":
        # The newly activated subscription becomes the current one.
        old_subscriptions = db.scalars(
            select(Subscription).where(
                Subscription.tenant_id == subscription.tenant_id,
                Subscription.id != subscription.id,
                Subscription.status == "active",
            )
        ).all()

        for old_subscription in old_subscriptions:
            old_subscription.status = "inactive"

        subscription.status = "active"

        if plan is not None:
            subscription.plan_id = plan.id

    elif razorpay_status == "cancelled":
        subscription.status = "cancelled"

    elif razorpay_status == "completed":
        subscription.status = "completed"

    else:
        subscription.status = razorpay_status


@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    # IMPORTANT:
    # Read raw body before parsing JSON.
    payload = await request.body()

    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    event_id = request.headers.get(
        "x-razorpay-event-id"
    )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay webhook signature.",
        )

    if not event_id:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay event ID.",
        )

    if not verify_signature(
        payload,
        signature,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature.",
        )

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        ) from None

    event_type = data.get("event")

    if not event_type:
        raise HTTPException(
            status_code=400,
            detail="Missing webhook event type.",
        )

    # Check duplicate event AFTER signature verification.
    existing_event = db.scalar(
        select(PaymentEvent).where(
            PaymentEvent.provider_event_id == event_id
        )
    )

    if existing_event:
        return {
            "status": "duplicate",
        }

    payment_event = PaymentEvent(
        provider_event_id=event_id,
        event_type=event_type,
    )

    db.add(payment_event)

    subscription_events = {
        "subscription.authenticated",
        "subscription.activated",
        "subscription.updated",
        "subscription.cancelled",
        "subscription.completed",
    }

    if event_type in subscription_events:
        razorpay_subscription = get_subscription_from_event(data)

        if razorpay_subscription:
            update_subscription(
                db,
                razorpay_subscription,
            )

    db.commit()

    return {
        "status": "processed",
    }