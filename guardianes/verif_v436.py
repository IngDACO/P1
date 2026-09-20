"""Guardián de v436 — F1a: los documentos comerciales, en inglés.

Lo que protege:

 1. ⚠️ **Ninguna comparación puede depender de un texto traducido.** Es el fallo que
    cometí en el PRIMER módulo que toqué: `elif lbl == "Marca/Modelo"` dejó de
    cumplirse al traducir la etiqueta a «Make/Model», y esa línea desapareció de la
    etiqueta QR **sin ningún error**. Es el modo de fallo típico de una traducción.
 2. Los documentos usan `d()` (idioma BASE) y no `t()`: una factura sale de la
    empresa y su idioma no puede depender de cómo tenga la pantalla quien la emite.
 3. Los PDFs se GENERAN y su texto sale en inglés (prueba funcional, no lectura).
 4. Las claves de los checks del Pre-Start no cambian: en la hoja se guarda
    `{"permisos": "YES"}`, así que tocar la clave rompería todo el histórico.
 5. Un valor de negocio se muestra con `etiqueta()`, nunca traducido a mano.
"""
import ast
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
from core.valores import LEGADO as _VLEG   # noqa: E402
_VALORES_NEGOCIO = set(_VLEG.values()) | set(_VLEG)

DOCS = ["invoice_pdf.py", "quote_pdf.py", "payslip_pdf.py", "prestart_pdf.py",
        "asset_label_pdf.py"]
ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


# ── 1 ────────────────────────────────────────────────────────────
sec("1. Ninguna comparación depende de un texto traducido (el fallo de la etiqueta)")
malos = []
for f in sorted((RAIZ / "core").glob("*.py")):
    tr = ast.parse(f.read_text(encoding="utf-8"))
    trad = set()                       # textos que pasan por d()/t()
    for x in ast.walk(tr):
        if isinstance(x, ast.Call) and (
                (isinstance(x.func, ast.Name) and x.func.id in ("d", "t"))
                or (isinstance(x.func, ast.Attribute) and x.func.attr in ("d", "t"))):
            if x.args and isinstance(x.args[0], ast.Constant) \
                    and isinstance(x.args[0].value, str):
                trad.add(x.args[0].value)
    if not trad:
        continue
    for x in ast.walk(tr):
        if not isinstance(x, ast.Compare):
            continue
        for c in x.comparators:
            if isinstance(c, ast.Constant) and isinstance(c.value, str)                and c.value in trad and c.value not in _VALORES_NEGOCIO:
                malos.append(f"{f.name}:{x.lineno} → {c.value!r}")
chk("ninguna comparación usa un texto que pasa por d()/t()", not malos, str(malos))
chk("el chequeo NO corre en vacío: hay textos traducidos que vigilar",
    any("d(" in (RAIZ / "core" / m).read_text(encoding="utf-8") for m in DOCS))

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Los documentos van en el idioma BASE, no en el de la pantalla")
for m in DOCS:
    src = (RAIZ / "core" / m).read_text(encoding="utf-8")
    tr = ast.parse(src)
    usa_d = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "d"
                for x in ast.walk(tr))
    usa_t = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "t"
                for x in ast.walk(tr))
    chk(f"{m:22} usa d() y no t()", usa_d and not usa_t,
        f"d={usa_d} t={usa_t}")
from core import i18n                                            # noqa: E402
# ⚠️ Con el diccionario español VACÍO, `t()` y `d()` devuelven lo mismo y el chequeo
# no distingue nada: pasaba aunque `d()` delegara en `t()`. Hay que darle al motor una
# traducción de verdad para que la diferencia exista.
_orig_dic = i18n._dic
try:
    i18n._dic = lambda idi: {"Invoice": "Factura"}
    i18n.set_idioma("es")
    chk("con idioma español, t() SÍ traduce", i18n.t("Invoice") == "Factura")
    chk("...y d() NO (el documento va en el idioma base)", i18n.d("Invoice") == "Invoice")
