"""Corre la suite ENTERA de guardianes (regla v385: nunca un subconjunto).

Un subconjunto curado da la sensacion de cobertura sin la cobertura: cuando
reportaba "13 en verde", la suite completa tenia 48 y 13 estaban en rojo.

Desde 01/11/2026 corre EN PARALELO, `PROCESOS` a la vez (de 35 a unos 6 min). `--procesos=1` los
corre de uno en uno, para saber cuál de los que corrían a la vez tocó el código.
"""
import atexit
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = pathlib.Path(__file__).parent
# ⚠️ CWD = survey_app: Streamlit busca `.streamlit/secrets.toml` RELATIVO al
# directorio de trabajo, asi que lanzarlos desde otro sitio los tumba a todos con
# "No secrets found" — 16 rojos que no eran rojos de verdad.
CWD = r"C:\Users\diego\P1\survey_app"
# ⚠️ El techo son 60 lecturas/min por cuenta de servicio, y es la MISMA cuenta de la app en producción:
# amontonarlas es provocar un 429 y leer un falso rojo (el error de v377: el verificador reventando
# por el problema que verificaba). Hasta 01/11/2026 se cuidaba con 2,5 s tras CADA guardián: 10 de los
# 35 min de la suite durmiendo, y repartía 1351 peticiones que eran casi todas la misma. Ahora cada
# lectura se pide UNA vez por tanda (`arnes/sitecustomize.py`), y si se pasa del techo, ROJO.
PROCESOS = 5
TECHO_HOJA = 50
_HOST_HOJA = "sheets.googleapis.com"
# ⚠️ El hijo hereda un stdout en cp1252, así que un guardián que imprima un emoji
# (🔩, 🌐…) muere con UnicodeEncodeError y sale con código != 0 — ROJO que no es rojo:
# el fallo está en la consola, no en el código auditado. Pasó con 4 a la vez. Es la
# misma familia que el CWD de v19: el entorno de ejecución fabricando falsos rojos.
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8",
           "PYTHONPATH": os.pathsep.join(x for x in (str(AQUI / "arnes"), os.environ.get("PYTHONPATH")) if x)}


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
# v573 · un argumento suelto filtra por nombre (`run_suite.py verif_v57`): para validar
# esta misma red sin esperar media hora. ⚠️ Antes de desplegar, SIEMPRE la suite entera.
_filtro = [a for a in sys.argv[1:] if not a.startswith("-")]
if _filtro:
    guardianes = [p for p in guardianes if any(f in p.name for f in _filtro)]
for _a in sys.argv[1:]:
    if _a.startswith("--procesos="):
        PROCESOS = max(1, int(_a.split("=", 1)[1]))
APP = AQUI.parent / "survey_app"


def _huella():
    """{fichero: md5} del CÓDIGO de la app. ⚠️ v573 · la suite NO debe tocarlo: tres
    guardianes (v463, v471, v498) escribían en `core/` para validar sus sondas —rompían y
    restauraban, o creaban un fichero allí— y `quotes_ui.py` salía «modificado» (CRLF→LF)
    tras cada suite. Un guardián que lo toque sale en ROJO aunque sus afirmaciones pasen."""
    return {str(f.relative_to(APP)): hashlib.md5(f.read_bytes()).hexdigest()
            for f in APP.rglob("*.py") if "__pycache__" not in f.parts}


SIN_DATOS = 2


def _correr(p, carpeta_red):
    """(guardián, código, última línea, segundos, [(host, método)] de lo que salió de verdad a la
    red). Código None = no terminó."""
    red = os.path.join(carpeta_red, p.stem + ".txt")
    t = time.time()
    try:
        r = subprocess.run([PY, str(p)], capture_output=True, cwd=CWD, env={**ENTORNO, "COPEX_RED": red},
                           text=True, encoding="utf-8", errors="replace", timeout=240)
        cod, cola = r.returncode, ([l for l in (r.stdout or "").splitlines() if l.strip()][-1:] or [""])[0]
        # ⚠️ Un guardián que MUERE no imprime nada por stdout: sin esto, un rojo sin ninguna pista
        # (check_ceros, 01/11/2026). Lo último que dijo por stderr.
        if cod not in (0, SIN_DATOS):
            cola = (([l for l in (r.stderr or "").splitlines() if l.strip()][-1:] or [""])[0][:70]
                    + " | " + cola)
    except subprocess.TimeoutExpired:
        cod, cola = None, "timeout 240 s"
    except Exception as e:                                   # noqa: BLE001
        cod, cola = None, repr(e)[:90]
    seg = time.time() - t
    try:
        with open(red, encoding="utf-8") as f:
            peticiones = [tuple(l.split()) for l in f if l.strip()]
    except OSError:
        peticiones = []
    return p, cod, cola, seg, peticiones


