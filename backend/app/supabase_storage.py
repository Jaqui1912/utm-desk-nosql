"""
Servicio de Supabase Storage para UTM Desk NoSQL Cloud.
Sube archivos reales al bucket 'evidencias' y retorna la URL pública.
Usa httpx (async) directamente contra la REST API de Supabase Storage.
"""
import logging
import mimetypes
from typing import Optional

import httpx

from .config import settings

logger = logging.getLogger("utm_desk")

# ── Tipos MIME permitidos (espejo del $jsonSchema de Atlas) ───────────────────
MIME_PERMITIDOS = {
    "image/jpeg",
    "image/png",
    "application/pdf",
    "video/mp4",
}


def _storage_base() -> str:
    """URL base del endpoint de Storage REST de Supabase."""
    return f"{settings.supabase_url}/storage/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.supabase_key}",
        "apikey": settings.supabase_key,
    }


async def subir_archivo(
    contenido: bytes,
    nombre_archivo: str,
    tipo_mime: str,
    carpeta: str = "",
) -> Optional[str]:
    """
    Sube `contenido` al bucket configurado en Supabase Storage.

    Args:
        contenido:      Bytes del archivo.
        nombre_archivo: Nombre con extensión, p. ej. 'foto.jpg'.
        tipo_mime:      MIME type validado, p. ej. 'image/jpeg'.
        carpeta:        Prefijo de ruta dentro del bucket (código de incidencia).

    Returns:
        URL pública del archivo en Supabase, o None si Supabase no está configurado.

    Raises:
        ValueError: Si el tipo MIME no está permitido.
        RuntimeError: Si la subida falla.
    """
    if tipo_mime not in MIME_PERMITIDOS:
        raise ValueError(
            f"Tipo MIME '{tipo_mime}' no permitido. "
            f"Permitidos: {', '.join(sorted(MIME_PERMITIDOS))}"
        )

    # Si no hay configuración de Supabase, retornar None (modo degradado)
    if not settings.supabase_url or not settings.supabase_key:
        logger.warning("Supabase no configurado — se guardará solo metadatos sin archivo real.")
        return None

    ruta_objeto = f"{carpeta}/{nombre_archivo}" if carpeta else nombre_archivo
    url_upload = f"{_storage_base()}/object/{settings.supabase_bucket}/{ruta_objeto}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            **_headers(),
            "Content-Type": tipo_mime,
            "x-upsert": "true",  # Sobreescribe si ya existe el mismo nombre
        }
        response = await client.post(url_upload, content=contenido, headers=headers)

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Supabase Storage error {response.status_code}: {response.text}"
            )

    # Construir URL pública (el bucket es público)
    url_publica = (
        f"{_storage_base()}/object/public/{settings.supabase_bucket}/{ruta_objeto}"
    )
    logger.info(f"Archivo subido a Supabase: {url_publica}")
    return url_publica
