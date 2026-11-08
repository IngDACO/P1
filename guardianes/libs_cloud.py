# -*- coding: utf-8 -*-
"""Antes de tocar `requirements.txt`: lo que instalará el Cloud (v657).

Por qué existe: el Cloud instala con `uv` (estricto) en Linux con Python 3.12, y el local con
`pip` en Windows. En v655, pedir `lxml>=6.1` hizo que el resolvedor eligiera svglib 1.6.0, que
trae `rlpycairo` → `pycairo`; pycairo solo publica ruedas para Windows, así que en Linux hay que
compilarla con las librerías de sistema de cairo, que el Cloud no tiene. En local la suite entera
estaba en verde (allí pycairo tiene rueda) y en el Cloud la app no arrancó.

Qué hace:
  1. Resuelve el `requirements.txt` del árbol con uv, para Linux x86_64 y Python 3.12, y también
     el de HEAD (lo que corre hoy), y enseña lo que cambia: un paquete NUEVO es lo que hay que mirar.
  2. Para cada paquete resuelto pregunta a PyPI si hay rueda para Linux/cp312. Uno sin rueda se
     compilaría en el Cloud: solo se admiten los de `COMPILAN_BIEN` (Python puro, se compilan hoy).
  3. Compara con lo instalado en el Python local: lo que difiera, la suite no lo prueba.

Uso:  py -3.12 libs_cloud.py [ruta-a-requirements]      (si falta uv: py -3.12 -m pip install uv)
Sale a la red (PyPI) y no escribe nada: por eso NO es un guardián de la suite.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request
from importlib.metadata import PackageNotFoundError, version

from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = pathlib.Path(__file__).resolve().parent.parent
REQ = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "survey_app" / "requirements.txt"

# Sin rueda en PyPI y aun así se instalan bien en el Cloud (Python puro; el registro del
# 08/11/2026 dice «Building svglib==1.5.1» y la app arranca). Uno nuevo aquí se razona.
COMPILAN_BIEN = {"svglib"}

# Lo que admite una máquina Linux x86_64 con Python 3.12 (glibc >= 2.28, lo que supone uv
# para x86_64-unknown-linux-gnu): las etiquetas de rueda que pip/uv aceptarían allí.
_PLAT = ["manylinux_2_%d_x86_64" % g for g in range(28, 4, -1)] + [
    "manylinux2014_x86_64", "manylinux2010_x86_64", "manylinux1_x86_64", "linux_x86_64"]
_TAGS = set(cpython_tags((3, 12), abis=["cp312", "abi3", "none"], platforms=_PLAT)) | set(
    compatible_tags((3, 12), interpreter="cp312", platforms=_PLAT))


def resolver(req_texto: str) -> dict:
    """{nombre: versión} que elegiría uv en el Cloud para ese requirements."""
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "requirements.txt"
        f.write_text(req_texto, encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "uv", "pip", "compile", str(f),
                            "--python-version", "3.12", "--python-platform", "x86_64-unknown-linux-gnu",
                            "--no-header", "--no-annotate", "--quiet"],
                           capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("uv no resuelve (el Cloud tampoco):\n" + (r.stderr or r.stdout)[-2500:])
    out = {}
    for ln in r.stdout.splitlines():
        ln = ln.split("#")[0].strip()
        if "==" in ln:
            n, v = ln.split("==", 1)
            out[canonicalize_name(n.split("[")[0])] = v.strip()
    return out


def rueda_linux(nombre: str, ver: str) -> bool:
    """¿Publica PyPI una rueda instalable en Linux x86_64 / cp312 para esa versión?"""
    with urllib.request.urlopen(f"https://pypi.org/pypi/{nombre}/{ver}/json", timeout=30) as resp:
        datos = json.load(resp)
    for f in datos.get("urls", []):
        if f.get("packagetype") != "bdist_wheel":
            continue
        try:
            _n, _v, _b, tags = parse_wheel_filename(f["filename"])
        except Exception:
            continue
        if tags & _TAGS:
            return True
    return False


def main() -> int:
    fallos = []
    nuevo = resolver(REQ.read_text(encoding="utf-8"))
    hoy = {}  # lo que corre hoy = el requirements de la app en HEAD (también si se mira otro fichero)
    r = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:survey_app/requirements.txt"],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        hoy = resolver(r.stdout)

    print(f"\n1. Lo que instalaría el Cloud con {REQ.name}: {len(nuevo)} paquetes")
    if hoy:
        cambios = sorted(set(nuevo) | set(hoy))
        hay = False
        for n in cambios:
            a, b = hoy.get(n), nuevo.get(n)
            if a != b:
                hay = True
                marca = "  NUEVO  " if a is None else ("  FUERA  " if b is None else "  cambia ")
                print(f"{marca}{n}: {a or '-'} -> {b or '-'}")
        if not hay:
            print("   igual que HEAD")

    print("\n2. Rueda para Linux / Python 3.12 en PyPI")
    sin_rueda = []
    for n, v in sorted(nuevo.items()):
        try:
            ok = rueda_linux(n, v)
        except Exception as e:  # sin red o PyPI caído: que se vea, no que pase
            fallos.append(f"no se pudo preguntar a PyPI por {n} {v}: {e}")
            continue
        if not ok:
            sin_rueda.append((n, v))
    for n, v in sin_rueda:
        if n in COMPILAN_BIEN:
            print(f"   sin rueda, admitido: {n} {v} (Python puro, el Cloud ya lo compila)")
        else:
            fallos.append(f"{n} {v} no tiene rueda para Linux: el Cloud tendría que compilarlo")
    if not sin_rueda:
        print("   todos con rueda")

    print("\n3. Lo instalado en el Python local (la suite prueba esto)")
    distintos = []
    for n, v in sorted(nuevo.items()):
        try:
            loc = version(n)
        except PackageNotFoundError:
            loc = None
        if loc != v:
            distintos.append(f"{n}: local {loc or 'NO INSTALADO'}, Cloud {v}")
    print("   igual" if not distintos else "\n".join("   " + d for d in distintos))

    print("\n" + "=" * 70)
    for f in fallos:
        print("  FALLO  " + f)
    if distintos:
        print(f"  AVISO  {len(distintos)} distintos en local: la suite no prueba lo del Cloud "
              "(py -3.12 -m pip install nombre==versión)")
    print("=== " + ("SE PUEDE SUBIR" if not fallos else "NO SUBIR") + " ===")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
