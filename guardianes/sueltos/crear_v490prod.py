# -*- coding: utf-8 -*-
import io, json, os, sys
AQUI = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir("C:/Users/diego/P1/survey_app"); sys.path.insert(0, ".")
import streamlit as st
G = "cliente1"
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "nombre": "Bobo", "grupo": G}
from core import timeclock as TC, ausencias as AU
U, N = "helper 2", "helper 2"
r = {}
r["in"] = TC.clock_in(N, "", "", grupo=G, tipo=TC.TIPO_GENERAL, usuario=U, in_ts="2026-09-15 07:00:00")
r["out"] = TC.clock_out(N, grupo=G, tipo=TC.TIPO_GENERAL, usuario=U, out_ts="2026-09-15 15:00:00")
ok, aid = AU.solicitar(G, U, N, "vacaciones", "2026-09-17", "2026-09-17", motivo="ZZ PRUEBA v490 - borrar")
r["solicitar"] = (ok, aid)
if ok:
    r["aprobar"] = AU.resolver(aid, True, "Admin2", nota="ZZ PRUEBA v490")
print(json.dumps(r, ensure_ascii=False, default=str, indent=1))
io.open(os.path.join(AQUI, "creado_v490prod.json"), "w", encoding="utf-8").write(json.dumps({"ausencia": aid if ok else None}))
