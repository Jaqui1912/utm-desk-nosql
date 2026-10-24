
import argparse
import subprocess
import sys
import time
from pathlib import Path

CARPETA_DB = Path(__file__).resolve().parent
RAIZ = CARPETA_DB.parent

# (descripción, script, argumentos, texto para el input() del script, es_exportacion)
PASOS = [
    ("Conexión con Atlas", "test_conexion.py", [], None, False),
    ("Estructura: colecciones, validador e índices", "setup_db.py", ["--reset"], "SI\n", False),
    ("Verificación del validador", "prueba_validacion.py", [], None, False),
    ("Datos de prueba", "seed.py", ["--yes"], None, False),
    ("Operaciones, búsqueda de texto y pipelines", "consultas.py", [], None, False),
    ("Exportación a JSON", "exportar.py", [], None, True),
]


def ejecutar(pasos, carpeta=CARPETA_DB, cwd=RAIZ):
    """Corre cada paso con el mismo Python. Devuelve (ok, nombre_del_paso_que_falló)."""
    total = len(pasos)
    for i, (descripcion, script, argumentos, entrada, _) in enumerate(pasos, start=1):
        print(f"\n{'=' * 70}\nPaso {i}/{total}: {descripcion}  ({script})\n{'=' * 70}", flush=True)
        r = subprocess.run([sys.executable, str(carpeta / script), *argumentos],
                           input=entrada, text=True, cwd=cwd)
        if r.returncode != 0:
            return False, descripcion
    return True, None


def main():
    parser = argparse.ArgumentParser(description="Reconstruye toda la base de datos.")
    parser.add_argument("--yes", action="store_true", help="no pedir confirmación")
    parser.add_argument("--sin-exportar", action="store_true", help="omitir la exportación a JSON")
    args = parser.parse_args()

    if not args.yes and input("Esto BORRA todos los datos de 'usuarios' e 'incidencias_campus' "
                              "y los vuelve a crear. Escribe SI para continuar: ") != "SI":
        sys.exit("Cancelado.")

    pasos = [p for p in PASOS if not (args.sin_exportar and p[4])]
    inicio = time.time()
    ok, fallo = ejecutar(pasos)
    segundos = time.time() - inicio

    print("\n" + "=" * 70)
    if not ok:
        sys.exit(f"FALLÓ el paso: {fallo}. Revisa el mensaje de arriba; los pasos siguientes no se ejecutaron.")
    print(f"Base de datos reconstruida correctamente en {segundos:.0f} s.")
    if not args.sin_exportar:
        print("Los JSON están en db/export/. Súbelos a Git con:  git add db/export")


if __name__ == "__main__":
    main()