# -*- coding: utf-8 -*-
"""v691 · Ciclo 5 → mejoras 3/4, el INVENTARIO (22/11), con las decisiones del usuario:
- D4 / H11 · dar de baja pide motivo y avisa si está fuera, y suelta al responsable; reactivar lo devuelve a un almacén;
- D3 / H15 · el QR sirve al campo: «My equipment» con la ficha de solo lectura, «I have it», «I returned it» y
  «Report a problem»; la oficina lo ve en la ficha y en la campana, y lo confirma o lo da por visto;
- H12 · la obra dice qué equipos tiene (oficina y campo) y el campo recibe el aviso de la vuelta;
- H7 · la vuelta se ve con o sin responsable; H8/H13 · sin preselección (categoría, obra, persona);
- H10 · la persona por su nombre, no la cuenta; H14 · quitar una categoría en uso pide a cuál pasarlas;
- H9 · la etiqueta con la razón social; y lo visto verificando v689: el aviso del emisor no salía nunca
  (`identidad()["legal"]` cae al nombre del grupo) → `contable.tiene_razon_social`.

Nada sale a la red ni escribe: hojas FALSAS que apuntan lo escrito, sustitutos y AppTest.
"""
import ast
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import inventory as INV                                          # noqa: E402
from core import contable, auth                                            # noqa: E402
from core import clock                                                     # noqa: E402
from core.num import col_letter                                            # noqa: E402

HOY = date(2026, 11, 22)


class _Hoja:
    def __init__(self, cab, filas):
        self.cab, self.filas, self.escrito, self.borradas = list(cab), [dict(x) for x in filas], [], []

    def get_all_records(self, **k):
        return [dict(x) for x in self.filas]

    def append_row(self, fila, **k):
        self.filas.append(dict(zip(self.cab, [str(x) for x in fila])))

    def batch_update(self, lote, **k):
        self.escrito += lote
        for it in lote:
            _col = "".join(ch for ch in it["range"] if ch.isalpha())
            _row = int("".join(ch for ch in it["range"] if ch.isdigit()))
            self.filas[_row - 2][next(h for i, h in enumerate(self.cab) if col_letter(i + 1) == _col)] = it["values"][0][0]

    def delete_rows(self, i):
        self.borradas.append(i)
        del self.filas[i - 2]


def _act(aid, nombre, **kw):
    r = {h: "" for h in INV.ACTIVOS_HEADERS}
    r.update({"ID": aid, "Group": "G", "Name": nombre, "Category": "Tool", "Status": "available", "Active": "SI",
              "LocationType": "warehouse", "LocationRef": "Main store, bay 3"})
    r.update(kw)
    return r


def _mov(mid, aid, tipo, creado, user="", nota="", desde="", hacia=""):
    return {"ID": mid, "Group": "G", "AssetID": aid, "Type": tipo, "Date": creado[:10], "FromLocation": desde,
            "ToLocation": hacia, "User": user, "Cost": "", "Note": nota, "CreatedBy": "x", "Created": creado}


def _hojas(acts, movs=(), cats=()):
    H = {INV.ACTIVOS_SHEET: _Hoja(INV.ACTIVOS_HEADERS, acts), INV.MOV_SHEET: _Hoja(INV.MOV_HEADERS, movs),
         INV.CAT_SHEET: _Hoja(INV.CAT_HEADERS, cats)}
    _n = [100]

    def _sig():
        _n[0] += 1
        return f"MOV-{_n[0]}"
    return H, [_sustituir(INV, _ws=lambda nombre: (H[nombre], None), _records=lambda nombre: [dict(x) for x in H[nombre].filas],
                          _invalidate=lambda: None, _next_mov_id=_sig),
               _sustituir(clock, today=lambda *a, **k: HOY)]


def _deshacer(d):
    for x in d:
        x()


print("1. La baja y la vuelta (D4, H11)")
H, d = _hojas([_act("ACT-6", "Chain hoist", Status="in use", LocationType="project", LocationRef="PRJ-45",
                    AssignedTo="campo000", ReturnDate="2026-11-25")],
              [_mov("MOV-1", "ACT-6", "check-out", "2026-11-17 17:55:33", desde="warehouse: Main store, bay 3",
                    hacia="project: C4")])
