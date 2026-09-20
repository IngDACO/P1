"""Barrido de control de F3: compila, importa y busca español en lo que se PINTA.

⚠️ El detector de español NO decide si un módulo está terminado (esa es la lección de
v439): lo que decide es el barrido por POSICIÓN de `i18n_tool.piezas`. Esto es solo una
red de seguridad para leer de un vistazo lo que haya quedado.
"""
import ast
import importlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "x", "rol": "administrador",
                            "grupo": "cliente1", "nombre": "x"}
from i18n_tool import piezas                                      # noqa: E402

ES = re.compile(
    r"[áéíóúÁÉÍÓÚñÑ¿¡]|\b(de|del|la|el|los|las|con|para|por|que|una|un|su|al|es|son|"
    r"se|y|lo|grupo|usuario|usuarios|manual|riel|credencial|zona|nomina|proyecto|"
    r"cliente|obra|fichaje|dia|dias|semana|activo|bodega|hora|horas|nombre|fecha|"
    r"guardar|eliminar|crear|nuevo|nueva|todos|todas|sin|más|aún|ver)\b", re.I)

tot = 0
for m in sys.argv[1:]:
    rel = f"core/{m}.py" if m != "app" else "app.py"
    ast.parse((RAIZ / rel).read_text(encoding="utf-8"))
    try:
        importlib.import_module(m if m == "app" else "core." + m)
        imp = "importa"
    except Exception as e:                                        # noqa: BLE001
        imp = f"⚠️ NO IMPORTA: {type(e).__name__}: {e}"
    ps = [p for p in piezas(RAIZ / rel) if ES.search(p["txt"])]
    tot += len(ps)
    print(f"{m:18} compila · {imp} · {len(ps)} con español")
    for p in sorted(ps, key=lambda x: x["lin"])[:8]:
        print(f"     {p['lin']:5} {p['txt'][:64]!r}")
print(f"\nTOTAL con español (revisar: puede haber falsos positivos): {tot}")
