# -*- coding: utf-8 -*-
"""Cadena del dinero de punta a punta, contra la HOJA REAL.

    catálogo → cotización → aceptar → OBRA → avance → reclamación → PDF
                                        ├→ variación → mueve el contrato
                                        ├→ 100% → liberación de retención → PDF
                                        ├→ cotizar leyendo el plano (v509)
                                        └→ expediente de entrega (v506)

## Por qué existe

v506, v507-v508, v509 y v510 se verificaron cada una por su lado, pero **la cadena
entera nunca se había recorrido con datos reales**: el catálogo del cliente de prueba
estaba vacío, así que no había contrato contra el que reclamar, ni precios que proponer,
ni expediente que cruzar. Cada eslabón verde no dice nada del eslabón siguiente.

## Cómo se usa

    python ejercitar_e2e_dinero.py            # limpia restos, corre la cadena, LA DEJA
    python ejercitar_e2e_dinero.py --limpiar  # solo borra lo de la prueba

⚠️ **Re-ejecutable a propósito**: empieza borrando sus propios restos, así que repetir
el paso que provocó un fallo es volver a lanzarlo. Sin eso, «arreglado» sería una
opinión (el método que pidió el usuario: corregir, repetir, garantizar).

⚠️ **Todo lo que crea lleva la marca `PRUEBA E2E`** y se apunta en un registro EN DISCO
conforme se crea, no reconstruido al final: si el guion se cae a mitad, el registro ya
existe y la limpieza sigue siendo posible. Una limpieza «por aproximación» sobre la hoja
de un cliente es justo lo que no se puede permitir.

⚠️ **No toca NADA que no haya creado él.** Las obras y actividades que ya estaban se
identifican por la foto previa y quedan fuera de cualquier borrado.
"""
import json
import os
import sys
import time
from io import BytesIO

from pypdf import PdfReader

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}
import gspread                                                    # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402

GRUPO = "cliente1"
MARCA = "PRUEBA E2E"
QUIEN = "Bobo"
REGISTRO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_e2e_registro.json")

fallos, n_ok = [], 0
reg = {"catalogo": [], "cotizaciones": [], "proyectos": [], "reclamaciones": [],
       "variaciones": [], "documentos": []}


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, d=""):
    fallos.append(q)
    print("  *** FALLO  %s" % q + ("  -> %s" % d if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, "%r != %r" % (real, esp))


def respira(s=18, por_que=""):
    """Espera antes de la siguiente tanda de lecturas.

    ⚠️ El techo es de **60 lecturas por minuto** para toda la cuenta de servicio, y esta
    cadena lee mucho: la primera corrida se comió la cuota y el 429 se disfrazó de
    fallos que no existían —la obra «al 0%», una reclamación «sin configurar»—. Es el
    error de v377 y de v399 otra vez: amontonar lecturas y leer un rojo falso.
    """
    print("   (pausa %ds%s)" % (s, " — " + por_que if por_que else ""))
    time.sleep(s)


def apunta(clave, valor):
    """⚠️ Al disco EN EL ACTO. Un registro que solo vive en memoria se pierde con la
    excepción que lo hacía falta."""
    if valor and valor not in reg[clave]:
        reg[clave].append(valor)
        with open(REGISTRO, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=1)


def _gc(escribir=False):
    sc = ["https://www.googleapis.com/auth/spreadsheets"] if escribir else \
         ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    cr = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]),
                                               scopes=sc)
    gc = gspread.authorize(cr)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def borrar_donde(hoja, pred, etq="", intentos=4):
    """Borra las filas que cumplen `pred(fila, cabecera)`. Devuelve cuántas.

    ⚠️ **Reintenta.** Una limpieza que se rinde ante un 429 deja basura en la hoja de un
    cliente, y peor: la corrida siguiente la encuentra y cree que sus propias altas se
    duplicaron. Paso exactamente eso —tres hojas sin limpiar y ocho artículos donde
    debía haber cinco—. El borrado es lo ÚLTIMO que puede permitirse fallar en silencio.
    """
    for n in range(intentos):
        try:
            lb = _gc(escribir=True)
            if hoja not in {w.title for w in lb.worksheets()}:
                return 0
            ws = lb.worksheet(hoja)
            v = ws.get_all_values()
            if not v:
                return 0
            cab = v[0]
            ns = [i for i, f in enumerate(v[1:], start=2) if f and pred(f, cab)]
            for i in sorted(ns, reverse=True):
                ws.delete_rows(i)
            if ns:
                print("   %-16s %d fila(s) %s" % (hoja, len(ns), etq))
            return len(ns)
        except Exception as e:
            if n + 1 >= intentos:
                print("   *** no se pudo limpiar %s tras %d intentos: %r"
                      % (hoja, intentos, e))
                fallos.append("limpieza de %s" % hoja)
                return 0
            print("   (%s: reintento %d/%d en 25s — %s)"
                  % (hoja, n + 1, intentos - 1, str(e)[:60]))
            time.sleep(25)
    return 0