try:
    _ok, _m = INV.dar_de_baja("ACT-6", "G", "", "Admin2")
    chk("sin motivo NO se da de baja (salía «Asset written off.» sin él)", not _ok and "reason" in _m
        and H[INV.ACTIVOS_SHEET].filas[0]["Status"] == "in use", _m)
    _ok, _m = INV.dar_de_baja("ACT-6", "G", "lost — fell into the pit", "Admin2")
    _a = H[INV.ACTIVOS_SHEET].filas[0]
    chk("prestado a campo000: de baja, SIN responsable ni fecha de vuelta",
        _ok and _a["Status"] == "written off" and _a["Active"] == "NO" and _a["AssignedTo"] == "" and _a["ReturnDate"] == "",
        _a)
    _mv = H[INV.MOV_SHEET].filas[-1]
    chk("…y el movimiento guarda quién lo tenía y el motivo",
        _mv["Type"] == "written off" and _mv["User"] == "campo000" and _mv["Note"] == "lost — fell into the pit", _mv)
    _ok, _m = INV.reactivar("ACT-6", "G", "Admin2")
    _a = H[INV.ACTIVOS_SHEET].filas[0]
    chk("reactivar: disponible, en el almacén de donde salió («Main store, bay 3»), sin responsable",
        _ok and _a["Status"] == "available" and _a["Active"] == "SI" and _a["LocationType"] == "warehouse"
        and _a["LocationRef"] == "Main store, bay 3" and _a["AssignedTo"] == "", (_m, _a))
    chk("…con su movimiento a «warehouse: Main store, bay 3»",
        H[INV.MOV_SHEET].filas[-1]["ToLocation"] == "warehouse: Main store, bay 3", H[INV.MOV_SHEET].filas[-1])
finally:
    _deshacer(d)

print("2. La persona por su nombre (H10), solo para pantalla")
_NOM = {"campo000": "hjg,ujgjg (campo000)"}
_a = _act("ACT-7", "Drill", Status="in use", LocationType="user", LocationRef="campo000")
chk("ubic_str con nombres: «user: hjg,ujgjg (campo000)»", INV.ubic_str(_a, None, _NOM) == "user: hjg,ujgjg (campo000)",
    INV.ubic_str(_a, None, _NOM))
chk("…sin nombres (lo que se ESCRIBE en el historial), la cuenta", INV.ubic_str(_a) == "user: campo000")
chk("ubic_texto del historial también", INV.ubic_texto("user: campo000", lambda x: x.title(), _NOM) == "User: hjg,ujgjg (campo000)",
    INV.ubic_texto("user: campo000", lambda x: x.title(), _NOM))

print("3. Quitar una categoría en uso (H14)")
H, d = _hojas([_act("ACT-6", "Hoist", Category="C5 Lifting gear"), _act("ACT-8", "Old", Category="C5 Lifting gear",
                                                                          Active="NO", Status="written off")],
              cats=[{"Group": "G", "Name": "C5 Lifting gear"}])
try:
    _ok, _m = INV.del_categoria("G", "C5 Lifting gear")
    chk("con 2 activos (uno de baja) y sin destino, se NIEGA", not _ok and "2 asset(s)" in _m
        and not H[INV.CAT_SHEET].borradas, _m)
    _ok, _m = INV.del_categoria("G", "C5 Lifting gear", mover_a="Tool")
    chk("con destino «Tool», los pasa y la quita",
        _ok and [a["Category"] for a in H[INV.ACTIVOS_SHEET].filas] == ["Tool", "Tool"] and H[INV.CAT_SHEET].borradas == [2],
        (_m, [a["Category"] for a in H[INV.ACTIVOS_SHEET].filas]))
finally:
    _deshacer(d)

print("4. Lo que dice el campo (D3): pendiente hasta que se cierra")
_MV = [_mov("MOV-1", "ACT-6", "field: has it", "2026-11-20 08:00:00", user="campo000"),
       _mov("MOV-2", "ACT-6", "check-out", "2026-11-20 09:00:00"),                        # lo cierra
       _mov("MOV-3", "ACT-6", "field: returned", "2026-11-21 08:00:00", user="campo000"),   # pendiente
       _mov("MOV-4", "ACT-7", "field: problem", "2026-11-21 09:00:00", user="helper1", nota="hook bent"),
       _mov("MOV-5", "ACT-7", "office: seen", "2026-11-21 10:00:00", nota="MOV-4"),          # visto
       _mov("MOV-6", "ACT-7", "field: problem", "2026-11-22 07:00:00", user="helper1", nota="chain noisy"),
       _mov("MOV-7", "ACT-7", "transfer", "2026-11-22 08:00:00")]                         # NO cierra un problema
H, d = _hojas([_act("ACT-6", "Hoist", Status="in use", AssignedTo="campo000", LocationType="user",
                    LocationRef="campo000"), _act("ACT-7", "Drill"),
               _act("ACT-9", "Ajeno", Group="OTRA")], _MV)
