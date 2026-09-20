# -*- coding: utf-8 -*-
"""Guardián de v444 — las CABECERAS DE TABLA que son clave de dict.

⚠️ Una clave de dict y una etiqueta se ven IGUAL en el AST, así que aquí la decisión
no se toma por idioma: se mide qué hace cada cadena en el repo. Cuatro motivos para
NO traducirla, y los cuatro fallan EN SILENCIO si se ignoran:

  IDENTIFICADOR      es opción de un widget o se compara con `==` → la rama queda
                     MUERTA (el fallo de v441 en corte de rieles)
  COLUMNA DE EDITOR  el código lee la tabla editada por ese nombre Y el `_snapshot`
                     de v148 la guarda en `DatosJSON` (`CAL-0002` ya tiene una con
                     la columna `Elevador`) → renombrarla rompe «reabrir el cálculo»
  SE LEE             se indexa por ella en otro módulo → la lectura se queda
                     buscando una columna que ya no existe
  VALOR i18n         es el DATO en español de la hoja; `etiqueta()` lo traduce solo
                     al MOSTRARLO (v442)

Y el modo de fallo propio de esta tanda: traducir la clave de la FILA y no la del
`column_config` (o al revés). Streamlit no da error — la columna pierde formato,
ancho y etiqueta, y la tabla se descoloca.
"""

def _cc_dict(v, fn=None):
    """El dict de `column_config`, venga literal, por `tabla.cfg(None, {...})` o por
    una VARIABLE.

    ⚠️ v450 movió la configuración a `tabla.cfg`, que traduce la CABECERA sin tocar la
    clave. Sin resolverlo, un chequeo que solo entiende `ast.Dict` deja de mirar todas
    las tablas y devuelve 0 — que parece un aprobado y no lo es.

    ⚠️ v471: y si llega por VARIABLE (`_colcfg = {...}` → `tabla.cfg(None, _colcfg)`)
    hay que resolverla, por dos motivos. Uno, si no, esa tabla no se mira. Y dos, el
    grave: ese dict sigue viviendo en la función, así que sus claves entraban en
    `filas` y **el chequeo se aprobaba a sí mismo otra vez, por otra puerta** — estaba
    VERDE con dos huérfanas delante en `clientes_ui`, y una le costó a la columna de
    dinero su formato `$%,d` (o sea, reintrodujo el fallo de v399).
    """
    import ast as _a
    if isinstance(v, _a.Call) and getattr(v.func, "attr", "") == "cfg":
        v = v.args[1] if len(v.args) > 1 else None
    if isinstance(v, _a.Name) and fn is not None:
        # el ULTIMO valor asignado a esa variable dentro de la función
        for nd in _a.walk(fn):
            if isinstance(nd, _a.Assign) and len(nd.targets) == 1 \
               and isinstance(nd.targets[0], _a.Name) \
               and nd.targets[0].id == v.id and isinstance(nd.value, _a.Dict):
                return nd.value
        return None
    return v if isinstance(v, _a.Dict) else None

import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
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


UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
ARB = {f: ast.parse(f.read_text(encoding="utf-8")) for f in UI}

# ── 1 ────────────────────────────────────────────────────────────
sec("1. Ninguna `column_config` apunta a una columna que ya no existe")


def _fn_de(tr, nodo):
    for c in ast.walk(tr):
        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(c):
                if x is nodo:
                    return c
    return None


