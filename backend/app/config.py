import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "utm_desk")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT Settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "utm_desk_jwt_secret_key_2026_nosql_cloud")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 horas

    # Supabase Storage Settings
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_bucket: str = os.getenv("SUPABASE_BUCKET", "evidencias")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
