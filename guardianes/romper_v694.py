# -*- coding: utf-8 -*-
"""Batería de roturas de v694. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v694"
TOPE_S = 400
CR = "core/credentials.py"
TU = "core/timeclock_ui.py"
PSU = "core/prestart_ui.py"
PS = "core/prestart.py"
FC = "core/falsecar.py"
FCU = "core/falsecar_ui.py"
PR = "core/projects.py"
PU = "core/projects_ui.py"
AL = "core/alerts.py"
AD = "core/admin_digest.py"
HU = "core/home_ui.py"
DLU = "core/daily_log_ui.py"
HO = "core/handover.py"
HOU = "core/handover_ui.py"

ROTURAS = [
    ("⚠️ H4 · «por vencer» cuenta como incumplida", CR,
     [('        if est not in ("vencido", "falta"):\n            continue\n        _fs = [',
       '        if est not in ("vencido", "falta", "por_vencer"):\n            continue\n        _fs = [')]),
    ("H4 · la vencida sin su fecha", CR,
     [('        out.append((tipo, est, max(_fs).isoformat() if (est == "vencido" and _fs) else ""))',
       '        out.append((tipo, est, ""))')]),
    ("⚠️ H4 · fichar no avisa de la credencial", TU,
     [('    _nc = nota_credenciales(pid, grupo, usuario)     # v694 · H4 del ciclo 6\n    if _nc:\n        flash.aviso(_nc)\n',
       "")]),
    ("H4 · el Pre-Start no dice lo que no cumple cada asistente", PSU,
     [('                if _m:\n                    st.caption(":orange[:material/badge: " + literal_md(_CR.texto_incumplidas(_m)) + "]")\n',
       "")]),
    ("H5 · fichar no deja la obra para «My projects»", TU,
     [('    st.session_state["_fieldproj_pending"] = str(pid)\n', "")]),
    ("H5 · «My projects» recoge una obra que no es suya", PU,
     [("    if _pend and str(_pend) in idmap:\n", "    if _pend:\n")]),
    ("H6 · el icono de error vuelve a «A project alert was opened»", FCU,
     [('":material/notifications_active: A project alert was opened. The administrator has been notified."',
       '":material/cancel: A project alert was opened. The administrator has been notified."')]),
    ("⚠️ H8 · «It is installed» acredita al 50 %", FC,
     [('[{"etapa": _et, "actividad": S.FC_MONTAR, "pct": 100, "nota": ""}]',
       '[{"etapa": _et, "actividad": S.FC_MONTAR, "pct": 50, "nota": ""}]')]),
    ("H8 · el botón sale con la máquina ya montada antes", FCU,
     [("        if dia == hoy and not FC.periodo(prj)[0]:\n", "        if dia == hoy:\n")]),
    ("H9 · el nombre repetido no cambia", PR,
     [('    if str(nombre).strip().lower() not in _ya:\n        return nombre\n', "    return nombre\n")]),
    ("H9 · el Pre-Start no pasa por nombre_libre", PS,
     [('        fname = _Pn.nombre_libre(str(data.get("proyecto_id", "")), fname)\n', "        pass\n")]),
    ("⚠️ H26 · archivar sin la casilla", PU,
     [("                             disabled=not _ok_arch):\n", "                             disabled=False):\n")]),
    ("H26 · archivar no dice lo que es («Project updated.» otra vez)", PR,
     [('        return ok, (t("Project archived.") if ok else msg)     # v694 · decía «Project updated.»\n',
       "        return ok, msg\n")]),
    ("⚠️ H26 · la de seguridad de una obra archivada sale de la campana", AD,
     [('                if _pid in _vistos or not _seg.get(_pid):\n                    continue\n',
       "                continue\n")]),
    ("H26 · una alarma que no es de seguridad cuenta para la campana de una archivada", AL,
     [('        if str(r.get("Status", "")) == "abierta" and es_seguridad(r):\n            k = str(r.get("ProjectID", ""))\n'
       '            d[k] = d.get(k, 0) + 1\n    return d\n',
       '        if str(r.get("Status", "")) == "abierta":\n            k = str(r.get("ProjectID", ""))\n'
       '            d[k] = d.get(k, 0) + 1\n    return d\n')]),
    ("⚠️ H27 · escribir una alarma no tira el resumen del día", AL,
     [("    try:\n        from core import admin_digest\n        admin_digest.invalidar()\n    except Exception:\n        pass\n",
       "")]),
    ("H27 · invalidar no tira nada", AD,
     [("    try:\n        group_digest.clear()\n    except Exception:\n        pass\n", "    pass\n")]),
    ("⚠️ D4 · resolver no avisa a quien la levantó", AL,
     [("                _avisar_resuelta(r, resuelto_por, nota)\n", "                pass\n")]),
    ("D4 · también avisa de una que no es de seguridad", AL,
     [("            if gestor and es_seguridad(r) and _autor and", "            if gestor and _autor and")]),
    ("D4 · la campana del campo trae lo que resolvió él mismo", AL,
     [('                or str(r.get("ResolvedBy", "")).strip().lower() == u):\n', "):\n")]),
    ("D4 · la campana del campo no lleva a la obra", HU,
     [('        st.session_state["_fieldproj_pending"] = str(destino[1])\n        st.session_state["cpxseg_fld_sec"] = "🚨 Avisos"\n',
       "")]),
    ("⚠️ H15 · ampliar pisa el mensaje (pierde que era de seguridad)", AL,
     [('        _nuevo = "%s\\n\\n+ %s · %s: %s" % (str(r.get("Message", "")), quien,\n',
       '        _nuevo = "%s%s · %s: %s" % ("", quien,\n')]),
    ("H15 · ampliar acepta una alarma ya resuelta", AL,
     [('        if str(r.get("Status", "")) != "abierta":\n            return False, _d("That alert is already resolved: send it as a new one.")\n',
       "")]),
    ("⚠️ H15 · «Add it to» abre otra alarma", DLU,
     [('        if pet.get("alerta"):\n            # v694 · H15', '        if False:\n            # v694 · H15')]),
    ("H15 · la del false car de OTRO día también se ofrece", DLU,
     [('              if alerts.es_seguridad(a) and _dia and _pd(str(a.get("Date", "")).split(" ")[0]) == _dia]\n',
       "              if alerts.es_seguridad(a)]\n")]),
    ("⚠️ H25 · quien firmó sin fichar no sale", HO,
     [('            if u and _d.isoformat() not in (fich.get(u) or ()):\n                out.add((u, _d.isoformat()))\n',
       "            pass\n")]),
    ("H25 · sin `dias_fichados`, acusa a todos", HO,
     [('    if "dias_fichados" not in ctx:\n        return []\n', "")]),
    ("H25 · firmar sin certificado no se dice", HO,
     [("    for u, _d in sorted(_sin_cert.items(), key=lambda x: x[1]):\n", "    for u, _d in []:\n")]),
    ("H25 · (l) no cuenta a quien firmó", HO,
     [("    for u, d in _asistieron(ctx).items():\n        if str(d) > str(trabajaron.get(u) or \"\"):\n            trabajaron[u] = d\n",
       "")]),
    ("H25 · la asistencia sin todos los días fichados", HOU,
     [("                dias.setdefault(_u, set()).add(_d)\n", "")]),
    ("H25 · la ficha no lo dice", PU,
     [("    st.caption(f\"Total: **{_lb['horas']:.1f} h**\")\n    _firmaron_sin_fichar(pid, grupo)                # v694 · H25\n",
       "    st.caption(f\"Total: **{_lb['horas']:.1f} h**\")\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", AL,
           [("    # v694 · D4 del ciclo 6 (decisión del usuario): una de SEGURIDAD resuelta por la oficina se le dice a quien\n",
             "    # v694 · D4 del ciclo 6 (decisión del usuario): una de SEGURIDAD resuelta por la oficina se le dice a quien · control\n")])


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
