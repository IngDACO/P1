# -*- coding: utf-8 -*-
"""v635 · COMENTARIOS EN LAS TAREAS DE LA LISTA DE PENDIENTES (02/11/2026, «Dale con todo incluido lo recomendado»).

Decisiones del usuario: comenta cualquiera que vea la lista, también en las hechas; borra su autor o la oficina, sin
editar; no avisan a nadie: el número se ve en la tarea. Solo texto, hasta 500 caracteres, y comentar no acredita nada.

Lo que protege, SIN la hoja real (dos hojas sustituidas en memoria; el módulo y la pantalla, REALES):
  (a) comentar: texto limpio con sus saltos de línea, ni vacío ni larguísimo, ID `TKC-####`, quién y cuándo; un doble
      toque no duplica; no se comenta una tarea borrada ni la de otra obra;
  (b) se lee como conversación, y cada obra ve solo lo suyo;
  (c) borrar OCULTA, con quién y cuándo; lo decide el módulo; con confirmación en pantalla;
  (d) al borrar la obra se van, y borrar una obra sin comentarios no crea la hoja;
  (e) la hoja va en el LOTE (lector sin cabeceras: fuera, vacía para siempre);
  (f) la pantalla: el número sin abrir nada, la caja se vacía o conserva lo escrito, y también en las hechas.
"""
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import chat_agent as CA, hojas as H, tareas as T        # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


FAKE = r'''
class HojaFalsa:
    def __init__(self, cab):
        self.cab, self.filas, self.escrituras = list(cab), [], 0
    def get_all_records(self, **k):
        return [dict(zip(self.cab, f + [""] * (len(self.cab) - len(f)))) for f in self.filas]
    def append_row(self, fila, value_input_option=None):
        if getattr(self, "falla", False):
            raise RuntimeError("sin red")
        assert value_input_option == "RAW" and len(fila) == len(self.cab), fila
        self.filas.append([str(x) for x in fila]); self.escrituras += 1
    def batch_update(self, lote, value_input_option=None):
        assert value_input_option == "RAW"
        import re
        for d in lote:
            col, fila = re.match(r"([A-Z]+)(\d+)$", d["range"]).groups()
            c = 0
            for ch in col:
                c = c * 26 + ord(ch) - 64
            self.filas[int(fila) - 2][c - 1] = str(d["values"][0][0])
        self.escrituras += 1
    def delete_rows(self, n):
        del self.filas[n - 2]; self.escrituras += 1
'''
exec(FAKE)


def tarea(tid, pid, autor="campo000", hecha="", activa=""):
    return [tid, "cliente1", pid, "Tarea " + tid, autor, "2026-10-28 09:00:00", hecha, "", "2026-10-29 10:00:00" if hecha else "", activa, "", ""]