print(f"{len(guardianes)} guardianes · {PROCESOS} a la vez · {_ver}{AVISO_PY}\n", flush=True)
# ⚠️ Un guardián que necesita datos y no los tiene NO debe salir verde (sería el paso
# en vacío de la trampa nº1: un OK que no comprobó nada) ni rojo (no hay nada roto).
# Sale con código 2 = SIN DATOS y se cuenta aparte: así vaciar la demo no deja rojos
# permanentes —lo que hace que una suite acabe ignorándose (v385)— pero tampoco
# esconde que esas afirmaciones dejaron de comprobarse.
verde, rojo, roto, sindatos = [], [], [], []
tiempos, salidas = {}, {}
t0 = time.time()
_h0 = _huella()
_carpeta_red = tempfile.mkdtemp(prefix="suite_red_")
atexit.register(shutil.rmtree, _carpeta_red, ignore_errors=True)
# ⚠️ Datos reales: fuera del repo y borrados al acabar. Si la tanda ya trae carpeta, es suya.
if not ENTORNO.get("COPEX_CACHE_HOJA"):
    ENTORNO["COPEX_CACHE_HOJA"] = tempfile.mkdtemp(prefix="suite_hoja_")
    atexit.register(shutil.rmtree, ENTORNO["COPEX_CACHE_HOJA"], ignore_errors=True)
with ThreadPoolExecutor(PROCESOS) as _varios:
    _futuros = [_varios.submit(_correr, p, _carpeta_red) for p in guardianes]
    for _f in as_completed(_futuros):
        p, cod, cola, seg, peticiones = _f.result()
        tiempos[p.name] = seg
        if peticiones:
            salidas[p.name] = peticiones
        # ⚠️ Después de CADA guardián. Con varios a la vez, el que toca el código es él o uno de
        # los que corrían con él: `--procesos=1` y `verif_v573` (estático) dicen cuál.
        _h1 = _huella()
        _tocados = sorted(k for k in set(_h0) | set(_h1) if _h0.get(k) != _h1.get(k))
        _h0 = _h1
        if _tocados:
            _m = "TOCÓ el código de la app (él o uno de los que corrían a la vez): %s" % ", ".join(_tocados)[:70]
            rojo.append((p.name, _m))
            print(f"  ROJO  {p.name}   {_m}", flush=True)
        elif cod is None:
            roto.append((p.name, cola))
            print(f"  ROTO  {p.name}   {cola}", flush=True)
        elif cod == 0:
            verde.append(p.name)
            print(f"  ok    {p.name}", flush=True)
        elif cod == SIN_DATOS:
            sindatos.append((p.name, cola[:90]))
            print(f"  --    {p.name}   (sin datos) {cola[:70]}", flush=True)
        else:
            rojo.append((p.name, cola[:90]))
            print(f"  ROJO  {p.name}   {cola[:90]}", flush=True)

_dur = time.time() - t0
_lect = [n for n, v in salidas.items() for h, *m in v if _HOST_HOJA in h and m[:1] == ["GET"]]
_escr = sorted({n for n, v in salidas.items() for h, *m in v if _HOST_HOJA in h and m[:1] != ["GET"]})
_ritmo = len(_lect) / max(_dur / 60, 1)
if _ritmo > TECHO_HOJA:
    rojo.append(("hoja real", f"{_ritmo:.0f} lecturas/min, por encima de {TECHO_HOJA}: mirar qué se dejó de guardar"))
print(f"\n=== {len(verde)} verde · {len(rojo)} rojo · {len(roto)} roto "
      f"· {_dur:.0f} s · {_ver} ==={AVISO_PY}")
for n, c in rojo + roto:
    print(f"  {n}: {c}")
if sindatos:
    print("")
    print("  ⚠️ NO comprobados por falta de datos en la demo. No es un fallo, pero")
    print("     tampoco es una garantía: esas afirmaciones dejaron de comprobarse.")
    for n, c in sindatos:
        print(f"     {n}: {c}")
print("")
print("  Más lentos: " + " · ".join(f"{n[:-3]} {s:.0f} s" for n, s in
                                    sorted(tiempos.items(), key=lambda x: -x[1])[:8]))
print(f"  Hoja real: {len(_lect)} lecturas de verdad, {_ritmo:.0f}/min (techo {TECHO_HOJA})")
if _escr:
    print(f"  ⚠️ Escriben en la hoja real: {', '.join(x[:-3] for x in _escr)}")
_fuera = sorted({h for v in salidas.values() for h, *m in v if "googleapis.com" not in h})
if _fuera:
    print(f"  ⚠️ Salen a otros sitios: {', '.join(_fuera)}")
sys.exit(0 if not rojo and not roto else 1)
