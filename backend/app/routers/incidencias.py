import logging
import re
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as aioredis
from pymongo.errors import WriteError

from .. import storage
from ..config import settings
from ..database import get_db, get_redis
from ..auth import obtener_usuario_actual, requerir_roles
from ..models.incidencia import (
    ActualizarEstado,
    CargarEvidencia,
    GestionarTags,
    IncidenciaCreate,
    serialize_doc,
)

logger = logging.getLogger("utm_desk")
router = APIRouter(prefix="/incidencias", tags=["incidencias"])

COLECCION = "incidencias_campus"
ESTADOS_ABIERTOS = ["abierta", "en proceso", "en espera"]
MS_POR_HORA = 3_600_000
MIMES_PERMITIDOS = ["image/jpeg", "image/png", "application/pdf", "video/mp4"]


# ── Payload para Asignación de Técnico (RF-13) ────────────────────────────────
class AsignarTecnicoRequest(BaseModel):
    tecnico_id: str = Field(..., description="ObjectId del técnico en la colección usuarios")


# ── Helpers de Búsqueda y Resolución de Identificadores ───────────────────────
def _construir_filtro_identificador(identificador: str) -> dict:
    """Permite buscar tanto por ObjectId hexadecimal como por código formal (ej. INC-2026-0042)."""
    if len(identificador) == 24 and ObjectId.is_valid(identificador):
        return {"_id": ObjectId(identificador)}
    return {"codigo": identificador}


async def _obtener_incidencia_or_404(db: AsyncIOMotorDatabase, identificador: str) -> dict:
    filtro = _construir_filtro_identificador(identificador)
    doc = await db[COLECCION].find_one(filtro)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia con identificador '{identificador}' no encontrada.",
        )
    return doc


async def _generar_consecutivo_codigo(db: AsyncIOMotorDatabase, redis: Optional[aioredis.Redis]) -> str:
    """
    CU-01 / RF-04: Genera el código único formal en formato INC-YYYY-XXXX.
    Implementa Redis INCR con clave 'contador:incidencias:YYYY'.
    Si Redis no estuviera disponible, utiliza fallback atómico en MongoDB.
    """
    anio = datetime.now(timezone.utc).year
    consecutivo: int = 1

    # Mayor consecutivo ya usado en la colección (evita repetir folios si el
    # contador se reinicia, p. ej. Redis sin persistencia o base recién poblada).
    ultimo = await db[COLECCION].find_one(
        {"codigo": {"$regex": f"^INC-{anio}-"}}, {"codigo": 1}, sort=[("codigo", -1)]
    )
    maximo_existente = int(ultimo["codigo"].rsplit("-", 1)[1]) if ultimo else 0

    if redis is not None:
        try:
            clave_redis = f"contador:incidencias:{anio}"
            consecutivo = await redis.incr(clave_redis)
            if consecutivo <= maximo_existente:
                consecutivo = maximo_existente + 1
                await redis.set(clave_redis, consecutivo)
        except Exception as e:
            logger.warning(f"Falla al ejecutar INCR en Redis: {e}. Usando fallback.")
            redis = None

    if redis is None:
        # Fallback atómico en MongoDB: $max sincroniza con lo existente y $inc reserva el folio.
        await db["contadores"].update_one(
            {"_id": f"incidencias_{anio}"},
            {"$max": {"consecutivo": maximo_existente}},
            upsert=True,
        )
        contador = await db["contadores"].find_one_and_update(
            {"_id": f"incidencias_{anio}"},
            {"$inc": {"consecutivo": 1}},
            return_document=True,
        )
        consecutivo = contador.get("consecutivo", 1)

    return f"INC-{anio}-{consecutivo:04d}"