finally:
    i18n._dic = _orig_dic
    i18n.set_idioma("en")

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Los PDFs se GENERAN y salen en inglés (prueba funcional)")
import streamlit as st                                           # noqa: E402
G = "cliente1"
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": G, "nombre": "verif"}
try:
    from pypdf import PdfReader                                  # noqa: E402
    from core import invoices as I, invoice_pdf, quotes as Q, quote_pdf
    from core import payroll as PR, payslip_pdf

    def texto(b):
        return " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(b)).pages)

    _f = next((x for x in I.list_facturas(G) if str(x.get("Status")) != "anulada"), None)
    if _f:
        _t = texto(invoice_pdf.generate_invoice_pdf(_f, None, "COPEX"))
        chk("la FACTURA sale en inglés",
            all(k in _t for k in ("TAX INVOICE", "Bill to", "Description", "Balance due")))
        chk("...y no quedan etiquetas en español",
            not any(k in _t for k in ("Facturar a", "Concepto", "Por cobrar", "Importe")))
    _c = next(iter(Q.list_cotizaciones(G)), None)
    if _c:
        _t = texto(quote_pdf.generate_quote_pdf(_c, None, "COPEX"))
        chk("la COTIZACIÓN sale en inglés",
            all(k in _t for k in ("QUOTE", "Valid until", "Description")))
    _n = next(iter(PR.list_nominas(G)), None)
    if _n:
        _t = texto(payslip_pdf.generate_payslip_pdf(_n, "COPEX"))
        chk("la COLILLA sale en inglés",
            all(k in _t for k in ("PAYSLIP", "Employee", "NET PAY", "Deductions")))
        chk("...y el tipo de concepto se muestra traducido",
            not any(k in _t for k in ("devengo", "deduccion", "aporte")))
except Exception as e:
    chk("los PDFs se generan", False, f"{type(e).__name__}: {e}")

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Las CLAVES del Pre-Start no cambian (la hoja guarda la clave)")
from core import prestart as PS                                  # noqa: E402
_esp = {"permisos", "toolbox", "subcontratistas", "preop",
        "cages", "landings", "penetrations"}
_hay = {k for k, _ in PS.CHECKS_S1} | {k for k, _ in PS.CHECKS_S3}
chk("las 7 claves siguen siendo las mismas", _hay == _esp, str(sorted(_hay ^ _esp)))
# ⚠️ Y hacen falta LIMITES de palabra y umbral 1, no 2: la frase de prueba
# <<Penetraciones del hueco cubiertas>> solo tiene UNA palabra funcional espanola,
# asi que con umbral 2 seguia colandose. Se excluyen <<no>> y <<de>>, que tambien
# son palabras inglesas o aparecen en nombres propios.
_ES = re.compile(r"\b(el|la|los|las|del|con|para|por|que|una|en|su|al|lo|es|son|"
                 r"como|desde|hasta|obra|hueco|y)\b", re.I)
_malos_txt = [v for _, v in PS.CHECKS_S1 + PS.CHECKS_S3
              if re.search(r"[áéíóúñÑ]", v) or _ES.search(v)]
chk("y sus textos ya están en inglés", not _malos_txt, str(_malos_txt))
chk("`_LABELS` sigue resolviendo clave → texto",
    PS._LABELS.get("cages", "").startswith("Landing cages"))

# ── 5 ────────────────────────────────────────────────────────────
sec("5. Un valor de negocio se muestra con etiqueta(), no traducido a mano")
# ⚠️ Por AST: la subcadena "i18n.etiqueta" aparecía también en MI PROPIO docstring
# del módulo, así que el chequeo pasaba con la llamada borrada (trampa nº2).
for m in ("invoice_pdf.py", "quote_pdf.py", "payslip_pdf.py"):
    _tr = ast.parse((RAIZ / "core" / m).read_text(encoding="utf-8"))
    _lla = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
               and x.func.attr == "etiqueta" for x in ast.walk(_tr))
    chk(f"{m:22} LLAMA a i18n.etiqueta para el estado", _lla)
chk("`devengo`/`deduccion`/`aporte` están mapeados",
    all(k in i18n.VALORES for k in ("devengo", "deduccion", "aporte")))
chk("...y siguen comparándose en español en payslip_pdf",
    '"devengo"' in (RAIZ / "core" / "payslip_pdf.py").read_text(encoding="utf-8"))

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
