"""
Carga los datos de prueba de UTM Desk NoSQL Cloud en MongoDB Atlas.

Inserta:
  * 13 usuarios (al menos uno por rol; un reportante desactivado para probar RF-14).
  * 27 incidencias: 9 por categoría, 5 edificios, las 4 prioridades y los 5 estados,
    12 con fecha de resolución y 23 con evidencias. Incluye los 3 ejemplos del reporte
    (INC-2026-0042, INC-2026-0017 e INC-2026-0051).
"""
import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

DB_NAME = "utm_desk"
DEMO_PASSWORD = "Utm2026!"          # contraseña de todos los usuarios de prueba
PERIODO = "Sep-Dic 2026"
MIME = {".jpg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf", ".mp4": "video/mp4"}


# ----------------------------------------------------------------------------
# Usuarios
# ----------------------------------------------------------------------------
# clave: (oid, nombre, correo, rol, tipo | especialidades)
USUARIOS = {
    # Reportantes (los tres primeros del reporte)
    "maria":    ("6710a1b2c3d4e5f607182931", "María López",   "m.lopez@utm.example",   "reportante", "docente"),
    "luis":     ("6710a1b2c3d4e5f607182932", "Luis Chan",     "l.chan@utm.example",    "reportante", "estudiante"),
    "ana":      ("6710a1b2c3d4e5f607182933", "Ana Pool",      "a.pool@utm.example",    "reportante", "administrativo"),
    "pedro":    ("6710a1b2c3d4e5f607182934", "Pedro Canul",   "p.canul@utm.example",   "reportante", "docente"),
    "sofia":    ("6710a1b2c3d4e5f607182935", "Sofía Uc",      "s.uc@utm.example",      "reportante", "estudiante"),
    "rosa":     ("6710a1b2c3d4e5f607182936", "Rosa May",      "r.may@utm.example",     "reportante", "administrativo"),
    # Resto de roles
    "laura":    ("6710a1b2c3d4e5f607182941", "Laura Medina",  "l.medina@utm.example",  "admin_general", None),
    "roberto":  ("6710a1b2c3d4e5f607182942", "Roberto Cetina", "r.cetina@utm.example", "directivo", None),
    "soporte":  ("6710a1b2c3d4e5f607182943", "Soporte UTM Desk", "soporte@utm.example", "admin_sistema", None),
    "carlos":   ("6710a1b2c3d4e5f607182945", "Carlos Pech",   "c.pech@utm.example",    "tecnico", ["computo_redes", "infraestructura"]),
    "jorge":    ("6710a1b2c3d4e5f607182946", "Jorge Cauich",  "j.cauich@utm.example",  "tecnico", ["infraestructura"]),
    "diana":    ("6710a1b2c3d4e5f607182947", "Diana Euán",    "d.euan@utm.example",    "tecnico", ["academico", "computo_redes"]),
    # Usuario desactivado (para probar que no puede iniciar sesión)
    "mario":    ("6710a1b2c3d4e5f607182937", "Mario Dzul",    "m.dzul@utm.example",    "reportante", "docente"),
    # Cuenta de evaluación solicitada por el docente (rol superAdmin, acceso total)
    "lizandro": ("6710a1b2c3d4e5f607182950", "lizandro.reyes", "lizandro.reyes@utmetropolitana.edu.mx", "superAdmin", None),
}

# Contraseñas distintas a la de demostración
PASSWORDS_ESPECIALES = {"lizandro": "lizandro_2026"}


def construir_usuarios(ahora):
    try:
        import bcrypt
    except ImportError:
        sys.exit("Falta la librería bcrypt. Instálala con:  pip install bcrypt")
    hash_demo = lambda pw=DEMO_PASSWORD: bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()
    docs = {}
    for clave, (oid, nombre, correo, rol, extra) in USUARIOS.items():
        d = {
            "_id": ObjectId(oid), "nombre": nombre, "correo": correo,
            "password_hash": hash_demo(PASSWORDS_ESPECIALES.get(clave, DEMO_PASSWORD)), "rol": rol,
            "activo": clave != "mario",
            "fecha_alta": ahora - timedelta(days=40),
        }
        if rol == "reportante":
            d["tipo"] = extra
        if rol == "tecnico":
            d["especialidades"] = extra
        docs[clave] = d
    return docs