# ── CU-05: Búsqueda Textual Ponderada (RF-08) ────────────────────────────────
@router.get("/buscar", summary="CU-05 / RF-08 – Búsqueda textual por relevancia")
async def buscar_incidencias(
    q: str = Query(..., min_length=2, description="Términos clave para la búsqueda textual"),
    limite: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    """
    RF-08: Búsqueda sobre título y descripción ordenada por relevancia (textScore).
    El reportante solo obtiene resultados de sus propias incidencias.
    """
    filtro: dict = {"$text": {"$search": q}}

    # Restricción RF-08: Reportante solo ve sus incidencias
    if usuario.get("rol") == "reportante":
        filtro["reportante.usuario_id"] = usuario["_id"]

    proyeccion = {
        "codigo": 1,
        "titulo": 1,
        "descripcion": 1,
        "categoria": 1,
        "prioridad": 1,
        "estado": 1,
        "ubicacion": 1,
        "tags": 1,
        "score": {"$meta": "textScore"},
    }

    cursor = db[COLECCION].find(filtro, proyeccion).sort([("score", {"$meta": "textScore"})]).limit(limite)
    resultados = [serialize_doc(doc) async for doc in cursor]
    return {"total": len(resultados), "resultados": resultados}


# ── CU-06: Analítica de Resolución y Fallas Crónicas (RF-09) ─────────────────
@router.get("/analitica", summary="CU-06 / RF-09 – Analítica de resolución y top tags")
async def obtener_analitica(
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(requerir_roles(["admin_general", "directivo"])),
):
    """
    RF-09: Promedio y total de horas de resolución por edificio y ranking de las 10 etiquetas más frecuentes.
    Restringido exclusivamente a Administrador General y Directivo (demás roles reciben HTTP 403).
    """
    pipeline_edificios = [
        {
            "$match": {
                "estado": {"$in": ["resuelta", "cerrada"]},
                "fecha_resolucion": {"$exists": True},
            }
        },
        {
            "$addFields": {
                "horas_resolucion": {
                    "$divide": [
                        {"$subtract": ["$fecha_resolucion", "$fecha_creacion"]},
                        MS_POR_HORA,
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$ubicacion.edificio",
                "incidencias": {"$sum": 1},
                "promedio_horas": {"$avg": "$horas_resolucion"},
                "total_horas": {"$sum": "$horas_resolucion"},
            }
        },
        {"$sort": {"promedio_horas": -1}},
        {
            "$project": {
                "_id": 0,
                "edificio": "$_id",
                "incidencias": 1,
                "promedio_horas": {"$round": ["$promedio_horas", 1]},
                "total_horas": {"$round": ["$total_horas", 1]},
            }
        },
    ]

    pipeline_tags = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "total": {"$sum": 1}}},
        {"$sort": {"total": -1, "_id": 1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "tag": "$_id", "total": 1}},
    ]

    cursor_edificios = db[COLECCION].aggregate(pipeline_edificios)
    cursor_tags = db[COLECCION].aggregate(pipeline_tags)

    eficiencia = [doc async for doc in cursor_edificios]
    top_tags = [doc async for doc in cursor_tags]

    return {
        "eficiencia_por_edificio": eficiencia,
        "top_10_tags": top_tags,
    }


