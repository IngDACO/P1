# -*- coding: utf-8 -*-
"""v510 · EL PDF DE LA RECLAMACIÓN Y LA LIBERACIÓN DE LA RETENCIÓN.

Lo que protege:
  (a) la fila posicional de `Claims` contra su cabecera (v363), en las DOS escrituras;
  (b) ⚠️ que una liberación NO retenga nada y que `neto = ThisClaim − Retention` siga
      valiendo para las dos clases de documento sin un `if` en la pantalla;
  (c) ⚠️ que una liberación NO mueva la base de trabajo ejecutado: si lo hiciera, la
      siguiente reclamación de avance saldría mal y nadie lo notaría hasta cobrar;
  (d) ⚠️ que no se pueda liberar más de lo retenido —eso no es una liberación, es una
      factura— ni con la obra sin terminar, ni cuando el avance NO SE PUDO LEER (ante
      la duda no se libera: tratar un fallo de lectura como «está terminada» es el
      criterio que v492 prohibió);
  (e) que el PDF salga con las cifras CONGELADAS de la fila y no recalcule ninguna;
  (f) ⚠️ que detalle las variaciones APROBADAS y no las propuestas: una propuesta no es
      dinero (v507) y meterla en el papel sería reclamar lo que nadie aceptó;
  (g) que el documento no invoque ninguna ley por su cuenta (criterio v506);
  (h) que la pantalla enseñe lo que SIGUE retenido, no lo retenido histórico.
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


from core import claims as CL                                     # noqa: E402
from core import claim_pdf as PDF                                 # noqa: E402

# Filas de ejemplo: dos reclamaciones de avance y una liberación parcial.
R1 = {"Number": "1", "WorkDone": "30000", "Retention": "1500", "ThisClaim": "30000",
      "PctComplete": "30", "Status": "issued", "Type": ""}
R2 = {"Number": "2", "WorkDone": "100000", "Retention": "3500", "ThisClaim": "70000",
      "PctComplete": "100", "Status": "issued", "Type": ""}
L1 = {"Number": "3", "WorkDone": "100000", "Retention": "0", "ThisClaim": "2000",
      "PctComplete": "100", "Status": "issued", "Type": CL.LIBERACION}

_orig_rec = CL.reclamaciones


def _con(filas):
    """Sustituye la lectura de la hoja por estas filas. Ejecutar de verdad la aritmética
    es lo único que prueba algo: leer el fuente no (v439)."""
    CL.reclamaciones = lambda pid, incluir_anuladas=False: list(filas)


class _WS:
    """Una hoja de mentira que se queda con la fila que se le escribe."""

    def __init__(self):
        self.filas = []

    def append_row(self, fila, value_input_option=None):
        self.filas.append(list(fila))


class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-09-21"

    def now(self, g):
        return self._T()


def _escribe(previas, prj, importe=None):
    """Ejecuta `crear_liberacion` DE VERDAD, con la hoja sustituida, y devuelve
    `(ok, mensaje, fila_escrita)`.

    ⚠️ Esto existe porque sin ello **cinco roturas de la batería escapaban**, y eran las
    caras: liberar más de lo retenido, liberar con la obra a medias por un fallo de
    lectura, que la liberación retuviera un 5% y que moviera la base de trabajo
    ejecutado. Todas viven en el camino de ESCRITURA, y el guardián solo miraba la
    aritmética de lectura: comprobaba mis propias filas de ejemplo, no lo que el código
    escribe. Es la trampa nº1 —el paso en vacío— dentro del propio guardián.
    """
    _hoja = _WS()
    _viejos = (CL._ws, CL._siguiente, CL._invalidate, CL.clock)
    CL._ws = lambda *a, **k: _hoja
    CL._siguiente = lambda *a, **k: 7
    CL._invalidate = lambda *a, **k: None
    CL.clock = _Reloj()
    _con(previas)
    try:
        _ok, _msg = CL.crear_liberacion("P", "cliente1", importe, "", "Bobo", prj)
    finally:
        CL._ws, CL._siguiente, CL._invalidate, CL.clock = _viejos
    return _ok, _msg, (_hoja.filas[0] if _hoja.filas else None)


def _campo(fila, nombre):
    """El valor de esa columna en la fila escrita, por NOMBRE.

    ⚠️ Nunca `fila[i]` a pelo: cuando la rotura hace que no se escriba nada, `fila` es
    None y el guardián moriría con TypeError justo en el caso que vigila — el patrón
    que se repitió cinco veces en v505-v509. Un guardián que muere no denuncia.
    """
    if not fila:
        return "(no se escribio ninguna fila)"
    try:
        return fila[CL.C_HEADERS.index(nombre)]
    except Exception as e:
        return "(no se pudo leer %s: %r)" % (nombre, e)


def _num_txt(v):
    """El número de lo escrito. La hoja guarda TEXTO, así que «0» y «0.0» son la misma
    cifra y compararlos como cadena daría un fallo en falso (la lección del "40" vs
    "40.0" de v372). Lo que NO es un número se devuelve tal cual, para que el mensaje
    del fallo enseñe el aviso en vez de un 0 inventado."""
    try:
        return float(str(v))
    except Exception:
        return v


# ═════ 1 · la columna y las dos filas posicionales ═══════════════════════════
print("\n[1] la hoja")
ck("«Type» es la ULTIMA columna de Claims", CL.C_HEADERS[-1], "Type")
ck("una reclamacion de avance vale «»", CL.PROGRESO, "")
_tree = ast.parse(_fuente("core/claims.py"))
# ⚠️ v363: la columna nueva no sirve de nada si la fila que se escribe no la lleva, y
# hay DOS escrituras. Se comprueban las dos, por AST y contra la cabecera real.
for _fn in ("crear_reclamacion", "crear_liberacion"):
    _f = next((n for n in ast.walk(_tree)
               if isinstance(n, ast.FunctionDef) and n.name == _fn), None)
    if _f is None:
        fallo("no existe %s" % _fn)
        continue
    _ap = next((n for n in ast.walk(_f) if isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") == "append_row"), None)
    if _ap is None:
        fallo("%s ya no usa append_row" % _fn)
        continue
    ck("la fila de %s cuadra con la cabecera" % _fn,
       len(_ap.args[0].elts), len(CL.C_HEADERS))


# ═════ 2 · la aritmetica de la retencion ═════════════════════════════════════
print("\n[2] cuanto sigue retenido")
_con([R1, R2])
ck("sin liberaciones, pendiente = retenido", CL.retenido("P")["pendiente"], 5000.0)
_con([R1, R2, L1])
_r = CL.retenido("P")
ck("lo retenido NO cambia al liberar", _r["retenido"], 5000.0)
ck("...lo liberado se cuenta aparte", _r["liberado"], 2000.0)
ck("...y el pendiente baja", _r["pendiente"], 3000.0)
# ⚠️ La propiedad que evita el disparate: liberar de mas no crea una deuda al reves.
_con([R1, dict(L1, ThisClaim="99999")])
ck("⚠️ liberar de mas deja pendiente en CERO, no en negativo",
   CL.retenido("P")["pendiente"], 0.0)
_con([])
ck("una obra sin reclamaciones no lanza", CL.retenido("P")["pendiente"], 0.0)
# ⚠️ El filtro `if not es_liberacion(r)` solo se puede probar con una fila de liberacion
# que SI lleve retencion. Con las filas que escribe el codigo —retencion 0— quitar el
# filtro no cambia el resultado, asi que la rotura correspondiente ESCAPABA de la
# bateria: el chequeo no podia distinguir. Una fila sucia (importada, o de una version
# futura) es justo de lo que el filtro protege.
_con([R1, R2, dict(L1, Retention="777")])
ck("⚠️ una liberacion con retencion sucia NO se suma a lo retenido",
   CL.retenido("P")["retenido"], 5000.0)

# ⚠️ Lo mas facil de romper sin que se note: que la liberacion ensucie la base de
# trabajo ejecutado. `calcular` hace `max(WorkDone)`, asi que una liberacion con un
# WorkDone raro desplazaria lo ya reclamado y la SIGUIENTE reclamacion saldria mal.
_con([R1, R2, L1])
_base = max(float(x.get("WorkDone")) for x in CL.reclamaciones("P"))
ck("⚠️ la liberacion no mueve la base de trabajo ejecutado", _base, 100000.0)


# ═════ 3 · cuando se puede pedir de vuelta ═══════════════════════════════════
print("\n[3] quien puede liberar")
_con([R1, R2])
ck("con la obra al 100% se puede", CL.puede_liberar("P", {"Progress": "100"})[0], True)
ck("...y aun asi se dice cuanto hay", "5000" in CL.puede_liberar("P", {"Progress": "100"})[1], True)
ck("con la obra al 90% NO", CL.puede_liberar("P", {"Progress": "90"})[0], False)
ck("...y el motivo dice el avance", "90" in CL.puede_liberar("P", {"Progress": "90"})[1], True)
_con([R1, R2, dict(L1, ThisClaim="5000")])
ck("si ya se libero todo, no queda nada que pedir",
   CL.puede_liberar("P", {"Progress": "100"})[0], False)


class _Rompe(dict):
    """Un proyecto cuyo avance no se puede leer.

    ⚠️ Nace con una clave DENTRO a propósito: la primera versión era un dict vacío, o
    sea FALSY, así que `prj or P.get_project(pid)` lo descartaba y nunca se llegaba a
    lanzar nada. El chequeo pasaba en verde sin ejercitar ni una línea del `except`, y
    la rotura correspondiente escapó de la batería. Un objeto de prueba que el código
    descarta no prueba nada (trampa nº1).
    """

    def __init__(self):
        dict.__init__(self, ID="P")

    def get(self, k, d=None):
        if k == "Progress":
            raise RuntimeError("la hoja no responde")
        return dict.get(self, k, d)


_con([R1, R2])
ck("el objeto de prueba NO se descarta por falsy", bool(_Rompe()), True)
# ⚠️ Un fallo de lectura NO es «esta terminada». Si lo fuera, una caida de Sheets
# abriria la puerta a liberar retencion de obras a medias.
ck("⚠️ si el avance no se puede leer, NO se libera",
   CL.puede_liberar("P", _Rompe())[0], False)
ck("...y el motivo lo dice, no miente con un «al 0%»",
   "could not be read" in CL.puede_liberar("P", _Rompe())[1], True)


# ═════ 3b · ⚠️ lo que de verdad se ESCRIBE ═══════════════════════════════════
print("\n[3b] la fila que se escribe")
_ok_w, _msg_w, _fila = _escribe([R1, R2], {"Progress": "100"})
ck("con la obra terminada, la liberacion se guarda", _ok_w, True)
ck("...y escribe UNA fila con todas las columnas",
   len(_fila) if _fila else 0, len(CL.C_HEADERS))
ck("⚠️ la liberacion NO retiene nada", _num_txt(_campo(_fila, "Retention")), 0.0)
ck("...ni lleva porcentaje de retencion", _num_txt(_campo(_fila, "RetentionPct")), 0.0)
ck("⚠️ pide todo lo pendiente por defecto", _num_txt(_campo(_fila, "ThisClaim")), 5000.0)
ck("⚠️ NO mueve la base de trabajo ejecutado",
   _num_txt(_campo(_fila, "WorkDone")), 100000.0)
ck("se marca como liberacion", _campo(_fila, "Type"), CL.LIBERACION)

_ok_w, _msg_w, _fila = _escribe([R1, R2], {"Progress": "100"}, importe=1200)
ck("una liberacion PARCIAL se admite (las dos mitades de AU)", _ok_w, True)
ck("...y guarda lo pedido, no el total", _num_txt(_campo(_fila, "ThisClaim")), 1200.0)

_ok_w, _msg_w, _fila = _escribe([R1, R2], {"Progress": "100"}, importe=99999)
ck("⚠️ NO se puede liberar mas de lo retenido", _ok_w, False)
ck("...y no se escribe nada", _fila, None)
ck("...y el mensaje dice cuanto hay", "5000" in str(_msg_w), True)

_ok_w, _msg_w, _fila = _escribe([R1, R2], {"Progress": "40"})
ck("⚠️ con la obra a medias no se escribe nada", _fila, None)
_ok_w, _msg_w, _fila = _escribe([R1, R2], {"Progress": "100"}, importe=-5)
ck("un importe negativo se rechaza", _ok_w, False)
_ok_w, _msg_w, _fila = _escribe([R1, R2], _Rompe())
ck("⚠️ con el avance ilegible tampoco se escribe", _fila, None)


# ═════ 4 · el PDF: lo que dice y lo que no ═══════════════════════════════════
print("\n[4] el documento")
REC = {"Group": "cliente1", "Number": "2", "Date": "2026-09-21", "PctComplete": "60",
       "ContractValue": "100000", "VariationsValue": "8500", "WorkDone": "65100",
       "PreviouslyClaimed": "32550", "RetentionPct": "5", "Retention": "1627.5",
       "ThisClaim": "32550", "Status": "issued", "Note": "Under the SOP Act.", "Type": ""}
VARS = [{"Number": "1", "Description": "Extra landing door", "Amount": "6000",
         "Status": "approved"},
        {"Number": "9", "Description": "Nobody agreed to this", "Amount": "9999",
         "Status": "proposed"}]


def _texto(b):
    """Lo legible del PDF, con pypdf (ya es dependencia).

    ⚠️ El primer extractor de esta version descomprimia los flujos a mano y devolvia
    CERO con el texto perfectamente puesto: TODAS las afirmaciones de contenido pasaban
    en vacio y las negativas pasaban por partida doble. Lo delato el chequeo de abajo
    —que la sonda sepa leer el caso conocido-bueno—, que es la trampa nº12.
    """
    import io as _io
    from pypdf import PdfReader
    return "\n".join((p.extract_text() or "") for p in PdfReader(_io.BytesIO(b)).pages)


_b = PDF.generate_claim_pdf(REC, VARS, {}, "cliente1", {"Name": "Tower A"})
ck("es un PDF", _b[:5], b"%PDF-")
_t = _texto(_b)
ck("⚠️ la sonda SABE leer este PDF (sin esto, nada de abajo vale)",
   "PROGRESS CLAIM" in _t.upper(), True)
ck("lleva el neto a pagar", "NET AMOUNT PAYABLE" in _t.upper(), True)
ck("detalla la variacion aprobada", "Extra landing door" in _t, True)
ck("⚠️ NO mete la propuesta: no es dinero", "Nobody agreed" in _t, False)
ck("la nota viaja entera", "SOP Act" in _t, True)
ck("dice contra que obra es", "Tower A" in _t, True)

_bl = PDF.generate_claim_pdf(dict(REC, Number="3", Type=CL.LIBERACION, ThisClaim="2000",
                                  Retention="0", Note=""), VARS, {}, "cliente1", {},
                             {"retenido": 5000.0, "liberado": 2000.0, "pendiente": 3000.0})
_tl = _texto(_bl)
ck("la liberacion se titula distinto", "RETENTION RELEASE" in _tl.upper(), True)
ck("...y NO se titula reclamacion de avance", "PROGRESS CLAIM" in _tl.upper(), False)
ck("⚠️ dice lo que QUEDA retenido (una parcial no cierra nada)",
   "still held" in _tl.lower(), True)
ck("...con su importe", "3,000.00" in _tl, True)
ck("no desglosa variaciones en una liberacion", "Extra landing door" in _tl, False)
ck("un dict vacio no revienta el boton", PDF.generate_claim_pdf({})[:5], b"%PDF-")

# ⚠️ El PDF cuenta lo PACTADO, no lo que daria la formula hoy: si recalculara, un
# cambio del % de retencion del grupo reescribiria documentos ya enviados.
_src = _fuente("core/claim_pdf.py")
_ar = ast.parse(_src)
ck("⚠️ el PDF no llama a calcular() ni a retenido()",
   [n for n in ast.walk(_ar) if isinstance(n, ast.Call)
    and getattr(n.func, "attr", "") in ("calcular", "retenido")], [])
# (g) v506: la app no declara cumplimiento de ninguna ley por su cuenta.
ck("⚠️ el documento no invoca ninguna ley por su cuenta",
   any(s in _src for s in ("Security of Payment Act 1999", "SOPA claim under",
                           "This is a payment claim under")), False)


# ═════ 5 · la pantalla ═══════════════════════════════════════════════════════
print("\n[5] lo que se ve")
_ui = _fuente("core/claims_ui.py")
_tu = ast.parse(_ui)
ck("⚠️ el indicador enseña lo que SIGUE retenido, no el historico",
   "retenido_pendiente" in _ui.split("Retention held")[1][:200], True)
for _f in ("_descarga", "_retencion"):
    ck("existe %s" % _f,
       any(isinstance(n, ast.FunctionDef) and n.name == _f for n in ast.walk(_tu)), True)
# ⚠️ Definir la funcion no es llamarla: es la trampa nº2 (grep no es uso) y el fallo
# que dejo `_field_activities` verificado en vacio.
_rn = next(n for n in ast.walk(_tu) if isinstance(n, ast.FunctionDef) and n.name == "render")
_llamadas = {getattr(n.func, "id", "") for n in ast.walk(_rn) if isinstance(n, ast.Call)}
ck("...y render() LLAMA a _descarga", "_descarga" in _llamadas, True)
ck("...y a _retencion", "_retencion" in _llamadas, True)
ck("el formateador de dinero sigue delegando en theme (v508)",
   "theme.dinero" in _ui, True)

# ═════ 6 · el mensaje no puede mentir sobre la causa ═════════════════════════
# ⚠️ Lo encontro la CADENA de punta a punta, no un test: al comerse la cuota (429), la
# app contestaba «Google Sheets is not configured» — falso, y manda a revisar unos
# secrets perfectos. En una reclamacion es peor: el usuario puede concluir que la obra
# no tiene contrato. Paso en claims.py y, otra corrida despues, en catalogo.py.
print("\n[6] por que no hay hoja")
from core import timeclock as TC                                  # noqa: E402

_orig_sp = TC._secrets_present
try:
    TC._secrets_present = lambda: False
    _sin_secrets = TC.motivo_sin_hoja()
    TC._secrets_present = lambda: True
    _con_secrets = TC.motivo_sin_hoja()
finally:
    TC._secrets_present = _orig_sp
ck("sin secrets dice que falta configurar",
   "not configured" in _sin_secrets, True)
ck("⚠️ CON secrets NO dice que falte configurar",
   "not configured" in _con_secrets, False)
ck("...dice que es pasajero y que se reintente",
   "Try again" in _con_secrets, True)
ck("⚠️ y son mensajes DISTINTOS (si no, el arreglo no hace nada)",
   _sin_secrets != _con_secrets, True)

# ⚠️ Y que los modulos de la cadena del dinero no hayan vuelto al literal. Se mira por
# AST el cuerpo de `if w is None:`, no por grep: el literal aparece legitimamente en
# otros sitios (cuando SI se ha comprobado que faltan los secrets).
for _mod in ("claims.py", "catalogo.py", "quotes.py"):
    _t = ast.parse(_fuente("core/" + _mod))
    _malos = []
    for _n in ast.walk(_t):
        if not isinstance(_n, ast.If):
            continue
        _test = ast.unparse(_n.test)
        if "is None" not in _test:
            continue
        for _s in _n.body:
            if "Google Sheets is not configured" in ast.unparse(_s):
                _malos.append(_test)
    ck("%s no culpa a la configuracion cuando la hoja no abre" % _mod, _malos, [])

print("\n" + "=" * 70)
CL.reclamaciones = _orig_rec
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
