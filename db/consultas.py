
import os
import sys
from datetime import datetime, timezone

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

ESTADOS_ABIERTOS = ["abierta", "en proceso", "en espera"]
MS_POR_HORA = 3_600_000


# ----------------------------------------------------------------------------
# CU-02: evidencias 
# ----------------------------------------------------------------------------
def agregar_evidencia(col, codigo, nombre_archivo, tipo_mime, peso_kb, url_storage):
    evidencia = {
        "nombre_archivo": nombre_archivo,
        "tipo_mime": tipo_mime,
        "peso_kb": int(peso_kb),
        "url_storage": url_storage,          # ruta dentro del bucket, no la URL firmada
        "fecha_carga": datetime.now(timezone.utc),
    }
    return col.update_one({"codigo": codigo}, {"$push": {"evidencias_adjuntas": evidencia}})


# ----------------------------------------------------------------------------
# CU-03: estado + horas + bitácora en una sola operación atómica
# ----------------------------------------------------------------------------
def actualizar_estado(col, codigo, nuevo_estado, horas, comentario, tecnico):
    ahora = datetime.now(timezone.utc)
    cambios = {
        "$set": {"estado": nuevo_estado},                       # $set
        "$inc": {"horas_invertidas": horas},                    # $inc
        "$push": {"historial_seguimiento": {                    # $push
            "fecha": ahora,
            "tecnico": tecnico,
            "estado": nuevo_estado,
            "horas": horas,
            "comentario": comentario,
        }},
    }
    if nuevo_estado == "resuelta":
        cambios["$set"]["fecha_resolucion"] = ahora             # activa el TTL de 60 días
    # Precondición del CU-03: la incidencia debe seguir abierta, en proceso o en espera
    filtro = {"codigo": codigo, "estado": {"$in": ESTADOS_ABIERTOS}}
    return col.update_one(filtro, cambios)       # matched_count == 0 -> no cumple la precondición


# ----------------------------------------------------------------------------
# CU-04: etiquetas
# ----------------------------------------------------------------------------
def agregar_tags(col, codigo, tags):
    """$addToSet con $each: agrega varias etiquetas sin duplicar las existentes."""
    return col.update_one({"codigo": codigo}, {"$addToSet": {"tags": {"$each": tags}}})


def quitar_tag(col, codigo, tag):
    return col.update_one({"codigo": codigo}, {"$pull": {"tags": tag}})


# ----------------------------------------------------------------------------
# CU-05: búsqueda de texto ponderada, ordenada por relevancia
# ----------------------------------------------------------------------------
def buscar_texto(col, palabras, usuario_id=None, limite=10):
    """Si se pasa usuario_id (rol reportante), solo busca entre sus incidencias."""
    filtro = {"$text": {"$search": palabras}}
    if usuario_id is not None:
        filtro["reportante.usuario_id"] = usuario_id
    proyeccion = {"codigo": 1, "titulo": 1, "estado": 1, "prioridad": 1,
                  "score": {"$meta": "textScore"}}
    return list(col.find(filtro, proyeccion)
                .sort([("score", {"$meta": "textScore"})])
                .limit(limite))


# ----------------------------------------------------------------------------
# CU-06: pipelines analíticos
# ----------------------------------------------------------------------------
# Pipeline 1: eficiencia por edificio.
# Horas de resolución = tiempo transcurrido desde fecha_creacion hasta fecha_resolucion.
PIPELINE_EDIFICIOS = [
    {"$match": {"estado": {"$in": ["resuelta", "cerrada"]},
                "fecha_resolucion": {"$exists": True}}},
    {"$addFields": {"horas_resolucion": {
        "$divide": [{"$subtract": ["$fecha_resolucion", "$fecha_creacion"]}, MS_POR_HORA]}}},
    {"$group": {
        "_id": "$ubicacion.edificio",
        "incidencias": {"$sum": 1},
        "promedio_horas": {"$avg": "$horas_resolucion"},
        "total_horas": {"$sum": "$horas_resolucion"},
    }},
    {"$sort": {"promedio_horas": -1}},
    {"$project": {"_id": 0, "edificio": "$_id", "incidencias": 1,
                  "promedio_horas": {"$round": ["$promedio_horas", 1]},
                  "total_horas": {"$round": ["$total_horas", 1]}}},
]