# ── CU-01: Registrar Incidencia (RF-01 / RF-02 / RF-03 / RF-04) ───────────────
@router.post("/", status_code=status.HTTP_201_CREATED, summary="CU-01 / RF-01 – Registrar incidencia")
async def registrar_incidencia(
    payload: IncidenciaCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: Optional[aioredis.Redis] = Depends(get_redis),
    usuario: dict = Depends(requerir_roles(["reportante", "admin_general"])),
):
    """
    RF-01 / RF-02: Registra incidencia adaptando detalle_especifico según categoría.
    Permitido para reportante y admin_general.
    - Genera código único vía Redis INCR (formato INC-YYYY-XXXX).
    - Valida contra $jsonSchema estricto de Atlas (rechaza campos ajenos con HTTP 400).
    """
    # Si quien reporta es un usuario con rol 'reportante', asociar automáticamente su usuario_id y datos
    if usuario.get("rol") == "reportante":
        reportante_uid = usuario["_id"]
        nombre_rep = usuario.get("nombre", payload.reportante.nombre)
        tipo_rep = usuario.get("tipo", payload.reportante.tipo)
        correo_rep = usuario.get("correo", payload.reportante.correo)
    else:
        try:
            reportante_uid = ObjectId(payload.reportante.usuario_id)
            nombre_rep = payload.reportante.nombre
            tipo_rep = payload.reportante.tipo
            correo_rep = payload.reportante.correo
        except InvalidId:
            raise HTTPException(status_code=400, detail="reportante.usuario_id no es un ObjectId válido.")

    codigo = await _generar_consecutivo_codigo(db, redis)
    ahora = datetime.now(timezone.utc)

    doc = {
        "codigo": codigo,
        "titulo": payload.titulo,
        "descripcion": payload.descripcion,
        "categoria": payload.categoria,
        "prioridad": payload.prioridad,
        "estado": "abierta",
        "reportante": {
            "usuario_id": reportante_uid,
            "nombre": nombre_rep,
            "tipo": tipo_rep,
            "correo": correo_rep,
        },
        "ubicacion": payload.ubicacion.model_dump(exclude_none=True),
        "fecha_creacion": ahora,
        "horas_invertidas": 0,
        "tags": list(set(payload.tags)),
        "detalle_especifico": payload.detalle_especifico,
        "historial_seguimiento": [],
        "evidencias_adjuntas": [],
    }

    if payload.tecnico_asignado:
        try:
            doc["tecnico_asignado"] = {
                "usuario_id": ObjectId(payload.tecnico_asignado.usuario_id),
                "nombre": payload.tecnico_asignado.nombre,
            }
        except InvalidId:
            raise HTTPException(status_code=400, detail="tecnico_asignado.usuario_id no es un ObjectId válido.")

    try:
        resultado = await db[COLECCION].insert_one(doc)
        doc["_id"] = resultado.inserted_id
        return serialize_doc(doc)
    except WriteError as we:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El documento no cumple el $jsonSchema de MongoDB Atlas: "
                + str((we.details or {}).get("errmsg", "validación fallida"))
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar la incidencia: {str(e)}",
        )