def _col(f, cab, nombre):
    try:
        return f[cab.index(nombre)]
    except Exception:
        return ""


def limpiar(ruidoso=True):
    """Borra TODO lo de la prueba. Por marca y por los IDs del registro.

    ⚠️ Por las dos vías a propósito: la marca coge lo que se creó aunque el registro se
    haya perdido, y el registro coge lo que el código no marcó (un proyecto creado por
    `aceptar_y_crear_proyecto` lleva el nombre que le demos, pero sus ACTIVIDADES no
    llevan marca ninguna — cuelgan del proyecto).
    """
    if ruidoso:
        print("\n── limpieza ──")
    pr = {}
    try:
        with open(REGISTRO, encoding="utf-8") as f:
            pr = json.load(f)
    except Exception:
        pr = {}
    pids = set(pr.get("proyectos", [])) | set(reg["proyectos"])

    # 1) lo que cuelga de los proyectos de prueba (por ID, no por marca)
    for h, campo in (("Claims", "ProjectID"), ("Variations", "ProjectID"),
                     ("Activities", "ProjectID"), ("Documents", "ProyectoID"),
                     ("Invoices", "ProjectID"), ("PurchaseOrders", "ProjectID")):
        if pids:
            borrar_donde(h, lambda f, c: _col(f, c, campo) in pids, "(obras de prueba)")
    # 2) los propios proyectos: por ID y, por si acaso, por nombre marcado
    borrar_donde("Projects", lambda f, c: (f[0] in pids or MARCA in _col(f, c, "Nombre")
                                           or MARCA in _col(f, c, "Name")), "(obras)")
    # 3) cotizaciones y catálogo: por marca en el nombre/cliente
    borrar_donde("Quotes", lambda f, c: (f[0] in set(pr.get("cotizaciones", []))
                                         or MARCA in _col(f, c, "ClientName")), "(cotizaciones)")
    borrar_donde("Catalogue", lambda f, c: MARCA in _col(f, c, "Name"), "(catalogo)")
    try:
        os.remove(REGISTRO)
    except Exception:
        pass
    for k in reg:
        reg[k] = []


if "--limpiar" in sys.argv:
    limpiar()
    print("\nlimpieza terminada" + (" CON FALLOS" if fallos else ""))
    sys.exit(1 if fallos else 0)


# ═══════════════════════════════════════════════════════════════════
print("=" * 72)
print("CADENA DEL DINERO — %s" % MARCA)
print("=" * 72)
print("\n[0] se borran restos de una corrida anterior")
limpiar(ruidoso=False)
# ⚠️ Si la limpieza no pudo con alguna hoja, SE PARA. Seguir significaria crear encima
# de restos: la corrida anterior acabo con ocho articulos donde debia haber cinco y un
# rojo que no era un fallo del producto, sino basura mia.
if fallos:
    print("\n*** la limpieza inicial fallo: se aborta antes de crear nada encima")
    for f in fallos:
        print("  - " + f)
    sys.exit(2)

from core import catalogo as CAT                                  # noqa: E402
from core import claim_pdf as PDFC                                # noqa: E402
from core import claims as CL                                     # noqa: E402
from core import projects as P                                    # noqa: E402
from core import quote_from_plan as QP                            # noqa: E402
from core import quotes as Q                                      # noqa: E402

for _m in (CAT, Q, P, CL):
    try:
        _m._invalidate()
    except Exception:
        pass

# ═════ 1 · el catálogo ══════════════════════════════════════════════════════
# ⚠️ La limpieza de arriba lee SEIS hojas enteras y lista el libro. Encadenar las altas
# justo detras se comio la cuota y dos articulos no se crearon — con el agravante de que
# el error decia «Google Sheets is not configured», que es falso.
respira(30, "la limpieza acaba de leer seis hojas")
print("\n[1] catalogo de prueba")
ITEMS = [
    # (nombre, tipo, costo, horas, tarifa, regla de cantidad)
    ("Site set-up and mobilisation", CAT.PRODUCTO, 1800, 0, 0, QP.FIJA),
    ("Landing door assembly", CAT.PRODUCTO, 950, 0, 0, QP.POR_PARADA),
    ("Inter-floor wiring loom", CAT.PRODUCTO, 140, 0, 0, QP.POR_PARADA_MENOS_1),
    ("Guide rail set", CAT.PRODUCTO, 3200, 0, 0, QP.MANUAL),
    ("Installation labour", CAT.SERVICIO, 0, 120, 85, QP.MANUAL),
]
for nombre, tipo, costo, horas, tarifa, regla in ITEMS:
    _ok, _cid = CAT.crear(GRUPO, "%s %s" % (MARCA, nombre), tipo,
                          costo_unit=costo, horas_est=horas, tarifa_hora=tarifa,
                          descripcion=nombre, categoria="Installation",
                          creado_por=QUIEN, qty_rule=regla)
    if _ok:
        apunta("catalogo", _cid)
    else:
        fallo("no se pudo crear %r" % nombre, _cid)