# Pipeline 2: las 10 etiquetas más frecuentes (fallas recurrentes).
PIPELINE_TAGS = [
    {"$unwind": "$tags"},
    {"$group": {"_id": "$tags", "total": {"$sum": 1}}},
    {"$sort": {"total": -1, "_id": 1}},
    {"$limit": 10},
    {"$project": {"_id": 0, "tag": "$_id", "total": 1}},
]


def analitica_edificios(col):
    return list(col.aggregate(PIPELINE_EDIFICIOS))


def analitica_tags(col):
    return list(col.aggregate(PIPELINE_TAGS))


# ----------------------------------------------------------------------------
# Demostración contra Atlas
# ----------------------------------------------------------------------------
def _demo():
    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("Falta MONGODB_URI en el archivo .env")
    col = MongoClient(uri, serverSelectionTimeoutMS=8000)["utm_desk"]["incidencias_campus"]

    print("\n== CU-06 Pipeline 1: horas de resolución por edificio ==")
    for fila in analitica_edificios(col):
        print("  ", fila)
    print("\n== CU-06 Pipeline 2: top 10 etiquetas ==")
    for fila in analitica_tags(col):
        print("  ", fila)

    codigo = "INC-9999-0002"
    uid = ObjectId()
    doc = {
        "codigo": codigo,
        "titulo": "Incidencia temporal de demostración",
        "descripcion": "Documento temporal para probar las consultas del sistema.",
        "categoria": "computo_redes", "prioridad": "media", "estado": "abierta",
        "reportante": {"usuario_id": uid, "nombre": "Prueba", "tipo": "docente",
                       "correo": "p@utm.example"},
        "ubicacion": {"edificio": "Edificio A", "zona": "Laboratorio 1", "piso": 1},
        "fecha_creacion": datetime.now(timezone.utc),
        "horas_invertidas": 0, "tags": ["red"],
        "detalle_especifico": {"equipo_afectado": "Switch", "direccion_ip": "10.0.0.2",
                               "vlan": 10, "puerto_uplink": "Gi1/0/2", "equipos_afectados": 2},
        "historial_seguimiento": [], "evidencias_adjuntas": [],
    }
    try:
        col.insert_one(doc)
        print(f"\n== Documento temporal {codigo} insertado ==")

        r = actualizar_estado(col, codigo, "resuelta", 1.5, "Se reemplazó el cable.", "Carlos Pech")
        d = col.find_one({"codigo": codigo})
        print(f"CU-03 actualizar_estado -> modificados: {r.modified_count} | estado: {d['estado']} | "
              f"horas: {d['horas_invertidas']} | historial: {len(d['historial_seguimiento'])} | "
              f"fecha_resolucion: {'sí' if 'fecha_resolucion' in d else 'no'}")

        r = actualizar_estado(col, codigo, "en proceso", 1, "Intento sobre una incidencia ya resuelta", "Carlos Pech")
        print(f"CU-03 precondición (ya resuelta) -> modificados: {r.modified_count} (debe ser 0)")

        agregar_tags(col, codigo, ["red", "cableado"])
        print("CU-04 $addToSet (red ya existía) ->", col.find_one({'codigo': codigo})["tags"])
        quitar_tag(col, codigo, "cableado")
        print("CU-04 $pull ->", col.find_one({'codigo': codigo})["tags"])

        agregar_evidencia(col, codigo, "foto.jpg", "image/jpeg", 300, f"incidencias/{codigo}/foto.jpg")
        print("CU-02 $push -> evidencias:", len(col.find_one({'codigo': codigo})["evidencias_adjuntas"]))

        print("CU-05 búsqueda 'demostración' ->",
              [(x["codigo"], round(x["score"], 2)) for x in buscar_texto(col, "demostración")])
        print("CU-05 como reportante ajeno   ->", len(buscar_texto(col, "demostración", usuario_id=ObjectId())), "resultados (debe ser 0)")
    finally:
        col.delete_many({"codigo": codigo})
        print("\nDocumento temporal eliminado.")


if __name__ == "__main__":
    _demo()