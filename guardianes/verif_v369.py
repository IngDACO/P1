"""GUARDIÁN v369 — el alta manual de factura puede alcanzar obras ARCHIVADAS.

`list_projects` las oculta por defecto desde v149 (correcto para una lista, falso aquí:
**archivar no es no-cobrar**). Hasta ahora solo entraban por el atajo desde la ficha del
proyecto (v358); desde Finanzas → Facturas → Nueva eran inalcanzables.

⚠️ Se comprueba la lógica REAL del formulario reproduciendo sus llamadas a `projects` y
`clientes` con los datos de producción, no una copia del `if`.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrator"}

from core import projects as P, clientes as C            # noqa: E402

G = "cliente1"
ok = True

# ── 1) el código: la casilla existe y va ANTES del radio ────────
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\invoices_ui.py").read_text(encoding="utf-8")
arbol = ast.parse(src)
ln_chk = ln_radio = ln_pop = None
for n in ast.walk(arbol):
    if isinstance(n, ast.Call):
        f = getattr(n.func, "attr", "")
        # ⚠️ CADUCADO por v440 (i18n F3): «archivadas» → «archived». Se aceptan las dos
        # raíces; lo que la regla protege es el ORDEN (casilla y reset ANTES del radio).
        if f == "checkbox" and any(("archivad" in ast.unparse(a).lower()
                                    or "archived" in ast.unparse(a).lower())
                                   for a in n.args):
            ln_chk = n.lineno
        if f == "radio" and any(("Alcance" in ast.unparse(a)
                                 or "Scope" in ast.unparse(a)) for a in n.args):
            ln_radio = n.lineno
        # ⚠️ `ast.unparse` normaliza a comillas SIMPLES: buscar '"fac_scope"' no casa nunca
        if f == "pop" and n.args and "fac_scope" in ast.unparse(n.args[0]):
            ln_pop = n.lineno
print("== orden en el código ==")
print(f"   casilla «archivadas» : línea {ln_chk}")
print(f"   soltar `fac_scope`   : línea {ln_pop}")
print(f"   radio «Alcance»      : línea {ln_radio}")
for nom, v in (("casilla", ln_chk), ("pop", ln_pop), ("radio", ln_radio)):
    if v is None:
        print(f"   ‼️ falta: {nom}")
        ok = False
if ok:
    # ⚠️ regla v111: escribir/soltar la clave de un widget DESPUÉS de instanciarlo revienta
    ok &= ln_chk < ln_radio and ln_pop < ln_radio
    print(f"   {'✓' if ok else '✗'} la casilla y el reset van ANTES del radio (regla v111)")

# ── 2) los datos: ¿hay obras archivadas facturables? ────────────
print("\n== obras por cliente (activas vs archivadas) ==")
from core import invoices as I
fichas = C.list_clientes(G, incluir_inactivos=True)
hubo = False
for cl in fichas:
    cid = str(cl.get("ID", ""))
    cnorm = C._norm(cl.get("Nombre"))
    act = [p for p in P.list_projects(grupo=G) if C.es_del_cliente(p, cid, cnorm)]
    tod = [p for p in P.list_projects(grupo=G, incluir_archivados=True)
           if C.es_del_cliente(p, cid, cnorm)]
    arch = [p for p in tod if str(p.get("ID")) not in {str(x.get("ID")) for x in act}]
    if not arch:
        continue
    hubo = True
    print(f"   {str(cl.get('Nombre'))[:26]:<27} activas {len(act):>2} · archivadas {len(arch):>2}")
    for p in arch:
        pid = str(p.get("ID"))
        try:
            pend = I.pendiente_de_facturar(pid, G)
        except Exception:
            pend = None
        marca = ""
        if isinstance(pend, (int, float)) and pend > 0:
            marca = f"  ← ⚠️ ${pend:,.2f} PENDIENTE DE FACTURAR y antes inalcanzable"
        print(f"      {pid} {str(p.get('Nombre'))[:26]:<27}{marca}")
if not hubo:
    print("   (ninguna archivada en este grupo)")

# ── 3) la etiqueta las distingue ────────────────────────────────
print("\n== ¿se distinguen en el radio? ==")
# ⚠️ CADUCADO por v440 (i18n F3): la marca pasó al inglés. Lo que la regla protege
# es que una obra ARCHIVADA se DISTINGA en el radio, no cómo se escriba.
_marca = "· archivada" in src or "· archived" in src
print(f"   el código marca «· archivada/archived»: {_marca}")
ok &= _marca

print("\n" + ("✅ v369 OK: la casilla existe, va antes del radio, suelta el alcance obsoleto "
              "y las archivadas se marcan" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
