
"""
Creación de las conexiones

"""
import argparse
import os
import sys
 
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure
 
DB_NAME = "utm_desk"
COL_INCIDENCIAS = "incidencias_campus"
COL_USUARIOS = "usuarios"
 
CATEGORIAS = ["computo_redes", "infraestructura", "academico"]
ESTADOS = ["abierta", "en proceso", "en espera", "resuelta", "cerrada"]
PRIORIDADES = ["baja", "media", "alta", "critica"]
ROLES = ["reportante", "admin_general", "tecnico", "directivo", "admin_sistema"]
TIPOS_REPORTANTE = ["docente", "estudiante", "administrativo"]
TIPOS_MIME = ["image/jpeg", "image/png", "application/pdf", "video/mp4"]
NUMERO = ["double", "int"]          
TTL_SEGUNDOS = 60 * 24 * 60 * 60    
 
 
# ----------------------------------------------------------------------------
# Esquema de la colección incidencias_campus
# ----------------------------------------------------------------------------
def _por_categoria(categoria, detalle):
    """Rama del oneOf: si la categoría es X, el detalle debe tener la forma de X."""
    return {
        "properties": {
            "categoria": {"enum": [categoria]},
            "detalle_especifico": detalle,
        }
    }
 
 
def schema_incidencias():
    detalle_computo = {
        "bsonType": "object",
        "required": ["equipo_afectado", "direccion_ip", "vlan",
                     "puerto_uplink", "equipos_afectados"],
        "additionalProperties": False,
        "properties": {
            "equipo_afectado": {"bsonType": "string"},
            "direccion_ip": {"bsonType": "string"},
            "vlan": {"bsonType": "int", "minimum": 1, "maximum": 4094},
            "puerto_uplink": {"bsonType": "string"},
            "equipos_afectados": {"bsonType": "int", "minimum": 0},
        },
    }
    detalle_infra = {
        "bsonType": "object",
        "required": ["tipo_dano", "riesgo_seguridad"],
        "additionalProperties": False,
        "properties": {
            "tipo_dano": {"bsonType": "string"},
            "riesgo_seguridad": {"bsonType": "bool"},
            "insumos_requeridos": {"bsonType": "array", "items": {"bsonType": "string"}},
            "contratista": {
                "bsonType": "object",
                "required": ["empresa", "intervencion"],
                "additionalProperties": False,
                "properties": {
                    "empresa": {"bsonType": "string"},
                    "intervencion": {"bsonType": "string"},
                },
            },
        },
    }
    detalle_academico = {
        "bsonType": "object",
        "required": ["plataforma", "codigo_curso", "periodo_escolar",
                     "estudiantes_impactados"],
        "additionalProperties": False,
        "properties": {
            "plataforma": {"bsonType": "string"},
            "codigo_curso": {"bsonType": "string"},
            "periodo_escolar": {"bsonType": "string"},
            "estudiantes_impactados": {"bsonType": "int", "minimum": 0},
        },
    }
 
    return {
        "bsonType": "object",
        "required": ["codigo", "titulo", "descripcion", "categoria", "prioridad",
                     "estado", "reportante", "ubicacion", "fecha_creacion",
                     "horas_invertidas", "tags", "detalle_especifico",
                     "historial_seguimiento", "evidencias_adjuntas"],
        "additionalProperties": False,   # rechaza campos que no están en el modelo
        "properties": {
            "_id": {"bsonType": "objectId"},
            "codigo": {"bsonType": "string", "pattern": r"^INC-\d{4}-\d{4}$"},
            "titulo": {"bsonType": "string", "minLength": 5, "maxLength": 150},
            "descripcion": {"bsonType": "string", "minLength": 10},
            "categoria": {"enum": CATEGORIAS},
            "prioridad": {"enum": PRIORIDADES},
            "estado": {"enum": ESTADOS},
            "reportante": {
                "bsonType": "object",
                "required": ["usuario_id", "nombre", "tipo", "correo"],
                "additionalProperties": False,
                "properties": {
                    "usuario_id": {"bsonType": "objectId"},
                    "nombre": {"bsonType": "string"},
                    "tipo": {"enum": TIPOS_REPORTANTE},
                    "correo": {"bsonType": "string"},
                },
            },
            # Opcional: solo existe después de asignar al técnico (no se guarda null)
            "tecnico_asignado": {
                "bsonType": "object",
                "required": ["usuario_id", "nombre"],
                "additionalProperties": False,
                "properties": {
                    "usuario_id": {"bsonType": "objectId"},
                    "nombre": {"bsonType": "string"},
                },
            },
            "ubicacion": {
                "bsonType": "object",
                "required": ["edificio", "zona"],
                "additionalProperties": False,
                "properties": {
                    "edificio": {"bsonType": "string"},
                    "zona": {"bsonType": "string"},
                    "piso": {"bsonType": "int", "minimum": 0},
                },
            },
            "fecha_creacion": {"bsonType": "date"},
            # Opcional: solo en incidencias resueltas o cerradas (activa el índice TTL)
            "fecha_resolucion": {"bsonType": "date"},
            "horas_invertidas": {"bsonType": NUMERO, "minimum": 0},
            "tags": {"bsonType": "array", "uniqueItems": True,
                     "items": {"bsonType": "string"}},
            "detalle_especifico": {"bsonType": "object"},
            "historial_seguimiento": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["fecha", "tecnico", "estado", "horas", "comentario"],
                    "additionalProperties": False,
                    "properties": {
                        "fecha": {"bsonType": "date"},
                        "tecnico": {"bsonType": "string"},
                        "estado": {"enum": ESTADOS},
                        "horas": {"bsonType": NUMERO, "minimum": 0},
                        "comentario": {"bsonType": "string"},
                    },
                },
            },
            "evidencias_adjuntas": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["nombre_archivo", "tipo_mime", "peso_kb",
                                 "url_storage", "fecha_carga"],
                    "additionalProperties": False,
                    "properties": {
                        "nombre_archivo": {"bsonType": "string"},
                        "tipo_mime": {"enum": TIPOS_MIME},
                        "peso_kb": {"bsonType": "int", "minimum": 1},
                        "url_storage": {"bsonType": "string"},
                        "fecha_carga": {"bsonType": "date"},
                    },
                },
            },
        },
        # La forma de detalle_especifico depende de la categoría
        "oneOf": [
            _por_categoria("computo_redes", detalle_computo),
            _por_categoria("infraestructura", detalle_infra),
            _por_categoria("academico", detalle_academico),
        ],
    }
 
 