try:
    _p = INV.avisos_pendientes("G")
    chk("pendientes: MOV-3 (devuelto) y MOV-6 (problema); no MOV-1 (lo cerró la salida) ni MOV-4 (visto)",
        [x["id"] for x in _p] == ["MOV-3", "MOV-6"], _p)
    chk("…con el nombre del activo, quién y la nota", _p[1]["activo"] == "Drill" and _p[1]["usuario"] == "helper1"
        and _p[1]["nota"] == "chain noisy", _p[1])
    _ok, _m = INV.avisar_desde_campo("ACT-6", "G", "campo000", "returned")
    chk("repetir un aviso pendiente se niega", not _ok and "already" in _m, _m)
    _ok, _m = INV.avisar_desde_campo("ACT-7", "G", "campo000", "problem", "")
    chk("un problema sin nota se niega", not _ok, _m)
    _ok, _m = INV.avisar_desde_campo("ACT-9", "G", "campo000", "has it")
    chk("un equipo de OTRA empresa no existe para él", not _ok and "not found" in _m, _m)
    _ok, _m = INV.avisar_desde_campo("ACT-7", "G", "campo000", "hello")
    chk("un tipo inventado se niega", not _ok, _m)
    _ok, _m = INV.avisar_desde_campo("ACT-7", "G", "campo000", "has it")
    _mv = H[INV.MOV_SHEET].filas[-1]
    chk("«I have it» apunta «field: has it» a su nombre y lo dice", _ok and _mv["Type"] == "field: has it"
        and _mv["User"] == "campo000" and _mv["AssetID"] == "ACT-7" and "office will confirm" in _m, (_m, _mv))
    _ok, _m = INV.dar_por_visto("ACT-7", "G", "MOV-6", "Admin2")
    chk("«Dismiss» apunta «office: seen» con el ID del aviso, y deja de estar pendiente",
        _ok and H[INV.MOV_SHEET].filas[-1]["Type"] == "office: seen" and H[INV.MOV_SHEET].filas[-1]["Note"] == "MOV-6"
        and "MOV-6" not in [x["id"] for x in INV.avisos_pendientes("G")], _m)
    _ok, _m = INV.dar_por_visto("ACT-7", "G", "MOV-6", "Admin2")
    chk("…y otra vez, no", not _ok, _m)
finally:
    _deshacer(d)

print("5. Confirmar «lo tengo» (pasar_a)")
_SAL = []
H, d = _hojas([_act("ACT-1", "Disponible"),
               _act("ACT-2", "En obra", Status="in use", LocationType="project", LocationRef="PRJ-45", AssignedTo="otro"),
               _act("ACT-3", "Con alguien", Status="in use", LocationType="user", LocationRef="otro", AssignedTo="otro"),
               _act("ACT-4", "Taller", Status="maintenance", LocationType="under repair")])
d.append(_sustituir(INV, salida=lambda aid, g, **k: (_SAL.append((aid, k)), (True, "Check-out recorded."))[1]))
try:
    _ok, _m = INV.pasar_a("ACT-1", "G", "campo000", "Admin2")
    chk("disponible → SALE a su nombre", _ok and _SAL and _SAL[0][0] == "ACT-1"
        and _SAL[0][1].get("hacia_tipo") == "user" and _SAL[0][1].get("usuario") == "campo000", _SAL)
    _ok, _m = INV.pasar_a("ACT-2", "G", "campo000", "Admin2")
    _a = H[INV.ACTIVOS_SHEET].filas[1]
    chk("en una obra → pasa a su CUSTODIA y sigue en la obra", _ok and _a["AssignedTo"] == "campo000"
        and _a["LocationRef"] == "PRJ-45", _a)
    _ok, _m = INV.pasar_a("ACT-3", "G", "campo000", "Admin2")
    _a = H[INV.ACTIVOS_SHEET].filas[2]
    chk("con otra persona → pasa a la SUYA (ubicación y custodia)", _ok and _a["AssignedTo"] == "campo000"
        and _a["LocationRef"] == "campo000", _a)
    chk("…con su movimiento «transfer» a su nombre", H[INV.MOV_SHEET].filas[-1]["Type"] == "transfer"
        and H[INV.MOV_SHEET].filas[-1]["User"] == "campo000")
    _ok, _m = INV.pasar_a("ACT-4", "G", "campo000", "Admin2")
    chk("en mantenimiento, no", not _ok, _m)
    chk("de_la_persona: ACT-2 y ACT-3 son de campo000", sorted(a["ID"] for a in INV.de_la_persona("G", "campo000"))
        == ["ACT-2", "ACT-3"])
    chk("en_obra(PRJ-45): ACT-2", [a["ID"] for a in INV.en_obra("G", "PRJ-45")] == ["ACT-2"])
