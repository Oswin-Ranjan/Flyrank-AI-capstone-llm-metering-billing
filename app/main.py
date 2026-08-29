from fastapi import FastAPI

from app.api.routes.billing import router as billing_router
from app.api.routes.usage import router as generate_router
from app.api.routes.usage_summary import router as usage_router
from app.api.routes.webhooks import router as webhooks_router


app = FastAPI(
    title="FlyRank Usage Metering & Billing Engine",
    version="1.0.0",
)


app.include_router(generate_router)
app.include_router(usage_router)
app.include_router(billing_router)
app.include_router(webhooks_router)


@app.get("/")
def root():
    return {
        "message": "Usage Metering & Billing Engine is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }