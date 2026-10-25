# -*- coding: utf-8 -*-
"""Bateria de roturas de v600 (lo visto verificando v599: fantasmas durante las pasadas, el 2º
toque, «bodega»/«baja», el estado de un activo de baja, filtros recordados, todo activo).
⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales
(v570). `--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v600"
TH = "core/theme.py"
AP = "app.py"
IN = "core/inventory.py"
IU = "core/inventory_ui.py"
MG = "../guardianes/sueltos/migrar_v600_movimientos.py"
TOPE_S = 900

ROTURAS = [
    # ── los fantasmas ──
    ("⚠️ lo marcado vuelve a VERSE durante las pasadas (sin su regla)", TH,
     [('[data-copex-fantasma][data-stale="true"] {{\n', '[data-copex-fantasma-no][data-stale="true"] {{\n')]),
    ("⚠️ la regla oculta lo marcado aunque VUELVA a la vida", TH,
     [('[data-copex-fantasma][data-stale="true"] {{\n', '[data-copex-fantasma] {{\n')]),
    ("el bloque marcado se oculta aunque tenga algo vivo", TH,
     [('[data-testid="stLayoutWrapper"][data-copex-fantasma]:not(:has([data-stale="false"])) {{\n',
       '[data-testid="stLayoutWrapper"][data-copex-fantasma] {{\n')]),
    ("⚠️ el marcador marca DURANTE la pasada (ocultaría lo viejo legítimo)", TH,
     [(" if(!a||a.getAttribute('data-test-script-state')!=='notRunning')return;\n", " if(!a)return;\n")]),
    ("⚠️ …o sube a bloques con algo vivo dentro", TH,
     [("  while(w&&!w.querySelector('[data-stale=\"false\"]')){", "  while(w){")]),
    ("el marcador deja de escuchar el estado de la pasada", TH,
     [("o.observe(a,{attributes:true,attributeFilter:['data-test-script-state']});", "")]),
    ("se instala desde el recuadro (sin el <script> en la página)", TH,
     [("\"try{var s=D.createElement('script');s.textContent=c;D.head.appendChild(s);}catch(e){}\"", '""')]),
    ("⚠️ app.py deja de traer el marcador", AP,
     [("incrustar.script(_cpx_theme.script_fantasmas() + \"\"\"\n", 'incrustar.script("""\n')]),
    ("⚠️ …o lo trae en un recuadro NUEVO (cambia las posiciones de todo lo de debajo)", AP,
     [("incrustar.script(_cpx_theme.script_fantasmas() + \"\"\"\n",
       "incrustar.script(_cpx_theme.script_fantasmas())\nincrustar.script(\"\"\"\n")]),
    # ── el motor ──
    ("⚠️ un activo de baja vuelve a poder pasar a «available» editándolo", IN,
     [("        if (_est == BAJA) != (_act in (\"NO\", \"FALSE\", \"0\")):\n", "        if False:\n")]),
    ("⚠️ la baja vuelve a escribir «baja»", IN,
     [('        _log_mov(grupo or str(a.get("Group", "")), aid, "written off", ubic_str(a), BAJA,\n',
       '        _log_mov(grupo or str(a.get("Group", "")), aid, "written off", ubic_str(a), "baja",\n')]),
    ("…la reactivación también", IN,
     [('        _log_mov(grupo or str(a.get("Group", "")), aid, "reactivated", BAJA, ubic_str(a),\n',
       '        _log_mov(grupo or str(a.get("Group", "")), aid, "reactivated", "baja", ubic_str(a),\n')]),
    ("⚠️ la devolución vuelve a escribir «bodega: …»", IN,
     [('(f"warehouse: {bodega}" if bodega else "warehouse")', '(f"bodega: {bodega}" if bodega else "bodega")')]),
    ("⚠️ un 2º toque de salida vuelve a valer", IN,
     [('    if str(a.get("Status", "")) != DISPONIBLE:\n', "    if False:\n")]),
    ("…de devolución", IN,
     [('    if str(a.get("Status", "")) in (DISPONIBLE, BAJA):\n', "    if False:\n")]),
    ("…de baja", IN,
     [('    if str(a.get("Status", "")) == BAJA:\n        return False, t("This asset is already written off.")',
       '    if False:\n        return False, t("This asset is already written off.")')]),
    ("…de reactivar", IN,
     [('    if str(a.get("Status", "")) != BAJA:\n        return False, t("This asset is not written off.")',
       '    if False:\n        return False, t("This asset is not written off.")')]),
    ("⚠️ trasladar a donde ya está vuelve a valer", IN,
     [('    if (str(hacia_tipo) == str(a.get("LocationType", ""))\n', "    if False and (str(hacia_tipo) == str(a.get(\"LocationType\", \"\"))\n")]),
    ("⚠️ un servicio sin nada que anotar vuelve a valer", IN,
     [("    if not servicio_con_datos(a, costo, proximo, nota, en_mant):\n", "    if False:\n")]),
    ("…y la MISMA fecha vuelve a contar como dato", IN,
     [('    _nueva_fecha = bool(_p) and _p != str(a.get("NextService", "") or "").strip()[:10]\n',
       "    _nueva_fecha = bool(_p)\n")]),
    # ── la ficha ──
    ("⚠️ los paneles vuelven a quedarse con lo tecleado (sin otra generación)", IU,
     [('            st.session_state[f"_inv_acc_gen_{aid}"] = _ag + 1\n', "            pass\n")]),
    ("⚠️ el traslado vuelve a nacer en «warehouse» vacío", IU,
     [("                               index=_indice_de(INV.UBIC_TIPOS, _t0),\n",
       "                               index=0,\n")]),
    ("…o deja de desactivarse a donde ya está", IU,
     [('                         disabled=(_tt in ("project", "user") and not _tr) or _ya):\n',
       '                         disabled=(_tt in ("project", "user") and not _tr)):\n')]),
    ("⚠️ «Record service» deja de desactivarse sin nada que anotar", IU,
     [("                         disabled=not INV.servicio_con_datos(a, _costo, _prox, _n, _enm)):\n",
       "                         disabled=False):\n")]),
    ("⚠️ el estado de un activo de baja o prestado vuelve a editarse", IU,
     [("        if _st0 in (INV.EN_USO, INV.BAJA):\n", "        if False:\n")]),
    # ── la lista ──
    ("⚠️ la búsqueda vuelve a olvidarse al abrir una ficha", IU,
     [('    q = st.text_input(t(":material/search: Search"), key="inv_q", persist_state="session",\n',
       '    q = st.text_input(t(":material/search: Search"), key="inv_q",\n')]),
    ("el filtro de ubicación no filtra", IU,
     [('        _rows = [a for a in _rows if str(a.get("LocationType", "")) == ubic_f]\n', "        pass\n")]),
    ("⚠️ «nada coincide» se queda sin salida", IU,
     [('            st.button(t(":material/filter_alt_off: Show all"), key="inv_ver_todo", on_click=_filtrar)\n', "")]),
    ("«N written-off assets hidden» vuelve a ser mudo", IU,
     [('                  key="inv_ver_bajas_btn", type="tertiary", on_click=_ver_bajas)\n',
       '                  key="inv_ver_bajas_btn", type="tertiary")\n')]),
    ("⚠️ una fila de los informes deja de filtrar", IU,
     [('        _filtrar(categoria=_v if _v != "—" else "Todas")\n', "        pass\n")]),
    ("…o una de ubicación", IU,
     [('        _filtrar(ubicacion=_v if _v in INV.UBIC_TIPOS else "Todas")\n', "        pass\n")]),
    ("⚠️ los nombres de categoría dejan de filtrar", IU,
     [("        _filtrar(categoria=_v)\n", "        pass\n")]),
    ("los filtros vuelven a [2, 1, 1] («Service ov…»)", IU,
     [("    f2, f3, f4 = st.columns(3)\n", "    f2, f3, f4 = st.columns([2, 1, 1])\n")]),
    # ── la migración ──
    ("⚠️ la migración deja «baja» sin traducir", MG,
     [('        return "written off"\n', "        return None\n")]),
    ("…o toca lo que no empieza por «bodega»", MG,
     [('    if pre.strip().lower() == "bodega":\n', '    if "bodega" in s.lower() or "baja" in s.lower():\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", IU,
           [("def _ver_bajas():\n", "def _ver_bajas():  # comentario inocuo\n")])


def corre() -> bool:
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ, env=ENV,
                           capture_output=True, text=True, encoding="utf-8", timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return False
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d" % txt.count(viejo)
        txt = txt.replace(viejo, nuevo)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))),
                          encoding="utf-8", newline="").read()
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
