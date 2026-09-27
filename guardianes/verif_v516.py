# -*- coding: utf-8 -*-
"""v516 · EL PARTE DIARIO EN TEXTO LIBRE.

Lo que protege:
  (a) ⚠️ que `DailyLogs` esté en el lote de lectura: fuera de él, `registros()` devuelve
      None y un parte se escribiría en la hoja sin que la app lo volviera a ver NUNCA,
      sin un solo error (v461, v507, v514 — tres veces ya);
  (b) ⚠️ que un guardado fallido NO se lleve el texto por delante, y que el motivo que
      se enseña sea el REAL (v511) y no «no está configurado» cuando es la cuota;
  (c) que el parte se guarde con obra, fecha, autor y hora, en la fila POSICIONAL que
      dice la cabecera (v363);
  (d) ⚠️ que solo su AUTOR pueda borrarlo, y solo el MISMO día: el valor de esto es que
      sea lo que alguien dijo que hizo ese día;
  (e) ⚠️ que borrar la obra se lleve sus partes — el fallo de los créditos huérfanos de
      v514, escrito de antemano esta vez;
  (f) que un parte vacío o desmedido se rechace ANTES de tocar la hoja;
  (g) que el orden sea por CUÁNDO se escribió, no por el día reportado.
Todo EJECUTANDO, con la hoja sustituida: importar no ejecuta (v378), y sin ejercitar la
ESCRITURA las roturas que importan se escapan (la lección de v510).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    # ⚠️ Acepta el detalle y lo ignora: el idioma `(ok if cond else fallo)(msg, det)`
    # llama a las dos con la MISMA firma, y sin esto el guardián revienta justo cuando
    # la comprobación PASA. Está escrito en la cabecera de `verif_v470` y lo volví a
    # hacer igual: reventar en vez de denunciar, por séptima vez en este proyecto.
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from core import hojas as H                                       # noqa: E402
from core import daily_log as DL                                  # noqa: E402

HOY = "2026-09-23"
AYER = "2026-09-22"


class _WS:
    """Hoja de mentira que se queda con lo escrito y deja borrar por índice."""

    def __init__(self, filas=None):
        self.filas = [list(f) for f in (filas or [])]
        self.borradas = []
        self.revienta = False

    def get_all_records(self, numericise_ignore=None):
        if self.revienta:
            raise RuntimeError("429 quota exceeded")
        return [dict(zip(DL.HEADERS, f)) for f in self.filas]

    def append_row(self, fila, value_input_option=None):
        if self.revienta:
            raise RuntimeError("429 quota exceeded")
        self.filas.append(list(fila))

    def delete_rows(self, fila):
        self.borradas.append(fila)
        del self.filas[fila - 2]


# ⚠️ El reloj de mentira FORMATEA de verdad, no devuelve una cadena fija. La primera
# versión devolvía `"2026-09-23 18:40"` dijera lo que dijera el formato, así que el
# código podía pedir segundos y el guardián nunca se enteraba — un stub que miente
# sobre su contrato hace que el guardián mida al stub y no al código.
import datetime as _dt                                            # noqa: E402

_AHORA = _dt.datetime(2026, 9, 23, 18, 40, 7)


class _Reloj:
    def now(self, g=None):
        return _AHORA

    def today(self, g=None):
        return _AHORA.date()


def _fila(lid, pid, dia, autor, texto, creado=None):
    return [lid, "cliente1", pid, dia, autor, texto, DL.MANUAL,
            creado or (dia + " 12:00")]


def _con(filas=None):
    """Sustituye hoja, caché y reloj. Devuelve la hoja falsa."""
    h = _WS(filas)
    DL._ws = lambda: h
    DL._records = lambda: [dict(zip(DL.HEADERS, f)) for f in h.filas]
    DL._invalidate = lambda: None
    DL.clock = _Reloj()
    return h


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ La hoja está en el LOTE (o leería vacío para siempre)")
chk("«DailyLogs» está en HOJAS_LECTURA", DL.SHEET in H.HOJAS_LECTURA,
    "no está: un parte guardado no se volvería a ver, sin ningún error")
# ⚠️ Y se lee SIN cabeceras, que es lo que hace que el punto anterior importe: con
# cabeceras caería en `get_sheet`, que CREA la hoja — un lector que escribe (v145).
_src = io.open("core/daily_log.py", encoding="utf-8").read()
_a = ast.parse(_src)
_reg = [n for n in ast.walk(_a)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "registros"]
chk("lee con `registros(SHEET)` sin cabeceras",
    len(_reg) == 1 and len(_reg[0].args) == 1, "%d llamadas" % len(_reg))

# ═════════════════════════════════════════════════════════════════
sec("2. La fila POSICIONAL casa con la cabecera (v363)")
h = _con()
_ok, lid = DL.crear("PRJ-1", "cliente1", "Cerré los bedplates del 3 y el 4", "juan")
chk("se guarda y devuelve su ID", _ok and str(lid).startswith("LOG-"), lid)
chk("...y escribe UNA fila", len(h.filas) == 1, len(h.filas))
_f = dict(zip(DL.HEADERS, h.filas[0])) if h.filas else {}
chk("...con tantas columnas como cabeceras",
    len(h.filas[0]) == len(DL.HEADERS) if h.filas else False,
    "%s vs %s" % (len(h.filas[0]) if h.filas else 0, len(DL.HEADERS)))
for _c, _v in (("ProjectID", "PRJ-1"), ("Group", "cliente1"), ("Author", "juan"),
               ("Date", HOY), ("Source", DL.MANUAL)):
    chk("...`%s` cae en su sitio" % _c, _f.get(_c) == _v, _f.get(_c))
chk("...el texto llega entero", _f.get("Text") == "Cerré los bedplates del 3 y el 4")
chk("...y queda la hora, no solo el día",
    len(str(_f.get("Created", ""))) >= 16, _f.get("Created"))
# ⚠️ Día reportado y día de escritura son cosas distintas y las dos hacen falta: sin
# `Created` no se puede ordenar dos partes del mismo día; sin `Date` no se sabe de qué
# jornada habla uno escrito a la mañana siguiente.
chk("...y son DOS columnas distintas, no una",
    "Date" in DL.HEADERS and "Created" in DL.HEADERS
    and DL.HEADERS.index("Date") != DL.HEADERS.index("Created"))

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ Un guardado fallido NO puede llevarse el texto")
h = _con()
h.revienta = True
_ok, _msg = DL.crear("PRJ-1", "cliente1", "doscientas palabras", "juan")
chk("si la hoja no responde, se dice que NO se guardó", _ok is False, _ok)
chk("...y nada quedó escrito a medias", len(h.filas) == 0, len(h.filas))
# ⚠️ El motivo REAL: con la cuota agotada, «no está configurado» es FALSO y manda al
# usuario a tocar los secretos en vez de esperar un minuto (el fallo de v511).
from core import timeclock as TC                                  # noqa: E402
chk("...y el motivo sale de `timeclock.motivo_sin_hoja` (v511)",
    _msg == TC.motivo_sin_hoja(), _msg)
chk("...que NO dice «not configured» cuando el problema es la cuota",
    "not configured" not in TC.motivo_sin_hoja().lower()
    or not TC._secrets_present(), TC.motivo_sin_hoja())
# ⚠️ ESCAPE CAZADO POR LA BATERÍA: hay DOS maneras de no tener hoja —que `_ws()` devuelva
# None y que la escritura reviente—, y lo de arriba solo ejercita la segunda. Romper la
# primera pasaba por delante sin que nada saltara. Son la misma familia de fallo (v511:
# `_ws()` devuelve None por dos motivos distintos y el llamante culpa a la configuración),
# así que las dos ramas tienen que decir lo mismo.
DL._ws = lambda: None
for _f, _q in ((lambda: DL.crear("PRJ-1", "cliente1", "algo", "juan"), "crear"),
               (lambda: DL.borrar("LOG-0001", "juan"), "borrar")):
    _r = _f()
    chk("sin hoja, `%s` da el motivo real y no «not configured»" % _q,
        _r[0] is False and _r[1] == TC.motivo_sin_hoja(), _r)
chk("sin hoja, `borrar_de_obra` no dice que borró nada",
    DL.borrar_de_obra("PRJ-1") == 0)

# ⚠️ Y la pantalla tiene que RESPETARLO: la caja solo se vacía en la rama del éxito.
_ui = io.open("core/daily_log_ui.py", encoding="utf-8").read()
_au = ast.parse(_ui)
_pops = [n for n in ast.walk(_au)
         if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "pop"
         and any(getattr(a, "id", "") == "_k" for a in n.args)]
_dentro = False
for _n in ast.walk(_au):
    if isinstance(_n, ast.If):
        _seg = ast.get_source_segment(_ui, _n) or ""
        if "session_state.pop(_k" in _seg and _seg.lstrip().startswith("if ok"):
            _dentro = True
chk("la caja de texto SOLO se vacía si la hoja confirmó",
    len(_pops) == 1 and _dentro,
    "pops=%d dentro_de_if_ok=%s" % (len(_pops), _dentro))

# ═════════════════════════════════════════════════════════════════
sec("4. Lo que NO es un parte se rechaza ANTES de tocar la hoja")
h = _con()
for _txt, _q in ((" ", "vacío"), ("", "cadena vacía"), (None, "None"),
                 ("x" * (DL.MAX_TEXTO + 1), "más largo que el tope")):
    _ok, _m = DL.crear("PRJ-1", "cliente1", _txt, "juan")
    chk("un parte %s se rechaza" % _q, _ok is False, _m)
chk("...y la hoja sigue intacta (no se tocó para rechazarlos)",
    len(h.filas) == 0, len(h.filas))
_ok, _m = DL.crear("", "cliente1", "algo", "juan")
chk("un parte sin obra se rechaza", _ok is False, _m)
_ok, _m = DL.crear("PRJ-1", "cliente1", "x" * DL.MAX_TEXTO, "juan")
chk("...pero uno JUSTO en el tope entra (el límite no se pasa de celoso)", _ok is True, _m)

# ═════════════════════════════════════════════════════════════════
sec("5. ⚠️ Borrar: solo su autor, y solo el mismo día")
_base = [_fila("LOG-0001", "PRJ-1", HOY, "juan", "lo de hoy"),
         _fila("LOG-0002", "PRJ-1", AYER, "juan", "lo de ayer"),
         _fila("LOG-0003", "PRJ-1", HOY, "ana", "lo de ana")]
h = _con(_base)
_ok, _m = DL.borrar("LOG-0003", "juan")
chk("otro usuario NO puede borrar un parte ajeno", _ok is False, _m)
chk("...y no lo borró", len(h.filas) == 3, len(h.filas))
_ok, _m = DL.borrar("LOG-0002", "juan")
chk("ni su propio parte de OTRO día", _ok is False, _m)
chk("...y tampoco lo borró", len(h.filas) == 3, len(h.filas))
_ok, _m = DL.borrar("LOG-0001", "juan")
chk("su propio parte de HOY sí", _ok is True, _m)
chk("...y se fue de la hoja", len(h.filas) == 2, len(h.filas))
chk("...la fila correcta (la 2, no otra)", h.borradas == [2], h.borradas)
_ok, _m = DL.borrar("LOG-9999", "juan")
chk("un ID que no existe se dice, no revienta", _ok is False, _m)

# ═════════════════════════════════════════════════════════════════
sec("6. ⚠️ Borrar la obra se lleva sus partes (el fallo de v514)")
h = _con([_fila("LOG-0001", "PRJ-1", HOY, "juan", "a"),
          _fila("LOG-0002", "PRJ-2", HOY, "ana", "b"),
          _fila("LOG-0003", "PRJ-1", AYER, "juan", "c")])
_n = DL.borrar_de_obra("PRJ-1")
chk("se lleva los DOS de esa obra", _n == 2, _n)
chk("...y deja el de la otra", len(h.filas) == 1 and h.filas[0][2] == "PRJ-2",
    [f[2] for f in h.filas])
# ⚠️ De abajo arriba: borrando de arriba abajo, la segunda fila ya se habría desplazado
# y se llevaría por delante a la de la obra de al lado.
chk("...borrando de ABAJO ARRIBA", h.borradas == sorted(h.borradas, reverse=True),
    h.borradas)
# Y que `delete_project` lo LLAME de verdad, no que exista sin usarse (trampa nº2: AST).
_ap = ast.parse(io.open("core/projects.py", encoding="utf-8").read())
_del = next((n for n in ast.walk(_ap)
             if isinstance(n, ast.FunctionDef) and n.name == "delete_project"), None)
_llama = any(isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "borrar_de_obra"
             for c in ast.walk(_del)) if _del else False
chk("`delete_project` lo llama", _llama)

# ═════════════════════════════════════════════════════════════════
sec("7. Se lee del más reciente al más viejo, por CUÁNDO se escribió")
h = _con([_fila("LOG-0001", "PRJ-1", HOY, "juan", "primero", HOY + " 09:00"),
          _fila("LOG-0002", "PRJ-1", HOY, "juan", "segundo", HOY + " 18:00"),
          _fila("LOG-0003", "PRJ-1", AYER, "ana", "de ayer", AYER + " 17:00")])
_p = DL.partes("PRJ-1")
chk("los trae todos", len(_p) == 3, len(_p))
chk("...el último escrito primero", _p[0].get("Text") == "segundo",
    [x.get("Text") for x in _p])
# ⚠️ Ordenar por `Date` dejaría los dos de hoy en el orden en que estén en la hoja: da
# igual casi siempre y justo el día que alguien escriba dos veces, miente.
chk("...y dos del MISMO día quedan en su orden real",
    [x.get("Text") for x in _p[:2]] == ["segundo", "primero"],
    [x.get("Text") for x in _p[:2]])
# ⚠️ ESTO LO ENCONTRÓ LA HOJA REAL, NO ESTE GUARDIÁN, y la razón es exactamente la que
# hace que ejercitar contra la hoja valga la pena: arriba les puse horas DISTINTAS a
# mano, y en la obra los dos partes se escriben en el mismo minuto. Con `%H:%M` el
# `Created` empataba, `sorted` es estable y el empate dejaba el más VIEJO arriba.
# Ahora `Created` lleva segundos y el ID desempata lo que quede.
h = _con([_fila("LOG-0001", "PRJ-1", HOY, "juan", "viejo", HOY + " 18:40:07"),
          _fila("LOG-0002", "PRJ-1", HOY, "juan", "nuevo", HOY + " 18:40:41")])
chk("dos partes del mismo MINUTO se ordenan bien (segundos)",
    [x.get("Text") for x in DL.partes("PRJ-1")] == ["nuevo", "viejo"],
    [x.get("Text") for x in DL.partes("PRJ-1")])
# ⚠️ Y si hasta los segundos empatan —dos escrituras en el mismo segundo— el ID manda.
h = _con([_fila("LOG-0001", "PRJ-1", HOY, "juan", "viejo", HOY + " 18:40:07"),
          _fila("LOG-0002", "PRJ-1", HOY, "juan", "nuevo", HOY + " 18:40:07")])
chk("...y con el MISMO segundo, desempata el ID",
    [x.get("Text") for x in DL.partes("PRJ-1")] == ["nuevo", "viejo"],
    [x.get("Text") for x in DL.partes("PRJ-1")])
# ⚠️ Y que lo que se ESCRIBE tenga esa resolución: ordenar por segundos con un reloj que
# solo da minutos sería un arreglo que no arregla nada (la trampa nº30 otra vez).
h = _con()
DL.crear("PRJ-9", "cliente1", "con segundos", "juan")
chk("...y `Created` se escribe CON segundos",
    len(str(dict(zip(DL.HEADERS, h.filas[0])).get("Created", ""))) == 19,
    dict(zip(DL.HEADERS, h.filas[0])).get("Created") if h.filas else "(sin fila)")

# ⚠️ Se repone el juego de tres filas: los chequeos de abajo cuentan con él, y las
# sustituciones de arriba lo habían tirado. Un fixture pisado da rojos que no son.
h = _con([_fila("LOG-0001", "PRJ-1", HOY, "juan", "primero", HOY + " 09:00:00"),
          _fila("LOG-0002", "PRJ-1", HOY, "juan", "segundo", HOY + " 18:00:00"),
          _fila("LOG-0003", "PRJ-1", AYER, "ana", "de ayer", AYER + " 17:00:00")])
chk("filtra por autor", [x.get("ID") for x in DL.partes("PRJ-1", autor="ana")] == ["LOG-0003"])
chk("filtra por día", len(DL.partes("PRJ-1", dia=HOY)) == 2)
chk("otra obra no ve los de ésta", DL.partes("PRJ-2") == [])
chk("`ultimo` es el primero de la lista", DL.ultimo("PRJ-1").get("Text") == "segundo")
# ⚠️ Días CUBIERTOS, no entradas: es lo que mide el corpus. Dos partes del mismo día
# son un día, y contarlos como dos haría creer que hay más material del que hay.
chk("`dias_cubiertos` cuenta días, no partes", DL.dias_cubiertos("PRJ-1") == 2,
    DL.dias_cubiertos("PRJ-1"))
chk("`cuenta` sí cuenta partes", DL.cuenta("PRJ-1") == 3, DL.cuenta("PRJ-1"))

# ═════════════════════════════════════════════════════════════════
sec("8. La pantalla del campo llega a existir por su camino")
_pu = io.open("core/projects_ui.py", encoding="utf-8").read()
_apu = ast.parse(_pu)
# ⚠️ ESCAPE CAZADO POR LA BATERÍA: comprobar que el literal «📝 Parte» está EN EL FICHERO
# pasaba aunque se cayera de la lista de opciones, porque el mismo texto sigue en el
# `format_func` de al lado. Es la trampa nº2 (grep ≠ uso) y la nº30 a la vez: medía una
# forma que sobrevive al fallo. Se mira la LISTA `_opts`, que es lo que la pinta.
_opts_lit = []
for _n in ast.walk(_apu):
    if (isinstance(_n, ast.Assign)
            and any(getattr(t_, "id", "") == "_opts" for t_ in _n.targets)
            and isinstance(_n.value, ast.List)):
        _l = [e.value for e in _n.value.elts if isinstance(e, ast.Constant)]
        if "🏗 Avance" in _l:
            _opts_lit = _l
chk("el campo tiene su sección «Parte» en la LISTA de opciones",
    "📝 Parte" in _opts_lit, _opts_lit)
# ⚠️ Y que la rama exista: una opción sin su `elif` sale en el segmentado y no pinta nada.
_ramas = [ast.get_source_segment(_pu, n) or "" for n in ast.walk(_apu)
          if isinstance(n, ast.If)]
chk("...y su rama la atiende",
    any('_sec == "📝 Parte"' in r for r in _ramas))
_ren = [n for n in ast.walk(_apu)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "render_campo"]
chk("...y se llama a `render_campo`", len(_ren) == 1, len(_ren))
_adm = [n for n in ast.walk(_apu)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "render_admin"]
chk("el admin lo ve, en solo lectura", len(_adm) == 1, len(_adm))
# ⚠️ El admin NO puede escribir ni borrar: el parte es de quien lo escribió.
_aui = ast.parse(_ui)
_fn = next((n for n in ast.walk(_aui)
            if isinstance(n, ast.FunctionDef) and n.name == "render_admin"), None)
_escribe = any(isinstance(c, ast.Call)
               and getattr(c.func, "attr", "") in ("crear", "borrar")
               for c in ast.walk(_fn)) if _fn else True
chk("...y su vista no llama ni a `crear` ni a `borrar`", not _escribe)
# La lista del campo tampoco ofrece un botón que va a decir que no (v499).
_fc = next((n for n in ast.walk(_aui)
            if isinstance(n, ast.FunctionDef) and n.name == "render_campo"), None)
_seg = ast.get_source_segment(_ui, _fc) or ""
chk("la del campo solo ofrece borrar lo PROPIO y de HOY",
    'Author"' in _seg and "_hoy_txt" in _seg)

print("")
print("=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "HAY FALLOS" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
