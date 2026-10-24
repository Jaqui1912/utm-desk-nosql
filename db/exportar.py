
import argparse
import os
import sys
from pathlib import Path

from bson import json_util
from dotenv import load_dotenv
from pymongo import MongoClient

DB_NAME = "utm_desk"
CARPETA = Path(__file__).resolve().parent / "export"
OPCIONES = json_util.RELAXED_JSON_OPTIONS        # {"$oid": ...} y {"$date": "...Z"}


def volcar(objeto, ruta):
    texto = json_util.dumps(objeto, indent=2, ensure_ascii=False, json_options=OPCIONES)
    ruta.write_text(texto + "\n", encoding="utf-8")


def exportar_coleccion(db, nombre, orden, quitar=()):
    docs = list(db[nombre].find().sort(orden, 1))
    for d in docs:
        for campo in quitar:
            d.pop(campo, None)
    return docs


def exportar_esquema(db, nombres):
    resultado = []
    for nombre in nombres:
        info = next(iter(db.list_collections(filter={"name": nombre})), {})
        opciones = info.get("options", {})
        indices = []
        for ix in db[nombre].list_indexes():
            ix = dict(ix)
            ix.pop("v", None)
            indices.append(ix)
        resultado.append({
            "coleccion": nombre,
            "validador": opciones.get("validator"),
            "nivel_de_validacion": opciones.get("validationLevel"),
            "accion_de_validacion": opciones.get("validationAction"),
            "indices": indices,
        })
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Exporta la base de datos a JSON.")
    parser.add_argument("--con-hash", action="store_true",
                        help="incluir password_hash en usuarios.json")
    args = parser.parse_args()

    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("Falta MONGODB_URI. Revisa el archivo .env en la raíz del repo.")
    db = MongoClient(uri, serverSelectionTimeoutMS=8000)[DB_NAME]

    CARPETA.mkdir(exist_ok=True)
    incidencias = exportar_coleccion(db, "incidencias_campus", "codigo")
    usuarios = exportar_coleccion(db, "usuarios", "correo",
                                  quitar=() if args.con_hash else ("password_hash",))
    volcar(incidencias, CARPETA / "incidencias_campus.json")
    volcar(usuarios, CARPETA / "usuarios.json")
    volcar(exportar_esquema(db, ["usuarios", "incidencias_campus"]),
           CARPETA / "esquema_y_indices.json")

    print(f"[+] {len(incidencias)} incidencias -> db/export/incidencias_campus.json")
    print(f"[+] {len(usuarios)} usuarios -> db/export/usuarios.json"
          + ("" if args.con_hash else " (sin password_hash)"))
    print("[+] Validador e índices -> db/export/esquema_y_indices.json")
    if not incidencias:
        print("Aviso: la colección de incidencias está vacía. ¿Ya corriste db/seed.py?")


if __name__ == "__main__":
    main()