# ── Listar Incidencias (RF-11 / Matriz de Permisos) ──────────────────────────
@router.get("/", summary="Listar incidencias del campus con filtros")
async def listar_incidencias(
    categoria: Optional[str] = Query(None, description="computo_redes, infraestructura, academico"),
    estado: Optional[str] = Query(None, description="abierta, en proceso, en espera, resuelta, cerrada"),
    prioridad: Optional[str] = Query(None, description="baja, media, alta, critica"),
    edificio: Optional[str] = Query(None, description="Nombre exacto del edificio"),
    asignadas_a_mi: bool = Query(False, description="Para técnicos: filtrar solo incidencias asignadas a su usuario"),
    limit: int = Query(25, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    """
    Lista incidencias utilizando el índice compuesto { categoria: 1, estado: 1, 'ubicacion.edificio': 1 }.
    - Reportantes: Solo pueden ver sus propias incidencias (Tabla 3).
    - Técnicos: Pueden consultar todas o filtrar las asignadas a ellos.
    - Administradores y directivos: Acceso a todo el catálogo.
    """
    filtro: dict = {}

    # Restricción según rol (Tabla 3 pág. 10)
    if usuario.get("rol") == "reportante":
        filtro["reportante.usuario_id"] = usuario["_id"]
    elif usuario.get("rol") == "tecnico" and asignadas_a_mi:
        filtro["tecnico_asignado.usuario_id"] = usuario["_id"]

    if categoria:
        filtro["categoria"] = categoria
    if estado:
        filtro["estado"] = estado
    if prioridad:
        filtro["prioridad"] = prioridad
    if edificio:
        filtro["ubicacion.edificio"] = edificio

    total = await db[COLECCION].count_documents(filtro)
    cursor = db[COLECCION].find(filtro).sort([("fecha_creacion", -1)]).skip(skip).limit(limit)
    incidencias = [serialize_doc(doc) async for doc in cursor]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "incidencias": incidencias,
    }


# ── Conteos por Estado (para pills del frontend) ──────────────────────────────
@router.get("/conteos-estado", summary="Conteo de incidencias agrupadas por estado")
async def conteos_por_estado(
    categoria: Optional[str] = Query(None),
    edificio: Optional[str] = Query(None),
    asignadas_a_mi: bool = Query(False),
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    """
    Devuelve un objeto { estado: count } con el total de incidencias por estado.
    No aplica filtro de estado para que los pills del frontend siempre reflejen
    los conteos reales independientemente del filtro activo.
    Respeta las mismas restricciones de rol que el endpoint de listado.
    """
    filtro: dict = {}

    if usuario.get("rol") == "reportante":
        filtro["reportante.usuario_id"] = usuario["_id"]
    elif usuario.get("rol") == "tecnico" and asignadas_a_mi:
        filtro["tecnico_asignado.usuario_id"] = usuario["_id"]

    if categoria:
        filtro["categoria"] = categoria
    if edificio:
        filtro["ubicacion.edificio"] = edificio

    pipeline = [
        {"$match": filtro},
        {"$group": {"_id": "$estado", "count": {"$sum": 1}}},
    ]
    cursor = db[COLECCION].aggregate(pipeline)
    conteos = {doc["_id"]: doc["count"] async for doc in cursor}
    return conteos


# ── Obtener Incidencia por Identificador ──────────────────────────────────────
@router.get("/{identificador}", summary="Obtener incidencia por ObjectId o código")
async def obtener_incidencia(
    identificador: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    doc = await _obtener_incidencia_or_404(db, identificador)

    # Restricción para reportante: no puede ver incidencias ajenas
    if usuario.get("rol") == "reportante":
        if doc.get("reportante", {}).get("usuario_id") != usuario["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso restringido: no puedes consultar expedientes de otros usuarios.",
            )

    return serialize_doc(doc)


# ── RF-13: Asignar Técnico a Incidencia (Solo admin_general) ──────────────────
@router.patch("/{identificador}/asignar-tecnico", summary="RF-13 – Asignar técnico responsable")
async def asignar_tecnico(
    identificador: str,
    payload: AsignarTecnicoRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(requerir_roles(["admin_general"])),
):
    """
    RF-13: El Administrador General asigna un técnico responsable a una incidencia.
    Cualquier rol distinto al Administrador General recibe HTTP 403.
    """
    await _obtener_incidencia_or_404(db, identificador)

    try:
        tec_oid = ObjectId(payload.tecnico_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="tecnico_id no es un ObjectId válido.")

    # Verificar que el usuario exista y tenga rol tecnico
    tecnico = await db["usuarios"].find_one({"_id": tec_oid, "rol": "tecnico"})
    if not tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un usuario técnico con ID '{payload.tecnico_id}'.",
        )

    filtro = _construir_filtro_identificador(identificador)
    await db[COLECCION].update_one(
        filtro,
        {
            "$set": {
                "tecnico_asignado": {
                    "usuario_id": tec_oid,
                    "nombre": tecnico.get("nombre"),
                }
            }
        },
    )

    doc_actualizado = await _obtener_incidencia_or_404(db, identificador)
    return serialize_doc(doc_actualizado)


# ── CU-02: Cargar Evidencia Multimedia (RF-05) ────────────────────────────────
@router.post("/{identificador}/evidencias", summary="CU-02 / RF-05 – Cargar evidencia multimedia")
async def cargar_evidencia(
    identificador: str,
    payload: CargarEvidencia,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(requerir_roles(["reportante", "tecnico", "admin_general"])),
):
    """
    CU-02 / RF-05: Asocia metadatos de evidencias multimedia al arreglo evidencias_adjuntas con $push.
    Permitido para reportante, técnico y administrador general.
    """
    doc_inc = await _obtener_incidencia_or_404(db, identificador)

    # Si es reportante, verificar que sea el dueño de la incidencia
    if usuario.get("rol") == "reportante" and doc_inc.get("reportante", {}).get("usuario_id") != usuario["_id"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para adjuntar evidencias en esta incidencia.")

    filtro = _construir_filtro_identificador(identificador)
    nueva_evidencia = {
        "nombre_archivo": payload.nombre_archivo,
        "tipo_mime": payload.tipo_mime,
        "peso_kb": payload.peso_kb,
        "url_storage": payload.url_storage,
        "fecha_carga": datetime.now(timezone.utc),
    }

    try:
        res = await db[COLECCION].update_one(filtro, {"$push": {"evidencias_adjuntas": nueva_evidencia}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Incidencia no encontrada.")
    except WriteError as we:
        raise HTTPException(status_code=400, detail=f"Error de validación de evidencia: {we.details}")

    doc_actualizado = await _obtener_incidencia_or_404(db, identificador)
    return serialize_doc(doc_actualizado)


# ── CU-02: Subir archivo de evidencia a Cloud Storage (RF-05) ─────────────────
@router.post(
    "/{identificador}/evidencias/archivo",
    status_code=status.HTTP_201_CREATED,
    summary="CU-02 / RF-05 – Subir archivo de evidencia al bucket y registrar metadatos",
)
async def subir_evidencia(
    identificador: str,
    archivo: UploadFile = File(..., description="Imagen (JPG/PNG), PDF o video MP4"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(requerir_roles(["reportante", "tecnico", "admin_general"])),
):
    """
    1. Sube el archivo físico a Supabase Storage (o a la carpeta local en desarrollo).
    2. Registra solo los metadatos en evidencias_adjuntas con $push.
    El binario nunca se guarda en MongoDB (límite de 512 MB de la capa M0).
    """
    doc_inc = await _obtener_incidencia_or_404(db, identificador)
    if usuario.get("rol") == "reportante" and doc_inc.get("reportante", {}).get("usuario_id") != usuario["_id"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para adjuntar evidencias en esta incidencia.")

    tipo_mime = archivo.content_type or ""
    if tipo_mime not in MIMES_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido ({tipo_mime or 'desconocido'}). Usa JPG, PNG, PDF o MP4.",
        )

    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(contenido) > settings.evidencia_max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"El archivo supera el máximo de {settings.evidencia_max_mb} MB.")

    nombre_limpio = re.sub(r"[^A-Za-z0-9._-]+", "_", archivo.filename or "evidencia")[:80]
    ahora = datetime.now(timezone.utc)
    ruta = f"incidencias/{doc_inc['codigo']}/{ahora:%Y%m%d%H%M%S}_{nombre_limpio}"

    try:
        await storage.subir_archivo(ruta, contenido, tipo_mime)
    except Exception as e:
        logger.error(f"Error al subir evidencia: {e}")
        raise HTTPException(status_code=502, detail="No se pudo subir el archivo al almacenamiento externo.")

    nueva_evidencia = {
        "nombre_archivo": nombre_limpio,
        "tipo_mime": tipo_mime,
        "peso_kb": max(1, round(len(contenido) / 1024)),
        "url_storage": ruta,
        "fecha_carga": ahora,
    }
    try:
        await db[COLECCION].update_one(
            {"_id": doc_inc["_id"]}, {"$push": {"evidencias_adjuntas": nueva_evidencia}}
        )
    except WriteError as we:
        raise HTTPException(status_code=400, detail=f"Error de validación de evidencia: {we.details}")

    doc_actualizado = await _obtener_incidencia_or_404(db, identificador)
    return serialize_doc(doc_actualizado)


# ── CU-02: URL firmada temporal para ver una evidencia ────────────────────────
@router.get("/{identificador}/evidencias/{indice}/url", summary="CU-02 – Generar URL firmada de una evidencia")
async def url_evidencia(
    identificador: str,
    indice: int,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_actual),
):
    """Genera un enlace de acceso temporal (10 minutos) al archivo guardado en el bucket."""
    doc = await _obtener_incidencia_or_404(db, identificador)
    if usuario.get("rol") == "reportante" and doc.get("reportante", {}).get("usuario_id") != usuario["_id"]:
        raise HTTPException(status_code=403, detail="Acceso restringido a expedientes propios.")

    evidencias = doc.get("evidencias_adjuntas", [])
    if indice < 0 or indice >= len(evidencias):
        raise HTTPException(status_code=404, detail="Evidencia no encontrada.")

    ruta = evidencias[indice].get("url_storage", "")
    try:
        url = await storage.generar_url_firmada(ruta, str(request.base_url))
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="El archivo no está en el almacenamiento (las evidencias de ejemplo solo tienen metadatos).",
        )
    return {"url": url, "expira_en_segundos": settings.url_firmada_segundos}


# ── CU-03: Actualizar Estado y Bitácora Atómica (RF-06) ────────────────────────
@router.patch("/{identificador}/estado", summary="CU-03 / RF-06 – Actualizar estado y bitácora")
async def actualizar_estado(
    identificador: str,
    payload: ActualizarEstado,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(requerir_roles(["tecnico", "admin_general"])),
):
    """
    CU-03 / RF-06: Operación atómica de actualización sin condiciones de carrera.
    - $set: estado nuevo (y fecha_resolucion si pasa a resuelta).
    - $push: entrada en historial_seguimiento con tecnico, comentario y horas.
    - $inc: horas_invertidas acumuladas.
    Precondición: incidencia en estado abierta, en proceso o en espera.
    Permitido para técnico y administrador general.
    """
    incidencia_actual = await _obtener_incidencia_or_404(db, identificador)
    estado_actual = incidencia_actual["estado"]

    if estado_actual not in ESTADOS_ABIERTOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se puede actualizar una incidencia en estado '{estado_actual}'. "
                f"Debe encontrarse en uno de: {ESTADOS_ABIERTOS}."
            ),
        )

    ahora = datetime.now(timezone.utc)
    tecnico_nombre = payload.tecnico or usuario.get("nombre", "Técnico")

    cambios: dict = {
        "$set": {"estado": payload.nuevo_estado},
        "$inc": {"horas_invertidas": payload.horas},
        "$push": {
            "historial_seguimiento": {
                "fecha": ahora,
                "tecnico": tecnico_nombre,
                "estado": payload.nuevo_estado,
                "horas": payload.horas,
                "comentario": payload.comentario,
            }
        },
    }

    if payload.nuevo_estado in ["resuelta", "cerrada"]:
        cambios["$set"]["fecha_resolucion"] = ahora

    filtro = {
        **_construir_filtro_identificador(identificador),
        "estado": {"$in": ESTADOS_ABIERTOS},
    }

    res = await db[COLECCION].update_one(filtro, cambios)
    if res.matched_count == 0:
        raise HTTPException(
            status_code=400,
            detail="La incidencia ya fue modificada concurrentemente o no cumple la precondición de estado.",
        )

    doc_actualizado = await _obtener_incidencia_or_404(db, identificador)
    return serialize_doc(doc_actualizado)


# ── CU-04: Gestionar Etiquetas Técnicas Dinámicas (RF-07) ─────────────────────
@router.patch("/{identificador}/tags", summary="CU-04 / RF-07 – Gestionar etiquetas técnicas")
async def gestionar_tags(
    identificador: str,
    payload: GestionarTags,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(requerir_roles(["tecnico", "admin_general"])),
):
    """
    CU-04 / RF-07:
    - Para agregar: operador $addToSet con $each (evita duplicados).
    - Para retirar: operador $pull con $in.
    Permitido para técnico y administrador general.
    """
    await _obtener_incidencia_or_404(db, identificador)
    filtro = _construir_filtro_identificador(identificador)

    if payload.accion == "agregar":
        operacion = {"$addToSet": {"tags": {"$each": payload.tags}}}
    else:
        operacion = {"$pull": {"tags": {"$in": payload.tags}}}

    try:
        await db[COLECCION].update_one(filtro, operacion)
    except WriteError as we:
        raise HTTPException(status_code=400, detail=f"Error en modificación de tags: {we.details}")

    doc_actualizado = await _obtener_incidencia_or_404(db, identificador)
    return serialize_doc(doc_actualizado)
