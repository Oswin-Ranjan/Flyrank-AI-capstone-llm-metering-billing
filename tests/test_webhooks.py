import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def make_signature(payload: bytes) -> str:
    return hmac.new(
        settings.razorpay_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


def test_invalid_webhook_signature_returns_400():
    payload = json.dumps(
        {
            "entity": "event",
            "event": "subscription.activated",
        }
    ).encode()

    response = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={
            "X-Razorpay-Signature": "invalid-signature",
            "x-razorpay-event-id": "test-event-invalid",
        },
    )

    assert response.status_code == 400
    
def test_valid_webhook_is_processed():
    payload = json.dumps(
        {
            "entity": "event",
            "event": "subscription.activated",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_test_001",
                        "plan_id": "plan_test_001",
                        "customer_id": "cust_test_001",
                        "status": "active",
                    }
                }
            },
        }
    ).encode()

    signature = make_signature(payload)

    response = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": "test-event-valid",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed" 
    
def test_duplicate_webhook_is_ignored():
    payload = json.dumps(
        {
            "entity": "event",
            "event": "subscription.activated",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_test_002",
                        "plan_id": "plan_test_002",
                        "customer_id": "cust_test_002",
                        "status": "active",
                    }
                }
            },
        }
    ).encode()

    signature = make_signature(payload)

    headers = {
        "X-Razorpay-Signature": signature,
        "x-razorpay-event-id": "test-event-duplicate",
    }

    first = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers=headers,
    )

    second = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["status"] == "processed"
    assert second.json()["status"] == "duplicate"       