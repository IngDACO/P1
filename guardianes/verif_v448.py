# -*- coding: utf-8 -*-
"""Guardián de v448 — F5 COMPLETO: el informe ADMIN, los correos y los prompts de la IA.

Con esto la migración i18n queda cerrada salvo lo que es DATO. Las tres exclusiones
son deliberadas y cada una tiene su razón escrita:

  1. **`schedule.PHASES`** — los nombres de actividad se GUARDAN en la hoja
     `Actividades`. Traducirlos dejaría los proyectos viejos en español y los nuevos
     en inglés sin forma de casarlos: es migración de histórico, no traducción.
  2. **La base de conocimiento de `chat_agent.SYSTEM_PROMPT`** (353 líneas de
     geometría del hueco, fórmulas, casos 1/2). Lo que decide el idioma de la
     RESPUESTA es la regla de estilo, que ya dice «responde SIEMPRE en inglés aunque
     esta guía esté en español»; el modelo lee español sin problema. Traducir 353
     líneas de contenido técnico denso mete riesgo de error en el conocimiento del
     asistente a cambio de cero beneficio visible.
  3. **Las CLAVES** de `INTERPRETATION_SCHEMA`/`USER_SCHEMA` (se guardan en
     `InterpJSON`) y las de los payloads del prompt.
"""
import ast
import io
import json
import logging
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "verif"}

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


# ── 1 ────────────────────────────────────────────────────────────
sec("1. El informe ADMIN se GENERA y sale en inglés (importar no ejecuta, v378)")
from pypdf import PdfReader                                        # noqa: E402
from core import projects as P, report, schedule as SCH, survey_calc  # noqa: E402
import pandas as _pd                                               # noqa: E402
from core.calculations import apply_offsets as _ao, analyze_matrix as _am  # noqa: E402
from core.bs_logic import find_bs_step as _bs                      # noqa: E402
from core.survey_calc import SURVEY_COLS as _SC                    # noqa: E402

_prj = next((x for x in P.list_projects("cliente1", incluir_archivados=True)
             if x.get("ParamsJSON") and x.get("MatrizJSON")), None)
# ⚠️ v474 · Si la demo no tiene ningún proyecto con survey (v456 la vació), se cae a un
# caso CONSTRUIDO en vez de salir SIN DATOS: la afirmación de este guardián llevaba
# versiones sin comprobarse. Se prefieren los datos REALES cuando los hay.
if _prj is None:
    import fixture_survey as _FIX
    if not _FIX.valido():
        print("‼️ el fixture no lo digiere el cálculo: no se puede afirmar nada")
        sys.exit(1)
    _prj = _FIX.proyecto()
    print("   (demo sin survey: se usa el caso construido `fixture_survey`)")

_r = survey_calc.recalcular(json.loads(_prj["ParamsJSON"]),
                            json.loads(_prj["MatrizJSON"]))
chk("`recalcular` devuelve la solución", _r is not None)
_df = _pd.DataFrame(json.loads(_prj["MatrizJSON"]))
_adj = _pd.DataFrame(_ao(_df.to_dict("records"), _r["limits"]))
_ana = _am(_adj.to_dict("records"), _r["limits"],
           wall_limiting=bool(_r["all_params"].get("WALL_LIMITING")))
try:
    _bsr = _bs(_r["all_params"], _r["limits"])
except Exception:
    _bsr = {}
_sch = SCH.build_schedule(int(json.loads(_prj["ParamsJSON"]).get("NS") or 2),
                          __import__("datetime").date(2026, 3, 2), {})
_ia = {"_ok": True, "parametros": "Geometry is consistent.",
       "estado_inicial": "Two levels are out of limit.",
       "desplazamientos": "Shift the block 6 mm.",
       "solucion_optima": "RL -6.0, FB 0.0.", "evasion_pared": "No limiting wall.",
       "bsr_vs_bs": "BSR matches BS.", "consideraciones": "Check the brackets."}


class _Caz(logging.Handler):
    def __init__(self):
        super().__init__()
        self.msgs = []

    def emit(self, rec):
        self.msgs.append(rec.getMessage())


