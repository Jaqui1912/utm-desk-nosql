from datetime import datetime, timedelta, timezone
from typing import Optional
from bson import ObjectId
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from .config import settings
from .database import get_db

security = HTTPBearer(auto_error=False)


def verificar_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def hashear_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def crear_token_acceso(datos: dict, expira_minutos: Optional[int] = None) -> str:
    datos_payload = datos.copy()
    tiempo_exp = datetime.now(timezone.utc) + timedelta(
        minutes=expira_minutos or settings.jwt_expiration_minutes
    )
    datos_payload.update({"exp": tiempo_exp, "iat": datetime.now(timezone.utc)})
    return jwt.encode(datos_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de sesión ha expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def obtener_usuario_actual(
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """
    Valida el token JWT del encabezado Authorization: Bearer <token>.
    Recupera el usuario de la colección usuarios y verifica que esté activo.
    """
    if credenciales is None or not credenciales.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decodificar_token(credenciales.credentials)
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado: falta identificador de usuario.",
        )

    usuario = await db["usuarios"].find_one({"_id": ObjectId(usuario_id)})
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario asociado al token no existe.",
        )

    if not usuario.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de usuario se encuentra desactivada.",
        )

    usuario["id"] = str(usuario["_id"])
    return usuario


def requerir_roles(roles_permitidos: list[str]):
    """
    Verifica que el rol del usuario autenticado esté dentro de la lista de roles autorizados
    según la Matriz de Permisos (Tabla 3 del documento).
    Responde HTTP 403 Forbidden si el rol no tiene acceso.
    """
    async def validador_rol(usuario_actual: dict = Depends(obtener_usuario_actual)) -> dict:
        rol_usuario = usuario_actual.get("rol")
        if rol_usuario not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado: el rol '{rol_usuario}' no tiene permisos para esta operación. "
                    f"Roles requeridos: {roles_permitidos}"
                ),
            )
        return usuario_actual

    return validador_rol