# ═════════════════════════════════════════════════════════════════
sec("1. El módulo")
_w, _wc = HojaFalsa(T.HEADERS), HojaFalsa(T.HEADERS_COM)          # noqa: F821
_w.filas = [tarea("TSK-1", "PRJ-1"), tarea("TSK-2", "PRJ-1", activa="NO"), tarea("TSK-3", "PRJ-2"), tarea("TSK-4", "PRJ-1", hecha="YES")]
_o = (T._ws, T._ws_com, T._records, T._registros_com, T._invalidate, T._invalidate_com, H.siguiente_id_libre)
T._ws, T._ws_com = (lambda: _w), (lambda: _wc)
T._records, T._registros_com = (lambda: _w.get_all_records()), (lambda: _wc.get_all_records())
T._invalidate = T._invalidate_com = lambda: None
H.siguiente_id_libre = lambda pref, n, propia=None, ancho=4: "%s%04d" % (pref, n + 1)
try:
    ok1, c1 = T.comentar("TSK-1", "PRJ-1", "cliente1", "  Hola\r\n\r\n\r\n\r\nsegunda línea  ", "campo000")
    _f = _wc.filas[0] if _wc.filas else []
    chk("comentar: ID `TKC-0001`, obra, tarea y autor", ok1 and c1 == "TKC-0001" and _f[:4] == ["TKC-0001", "cliente1", "PRJ-1", "TSK-1"] and _f[5] == "campo000", _f)
    chk("...con el texto limpio y sus saltos de línea", _f[4] == "Hola\n\nsegunda línea", repr(_f[4:5]))
    chk("...y la hora", len(_f[6]) == 19, _f)
    chk("la fila entera, con lo de «borrado» vacío", _f[7:] == ["", "", ""], _f)
    chk("vacío, no", T.comentar("TSK-1", "PRJ-1", "g", "  \n ", "c")[0] is False)
    okl, ml = T.comentar("TSK-1", "PRJ-1", "g", "x" * (T.MAX_COMENTARIO + 1), "c")
    chk("larguísimo, no, y dice cuánto", okl is False and "501 of 500" in ml, ml)
    chk("el límite son 500 caracteres", T.MAX_COMENTARIO == 500 and T.comentar("TSK-1", "PRJ-1", "g", "x" * 500, "c")[0])
    _e = _wc.escrituras
    okd, cd = T.comentar("TSK-1", "PRJ-1", "g", "HOLA\n\n segunda   línea", "campo000")
    chk("⚠️ un doble toque no duplica: ya está, y dice que sí", okd and cd == "TKC-0001" and _wc.escrituras == _e, (okd, cd))
    chk("...pero el mismo texto de OTRA persona sí entra", T.comentar("TSK-1", "PRJ-1", "g", "Hola\n\nsegunda línea", "helper 1")[0] and _wc.escrituras == _e + 1)
    _e = _wc.escrituras
    okb, mb = T.comentar("TSK-2", "PRJ-1", "g", "tarde", "c")
    chk("⚠️ una tarea borrada no se comenta", okb is False and "no longer on the list" in mb and _wc.escrituras == _e, mb)
    chk("⚠️ ni la de OTRA obra", T.comentar("TSK-3", "PRJ-1", "g", "x", "c")[0] is False and _wc.escrituras == _e)
    chk("ni una que no existe", T.comentar("TSK-9", "PRJ-1", "g", "x", "c")[0] is False)
    chk("⚠️ en una tarea HECHA sí", T.comentar("TSK-4", "PRJ-1", "g", "ya está", "c")[0])
    chk("en la otra obra, también", T.comentar("TSK-3", "PRJ-2", "g", "de la otra", "c")[0])

    _c = T.comentarios("PRJ-1")
    chk("cada tarea con los suyos", sorted(_c) == ["TSK-1", "TSK-4"], sorted(_c))
    _wc.filas[0][6] = "2026-11-02 12:00:00"
    _wc.filas[1][6] = "2026-11-01 08:00:00"
    chk("se leen como conversación: el más ANTIGUO primero", [c["ID"] for c in T.comentarios("PRJ-1")["TSK-1"]][0] == "TKC-0002", [c["ID"] for c in T.comentarios("PRJ-1")["TSK-1"]])
    chk("⚠️ otra obra no ve nada de esta", list(T.comentarios("PRJ-2")) == ["TSK-3"])

    _e = _wc.escrituras
    okx, mx = T.borrar_comentario("TKC-0001", "PRJ-1", "helper 1", False)
    chk("⚠️ el de OTRO siendo del campo: no (lo decide el módulo)", okx is False and "Only the person" in mx and _wc.escrituras == _e, mx)
    oky, my = T.borrar_comentario("TKC-0001", "PRJ-1", "campo000", False)
    _f = _wc.filas[0]
    chk("el suyo sí: OCULTA, con quién y cuándo, y la fila sigue", oky and _f[7:9] == ["NO", "campo000"] and len(_f[9]) == 19 and len(_wc.filas) == 5, _f)
    chk("...y desaparece", "TKC-0001" not in [c["ID"] for c in T.comentarios("PRJ-1")["TSK-1"]])
    chk("uno ya borrado no se borra otra vez", T.borrar_comentario("TKC-0001", "PRJ-1", "campo000", False)[0] is False)
    chk("⚠️ el ID de otra obra no vale", T.borrar_comentario("TKC-0005", "PRJ-1", "Admin2", True)[0] is False, [(f[0], f[2]) for f in _wc.filas])
    chk("la oficina borra cualquiera", T.borrar_comentario("TKC-0002", "PRJ-1", "Admin2", True)[0])

    _n0 = len(_w.filas)
    chk("⚠️ borrar la OBRA se lleva sus tareas y sus comentarios, y solo los suyos",
        T.borrar_de_obra("PRJ-1") == 3 and {f[2] for f in _wc.filas} == {"PRJ-2"}, [(f[0], f[2]) for f in _wc.filas])
    _crea = []
    T._ws_com = lambda: _crea.append(1) or _wc
    T.borrar_de_obra("PRJ-77")
    chk("⚠️ una obra sin comentarios no abre la hoja: `_ws_com` la CREARÍA", _crea == [], _crea)
    T._ws_com = lambda: None
    chk("sin hoja: dice que no y no revienta",
        T.comentar("TSK-3", "PRJ-2", "g", "x", "u")[0] is False and T.borrar_comentario("TKC-1", "PRJ-2", "u", True)[0] is False)
finally:
    T._ws, T._ws_com, T._records, T._registros_com, T._invalidate, T._invalidate_com, H.siguiente_id_libre = _o


