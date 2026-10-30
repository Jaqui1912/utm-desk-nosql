
import argparse
import subprocess
import sys
import time
from pathlib import Path

CARPETA_DB = Path(__file__).resolve().parent
RAIZ = CARPETA_DB.parent

def construir_pasos(force_reset, sin_exportar):
    if force_reset:
        args_setup = ["--reset"]
        entrada_setup = "SI\n"
        args_seed = ["--force-reset", "--yes"]
    else:
        args_setup = []
        entrada_setup = None
        args_seed = ["--solo-faltantes", "--yes"]

    pasos = [
        ("Conexión con Atlas", "test_conexion.py", [], None, False),
        ("Estructura: colecciones, validador e índices", "setup_db.py", args_setup, entrada_setup, False),
        ("Verificación del validador", "prueba_validacion.py", [], None, False),
        ("Datos de prueba (preservando datos vivos)", "seed.py", args_seed, None, False),
        ("Operaciones, búsqueda de texto y pipelines", "consultas.py", [], None, False),
        ("Exportación a JSON", "exportar.py", [], None, True),
    ]
    return [p for p in pasos if not (sin_exportar and p[4])]


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
    parser = argparse.ArgumentParser(description="Verifica, sincroniza y exporta la base de datos.")
    parser.add_argument("--yes", action="store_true", help="no pedir confirmación")
    parser.add_argument("--sin-exportar", action="store_true", help="omitir la exportación a JSON")
    parser.add_argument("--force-reset", action="store_true", help="PELIGRO: borra y reconstruye toda la base de datos")
    args = parser.parse_args()

    if args.force_reset:
        if not args.yes and input("PELIGRO: Esto BORRA todos los datos de 'usuarios' e 'incidencias_campus' "
                                  "y los vuelve a crear desde cero. Escribe SI para continuar: ") != "SI":
            sys.exit("Cancelado.")
    else:
        print("[*] Modo Seguro: No se borrarán los usuarios ni las incidencias existentes en Atlas.")

    pasos = construir_pasos(args.force_reset, args.sin_exportar)
    inicio = time.time()
    ok, fallo = ejecutar(pasos)
    segundos = time.time() - inicio

    print("\n" + "=" * 70)
    if not ok:
        sys.exit(f"FALLÓ el paso: {fallo}. Revisa el mensaje de arriba; los pasos siguientes no se ejecutaron.")
    print(f"Base de datos verificada y sincronizada correctamente en {segundos:.0f} s.")
    if not args.sin_exportar:
        print("Los JSON actualizados están en db/export/. Súbelos a Git con:  git add db/export")


if __name__ == "__main__":
    main()