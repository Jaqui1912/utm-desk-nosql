from datetime import datetime
from typing import Any, Literal, Optional, Union
from bson import ObjectId
from pydantic import BaseModel, Field

# ── Tipos y Enums según el esquema oficial de Atlas ───────────────────────────
CategoriaEnum = Literal["computo_redes", "infraestructura", "academico"]
EstadoEnum = Literal["abierta", "en proceso", "en espera", "resuelta", "cerrada"]
PrioridadEnum = Literal["baja", "media", "alta", "critica"]
TipoReportanteEnum = Literal["docente", "estudiante", "administrativo"]
TipoMimeEnum = Literal["image/jpeg", "image/png", "application/pdf", "video/mp4"]


# ── Subdocumentos de detalle_especifico polimórficos ──────────────────────────
class DetalleComputoRedes(BaseModel):
    equipo_afectado: str = Field(..., min_length=2)
    direccion_ip: str
    vlan: int = Field(..., ge=1, le=4094)
    puerto_uplink: str
    equipos_afectados: int = Field(..., ge=0)

    model_config = {"extra": "forbid"}


class ContratistaModel(BaseModel):
    empresa: str = Field(..., min_length=2)
    intervencion: str = Field(..., min_length=2)

    model_config = {"extra": "forbid"}


class DetalleInfraestructura(BaseModel):
    tipo_dano: str = Field(..., min_length=2)
    riesgo_seguridad: bool
    insumos_requeridos: Optional[list[str]] = None
    contratista: Optional[ContratistaModel] = None

    model_config = {"extra": "forbid"}


class DetalleAcademico(BaseModel):
    plataforma: str = Field(..., min_length=2)
    codigo_curso: str = Field(..., min_length=2)
    periodo_escolar: str = Field(..., min_length=2)
    estudiantes_impactados: int = Field(..., ge=0)

    model_config = {"extra": "forbid"}


# ── Estructuras anidadas de la incidencia ──────────────────────────────────────
class ReportanteModel(BaseModel):
    usuario_id: str = Field(..., description="ObjectId del usuario en colección usuarios")
    nombre: str = Field(..., min_length=3)
    tipo: TipoReportanteEnum
    correo: str

    model_config = {"extra": "forbid"}


class TecnicoAsignadoModel(BaseModel):
    usuario_id: str
    nombre: str

    model_config = {"extra": "forbid"}


class UbicacionModel(BaseModel):
    edificio: str = Field(..., min_length=2)
    zona: str = Field(..., min_length=2)
    piso: Optional[int] = Field(None, ge=0)

    model_config = {"extra": "forbid"}


class EntradaHistorialModel(BaseModel):
    fecha: datetime = Field(default_factory=datetime.utcnow)
    tecnico: str = Field(..., min_length=2)
    estado: EstadoEnum
    horas: float = Field(..., ge=0)
    comentario: str = Field(..., min_length=5)

    model_config = {"extra": "forbid"}


class EvidenciaAdjuntaModel(BaseModel):
    nombre_archivo: str = Field(..., min_length=3)
    tipo_mime: TipoMimeEnum
    peso_kb: int = Field(..., ge=1)
    url_storage: str
    fecha_carga: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"extra": "forbid"}


# ── Request Payloads (Casos de Uso) ───────────────────────────────────────────
class IncidenciaCreate(BaseModel):
    """CU-01: Alta de Incidencia Polimórfica."""
    titulo: str = Field(..., min_length=5, max_length=150)
    descripcion: str = Field(..., min_length=10)
    categoria: CategoriaEnum
    prioridad: PrioridadEnum
    reportante: ReportanteModel
    ubicacion: UbicacionModel
    detalle_especifico: Union[DetalleComputoRedes, DetalleInfraestructura, DetalleAcademico, dict[str, Any]]
    tags: list[str] = Field(default_factory=list)
    tecnico_asignado: Optional[TecnicoAsignadoModel] = None


class CargarEvidencia(BaseModel):
    """CU-02: Cargar evidencia multimedia con metadatos."""
    nombre_archivo: str = Field(..., min_length=3)
    tipo_mime: TipoMimeEnum
    peso_kb: int = Field(..., ge=1)
    url_storage: str


class ActualizarEstado(BaseModel):
    """CU-03: Actualizar Estado y Bitácora Atómica ($set, $push, $inc)."""
    nuevo_estado: EstadoEnum
    horas: float = Field(..., ge=0)
    comentario: str = Field(..., min_length=5)
    tecnico: str = Field(..., min_length=2)


class GestionarTags(BaseModel):
    """CU-04: Gestión de Etiquetas Técnicas ($addToSet / $pull)."""
    accion: Literal["agregar", "quitar"]
    tags: list[str] = Field(..., min_length=1)


# ── Helper de Serialización BSON -> JSON ───────────────────────────────────────
def serialize_doc(doc: Any) -> Any:
    """Convierte recursivamente ObjectIds y datetimes para que sean JSON-serializables."""
    if isinstance(doc, dict):
        res = {}
        for k, v in doc.items():
            if k == "_id":
                res["id"] = str(v)
                res["_id"] = str(v)
            else:
                res[k] = serialize_doc(v)
        return res
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    return doc
