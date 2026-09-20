# -*- coding: utf-8 -*-
"""Smoke de F5b: EJECUTAR los mensajes de los 6 módulos traducidos.

⚠️ Importar no ejecuta (v378). Y en esta tanda hubo dos fallos que SOLO se ven
llamando: un `t()` congelado dentro de `ausencias.TIPOS` y un `AU.nombre_tipo(k)`
con la variable equivocada (el bucle usa `_tp`) — un NameError que habría reventado
«Mis ausencias» al abrirla.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "dmoreno"}

ok = True


def chk(t_, cond, det=""):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det else ""))


from core import ausencias as AU, catalogo as CAT, clientes as CL   # noqa: E402
from core import orders as OR, projects as P, quotes as Q           # noqa: E402

# ── ausencias: el helper nuevo y los tipos ──
chk("ausencias.nombre_tipo se EJECUTA",
    AU.nombre_tipo(AU.VACACIONES) == "Annual leave", AU.nombre_tipo(AU.VACACIONES))
chk("...y con un tipo desconocido devuelve lo que le llega",
    AU.nombre_tipo("zzz") == "zzz")
chk("las CLAVES de TIPOS siguen siendo el dato",
    set(AU.TIPOS) == {"vacaciones", "enfermedad", "libre"}, str(set(AU.TIPOS)))
chk("...y `estado_roster` también (se guarda en el tablero)",
    AU.TIPOS[AU.VACACIONES]["estado_roster"] == "LEAVE")
# firma REAL: (grupo, usuario, nombre, tipo, desde, hasta, motivo="")
_o, _m = AU.solicitar("cliente1", "zzz", "ZZZ", "libre", "2026-13-99", "2026-13-99")
chk("ausencias.solicitar (fechas malas) en inglés",
    "could not be read" in str(_m).lower(), str(_m))

# ── quotes / projects: rutas de validación, sin escribir ──
# firma REAL: (grupo, cliente_id, cliente_nombre, lineas, ...)
_o, _m = Q.crear("cliente1", "CLI-0001", "zzz", [], creado_por="zzz")
chk("quotes.crear sin líneas → inglés", "at least one line" in str(_m).lower(), str(_m))
_o, _m = Q.set_estado("COT-NO-EXISTE", Q.ACEPTADA)
chk("quotes.set_estado (id inexistente) → inglés",
    "not found" in str(_m).lower(), str(_m))
_o, _m = Q.set_estado("COT-0001", "estado-que-no-existe")
chk("quotes.set_estado (estado inválido) → inglés",
    "invalid status" in str(_m).lower(), str(_m))
_o, _m = P.update_project("PRJ-NO-EXISTE", {"Nombre": "x"})
chk("projects.update_project (id inexistente) → inglés",
    "not found" in str(_m).lower(), str(_m))
# ⚠️ Este mensaje solo se alcanza con un proyecto que EXISTA: con la demo vacía,
# `update_project` corta antes con «not found» y el chequeo daba un rojo que no era
# un fallo del código, sino falta de datos.
_algun = next((str(p.get("ID")) for p in P.list_projects(incluir_archivados=True,
                                                         incluir_internos=True)), None)
if _algun:
    _o, _m = P.update_project(_algun, {"ColumnaQueNoExiste": "x"})
    chk("projects.update_project (campo desconocido) → inglés",
        "no recognised field" in str(_m).lower(), str(_m))
else:
    print("  --  (sin proyectos: no se puede comprobar el mensaje de campo desconocido)")

# ── orders / catalogo / clientes ──
# firma REAL: (pid, grupo, proveedor, valor, ...)
_o, _m = OR.crear("PRJ-0001", "cliente1", "prov", 0, creado_por="zzz")
chk("orders.crear (valor 0) → inglés", "greater than 0" in str(_m).lower(), str(_m))
_o, _m = CAT.crear("cliente1", "", tipo="producto", costo_unit=1)
chk("catalogo.crear (sin nombre) → inglés", "a name" in str(_m).lower(), str(_m))
_o, _m = CAT.crear("cliente1", "x", tipo="tipo-raro", costo_unit=1)
chk("catalogo.crear (tipo inválido) → inglés",
    "invalid type" in str(_m).lower(), str(_m))
# ⚠️ se llama `create_cliente`, no `crear` (regla v135: mirar el nombre real)
_o, _m = CL.create_cliente("cliente1", "")
chk("clientes.crear (sin nombre) → inglés", "required" in str(_m).lower(), str(_m))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