CAT._invalidate()
_mios = [i for i in (CAT.list_items(GRUPO) or []) if MARCA in str(i.get("Name", ""))]
ck("los 5 articulos estan en el catalogo", len(_mios), 5)
# ⚠️ Si el catalogo no esta completo, SE PARA. La corrida anterior siguio con 3 de 5 y
# escupio cuatro rojos mas —«hay 5 lineas», «propone las 3 reglas», «la puerta va NS
# veces»— que no eran fallos distintos: eran el MISMO fallo repetido aguas abajo. Un
# test que continua con la precondicion rota fabrica ruido que tapa la senal.
if len(_mios) != len(ITEMS):
    print("\n*** el catalogo no quedo completo: se aborta para no encadenar rojos falsos")
    limpiar()
    sys.exit(1)
ck("...y el servicio cuesta horas x tarifa",
   CAT.costo_de(next((i for i in _mios if i.get("Type") == CAT.SERVICIO), {}), 1),
   10200.0)

# ═════ 2 · la cotización ════════════════════════════════════════════════════
print("\n[2] cotizacion desde el catalogo")
NS = 8
CANT = {"Site set-up and mobilisation": 1, "Landing door assembly": NS,
        "Inter-floor wiring loom": NS - 1, "Guide rail set": 1,
        "Installation labour": 1}
_lineas = []
for it in _mios:
    _n = str(it.get("Description", ""))
    _lineas.append(Q.linea_de(it, CANT.get(_n, 1), margen_pct=25.0))
_tot = Q.totales(_lineas, 10.0)
print("   subtotal %.2f · impuesto %.2f · total %.2f · margen %.1f%%"
      % (_tot["subtotal"], _tot["impuesto"], _tot["total"], _tot["margen_pct"]))
ck("hay 5 lineas", len(_lineas), 5)
ck("el subtotal no es cero", _tot["subtotal"] > 0, True)
_okq, _cot = Q.crear(GRUPO, "", "%s Meridian Constructions" % MARCA, _lineas,
                     impuesto_pct=10.0, nota="Cadena de prueba", creado_por=QUIEN)
ck("la cotizacion se guarda", _okq, True)
if not _okq:
    print("   -> %s" % _cot)
    limpiar()
    sys.exit(1)
apunta("cotizaciones", _cot)
print("   %s" % _cot)

# ═════ 3 · aceptarla crea la obra ═══════════════════════════════════════════
print("\n[3] aceptar la cotizacion")
_oka, _pid = Q.aceptar_y_crear_proyecto(_cot, nombre="%s Tower A Lift 2" % MARCA,
                                        tipo="Installation", ns=NS,
                                        ubicacion="100 Barangaroo Ave, Sydney",
                                        creado_por=QUIEN)
ck("se crea la obra", _oka, True)
if not _oka:
    print("   -> %s" % _pid)
    limpiar()
    sys.exit(1)
apunta("proyectos", _pid)
print("   obra %s" % _pid)
Q._invalidate()
P._invalidate()
_prj = P.get_project(_pid) or {}
_acts = P.list_activities(_pid) or []
ck("la obra trae cronograma", len(_acts) > 1, True)
# ⚠️ La clave se DERIVA de la cabecera real, no se escribe a mano. La primera version
# preguntaba por «Presupuesto» y la migracion a ingles (v441-v452) la renombro a
# «Budget»: el chequeo daba 0.0 y acusaba a codigo sano. Mirar el codigo acusado antes
# de «arreglarlo» (v385) es lo que evito parchear algo que funcionaba.
_K_PRESU = next((h for h in P.PROJECTS_HEADERS if h in ("Budget", "Presupuesto")), "Budget")
ck("el presupuesto es el COSTO, no el precio",
   round(float(_prj.get(_K_PRESU) or 0), 2), round(_tot["costo"], 2))