finally:
    _deshacer(d)
chk("vuelta_de: el 25/11 visto el 22/11 → 3 días; el 20/11 → -2",
    INV.vuelta_de({"ReturnDate": "2026-11-25"}, HOY)[1] == 3 and INV.vuelta_de({"ReturnDate": "2026-11-20"}, HOY)[1] == -2)

print("6. La razón social (lo visto verificando v689)")
_d = _sustituir(auth, group_text_setting=lambda g, k, d="": "")
chk("CONTROL: `identidad()['legal']` cae al nombre del grupo (por eso el aviso de v689 no salía)",
    contable.identidad("cliente1")["legal"] == "cliente1")
chk("tiene_razon_social mira el ajuste de verdad: sin él, False", contable.tiene_razon_social("cliente1") is False)
_d()
_d = _sustituir(auth, group_text_setting=lambda g, k, d="": "Acme Lifts Pty Ltd" if k == "LegalName" else d)
chk("…con él, True", contable.tiene_razon_social("cliente1") is True)
_d()

print("7. La ficha del activo para la oficina (AppTest)")
FICHA = r'''
import datetime as dt
import streamlit as st
from core import inventory_ui as IU, inventory as INV, clock, contable, drive_store
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
_A = dict(st.session_state["_A"])
INV.get_activo = lambda aid: dict(_A)
INV.list_movimientos = lambda g, aid=None: [dict(x) for x in st.session_state.get("_M", [])]
INV.list_activos = lambda g, incluir_baja=False: [dict(_A)]
INV.avisos_pendientes = lambda g, aid=None: list(st.session_state.get("_AV", []))
INV.categorias = lambda g: ["Consumable", "Equipment", "Tool"]
INV.ultima_bodega = lambda g, aid: "Main store, bay 3"
_LL = st.session_state.setdefault("_LL", [])
INV.pasar_a = lambda aid, g, u, cp="": (_LL.append(("pasar", aid, u)), (True, "ok"))[1]
INV.dar_por_visto = lambda aid, g, i, cp="": (_LL.append(("visto", i)), (True, "ok"))[1]
INV.dar_de_baja = lambda aid, g, m, cp="": (_LL.append(("baja", m)), (True, "ok"))[1]
INV.reactivar = lambda aid, g, cp="", bodega="": (_LL.append(("react", bodega)), (True, "ok"))[1]
contable.tiene_razon_social = lambda g: bool(st.session_state.get("_LEGAL"))
contable.identidad = lambda g: {"legal": st.session_state.get("_LEGAL") or g}
IU._usuarios = lambda g: ["admin1", "campo000"]
IU._nombres = lambda g: {"admin1": "asfgjjd (admin1)", "campo000": "hjg,ujgjg (campo000)"}
IU._proyectos = lambda g: (["PRJ-26", "PRJ-45"], {"PRJ-26": "Bondi (PRJ-26)", "PRJ-45": "C4 (PRJ-45)"})
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
IU._detalle("G", _A["ID"])
'''


def _ficha(a, **ss):
    at = AppTest.from_string(FICHA, default_timeout=90)
    at.session_state["_A"] = a
    for k, v in ss.items():
        at.session_state[k] = v
    at.run()
    return at


def _txt(at):
    return " ¦ ".join(str(x.value) for x in list(at.markdown) + list(at.caption) + list(at.info) + list(at.warning)
                      + list(at.error)).replace("\\", "")


_EN_OBRA = _act("ACT-6", "Chain hoist", Status="in use", LocationType="project", LocationRef="PRJ-45",
                ReturnDate="2026-11-24")
