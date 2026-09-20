# -*- coding: utf-8 -*-
"""v506 · el EXPEDIENTE DE ENTREGA: qué tiene la obra y qué le falta.

Lo que protege:
  (a) los trece ítems de la lista REAL (NSW DoE, a–m), con su reparto 5 / 8;
  (b) ⚠️ que un ítem de TERCERO no pueda salir OK por cálculo — la app no puede afirmar
      que existe el certificado eléctrico, solo que alguien subió un documento;
  (c) que cada evidencia de los cinco nuestros distinga los tres estados, en las dos
      direcciones (un chequeo que solo sabe decir OK no comprueba nada);
  (d) ⚠️ el CRUCE que nos hace únicos: firmó con el ticket vencido;
  (e) que un invitado (login vacío) NO se reporte como si le faltara certificado propio:
      un subcontratista no tiene ticket de esta empresa y acusarlo sería un falso rojo;
  (f) la fila posicional de Documentos contra su cabecera (v363);
  (g) que `handover` siga siendo módulo HOJA (no puede ciclar con projects);
  (h) ⚠️ que la pantalla NO prometa cumplimiento: decir «certificado» donde solo hay un
      expediente mete al cliente en un problema, y es el riesgo de producto de v506.
Todo EJECUTANDO: importar no ejecuta (v378) y compilar no verifica nada (v439).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import handover as H                                    # noqa: E402
from core import projects as P                                    # noqa: E402


def _est(filas, clave):
    return next(f["estado"] for f in filas if f["clave"] == clave)


BUENA = {
    "params": {"BKS": 1400, "LengthTemplate": 500}, "matrix": [[1, 2]], "plumb_ok": True,
    "acts": [{"Order": "1", "ActualStartDate": "2026-09-01", "ActualEndDate": "2026-09-05"},
             {"Order": "2", "ActualStartDate": "2026-09-06", "ActualEndDate": "2026-09-10"}],
    "prestarts": [{"Date": "2026-09-03", "Attendees": ["ana"]}],
    "trabajaron": {"ana": "2026-09-10"},
    "credenciales": {"ana": ["2026-12-31"]},
    "asignados": ["ana"], "docs": {},
}


# ═════ 1 · la lista es la REAL, no una inventada ═════════════════════════════
print("\n[1] los trece items")
ck("son TRECE items", len(H.ITEMS), 13)
ck("...con las letras a-m del estandar, sin repetir",
   sorted(i["letra"] for i in H.ITEMS), list("abcdefghijklm"))
ck("cinco los evidencia la app", sum(1 for i in H.ITEMS if i["fuente"] == H.COPEX), 5)
ck("...y ocho son de terceros", sum(1 for i in H.ITEMS if i["fuente"] == H.TERCERO), 8)
ck("las claves no se repiten", len(set(H.CLAVES)), 13)


# ═════ 2 · ⚠️ un item de TERCERO no pasa por calculo ═════════════════════════
print("\n[2] lo que la app NO puede afirmar")
_f = H.estado(BUENA)
_terc = [x for x in _f if x["fuente"] == H.TERCERO]
ck("⚠️ con la obra PERFECTA, los ocho de terceros siguen faltando",
   sorted({x["estado"] for x in _terc}), [H.FALTA])
_con = H.estado({**BUENA, "docs": {"safe_to_operate": "STO.pdf"}})
ck("...y solo pasan si alguien sube el documento",
   _est(_con, "safe_to_operate"), H.OK)
ck("...diciendo cual es",
   "STO.pdf" in next(x["detalle"] for x in _con if x["clave"] == "safe_to_operate"), True)


# ═════ 3 · los cinco nuestros, en las dos direcciones ════════════════════════
print("\n[3] cada evidencia distingue los tres estados")
ck("obra vacia: los trece faltan", H.resumen(H.estado({}))["falta"], 13)
ck("obra buena: los cinco nuestros en verde", H.resumen(_f)["ok"], 5)

ck("check_sheets sin survey: falta", _est(H.estado({}), "check_sheets"), H.FALTA)
ck("...con parametros pero sin matriz: PARCIAL",
   _est(H.estado({"params": {"BKS": 1}}), "check_sheets"), H.PARCIAL)

ck("as_built sin plomada: PARCIAL",
   _est(H.estado({**BUENA, "plumb_ok": False}), "as_built"), H.PARCIAL)

_media = {**BUENA, "acts": [BUENA["acts"][0], {"Order": "2"}]}
ck("commissioning con una actividad abierta: PARCIAL",
   _est(H.estado(_media), "commissioning"), H.PARCIAL)
ck("...y lo dice con numeros",
   "1 of 2" in next(x["detalle"] for x in H.estado(_media) if x["clave"] == "commissioning"), True)

ck("risk sin pre-starts: falta",
   _est(H.estado({**BUENA, "prestarts": []}), "risk"), H.FALTA)

ck("installer_certs sin certificado: falta",
   _est(H.estado({**BUENA, "credenciales": {}}), "installer_certs"), H.FALTA)
ck("...vencido antes de su ultimo dia: PARCIAL",
   _est(H.estado({**BUENA, "credenciales": {"ana": ["2026-08-12"]}}), "installer_certs"),
   H.PARCIAL)
# ⚠️ Un certificado SIN vencimiento no caduca: tratarlo como vencido seria un falso rojo.
ck("...y uno SIN fecha de vencimiento no se cuenta como vencido",
   _est(H.estado({**BUENA, "credenciales": {"ana": [""]}}), "installer_certs"), H.OK)


# ═════ 4 · ⚠️ el cruce que nadie mas puede hacer ═════════════════════════════
print("\n[4] lo que no cuadra")
ck("la obra buena no tiene incoherencias", H.incoherencias(BUENA), [])

_venc = {**BUENA, "credenciales": {"ana": ["2026-08-12"]}}
_i = H.incoherencias(_venc)
ck("⚠️ firmo el pre-start con el ticket vencido: se caza",
   [x["tipo"] for x in _i], ["cert_vencido"])
# ⚠️ `_i[0]` a secas mata al guardián con IndexError cuando la rotura hace que no cace
# nada, y la batería lo cuenta como «revienta, no cuenta»: la rotura se va de rositas.
# Un guardián que muere no denuncia — cuarta vez hoy con este mismo patrón.
_txt = _i[0]["texto"] if _i else ""
ck("...y se dice con las dos fechas",
   ("03/09/2026" in _txt and "12/08/2026" in _txt), True)

# ⚠️ (e) un invitado viene con el login VACÍO. El caso se prueba con una credencial
# colgada de la clave "" a propósito: sin la guarda explícita, esa fila suelta haría
# que TODO pre-start con un invitado saliera acusado.
_inv = {**BUENA, "prestarts": [{"Date": "2026-09-03", "Attendees": ["ana", ""]}],
        "credenciales": {"ana": ["2026-12-31"], "": ["2020-01-01"]}}
ck("⚠️ un invitado sin login no genera un falso rojo", H.incoherencias(_inv), [])

ck("obra cerrada sin plomada: se caza",
   [x["tipo"] for x in H.incoherencias({**BUENA, "plumb_ok": False})], ["sin_plomada"])
ck("fichó quien no estaba asignado: se caza",
   [x["tipo"] for x in H.incoherencias({**BUENA, "trabajaron": {"ana": "2026-09-10",
                                                               "colado": "2026-09-09"}})],
   ["no_asignado"])
ck("actividad cerrada antes de empezar: se caza",
   [x["tipo"] for x in H.incoherencias(
       {**BUENA, "acts": [{"Order": "1", "ActualStartDate": "2026-09-05",
                           "ActualEndDate": "2026-09-01"}]})],
   ["fechas_invertidas"])

# una celda con basura no puede tumbar la pantalla del expediente
ck("una fecha con basura no lanza",
   isinstance(H.incoherencias({**BUENA, "acts": [{"Order": "1", "ActualEndDate": "ayer"}]}), list),
   True)


# ═════ 5 · la hoja: la columna nueva no descuadra la fila (v363) ═════════════
print("\n[5] Documentos")
ck("«HandoverItem» es la ULTIMA columna", P.DOCUMENTS_HEADERS[-1], "HandoverItem")
_tr = ast.parse(_fuente("core/projects.py"))
_ad = next(n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef) and n.name == "add_document")
_ap = next((n for n in ast.walk(_ad) if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "append_row"), None)
assert _ap is not None, "add_document ya no usa append_row (revisar el chequeo)"
ck("la fila de add_document tiene tantos valores como columnas",
   len(_ap.args[0].elts), len(P.DOCUMENTS_HEADERS))
ck("...y acepta el item del expediente",
   "handover_item" in [a.arg for a in _ad.args.args], True)


# ═════ 6 · handover es modulo HOJA ═══════════════════════════════════════════
print("\n[6] sin ciclos")
_imp = [ast.unparse(n) for n in ast.walk(ast.parse(_fuente("core/handover.py")))
        if isinstance(n, (ast.Import, ast.ImportFrom))]
ck("no importa nada de core (no puede ciclar con projects)",
   [i for i in _imp if "core" in i], [])


# ═════ 7 · ⚠️ la pantalla no promete cumplimiento ════════════════════════════
print("\n[7] lo que la interfaz NO dice")
_ui = _fuente("core/handover_ui.py").lower()
# ⚠️ Este es el riesgo de producto de v506: un expediente no certifica nada, y decir
# lo contrario en pantalla mete al cliente en un problema con su certificador.
_prohibidas = ["compliance certificate", "certifies", "as1735 certificate",
               "certificate of compliance", "fully compliant"]


def _afirmadas(txt, frases):
    """Las que aparecen SIN negar. ⚠️ Buscar la frase a secas se caza a si mismo: el
    descargo honesto («this is **not** a compliance certificate») CONTIENE la expresion
    prohibida, y el chequeo fallaba por su propia construccion (el error de v500, que
    hoy ya ha aparecido tres veces). Lo que importa no es si la frase esta, sino si se
    AFIRMA: se exige un «not» en las 30 letras de delante."""
    malas = []
    for p in frases:
        i = txt.find(p)
        while i >= 0:
            if "not" not in txt[max(0, i - 30):i]:
                malas.append(p)
                break
            i = txt.find(p, i + 1)
    return malas


# la sonda se valida contra un caso conocido-malo antes de creerse su cero (nº12)
ck("la red SABE ver una promesa afirmada",
   _afirmadas("our software certifies the lift", ["certifies"]), ["certifies"])
ck("...y no confunde el descargo con la promesa",
   _afirmadas("this is not a compliance certificate", ["compliance certificate"]), [])
ck("⚠️ la pantalla no promete un certificado", _afirmadas(_ui, _prohibidas), [])
ck("...y dice explicitamente que NO lo es", "is **not** a compliance certificate" in _ui, True)
ck("el modulo tambien lo deja escrito",
   "NO certifica nada" in _fuente("core/handover.py"), True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
