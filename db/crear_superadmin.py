"""
Agrega el rol 'superAdmin' al validador de la colección usuarios y crea (o actualiza)
la cuenta de evaluación del docente, SIN borrar los datos existentes.

  Nombre:     lizandro.reyes
  Correo:     lizandro.reyes@utmetropolitana.edu.mx
  Contraseña: lizandro_2026

Uso (desde la raíz del proyecto):  python db/crear_superadmin.py
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from setup_db import COL_USUARIOS, crear_o_actualizar, schema_usuarios  # noqa: E402

NOMBRE = "lizandro.reyes"
CORREO = "lizandro.reyes@utmetropolitana.edu.mx"
PASSWORD = "lizandro_2026"


def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    uri = os.getenv("MONGODB_URI")
    if not uri:
        sys.exit("Falta MONGODB_URI en el archivo .env")
    db = MongoClient(uri, serverSelectionTimeoutMS=20000)[os.getenv("MONGODB_DB", "utm_desk")]

    # 1. Validador actualizado (incluye superAdmin en el enum de roles)
    crear_o_actualizar(db, COL_USUARIOS, schema_usuarios())

    # 2. Alta o actualización de la cuenta
    password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode()
    res = db[COL_USUARIOS].update_one(
        {"correo": CORREO},
        {
            "$set": {"nombre": NOMBRE, "password_hash": password_hash, "rol": "superAdmin", "activo": True},
            "$setOnInsert": {"fecha_alta": datetime.now(timezone.utc)},
        },
        upsert=True,
    )
    accion = "creada" if res.upserted_id else "actualizada"
    print(f"Cuenta superAdmin {accion}: {CORREO} / {PASSWORD}")


if __name__ == "__main__":
    main()
