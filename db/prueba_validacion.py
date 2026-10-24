"""
Comprueba en Atlas que el validador acepta lo correcto y rechaza lo incorrecto.

Inserta documentos de prueba y los borra al terminar, aunque algo falle.
"""
import copy
import os
import sys
from datetime import datetime, timezone

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, WriteError

load_dotenv()
uri = os.environ.get("MONGODB_URI")
if not uri:
    sys.exit("Falta MONGODB_URI en el archivo .env")

db = MongoClient(uri, serverSelectionTimeoutMS=8000)["utm_desk"]
incidencias = db["incidencias_campus"]
usuarios = db["usuarios"]

AHORA = datetime.now(timezone.utc)
CODIGO_PRUEBA = "INC-9999-0001"
CORREO_PRUEBA = "prueba.validacion@utm.example"

base = {
    "codigo": CODIGO_PRUEBA,
    "titulo": "Prueba de validación de esquema",
    "descripcion": "Documento temporal para verificar el validador de la colección.",
    "categoria": "computo_redes",
    "prioridad": "alta",
    "estado": "abierta",
    "reportante": {"usuario_id": ObjectId(), "nombre": "Prueba",
                   "tipo": "docente", "correo": "p@utm.example"},
    "ubicacion": {"edificio": "Edificio A", "zona": "Laboratorio 1", "piso": 1},
    "fecha_creacion": AHORA,
    "horas_invertidas": 0,
    "tags": ["prueba"],
    "detalle_especifico": {"equipo_afectado": "Switch", "direccion_ip": "10.0.0.1",
                           "vlan": 10, "puerto_uplink": "Gi1/0/1", "equipos_afectados": 3},
    "historial_seguimiento": [],
    "evidencias_adjuntas": [],
}


def con(**cambios):
    d = copy.deepcopy(base)
    d.update(cambios)
    return d


def sin_tipo():
    d = copy.deepcopy(base)
    d["reportante"].pop("tipo")
    return d


def vlan_decimal():
    d = copy.deepcopy(base)
    d["detalle_especifico"]["vlan"] = 10.0
    return d


rechazos = {
    "Detalle de otra categoría": con(detalle_especifico={"tipo_dano": "filtracion",
                                                         "riesgo_seguridad": True}),
    "VLAN como decimal (10.0)": vlan_decimal(),
    "Estado fuera de la lista": con(estado="pendiente"),
    "Reportante sin 'tipo'": sin_tipo(),
    "Campo que no existe en el modelo": con(campo_inventado=1),
    "Etiquetas duplicadas": con(tags=["red", "red"]),
    "Código con formato incorrecto": con(codigo="INC-26-1"),
}

fallos = 0
try:
    print("\n== Debe ACEPTAR ==")
    r = incidencias.insert_one(base)
    print("  [OK] Incidencia válida insertada")

    print("\n== Debe RECHAZAR (código 121 = falló la validación) ==")
    for nombre, doc in rechazos.items():
        try:
            incidencias.insert_one(doc)
            print(f"  [ERROR] Se aceptó: {nombre}")
            fallos += 1
        except WriteError as e:
            if e.code == 121:
                print(f"  [OK] Rechazado: {nombre}")
            else:
                print(f"  [?] {nombre}: error distinto ({e.code})")
                fallos += 1

    print("\n== Usuarios ==")
    hash_falso = "$2b$12$" + "a" * 53
    tecnico = {"nombre": "Usuario de Prueba", "correo": CORREO_PRUEBA,
               "password_hash": hash_falso, "rol": "tecnico",
               "especialidades": ["computo_redes"], "activo": True, "fecha_alta": AHORA}
    usuarios.insert_one(copy.deepcopy(tecnico))
    print("  [OK] Usuario válido insertado")

    try:
        usuarios.insert_one(copy.deepcopy(tecnico))
        print("  [ERROR] Se aceptó un correo repetido")
        fallos += 1
    except DuplicateKeyError:
        print("  [OK] Rechazado: correo repetido")

    reportante_sin_tipo = dict(copy.deepcopy(tecnico), correo="otro." + CORREO_PRUEBA, rol="reportante")
    reportante_sin_tipo.pop("especialidades")
    try:
        usuarios.insert_one(reportante_sin_tipo)
        print("  [ERROR] Se aceptó un reportante sin tipo")
        fallos += 1
    except WriteError as e:
        print("  [OK] Rechazado: reportante sin tipo" if e.code == 121
              else f"  [?] error distinto ({e.code})")
finally:
    incidencias.delete_many({"codigo": CODIGO_PRUEBA})
    usuarios.delete_many({"correo": {"$in": [CORREO_PRUEBA, "otro." + CORREO_PRUEBA]}})
    print("\nDocumentos de prueba eliminados.")

print("\nTodo correcto." if fallos == 0 else f"\nHay {fallos} problema(s). Revisa el validador.")
sys.exit(1 if fallos else 0)