# ═════ 4 · el contrato que ve el cobro de obra ══════════════════════════════
print("\n[4] el contrato (v507)")
CL._invalidate()
_c, _cid_q = CL.contrato(_pid)
ck("el contrato sale de la cotizacion aceptada", _cid_q, _cot)
ck("...y vale el SUBTOTAL", _c, round(_tot["subtotal"], 2))

# ═════ 5 · el avance, que es lo que se reclama ══════════════════════════════
respira(25, "el alta de la obra ha leido mucho")
print("\n[5] el campo reporta avance")
_ordenes = sorted(int(float(a.get("Orden") or a.get("Order") or 0)) for a in _acts)
_mitad = _ordenes[:max(1, len(_ordenes) // 2)]
_okp, _msgp = P.save_field_progress(_pid, [{"orden": o, "avance": 100} for o in _mitad])
ck("el avance se guarda", _okp, True)
P._invalidate()
_prj = P.get_project(_pid) or {}
_av = float(_prj.get("Progress") or _prj.get("Avance") or 0)
print("   %d de %d actividades al 100%% -> obra al %.1f%%" % (len(_mitad), len(_acts), _av))
ck("la obra avanza", _av > 0, True)
ck("...y no llega al 100 todavia", _av < 100, True)

# ═════ 6 · la reclamación y su PDF ══════════════════════════════════════════
respira(25)
print("\n[6] reclamacion de avance (v507) + PDF (v510)")
CL._invalidate()
_d = CL.calcular(_pid, GRUPO, None, _prj)
print("   valor %.2f · avance %.1f%% · hecho %.2f · bruto %.2f · retencion %.2f · neto %.2f"
      % (_d["valor"], _d["pct"], _d["hecho"], _d["bruto"], _d["retencion"], _d["neto"]))
ck("hay contrato contra el que reclamar", _d["hay_contrato"], True)
ck("el valor es el contrato (aun sin variaciones)", _d["valor"], _d["contrato"])
ck("el bruto sale del avance real", round(_d["valor"] * _av / 100.0, 2), _d["hecho"])
_okr, _msgr = CL.crear_reclamacion(_pid, GRUPO, None, "", "Primera", QUIEN, _prj)
ck("la reclamacion se emite", _okr, True)
print("   -> %s" % _msgr)
CL._invalidate()
_recs = CL.reclamaciones(_pid)
ck("...y se lee de vuelta", len(_recs), 1)
if _recs:
    apunta("reclamaciones", str(_recs[0].get("ID", "")))
    _pdf = PDFC.generate_claim_pdf(_recs[0], CL.variaciones(_pid), {}, GRUPO, _prj,
                                   CL.retenido(_pid))
    ck("el PDF se genera", _pdf[:5], b"%PDF-")
    from io import BytesIO
    from pypdf import PdfReader
    _tx = "\n".join((p.extract_text() or "") for p in PdfReader(BytesIO(_pdf)).pages)
    ck("⚠️ la sonda sabe leerlo", "PROGRESS CLAIM" in _tx.upper(), True)
    ck("lleva el nombre de la obra", "Tower A" in _tx, True)

# ═════ 7 · una variación mueve el contrato ══════════════════════════════════
respira(25)
print("\n[7] variacion (v507)")
_okv, _vid = CL.crear_variacion(_pid, GRUPO, "Extra landing door level 7", 7400,
                                "", QUIEN)
ck("la variacion se crea", _okv, True)
CL._invalidate()
_vs = CL.variaciones(_pid)
if _vs:
    apunta("variaciones", str(_vs[0].get("ID", "")))
_d2 = CL.calcular(_pid, GRUPO, None, _prj)
ck("⚠️ PROPUESTA no es dinero: el valor no se mueve", _d2["valor"], _d["valor"])
_okd, _msgd = CL.decidir_variacion(_vs[0].get("ID"), True, QUIEN, GRUPO)
ck("se aprueba", _okd, True)
CL._invalidate()
_d3 = CL.calcular(_pid, GRUPO, None, _prj)
ck("⚠️ aprobada SI mueve el valor", _d3["valor"], round(_d["valor"] + 7400, 2))
print("   valor %.2f -> %.2f" % (_d["valor"], _d3["valor"]))
ck("...y ya hay algo nuevo que reclamar", _d3["bruto"] > 0, True)

# ═════ 8 · obra terminada → liberación de retención ═════════════════════════
respira(30, "el 100% reescribe todas las actividades")
print("\n[8] obra al 100% y liberacion (v510)")
P.save_field_progress(_pid, [{"orden": o, "avance": 100} for o in _ordenes])
P._invalidate()
CL._invalidate()
_prj = P.get_project(_pid) or {}
_av2 = float(_prj.get("Progress") or 0)
ck("la obra queda al 100%", _av2, 100.0)
CL.crear_reclamacion(_pid, GRUPO, None, "", "Final", QUIEN, _prj)
CL._invalidate()
_ret = CL.retenido(_pid)
print("   retenido %.2f · liberado %.2f · pendiente %.2f"
      % (_ret["retenido"], _ret["liberado"], _ret["pendiente"]))
ck("se ha retenido algo", _ret["retenido"] > 0, True)
_okl, _motl = CL.puede_liberar(_pid, _prj)
ck("con la obra terminada se puede liberar", _okl, True)
_mitad_ret = round(_ret["pendiente"] / 2.0, 2)
_okL, _msgL = CL.crear_liberacion(_pid, GRUPO, _mitad_ret, "Practical completion",
                                  QUIEN, _prj)
ck("la liberacion parcial se emite", _okL, True)
print("   -> %s" % _msgL)
CL._invalidate()
_ret2 = CL.retenido(_pid)
ck("⚠️ el pendiente baja justo la mitad", _ret2["pendiente"],
   round(_ret["retenido"] - _mitad_ret, 2))
ck("...y lo retenido NO cambia", _ret2["retenido"], _ret["retenido"])
_lib = [r for r in CL.reclamaciones(_pid) if CL.es_liberacion(r)]
ck("se lee de vuelta como liberacion", len(_lib), 1)
if _lib:
    _pdf2 = PDFC.generate_claim_pdf(_lib[0], CL.variaciones(_pid), {}, GRUPO, _prj, _ret2)
    _tx2 = "\n".join((p.extract_text() or "")
                     for p in PdfReader(BytesIO(_pdf2)).pages)
    ck("el PDF de la liberacion se titula distinto",
       "RETENTION RELEASE" in _tx2.upper(), True)
    ck("...y dice lo que queda retenido", "still held" in _tx2.lower(), True)
_okl2, _ = CL.puede_liberar(_pid, _prj)
ck("todavia se puede pedir la otra mitad", _okl2, True)

# ═════ 9 · cotizar leyendo el plano (v509) ══════════════════════════════════
respira(25)
print("\n[9] cotizar desde el plano (v509)")
CAT._invalidate()
_items = [i for i in (CAT.list_items(GRUPO) or []) if MARCA in str(i.get("Name", ""))]
_prop = QP.proponer({"ns": NS, "modelo": "3300", "rail": "T75-3/B"}, _items)
for l in _prop["lineas"]:
    print("   %-42s cant=%-5s %s" % (str(l["descripcion"])[:42], l["cantidad"],
                                     l["precio_total"]))
ck("propone las 3 reglas automaticas", len(_prop["lineas"]), 3)
ck("...y dice las que salta", len(_prop["saltadas"]), 2)
_puerta = next((l for l in _prop["lineas"] if "Landing" in str(l["descripcion"])), None)
ck("la puerta va NS veces", _puerta["cantidad"] if _puerta else None, float(NS))
_loom = next((l for l in _prop["lineas"] if "Inter-floor" in str(l["descripcion"])), None)
ck("el cableado va NS-1", _loom["cantidad"] if _loom else None, float(NS - 1))
_sin = QP.proponer({"ns": None}, _items)
ck("⚠️ sin paradas NO se omite ninguna linea",
   len(_sin["lineas"]), len(_prop["lineas"]))
ck("...y las incompletas se marcan", len(_sin["incompletas"]) > 0, True)

# ═════ 10 · expediente de entrega (v506) ════════════════════════════════════
respira(25, "el expediente cruza varias hojas")
print("\n[10] expediente de entrega (v506)")
try:
    from core import handover as HO
    from core import handover_ui as HOU
    _ctx = HOU.contexto(_pid, GRUPO, _prj)
    _filas = HO.estado(_ctx)
    _res = HO.resumen(_filas)
    print("   %s" % _res)
    ck("salen los 13 items del estandar", len(_filas), 13)
    ck("...y ninguno de tercero pasa por calculo",
       [f for f in _filas if f.get("quien") == "TERCERO" and f.get("estado") == "OK"
        and not f.get("documento")], [])
    _inc = HO.incoherencias(_ctx)
    print("   incoherencias: %s" % (_inc or "ninguna"))
except Exception as e:
    fallo("el expediente revento", repr(e))

print("\n" + "=" * 72)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
print("\n⚠️ La cadena queda MONTADA (obra %s). Para borrarla: --limpiar" % reg["proyectos"])
sys.exit(1 if fallos else 0)
