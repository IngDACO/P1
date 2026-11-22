# -*- coding: utf-8 -*-
"""Batería de roturas de v692. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v692"
TOPE_S = 400
CA = "core/chat_agent.py"
CT = "core/chat_tools.py"

ROTURAS = [
    ("⚠️ el recordatorio del idioma vuelve a ir solo tras las herramientas", CA,
     [('    if herramientas:\n        _rec = {"type": "text", "text": _idioma_tras_datos(user_message, rol)}',
       '    if False:\n        _rec = {"type": "text", "text": _idioma_tras_datos(user_message, rol)}')]),
    ("con una foto, el recordatorio se come la imagen", CA,
     [("        messages[-1] = {\"role\": \"user\", \"content\": (list(_c) if isinstance(_c, list)\n"
       "                                                    else [{\"type\": \"text\", \"text\": _c}]) + [_rec]}",
       "        messages[-1] = {\"role\": \"user\", \"content\": [{\"type\": \"text\", \"text\": str(_c)}] + [_rec]}")]),
    ("⚠️ la oficina sin get_quotes", CT,
     [('    {"name": "get_quotes", "fn": _cotizaciones,', '    {"name": "get_quotes_x", "fn": _cotizaciones,')]),
    ("⚠️ la oficina sin get_assets", CT,
     [('    {"name": "get_assets", "fn": _activos,', '    {"name": "get_assets_x", "fn": _activos,')]),
    ("⚠️ el campo sin get_my_equipment", CT,
     [('    {"name": "get_my_equipment", "input_schema": _SIN_ENTRADA, "fn": _mi_equipo,',
       '    {"name": "get_my_equipment_x", "input_schema": _SIN_ENTRADA, "fn": _mi_equipo,')]),
    ("⚠️ get_quotes cuenta versiones, no tratos", CT,
     [("    tratos = [_trato_txt(Q.representante(vs), vs, hoy) for vs in Q._por_trato(cs).values()]",
       "    tratos = [_trato_txt(c, [c], hoy) for c in cs]")]),
    ("una enviada no dice cuántos días le quedan", CT,
     [('    if e == Q.ENVIADA and _v:\n        d["days_left"] = (_v - hoy).days\n', "")]),
    ("una perdida no dice por qué", CT,
     [('        d["reject_reason"] = (_k or "not recorded") + (f" ({_corto(_n)})" if _n else "")',
       '        d["reject_reason"] = ""')]),
    ("el filtro por cliente no filtra", CT,
     [('    if _cli:\n        cs = [c for c in cs if _cli in str(c.get("ClientName", "")).lower()]',
       '    if False:\n        cs = [c for c in cs if _cli in str(c.get("ClientName", "")).lower()]')]),
    ("⚠️ el inventario vuelve a la cuenta en «where»", CT,
     [('"where": INV.ubic_str(a, None, nom),', '"where": INV.ubic_str(a),')]),
    ("…y en «with»", CT,
     [('"with": nom.get(_asg, _asg) if _asg else "nobody"}', '"with": _asg or "nobody"}')]),
    ("⚠️ un equipo en una obra sin el ID de la obra (lo del examen)", CT,
     [('        d["project_id"] = str(a.get("LocationRef", "") or "")', "        pass")]),
    ("lo atrasado no dice cuántos días", CT,
     [('        if dd < 0:\n            d["days_late"] = -dd', '        if False:\n            d["days_late"] = -dd')]),
    ("el filtro por persona no filtra", CT,
     [("    if _p:\n        _logins", "    if False:\n        _logins")]),
    ("⚠️ no ve lo que dijo el campo", CT,
     [('            for x in INV.avisos_pendientes(g) if not _q or x["aid"].lower() == _q or _q in x["activo"].lower()]',
       "            for x in []]")]),
    ("⚠️ el campo ve el equipo de TODOS", CT,
     [('    return {"signed_out_to_you": [_equipo_txt(a, nom, hoy) for a in INV.de_la_persona(g, u)][:MAX_LISTA],',
       '    return {"signed_out_to_you": [_equipo_txt(a, nom, hoy) for a in INV.list_activos(g)][:MAX_LISTA],')]),
    ("⚠️ la bandeja (y el resumen del día) sin ventas ni equipo", CT,
     [("        **_pendiente_ventas_y_equipo(g)}", "        }")]),
    ("la guía de la oficina no dice que ve cotizaciones e inventario", CA,
     [('"tiene pendiente de decidir, el dinero, las cotizaciones, el inventario (los equipos: dónde están, con quién y "',
       '"tiene pendiente de decidir, el dinero, (los equipos: dónde están, con quién y "')]),
    ("la del campo, su equipo", CA,
     [('"ausencias, sus credenciales y el equipo de la empresa que tiene a su cargo. Ya sabes quién es: no se lo "',
       '"ausencias y sus credenciales. Ya sabes quién es: no se lo "')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CT,
           [('    """Lo de cotizaciones e inventario que espera a la oficina (v692): para la bandeja y el resumen del día."""',
             '    """Lo de cotizaciones e inventario que espera a la oficina (v692): para la bandeja y el resumen del día. (control)"""')])


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
