# -*- coding: utf-8 -*-
"""v692 · Ciclo 5 → mejoras 4/4, los ASISTENTES (22/11):
- H22 · el recordatorio del idioma va también con la PREGUNTA: iba solo detrás de los resultados de una herramienta, y
  el Field assistant contestó EN ESPAÑOL a una pregunta en inglés cuando no consultó nada;
- H20 · la oficina consulta las cotizaciones (`get_quotes`, por trato) y el inventario (`get_assets`), y el campo el
  equipo que tiene a su cargo (`get_my_equipment`); la bandeja (y con ella el resumen del día) suma lo de ventas y equipo.

Nada sale a la red: `_conversar` sustituido (se mira lo que se mandaría al modelo), datos falsos y sustitutos.
"""
import json
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


import streamlit as st                                                     # noqa: E402
from core import chat_agent as CA, chat_tools as CT                        # noqa: E402
from core import quotes as Q, inventory as INV, admin_digest as AD         # noqa: E402
from core import manuals, clock                                            # noqa: E402

HOY = date(2026, 11, 22)

print("1. El idioma, también con la pregunta (H22)")
_VISTO = []


def _conv(client, system, messages, herramientas, ctx):
    _VISTO.append({"messages": messages, "tools": [h["name"] for h in herramientas or []], "ctx": ctx})
    return "ok"


