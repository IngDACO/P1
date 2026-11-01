# -*- coding: utf-8 -*-
"""La tanda de una versión, de principio a fin (01/11/2026): suite → baterías → anclas.

⚠️ En ESTE orden: un rojo de la suite salía antes al final, después de una hora de baterías. Con la
suite primero, lo que esté mal se sabe en 10 min, y si está en rojo las baterías no se corren.

⚠️ Las baterías viejas van con CORTE (`COPEX_CORTE`: el guardián termina en su primer FALLO). Las
NUEVAS, sin él: son las que prueban que el guardián sale con código de error (`arnes/sitecustomize.py`).

⚠️ Tras CADA batería se compara el código con el de antes: una que deje una rotura puesta para la
tanda (v600 dejó dos en la app). Y ninguna lleva tiempo máximo: cortar una batería es lo que deja
roturas puestas.

    py -3.12 tanda.py                      # lo que hay sin commit, contra HEAD
    py -3.12 tanda.py --base a123..b456    # lo que cambió entre dos commits
    py -3.12 tanda.py --sin-suite          # solo baterías y anclas
    py -3.12 tanda.py romper_v440          # además de las afectadas, estas
    py -3.12 tanda.py --salida=CARPETA     # dónde guardar lo que imprime cada una
    py -3.12 tanda.py --sin=romper_v625    # sin esa (una batería nueva y larga ya pasada)
"""
import atexit
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import baterias_afectadas as BA                                    # noqa: E402

APP = AQUI.parent / "survey_app"
_MALAS = ("ESCAPA", "COLGADA", "YA esta", "ya falla", "ABORT")


def entorno(nueva):
    """El de una batería: el arnés siempre; el corte, solo si NO es nueva."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8",
           "PYTHONPATH": os.pathsep.join(x for x in (str(AQUI / "arnes"), os.environ.get("PYTHONPATH")) if x)}
    env.pop("COPEX_CORTE", None)
    if not nueva:
        env["COPEX_CORTE"] = "1"
    return env


def salio_mal(codigo, texto):
    """⚠️ Por código Y por texto: las baterías viejas pueden acabar con 0 y una rotura escapada."""
    return codigo != 0 or any(m in texto for m in _MALAS)


def huella():
    """{fichero: md5} de la app y de los guardianes: las baterías rompen los dos."""
    ficheros = [f for f in APP.rglob("*.py") if "__pycache__" not in f.parts]
    ficheros += [f for f in AQUI.glob("*.py") if not f.name.startswith("_")]
    # ⚠️ Sin CRLF: 74 baterías guardan con LF lo que estaba en CRLF, y eso no es tocar el código
    # (git lo normaliza). v625: romper_v532 paró la tanda con el contenido idéntico.
    return {str(f): hashlib.md5(f.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for f in ficheros}


def distintos(a, b):
    return sorted(Path(k).name for k in set(a) | set(b) if a.get(k) != b.get(k))


def _ultima(texto):
    return ([l.strip() for l in texto.splitlines() if l.strip()][-1:] or [""])[0][:90]


def _reloj(s):
    return "%d:%02d" % (s // 60, s % 60)


def correr(nombre, salida, env):
    """(código, texto, segundos). Lo que imprime queda en `salida/<nombre>.txt`."""
    t = time.time()
    fich = Path(salida) / (nombre + ".txt")
    with open(fich, "w", encoding="utf-8", errors="replace") as fh:
        r = subprocess.run([sys.executable, str(AQUI / (nombre + ".py"))], cwd=str(AQUI), env=env,
                           stdout=fh, stderr=subprocess.STDOUT)
    return r.returncode, fich.read_text(encoding="utf-8", errors="replace"), time.time() - t


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    base, salida, sin_suite, extra, sin = "HEAD", None, False, [], set()
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--base":
            i += 1
            base = argv[i]
        elif a.startswith("--salida="):
            salida = a.split("=", 1)[1]
        elif a == "--sin-suite":
            sin_suite = True
        elif a.startswith("--sin="):
            sin.add(a.split("=", 1)[1])
        else:
            extra.append(a)
        i += 1
    salida = salida or tempfile.mkdtemp(prefix="tanda_")
    os.makedirs(salida, exist_ok=True)
    # ⚠️ Una sola carpeta de lecturas para toda la tanda, suite y baterías: cada rotura repite el
    # guardián, y sin esto cada repetición volvía a pedir las mismas hojas. Datos reales: se borra.
    _cache = tempfile.mkdtemp(prefix="tanda_hoja_")
    atexit.register(shutil.rmtree, _cache, ignore_errors=True)
    os.environ["COPEX_CACHE_HOJA"] = _cache
    t0 = time.time()
    print("Tanda · base %s · salidas en %s" % (base, salida))

    if not sin_suite:
        cod, txt, seg = correr("run_suite", salida, entorno(True))
        print("\n1. Suite (%s)" % _reloj(seg))
        for l in txt.splitlines():
            if l.startswith(("===", "  ROJO", "  ROTO")):
                print("  " + l[:150])
        if cod != 0:
            print("\n⚠️ LA SUITE ESTÁ EN ROJO: no se corren las baterías.")
            return 1

    _nuevas = set(BA.nuevas(base))
    _af = BA.afectadas(base)
    lista = sorted(_nuevas) + sorted(b for b in set(_af) | set(extra) if b not in _nuevas)
    lista = [b for b in lista if b not in sin]
    print("\n2. Baterías: %d (%d nuevas, sin corte)" % (len(lista), len(_nuevas)))
    malas = []
    h0 = huella()
    for b in lista:
        cod, txt, seg = correr(b, salida, entorno(b in _nuevas))
        mal = salio_mal(cod, txt)
        print("  %-5s %-16s %6s  %s" % ("MAL" if mal else "ok", b, _reloj(seg), _ultima(txt)))
        if mal:
            malas.append(b)
        _t = distintos(h0, huella())
        if _t:
            print("\n⚠️ %s DEJÓ TOCADO EL CÓDIGO: %s. Se para la tanda: mirar el diff." % (b, ", ".join(_t)))
            return 1

    cod, txt, seg = correr("check_anclas_roturas", salida, entorno(False))
    print("\n3. Anclas: %s" % ("ok" if cod == 0 else "MAL"))
    for l in txt.splitlines():
        if "vivas" in l or "FALLO" in l:
            print("  " + l.strip()[:120])
    if cod != 0:
        malas.append("check_anclas_roturas")

    print("\n=== Tanda %s · %s ===" % ("EN VERDE" if not malas else "EN ROJO: " + ", ".join(malas),
                                       _reloj(time.time() - t0)))
    return 0 if not malas else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
