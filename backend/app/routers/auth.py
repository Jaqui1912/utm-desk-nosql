from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..auth import verificar_password, crear_token_acceso, obtener_usuario_actual

router = APIRouter(prefix="/auth", tags=["autenticacion"])


class LoginRequest(BaseModel):
    correo: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: dict


@router.post("/login", response_model=LoginResponse, summary="RF-12 – Iniciar sesión y emitir token JWT")
async def login(credenciales: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    RF-12: Permite iniciar sesión con correo y contraseña.
    Verifica contra la colección 'usuarios' y valida contraseña con bcrypt.
    Emite un token JWT con identidad y rol del usuario.
    Si las credenciales son incorrectas o la cuenta está desactivada, devuelve HTTP 401.
    """
    usuario = await db["usuarios"].find_one({"correo": credenciales.correo})
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas: correo o contraseña inválidos.",
        )

    if not usuario.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de usuario se encuentra desactivada.",
        )

    if not verificar_password(credenciales.password, usuario.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas: correo o contraseña inválidos.",
        )

    # Datos para el payload del token JWT
    payload_token = {
        "sub": str(usuario["_id"]),
        "nombre": usuario.get("nombre"),
        "correo": usuario.get("correo"),
        "rol": usuario.get("rol"),
        "tipo": usuario.get("tipo"),
    }

    token = crear_token_acceso(payload_token)

    datos_usuario = {
        "id": str(usuario["_id"]),
        "nombre": usuario.get("nombre"),
        "correo": usuario.get("correo"),
        "rol": usuario.get("rol"),
        "tipo": usuario.get("tipo"),
        "activo": usuario.get("activo"),
        "especialidades": usuario.get("especialidades"),
    }

    return LoginResponse(access_token=token, usuario=datos_usuario)


@router.get("/me", summary="Obtener perfil del usuario autenticado")
async def perfil_usuario(usuario_actual: dict = Depends(obtener_usuario_actual)):
    """Devuelve los datos del usuario en sesión activa."""
    return {
        "id": usuario_actual["id"],
        "nombre": usuario_actual.get("nombre"),
        "correo": usuario_actual.get("correo"),
        "rol": usuario_actual.get("rol"),
        "tipo": usuario_actual.get("tipo"),
        "especialidades": usuario_actual.get("especialidades"),
        "activo": usuario_actual.get("activo"),
    }
