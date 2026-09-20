"""v442 (2/2) · el resto de módulos que pintan un VALOR crudo.

Mismo criterio que la primera tanda: solo los puntos que LLEGAN A PANTALLA. Las
comparaciones y los dicts que se escriben en la hoja no se tocan.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
 "core/catalogo_ui.py": [
   ('''f"  ·  {it.get('Categoria', '') or '—'}  ·  "''',
    '''f"  ·  {_etq(str(it.get('Categoria', ''))) or '—'}  ·  "'''),
 ],
 "core/inventory_ui.py": [
   ('''    st.markdown(f"**{a.get('ID', '')}**  ·  {a.get('Categoria', '') or '—'}  ·  "''',
    '''    st.markdown(f"**{a.get('ID', '')}**  ·  {_etq(str(a.get('Categoria', ''))) or '—'}  ·  "'''),
   ('''            "Tipo":    m.get("Tipo", ""),''',
    '''            "Tipo":    _etq(str(m.get("Tipo", ""))),'''),
 ],
 "core/payroll_ui.py": [
   ('''                        f"{f.get('Estado', '')}")''',
    '''                        f"{_etq(str(f.get('Estado', '')))}")'''),
   # la columna Estado de la lista de nóminas
   ('''        "Estado":   str(x.get("Estado", "")),''',
    '''        "Estado":   _etq(str(x.get("Estado", ""))),'''),
 ],
}

fallos, hechos = [], 0
for rel, pares in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for viejo, nuevo in pares:
        c = s.count(viejo)
        if c != 1:
            fallos.append(f"{rel}: ({c}x) {viejo[:70]}")
            continue
        s = s.replace(viejo, nuevo, 1)
        n += 1
    if n and "etiqueta as _etq" not in s:
        s = s.replace("from core.i18n import t", "from core.i18n import t, etiqueta as _etq", 1)
    try:
        ast.parse(s)
    except SyntaxError as e:
        fallos.append(f"{rel}: NO COMPILA {e}")
        continue
    p.write_text(s, encoding="utf-8")
    hechos += n
    print(f"  {rel:26} {n} puntos de pantalla")

print(f"\n{hechos} hechas")
if fallos:
    print("⚠️ ANCLAS QUE NO CASAN:")
    for f in fallos:
        print("   ", f)
    sys.exit(1)
