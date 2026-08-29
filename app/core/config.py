from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str = ""
    razorpay_pro_plan_id: str

    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()