# ----------------------------------------------------------------------------
# Incidencias
# ----------------------------------------------------------------------------
def _computo(equipo, ip, vlan, uplink, afectados):
    return {"equipo_afectado": equipo, "direccion_ip": ip, "vlan": vlan,
            "puerto_uplink": uplink, "equipos_afectados": afectados}


def _infra(dano, riesgo, insumos=None, contratista=None):
    d = {"tipo_dano": dano, "riesgo_seguridad": riesgo}
    if insumos:
        d["insumos_requeridos"] = insumos
    if contratista:
        d["contratista"] = {"empresa": contratista[0], "intervencion": contratista[1]}
    return d


def _academico(plataforma, curso, estudiantes):
    return {"plataforma": plataforma, "codigo_curso": curso,
            "periodo_escolar": PERIODO, "estudiantes_impactados": estudiantes}


# Cada incidencia: codigo, categoria, titulo, descripcion, prioridad, estado, ubicacion,
# reportante, tecnico, dias (hace cuántos días se creó), tags, detalle,
# avances [(horas, comentario)] en estado "en proceso",
# final (horas, comentario) para resuelta/cerrada/en espera,
# res_h (horas entre creación y resolución), evid [(archivo, peso_kb | None)]
INCIDENCIAS = [
    # ------------------------- Cómputo y redes -------------------------
    dict(codigo="INC-2026-0001", categoria="computo_redes", prioridad="media", estado="resuelta",
         titulo="Punto de acceso Wi-Fi desconectado en la biblioteca",
         descripcion="El punto de acceso de la sala de lectura no emite señal y los usuarios no pueden conectarse.",
         ubic=("Biblioteca", "Sala de lectura", 1), rep="pedro", tec="diana", dias=20,
         tags=["wifi", "red"], detalle=_computo("Punto de acceso Wi-Fi", "10.10.40.12", 40, "Gi0/12", 30),
         avances=[(1.5, "Se verificó el cableado del punto de acceso.")],
         final=(1.0, "Se reemplazó el inyector PoE y volvió la señal."), res_h=6,
         evid=[],),
    dict(codigo="INC-2026-0002", categoria="computo_redes", prioridad="critica", estado="resuelta",
         titulo="Servidor de archivos sin respuesta",
         descripcion="El servidor de archivos no responde y se perdió el acceso a las carpetas compartidas.",
         ubic=("Edificio D", "Cuarto de servidores", 1), rep="ana", tec="carlos", dias=15,
         tags=["servidor", "urgente"], detalle=_computo("Servidor de archivos", "10.10.1.5", 10, "Te1/0/1", 85),
         avances=[(1.0, "Se reinició el servicio y no recuperó.")],
         final=(2.0, "Se reemplazó la fuente de poder y se restauró el servicio."), res_h=3,
         evid=[],),
    dict(codigo="INC-2026-0003", categoria="computo_redes", prioridad="alta", estado="resuelta",
         titulo="Switch de piso con puertos caídos",
         descripcion="Varios puertos del switch del segundo piso no entregan red a las aulas.",
         ubic=("Edificio A", "Cuarto de comunicaciones", 2), rep="maria", tec="carlos", dias=12,
         tags=["switch", "red"], detalle=_computo("Switch de acceso", "10.10.20.8", 20, "Gi1/0/48", 22),
         avances=[(2.0, "Se identificaron puertos con error de negociación.")],
         final=(3.0, "Se sustituyó el módulo de puertos."), res_h=28,
         evid=[],),
    dict(codigo="INC-2026-0004", categoria="computo_redes", prioridad="media", estado="en proceso",
         titulo="Equipos del laboratorio sin acceso a internet",
         descripcion="Los equipos del laboratorio 2 se conectan a la red local pero no tienen salida a internet.",
         ubic=("Edificio A", "Laboratorio 2", 1), rep="luis", tec="diana", dias=3,
         tags=["red", "laboratorio"], detalle=_computo("Equipos de laboratorio", "10.10.30.1", 30, "Gi1/0/12", 25),
         avances=[(2.0, "Se revisa la configuración de la VLAN y la puerta de enlace.")],
         evid=[],),
    dict(codigo="INC-2026-0005", categoria="computo_redes", prioridad="baja", estado="abierta",
         titulo="Proyector del aula sin señal HDMI",
         descripcion="El proyector del aula C-105 no detecta la señal del equipo del docente.",
         ubic=("Edificio C", "Aula C-105", 1), rep="sofia", tec=None, dias=1.5,
         tags=["proyector"], detalle=_computo("Proyector", "10.10.60.31", 60, "Gi0/5", 1),
         evid=[],),
    dict(codigo="INC-2026-0006", categoria="computo_redes", prioridad="baja", estado="cerrada",
         titulo="Impresora de control escolar fuera de la red",
         descripcion="La impresora multifuncional de control escolar ya no aparece en la red.",
         ubic=("Edificio C", "Control escolar", 1), rep="rosa", tec="diana", dias=18,
         tags=["impresora", "red"], detalle=_computo("Impresora multifuncional", "10.10.60.40", 60, "Gi0/9", 6),
         avances=[(0.5, "Se verificó la dirección IP asignada.")],
         final=(1.0, "Se reasignó una IP fija y se reinstaló el controlador."), res_h=20,
         evid=[],),
    dict(codigo="INC-2026-0007", categoria="computo_redes", prioridad="alta", estado="en espera",
         titulo="Conexión intermitente en el servidor local",
         descripcion="El servidor local se reinicia varias veces al día y interrumpe los servicios internos.",
         ubic=("Edificio D", "Cuarto de servidores", 1), rep="pedro", tec="carlos", dias=6,
         tags=["servidor", "recurrente"], detalle=_computo("Servidor de aplicaciones", "10.10.1.8", 10, "Te1/0/2", 60),
         avances=[(1.5, "Se identificó una fuente de poder defectuosa.")],
         final=(0.5, "A la espera de la refacción del proveedor."),
         evid=[],),
    dict(codigo="INC-2026-0008", categoria="computo_redes", prioridad="media", estado="abierta",
         titulo="Cableado dañado en el laboratorio 4",
         descripcion="Hay cables de red expuestos y dañados bajo las mesas del laboratorio 4.",
         ubic=("Edificio B", "Laboratorio 4", 1), rep="maria", tec=None, dias=0.5,
         tags=["cableado", "laboratorio"], detalle=_computo("Cableado estructurado", "10.10.50.1", 50, "Gi1/0/20", 12),
         evid=[],),
    # Ejemplo 1 del reporte
    dict(codigo="INC-2026-0042", categoria="computo_redes", prioridad="alta", estado="en proceso",
         titulo="Switch de distribución sin respuesta en Laboratorio 3",
         descripcion="El switch del laboratorio no responde y los equipos perdieron conexión a la red.",
         ubic=("Edificio A", "Laboratorio 3", 2), rep="maria", tec="carlos", dias=3,
         tags=["red", "switch", "laboratorio"],
         detalle=_computo("Switch de distribución", "10.10.20.5", 120, "Gi1/0/24", 14),
         avances=[(2.5, "Se detecta falla en el puerto de uplink; se solicita reemplazo de módulo.")],
         evid=[],),

    # ------------------------- Infraestructura -------------------------
    dict(codigo="INC-2026-0009", categoria="infraestructura", prioridad="baja", estado="resuelta",
         titulo="Luminarias fundidas en el pasillo",
         descripcion="Tres luminarias del pasillo de planta baja están fundidas y el área queda oscura.",
         ubic=("Edificio B", "Pasillo principal", 1), rep="ana", tec="jorge", dias=14,
         tags=["iluminacion", "electrico"], detalle=_infra("luminarias fundidas", False, ["lámparas LED"]),
         avances=[(1.0, "Se midió el voltaje de las luminarias.")],
         final=(1.5, "Se sustituyeron las tres lámparas."), res_h=8,
         evid=[],),
    dict(codigo="INC-2026-0010", categoria="infraestructura", prioridad="media", estado="en proceso",
         titulo="Aire acondicionado sin enfriar en el laboratorio",
         descripcion="El aire acondicionado del laboratorio enciende pero no enfría el ambiente.",
         ubic=("Edificio A", "Laboratorio 1", 1), rep="pedro", tec="jorge", dias=4,
         tags=["clima", "laboratorio"],
         detalle=_infra("falla de climatización", False, ["gas refrigerante"], ("Clima del Sureste", "recarga de gas")),
         avances=[(2.0, "Se revisa el compresor y se detecta baja presión.")],
         evid=[],),
    dict(codigo="INC-2026-0011", categoria="infraestructura", prioridad="media", estado="resuelta",
         titulo="Cerradura dañada en la puerta del laboratorio",
         descripcion="La cerradura de la puerta del laboratorio no gira y el acceso queda sin seguridad.",
         ubic=("Edificio C", "Laboratorio 5", 1), rep="maria", tec="jorge", dias=11,
         tags=["cerradura", "seguridad"], detalle=_infra("cerradura dañada", True, ["cerradura nueva"]),
         avances=[(1.0, "Se desmontó la cerradura para diagnóstico.")],
         final=(1.5, "Se instaló una cerradura nueva."), res_h=30,
         evid=[],),
    dict(codigo="INC-2026-0012", categoria="infraestructura", prioridad="alta", estado="en espera",
         titulo="Humedad en la pared de la biblioteca",
         descripcion="Una pared del área de acervo presenta humedad y desprendimiento de pintura.",
         ubic=("Biblioteca", "Acervo general", 1), rep="rosa", tec="jorge", dias=7,
         tags=["humedad", "recurrente"], detalle=_infra("humedad en muro", False, ["impermeabilizante"]),
         avances=[(1.0, "Se inspeccionó la pared afectada.")],
         final=(0.5, "Pendiente de autorización de presupuesto."),
         evid=[],),
    dict(codigo="INC-2026-0013", categoria="infraestructura", prioridad="baja", estado="abierta",
         titulo="Banca rota en el patio central",
         descripcion="Una banca del patio central tiene la base rota y puede ser un riesgo para quien la use.",
         ubic=("Edificio D", "Patio central", 0), rep="luis", tec=None, dias=2,
         tags=["mobiliario"], detalle=_infra("mobiliario dañado", False),
         evid=[],),
    dict(codigo="INC-2026-0014", categoria="infraestructura", prioridad="critica", estado="resuelta",
         titulo="Cortocircuito en un contacto del aula",
         descripcion="Un contacto del aula B-110 hizo chispas y se disparó la protección eléctrica.",
         ubic=("Edificio B", "Aula B-110", 1), rep="sofia", tec="jorge", dias=10,
         tags=["electrico", "urgente"], detalle=_infra("cortocircuito", True, ["contacto", "cable calibre 12"]),
         avances=[(1.0, "Se cortó la energía del circuito y se aisló el área.")],
         final=(2.0, "Se reemplazó el contacto y el cableado dañado."), res_h=4,
         evid=[],),
    dict(codigo="INC-2026-0015", categoria="infraestructura", prioridad="alta", estado="cerrada",
         titulo="Goteras en el techo de la biblioteca",
         descripcion="Entra agua por el techo de la biblioteca durante las lluvias y moja el mobiliario.",
         ubic=("Biblioteca", "Sala de lectura", 2), rep="ana", tec="jorge", dias=22,
         tags=["filtracion", "techo", "recurrente"],
         detalle=_infra("filtración", True, ["impermeabilizante", "sellador"],
                        ("Impermeabilizaciones del Sureste", "sellado de losa")),
         avances=[(2.0, "Se localizó el punto de filtración en la losa.")],
         final=(5.0, "Se selló la losa con impermeabilizante."), res_h=52,
         evid=[],),
    dict(codigo="INC-2026-0016", categoria="infraestructura", prioridad="critica", estado="en proceso",
         titulo="Falla en la bomba de agua del edificio",
         descripcion="La bomba de agua dejó de funcionar y los sanitarios del edificio no tienen servicio.",
         ubic=("Edificio D", "Cuarto de máquinas", 0), rep="pedro", tec="jorge", dias=1,
         tags=["bomba", "urgente"],
         detalle=_infra("falla de bomba de agua", False, ["motor de bomba"], ("Hidráulica Peninsular", "rebobinado de motor")),
         avances=[(3.0, "Se detecta motor quemado y se cotiza el rebobinado.")],
         evid=[],),
    # Ejemplo 2 del reporte
    dict(codigo="INC-2026-0017", categoria="infraestructura", prioridad="media", estado="resuelta",
         titulo="Filtración de agua en techo del aula B-204",
         descripcion="Gotea agua desde el plafón durante lluvias y afecta el mobiliario.",
         ubic=("Edificio B", "Aula B-204", 2), rep="luis", tec="jorge", dias=20,
         tags=["filtracion", "techo", "recurrente"],
         detalle=_infra("filtracion", True, ["impermeabilizante", "sellador"],
                        ("Impermeabilizaciones del Sureste", "sellado de losa")),
         avances=[], final=(6.0, "Se selló la losa y se verificó sin filtraciones."), res_h=168,
         evid=[],),

    # ------------------------- Servicios académicos -------------------------
    dict(codigo="INC-2026-0018", categoria="academico", prioridad="alta", estado="resuelta",
         titulo="Error al iniciar sesión en el aula virtual",
         descripcion="Los docentes reciben un error de credenciales al entrar al aula virtual.",
         ubic=("Edificio C", "Sala de docentes", 2), rep="maria", tec="diana", dias=13,
         tags=["aula-virtual", "acceso"], detalle=_academico("Aula virtual", "TI-501", 42),
         avances=[(1.0, "Se reproduce el error con una cuenta de prueba.")],
         final=(1.5, "Se restableció la sincronización de cuentas."), res_h=12,
         evid=[],),
    dict(codigo="INC-2026-0019", categoria="academico", prioridad="critica", estado="en proceso",
         titulo="El portal Saeko no muestra las calificaciones",
         descripcion="Los estudiantes no ven sus calificaciones parciales en el portal Saeko.",
         ubic=("Edificio C", "Control escolar", 1), rep="rosa", tec="diana", dias=2,
         tags=["saeko", "calificaciones"], detalle=_academico("Portal Saeko", "TI-603", 120),
         avances=[(2.0, "Se reportó la falla al proveedor del portal.")],
         evid=[],),
    dict(codigo="INC-2026-0020", categoria="academico", prioridad="media", estado="resuelta",
         titulo="Bloqueo de cuenta de correo institucional",
         descripcion="La cuenta de correo institucional de un docente quedó bloqueada tras varios intentos fallidos.",
         ubic=("Edificio A", "Cubículo de docentes", 1), rep="pedro", tec="diana", dias=8,
         tags=["correo", "cuenta"], detalle=_academico("Correo institucional", "N/A", 1),
         avances=[], final=(0.5, "Se desbloqueó la cuenta y se restableció la contraseña."), res_h=3,
         evid=[],),
    dict(codigo="INC-2026-0021", categoria="academico", prioridad="alta", estado="cerrada",
         titulo="Página institucional fuera de servicio",
         descripcion="La página institucional no carga y el público no puede consultar la oferta educativa.",
         ubic=("Edificio D", "Dirección", 1), rep="ana", tec="diana", dias=17,
         tags=["pagina-institucional", "urgente"], detalle=_academico("Página institucional", "N/A", 900),
         avances=[(1.0, "Se confirma que el hosting dejó de responder.")],
         final=(1.5, "Se reinició el servicio con el proveedor de hosting."), res_h=14,
         evid=[],),
    dict(codigo="INC-2026-0022", categoria="academico", prioridad="critica", estado="en espera",
         titulo="No se puede asentar el acta de calificaciones del grupo TI-701",
         descripcion="El portal marca error al guardar las calificaciones finales del grupo TI-701.",
         ubic=("Edificio C", "Control escolar", 1), rep="maria", tec="diana", dias=5,
         tags=["calificaciones", "portal"], detalle=_academico("Portal de calificaciones", "TI-701", 35),
         avances=[(1.5, "Se reproduce el error y se recopilan evidencias.")],
         final=(0.5, "Esperando respuesta del proveedor del portal."),
         evid=[],),
    dict(codigo="INC-2026-0023", categoria="academico", prioridad="baja", estado="abierta",
         titulo="No carga el material del curso en el aula virtual",
         descripcion="Los archivos del curso TI-402 no se descargan desde el aula virtual.",
         ubic=("Edificio B", "Aula B-201", 2), rep="luis", tec=None, dias=1,
         tags=["aula-virtual"], detalle=_academico("Aula virtual", "TI-402", 28),
         evid=[],),
    dict(codigo="INC-2026-0024", categoria="academico", prioridad="baja", estado="abierta",
         titulo="Restablecer la contraseña del portal de alumnos",
         descripcion="Una estudiante no puede entrar al portal de alumnos y no recuerda su contraseña.",
         ubic=("Biblioteca", "Sala de cómputo", 1), rep="sofia", tec=None, dias=0.3,
         tags=["acceso", "cuenta"], detalle=_academico("Portal de alumnos", "N/A", 1)),
    dict(codigo="INC-2026-0025", categoria="academico", prioridad="media", estado="en proceso",
         titulo="Error 500 al registrar asistencia en el aula virtual",
         descripcion="Al registrar la asistencia del curso TI-502 el aula virtual muestra un error 500.",
         ubic=("Edificio A", "Aula A-103", 1), rep="pedro", tec="diana", dias=2.5,
         tags=["aula-virtual", "error-500"], detalle=_academico("Aula virtual", "TI-502", 31),
         avances=[(1.0, "Se reproduce el error en el curso TI-502.")],
         evid=[],),
    # Ejemplo 3 del reporte
    dict(codigo="INC-2026-0051", categoria="academico", prioridad="critica", estado="abierta",
         titulo="No se puede asentar el acta de calificaciones",
         descripcion="El portal marca error al guardar las calificaciones del grupo.",
         ubic=("Edificio C", "Control escolar", 1), rep="ana", tec=None, dias=0.5,
         tags=["portal", "calificaciones"], detalle=_academico("Portal de calificaciones", "TI-702", 38)),
]