# ═════════════════════════════════════════════════════════════════
sec("2. Lo que lo rodea")
chk("⚠️ `TaskComments` va en el LOTE: su lector va sin cabeceras, y fuera leería vacío para siempre", T.SHEET_COM in H.HOJAS_LECTURA)
chk("la hoja es del libro del CLIENTE", T.SHEET_COM.lower() not in __import__("core.timeclock", fromlist=["x"]).SHEETS_GLOBALES)
_t = leer("core/tareas.py")
chk("el lector, sin cabeceras: no crea la hoja", "hojas.registros(SHEET_COM) or []" in _t)
_i = _t.index("def _ws_com")
chk("el ID va por el generador común, saltando los referenciados (v581)", 'hojas.siguiente_id_libre("TKC-", n, propia=SHEET_COM)' in _t)
_u = leer("core/tareas_ui.py")
chk("Enter no envía: es un salto de línea (v617)", 'border=False, enter_to_submit=False' in _u)
_g = re.sub(r"\s+", " ", CA.SYSTEM_PROMPT)
chk("la guía del asistente lo sabe", "Cada tarea tiene **Comments**: comenta cualquiera (también en las hechas), borra su autor o la oficina, y no se avisa a nadie" in _g)


# ═════════════════════════════════════════════════════════════════
sec("3. La pantalla (AppTest, con el módulo REAL y las hojas sustituidas)")
APP = FAKE + r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
st.session_state.setdefault("auth", {"usuario": ss.get("_u", "campo000"), "nombre": "X",
                                     "rol": ss.get("_rol", "field"), "grupo": "cliente1"})
from core import auth, flash, hojas, tareas as T, tareas_ui as TU
if "_hoja" not in ss:
    ss["_hoja"], ss["_hojac"] = HojaFalsa(T.HEADERS), HojaFalsa(T.HEADERS_COM)
    ss["_hoja"].filas = list(ss["_ini"])
T._ws = lambda: ss["_hoja"]
T._ws_com = lambda: ss["_hojac"]
T._records = lambda: ss["_hoja"].get_all_records()
T._registros_com = lambda: ss["_hojac"].get_all_records()
T._invalidate = T._invalidate_com = lambda: None
T.is_configured = lambda: True
hojas.siguiente_id_libre = lambda pref, n, propia=None, ancho=4: "%s%04d" % (pref, n + 1)
auth.list_users = lambda grupo=None: [{"User": "campo000", "Name": "Carlos Campo"},
                                      {"User": "helper 1", "Name": "Helena Uno"},
                                      {"User": "Admin2", "Name": "Bobo"}]
flash.mostrar()
TU.render("PRJ-9", "cliente1", ss["auth"]["usuario"], gestor=bool(ss.get("_gestor")),
          key_prefix=ss.get("_kp", "fld"))
