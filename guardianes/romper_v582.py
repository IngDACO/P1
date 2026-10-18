# -*- coding: utf-8 -*-
"""Bateria de roturas de v582 (Finance → Catalogue, probada acción por acción). ⚠️ Verde de
BASE primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v582"
CM = "core/catalogo.py"
CU = "core/catalogo_ui.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ los fantasmas vuelven a verse (la regla del tema)", "core/theme.py",
     [('[data-testid="stApp"][data-test-script-state="notRunning"] [data-stale="true"] {{\n',
       '[data-roto] {{\n')]),
    ("…o la carcasa del desplegable fantasma", "core/theme.py",
     [(':has([data-stale="true"]):not(:has([data-stale="false"])) {{\n', ' {{\n')]),
    ("⚠️ la edición vuelve a aceptar costo 0", CM,
     [('    if any(k in escritos for k in ("Name", "Type", "UnitCost", "EstHours", "HourlyRate")):\n',
       "    if False:\n")]),
    ("…o el alta deja de validar", CM,
     [("    _err = _valida(tipo, nombre, costo_unit, horas_est, tarifa_hora)\n    if _err:\n"
       "        return False, _err\n", "")]),
    ("⚠️ un servicio vuelve a nacer con la unidad que le llegue («hora»)", CM,
     [('    if tipo == SERVICIO:\n        unidad = ""\n', "")]),
    ("desactivar/reactivar vuelven a decir «Item updated.»", CM,
     [('        msg = t("Item reactivated.") if activo else t("Item deactivated.")\n', "        pass\n")]),
    ("la categoría por defecto vuelve a «Engineering»", CM,
     [('    return "Installation" if tipo == SERVICIO else "Materials"\n', '    return "Engineering"\n')]),
    ("⚠️ un nombre repetido ya no avisa", CU,
     [("                if _dups and not st.session_state.get(_k_dup(nombre)):\n",
       "                if False:\n")]),
    ("⚠️ el formulario vuelve a quedarse lleno tras crear", CU,
     [('                    st.session_state["_cat_new_gen"] = _g + 1\n', "")]),
    ("el aviso de alta vuelve a decir el ID", CU,
     [('                    flash.exito(t("Item «{n}» created.", n=str(nombre).strip()))\n',
       '                    flash.exito(f"Item {msg} created.")\n')]),
    ("⚠️ la regla de cantidad no llega al motor", CU,
     [("                                    creado_por=_creado_por(), qty_rule=regla)\n",
       "                                    creado_por=_creado_por())\n")]),
    ("⚠️ la tabla vuelve a `single-row` (tocar la celda solo la enmarca)", CU,
     [('                               on_select="rerun", selection_mode="single-cell",\n',
       '                               on_select="rerun", selection_mode="single-row",\n')]),
    ("el nombre deja de ir fijado", CU,
     [('                                   "Item": st.column_config.TextColumn(t("Item"), pinned=True),\n',
       '                                   "Item": st.column_config.TextColumn(t("Item")),\n')]),
    ("«Active» vuelve a salir siempre", CU,
     [('            if not _ver_inact:\n                df = df.drop(columns=["Activo"])\n', "")]),
    ("⚠️ las cifras dejan de filtrar", CU,
     [('                st.session_state["_cat_tipo_pending"] = _fl\n', "")]),
    ("el filtro deja de recordarse", CU,
     [('                      horizontal=True, key="cpxseg_cat_tipo", label_visibility="collapsed",\n'
       '                      persist_state="session")\n',
       '                      horizontal=True, key="cpxseg_cat_tipo", label_visibility="collapsed")\n')]),
    ("⚠️ una búsqueda vacía vuelve a decir «No items yet»", CU,
     [('        elif r["n"] + r["inactivos"] == 0:\n', "        elif True:\n")]),
    ("vuelve «item(s)»", CU,
     [('            st.caption(t("1 item") if len(items) == 1 else t("{n} items", n=len(items)))\n',
       '            st.caption(f"{len(items)} item(s)")\n')]),
    ("⚠️ el servicio vuelve a enseñar su «hora»", CU,
     [('    if str(i.get("Type", "")) == CAT.SERVICIO:\n        return "—"\n', "")]),
    ("«product / service» vuelve a la minúscula", CU,
     [('_TIPO_TXT = {CAT.PRODUCTO: "Product", CAT.SERVICIO: "Service"}\n',
       '_TIPO_TXT = {CAT.PRODUCTO: "product", CAT.SERVICIO: "service"}\n')]),
    ("el PDF vuelve a pintar la unidad del servicio", "core/quote_pdf.py",
     [('        if str(l.get("tipo", "")) == "service":\n            uni = ""\n', "")]),
    ("⚠️ «Catalogue» en el menú deja de cerrar el artículo", "core/home_ui.py",
     [('                   ("finanzas", "📚 Catálogo"): "_cat_open"}\n', "                   }\n")]),
    ("⚠️ el detalle deja de decir dónde se usa", CU,
     [("    _usos(grupo, cid)\n", "")]),
    ("…o el botón de la cotización no la abre", CU,
     [('            st.session_state["_cot_open"] = str(c.get("ID", ""))\n', "")]),
    ("…o se busca por subcadena (CAT-1 casaría con CAT-11)", "core/quotes.py",
     [('        if any(str(l.get("catalogo_id", "")) == str(item_id) for l in lineas_de(c)):\n',
       '        if any(str(item_id) in str(l.get("catalogo_id", "")) for l in lineas_de(c)):\n')]),
    ("⚠️ el tipo editado no se guarda", CU,
     [('                           "Type": tipo, "QtyRule": regla})\n', '                           "QtyRule": regla})\n')]),
    ("de servicio a producto, la unidad se queda con la «hora»", CU,
     [("            if _t0 != CAT.PRODUCTO:\n", "            if False:\n")]),
    ("⚠️ vuelve el aviso falso del desactivado", CU,
     [('it is not offered when quoting. Reactivate it to quote it again."))',
       'it does not appear when quoting unless you tick «Show deactivated ones too»."))')]),
    ("⚠️ el aviso de la cotización ya no lleva al catálogo", "core/quotes_ui.py",
     [('                _PU._ir_a("finanzas", "📚 Catálogo")\n', "                pass\n")]),
    ("la condición del alta abierta sale de la clave", CU,
     [('key=f"exp_cat_new_{vacio}",', 'key="exp_cat_new",')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CU,
           [("def _alta(grupo, vacio=False):\n", "def _alta(grupo, vacio=False):   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