_c = _Caz()
_lg = logging.getLogger("core.report")
_lg.addHandler(_c)
try:
    _pdf = report.generate_report(
        project_params=_r["all_params"], calculated=_r["limits"],
        survey_original=_df, survey_adjusted=_adj, lim_map=_r["lim_map"],
        analysis=_ana,
        optimizer_result={"best": _r["best"], "solutions": [_r["best"]],
                          "log": [], "total": 0, "valid": 0},
        bs_result=_bsr, survey_cols=list(_SC),
        interpretation=_ia, schedule=_sch, plumb=_r.get("plumb"))
finally:
    _lg.removeHandler(_c)

chk(f"el informe se genera ({len(_pdf) // 1024} KB)", len(_pdf) > 20000)
# ⚠️ El veredicto va dentro de un try/except que registra y sigue: un NameError ahí
# no revienta nada (el fallo real de v437). Se captura el log del módulo.
chk("nada se cayó a un `except` (log vacío)", not _c.msgs, str(_c.msgs))
_txt = " ".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(_pdf)).pages)
for _i in ("INPUT PARAMETERS", "GEOMETRIC LIMITS", "SURVEY MATRIX",
           "Interpretation", "Automatically generated report", "Omega side"):
    chk(f"el PDF dice «{_i}»", _i in _txt)

# ── 2 ────────────────────────────────────────────────────────────
sec("2. 0 español en el PDF RENDERIZADO (salvo los nombres de actividad, que son DATO)")
import re                                                          # noqa: E402
import unicodedata as _u                                           # noqa: E402


def _sin(x):
    return "".join(c for c in _u.normalize("NFD", x.lower())
                   if _u.category(c) != "Mn")


_ES = {"de", "la", "el", "los", "las", "del", "por", "para", "con", "sin", "que",
       "una", "unos", "unas", "cada", "sobre", "entre", "hasta", "desde", "limite",
       "limites", "matriz", "calculo", "parametros", "pisos", "paso", "pasos",
       "valores", "hueco", "cabina", "pared", "riel", "rieles"}
_ACT = {_sin(str(a.get("nombre", ""))) for a in _sch.get("activities", [])}
_malas = [l.strip()[:70] for l in _txt.splitlines()
          if _sin(l.strip()) not in _ACT
          and len(set(re.findall(r"[a-záéíóúñ]+", _sin(l))) & _ES) >= 2]
chk("0 líneas en español", not _malas, f"{len(_malas)}: {_malas[:3]}")
# ⚠️ Un «0» no vale si la sonda no ve el caso malo (trampa nº12).
chk("...y la sonda SABE ver una línea española",
    len(set(re.findall(r"[a-záéíóúñ]+", _sin("valores de la matriz limite"))) & _ES) >= 2)
chk("las ACTIVIDADES siguen en español (dato de la hoja `Actividades`)",
    bool(_ACT) and any(_sin(l.strip()) in _ACT for l in _txt.splitlines()))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Los prompts de la IA y sus claves")
from core import chat_agent, interpretation                        # noqa: E402
chk("el prompt del informe ADMIN está en inglés",
    interpretation.SYSTEM_PROMPT.lstrip().startswith("You are a senior engineer"))
chk("...y le pide al modelo escribir en inglés",
    "Always answer in clear, technical English" in interpretation.SYSTEM_PROMPT)
# ⚠️ Las CLAVES se guardan en `InterpJSON`: traducirlas deja las 7 secciones en blanco
chk("las CLAVES del schema NO se tradujeron",
    set(interpretation.INTERPRETATION_SCHEMA) ==
    {"parametros", "estado_inicial", "desplazamientos", "solucion_optima",
     "evasion_pared", "bsr_vs_bs", "consideraciones"},
    str(set(interpretation.INTERPRETATION_SCHEMA)))
chk("...y sus DESCRIPCIONES sí (van al prompt)",
    interpretation.INTERPRETATION_SCHEMA["parametros"].startswith("Analysis of"))
# ⚠️ EXCLUSIÓN DELIBERADA: la base de conocimiento se queda en español; lo que manda
# es la regla de estilo, que sí se tradujo.
chk("el asistente tiene la orden de responder en INGLÉS",
    "Responde SIEMPRE en inglés técnico claro" in chat_agent.SYSTEM_PROMPT)