at = _ficha(_EN_OBRA)
chk("la ficha se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("H7 · la vuelta SIN responsable se ve: «Due back: 24/11/2026»", "Due back: 24/11/2026" in _txt(at), _txt(at)[:600])
chk("H9 · la etiqueta sin razón social lo avisa: «The label shows «G»»", "The label shows «G»" in _txt(at))
at = _ficha(_EN_OBRA, _LEGAL="Acme Lifts Pty Ltd")
chk("…y con ella, no", "The label shows" not in _txt(at))
_PRES = dict(_EN_OBRA, AssignedTo="campo000", ReturnDate="2026-11-20")
at = _ficha(_PRES)
chk("vencida: «Due back: 20/11/2026 · 2 d late» en rojo", "Due back: 20/11/2026 · 2 d late" in _txt(at), _txt(at)[:700])
chk("H10 · «Location: Project…» y el responsable por su nombre", "hjg,ujgjg (campo000)" in _txt(at))
chk("D4 · la baja de algo prestado AVISA: «It is out … with hjg,ujgjg (campo000) until 20/11/2026»",
    "with **hjg,ujgjg (campo000)** until 20/11/2026" in _txt(at), _txt(at)[-900:])
chk("…y «Write off this asset» PARADO sin motivo (aun confirmando)",
    at.button(key="inv_baja_ACT-6").disabled, None)
at.checkbox(key="inv_baja_conf_ACT-6").check().run()
chk("…confirmado y sin motivo, sigue parado", at.button(key="inv_baja_ACT-6").disabled)
at.selectbox(key="inv_baja_mk_ACT-6").set_value("lost").run()
at.text_input(key="inv_baja_mot_ACT-6").set_value("  fell into   the pit ").run()
at.button(key="inv_baja_ACT-6").click().run()
chk("…con «Lost» y la nota, da de baja con «lost — fell into the pit»",
    ("baja", "lost — fell into the pit") in at.session_state["_LL"], at.session_state["_LL"])
_DISP = _act("ACT-6", "Chain hoist")
at = _ficha(_DISP)
_sel = {s.key: s.value for s in at.selectbox if str(s.key).startswith("inv_s")}
chk("H8 · la salida a una obra nace SIN obra elegida", _sel.get(next((k for k in _sel if k.startswith("inv_srp_")), ""), "x") is None,
    _sel)
chk("H7 · a una obra sin responsable lo avisa: «Nobody will be responsible for it on site»",
    "Nobody will be responsible for it on site" in _txt(at), _txt(at)[:600])
at.selectbox(key=next(s.key for s in at.selectbox if str(s.key).startswith("inv_sdt_"))).set_value("user").run()
chk("H13 · a una persona, nace SIN persona elegida",
    next((s.value for s in at.selectbox if str(s.key).startswith("inv_sru_")), "x") is None)
_BAJA = _act("ACT-6", "Chain hoist", Status="written off", Active="NO")
at = _ficha(_BAJA, _M=[_mov("MOV-9", "ACT-6", "written off", "2026-11-22 10:00:00", nota="lost — fell into the pit")])
chk("de baja: «Reason: Lost — fell into the pit»", "Reason: Lost — fell into the pit" in _txt(at), _txt(at)[:500])
chk("…y «Back to (store location)» con el almacén de donde salió",
    any(x.key == "inv_react_bod_ACT-6" and x.value == "Main store, bay 3" for x in at.text_input))
at.button(key="inv_react_ACT-6").click().run()
chk("…«Reactivate» lo devuelve ahí", ("react", "Main store, bay 3") in at.session_state["_LL"], at.session_state["_LL"])
_AV = [{"id": "MOV-20", "aid": "ACT-6", "activo": "Chain hoist", "usuario": "campo000", "tipo": "has it", "nota": "",
        "fecha": "2026-11-22 10:20:05"}]
at = _ficha(_DISP, _AV=_AV)
chk("D3 · en la ficha: «hjg,ujgjg (campo000) says they have it (22/11/2026 10:20)»",
    "says they have it (22/11/2026 10:20)" in _txt(at) and "hjg,ujgjg (campo000)" in _txt(at), _txt(at)[:500])
at.button(key="inv_avok_MOV-20").click().run()
chk("…«Confirm: it is with them» se lo pasa a él", ("pasar", "ACT-6", "campo000") in at.session_state["_LL"],
    at.session_state["_LL"])
at = _ficha(_DISP, _AV=_AV)
at.button(key="inv_avno_MOV-20").click().run()
chk("…y «Dismiss» lo da por visto", ("visto", "MOV-20") in at.session_state["_LL"], at.session_state["_LL"])

print("8. El alta y las categorías (H8, H14)")
ALTA = r'''
import streamlit as st
from core import inventory_ui as IU, inventory as INV
INV.categorias = lambda g: ["Consumable", "Tool"]
INV.categorias_propias = lambda g: ["C5 Lifting gear"]
INV.en_uso_categoria = lambda g, c: [{"ID": "ACT-6"}] if c == "C5 Lifting gear" else []
INV.list_activos = lambda g, incluir_baja=False: []
INV.create_activo = lambda **k: (st.session_state.setdefault("_LL", []).append(("crear", k.get("categoria"))), (True, "ACT-1"))[1]
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
if st.session_state.get("_CAT"):
    IU._categorias_expander("G")
else:
    IU._registro("G")
'''
at = AppTest.from_string(ALTA, default_timeout=60).run()
chk("H8 · la categoría del alta nace SIN elegir", next(s for s in at.selectbox if "inv_reg_cat_" in str(s.key)).value is None)
at.text_input(key=next(x.key for x in at.text_input if "inv_reg_nom_" in str(x.key))).set_value("Hoist")
_sb = next(b for b in at.button if "Register" in str(b.label))
_sb.click().run()
chk("…registrar sin categoría: «Choose the category.» y no crea",
    "Choose the category." in _txt(at) and ("_LL" not in at.session_state or not at.session_state["_LL"]),
    _txt(at)[-300:])
at = AppTest.from_string(ALTA, default_timeout=60)
at.session_state["_CAT"] = True
at.run()
at.selectbox(key="inv_cat_del").set_value("C5 Lifting gear").run()
chk("H14 · quitar «C5 Lifting gear» en uso: lo dice y pide «Move them to»",
    "1 asset(s) use «C5 Lifting gear»" in _txt(at) and any(s.key == "inv_cat_dest" for s in at.selectbox), _txt(at)[-400:])
chk("…y «Remove» PARADO hasta elegir el destino", at.button(key="inv_cat_delbtn").disabled)

print("9. «My equipment» del campo (D3)")
CAMPO = r'''
import datetime as dt
import streamlit as st
from core import inventory_ui as IU, inventory as INV, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
_AS = {a["ID"]: a for a in st.session_state["_AS"]}
INV.get_activo = lambda aid: dict(_AS.get(aid, {}))
INV.list_activos = lambda g, incluir_baja=False: [dict(a) for a in _AS.values() if a["Group"] == g]
INV.avisos_pendientes = lambda g, aid=None: list(st.session_state.get("_AV", []))
_LL = st.session_state.setdefault("_LL", [])
INV.avisar_desde_campo = lambda aid, g, u, tipo, nota="": (_LL.append((aid, u, tipo, nota)), (True, "Sent."))[1]
IU._nombres = lambda g: {"campo000": "hjg,ujgjg (campo000)", "otro": "Otro (otro)"}
st.session_state.setdefault("auth", {"usuario": "campo000", "rol": "field", "grupo": "G", "nombre": "hjg,ujgjg"})
IU.render_equipo_campo("campo000", "G")
'''
_AS = [_act("ACT-6", "Chain hoist", Status="in use", LocationType="project", LocationRef="PRJ-45", AssignedTo="campo000",
            ReturnDate="2026-11-25"),
       _act("ACT-7", "Drill", Status="in use", LocationType="user", LocationRef="otro", AssignedTo="otro"),
       _act("ACT-9", "Ajeno", Group="OTRA")]


def _campo(**ss):
    at = AppTest.from_string(CAMPO, default_timeout=60)
    at.session_state["_AS"] = _AS
    for k, v in ss.items():
        at.session_state[k] = v
    at.run()
    return at


at = _campo()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("su lista: el polipasto con «back by 25/11/2026» (y no el taladro de otro)",
    any("Chain hoist" in str(b.label) and "back by 25/11/2026" in str(b.label) for b in at.button)
    and not any("Drill" in str(b.label) for b in at.button), [b.label for b in at.button])
# ⚠️ trampa 58: el campo de un FORMULARIO se pone en la MISMA pasada que su envío
at.text_input(key=next(x.key for x in at.text_input)).set_value("act-7")
next(b for b in at.button if "Open" in str(b.label)).click().run()
chk("buscar «act-7» (en minúsculas) abre la ficha del taladro", at.session_state["_equipo_open"] == "ACT-7")
chk("…que dice dónde está y con quién, por su nombre: «With: Otro (otro)»", "**With:** Otro (otro)" in _txt(at), _txt(at))
at.button(key="inv_campo_tengo_ACT-7").click().run()
chk("…«I have it» avisa a la oficina (no mueve nada)", ("ACT-7", "campo000", "has it", "") in at.session_state["_LL"],
    at.session_state["_LL"])
at = _campo(_equipo_open="ACT-6")
chk("el SUYO ofrece «I returned it» (y no «I have it»)",
    any(b.key == "inv_campo_devolvi_ACT-6" for b in at.button) and not any(b.key == "inv_campo_tengo_ACT-6" for b in at.button))
at = _campo(_equipo_open="ACT-6", _AV=[{"id": "M1", "aid": "ACT-6", "usuario": "campo000", "tipo": "returned",
                                          "nota": "", "fecha": "2026-11-22 10:00:00", "activo": "Chain hoist"}])
chk("con su aviso pendiente: «waiting for them to confirm» y sin repetir el botón",
    "You told the office you returned it" in _txt(at) and not any(b.key == "inv_campo_devolvi_ACT-6" for b in at.button))
at = _campo(_equipo_open="ACT-6")
_k = next(x.key for x in at.text_area if "inv_campo_prob_ACT-6" in str(x.key))
at.text_area(key=_k).set_value("the hook is bent").run()
at.button(key="inv_campo_probbtn_ACT-6").click().run()
chk("«Report a problem» manda la nota", ("ACT-6", "campo000", "problem", "the hook is bent") in at.session_state["_LL"],
    at.session_state["_LL"])
at = _campo(_equipo_open="ACT-9")
chk("un equipo de OTRA empresa: «Asset not found.»", "Asset not found." in _txt(at) and not any(
    "inv_campo_tengo" in str(b.key) for b in at.button))

print("10. La campana y la obra (H12, D3)")
CAMP = r'''
import datetime as dt
import streamlit as st
from core import home_ui as H, inventory as INV, clock, admin_digest, credentials, toolruns, quotes
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
admin_digest.group_digest = lambda g: {}
admin_digest.nombres_usuarios = lambda: {"campo000": "hjg,ujgjg", "otro": "Otro"}
credentials.is_configured = lambda: False
toolruns.survey_por_decidir = lambda g: []
quotes.seguimiento = lambda g: []
INV.is_configured = lambda: True
INV.list_activos = lambda g, incluir_baja=False: [dict(a) for a in st.session_state["_AS"]]
INV.avisos_pendientes = lambda g, aid=None: list(st.session_state.get("_AV", []))
INV.alertas = lambda g: [{"tipo": "no_devuelto", "activo": "Drill", "id": "ACT-7", "dias": 3, "usuario": "otro"}]
st.session_state.setdefault("auth", {"usuario": st.session_state.get("_U", "admin2"), "rol": st.session_state.get("_ROL", "administrator"),
                                     "grupo": "G", "nombre": "x"})
st.session_state["_IT"] = H._alertas_items("G")
if st.button("ir", key="ir"):                      # una vez: `_ir_alerta` relanza la página
    H._ir_alerta(st.session_state["_IT"][0]["destino"], "G")
'''
at = AppTest.from_string(CAMP, default_timeout=60)
at.session_state["_AS"] = [dict(_AS[0], ReturnDate="2026-11-23")]
at.session_state["_U"], at.session_state["_ROL"] = "campo000", "field"
at.run()
_it = at.session_state["_IT"]
chk("al CAMPO: «Chain hoist — back by 23/11/2026» (vuelve mañana) y lleva a SU ficha",
    any("Chain hoist" in x["texto"] and "back by 23/11/2026" in x["texto"] for x in _it)
    and ("equipo", "ACT-6") in [x["destino"] for x in _it], _it)
at = AppTest.from_string(CAMP, default_timeout=60)
at.session_state["_AS"] = [dict(_AS[0], ReturnDate="2026-11-23")]
at.session_state["_U"], at.session_state["_ROL"] = "campo000", "field"
at.run()
at.button(key="ir").click().run()
chk("…tocarla abre «My equipment» con esa ficha", at.session_state["_equipo_open"] == "ACT-6"
    and at.session_state["_admin_nav_pending"] == ("autogestion", "🧰 Equipo"))
at = AppTest.from_string(CAMP, default_timeout=60)
at.session_state["_AS"] = [dict(_AS[0], ReturnDate="2026-12-20")]
at.session_state["_U"], at.session_state["_ROL"] = "campo000", "field"
at.run()
chk("…con la vuelta lejos, nada", not [x for x in at.session_state["_IT"] if "Chain hoist" in x["texto"]])
at = AppTest.from_string(CAMP, default_timeout=60)
at.session_state["_AS"] = _AS
at.session_state["_AV"] = [{"id": "M1", "aid": "ACT-6", "activo": "Chain hoist", "usuario": "campo000", "tipo": "has it",
                            "nota": "", "fecha": "2026-11-22 10:00:00"}]
at.run()
_tx = [x["texto"] for x in at.session_state["_IT"]]
chk("a la OFICINA: «Chain hoist — hjg,ujgjg says they have it», que lleva al activo",
    any("Chain hoist" in x and "hjg,ujgjg says they have it" in x for x in _tx)
    and ("activo", "ACT-6") in [x["destino"] for x in at.session_state["_IT"]], _tx)
chk("H10 · y el no devuelto, con el NOMBRE: «(Otro)», no la cuenta", any("not returned" in x and "(Otro)" in x for x in _tx), _tx)

OBRA = r'''
import streamlit as st
from core import projects_ui as PU, inventory as INV, home_ui, auth
INV.is_configured = lambda: True
INV.list_activos = lambda g, incluir_baja=False: [dict(a) for a in st.session_state["_AS"]]
auth.list_users = lambda *a, **k: [{"User": "campo000", "Name": "hjg,ujgjg"}]
home_ui.navegar = lambda *a: st.session_state.__setitem__("_NAV", a)
if st.session_state.get("_CAMPO"):
    PU._equipos_en_obra_campo({"ID": "PRJ-45", "Type": "Installation"}, "G", "campo000")
else:
    PU._equipos_en_obra("PRJ-45", "G")
'''
at = AppTest.from_string(OBRA, default_timeout=60)
at.session_state["_AS"] = _AS
at.run()
_b = next((b for b in at.button if "Chain hoist" in str(b.label)), None)
chk("en la obra (oficina): «Chain hoist · ACT-6 · hjg,ujgjg · back by 25/11/2026»",
    _b is not None and "ACT-6" in _b.label and "hjg,ujgjg" in _b.label and "back by 25/11/2026" in _b.label,
    [b.label for b in at.button])
_b.click().run()
chk("…que abre su ficha en Inventory", at.session_state["_inv_open"] == "ACT-6" and at.session_state["_NAV"] == ("inventario", None))
at = AppTest.from_string(OBRA, default_timeout=60)
at.session_state["_AS"] = _AS
at.session_state["_CAMPO"] = True
at.run()
chk("en «My projects» (campo): «Equipment on site: Chain hoist (with you, back by 25/11/2026)»",
    any("Equipment on site: Chain hoist (with you, back by 25/11/2026)" in str(c.value) for c in at.caption),
    [c.value for c in at.caption])

print("11. Que las piezas estén ENCHUFADAS (estático)")
_src = lambda rel: open(os.path.join(RAIZ, rel), encoding="utf-8").read()        # noqa: E731


def _llama(rel, fn, llamada):
    tr = ast.parse(_src(rel))
    f = next((n for n in ast.walk(tr) if isinstance(n, ast.FunctionDef) and n.name == fn), None)
    return f is not None and any(isinstance(c, ast.Call) and ast.unparse(c.func) == llamada for c in ast.walk(f))


chk("la ficha de la obra (Status) llama a `_equipos_en_obra`", _llama("core/projects_ui.py", "_estado_section", "_equipos_en_obra"))
chk("«My projects» llama a `_equipos_en_obra_campo`", _llama("core/projects_ui.py", "render_field_projects",
                                                            "_equipos_en_obra_campo"))
chk("la ficha del activo llama a `_avisos_del_campo`", _llama("core/inventory_ui.py", "_detalle", "_avisos_del_campo"))
_app = _src("app.py")
# ⚠️ por AST: el texto `_ROL in ("administrator", "field")` está TRES veces en app.py, y buscarlo no decía si el
# bloque del QR lo usaba (romper_v691 lo destapó: volver a «== "administrator"» seguía en verde)
_ifs_qr = [n for n in ast.walk(ast.parse(_app)) if isinstance(n, ast.If) and "_ROL" in ast.unparse(n.test)
           and "query_params.get('activo')" in ast.unparse(n)]
chk("el QR del CAMPO abre «🧰 Equipo» con su ficha (app.py)",
    any(ast.unparse(n.test) == "_ROL in ('administrator', 'field')" for n in _ifs_qr)
    and '("autogestion", "🧰 Equipo")' in _app and '_equipo_open' in _app, [ast.unparse(n.test) for n in _ifs_qr])
_hu = _src("core/home_ui.py")
chk("Self-service del campo tiene «My equipment» y lo enruta",
    '("🧰 Equipo", ":material/construction: My equipment")' in _hu and "render_equipo_campo(_usr, grupo)" in _hu
    and 'elif _sub == "🧰 Equipo":' in _hu)
chk("el aviso del emisor de la cotización usa `tiene_razon_social` (no `identidad()['legal']`)",
    "_CB.tiene_razon_social(grupo)" in _src("core/quotes_ui.py")
    and 'identidad(grupo).get("legal") or "").strip()' not in _src("core/quotes_ui.py"))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
