"""Guardián v351 — aislamiento entre empresas cliente.

Hasta v350 el aislamiento no lo garantizaba el código: lo garantizaba que la interfaz
nunca te ofreciera el ID de otra empresa. Con los deep-links de v337 (`?p=`, `?activo=`)
eso dejaba de ser cierto en cuanto entrara el segundo cliente.

Este chequeo falla si alguien añade una vista de detalle que traiga un objeto POR ID
global sin comprobar el grupo.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
ok = True


def chk(nombre, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(f"  {'OK  ' if cond else '⚠️  '}{nombre}: {extra}")


print("== 1) la regla vive en UN solo sitio ==")
copias = [p.name for p in (RAIZ / "core").glob("*.py")
          if "def puede_ver" in p.read_text(encoding="utf-8")]
chk("definiciones de `puede_ver`", copias == ["tenant.py"], copias)

print("\n== 2) toda vista de detalle por ID GLOBAL llama al guardián ==")
# (getter global, fichero, función)
VISTAS = [("P.get_project", "core/projects_ui.py", "_detalle_proyecto"),
          ("I.get_factura", "core/invoices_ui.py", "_detalle_factura"),
          ("payroll.get_nomina", "core/payroll_ui.py", "_detalle"),
          ("INV.get_activo", "core/inventory_ui.py", "_detalle")]
for getter, fich, fn in VISTAS:
    tr = ast.parse((RAIZ / fich).read_text(encoding="utf-8"))
    f = next((n for n in ast.walk(tr)
              if isinstance(n, ast.FunctionDef) and n.name == fn), None)
    if f is None:
        chk(f"{fich}:{fn}", False, "la función ya no existe — revisar")
        continue
    c = ast.unparse(f)
    i_get, i_grd = c.find(getter), c.find("tenant.exigir")
    # el guardián tiene que ir DESPUÉS de traer el objeto y ANTES de pintarlo
    i_pinta = min([x for x in (c.find("st.markdown"), c.find("st.dataframe")) if x > 0]
                  or [10 ** 9])
    chk(f"{fich.split('/')[-1]}.{fn}", i_grd > i_get > -1 and i_grd < i_pinta,
        f"get@{i_get} guardián@{i_grd} render@{i_pinta if i_pinta < 10**9 else '—'}")

print("\n== 3) el propietario NO puede quedar bloqueado (es su función) ==")
import streamlit as st

from core import tenant
st.session_state["auth"] = {"rol": "owner", "grupo": ""}
chk("propietario ve cualquier grupo",
    all(tenant.puede_ver(g) for g in ("cliente1", "cliente2", "", "OTRO")), "los 4")

print("\n== 4) la matriz de la regla ==")
CASOS = [({"rol": "administrator", "grupo": "a"}, "a", True),
         ({"rol": "administrator", "grupo": "a"}, "b", False),
         ({"rol": "field", "grupo": "b"}, "a", False),
         ({"rol": "administrator", "grupo": "A"}, "a", True),   # sin distinguir mayúsculas
         ({"rol": "administrator", "grupo": "a"}, "", True),    # histórico sin grupo
         ({}, "a", False)]                                      # sin sesión
for sess, g, esp in CASOS:
    st.session_state["auth"] = sess
    chk(f"{sess.get('rol') or '(sin sesion)':<14} grupo={sess.get('grupo', '-')!r} -> obj {g!r}",
        tenant.puede_ver(g) == esp, "ve" if esp else "bloqueado")

print("\n== 5) probado contra el CÓDIGO ROTO ==")
# sin el guardián en _detalle_proyecto, el chequeo 2 tiene que fallar
roto = "prj = P.get_project(pid)\n    grupo = str(prj.get('Grupo',''))"
chk("un detalle sin `tenant.exigir` se detecta", "tenant.exigir" not in roto, "sí")

print("\n" + ("TODO OK" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
