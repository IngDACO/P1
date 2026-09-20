"""Guardián de v437 — F1b: el informe del CLIENTE, en inglés.

Lo que protege:

 1. ⚠️ **Las CLAVES de `USER_SCHEMA` son DATO.** Se guardan en `Proyectos.InterpJSON`
    y `user_report` las lee (`ia.get("resumen")`). Traducirlas dejaría las cinco
    secciones de texto EN BLANCO en todos los informes, sin ningún error.
 2. ⚠️ **Las claves de `schedule_table` / `plumb_table` / `plumb_checks` tampoco.**
    El informe traduce el ENCABEZADO de esas tablas pero indexa por la clave que
    produce el otro módulo; tocarla daría KeyError o una columna vacía.
 3. ⚠️ **El veredicto NO puede deducirse del texto de la IA.** Era
    `"requiere cortes" in ia["cortes"]`: frágil, e imposible en inglés — la frase
    española no casaría nunca y el informe diría «sin valores fuera de límite» en
    un hueco que sí hay que cortar. Sale de `interpretation.cortes_por_piso`.
 4. El informe usa `d()` (idioma BASE) y no `t()`.
 5. El PDF se GENERA y su texto sale en inglés (prueba funcional).
 6. La IA del informe del cliente escribe en INGLÉS.
"""
import ast
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def arbol(rel):
    return ast.parse((RAIZ / rel).read_text(encoding="utf-8"))


# ── 1 ────────────────────────────────────────────────────────────
sec("1. Las CLAVES de USER_SCHEMA son DATO (se guardan en InterpJSON)")
from core import interpretation as I                              # noqa: E402

_CLAVES = ["resumen", "desplazamientos", "cortes", "implementacion", "verificacion"]
chk("las 5 claves siguen siendo las mismas", list(I.USER_SCHEMA) == _CLAVES,
    str(list(I.USER_SCHEMA)))
# ⚠️ y el informe tiene que seguir leyendo ESAS claves, no otras
_ur = (RAIZ / "core" / "user_report.py").read_text(encoding="utf-8")
_leidas = set(re.findall(r'ia\.get\("([a-z_]+)"\)', _ur))
chk("el informe lee exactamente esas claves", _leidas == set(_CLAVES),
    f"lee {sorted(_leidas)}")
chk("...y el chequeo no corre en vacío", len(_leidas) == 5, f"{len(_leidas)}")
# las descripciones sí están en inglés
_ES = re.compile(r"\b(el|la|los|las|del|con|para|por|que|una|en|su|al|lo|es|son|"
                 r"como|desde|hasta|obra|hueco|piso|cliente|texto)\b", re.I)
_desc_es = [k for k, v in I.USER_SCHEMA.items()
            if re.search(r"[áéíóúñÑ¿¡]", v) or _ES.search(v)]
chk("sus descripciones sí están traducidas", not _desc_es, str(_desc_es))

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Las claves de las tablas de otros módulos siguen intactas")
from core import schedule as SCH, plumb as PL                     # noqa: E402

# ⚠️ Se comprueba contra lo que PRODUCEN de verdad, no contra una lista mía.
_sch = SCH.build_schedule(4, __import__("datetime").date(2026, 1, 5), {})
_fila = SCH.schedule_table(_sch)[0]
_usa_sch = set(re.findall(r'r\["([^"]+)"\]', _ur))
_faltan = [k for k in ("Actividad", "Inicio", "Fin", "Duración (d)", "Peso (%)")
           if k in _usa_sch and k not in _fila]
chk("las claves del cronograma que usa el informe EXISTEN", not _faltan, str(_faltan))
chk("...y el informe sí indexa alguna (no corre en vacío)",
    bool(_usa_sch & set(_fila)), f"usa={sorted(_usa_sch)}")

_pl_keys = {"Línea", "X inicial (mm)", "X final (mm)", "Desplazada",
            "Medida", "Distancia (mm)"}
chk("las claves del plomado que usa el informe siguen en el código",
    _pl_keys <= _usa_sch, str(sorted(_pl_keys - _usa_sch)))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. El veredicto sale de los DATOS, no del texto de la IA")
_t = arbol("core/user_report.py")
_gen = next(x for x in ast.walk(_t)
            if isinstance(x, ast.FunctionDef) and x.name == "generate_user_report")
