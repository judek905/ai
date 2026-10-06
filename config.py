from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://jaykay:jaykay_pass@localhost:3306/jaykay"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60 * 24
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-5-5"

    admin_email: str = "admin@jaykay.local"
    admin_password: str = "change-this-now"
    owner_payment_number: str = ""  # secret: only returned to the admin

    premium_price: int = 10000
    currency: str = "UGX"
    premium_days: int = 30

    free_daily_limit: int = 3
    premium_daily_limit: int = 50
    free_max_chars: int = 6000
    premium_max_chars: int = 60000
    max_upload_bytes: int = 5 * 1024 * 1024

    cors_origins: str = "http://localhost:5173"


settings = Settings()
