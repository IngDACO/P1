# -*- coding: utf-8 -*-
"""Batería de roturas de v689. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v689"
TOPE_S = 400
QM = "core/quotes.py"
QU = "core/quotes_ui.py"
HU = "core/home_ui.py"

ROTURAS = [
    ("⚠️ las cifras vuelven a contar cada VERSIÓN", QM,
     [("    for _vs in _por_trato(cs).values():\n        rep = representante(_vs)\n        e = estado_de(rep)\n"
       "        por_estado[e] = por_estado.get(e, 0) + 1\n",
       "    for rep in cs:\n        e = estado_de(rep)\n        por_estado[e] = por_estado.get(e, 0) + 1\n")]),
    ("⚠️ las versiones viejas no se dicen «superseded»", QM,
     [('                out[str(c.get("ID", ""))] = SUSTITUIDA\n', '                out[str(c.get("ID", ""))] = e\n')]),
    ("la versión vigente no prefiere la aceptada", QM,
     [("    if _ac:\n        return max(_ac, key=_ver)\n", "")]),
    ("⚠️ aceptar una versión de un trato con obra ya no es una variación", QM,
     [("            return aceptar_variacion(cid)\n", "            pass\n")]),
    ("⚠️ la variación no pone el costo cotizado de presupuesto", QM,
     [('    _ok_p, _msg_p = P.update_project(pid, {"Budget": str(_tot["costo"])})',
       '    _ok_p, _msg_p = True, ""')]),
    ("⚠️ se puede crear una SEGUNDA obra para el mismo trato", QM,
     [("    if _pid_t:\n        return False, t(\"This job already exists", "    if False:\n        return False, t(\"This job already exists")]),
    ("la obra vale la PRIMERA versión aceptada, no la más alta", QM,
     [("    return max(_acs, key=_ver) if _acs else {}", "    return _acs[0] if _acs else {}")]),
    ("⚠️ el rechazo no guarda su motivo", QM,
     [('        _campos["RejectReason"] = (str(motivo or "") + (f" — {_n}" if _n else "")).strip()\n', "")]),
    ("volver a «sent» no borra el motivo", QM,
     [('    elif str(c.get("RejectReason", "") or "").strip():\n        _campos["RejectReason"] = ""\n', "")]),
    ("un motivo inventado se acepta", QM,
     [("    if estado == RECHAZADA and motivo and motivo not in MOTIVOS_RECHAZO:", "    if False:")]),
    ("el seguimiento mete vencidas de hace meses", QM,
     [("        elif e == VENCIDA and 0 < -_d <= AVISO_DIAS_VENCIDA:", "        elif e == VENCIDA:")]),
    ("las perdidas por motivo cuentan versiones", QM,
     [("        rep = representante(_vs)\n        if estado_de(rep) == RECHAZADA:\n",
       "        rep = _vs[-1]\n        if estado_de(rep) == RECHAZADA:\n")]),
    ("⚠️ la celda de la tabla vuelve al estado guardado", QU,
     [('    _e = (vis or {}).get(str(c.get("ID", ""))) or Q.vista(c)', "    _e = Q.estado_de(c)")]),
    ("el aviso de vencidas incluye versiones viejas", QU,
     [('    _venc = [c for c in cots if _vis.get(str(c.get("ID", ""))) == Q.VENCIDA]',
       "    _venc = [c for c in cots if Q.estado_de(c) == Q.VENCIDA]")]),
    ("la lista de perdidas no dice el motivo", QU,
     [("        if _mot:\n            st.caption(t(\":material/block: Lost, by reason",
       "        if False:\n            st.caption(t(\":material/block: Lost, by reason")]),
    ("⚠️ «They rejected it» rechaza sin preguntar el motivo", QU,
     [('            st.session_state[f"_cot_rech_{cid}"] = True\n            st.rerun()',
       "            Q.set_estado(cid, Q.RECHAZADA)\n            st.rerun()")]),
    ("«Record the rejection» sin motivo elegido", QU,
     [('                          width="stretch", disabled=not _rm):', '                          width="stretch"):')]),
    ("⚠️ «Back to quotes» tira los cambios otra vez", QU,
     [('        if _c0 and Q.estado_de(_c0) == Q.BORRADOR:\n            st.session_state[f"_cot_salir_{cid}"] = True',
       '        if _c0 and Q.estado_de(_c0) == Q.BORRADOR:\n            st.session_state.pop("_cot_open", None)')]),
    ("la versión sustituida no lo dice", QU,
     [("    if Q.vista(c) == Q.SUSTITUIDA and _rep:", "    if False:")]),
    ("la variación no avisa de su obra", QU,
     [("    elif est in (Q.ENVIADA, Q.VENCIDA, Q.BORRADOR) and _pid_t:", "    elif False:")]),
    ("⚠️ una aceptada sin obra con su trato ya en obra ofrece crear OTRA", QU,
     [("        if _pid_t:\n            # ⚠️ v689 · D1: otra versión ya creó la obra",
       "        if False:\n            # ⚠️ v689 · D1: otra versión ya creó la obra")]),
    ("«New version» de una aceptada no dice que es una variación", QU,
     [("        _con_obra_v = _con_obra or (est == Q.ACEPTADA and bool(_pid_t))", "        _con_obra_v = False")]),
    ("⚠️ «New quote» vuelve a preseleccionar el cliente", QU,
     [("                        index=None if fichas else 0, placeholder=",
       "                        index=len(_map) if not fichas else 0, placeholder=")]),
    ("el PDF sin razón social no avisa", QU,
     [('        if not str(_CB.identidad(grupo).get("legal") or "").strip():', "        if False:")]),
    ("⚠️ la campana no avisa de las cotizaciones", HU,
     [("            for _q in _QT.seguimiento(grupo)[:8]:", "            for _q in []:")]),
    ("la alerta de una cotización no lleva a ella", HU,
     [('    elif destino[0] == "cotizacion":              # v689', '    elif destino[0] == "cotizacion_x":              # v689')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", QM,
           [('    """La versión que habla por el trato de `c` (v689): la que cuentan las cifras."""',
             '    """La versión que habla por el trato de `c` (v689): la que cuentan las cifras. (control)"""')])


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