_src_gen = ast.unparse(_gen)
chk("nada compara contra `ia[...]` para decidir el veredicto",
    "in str(ia.get(" not in _src_gen and "'requiere cortes'" not in _src_gen)
chk("se usa `cortes_por_piso`", "cortes_por_piso" in _src_gen)
# ejercitar la función REAL, no reproducir su lógica
_lim = {"LIMIT_OR": 50, "LIMIT_OL": 50}
chk("sin cortes → lista vacía",
    I.cortes_por_piso(_lim, {"matrix": [{"OR": 40, "OL": 30}]}) == [])
_c = I.cortes_por_piso(_lim, {"matrix": [{"OR": 40, "OL": 30}, {"OR": 63.5, "OL": 20}]})
chk("con un corte → lo localiza en su piso",
    _c == [{"cortar_OR_mm": 13.5, "piso": 2}], str(_c))
chk("best vacío / None no revientan",
    I.cortes_por_piso(_lim, {}) == [] and I.cortes_por_piso(_lim, None) == [])
# ⚠️ y `_build_user_payload` tiene que usar la MISMA función, o el veredicto y la
# IA hablarían de cortes distintos.
_ti = arbol("core/interpretation.py")
_bp = next(x for x in ast.walk(_ti)
           if isinstance(x, ast.FunctionDef) and x.name == "_build_user_payload")
chk("el payload de la IA usa la misma definición de cortes",
    "cortes_por_piso" in ast.unparse(_bp))

# ── 4 ────────────────────────────────────────────────────────────
sec("4. El informe va en el idioma BASE (d), no en el de la pantalla (t)")
_usa_d = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "d"
             for x in ast.walk(_t))
_usa_t = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "t"
             for x in ast.walk(_t))
chk("user_report usa d() y no t()", _usa_d and not _usa_t, f"d={_usa_d} t={_usa_t}")
# ⚠️ NINGÚN título de sección puede ser un literal suelto. Mi primera versión solo
# miraba el ÍNDICE, así que devolver `_section("3. Cortes necesarios")` al español
# pasaba el chequeo — el índice seguía en inglés y el título no. Se comprueba la
# llamada, que es lo que de verdad pinta la cabecera.
_lit = [ast.unparse(x.args[0])
        for x in ast.walk(_t)
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
        and x.func.id in ("_section", "_callout") and x.args
        and isinstance(x.args[0], ast.Constant)]
chk("ningún _section/_callout recibe un literal (todos pasan por d)", not _lit, str(_lit))
# ⚠️ NINGUNA variable ni argumento puede llamarse `d`: Python marca el nombre local en
# el ÁMBITO ENTERO de la función, así que un `for i, (t, d) in ...` al final del cuerpo
# revienta las 40 etiquetas de arriba con UnboundLocalError — y ni compilar ni importar
# lo ven. Fue el fallo real de v437. Se prohíbe también en lambdas: ahí sería inofensivo,
# pero deja la trampa puesta para el siguiente que edite.
_shadow = []
for _x in ast.walk(_t):
    if isinstance(_x, ast.Name) and isinstance(_x.ctx, ast.Store) and _x.id == "d":
        _shadow.append(f"asignación:{_x.lineno}")
    if isinstance(_x, ast.arg) and _x.arg == "d":
        _shadow.append(f"argumento:{_x.lineno}")
chk("ninguna variable llamada `d` tapa la función del motor", not _shadow, str(_shadow))
chk("...y el chequeo no corre en vacío: hay llamadas que vigilar",
    sum(1 for x in ast.walk(_t) if isinstance(x, ast.Call)
        and isinstance(x.func, ast.Name) and x.func.id == "_section") >= 12)
# ⚠️ con el diccionario español VACÍO, t() y d() devuelven lo mismo y esto no
# distinguiría nada: hay que darle una traducción de verdad.
from core import i18n                                             # noqa: E402
_orig = i18n._dic
try:
    i18n._dic = lambda idi: {"Client": "Cliente"}
    i18n.set_idioma("es")
    chk("con idioma español, t() SÍ traduce", i18n.t("Client") == "Cliente")
    chk("...y d() NO (el informe sale del mismo idioma siempre)",
        i18n.d("Client") == "Client")
finally:
    i18n._dic = _orig
    i18n.set_idioma("en")