# ----------------------------------------------------------------------------
# Esquema de la colección usuarios
# ----------------------------------------------------------------------------
def schema_usuarios():
    return {
        "bsonType": "object",
        "required": ["nombre", "correo", "password_hash", "rol", "activo", "fecha_alta"],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "nombre": {"bsonType": "string", "minLength": 3},
            "correo": {"bsonType": "string",
                       "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
            "password_hash": {"bsonType": "string", "minLength": 20},
            "rol": {"enum": ROLES},
            "tipo": {"enum": TIPOS_REPORTANTE},
            "especialidades": {"bsonType": "array", "uniqueItems": True,
                               "items": {"enum": CATEGORIAS}},
            "activo": {"bsonType": "bool"},
            "fecha_alta": {"bsonType": "date"},
        },
        # Los reportantes deben indicar su tipo (docente, estudiante o administrativo)
        "oneOf": [
            {"properties": {"rol": {"enum": ["reportante"]}}, "required": ["tipo"]},
            {"properties": {"rol": {"enum": [r for r in ROLES if r != "reportante"]}}},
        ],
    }
 
 
# ----------------------------------------------------------------------------
# Creación en Atlas
# ----------------------------------------------------------------------------
def crear_o_actualizar(db, nombre, schema):
    opciones = dict(validator={"$jsonSchema": schema},
                    validationLevel="strict", validationAction="error")
    try:
        db.create_collection(nombre, **opciones)
        print(f"  [+] Colección '{nombre}' creada.")
    except CollectionInvalid:
        db.command("collMod", nombre, **opciones)
        print(f"  [~] Colección '{nombre}' ya existía: validador actualizado.")
 
 
def crear_indices(db):
    inc = db[COL_INCIDENCIAS]
    inc.create_index(
        [("categoria", 1), ("estado", 1), ("ubicacion.edificio", 1)],
        name="idx_categoria_estado_edificio",
    )
    inc.create_index(
        "fecha_resolucion",
        expireAfterSeconds=TTL_SEGUNDOS,
        name="ttl_fecha_resolucion",
    )
    inc.create_index(
        [("titulo", "text"), ("descripcion", "text")],
        weights={"titulo": 10, "descripcion": 5},
        default_language="spanish",
        name="txt_titulo_descripcion",
    )
    db[COL_USUARIOS].create_index("correo", unique=True, name="uniq_correo")
 
 
def main():
    parser = argparse.ArgumentParser(description="Crea la estructura de la base de datos.")
    parser.add_argument("--reset", action="store_true",
                        help="borra las colecciones antes de crearlas")
    args = parser.parse_args()
 
    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("Falta MONGODB_URI. Revisa que exista el archivo .env en la raíz del repo.")
 
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    db = client[DB_NAME]
    print(f"Conectado a Atlas. Base de datos: {DB_NAME}")
 
    if args.reset:
        if input("Esto BORRA 'incidencias_campus' y 'usuarios'. Escribe SI para continuar: ") != "SI":
            sys.exit("Cancelado.")
        db.drop_collection(COL_INCIDENCIAS)
        db.drop_collection(COL_USUARIOS)
        print("  [-] Colecciones borradas.")
 
    print("Colecciones:")
    crear_o_actualizar(db, COL_USUARIOS, schema_usuarios())
    crear_o_actualizar(db, COL_INCIDENCIAS, schema_incidencias())
 
    print("Índices:")
    try:
        crear_indices(db)
    except OperationFailure as e:
        sys.exit(f"No se pudo crear un índice ({e.details.get('errmsg', e)}).\n"
                 "Si ya existía con otras opciones, ejecuta de nuevo con --reset.")
 
    for nombre in (COL_INCIDENCIAS, COL_USUARIOS):
        indices = [i["name"] for i in db[nombre].list_indexes()]
        print(f"  {nombre}: {', '.join(indices)}")
    print("Listo.")
 
 
if __name__ == "__main__":
    main()
 
