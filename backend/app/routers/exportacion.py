"""
Router de Exportación y Respaldo NoSQL para el Administrador del Sistema.
Permite descargar en formato JSON estándar:
1. Directorio de usuarios (sin hashes de contraseña sensibles).
2. Expediente completo de incidencias del campus (con detalle polimórfico y evidencias).
3. Esquema y validadores ($jsonSchema e índices vigentes en MongoDB Atlas).
"""
from fastapi import APIRouter, Depends, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import json_util

from ..database import get_db
from ..auth import requerir_roles

router = APIRouter(prefix="/admin/exportar", tags=["exportacion"])

OPCIONES_JSON = json_util.RELAXED_JSON_OPTIONS


@router.get(
    "/usuarios",
    summary="Exportar directorio de usuarios en JSON",
    description="Genera y descarga el archivo usuarios.json con todas las cuentas del sistema (excluyendo hashes).",
)
async def exportar_usuarios(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_sistema"])),
):
    cursor = db["usuarios"].find().sort([("correo", 1)])
    docs = []
    async for d in cursor:
        d.pop("password_hash", None)
        docs.append(d)

    contenido = json_util.dumps(docs, indent=2, ensure_ascii=False, json_options=OPCIONES_JSON)
    return Response(
        content=contenido,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="usuarios.json"'},
    )


@router.get(
    "/incidencias",
    summary="Exportar incidencias del campus en JSON",
    description="Genera y descarga el archivo incidencias_campus.json con el historial completo de incidencias.",
)
async def exportar_incidencias(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_sistema"])),
):
    cursor = db["incidencias_campus"].find().sort([("codigo", 1)])
    docs = [d async for d in cursor]

    contenido = json_util.dumps(docs, indent=2, ensure_ascii=False, json_options=OPCIONES_JSON)
    return Response(
        content=contenido,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="incidencias_campus.json"'},
    )


@router.get(
    "/esquema",
    summary="Exportar validador $jsonSchema e índices de MongoDB Atlas",
    description="Inspecciona dinámicamente las colecciones de Atlas y extrae los esquemas de validación e índices.",
)
async def exportar_esquema(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_sistema"])),
):
    colecciones = ["usuarios", "incidencias_campus"]
    resultado = []

    for nombre in colecciones:
        # Obtener información de la colección y su validador
        colls = await db.list_collections(filter={"name": nombre}).to_list(length=1)
        info = colls[0] if colls else {}
        opciones = info.get("options", {})

        # Obtener índices
        indices = []
        async for ix in db[nombre].list_indexes():
            ix = dict(ix)
            ix.pop("v", None)  # Omitir versión interna de MongoDB
            indices.append(ix)

        resultado.append({
            "coleccion": nombre,
            "validador": opciones.get("validator"),
            "nivel_de_validacion": opciones.get("validationLevel"),
            "accion_de_validacion": opciones.get("validationAction"),
            "indices": indices,
        })

    contenido = json_util.dumps(resultado, indent=2, ensure_ascii=False, json_options=OPCIONES_JSON)
    return Response(
        content=contenido,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="esquema_y_indices.json"'},
    )
