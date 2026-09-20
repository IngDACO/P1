"""Guardián de v439 — F1d (correos y alarmas) + F2 (la app de campo), en inglés.

Lo que protege:

 1. ⚠️ **Las CLAVES de dato siguen en español.** `usuario`, `proyecto`, `fecha`,
    `Desde`, `Hasta`, `Tipo`, `Estado`, `Ubicacion`, `clock_in`… son claves de dict y
    columnas de hoja: traducirlas rompe la lectura SIN dar ningún error.
 2. ⚠️ **Los correos y las alarmas van con `d` (idioma BASE), no con `t`.** Un correo
    SALE de la app: su idioma no puede depender de cómo tenga la pantalla quien lo
    dispara (regla de v436).
 3. ⚠️ **Los mensajes de LOG no se traducen ni se envuelven.** `logger.warning`
    comparte NOMBRE con `st.warning`, y el extractor los coló en la primera pasada.
 4. Los cuatro módulos de campo no tienen etiquetas en español.
 5. El motor está importado a nivel de MÓDULO (v342: ámbito, no presencia).
 6. Los cuerpos de correo y alarma se GENERAN en inglés (prueba funcional).
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

CAMPO = ["core/timeclock_ui.py", "core/prestart_ui.py",
         "core/ausencias_ui.py", "core/route_ui.py"]
CORREO = ["core/notify.py", "core/alerts.py"]
ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def _fuente(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


# ── 1 ────────────────────────────────────────────────────────────
sec("1. Las CLAVES de dato siguen en español (traducirlas rompe en silencio)")
# ⚠️ Se pinta el número MÍNIMO de apariciones, no la presencia: traducir UNA de las
# seis apariciones de `"clock_in"` deja las otras cinco y un chequeo de presencia lo
# aprueba — y una traducción PARCIAL es justo la más insidiosa (unos sitios leen la
# clave vieja y otros la nueva). Es un mínimo, no una igualdad: añadir usos legítimos
# sube la cuenta y sigue pasando; renombrar la baja y salta.
CLAVES = {
    "core/timeclock_ui.py": {'"usuario"': 5, '"proyecto"': 5, '"clock_in"': 6, '"tipo"': 1},
    "core/prestart_ui.py":  {'"usuario"': 10, '"User"': 2, '"fecha"': 2, '"nombre"': 5},
    "core/ausencias_ui.py": {"'From'": 5, "'To'": 5, "'Type'": 3, '"User"': 1},
    "core/route_ui.py":     {'"User"': 1, '"Location"': 4},
    "core/alerts.py":       {'"User"': 2, '"Date"': 1, '"ProjectID"': 3},
}
for rel, ks in CLAVES.items():
    src = _fuente(rel)
    bajan = [f"{k} {src.count(k)}<{n}" for k, n in ks.items() if src.count(k) < n]
    chk(f"{Path(rel).name:20} conserva sus claves", not bajan, str(bajan))
chk("...y el chequeo no corre en vacío", sum(len(v) for v in CLAVES.values()) >= 15)

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Correos y alarmas: idioma BASE (`d`), no el de la pantalla (`t`)")
for rel in CORREO:
    tr = ast.parse(_fuente(rel))
    _imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
               and any(a.name == "d" and a.asname == "_d" for a in x.names)
               for x in tr.body)
    _usa_t = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "t"
                 for x in ast.walk(tr))
    chk(f"{Path(rel).name:16} importa `d as _d` y NO usa t()", _imp and not _usa_t,
        f"imp={_imp} t={_usa_t}")
    _tapa = [x.lineno for x in ast.walk(tr)
             if (isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and x.id == "_d")
             or (isinstance(x, ast.arg) and x.arg == "_d")]
    chk(f"{Path(rel).name:16} nada tapa `_d`", not _tapa, str(_tapa))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Los mensajes de LOG no se envuelven en t()/d()")
malos = []
for rel in CAMPO + CORREO:
    tr = ast.parse(_fuente(rel))
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)):
            continue
        r = x.func.value
        rid = r.id if isinstance(r, ast.Name) else ""
        if rid.lower() not in {"logger", "logging", "log"}:
            continue
        for a in x.args:
            if isinstance(a, ast.Call) and isinstance(a.func, ast.Name) and a.func.id in ("t", "d", "_d"):
                malos.append(f"{Path(rel).name}:{x.lineno}")
chk("ningún logger.* recibe t()/d()", not malos, str(malos))
_nlogs = sum(len(re.findall(r"logger\.\w+\(", _fuente(r))) for r in CAMPO + CORREO)
chk("...y hay llamadas a logger que vigilar", _nlogs >= 5, f"{_nlogs}")

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Los módulos de campo no tienen etiquetas en español")
# ⚠️ Claves de dict y columnas de hoja. NO son etiquetas: aparecen en el barrido porque
# el AST no distingue un subíndice de un texto, y traducirlas rompería la lectura.
DATOS = {"usuario", "User", "proyecto", "Project", "nombre", "Name", "fecha", "Date",
         "From", "To", "Type", "Status", "Days", "Reason", "desde", "hasta", "tipo",
         "estado", "ingreso", "etiqueta", "clock_in", "Location", "ProjectID", "grupo",
         "dias", "general", "personas", "persona", "campo", "entrada", "salida", "horas",
         "asignados", "usados", "restantes", "periodo", "label", "error", "filename",
         "facilitador", "location", "asistentes", "act_notes", "gen_notes", "ilimitado",
         "near_miss_desc", "ficho", "drive_id", "emoji"}
ES = re.compile(r"[áéíóúñÑ¿¡]|\b(el|la|los|las|del|con|para|por|que|una|un|su|al|es|son|de|se|y|"
                r"como|hasta|obra|hoy|día|días|tu|te|esta|este|hay|ya|sin|más|cada|semana|"
                r"jornada|elige|añadir|guardar|abrir|cerrar|libres|registrada|firmado)\b", re.I)
rest = []
for rel in CAMPO:
    src = _fuente(rel)
    tr = ast.parse(src)
    doc, logs = set(), set()
    for x in ast.walk(tr):
        if isinstance(x, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            b = getattr(x, "body", None)
            if (b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                doc.add(id(b[0].value))
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute):
            r = x.func.value
            if (r.id if isinstance(r, ast.Name) else "").lower() in {"logger", "logging", "log"}:
                for a in ast.walk(x):
                    if isinstance(a, ast.Constant):
                        logs.add(id(a))
    for x in ast.walk(tr):
        if (isinstance(x, ast.Constant) and isinstance(x.value, str)
                and id(x) not in doc and id(x) not in logs
                and x.value.strip() not in DATOS and len(x.value.strip()) > 2
                and "function" not in x.value and ES.search(x.value)):
            rest.append(f"{Path(rel).name}:{x.lineno} {x.value[:45]!r}")
chk("0 etiquetas en español en los 4 módulos de campo", not rest, str(rest[:5]))

# ⚠️ EL CHEQUEO DE ARRIBA NO BASTA, y esta es la lección cara de v439: el detector de
# español busca acentos y palabras funcionales, así que «Fichar», «Firma», «Iniciales»,
# «Pendientes», «Sitios» o «Mis ausencias» pasan por delante — y con él dije que F2
# estaba terminada cuando quedaban 40 etiquetas. El chequeo que SÍ mide es por POSICIÓN:
# todo literal que llega a una función de display y NO está envuelto en `t()`.
# La lista de excepciones es explícita: si alguien añade una etiqueta suelta, salta.
DISPLAY = {"markdown", "write", "caption", "title", "header", "subheader", "info",
           "warning", "error", "success", "text", "button", "checkbox", "radio",
           "selectbox", "multiselect", "text_input", "text_area", "number_input",
           "date_input", "time_input", "file_uploader", "slider", "toggle", "expander",
           "popover", "metric", "download_button", "form_submit_button", "dialog",
           "toast", "link_button", "segmented_control"}
NO_TEXTO = re.compile(r"^\s*(</?\w|;|\{|:gray\[|:red\[)|style=|font-|border|background|"
                      r"margin|padding|flex|^https?:|^#[0-9a-fA-F]{3,8}$|^:material/[\w_]+:$")
sueltos = []
for rel in CAMPO:
    tr = ast.parse(_fuente(rel))
    envueltos = set()
    for x in ast.walk(tr):
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id in ("t", "d", "_d"):
            for c in ast.walk(x):
                if isinstance(c, ast.Constant):
                    envueltos.add(id(c))
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                and x.func.attr in DISPLAY):
            continue
        r = x.func.value
        if (r.id if isinstance(r, ast.Name) else "").lower() in {"logger", "logging", "log"}:
            continue
        _args = list(x.args) + [k.value for k in x.keywords
                                if k.arg in ("label", "help", "placeholder", "body", "text")]
        for a in _args:
            for c in ast.walk(a):
                if not (isinstance(c, ast.Constant) and isinstance(c.value, str)):
                    continue
                v = c.value.strip()
                if (id(c) in envueltos or len(v) < 3 or v in DATOS
                        or NO_TEXTO.search(v) or not re.search(r"[A-Za-zÁ-ú]{3}", v)):
                    continue
                sueltos.append(f"{Path(rel).name}:{c.lineno} {v[:48]!r}")
# ⚠️ Tope, no cero: quedan trozos legítimos (fragmentos de f-string ya en inglés que se
# concatenan, claves de dict que el AST no distingue de un texto). El número está
# MEDIDO sobre el código correcto; que SUBA significa que alguien metió una etiqueta
# suelta, y eso es lo que hay que cazar.
chk(f"literales de display sin t() bajo el tope ({len(sueltos)})", len(sueltos) <= 95,
    str(sueltos[:6]))
chk("...y el barrido no corre en vacío", len(sueltos) >= 10, f"{len(sueltos)}")

# ⚠️ El detector de español NO basta: «Registrados», «Planificado» o «Total» no llevan
# acento ni palabra funcional, así que una etiqueta traducida de vuelta pasa por delante
# (es lo que dejó escapar una etiqueta de plomada en v438). Chequeos POSITIVOS: el inglés
# esperado tiene que ESTAR.
INGLES = {
    "core/timeclock_ui.py": ["Close the workday", "On a project", "Day you finished"],
    "core/prestart_ui.py":  ["Who is attending the talk?", "Recorded", "First and last name"],
    "core/ausencias_ui.py": ["What do you need?", "Include weekends", "No absences recorded."],
    "core/route_ui.py":     ["Open the route in Google Maps", "Previous day",
                             "You have no active sites assigned."],
}
for rel, frases in INGLES.items():
    src = _fuente(rel)
    faltan = [f for f in frases if f not in src]
    chk(f"{Path(rel).name:20} conserva su inglés", not faltan, str(faltan))

# ── 5 ────────────────────────────────────────────────────────────
sec("5. El motor, importado a nivel de MÓDULO (v342: ámbito, no presencia)")
for rel in CAMPO:
    tr = ast.parse(_fuente(rel))
    _imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
               and any(a.name == "t" for a in x.names) for x in tr.body)
    _tapa = [x.lineno for x in ast.walk(tr)
             if (isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and x.id == "t")
             or (isinstance(x, ast.arg) and x.arg == "t")]
    chk(f"{Path(rel).name:20} importa `t` arriba y nada lo tapa",
        _imp and not _tapa, f"imp={_imp} tapa={_tapa}")

# ── 6 ────────────────────────────────────────────────────────────
sec("6. Los correos y las alarmas se GENERAN en inglés (sin enviar nada)")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "verif"}
from core import notify, alerts                                   # noqa: E402

cap = []
notify.notify_user = lambda u, s, l, link=None: cap.append((s, l)) or {}
notify.notify_assignment("x", {"Name": "Torre A", "Client": "ACME",
                               "Location": "Sydney", "StartDate": "2026-09-01",
                               "EndDateEst": "2026-10-01", "InductionLinks": "http://a"})
notify.notify_induction("x", "Torre A", ["http://a"])
alerts._notify = lambda dest, subj, lines: cap.append((subj, lines))
alerts.create_alert = lambda *a, **k: (True, "ALR-9999")
alerts._admins_and_owners = lambda g: ["admin1"]
alerts.report_problem("PRJ-1", "cliente1", "falta material", "campo1", "Torre A")
alerts.notify_change("PRJ-1", "cliente1", "fechas movidas", "admin1", ["campo1"], "Torre A")

chk("se generaron los 4 mensajes", len(cap) == 4, f"{len(cap)}")
_todo = " || ".join(s + " :: " + " | ".join(map(str, l)) for s, l in cap)
# ⚠️ el texto del USUARIO va en el mensaje ("falta material") y es suyo, no una
# etiqueta: se excluye antes de buscar español.
for _u in ("falta material", "fechas movidas"):
    _todo = _todo.replace(_u, "")
_mal = [w for w in ("Nuevo proyecto", "Te asignaron", "Ubicación", "Ábrelo",
                    "Inducciones del", "Completa las", "Alarma en", "Problema reportado",
                    "Actualización en", "El administrador actualizó", "Cliente:", "Inicio:")
        if w in _todo]
chk("ninguna etiqueta en español en los cuerpos", not _mal, str(_mal))
_esp = [k for k in ("New project assigned", "You have been assigned", "Location",
                    "Open it in the app", "Project inductions", "Alert on project",
                    "Problem reported by", "Update on",
                    "The administrator updated project") if k not in _todo]
chk("el inglés esperado SÍ está", not _esp, str(_esp))

# ── 7 ────────────────────────────────────────────────────────────
sec("7. REGLA GENERAL: ninguna función del repo tapa `t` / `d` / `_d`")
# ⚠️ Python marca un nombre local en el ÁMBITO ENTERO de la función, así que un
# `for t, cfg in ...` al final rompe las llamadas `t(...)` de arriba con
# UnboundLocalError — o con `'str' object is not callable`, que fue lo que dejó
# «Mis ausencias» sin abrir. No lo ven ni `compileall` ni importar el módulo.
import glob                                                       # noqa: E402


def _mismo_ambito(fn):
    """Nodos de ESTA función, sin descender a lambdas ni funciones anidadas.

    ⚠️ `ast.walk` sí desciende, y eso da FALSOS POSITIVOS: un `lambda t: ...` tiene su
    PROPIO ámbito, así que su parámetro no tapa nada de fuera (es la trampa nº3 del
    documento). Con `walk` a secas, `format_func=lambda t: …` se denunciaba como si
    rompiera la función entera.
    """
    fuera = []
    for hijo in fn.body:
        pila = [hijo]
        while pila:
            n = pila.pop()
            fuera.append(n)
            for c in ast.iter_child_nodes(n):
                if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef)):
                    pila.append(c)
    return fuera


tapan = []
for rel in sorted(glob.glob("core/*.py")) + ["app.py"]:
    try:
        tr = ast.parse((RAIZ / rel).read_text(encoding="utf-8"))
    except Exception:                                             # noqa: BLE001
        continue
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nodos = _mismo_ambito(fn)
        # ⚠️ En Python 3 una COMPRENSIÓN tiene su propio ámbito: `[t for t, e in …]` no
        # liga `t` en la función que la contiene, así que no tapa nada. Contarlo daba
        # falsos positivos sobre código correcto (trampa nº3).
        _comp = {id(nn) for x in nodos for g in (getattr(x, "generators", []) or [])
                 for nn in ast.walk(g.target) if isinstance(nn, ast.Name)}
        _args = {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
        for nm in ("t", "d", "_d"):
            _st = [x.lineno for x in nodos
                   if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)
                   and x.id == nm and id(x) not in _comp]
            if nm in _args:
                _st.append(fn.lineno)
            _ld = [x.lineno for x in nodos
                   if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == nm]
            if _st and _ld:
                tapan.append(f"{rel}:{fn.lineno} {fn.name} tapa `{nm}`")
chk("0 funciones tapan el motor en TODO el repo", not tapan, str(tapan[:4]))
# ⚠️ y que el barrido no corra en vacío: tiene que haber llamadas que vigilar
_llam = sum(1 for rel in sorted(glob.glob("core/*.py"))
            for x in ast.walk(ast.parse((RAIZ / rel).read_text(encoding="utf-8")))
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
            and x.func.id in ("t", "d", "_d"))
chk("...y hay llamadas al motor que vigilar", _llam >= 200, f"{_llam}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