def _historial(creada, d, tecnico_nombre):
    """Arma la bitácora a partir de los avances y del estado final."""
    entradas = []   # (estado, horas, comentario)
    for h, texto in d.get("avances", []):
        entradas.append(("en proceso", h, texto))
    estado = d["estado"]
    if estado == "en espera":
        h, texto = d["final"]
        entradas.append(("en espera", h, texto))
    elif estado in ("resuelta", "cerrada"):
        h, texto = d["final"]
        entradas.append(("resuelta", h, texto))
        if estado == "cerrada":
            entradas.append(("cerrada", 0, "Se confirmó con el reportante y se cierra la incidencia."))

    historial, fecha_resolucion = [], None
    n_resolucion = len([e for e in entradas if e[0] != "cerrada"])
    for i, (est, h, texto) in enumerate(entradas):
        if est == "resuelta":
            fecha = creada + timedelta(hours=d["res_h"])
            fecha_resolucion = fecha
        elif est == "cerrada":
            fecha = fecha_resolucion + timedelta(hours=1)
        elif d["estado"] in ("resuelta", "cerrada"):
            fecha = creada + timedelta(hours=d["res_h"] * (i + 1) / (n_resolucion + 1) * 0.9)
        else:
            fecha = creada + timedelta(hours=2 * (i + 1))
        historial.append({"fecha": fecha, "tecnico": tecnico_nombre, "estado": est,
                          "horas": h, "comentario": texto})
    return historial, fecha_resolucion


