"""Corre la suite ENTERA de guardianes (regla v385: nunca un subconjunto).

Un subconjunto curado da la sensacion de cobertura sin la cobertura: cuando
reportaba "13 en verde", la suite completa tenia 48 y 13 estaban en rojo.
"""
import os
import pathlib
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = pathlib.Path(__file__).parent
# ⚠️ CWD = survey_app: Streamlit busca `.streamlit/secrets.toml` RELATIVO al
# directorio de trabajo, asi que lanzarlos desde otro sitio los tumba a todos con
# "No secrets found" — 16 rojos que no eran rojos de verdad.
CWD = r"C:\Users\diego\P1\survey_app"
# ⚠️ Y se espacian: 16 guardianes leen la hoja real y el techo son 60 lecturas/min
# por cuenta de servicio. Amontonarlos es provocar un 429 y leer un falso rojo
# (es el error de v377: el verificador reventando por el problema que verificaba).
PAUSA = 2.5
# ⚠️ El hijo hereda un stdout en cp1252, así que un guardián que imprima un emoji
# (🔩, 🌐…) muere con UnicodeEncodeError y sale con código != 0 — ROJO que no es rojo:
# el fallo está en la consola, no en el código auditado. Pasó con 4 a la vez. Es la
# misma familia que el CWD de v19: el entorno de ejecución fabricando falsos rojos.
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _python_del_cloud():
    """⚠️ v535 · El intérprete del Cloud (3.12), si está instalado.

    Hasta v535 la suite corría con el 3.14 local y el Cloud usa 3.12 (trampa nº11: lo local
    no es lo que corre). El 06/10/2026 se instaló el 3.12 con las librerías de
    `requirements.txt`, así que la suite lo usa aunque se lance con otro Python. Si no
    está, sigue con el que la lanzó y LO DICE en la primera y en la última línea.
    """
    if sys.version_info[:2] == (3, 12):
        return sys.executable
    try:
        r = subprocess.run(["py", "-3.12", "-c", "import sys, streamlit; print(sys.executable)"],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().splitlines()[-1]
    except Exception:                                        # noqa: BLE001
        pass
    return None


PY = _python_del_cloud()
AVISO_PY = ("" if PY else "  ⚠️ SIN el Python del Cloud (3.12): la suite prueba otro intérprete")
PY = PY or sys.executable
_ver = subprocess.run([PY, "-c", "import sys, streamlit; print('Python %d.%d.%d' % "
                       "sys.version_info[:3], '· Streamlit', streamlit.__version__)"],
                      capture_output=True, text=True, encoding="utf-8", errors="replace",
                      env=ENTORNO).stdout.strip()
guardianes = sorted(p for p in AQUI.glob("*.py")
                    if p.name.startswith(("verif_", "check_")))

print(f"{len(guardianes)} guardianes · {_ver}{AVISO_PY}\n")
# ⚠️ Un guardián que necesita datos y no los tiene NO debe salir verde (sería el paso
# en vacío de la trampa nº1: un OK que no comprobó nada) ni rojo (no hay nada roto).
# Sale con código 2 = SIN DATOS y se cuenta aparte: así vaciar la demo no deja rojos
# permanentes —lo que hace que una suite acabe ignorándose (v385)— pero tampoco
# esconde que esas afirmaciones dejaron de comprobarse.
SIN_DATOS = 2
verde, rojo, roto, sindatos = [], [], [], []
t0 = time.time()
for p in guardianes:
    try:
        r = subprocess.run([PY, str(p)], capture_output=True, cwd=CWD, env=ENTORNO,
                           text=True, encoding="utf-8", errors="replace", timeout=240)
        time.sleep(PAUSA)
        cola = [l for l in (r.stdout or "").splitlines() if l.strip()][-1:] or [""]
        if r.returncode == 0:
            verde.append(p.name)
            print(f"  ok    {p.name}")
        elif r.returncode == SIN_DATOS:
            sindatos.append((p.name, cola[0][:90]))
            print(f"  --    {p.name}   (sin datos) {cola[0][:70]}")
        else:
            rojo.append((p.name, cola[0][:90]))
            print(f"  ROJO  {p.name}   {cola[0][:90]}")
    except subprocess.TimeoutExpired:
        roto.append((p.name, "timeout 240 s"))
        print(f"  ROTO  {p.name}   timeout")
    except Exception as e:                                   # noqa: BLE001
        roto.append((p.name, repr(e)[:90]))
        print(f"  ROTO  {p.name}   {e!r:.90}")

print(f"\n=== {len(verde)} verde · {len(rojo)} rojo · {len(roto)} roto "
      f"· {time.time() - t0:.0f} s · {_ver} ==={AVISO_PY}")
for n, c in rojo + roto:
    print(f"  {n}: {c}")
if sindatos:
    print("")
    print("  ⚠️ NO comprobados por falta de datos en la demo. No es un fallo, pero")
    print("     tampoco es una garantía: esas afirmaciones dejaron de comprobarse.")
    for n, c in sindatos:
        print(f"     {n}: {c}")
sys.exit(0 if not rojo and not roto else 1)
