import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as aioredis

# Fix para resolución DNS de SRV de MongoDB Atlas en Windows
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
except Exception:
    pass

from .config import settings

logger = logging.getLogger("utm_desk")

# ── Clientes Globales ──────────────────────────────────────────────────────────
_mongo_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None
_redis_client: aioredis.Redis | None = None
_redis_available: bool = False


async def connect_db() -> None:
    global _mongo_client, _db, _redis_client, _redis_available

    # 1. MongoDB Atlas (Inicialización)
    try:
        if _mongo_client is None:
            _mongo_client = AsyncIOMotorClient(
                settings.mongodb_uri,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=30000,
            )
            _db = _mongo_client[settings.mongodb_db]
        logger.info(f"✅ Conectado a MongoDB Atlas (Base de datos: {settings.mongodb_db})")
    except Exception as e:
        logger.error(f"❌ Error al inicializar MongoDB Atlas: {e}")
        raise e

    # 2. Redis (Opcional con fallback automático en MongoDB)
    try:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await _redis_client.ping()
        _redis_available = True
        logger.info(f"✅ Conectado a Redis ({settings.redis_url})")
    except Exception as e:
        _redis_available = False
        logger.warning(
            f"⚠️  Redis no disponible en {settings.redis_url}. "
            "Se usará fallback atómico en MongoDB para el contador de incidencias."
        )


async def close_db() -> None:
    global _mongo_client, _redis_client
    if _mongo_client:
        _mongo_client.close()
    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception:
            pass


def get_db() -> AsyncIOMotorDatabase:
    global _mongo_client, _db
    if _db is None:
        _mongo_client = AsyncIOMotorClient(
            settings.mongodb_uri,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000,
        )
        _db = _mongo_client[settings.mongodb_db]
    return _db


def get_redis() -> aioredis.Redis | None:
    if _redis_available and _redis_client is not None:
        return _redis_client
    return None
