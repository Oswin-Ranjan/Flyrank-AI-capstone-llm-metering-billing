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
    
def test_duplicate_webhook_is_ignored(db):
    payload = (
        b'{"entity":"event",'
        b'"event":"subscription.activated",'
        b'"payload":{"subscription":{"entity":'
        b'{"id":"sub_duplicate_test",'
        b'"plan_id":"unknown_plan",'
        b'"customer_id":"cust_test",'
        b'"status":"active"}}}}'
    )

    signature = make_signature(payload)

    headers = {
        "X-Razorpay-Signature": signature,
        "x-razorpay-event-id": "duplicate-event-001",
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
    
def test_invalid_webhook_signature_returns_400():
    payload = b'{"entity":"event","event":"subscription.activated"}'

    response = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={
            "X-Razorpay-Signature": "invalid-signature",
            "x-razorpay-event-id": "forged-event-001",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid Razorpay webhook signature."
    )          