_d = [_sustituir(CA, _conversar=_conv), _sustituir(manuals, is_available=lambda: False)]
try:
    st.session_state["auth"] = {"usuario": "campo000", "nombre": "hjg,ujgjg", "rol": "field", "grupo": "G"}
    CA.get_chat_response("Do I have any company tool signed out to me right now? When do I return it?", [], None, None,
                         rol="field", grupo="G", usuario="campo000", nombre="hjg,ujgjg")
    _m = _VISTO[-1]["messages"][-1]
    _bl = _m["content"] if isinstance(_m["content"], list) else []
    chk("el campo: la pregunta va con el recordatorio detrás («in English»), aunque no consulte nada",
        len(_bl) == 2 and _bl[0]["text"].startswith("Do I have any company tool") and "in English" in _bl[1]["text"]
        and "from the first word" in _bl[1]["text"], _m)
    chk("…y la regla de responder solo a eso, la del campo (v687)", "Answer only that question" in _bl[1]["text"])
    CA.get_chat_response("¿Qué equipos tiene hjg,ujgjg y cuándo los devuelve?", [], None, None,
                         rol="administrator", grupo="G", usuario="Admin2", nombre="Bobo")
    _bl = _VISTO[-1]["messages"][-1]["content"]
    chk("la oficina en español: «in Spanish»", isinstance(_bl, list) and "in Spanish" in _bl[-1]["text"], _bl)
    CA.get_chat_response("What is wrong with this hook?", [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello"}],
                         None, None, rol="field", grupo="G", usuario="campo000", nombre="hjg,ujgjg", fotos=["QUJD"])
    _bl = _VISTO[-1]["messages"][-1]["content"]
    chk("con una foto: imagen, pregunta y recordatorio, en ese orden",
        [b["type"] for b in _bl] == ["image", "text", "text"] and "in English" in _bl[-1]["text"], _bl)
    chk("…y el historial no se toca (el recordatorio solo va en ESTA pregunta)",
        _VISTO[-1]["messages"][0] == {"role": "user", "content": "hi"})
    CA.get_chat_response("hello", [], None, None, rol="owner", grupo="", usuario="", nombre="")
    _c = _VISTO[-1]["messages"][-1]["content"]
    chk("sin herramientas (nadie identificado) va como antes, sin recordatorio", _c == "hello", _c)
finally:
    for x in _d:
        x()

print("2. Quién tiene qué consultas (H20)")
_ofi = [h["name"] for h in CT.definiciones("administrator", "Admin2")]
_cam = [h["name"] for h in CT.definiciones("field", "campo000")]
chk("la oficina tiene get_quotes y get_assets", "get_quotes" in _ofi and "get_assets" in _ofi, _ofi)
chk("el campo tiene get_my_equipment, y NI get_quotes NI get_assets", "get_my_equipment" in _cam
    and "get_quotes" not in _cam and "get_assets" not in _cam, _cam)
_r, _e = CT.ejecutar("get_quotes", {}, {"rol": "field", "usuario": "campo000", "grupo": "G"})
chk("…y si el modelo del campo la pide igual, se niega («Unknown tool»)", _e and "Unknown tool" in _r, _r)
_g = CA._PERSONA
chk("la guía de la oficina dice que ve las cotizaciones y el inventario",
    "las cotizaciones, el inventario" in _g["office_tools"], _g["office_tools"][:400])
chk("la del campo, el equipo que tiene a su cargo", "el equipo de la empresa que tiene a su cargo" in _g["field_tools"])

print("3. get_quotes: por TRATO, a quién llamar y por qué se perdió")
_L = [{"concepto": "Panel", "cantidad": 1, "costo_total": 100.0, "precio_total": 120.0}]


def _q(cid, num, ver, st_, tot, valid="2026-12-17", pid="", reason="", cli="C5 — Bayview"):
    return {"ID": cid, "Group": "G", "ClientID": "CLI-1", "ClientName": cli, "Number": num, "Date": "2026-11-10",
            "ValidUntil": valid, "LinesJSON": json.dumps(_L), "Total": str(tot), "Status": st_, "ProjectID": pid,
            "Version": str(ver), "RejectReason": reason}


_QS = [_q("C81", "0008", 1, "sent", 12170.4), _q("C82", "0008", 2, "accepted", 12170.4, pid="PRJ-0046"),
       _q("C31", "0003", 1, "sent", 2858.46, valid="2026-11-18", cli="Inner West Strata"),
       _q("C91", "0009", 1, "rejected", 500.0, reason="price — too high", cli="Meridian"),
       _q("C11", "0011", 1, "sent", 900.0, valid="2026-11-25", cli="Meridian")]
_d = [_sustituir(Q, _records=lambda: [dict(x) for x in _QS]), _sustituir(clock, today=lambda *a, **k: HOY)]
try:
    Q.resumen.clear()
    _r = CT._cotizaciones({}, {"grupo": "G"})
    chk("las cifras de Quotes: en la calle 0003 + 0011 = 3.758,46, ganado 12.170,40, conversión 50 %",
        _r["company_totals"] == {"out_with_clients_inc_tax": 3758.46, "won_inc_tax": 12170.4, "conversion_pct": 50.0,
                                 "superseded_versions": 1}, _r["company_totals"])
    _esp = {x["number"]: x for x in _r["awaiting_reply"]}
    chk("esperando respuesta: la 0011 (le quedan 3 días) y la 0003 (vencida hace 4); NO la 0008 v1 (sustituida)",
        set(_esp) == {"0011", "0003"} and _esp["0011"]["days_left"] == 3 and _esp["0003"]["expired_days_ago"] == 4, _esp)
    chk("a quién llamar ya: la 0003 y la 0011", [x["number"] for x in _r["to_chase_now"]] == ["0003", "0011"],
        _r["to_chase_now"])
    chk("ganada: la 0008 v2 con su obra y «2 versions»", _r["won"] == [dict(_r["won"][0], number="0008", version=2,
                                                                            versions=2, project_id="PRJ-0046")]
        if _r["won"] else False, _r["won"])
    chk("perdida: la 0009 con su motivo «price (too high)»", _r["lost"][0]["reject_reason"] == "price (too high)",
        _r["lost"])
    _r = CT._cotizaciones({"client": "meridian"}, {"grupo": "G"})
    chk("filtrar por cliente («meridian»): solo sus tratos", {x["number"] for x in _r["awaiting_reply"] + _r["lost"]}
        == {"0011", "0009"} and not _r["won"], _r)
finally:
    for x in _d:
        x()

print("4. get_assets y get_my_equipment (H20)")


def _act(aid, nombre, **kw):
    r = {"ID": aid, "Group": "G", "Name": nombre, "Category": "Tool", "Status": "available", "Active": "SI",
         "LocationType": "warehouse", "LocationRef": "Main store", "AssignedTo": "", "ReturnDate": "", "NextService": ""}
    r.update(kw)
    return r


_AS = [_act("ACT-6", "Chain hoist", Status="in use", LocationType="project", LocationRef="PRJ-0045", AssignedTo="campo000",
            ReturnDate="2026-11-25"),
       _act("ACT-7", "Drill", Status="in use", LocationType="user", LocationRef="otro", AssignedTo="otro",
            ReturnDate="2026-11-20", NextService="2026-11-01"),
       _act("ACT-8", "Welder", Status="maintenance", LocationType="under repair")]
_AV = [{"id": "MOV-9", "aid": "ACT-8", "activo": "Welder", "usuario": "campo000", "tipo": "problem", "nota": "cable cut",
        "fecha": "2026-11-21 08:00:00"}]
_d = [_sustituir(INV, list_activos=lambda g, incluir_baja=False: [dict(a) for a in _AS],
                 avisos_pendientes=lambda g, aid=None: list(_AV),
                 alertas=lambda g: [{"tipo": "no_devuelto", "activo": "Drill", "id": "ACT-7", "dias": 2, "usuario": "otro"}],
                 ubic_ref_label=lambda r: {"PRJ-0045": "C4 — Lift 4"}.get(str(r), str(r))),
      _sustituir(AD, nombres_usuarios=lambda: {"campo000": "hjg,ujgjg", "otro": "Otro"}),
      _sustituir(clock, today=lambda *a, **k: HOY)]
try:
    _r = CT._activos({}, {"grupo": "G"})
    _f = {x["id"]: x for x in _r["out_of_the_store"]}
    chk("fuera: el polipasto en «project: C4 — Lift 4» con hjg,ujgjg, vuelve el 25/11 (3 días)",
        _f["ACT-6"]["where"] == "project: C4 — Lift 4" and _f["ACT-6"]["with"] == "hjg,ujgjg"
        and _f["ACT-6"]["due_back"] == "25/11/2026" and _f["ACT-6"]["days_left"] == 3, _f.get("ACT-6"))
    chk("…y el taladro con «Otro» (la PERSONA, no la cuenta), 2 días tarde",
        _f["ACT-7"]["where"] == "user: Otro" and _f["ACT-7"]["days_late"] == 2
        and [x["id"] for x in _r["not_returned_on_time"]] == ["ACT-7"], _f.get("ACT-7"))
    chk("revisión vencida: el taladro; en mantenimiento: el soldador",
        [x["id"] for x in _r["service_overdue"]] == ["ACT-7"] and [x["id"] for x in _r["under_maintenance"]] == ["ACT-8"])
    chk("lo que dijo el campo: hjg,ujgjg, un problema con el soldador («cable cut»)",
        _r["notices_from_the_field"] == [{"asset": "Welder", "asset_id": "ACT-8", "who": "hjg,ujgjg",
                                          "says": "there is a problem", "note": "cable cut", "date": "21/11/2026"}],
        _r["notices_from_the_field"])
    chk("…con el ID de su obra (examen: sin él dijo «The record doesn't link this hoist to PRJ-0045»)",
        _f["ACT-6"].get("project_id") == "PRJ-0045" and "project_id" not in _f["ACT-7"], _f)
    _r = CT._activos({"person": "hjg"}, {"grupo": "G"})
    chk("por PERSONA («hjg»): lo que tiene hjg,ujgjg (examen: la buscó como si fuera un equipo)",
        [x["id"] for x in _r["matching_assets"]] == ["ACT-6"], _r.get("matching_assets"))
    _r = CT._activos({"asset": "act-6"}, {"grupo": "G"})
    chk("buscar «act-6»: solo el polipasto", [x["id"] for x in _r["matching_assets"]] == ["ACT-6"]
        and not _r["notices_from_the_field"], _r)
    _m = CT._mi_equipo({}, {"grupo": "G", "usuario": "campo000"})
    chk("el campo (campo000): solo SU polipasto, y su aviso pendiente del soldador",
        [x["id"] for x in _m["signed_out_to_you"]] == ["ACT-6"]
        and _m["your_notices_waiting_for_the_office"] == [{"asset": "Welder", "you_said": "a problem", "date": "21/11/2026"}],
        _m)
    _d2 = _sustituir(Q, seguimiento=lambda g: [{"id": "C31", "numero": "0003", "cliente": "Inner West", "vencida": 4,
                                                "total": 1, "orden": 0}])
    _b = CT._pendiente_ventas_y_equipo("G")
    _d2()
    chk("la bandeja suma la 0003 por seguir, el aviso del soldador y el taladro sin devolver",
        _b["quotes_to_chase"] == [{"number": "0003", "client": "Inner West", "expired_days_ago": 4}]
        and _b["equipment_notices_from_the_field"][0]["asset"] == "Welder"
        and _b["equipment_not_returned"] == [{"asset": "Drill", "days_late": 2, "who": "Otro"}], _b)
finally:
    for x in _d:
        x()

import ast                                                                  # noqa: E402
_src = open(os.path.join(RAIZ, "core", "chat_tools.py"), encoding="utf-8").read()
_fb = next(n for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.FunctionDef) and n.name == "_bandejas")
chk("`_bandejas` (la bandeja y el resumen del día) incluye `_pendiente_ventas_y_equipo(g)`",
    any(isinstance(c, ast.Call) and ast.unparse(c.func) == "_pendiente_ventas_y_equipo" for c in ast.walk(_fb)))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
