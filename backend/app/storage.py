"""
Almacenamiento externo de evidencias (CU-02 / RF-05 / RNF-02).

Los archivos NO se guardan en MongoDB: se suben a un bucket de Supabase Storage
y en el documento solo queda la ruta (url_storage). Para verlos se genera una
URL firmada con vigencia limitada.

Si SUPABASE_URL / SUPABASE_KEY no están configurados (por ejemplo, en
desarrollo local), se usa la carpeta backend/uploads y una URL firmada local
(token JWT con expiración) servida por el router /archivos.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import httpx
import jwt

from .config import settings

CARPETA_LOCAL = Path(__file__).resolve().parent.parent / "uploads"


def usa_supabase() -> bool:
    url, key = settings.supabase_url.strip(), settings.supabase_key.strip()
    return bool(url and key and "<" not in url and "<" not in key)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.supabase_key}",
        "apikey": settings.supabase_key,
    }


async def subir_archivo(ruta: str, contenido: bytes, tipo_mime: str) -> None:
    """Sube el archivo al bucket (o a la carpeta local) en la ruta indicada."""
    if usa_supabase():
        url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_bucket}/{quote(ruta)}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                url,
                content=contenido,
                headers={**_headers(), "Content-Type": tipo_mime, "x-upsert": "true"},
            )
        if r.status_code >= 300:
            raise RuntimeError(f"Supabase Storage respondió {r.status_code}: {r.text[:200]}")
        return

    destino = CARPETA_LOCAL / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)


async def generar_url_firmada(ruta: str, base_url: str) -> str:
    """Devuelve una URL temporal (vigencia settings.url_firmada_segundos) para ver el archivo."""
    segundos = settings.url_firmada_segundos
    # Evidencias registradas con la URL completa (versión anterior con bucket público)
    if ruta.startswith("http://") or ruta.startswith("https://"):
        return ruta
    if usa_supabase():
        base = settings.supabase_url.rstrip("/")
        url = f"{base}/storage/v1/object/sign/{settings.supabase_bucket}/{quote(ruta)}"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, json={"expiresIn": segundos}, headers=_headers())
        if r.status_code >= 300:
            raise FileNotFoundError(f"No se pudo firmar el archivo ({r.status_code}).")
        firmada = r.json().get("signedURL") or r.json().get("signedUrl")
        return f"{base}/storage/v1{firmada}"

    if not (CARPETA_LOCAL / ruta).is_file():
        raise FileNotFoundError("El archivo no existe en el almacenamiento.")
    token = jwt.encode(
        {"ruta": ruta, "exp": datetime.now(timezone.utc) + timedelta(seconds=segundos)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return f"{base_url.rstrip('/')}/archivos/{token}"


def resolver_token_local(token: str) -> Path:
    """Valida el token de la URL firmada local y devuelve la ruta del archivo."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    ruta = (CARPETA_LOCAL / payload["ruta"]).resolve()
    if CARPETA_LOCAL.resolve() not in ruta.parents or not ruta.is_file():
        raise FileNotFoundError
    return ruta
