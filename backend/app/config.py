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

    # Almacenamiento de evidencias (Supabase Storage). Si no se configuran,
    # los archivos se guardan en backend/uploads y se sirven con URL firmada local.
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_bucket: str = os.getenv("SUPABASE_BUCKET", "evidencias")
    url_firmada_segundos: int = 600  # vigencia de las URLs firmadas (10 min)
    evidencia_max_mb: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
