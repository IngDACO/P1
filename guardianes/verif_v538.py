# -*- coding: utf-8 -*-
"""v538 · NINGÚN COMPONENTE PUEDE SUBIR DE VERSIÓN SOLO.

⚠️ Lo que tumbó el Pre-Start en v537: el Cloud reinstala TODAS las dependencias cada vez que
la app despierta, y `streamlit-drawable-canvas` subió de 0.9 a 0.13 dentro de su rango (`<1`).
Un COMPONENTE lleva su propio JavaScript y su API cambia entre versiones menores. Los otros
dos componentes de la app estaban igual de expuestos: `extra-streamlit-components` (la cookie
de «Keep me signed in») y `streamlit-folium` (los mapas). Y `anthropic` no tenía tope.

Lo que protege:
  (a) ⚠️ todo paquete del requirements que instala un COMPONENTE va fijo (`==`). Se detecta
      por lo que el paquete instala (su `frontend`/`build` con un `index.html`), no por una
      lista escrita a mano: uno nuevo que se añada sin fijar sale rojo;
  (b) el resto lleva tope (`<`) — la regla de v66 —, salvo `tzdata` (la base de husos
      horarios: tiene que ser la última);
  (c) en el Python de la suite están EXACTAMENTE esas versiones (si no, prueba otra cosa).
"""
import importlib.metadata as md
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


SIN_TOPE_PERMITIDO = {"tzdata"}          # la base de husos horarios: siempre la última

_req = io.open(os.path.join(RAIZ, "requirements.txt"), encoding="utf-8").read()
reqs = {}
for linea in _req.splitlines():
    linea = linea.split("#", 1)[0].strip()
    if not linea:
        continue
    m = re.match(r"([A-Za-z0-9_.\-]+)\s*(.*)$", linea)
    reqs[m.group(1).lower()] = m.group(2).strip()


def es_componente(dist):
    """¿Instala un componente de Streamlit (un frontend con su index.html)?"""
    try:
        files = md.files(dist) or []
    except md.PackageNotFoundError:
        return None
    for f in files:
        p = str(f).replace("\\", "/").lower()
        if p.endswith("index.html") and ("/build/" in p or "/frontend/" in p):
            return True
    return False


print("\n1. ⚠️ Los componentes, fijos")
comps = {n: spec for n, spec in reqs.items() if n != "streamlit" and es_componente(n)}
no_inst = [n for n in reqs if es_componente(n) is None]
chk("todos los paquetes del requirements están instalados en el Python de la suite "
    "(si falta uno, no se puede saber si es un componente)", not no_inst, no_inst)
chk("se detectaron los componentes por lo que instalan (no es un paso en vacío): al menos "
    "el lienzo, la cookie y el mapa",
    {"streamlit-drawable-canvas", "extra-streamlit-components", "streamlit-folium"} <= set(comps),
    sorted(comps))
_sueltos = {n: s for n, s in comps.items() if not s.startswith("==")}
chk("⚠️ TODO componente va fijo (==): un rango deja que el Cloud instale otra versión al "
    "despertar la app (lo que tumbó el Pre-Start)", not _sueltos, _sueltos)
_otra = {n: (s[2:], md.version(n)) for n, s in comps.items()
         if s.startswith("==") and md.version(n) != s[2:]}
chk("...y en el Python de la suite está EXACTAMENTE esa versión", not _otra, _otra)

print("\n2. El resto, con tope")
_sin = {n: s for n, s in reqs.items()
        if n not in comps and n not in SIN_TOPE_PERMITIDO and not s.startswith("==")
        and "<" not in s}
chk("⚠️ ningún paquete sin tope (`>=` a secas): la regla de v66", not _sin, _sin)
chk("`anthropic` con tope de major y la versión instalada dentro",
    "<2" in reqs.get("anthropic", "") and md.version("anthropic").split(".")[0] == "1",
    (reqs.get("anthropic"), md.version("anthropic")))
chk("la única excepción es `tzdata`, y está en el requirements",
    SIN_TOPE_PERMITIDO <= set(reqs), SIN_TOPE_PERMITIDO - set(reqs))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
