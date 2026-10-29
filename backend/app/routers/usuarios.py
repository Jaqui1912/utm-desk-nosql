from datetime import datetime, timezone
from typing import Literal, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, WriteError

from ..database import get_db
from ..auth import requerir_roles, hashear_password
from ..models.incidencia import CategoriaEnum, TipoReportanteEnum

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

RolEnum = Literal["reportante", "admin_general", "tecnico", "directivo", "admin_sistema", "superAdmin"]


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=3)
    correo: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=6)
    rol: RolEnum
    tipo: Optional[TipoReportanteEnum] = None
    especialidades: Optional[list[CategoriaEnum]] = None


class ActualizarEstadoUsuario(BaseModel):
    activo: bool


def _serializar_usuario(u: dict) -> dict:
    return {
        "id": str(u["_id"]),
        "nombre": u.get("nombre"),
        "correo": u.get("correo"),
        "rol": u.get("rol"),
        "tipo": u.get("tipo"),
        "especialidades": u.get("especialidades"),
        "activo": u.get("activo", True),
        "fecha_alta": u.get("fecha_alta").isoformat() if u.get("fecha_alta") else None,
    }


# ── RF-14: Listar Usuarios (Solo admin_sistema) ───────────────────────────────
@router.get("/", summary="RF-14 – Listar usuarios del sistema")
async def listar_usuarios(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_sistema"])),
):
    """Permite al Administrador del Sistema consultar el directorio de usuarios."""
    cursor = db["usuarios"].find().sort([("fecha_alta", -1)])
    usuarios = [_serializar_usuario(u) async for u in cursor]
    return {"total": len(usuarios), "usuarios": usuarios}


# ── RF-13: Técnicos activos (para asignar incidencias) ────────────────────────
@router.get("/tecnicos", summary="RF-13 – Listar técnicos activos para asignación")
async def listar_tecnicos(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_general"])),
):
    """Devuelve solo nombre y especialidades de los técnicos activos (sin datos sensibles)."""
    cursor = db["usuarios"].find(
        {"rol": "tecnico", "activo": True}, {"nombre": 1, "especialidades": 1}
    ).sort([("nombre", 1)])
    tecnicos = [
        {"id": str(u["_id"]), "nombre": u.get("nombre"), "especialidades": u.get("especialidades", [])}
        async for u in cursor
    ]
    return {"total": len(tecnicos), "tecnicos": tecnicos}


# ── RF-14: Crear Usuario (Solo admin_sistema) ─────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED, summary="RF-14 – Crear usuario con rol")
async def crear_usuario(
    payload: UsuarioCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_sistema"])),
):
    """
    RF-14: El Administrador del Sistema registra un usuario asignando rol.
    - Cifra la contraseña con bcrypt.
    - Rechaza correos duplicados con HTTP 400.
    - Valida contra el $jsonSchema de la colección 'usuarios'.
    """
    if payload.rol == "reportante" and not payload.tipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los usuarios con rol 'reportante' deben especificar el campo 'tipo' (docente, estudiante, administrativo).",
        )

    doc_usuario = {
        "nombre": payload.nombre,
        "correo": payload.correo,
        "password_hash": hashear_password(payload.password),
        "rol": payload.rol,
        "activo": True,
        "fecha_alta": datetime.now(timezone.utc),
    }

    if payload.tipo:
        doc_usuario["tipo"] = payload.tipo
    if payload.especialidades and payload.rol == "tecnico":
        doc_usuario["especialidades"] = list(set(payload.especialidades))

    try:
        resultado = await db["usuarios"].insert_one(doc_usuario)
        doc_usuario["_id"] = resultado.inserted_id
        return _serializar_usuario(doc_usuario)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo electrónico '{payload.correo}' ya se encuentra registrado.",
        )
    except WriteError as we:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en validación $jsonSchema de usuario: {we.details}",
        )


# ── RF-14: Activar o Desactivar Usuario (Solo admin_sistema) ──────────────────
@router.patch("/{usuario_id}/estado", summary="RF-14 – Activar o desactivar usuario")
async def cambiar_estado_usuario(
    usuario_id: str,
    payload: ActualizarEstadoUsuario,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_sistema"])),
):
    """
    RF-14: Permite activar o desactivar una cuenta de usuario.
    Los usuarios desactivados no pueden iniciar sesión (reciben HTTP 401).
    """
    try:
        oid = ObjectId(usuario_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Identificador de usuario inválido.")

    usuario = await db["usuarios"].find_one({"_id": oid})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    await db["usuarios"].update_one({"_id": oid}, {"$set": {"activo": payload.activo}})
    usuario["activo"] = payload.activo
    return _serializar_usuario(usuario)