# ── 5 ────────────────────────────────────────────────────────────
sec("5. El PDF se GENERA y sale en inglés (prueba funcional)")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "verif"}
try:
    from pypdf import PdfReader                                   # noqa: E402
    from core import projects as P, survey_calc, user_report      # noqa: E402
    import json                                                    # noqa: E402

    _prj = next((x for x in P.list_projects("cliente1", incluir_archivados=True)
                 if x.get("ParamsJSON") and x.get("MatrizJSON")), None)
    # ⚠️ v474 · caso CONSTRUIDO si la demo no tiene survey (ver `fixture_survey`).
    if _prj is None:
        import fixture_survey as _FIX
        if not _FIX.valido():
            print("‼️ el fixture no lo digiere el cálculo")
            sys.exit(1)
        _prj = _FIX.proyecto()
        print("   (demo sin survey: se usa el caso construido)")
    if True:
        _par = json.loads(_prj["ParamsJSON"])
        _mat = json.loads(_prj["MatrizJSON"])
        # ⚠️ `recalcular` devuelve {all_params, limits, lim_map, best, plumb} —
        # NO `calculated`/`optimizer_result`, que es como los llama la FIRMA del
        # informe. Comprobado leyendo la llamada real de `survey_ui` (regla v135):
        # calculated = limits, y el `best` hay que envolverlo.
        _r = survey_calc.recalcular(_par, _mat)
        _ia = {"_ok": True, "resumen": "The shaft is suitable.",
               "desplazamientos": "Shift the block.", "cortes": "No cuts required.",
               "implementacion": "Set the brackets.", "verificacion": "Measure again."}
        _sch = SCH.build_schedule(int(_par.get("NS") or 2),
                                  __import__("datetime").date(2026, 3, 2), {})
        # ⚠️ Se CAPTURA el log del módulo: el bloque del veredicto va dentro de un
        # `try/except` que registra y sigue, así que un NameError ahí no revienta
        # nada — deja `_cortes=False` en silencio. Fue el fallo real de v437
        # (`limits` en vez de `calculated`), y solo se vio leyendo este log.
        import logging

        class _Cazador(logging.Handler):
            def __init__(self):
                super().__init__(); self.msgs = []

            def emit(self, rec):
                self.msgs.append(rec.getMessage())

        _caz = _Cazador()
        _lg = logging.getLogger("core.user_report")
        _lg.addHandler(_caz)
        try:
            _pdf = user_report.generate_user_report(
                project_params=_r["all_params"], calculated=_r["limits"],
                optimizer_result={"best": _r["best"]}, lim_map=_r["lim_map"],
                survey_cols=["WR", "FR", "OR", "WL", "FL", "OL"],
                interpretation_user=_ia, schedule=_sch, plumb=_r.get("plumb"))
        finally:
            _lg.removeHandler(_caz)
        _txt = " ".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(_pdf)).pages)
        chk(f"el informe se genera ({len(_pdf)//1024} KB)", len(_pdf) > 20000)
        chk("el veredicto NO se cae al except (ningún aviso en el log)",
            not _caz.msgs, str(_caz.msgs))
        chk("la PORTADA sale en inglés",
            all(k in _txt for k in ("TECHNICAL REPORT", "Elevator", "Client", "Location")))
        chk("el ÍNDICE sale en inglés",
            all(k in _txt for k in ("Contents", "1. Solution summary", "3. Cuts required",
                                    "12. Conclusions")))
        # ⚠️ `_section` PARTE el título: pinta «05» en un lado y el texto en el otro,
        # así que buscar «5. Shaft diagrams» entero nunca casa. Mi primera versión lo
        # hacía y pasaba igual… porque el ÍNDICE contiene esas mismas cadenas: estaba
        # midiendo el índice, no la cabecera — un chequeo que aprueba por el motivo
        # equivocado. Se compara el título SIN el número, que es lo que se pinta.
        _TIT = ["Solution summary", "Final positioning", "Cuts required",
                "Solution matrix (by floor)", "Shaft diagrams",
                "Project schedule and S-curve", "Site implementation",
                "Final verification", "Final plumb line layout",
                "Scope and methodology", "Glossary", "Conclusions"]
        _falt_t = [x for x in _TIT if x not in _txt]
        chk("los 12 TÍTULOS de sección salen en inglés en el PDF", not _falt_t, str(_falt_t))
        # ⚠️ En MAYÚSCULAS: la etiqueta de la tarjeta KPI la sube el estilo, así que
        # comparar tal cual daba FALLO con el informe perfecto (`Values out of limit`
        # sale `VALUES OUT OF LIMIT`). El test fallando por su propio formato — v372.
        _up = _txt.upper()
        chk("el VEREDICTO y los KPI salen en inglés",
            all(k.upper() in _up for k in ("Lateral shift (RL)", "Front shift (FB)",
                                           "Values out of limit", "Stops")))
        # ⚠️ Y la frase del veredicto que depende de los cortes, EJERCITADA en las dos
        # direcciones sobre la función real (con el fallo del `except` daba siempre la
        # rama «sin valores fuera de límite»).
        _con = user_report.generate_user_report(
            project_params=_r["all_params"], calculated=_r["limits"],
            optimizer_result={"best": {**_r["best"], "total_off": 0,
                                       "matrix": [{**_r["best"]["matrix"][0],
                                                   "OR": _r["lim_map"]["OR"] + 12}]}},
            lim_map=_r["lim_map"], survey_cols=["WR", "FR", "OR", "WL", "FL", "OL"],
            interpretation_user=_ia)
        _sin = user_report.generate_user_report(
            project_params=_r["all_params"], calculated=_r["limits"],
            optimizer_result={"best": {**_r["best"], "total_off": 0,
                                       "matrix": [{**_r["best"]["matrix"][0],
                                                   "OR": _r["lim_map"]["OR"] - 12,
                                                   "OL": _r["lim_map"]["OL"] - 12}]}},
            lim_map=_r["lim_map"], survey_cols=["WR", "FR", "OR", "WL", "FL", "OL"],
            interpretation_user=_ia)

        def _t(b):
            return " ".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(b)).pages)

        chk("con cortes → el veredicto los CITA",
            "with the cuts listed in section 3" in _t(_con))
        chk("sin cortes → dice que no hay valores fuera de límite",
            "with no values out of limit" in _t(_sin))
        chk("el ALCANCE y el GLOSARIO salen en inglés",
            all(k in _txt for k in ("Scope and methodology", "Glossary",
                                    "Limitations and validity")))
        # ⚠️ CADUCADO en v459 y ACTUALIZADO (regla v385): decía «Engineer in
        # charge», que v459 renombró a «Head installer/s». No se vio antes
        # porque este guardián llevaba SIN DATOS desde v456 — un guardián que
        # no corre envejece a oscuras. Lo que se protege no cambia: el bloque
        # de firma sale en inglés.
        chk("la FIRMA sale en inglés",
            all(k in _txt for k in ("PREPARED BY", "RECEIVED BY",
                                    "Head installer/s")))
        chk("el pie de página sale en inglés", "Generated on" in _txt and "Page" in _txt)
        _restos = [k for k in ("INFORME TÉCNICO", "Resumen de la solución", "Contenido",
                               "Alcance y metodología", "Glosario", "PREPARADO POR",
                               "Conclusiones", "Ubicación", "Ingeniero responsable",
                               "Generado el", "Página") if k in _txt]
        chk("no queda ninguna etiqueta en español", not _restos, str(_restos))
