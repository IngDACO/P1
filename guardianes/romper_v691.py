# -*- coding: utf-8 -*-
"""Batería de roturas de v691. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v691"
TOPE_S = 400
IN = "core/inventory.py"
IU = "core/inventory_ui.py"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
CB = "core/contable.py"
QU = "core/quotes_ui.py"
APP = "app.py"

ROTURAS = [
    ("⚠️ la baja sin motivo otra vez", IN,
     [('    if not str(motivo or "").strip():\n        return False, t("Give the reason for the write-off.")\n', "")]),
    ("⚠️ la baja no suelta al responsable", IN,
     [('{"Active": "NO", "Status": BAJA, "AssignedTo": "", "ReturnDate": ""}', '{"Active": "NO", "Status": BAJA}')]),
    ("la baja no guarda quién lo tenía", IN,
     [('                 str(a.get("AssignedTo", "") or ""), "", motivo, creado_por=creado_por)',
       '                 "", "", motivo, creado_por=creado_por)')]),
    ("⚠️ reactivar no lo devuelve al almacén", IN,
     [('{"Active": "SI", "Status": DISPONIBLE, "LocationType": "warehouse",\n'
       '                                  "LocationRef": _bod, "AssignedTo": "", "ReturnDate": ""}',
       '{"Active": "SI", "Status": DISPONIBLE}')]),
    ("la ubicación de una persona vuelve a la cuenta", IN,
     [('    if nombres and _tp0 == "user" and ref:\n        ref = nombres.get(ref, ref)\n', "")]),
    ("el historial vuelve a la cuenta", IN,
     [('    if nombres and _pre.strip() == "user":\n        _resto = nombres.get(_resto.strip(), _resto)\n', "")]),
    ("⚠️ quitar una categoría en uso sin pedir destino", IN,
     [("    if _uso:\n        if not mover_a or", "    if False:\n        if not mover_a or")]),
    ("un aviso dado por visto sigue pendiente", IN,
     [('            if str(m.get("ID", "")) in _vistos:\n                continue\n', "")]),
    ("⚠️ un aviso cerrado por un movimiento sigue pendiente", IN,
     [('            if any(str(x.get("Type", "")) in CIERRAN.get(_k, ()) for x in movs[i + 1:]):\n                continue\n',
       "")]),
    ("un traslado cierra un aviso de problema", IN,
     [('    "problem": ("maintenance", "written off")}', '    "problem": ("maintenance", "written off", "transfer")}')]),
    ("el campo repite un aviso pendiente", IN,
     [('    if any(x["usuario"] == str(usuario) and x["tipo"] == tipo for x in avisos_pendientes(grupo, aid)):',
       "    if False:")]),
    ("⚠️ el campo avisa de un equipo de OTRA empresa", IN,
     [('    if not a or str(a.get("Group", "")) != str(grupo):\n        return False, t("Asset not found.")\n'
       '    if tipo == "problem"', '    if not a:\n        return False, t("Asset not found.")\n    if tipo == "problem"')]),
    ("confirmar «lo tengo» saca de la obra lo que está en ella", IN,
     [('    if str(a.get("LocationType", "")) == "user":\n        _c.update({"LocationRef": usuario})',
       '    if True:\n        _c.update({"LocationRef": usuario})')]),
    ("⚠️ la razón social vuelve a preguntarle a `identidad`", CB,
     [('    return bool(str(auth.group_text_setting(grupo, "LegalName", "") or "").strip())',
       '    return bool(identidad(grupo).get("legal"))')]),
    ("el aviso del emisor de la cotización vuelve a `identidad()['legal']`", QU,
     [("        if not _CB.tiene_razon_social(grupo):", '        if not str(_CB.identidad(grupo).get("legal") or "").strip():')]),
    ("⚠️ la vuelta sin responsable no se ve", IU,
     [('        if _fdv and str(a.get("Status", "")) == "in use":', "        if False:")]),
    ("la salida a una obra vuelve a nacer con una obra", IU,
     [("                                            format_func=lambda i: _plbl.get(i, i), index=None,",
       "                                            format_func=lambda i: _plbl.get(i, i),")]),
    ("la salida a una persona vuelve a nacer con una persona", IU,
     [("                                            format_func=lambda u: _nom.get(u, u), index=None,",
       "                                            format_func=lambda u: _nom.get(u, u),")]),
    ("a una obra sin responsable no avisa", IU,
     [('                if _dt == "project" and _resp == "—":', "                if False:")]),
    ("⚠️ la baja de algo prestado no avisa", IU,
     [('            if _est == "in use" or str(a.get("AssignedTo", "")).strip():\n                _q = _nom.get(',
       "            if False:\n                _q = _nom.get(")]),
    ("⚠️ «Write off» sin motivo elegido", IU,
     [("disabled=not (_conf and _mk)):", "disabled=not _conf):")]),
    ("reactivar no usa el almacén elegido", IU,
     [("            ok, msg = INV.reactivar(aid, grupo, _cp, bodega=_bod_r)", "            ok, msg = INV.reactivar(aid, grupo, _cp)")]),
    ("⚠️ la ficha no enseña lo que dijo el campo", IU,
     [("    _avisos_del_campo(grupo, aid, _nom, _cp)          # v691", "    pass          # v691")]),
    ("«Confirm: it is with them» no hace nada", IU,
     [('                    ok, msg = INV.pasar_a(aid, grupo, x["usuario"], _cp)', '                    ok, msg = True, "ok"')]),
    ("el alta vuelve a preseleccionar la categoría", IU,
     [('key=f"inv_reg_cat_{_g}", index=None, placeholder=t("— choose the category —"))', 'key=f"inv_reg_cat_{_g}")')]),
    ("el alta sin categoría se crea", IU,
     [('        if not categoria:                            # v691 · H8\n            st.error(t("Choose the category."))\n'
       "            return\n", "")]),
    ("quitar una categoría no mira si está en uso", IU,
     [("            _uso = INV.en_uso_categoria(grupo, _quitar)", "            _uso = []")]),
    ("la etiqueta sin razón social no avisa", IU,
     [("                if not _CB.tiene_razon_social(grupo):\n", "                if False:\n")]),
    ("⚠️ el campo ve un equipo de OTRA empresa", IU,
     [('    if not a or str(a.get("Group", "")) != str(grupo):\n        st.warning(t("Asset not found."))',
       '    if not a:\n        st.warning(t("Asset not found."))')]),
    ("«I have it» sale también en lo suyo", IU,
     [('    if not _mio and "has it" not in _esp:', '    if "has it" not in _esp:')]),
    ("buscar por ID no acepta minúsculas", IU,
     [('            _a = INV.get_activo(str(_id or "").strip().upper())', '            _a = INV.get_activo(str(_id or "").strip())')]),
    ("⚠️ el campo no recibe el aviso de la vuelta", HU,
     [("            for a in INV.de_la_persona(grupo, _u0):", "            for a in []:")]),
    ("el campo recibe el aviso aunque falte un mes", HU,
     [("                if _fd is None or _dd > 2:", "                if _fd is None:")]),
    ("⚠️ la oficina no ve en la campana lo que dijo el campo", HU,
     [("            for x in INV.avisos_pendientes(grupo)[:8]:", "            for x in []:")]),
    ("el no devuelto vuelve a la cuenta", HU,
     [("""+ (f" ({_nm.get(e['usuario'], e['usuario'])})" if e.get("usuario") else ""))""",
       """+ (f" ({e['usuario']})" if e.get("usuario") else ""))""")]),
    ("la alerta del campo no abre su equipo", HU,
     [('    elif destino[0] == "equipo":                  # v691', '    elif destino[0] == "equipo_x":                  # v691')]),
    ("Self-service no enruta «My equipment»", HU,
     [('            elif _sub == "🧰 Equipo":                # v691 · D3', '            elif _sub == "🧰 Equipo_x":                # v691 · D3')]),
    ("⚠️ la obra (oficina) no dice qué equipos tiene", PU,
     [("        _equipos_en_obra(pid, grupo)                 # v691", "        pass                 # v691")]),
    ("«My projects» no dice qué equipos hay en la obra", PU,
     [("    _equipos_en_obra_campo(prj, grupo, usuario)      # v691", "    pass      # v691")]),
    ("⚠️ el QR del campo no hace nada otra vez", APP,
     [('(antes, escanear la etiqueta no hacía nada).\nif _ROL in ("administrator", "field"):',
       '(antes, escanear la etiqueta no hacía nada).\nif _ROL == "administrator":')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", IN,
           [('    """Los equipos que están en una obra (v691, ciclo 5 H12)."""',
             '    """Los equipos que están en una obra (v691, ciclo 5 H12 · control)."""')])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
