# -*- coding: utf-8 -*-
"""v556 · TIME FIXES (BANDEJA DEL ADMIN), PROBADA ACCIÓN POR ACCIÓN.

Recorrido en producción (09/10/2026) sobre COR-0001..0003. Lo arreglado («Dale»):
  1. ⚠️ Dos correcciones sobre el MISMO fichaje: «Revert» en la vieja daba «no longer
     exists» y «Approve» habría confirmado una hora falsa → se detecta y se cierra como
     sustituida («superseded»).
  2. ⚠️ Cuando revertir choca con otra jornada no quedaba salida → «Set the right time»
     en TODAS; y el aviso de solape, neutro («the workday entry», no «your»).
  3. ⚠️ La persona nunca se enteraba de que su hora cambiaba → aviso al revertir o fijar.
  4. El DÍA del fichaje (tarjeta e historial) y fechas dd/mm/aaaa.
  5. Acción DIFERIDA (trampa 37).
  6. Lo más antiguo primero.  7. Tarjetas activas.  8. Tipo legible y el revisor por
     su NOMBRE.  + aislamiento: la acción busca SOLO en el grupo.

AppTest con datos inventados y el MOTOR REAL; solo se sustituyen la escritura en la hoja
(`_set`), el fichaje (`corregir_fichaje`) y el aviso. «Hoy» no importa aquí.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


print("0. Estático: las tarjetas solo APUNTAN (trampa 37: el fantasma no lo ve AppTest)")
_src = io.open(os.path.join("core", "correcciones_ui.py"), encoding="utf-8").read()
_fns = {n.name: n for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.FunctionDef)}
_LENTO = {"aprobar", "revertir", "ajustar", "cerrar_sustituida", "notify_user",
          "_avisar_persona", "_ejecutar", "corregir_fichaje"}
for _f in ("_tarjeta", "_kpis", "render_bandeja"):
    _n = _fns.get(_f)
    _ll = sorted({(c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", ""))
                  for c in ast.walk(_n) if isinstance(c, ast.Call)} & _LENTO) if _n else ["(no existe)"]
    chk("⚠️ `%s` no ejecuta nada lento (solo apunta)" % _f, not _ll, _ll)
_q = sorted(f for f, n in _fns.items()
            if any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_ejecutar"
                   for c in ast.walk(n)))
chk("`_ejecutar` solo se llama desde `_accion_pendiente`", _q == ["_accion_pendiente"], _q)
_rb = ast.unparse(_fns["render_bandeja"])
chk("…y la acción se ejecuta ANTES de pintar las tarjetas",
    0 <= _rb.find("_accion_pendiente(") < _rb.find("_tarjeta("))
_tc = io.open(os.path.join("core", "timeclock.py"), encoding="utf-8").read()
chk("el aviso de solape es neutro («the {what} entry», no «your»)",
    "overlaps the {what} entry" in _tc and "overlaps your {what} entry" not in _tc)

print("\n1. Con clics reales (AppTest, motor real)")
from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import streamlit as st
from core import correcciones as C, correcciones_ui as CUI, timeclock as TC, auth, notify

st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
def _r(i, g, u, n, tipo, campo, old, new, est, creado, proj="", pay="", rev="", revd=""):
    return {"ID": i, "Group": g, "User": u, "Name": n, "Type": tipo, "Project": proj,
            "Field": campo, "OldValue": old, "NewValue": new, "Reason": "r", "Status": est,
            "Created": creado, "ReviewedBy": rev, "ReviewedDate": revd, "AdminNote": "",
            "PayslipCovers": pay}
if "_RECS" not in st.session_state:
    st.session_state["_RECS"] = [
        _r("COR-2", "G", "ana", "Ana", "general", C.CAMPO_IN, "2026-10-08 18:00:00",
           "2026-10-08 18:27:00", C.PENDIENTE, "2026-10-08 18:29:00"),
        _r("COR-1", "G", "ana", "Ana", "general", C.CAMPO_IN, "2026-10-08 18:27:44",
           "2026-10-08 18:00:00", C.PENDIENTE, "2026-10-08 18:27:50"),
        _r("COR-3", "G", "beto", "Beto", "project", C.CAMPO_OUT, "", "2026-10-09 17:00:00",
           C.PENDIENTE, "2026-10-09 18:00:00", proj="Torre", pay="PAY-0001"),
        _r("COR-4", "G", "carl", "Carl", "general", C.CAMPO_IN, "2026-10-07 07:00:00",
           "2026-10-07 06:30:00", C.APROBADA, "2026-10-07 08:00:00", rev="jefa",
           revd="2026-10-08 09:00:00"),
        _r("COR-5", "OTRA", "zed", "Zed", "general", C.CAMPO_IN, "2026-10-08 07:00:00",
           "2026-10-08 06:00:00", C.PENDIENTE, "2026-10-08 08:00:00"),
    ]
    st.session_state["_LOG"] = []
RECS, LOG = st.session_state["_RECS"], st.session_state["_LOG"]
C.is_configured = lambda: True
C._records = lambda: RECS
C._invalidate = lambda: None
def _set(cid, campos):
    LOG.append(("set", cid, dict(campos)))
    for r in RECS:
        if r["ID"] == cid:
            r.update(campos)
    return True, cid
C._set = _set
def _corr(**kw):
    LOG.append(("fichaje", kw.get("valor_actual"), str(kw.get("valor_nuevo"))))
    if str(kw.get("valor_nuevo")).startswith("2026-10-08 18:00"):   # revertir COR-2 choca
        return False, TC._msg_choque({"Clock In": "2026-10-08 18:24:31",
                                      "Clock Out": "2026-10-08 18:26:22"}, TC.TIPO_GENERAL)
    return True, "ok"
TC.corregir_fichaje = _corr
notify.notify_user = lambda u, subj, lines: LOG.append(("aviso", u, subj, " ".join(lines)))
auth.list_users = lambda *a, **k: [{"User": u, "Name": n} for u, n in
                                   (("ana", "Ana"), ("beto", "Beto"), ("carl", "Carl"),
                                    ("jefa", "Jefa Boss"))]
CUI.render_bandeja("G")
'''


def b(at, k):
    x = [y for y in at.button if y.key == k]
    return x[0] if x else None


def log(at):
    return list(at.session_state["_LOG"])


def rec(at, cid):
    return next(r for r in at.session_state["_RECS"] if r["ID"] == cid)


def bloques(at, prefijo):
    out = []

    def _rec(n):
        for h in getattr(n, "children", {}).values():
            k = getattr(h, "key", None)
            if isinstance(k, str) and k.startswith(prefijo):
                out.append(k)
            _rec(h)
    _rec(at.main)
    return out


def texto(at):
    return " | ".join([m.value for m in at.markdown] + [m.value for m in at.caption]
                      + [m.value for m in at.info] + [m.value for m in at.warning])


def flashes(at):
    return list(at.session_state["_flash_cola"]) if "_flash_cola" in at.session_state else []


at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_c = [k for k in bloques(at, "cor_COR")]
chk("⚠️ lo más ANTIGUO primero (COR-1, COR-2, COR-3) y sin la de otra empresa",
    _c == ["cor_COR-1", "cor_COR-2", "cor_COR-3"], _c)
_t = texto(at)
chk("⚠️ el DÍA del fichaje en la tarjeta: «**Thu 08/10/2026**»", "**Thu 08/10/2026**" in _t, _t[:300])
chk("el tipo legible («workday» / «project»), no el dato crudo",
    "· workday" in _t and "· project · Torre" in _t and "`general`" not in _t)
chk("«Asked on» en dd/mm/aaaa", "Asked on 08/10/2026 18:27" in _t)

print("\n2. La sustituida")
chk("⚠️ COR-1 dice que la sustituyó COR-2", "Superseded by **COR-2**" in _t)
chk("…y solo ofrece cerrarla (ni Approve ni Revert ni hora)",
    b(at, "cor_sus_COR-1") is not None and b(at, "cor_ok_COR-1") is None
    and b(at, "cor_no_COR-1") is None and b(at, "cor_fixb_COR-1") is None)
chk("COR-2 (la posterior) NO sale como sustituida", b(at, "cor_ok_COR-2") is not None)
b(at, "cor_sus_COR-1").click()
at.run()
chk("⚠️ «Close as superseded» la cierra como «superseded» sin tocar el fichaje",
    rec(at, "COR-1")["Status"] == "superseded" and not any(x[0] == "fichaje" for x in log(at)),
    rec(at, "COR-1")["Status"])
chk("…anotando por cuál", rec(at, "COR-1")["AdminNote"] == "superseded by COR-2")
chk("…y lo dice, con la persona y el día", any("Ana · Thu 08/10/2026" in m and "COR-2" in m
                                              for _t2, m in flashes(at)), flashes(at))

print("\n3. Revertir que choca, y fijar la hora")
b(at, "cor_no_COR-2").click()
at.run()
_e = [m for tp, m in flashes(at) if tp == "error"]
chk("⚠️ revertir COR-2 choca con otra jornada y lo dice NEUTRO («the workday entry»)",
    any("overlaps the workday entry from 18:24 to 18:26" in m and "your" not in m for m in _e), _e)
chk("…y la corrección sigue pendiente", rec(at, "COR-2")["Status"] == "pending")
chk("⚠️ «Set the right time» también en la tarjeta CON hora anterior",
    b(at, "cor_fixb_COR-2") is not None)
at.time_input(key="cor_fix_COR-2").set_value(__import__("datetime").time(18, 30))
b(at, "cor_fixb_COR-2").click()
at.run()
chk("fijar 18:30 corrige el fichaje y la marca aprobada",
    ("fichaje", "2026-10-08 18:27:00", "2026-10-08 18:30:00") in log(at)
    and rec(at, "COR-2")["Status"] == "approved"
    and rec(at, "COR-2")["NewValue"] == "2026-10-08 18:30:00", log(at)[-3:])
_av = [x for x in log(at) if x[0] == "aviso" and x[1] == "ana"]
chk("⚠️ y AVISA a la persona, en inglés y con el día",
    bool(_av) and "set your clock in for <b>08/10/2026</b> to <b>18:30</b>" in _av[0][3]
    and _av[0][2] == "Time correction adjusted: 08/10/2026", _av)

print("\n4. El cierre olvidado y aprobar")
chk("COR-3 (cierre olvidado, sin hora anterior): sin «Revert», con «Set the right time»",
    b(at, "cor_no_COR-3") is None and b(at, "cor_fixb_COR-3") is not None)
chk("…y avisa de la nómina ya pagada", "already paid in **PAY-0001**" in texto(at))
_n_av = len([x for x in log(at) if x[0] == "aviso"])
b(at, "cor_ok_COR-3").click()
at.run()
chk("aprobar la marca aprobada", rec(at, "COR-3")["Status"] == "approved")
chk("…y NO avisa (aprobar no cambia ninguna hora)",
    len([x for x in log(at) if x[0] == "aviso"]) == _n_av)

print("\n5. Tarjetas activas e historial")
for k in ("pend", "ok", "rev"):
    chk("la tarjeta %s es un botón" % k, b(at, "cpxkpi_cor_%s" % k) is not None)
b(at, "cpxkpi_cor_ok").click()
at.run()
chk("«Approved» abre su lista (Carl · Wed 07/10/2026 · 07:00 → 06:30)",
    "**Carl** · clock in · Wed 07/10/2026 · 07:00 → 06:30" in texto(at))
_df = at.dataframe[0].value if at.dataframe else None
chk("el histórico trae el DÍA", _df is not None and "Día" in _df.columns, list(_df.columns) if _df is not None else None)
_carl = _df[_df["Persona"] == "Carl"].iloc[0] if _df is not None else {}
chk("…el revisor por su NOMBRE («Jefa Boss», no «jefa»)", _df is not None and _carl["Revisor"] == "Jefa Boss",
    _carl["Revisor"] if _df is not None else None)
chk("…y la fecha en dd/mm/aaaa", _df is not None and _carl["Fecha"] == "08/10/2026 09:00")
chk("la sustituida sale en el histórico como «superseded»",
    _df is not None and "superseded" in list(_df["Estado"]))

print("\n6. Aislamiento")
at.session_state["_cor_accion"] = {"cid": "COR-5", "accion": "aprobar", "nota": ""}
at.run()
chk("⚠️ una acción apuntada a la de OTRA empresa no la toca",
    rec(at, "COR-5")["Status"] == "pending"
    and any("Correction not found" in m for _t2, m in flashes(at)), flashes(at))
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