def construir_incidencias(ahora, usuarios):
    rng = random.Random(2026)             # pesos de archivo reproducibles
    docs = []
    for d in INCIDENCIAS:
        creada = ahora - timedelta(days=d["dias"])
        rep = usuarios[d["rep"]]
        doc = {
            "codigo": d["codigo"], "titulo": d["titulo"], "descripcion": d["descripcion"],
            "categoria": d["categoria"], "prioridad": d["prioridad"], "estado": d["estado"],
            "reportante": {"usuario_id": rep["_id"], "nombre": rep["nombre"],
                           "tipo": rep["tipo"], "correo": rep["correo"]},
        }
        tec = usuarios[d["tec"]] if d["tec"] else None
        if tec:
            doc["tecnico_asignado"] = {"usuario_id": tec["_id"], "nombre": tec["nombre"]}
        ubic: tuple[str,str,int] = d["ubic"]
        edificio, zona, piso = ubic
        doc["ubicacion"] = {"edificio": edificio, "zona": zona, "piso": piso}
        doc["fecha_creacion"] = creada

        historial, fecha_resolucion = _historial(creada, d, tec["nombre"] if tec else "")
        if fecha_resolucion:
            doc["fecha_resolucion"] = fecha_resolucion       # solo en resueltas y cerradas
            if (ahora - fecha_resolucion).days > 25:         # protege contra el TTL de 60 días
                raise ValueError(f"{d['codigo']}: la fecha de resolución es demasiado antigua")
        doc["horas_invertidas"] = sum(e["horas"] for e in historial)
        doc["tags"] = d["tags"]
        doc["detalle_especifico"] = d["detalle"]
        doc["historial_seguimiento"] = historial

        evidencias = []
        for nombre, peso in d.get("evid", []):
            ext = os.path.splitext(nombre)[1]
            if peso is None:
                peso = rng.randint(180, 900) if ext == ".pdf" else rng.randint(250, 2400)
            evidencias.append({
                "nombre_archivo": nombre, "tipo_mime": MIME[ext], "peso_kb": peso,
                "url_storage": f"incidencias/{d['codigo']}/{nombre}",
                "fecha_carga": creada + timedelta(minutes=15),
            })
        doc["evidencias_adjuntas"] = evidencias
        docs.append(doc)
    return docs


