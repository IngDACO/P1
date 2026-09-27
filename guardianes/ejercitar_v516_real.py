# -*- coding: utf-8 -*-
"""v516 contra la HOJA REAL (método v344): foto → ejercitar → verificar LEYENDO →
restaurar → segunda foto.

⚠️ Un test con datos que yo invento no prueba nada: contra la hoja real salieron cuatro
fallos que veinte versiones de tests no vieron. Aquí se crea la hoja de verdad, se
escriben partes de verdad, se leen por el LOTE (que es como los lee la app, no como los
escribe este guion) y se borran comprobando que se fueron.

⚠️ Se respira entre llamadas: el techo son 60 lecturas/min con UNA cuenta de servicio, y
un 429 se disfraza de cualquier otra cosa (v377, v511).
"""
import os
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dacox", "nombre": "dacox",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("\n%s" % x)


def respira(s=1.2):
    time.sleep(s)


from core import daily_log as DL                                  # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402

GRUPO = "cliente1"
YO = "dacox"
PID = None          # la obra de prueba, creada abajo
CREADOS = []        # todo lo que haya que limpiar pase lo que pase


def foto():
    """Cuántas filas hay en cada hoja que toca esto. La foto de antes y la de después
    tienen que ser IDÉNTICAS o la prueba dejó basura."""
    H.invalidar(DL.SHEET)
    respira()
    return {"Projects": len(P.list_projects(GRUPO) or []),
            "DailyLogs": len(H.registros(DL.SHEET) or [])}


def limpia():
    """⚠️ Se llama SIEMPRE, incluso si algo revienta a la mitad: dejar basura en la hoja
    del cliente es peor que un guardián que falla (v511 — una limpieza que se rendía
    ante un 429 dejaba restos)."""
    if PID:
        for intento in range(3):
            try:
                P.delete_project(PID)
                break
            except Exception as e:
                print("   (limpieza intento %d: %s)" % (intento + 1, e))
                time.sleep(5)
    for lid in list(CREADOS):
        try:
            DL.borrar(lid, YO)
        except Exception:
            pass


ANTES = foto()
print("ANTES · Projects %d · DailyLogs %d" % (ANTES["Projects"], ANTES["DailyLogs"]))

try:
    # ── 1 ────────────────────────────────────────────────────────
    sec("1. Una obra de verdad, y su parte")
    _ok, PID = P.create_project(
        GRUPO, "ZZ PRUEBA v516 parte diario", "cliente de prueba", "",
        tipo=P.TIPO_INSTALACION, ns=6, creado_por=YO)
    chk("se crea la obra de prueba", _ok, PID)
    if not _ok:
        raise SystemExit(1)
    respira()

    _ok, LID = DL.crear(PID, GRUPO,
                        "Terminados los bedplates del 3 y el 4. Empezado el cableado "
                        "de hueco. Esperando los marcos de puerta de rellano.", YO)
    chk("se guarda el parte", _ok, LID)
    if _ok:
        CREADOS.append(LID)
    respira()

    # ── 2 ────────────────────────────────────────────────────────
    sec("2. ⚠️ La app lo VUELVE A VER (por el lote, que es como lee ella)")
    # Esta es la comprobación que importa: escribir y leerlo con el mismo objeto no
    # demuestra nada. Si la hoja no estuviera en el lote, aquí saldría CERO y todo lo
    # demás seguiría pareciendo correcto (v461, v507, v514).
    H.invalidar(DL.SHEET)
    DL._records_cached.clear()
    respira()
    _p = DL.partes(PID)
    chk("el parte se lee de vuelta por el lote", len(_p) == 1, len(_p))
    if _p:
        chk("...con su texto entero",
            _p[0].get("Text", "").startswith("Terminados los bedplates"),
            _p[0].get("Text", "")[:40])
        chk("...su autor", _p[0].get("Author") == YO, _p[0].get("Author"))
        chk("...su obra", str(_p[0].get("ProjectID")) == str(PID), _p[0].get("ProjectID"))
        chk("...y la hora puesta sola",
            len(str(_p[0].get("Created", ""))) >= 16, _p[0].get("Created"))

    # ── 3 ────────────────────────────────────────────────────────
    sec("3. Dos partes el mismo día: se añaden, no se pisan")
    _ok2, LID2 = DL.crear(PID, GRUPO, "Tambien monte el sky lock del 5.", YO)
    chk("se guarda el segundo", _ok2, LID2)
    if _ok2:
        CREADOS.append(LID2)
    respira()
    H.invalidar(DL.SHEET)
    DL._records_cached.clear()
    respira()
    _p = DL.partes(PID)
    chk("la obra tiene DOS partes", len(_p) == 2, len(_p))
    chk("...y siguen siendo UN día de corpus", DL.dias_cubiertos(PID) == 1,
        DL.dias_cubiertos(PID))
    chk("...el último escrito sale primero",
        _p and _p[0].get("ID") == LID2, [x.get("ID") for x in _p])

    # ── 4 ────────────────────────────────────────────────────────
    sec("4. Borrar el suyo, del día, sí")
    _ok3, _m = DL.borrar(LID2, YO)
    chk("se borra", _ok3, _m)
    if _ok3 and LID2 in CREADOS:
        CREADOS.remove(LID2)
    respira()
    H.invalidar(DL.SHEET)
    DL._records_cached.clear()
    respira()
    chk("...y la hoja se quedó con UNO", len(DL.partes(PID)) == 1, len(DL.partes(PID)))
    _ok4, _m4 = DL.borrar(LID, "otro_usuario")
    chk("el de otro NO se lo puede llevar", _ok4 is False, _m4)
    respira()

    # ── 5 ────────────────────────────────────────────────────────
    sec("5. ⚠️ Borrar la obra se lleva sus partes (el fallo de v514)")
    # ⚠️ NO se limpian a mano antes: mi propio ejercicio de v514 tapaba este fallo
    # haciéndolo por su cuenta, y entonces no verificaba nada — arreglaba.
    _okd, _md = P.delete_project(PID)
    chk("se borra la obra", _okd, _md)
    if _okd:
        PID = None
        CREADOS.clear()
    respira(3)
    H.invalidar(DL.SHEET)
    DL._records_cached.clear()
    respira()
    _restos = [r for r in (H.registros(DL.SHEET) or [])
               if str(r.get("Text", "")).startswith("Terminados los bedplates")]
    chk("...y NO quedan partes huérfanos", not _restos, _restos)

finally:
    limpia()

# ── Foto final ───────────────────────────────────────────────────
respira(2)
DESPUES = foto()
print("")
print("DESPUES · Projects %d · DailyLogs %d" % (DESPUES["Projects"], DESPUES["DailyLogs"]))
chk("⚠️ la hoja quedó EXACTAMENTE como estaba", DESPUES == ANTES,
    "antes=%s despues=%s" % (ANTES, DESPUES))

print("")
if fallos:
    print("FALLOS: %d de %d" % (len(fallos), n_ok + len(fallos)))
    sys.exit(1)
print("PARTE DIARIO v516, HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
