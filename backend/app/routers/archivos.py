import jwt
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..storage import resolver_token_local

router = APIRouter(prefix="/archivos", tags=["evidencias"])


@router.get("/{token}", summary="Descargar evidencia con URL firmada (modo local)")
async def descargar_archivo(token: str):
    """Sirve un archivo solo si el token de la URL firmada es válido y no ha expirado."""
    try:
        ruta = resolver_token_local(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="La URL firmada ha expirado.")
    except (jwt.InvalidTokenError, FileNotFoundError, KeyError):
        raise HTTPException(status_code=404, detail="Archivo no encontrado o URL inválida.")
    return FileResponse(ruta)
