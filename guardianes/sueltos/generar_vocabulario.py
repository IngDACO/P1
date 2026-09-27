# -*- coding: utf-8 -*-
"""Saca del documento de tareas el mapa `actividad -> [tareas]` para pegarlo como DATO.

⚠️ Se genera UNA vez y el resultado se pega en `core/vocabulario.py`. NO se parsea el
documento en tiempo de ejecucion: un fichero de texto que el codigo lee para decidir es
un fichero que alguien edita sin saber que rompe algo. Lo mismo que se hizo con
`stages.py`, que se escribio a mano desde el otro documento.

⚠️ Y reporta lo que NO casa con el catalogo en vez de tragarselo: los nombres del
documento y los del codigo han derivado (rayas largas, titulos abreviados), y esa lista
es justo lo que hay que resolver a mano.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, os.getcwd())
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "owner", "grupo": "cliente1"}

from core import stages as S                                      # noqa: E402

DOC = r"C:\Users\diego\P1\docs\Lift_Install_Task_Breakdown.md"
CAT = {a[0] for v in S.ACTIVIDADES.values() for a in v}

# Nombres que el documento abrevia o escribe distinto. Cada uno mirado a mano contra el
# catalogo; la RAZON al lado, que es lo que permite revisarlo sin volver a los dos textos.
ALIAS = {
    # Raya larga en el doc, guion en el catalogo.
    "Rip out mechanical components — traction": "Rip out mechanical components - traction",
    "Rip out mechanical components — hydraulic": "Rip out mechanical components - hydraulic",
    # El doc abrevia el titulo; el catalogo lleva el completo. ⚠️ Cada uno LEIDO del
    # catalogo, no supuesto: mi primera tanda invento diez nombres que no existian.
    "Receive toolbox for installer": "Receive toolbox",
    "Receive rip-out kit": "Rip-out kit delivery",
    "Paperwork": "Paperwork (hand-over/procedure forms, SWMS sign-off)",
    "Survey": "Survey (verify vs. existing shaft)",
    "Prep doors": "Prep doors (panels/blades, frames)",
    "Install platform": "Install platform (cradle)",
    "Install cabin ceiling": "Install cabin ceiling (roof)",
    "Groutguarding": "Groutguarding (fire-rated)",
    "Install belts": "Install belts (motor, CW, cabin)",
    "Confirm free movement under tirak only, lift fully isolated/dead":
        "Confirm free movement under tirak only, lift fully isolated",
}

# ⚠️ Estas TRES estan en el desglose de tareas y NO en el documento de etapas del que
# salio el catalogo (comprobado: 0 apariciones en el draft, 1 en el breakdown). O sea que
# los dos documentos han DERIVADO y el codigo sigue solo a uno — el que trae los pesos.
#
# No se mapean a la actividad mas parecida: eso seria inventar. Es trabajo real (aligerar
# la cabina para la relacion del tirak, puentear el circuito de puertas, cortar el hueco
# de obra) y si un instalador lo escribe, hoy no hay donde ponerlo. Queda DECLARADO para
# que el usuario decida si entran al catalogo y con que peso — decision suya, no mia.
SIN_ACTIVIDAD = (
    "Lighten cabin if too heavy for intended tirak ratio",
    "Bridge landing door circuit",
    "Cut/expand concrete door openings",
)

txt = io.open(DOC, encoding="utf-8").read()
lineas = txt.splitlines()

mapa, actual, sin_casar = {}, None, []
for ln in lineas:
    # ⚠️ Se RESETEA al cambiar de bloque. Sin esto, `actual` sobrevivia a la etapa
    # entera: las actividades de la Stage 11 no van en negrita (son `- texto` bajo un
    # encabezado `**Under cabin**`), asi que sus tareas indentadas se colgaban de la
    # ultima actividad en negrita — «Chase», de la Stage 11, acabo dentro de «Spin
    # motor», 33 lineas mas arriba. Un vocabulario mal mapeado en silencio.
    if ln.startswith("#") or (ln.strip() and not ln.startswith((" ", "-", "\t"))):
        actual = None
    m = re.match(r"^- \*\*(.+?)\*\*", ln)
    if m:
        nom = m.group(1).strip()
        nom = ALIAS.get(nom, nom)
        if nom in CAT:
            actual = nom
            mapa.setdefault(actual, [])
        else:
            actual = None
            sin_casar.append(m.group(1).strip())
        continue
    m2 = re.match(r"^\s{2,}- (.+)$", ln)
    if m2 and actual:
        # Solo el texto util: lo que va antes de un guion explicativo o un parentesis.
        t = m2.group(1).strip()
        t = re.split(r"\s+[—–-]\s+", t)[0].strip()
        t = re.sub(r"\s*\(.*?\)\s*$", "", t).strip()
        # ⚠️ Un parentesis ABIERTO sin cerrar es un texto cortado por el troceo de
        # arriba («Pixel (intercom, also internet-connected»), y una linea que empieza
        # por «(Note:» es una nota del documento, no una tarea. Las dos se colaron en la
        # primera tanda y se habrian pegado como vocabulario.
        if t.count("(") != t.count(")") or t.startswith("(Note"):
            continue
        if 3 <= len(t) <= 70:
            mapa[actual].append(t)

con = {k: v for k, v in mapa.items() if v}
print("actividades con tareas: %d" % len(con))
print("tareas totales: %d" % sum(len(v) for v in con.values()))
_esperadas = set(SIN_ACTIVIDAD)
_inesperadas = [x for x in sin_casar if x not in _esperadas]
print("sin actividad en el catalogo, DECLARADAS: %d" % len(_esperadas & set(sin_casar)))
print("sin actividad y NO declaradas: %d" % len(_inesperadas))
for x in _inesperadas:
    print("   ⚠️ %s" % x)

print("")
print("# ── pegar en core/vocabulario.py ─────────────────────────────")
print("TAREAS = {")
for k in sorted(con):
    print("    %r: [" % k)
    for t in con[k]:
        print("        %r," % t)
    print("    ],")
print("}")