# ----------------------------------------------------------------------------
# Resumen y ejecución
# ----------------------------------------------------------------------------
def resumen(incidencias, usuarios, ahora):
    def marca(ok):
        return "OK " if ok else "REVISAR"

    por_cat = {}
    for i in incidencias:
        por_cat[i["categoria"]] = por_cat.get(i["categoria"], 0) + 1
    edificios = {i["ubicacion"]["edificio"] for i in incidencias}
    prioridades = {i["prioridad"] for i in incidencias}
    estados = {i["estado"] for i in incidencias}
    resueltas = [i for i in incidencias if "fecha_resolucion" in i]
    con_evid = [i for i in incidencias if i["evidencias_adjuntas"]]
    ultimo = max(int(i["codigo"].split("-")[2]) for i in incidencias)
    primer_borrado = min(i["fecha_resolucion"] for i in resueltas) + timedelta(days=60)

    print("\nResumen frente a los requisitos del proyecto:")
    print(f"  [{marca(20 <= len(incidencias) <= 30)}] Incidencias: {len(incidencias)} (20 a 30)")
    print(f"  [{marca(len(set(por_cat.values())) == 1)}] Por categoría: {por_cat}")
    print(f"  [{marca(len(edificios) >= 4)}] Edificios distintos: {len(edificios)} (mínimo 4)")
    print(f"  [{marca(len(prioridades) >= 3)}] Prioridades distintas: {len(prioridades)} (mínimo 3)")
    print(f"  [{marca(len(estados) == 5)}] Estados distintos: {len(estados)} (los 5)")
    print(f"  [{marca(len(resueltas) >= 8)}] Con fecha de resolución: {len(resueltas)} (mínimo 8)")
    print(f"  [{marca(len(con_evid) >= 15)}] Con evidencias: {len(con_evid)} (mínimo 15)")
    print(f"\nUsuarios creados: {len(usuarios)}. Contraseña de todos: {DEMO_PASSWORD}")
    print(f"Contador de Redis: inicialízalo en {ultimo} (mayor consecutivo ya usado).")
    print(f"El índice TTL empezará a borrar incidencias el {primer_borrado:%d/%m/%Y}; "
          "si la defensa es después, vuelve a correr este script antes.")