except Exception as e:
    import traceback
    chk("el informe se genera", False, f"{type(e).__name__}: {e}")
    traceback.print_exc()

# ── 6 ────────────────────────────────────────────────────────────
sec("6. La IA del informe del cliente escribe en INGLÉS")
chk("el system prompt está en inglés",
    "professional, clear, confident English" in I.USER_SYSTEM_PROMPT
    and "español" not in I.USER_SYSTEM_PROMPT.lower())
_pay = ast.unparse(_bp)
chk("las instrucciones del payload piden inglés", "ENGLISH text" in _pay)
chk("...y ya no piden español", "en español" not in _pay)
# ⚠️ CADUCADO por v448: esta afirmación fallaba **por haber ganado**. Cuando se
# escribió, el prompt del informe ADMIN seguía en español a propósito porque iba en
# F5 — y F5 ya se hizo. Se invierte: lo que hay que proteger ahora es que los DOS
# prompts (cliente y admin) pidan escribir en inglés, que es lo que decide el
# idioma de lo que el modelo redacta en cada informe.
chk("el prompt del informe ADMIN ya está en inglés (F5, v448)",
    I.SYSTEM_PROMPT.lstrip().startswith("You are a senior engineer")
    and "Always answer in clear, technical English" in I.SYSTEM_PROMPT)

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