huerfanas, miradas = [], 0
for f, tr in ARB.items():
    for nd in ast.walk(tr):
        if not (isinstance(nd, ast.Call)
                and getattr(nd.func, "attr", "") in ("dataframe", "data_editor")):
            continue
        cc = next((k.value for k in nd.keywords if k.arg == "column_config"), None)
        # ⚠️ CADUCADO en v450 y ACTUALIZADO, no relajado: la configuración pasó a
        # `tabla.cfg(None, {...})`, así que un chequeo que solo entiende `ast.Dict`
        # dejaba de mirar las 66 tablas y devolvía «0 huérfanas» — que parece un
        # aprobado. Lo que la regla protege sigue igual: ninguna `column_config`
        # puede apuntar a una columna que la tabla no tiene.
        fn = _fn_de(tr, nd)
        if fn is None:
            continue
        cc = _cc_dict(cc, fn)
        if cc is None:
            continue
        miradas += 1
        claves = {k.value for k in cc.keys
                  if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        # ⚠️ EXCLUIR el propio `column_config`: su dict también vive dentro de la
        # función, así que contándolo el chequeo SE APROBABA A SÍ MISMO — con la
        # mitad de la traducción rota delante decía «0 huérfanas». Lo destapó
        # probarlo contra código roto, no leerlo.
        _cc = {id(x) for x in ast.walk(cc)}
        # ⚠️ `_colcfg["Cost"] = ...` añade una clave al column_config, no a la fila:
        # sin esto volveria a contarse como columna existente.
        _cc_vars = {t_.value.id for t_ in
                    [x.targets[0] for x in ast.walk(fn)
                     if isinstance(x, ast.Assign) and len(x.targets) == 1]
                    if isinstance(t_, ast.Subscript) and isinstance(t_.value, ast.Name)}
        filas = {k.value for d in ast.walk(fn)
                 if isinstance(d, ast.Dict) and id(d) not in _cc
                 for k in d.keys
                 if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        h = claves - filas - {"_index"}
        if h:
            huerfanas.append(f"{f.name}:{nd.lineno} {sorted(h)}")
chk(f"0 huérfanas en las {miradas} tablas con column_config", not huerfanas,
    str(huerfanas))
chk("...y el chequeo miró algo (0 sobre 0 tablas no es un aprobado)", miradas >= 20,
    str(miradas))

# ── 2 ────────────────────────────────────────────────────────────
sec("2. El DATO no se tocó: identificadores, editores y valores")
_rc = (RAIZ / "core/rail_cut_ui.py").read_text(encoding="utf-8")
_pu = (RAIZ / "core/projects_ui.py").read_text(encoding="utf-8")
_au = (RAIZ / "core/auth_ui.py").read_text(encoding="utf-8")

# columnas de editor persistidas en DatosJSON (v148)
chk("rieles: `Riel` y `Elevador` siguen siendo las columnas del editor",
    'disabled=["Riel"]' in _rc and 'in_edit[f"Elevador {i+1}"]' in _rc)
# IDs de sub-pestaña, comparados por `sub ==` (v232) y usados por los deep-links
for _id in ('"📊 Estado"', '"💰 Costos"', '"📎 Archivos"', '"🚨 Avisos"'):
    chk(f"el ID de sub-pestaña {_id} sigue intacto", _id in _pu)
chk("el ID '📊 Su trabajo' de la ficha sigue intacto", '"📊 Su trabajo"' in _au)
# valores que traduce `i18n.etiqueta()` al mostrar
from core import i18n                                              # noqa: E402
chk("los estados siguen en español en el mapa de i18n (son el DATO)",
    "En progreso" in i18n.VALORES and "Planificado" in i18n.VALORES)

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Las cabeceras traducidas están, y ninguna a medias")
PARES = [
    ("projects_ui.py", "Status", "Situación"),
    ("projects_ui.py", "Alerts", "Alertas"),
    ("projects_ui.py", "Users", "Usuarios"),
    ("projects_ui.py", "Purchases", "Compras"),
    ("clientes_ui.py", "Phone", "Teléfono"),
    ("inventory_ui.py", "Location", "Ubicación"),
    ("auth_ui.py", "Credentials", "Credenciales"),
    ("catalogo_ui.py", "Item", "Artículo"),
]
for mod, ing, esp in PARES:
    src = (RAIZ / "core" / mod).read_text(encoding="utf-8")
    chk(f"{mod}: «{esp}» → «{ing}», y no queda ninguna a medias",
        f'"{ing}"' in src and f'"{esp}"' not in src,
        f"ing={f'\"{ing}\"' in src} esp_resto={f'\"{esp}\"' in src}")

# ── 4 ────────────────────────────────────────────────────────────
sec("4. QUINTA red: etiquetas de UNA palabra dentro de tuplas y dicts")
# ⚠️ Estas no las ve ninguna de las cuatro redes anteriores: la de posición mira el
# argumento de `st.*` (aquí el argumento es la TUPLA), la de frases pide 3+ palabras,
# la de cortas 2, y la de f-strings mira f-strings. Y no se pueden barrer en masa,
# porque la MISMA cadena es dato en otro sitio: `"Credenciales"` y `"Alarmas"` son
# también nombres de hoja, y `"Proyectos"`/`"Usuarios"` conviven con los IDs de
# sub-pestaña `"📊 Proyectos"`/`"👷 Usuarios"`, que NO se tocan.
_ind = _pu[_pu.index("    inds = ["):_pu.index("    _urg = sum(")]
for _esp, _ing in (("Vencidos", "Overdue"), ("Credenciales", "Credentials"),
                   ("Alarmas", "Alarms"), ("Sobre presup.", "Over budget")):
    chk(f"indicador «{_esp}» → «{_ing}»",
        f'"{_ing}"' in _ind and f'"{_esp}"' not in _ind)
# el 8º elemento (nombre visible) traducido, el 7º (ID de sub-pestaña) intacto
chk("el nombre visible de sección va en inglés",
    '"📊 Proyectos", "Projects",' in _ind and '"👷 Usuarios", "Users",' in _ind
    and '"💰 Gastos", "Expenses",' in _ind)
chk("...y el ID de sub-pestaña NO se tocó (lo compara `sub ==`)",
    _ind.count('"📊 Proyectos"') == 6 and _ind.count('"👷 Usuarios"') == 2)
chk("el botón de navegar ya no dice «Ir a»", "→ Ir a {secn}" not in _pu)

_hu = (RAIZ / "core/home_ui.py").read_text(encoding="utf-8")
chk("buscador: las etiquetas de tipo van en inglés y las CLAVES no se tocan",
    '"proyecto": "Projects"' in _hu and '"persona": "People"' in _hu)
_au2 = (RAIZ / "core/ausencias_ui.py").read_text(encoding="utf-8")
# ⚠️ Se comprueban los LITERALES EXACTOS del chip, no la subcadena en el fichero:
# «approved» aparece también en otros textos del módulo, así que la versión laxa
# seguía en verde con el chip devuelto al español. Lo destapó la rotura.
chk("ausencias: los 4 chips de estado en inglés, con la CLAVE intacta",
    all(x in _au2 for x in ('AU.PENDIENTE: "🟡 pending"',
                            'AU.APROBADA: "🟢 approved"',
                            'AU.RECHAZADA: "🔴 rejected"',
                            'AU.CANCELADA: "⚪ cancelled"')))

# ── 5 ────────────────────────────────────────────────────────────
sec("5. El clasificador de riesgo sigue sabiendo distinguir")
import riesgo_claves as RK  # noqa: E402,F401  (imprime su propia clasificación)







print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
