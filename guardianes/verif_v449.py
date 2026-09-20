# -*- coding: utf-8 -*-
"""Guardián de v449 — el CIERRE de la migración i18n.

Mide con las tres redes a la vez (frases, etiquetas cortas, f-strings mixtas) sobre
TODA la interfaz y todo el backend, y afirma que lo único que queda en español es lo
que NO se puede traducir. Cada exclusión lleva su razón; ninguna es «lo que no dio
tiempo».

⚠️ Un «0» solo vale para la forma que la red sabe ver (trampa nº30), así que las tres
redes se validan con casos construidos antes de creerse su cero.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "verif"}

from barre_frases import frases                                    # noqa: E402
from barre_cortas import _sin                                      # noqa: E402
from barre_fstr_mixto import mixtas, ES                            # noqa: E402
import medir_f5 as M                                               # noqa: E402

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


UI = sorted(list((RAIZ / "core").glob("*_ui.py"))) + [RAIZ / "app.py"]
INT = [f for f in sorted((RAIZ / "core").glob("*.py"))
       if not f.name.endswith("_ui.py")]

# ── Exclusiones DELIBERADAS, cada una con su razón ───────────────────────────
EXCL_CAD = {
    "🗺 Ruta del día", "📊 Su trabajo",       # IDs de sub-pestaña: los compara `sub ==`
    "En progreso", "En pausa", "⏸ En pausa",  # estados GUARDADOS en la hoja
    "por vencer",                            # lo devuelve `credentials.status()`
    # ⚠️ v467: la carpeta pasó a «COPEX Assets». Ya no se excluye porque el peligro
    # que lo justificaba —crear otra y dejar los archivos en la vieja— se resolvió
    # RENOMBRÁNDOLA en Drive (`drive_store.carpeta_con_legado`), que conserva su
    # contenido. Se sigue listando como identificador externo, no como etiqueta.
    "COPEX Assets",
}
EXCL_MOD = {
    "theme.py",       # comentarios dentro de las cadenas de CSS
    "schedule.py",    # nombres de actividad = DATO de la hoja `Actividades`
    "chat_agent.py",  # base de conocimiento del prompt (v448, decisión escrita)
    # SVG: el detector coge trozos de `fill="` / `text-anchor=`
    "belting.py", "buffer_cut.py", "plumb.py", "rail_cut.py", "diagrams.py",
}


def _esp(s):
    # `Login`, `Grupos`, `Rieles` son NOMBRES DE HOJA citados en un texto inglés
    if re.search(r"`(Login|Grupos|Rieles)`", s):
        return False
    limpio = re.sub(r"#[0-9a-fA-F]{3,8}", " ", s)
    limpio = re.sub(r"<[^>]*>", " ", limpio)
    return bool(set(re.findall(r"[a-záéíóúñü]+", _sin(limpio))) & ES)


def _saltar(s):
    return (s in EXCL_CAD or s.lstrip().startswith("<style>") or "/*" in s
            or "function f(s)" in s)


# ── 1 ────────────────────────────────────────────────────────────
sec("1. La INTERFAZ, con las tres redes a la vez")
_ui = [f"{f.name}:{ln} {s[:40]!r}" for f in UI for ln, s in set(frases(f, minimo=2))
       if not _saltar(s) and _esp(s)]
chk(f"0 etiquetas en español en los {len(UI)} módulos de interfaz", not _ui,
    f"{len(_ui)}: {_ui[:4]}")

_fs = [f"{f.name}:{ln} {s[:40]!r}" for f in UI for ln, s in set(mixtas(f))
       if not any(x in s for x in ("Elevador", "%Y%m%d"))
       and not s.lstrip().startswith("<") and "font-family" not in s
       and "display:flex" not in s]
chk("0 f-strings a medio traducir", not _fs, f"{len(_fs)}: {_fs[:3]}")

# ── 2 ────────────────────────────────────────────────────────────
sec("2. El BACKEND")


def _es_msg(s):
    return len(s.split()) >= 3 or s.rstrip().endswith((".", ":", "…"))


_bk = {}
# ⚠️ Las CLAVES de `i18n.VALORES` son el español HEREDADO: el dato viejo que el
# mapa traduce al MOSTRAR (v442/v469). No son mensajes y no se traducen — son
# la mitad izquierda del diccionario. Se derivan del mapa en vez de listarse,
# porque una lista a mano en paralelo a la verdad es lo que se queda vieja.
from core import i18n as _i18n_legado                                # noqa: E402
_LEGADO_ES = set(_i18n_legado.VALORES)
for f in INT:
    if f.name in EXCL_MOD:
        continue
    c = M.clasifica(f)
    r = sorted({s for _, s in c["RETORNO"] + c["OTRO"]
                if _es_msg(s) and s not in _LEGADO_ES})
    if r:
        _bk[f.name] = r[:2]
chk("0 mensajes en español fuera de las exclusiones", not _bk, str(_bk))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. ⚠️ Las redes SABEN ver el caso malo (un 0 sin esto no vale, trampa nº12)")
_p = AQUI / "_probe_v449.py"
_p.write_text('import streamlit as st\n'
              'st.caption("Se guardaron los datos del proyecto")\n'
              'x = 1\n'
              'y = f"Collected {x} de {x}"\n', encoding="utf-8")
try:
    _vf = {s for _, s in frases(_p, minimo=2)}
    chk("la red de frases ve una etiqueta española",
        any(_esp(s) for s in _vf), str(_vf))
    _vm = {s for _, s in mixtas(_p)}
    chk("la red de f-strings ve una mixta", bool(_vm), str(_vm))
finally:
    _p.unlink(missing_ok=True)

_p2 = AQUI / "_probe_v449b.py"
_p2.write_text('def f():\n    return False, "No se pudo abrir la hoja."\n',
               encoding="utf-8")
try:
    chk("la red del backend ve un mensaje devuelto",
        any(_es_msg(s) for _, s in M.clasifica(_p2)["RETORNO"]))
finally:
    _p2.unlink(missing_ok=True)

# ── 3b ───────────────────────────────────────────────────────────
sec("3b. Ningún `t()` se CONGELA al importar (el fallo que mordió CINCO veces)")
# ⚠️ v445 `auth.SESION_OCUPADA` · v446 `ausencias.TIPOS` · v447 `plan_data.USA` y
# `toolruns.HERRAMIENTAS` · v449 `invoices_ui._EST_FMT`. Las cinco las cazó este
# chequeo, y las cinco las cometí DESPUÉS de documentarlo. Va también en el guardián
# de cierre para que no dependa de que se corra otro.
from barre_t_modulo import congelados, EXCL                        # noqa: E402
_frios = []
for _f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    if _f.name in EXCL:
        continue
    _frios += [f"{_f.name}:{ln}" for ln, _ in sorted(set(congelados(_f)))]
chk("0 llamadas a `t()` congeladas al importar", not _frios, str(_frios))

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Las exclusiones se AFIRMAN, no se dan por hechas")
from core import i18n, schedule as SCH, chat_agent                 # noqa: E402
from core import projects as P                                     # noqa: E402
_hu = (RAIZ / "core/home_ui.py").read_text(encoding="utf-8")
_pu = (RAIZ / "core/projects_ui.py").read_text(encoding="utf-8")
_iu = (RAIZ / "core/inventory_ui.py").read_text(encoding="utf-8")

# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto
# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y
# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la
# afirmacion cambia de objeto pero NO de principio.
from core import valores as _VAL3                              # noqa: E402
chk("el ESTADO que se guarda es el canonico",
    "On hold" in P.ESTADOS_MANUAL and P.derive_estado(50, "", "") == "In progress",
    "%s - %s" % (P.ESTADOS_MANUAL, P.derive_estado(50, "", "")))
chk("...y una fila SIN migrar sigue casando",
    _VAL3.canon("En progreso") == "In progress" and _VAL3.canon("En pausa") == "On hold")
chk("...y `etiqueta()` no muta un estado que ya es canonico",
    all(i18n.etiqueta(e) == e for e in P.ESTADOS_MANUAL if e))
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
chk("la base de conocimiento del asistente sigue en español, con la orden en inglés",
    "GEOMETRÍA DEL HUECO" in chat_agent.SYSTEM_PROMPT
    and "Responde SIEMPRE en inglés técnico claro" in chat_agent.SYSTEM_PROMPT)
# ⚠️ CADUCADO por v467 e INVERTIDO, no relajado: la carpeta ya está en inglés y lo
# que hay que proteger es que se llegue ahí RENOMBRANDO la vieja —conserva los
# archivos— y nunca creando una nueva, que es lo que los dejaría huérfanos.
chk("la carpeta de Drive está en inglés y la vieja se RENOMBRA, no se recrea",
    '"COPEX Assets"' in _iu and '"COPEX Activos"' not in _iu
    and "carpeta_con_legado" in Path("core/drive_store.py").read_text(encoding="utf-8"))

# ⚠️ Los IDs de sub-pestaña llevan emoji porque SON el identificador: los compara
# `sub ==` y los usan los deep-links. Se tradujo el DISPLAY, no el ID.
# ⚠️ Se comprueba en el fichero que POSEE cada uno: con un `or` entre dos ficheros,
# romper el de `home_ui` pasaba porque `projects_ui` seguía teniéndolo. Lo destapó
# probarlo contra código roto, no leerlo (la lección de v439, otra vez).
# ⚠️ Y el chequeo que de verdad protege: cada ID DEFINIDO en `_SUBSECCIONES` tiene
# que aparecer en un `sub == "…"`. Comprobar solo que «el ID sigue ahí» dejaba pasar
# traducir la DEFINICIÓN y no la comparación — que es justo la RAMA MUERTA (el fallo
# de v441 en corte de rieles). Con el ID cambiado en un solo lado, la sub-pestaña
# deja de abrirse y no salta ningún error.
import ast                                                         # noqa: E402
_tr_hu = ast.parse(_hu)
_ids_def, _ultimos = set(), set()
for _n in ast.walk(_tr_hu):
    if not (isinstance(_n, ast.Assign) and any(
            isinstance(t_, ast.Name) and t_.id.startswith("_SUBSECCIONES")
            for t_ in _n.targets)):
        continue
    # cada valor es (clave_de_estado, [ (id, display), … ])
    for _e in ast.walk(_n.value):
        if not (isinstance(_e, ast.Tuple) and len(_e.elts) == 2
                and isinstance(_e.elts[1], ast.List)):
            continue                      # ⚠️ el 1º es la CLAVE DE ESTADO, no un ID
        _lista = [x.elts[0].value for x in _e.elts[1].elts
                  if isinstance(x, ast.Tuple) and x.elts
                  and isinstance(x.elts[0], ast.Constant)]
        if _lista:
            _ids_def.update(_lista)
            _ultimos.add(tuple(_lista))     # la sección entera, para el chequeo por grupo
_comparados = set()
for _f in list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]:
    _t = ast.parse(_f.read_text(encoding="utf-8"))
    for _n in ast.walk(_t):
        if isinstance(_n, ast.Compare):
            for _x in [_n.left] + list(_n.comparators):
                if isinstance(_x, ast.Constant) and isinstance(_x.value, str):
                    _comparados.add(_x.value)
                if isinstance(_x, (ast.List, ast.Tuple, ast.Set)):
                    for _e in _x.elts:
                        if isinstance(_e, ast.Constant) and isinstance(_e.value, str):
                            _comparados.add(_e.value)
chk("se leyeron los IDs de `_SUBSECCIONES` (si no, el chequeo pasa en vacío)",
    len(_ids_def) >= 15, str(len(_ids_def)))
# ⚠️ El invariante correcto es POR SECCIÓN: el despachador es un `if/elif/else`, así
# que su `else` puede absorber **exactamente uno** sin comparar. Dos sin comparar en
# la misma sección significa que un ID cambió en la definición y no en su rama — la
# RAMA MUERTA. (Mi primera versión asumía que el del `else` era «el último de la
# lista» y no lo es: en finanzas es `⏱ Horas`, el 5.º de 8, y en proyectos es el
# PRIMERO. Una heurística cómoda que daba dos ramas muertas inexistentes.)
_malas_sec = {sec: sorted(set(sec) - _comparados)
              for sec in _ultimos if len(set(sec) - _comparados) > 1}
chk("ninguna sección tiene 2+ IDs sin comparar (0 ramas muertas)", not _malas_sec,
    str({k[:2]: v for k, v in _malas_sec.items()}))
chk("...y el chequeo miró las secciones de verdad", len(_ultimos) >= 4,
    str(len(_ultimos)))
chk("...y su DISPLAY sí está en inglés",
    ":material/receipt_long: Expenses" in _hu
    and ":material/folder: Files" in _pu)

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