'''


def _w_(lista, key):
    return next((x for x in lista if x.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


def pantalla(**kw):
    at = AppTest.from_string(APP, default_timeout=90)
    at.session_state["_ini"] = [tarea("TSK-1", "PRJ-9"), tarea("TSK-2", "PRJ-9", autor="helper 1"), tarea("TSK-3", "PRJ-9", hecha="YES")]
    for k, v in kw.items():
        at.session_state[k] = v
    return at.run()


def desplegables(at):
    """⚠️ Con `icon`, AppTest los da como `status` (verif_v615 mira las dos listas)."""
    return list(at.expander) + list(at.status)


def etiquetas(at):
    return [str(e.label) for e in desplegables(at)]


def manda(at, texto, gen=0, tid="TSK-1", kp="fld"):
    _w_(at.text_area, "%s_td_com_PRJ-9_%s_%d" % (kp, tid, gen)).input(texto)
    _w_(at.button, "%s_td_csend_PRJ-9_%s" % (kp, tid)).click()
    return at.run()


at = pantalla()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("cada tarea su desplegable, también las hechas", etiquetas(at).count("Add a comment") == 3, etiquetas(at))
chk("⚠️ cerrado: la lista sigue siendo corta", all(not e.proto.expanded for e in desplegables(at) if e.label == "Add a comment"))
manda(at, "Llave en *caja* $5\nsegunda línea")
_h = at.session_state["_hojac"]
chk("comentar desde la caja: una fila, del autor de la sesión", len(_h.filas) == 1 and _h.filas[0][3:6] == ["TSK-1", "Llave en *caja* $5\nsegunda línea", "campo000"], _h.filas)
chk("⚠️ el número se ve sin abrir nada", "Comments (1)" in etiquetas(at), etiquetas(at))
chk("⚠️ el texto, ESCAPADO y con sus saltos", r"Llave en \*caja\* \$5" + "  \nsegunda línea" in _todo(at), _todo(at)[:6])
chk("con quién, por su NOMBRE, y día y hora", any(re.match(r"Carlos Campo · \d\d/\d\d/\d{4} \d\d:\d\d$", str(x)) for x in _todo(at)), _todo(at))
_cja = _w_(at.text_area, "fld_td_com_PRJ-9_TSK-1_1")
chk("la caja nace VACÍA", _cja is not None and _cja.value in ("", None), _cja and _cja.value)
chk("sin mensaje: el comentario aparece delante de quien lo escribió", not at.success, [s.value for s in at.success])
at.session_state["_hojac"].falla = True
manda(at, "Se cayó la red", gen=1)
at.session_state["_hojac"].falla = False
chk("⚠️ si falla lo dice, y lo escrito SE QUEDA", len(at.error) > 0 and _w_(at.text_area, "fld_td_com_PRJ-9_TSK-1_1").value == "Se cayó la red", [e.value for e in at.error])
chk("...y no se escribe nada", len(at.session_state["_hojac"].filas) == 1)
manda(at, "Hecha, pero faltó la tapa", tid="TSK-3")
chk("⚠️ en una tarea hecha también", etiquetas(at).count("Comments (1)") == 2 and at.session_state["_hojac"].filas[-1][3] == "TSK-3", etiquetas(at))

_del = "fld_td_cdel_PRJ-9_TKC-0001"
chk("su autor puede borrarlo", _w_(at.button, _del) is not None)
at.session_state["_hojac"].filas.append(["TKC-0009", "cliente1", "PRJ-9", "TSK-1", "De Helena", "helper 1", "2026-11-02 10:00:00", "", "", ""])
at.run()
chk("el número sube", "Comments (2)" in etiquetas(at), etiquetas(at))
chk("⚠️ el de otra persona no se le ofrece al campo", _w_(at.button, "fld_td_cdel_PRJ-9_TKC-0009") is None)
_w_(at.button, _del).click()
at.run()
chk("⚠️ borrar pregunta, y aún no borra", any("Delete this comment?" in str(w.value) for w in at.warning) and at.session_state["_hojac"].filas[0][7] == "", [w.value for w in at.warning])
_w_(at.button, "fld_td_cdelno_PRJ-9_TKC-0001").click()
at.run()
chk("«Keep it» no borra, y vuelve", at.session_state["_hojac"].filas[0][7] == "" and _w_(at.button, _del) is not None)
_w_(at.button, _del).click()
at.run()
_w_(at.button, "fld_td_cdelok_PRJ-9_TKC-0001").click()
at.run()
chk("«Yes, delete it» oculta, con quién", at.session_state["_hojac"].filas[0][7:9] == ["NO", "campo000"], at.session_state["_hojac"].filas[0])
chk("lo dice, y el número baja", any("Comment deleted." in str(s.value) for s in at.success) and "Comments (1)" in etiquetas(at), etiquetas(at))

at = pantalla(_u="Admin2", _rol="administrator", _gestor=True, _kp="adm")
manda(at, "Encargo de la oficina", kp="adm")
at.session_state["_hojac"].filas.append(["TKC-0009", "cliente1", "PRJ-9", "TSK-1", "De Helena", "helper 1", "2026-11-02 10:00:00", "", "", ""])
at.run()
chk("⚠️ la oficina comenta y borra el de cualquiera", _w_(at.button, "adm_td_cdel_PRJ-9_TKC-0009") is not None and at.session_state["_hojac"].filas[0][5] == "Admin2", at.session_state["_hojac"].filas)

at = pantalla()
manda(at, "   ")
chk("vacío: lo dice y no escribe", any("Write the comment first" in str(e.value) for e in at.error) and not at.session_state["_hojac"].filas, [e.value for e in at.error])
at.session_state["_hojac"].filas.append(["TKC-0009", "cliente1", "PRJ-8", "TSK-1", "De otra obra", "helper 1", "2026-11-02 10:00:00", "", "", ""])
at.run()
chk("⚠️ el comentario de otra obra no se cuela", "Comments (1)" not in etiquetas(at) and not any("De otra obra" in str(x) for x in _todo(at)), etiquetas(at))
at.session_state["_hojac"].filas.append(["TKC-0010", "cliente1", "PRJ-9", "TSK-2", "Sigue", "helper 1", "2026-11-02 10:00:00", "", "", ""])
at.session_state["_hoja"].filas[1][9] = "NO"
at.run()
chk("⚠️ borrar la tarea se lleva sus comentarios de la vista", not any("Sigue" in str(x) for x in _todo(at)), _todo(at)[:5])
chk("...y no se escribió nada para ello", at.session_state["_hojac"].filas[-1][7] == "")

print("\n=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
for x in fallos:
    print("  FALLO: %s" % x)
sys.exit(1 if fallos else 0)