def main():
    parser = argparse.ArgumentParser(description="Carga los datos de prueba.")
    parser.add_argument("--yes", action="store_true", help="no pedir confirmación")
    args = parser.parse_args()

    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("Falta MONGODB_URI. Revisa el archivo .env en la raíz del repo.")
    db = MongoClient(uri, serverSelectionTimeoutMS=8000)[DB_NAME]
    existentes = db.list_collection_names()
    if "usuarios" not in existentes or "incidencias_campus" not in existentes:
        sys.exit("Las colecciones no existen. Primero ejecuta:  python db/setup_db.py")

    if not args.yes and input("Esto BORRA los documentos actuales de 'usuarios' e "
                              "'incidencias_campus' y carga los datos de prueba. "
                              "Escribe SI para continuar: ") != "SI":
        sys.exit("Cancelado.")

    ahora = datetime.now(timezone.utc)
    usuarios = construir_usuarios(ahora)
    incidencias = construir_incidencias(ahora, usuarios)

    db["incidencias_campus"].delete_many({})
    db["usuarios"].delete_many({})
    try:
        db["usuarios"].insert_many(list(usuarios.values()))
        print(f"[+] {len(usuarios)} usuarios insertados.")
        db["incidencias_campus"].insert_many(incidencias)
        print(f"[+] {len(incidencias)} incidencias insertadas.")
    except BulkWriteError as e:
        err = e.details["writeErrors"][0]
        sys.exit(f"Atlas rechazó un documento (posición {err['index']}): {err.get('errmsg')}\n"
                 f"{err.get('errInfo', '')}")

    resumen(incidencias, usuarios, ahora)


if __name__ == "__main__":
    main()