chk("...aunque su base de conocimiento siga en español (exclusión con razón)",
    "GEOMETRÍA DEL HUECO" in chat_agent.SYSTEM_PROMPT)

# ── 4 ────────────────────────────────────────────────────────────
sec("4. El prefijo de «la IA falló» casa en los TRES sitios")
# ⚠️ Se PRODUCE en `interpretation` (×2) y se COMPARA en `report` y `user_report`:
# traducir unos y no otros deja la detección sin casar, y el informe imprimiría el
# mensaje de error como si fuera la interpretación.
_it = (RAIZ / "core/interpretation.py").read_text(encoding="utf-8")
_rp = (RAIZ / "core/report.py").read_text(encoding="utf-8")
_ur = (RAIZ / "core/user_report.py").read_text(encoding="utf-8")
chk("`interpretation` produce el prefijo inglés (2 veces)",
    _it.count('f"[Interpretation unavailable: {reason}]"') == 2,
    str(_it.count('f"[Interpretation unavailable: {reason}]"')))
chk("`report` compara contra ESE prefijo",
    '"[Interpretation unavailable"' in _rp and "Interpretación no disponible" not in _rp)
chk("`user_report` también",
    '"[Interpretation unavailable"' in _ur and "Interpretación no disponible" not in _ur)

# ── 5 ────────────────────────────────────────────────────────────
sec("5. El backend, sin mensajes en español (salvo las 3 exclusiones)")
import medir_f5 as M                                               # noqa: E402
EXCL_MOD = {"theme.py",        # comentarios dentro del CSS
            "schedule.py",     # nombres de actividad = DATO de la hoja
            "chat_agent.py",   # base de conocimiento del prompt (ver arriba)
            # SVG: el detector coge trozos de `fill="` / `text-anchor=`
            "belting.py", "buffer_cut.py", "plumb.py", "rail_cut.py", "diagrams.py"}


# ⚠️ Las CLAVES de `i18n.VALORES` son el español HEREDADO: DATO que el mapa
# traduce al MOSTRAR (v442/v469), no mensajes. Se derivan del mapa en vez de
# listarse, que es lo que se queda viejo. Mismo arreglo que en v449.
from core import i18n as _i18n_legado                       # noqa: E402
_LEGADO_ES = set(_i18n_legado.VALORES)


def _es_msg(s):
    return len(s.split()) >= 3 or s.rstrip().endswith((".", ":", "…"))


_pend = {}
for f in sorted((RAIZ / "core").glob("*.py")):
    if f.name.endswith("_ui.py") or f.name in EXCL_MOD:
        continue
    c = M.clasifica(f)
    r = sorted({s for _, s in c["RETORNO"] + c["OTRO"] if _es_msg(s) and s not in _LEGADO_ES})
    if r:
        _pend[f.name] = r[:2]
chk("0 mensajes en español fuera de las exclusiones", not _pend, str(_pend))
# ⚠️ Y las exclusiones se AFIRMAN, no se dan por hechas: si mañana alguien traduce
# los nombres de actividad, esto salta y obliga a mirar la migración del histórico.
chk("los nombres de ACTIVIDAD estan en INGLES y casan con el historico migrado (v453)",
    any("Guide rail installation" in str(x) for x in
        (getattr(SCH, "PHASES", None) or getattr(SCH, "ACTIVIDADES", []))))
# ⚠️ CADUCADO Y ACTUALIZADO en v453 (regla v385). Este chequeo EXIGIA que siguieran en
# espanol, y era correcto: los nombres se guardan en la hoja `Actividades`, asi que
# traducir solo el codigo habria dejado los proyectos viejos en espanol y los nuevos en
# ingles SIN forma de casarlos. Su trabajo era SALTAR el dia que alguien los tradujera y
# obligar a mirar la migracion — y eso es exactamente lo que hizo. La migracion se hizo
# en v453 (123/123 filas, 1 batch, verificadas leyendo), asi que la afirmacion se
# INVIERTE: ahora protege que no vuelvan al espanol y que codigo y hoja digan lo MISMO.

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
