"""F4 · el PDF de las 4 herramientas de cálculo.

⚠️ Por qué no lo vio ningún barrido: `tool_pdf(...)` NO es una función de display, así
que el invariante de posición (que mira los argumentos de `st.*`) nunca lo miró, y sus
etiquetas son de 1-3 palabras, así que el barrido de FRASES tampoco. Pero ese PDF se
descarga, se archiva en Drive y **se lleva a obra**: dejarlo en español sería la pantalla
en inglés y su documento en español — el desajuste de media-unificación de v419.

Va con **`d()`**, no con `t()`: un documento que sale de la empresa se escribe en el
idioma BASE, no en el de la pantalla de quien lo genera (regla v436/v439).

NO SE TOCAN, a propósito:
  · `herramienta="plomada"|"rieles"|"buffers"|"belting"` → es la clave de
    `toolruns.HERRAMIENTAS` y se guarda en la hoja `Calculos`.
  · las claves de `datos={...}` → van a `DatosJSON` y las lee `entradas_de` al reabrir
    un cálculo (v148).
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
 "core/plumb_ui.py": [
   ('_lbl = (f"{_pr_base} · Elevador {i+1}" if _pr_base else f"Elevador {i+1}")',
    '_lbl = (f"{_pr_base} · Lift {i+1}" if _pr_base else f"Lift {i+1}")'),
   ('        "Replanteo de plomadas",', '        d("Plumb setting-out"),'),
   ('meta={"Proyecto": _pr_base or "—", "Elevadores": str(n),',
    'meta={d("Project"): _pr_base or "—", d("Lifts"): str(n),'),
   ('render_guardar(herramienta="plomada", titulo_pdf="replanteo de plomadas",',
    'render_guardar(herramienta="plomada", titulo_pdf=d("plumb setting-out"),'),
   ('resumen=(f"Plantilla DBP {r0[\'dbp\']:.1f} · d1 {r0[\'d1\']:.1f}/d2 {r0[\'d2\']:.1f} · "',
    'resumen=(f"Template DBP {r0[\'dbp\']:.1f} · d1 {r0[\'d1\']:.1f}/d2 {r0[\'d2\']:.1f} · "'),
   ('f"{n} elevador(es)"),', 'f"{n} lift(s)"),'),
   ('            "Elevador": i + 1,', '            d("Lift"): i + 1,'),
   ('            "Encaje": _encaje_txt(r.get("displacement")),',
    '            d("Fit"): _encaje_txt(r.get("displacement")),'),
   ('            "di (pared izq→plomo)": round(v.get("plomo_izq_pared_izq", 0), 1),',
    '            d("di (left wall→plumb)"): round(v.get("plomo_izq_pared_izq", 0), 1),'),
   ('            "dd (plomo→pared der)": round(v.get("plomo_der_pared_der", 0), 1),',
    '            d("dd (plumb→right wall)"): round(v.get("plomo_der_pared_der", 0), 1),'),
 ],
 "core/buffer_cut_ui.py": [
   ('        "Corte de buffers",', '        d("Buffer cutting"),'),
   ('meta={"Proyecto": _pr or "—", "HKP del plano": f"{res[\'HKP\']:.0f} mm",',
    'meta={d("Project"): _pr or "—", d("HKP from the drawing"): f"{res[\'HKP\']:.0f} mm",'),
   ('        tablas=[("Cortes por buffer", filas)],', '        tablas=[(d("Cuts per buffer"), filas)],'),
   ('render_guardar(herramienta="buffers", titulo_pdf="corte de buffers",',
    'render_guardar(herramienta="buffers", titulo_pdf=d("buffer cutting"),'),
   ('        "Corte (mm)": b["CutBuffer"],', '        d("Cut (mm)"): b["CutBuffer"],'),
   ('        "Estado":     "revisar" if b["warn"] else "OK",',
    '        d("Status"):   d("check") if b["warn"] else "OK",'),
 ],
 "core/belting_ui.py": [
   ('meta={"Proyecto": _pr or "—", "HQ (travel)": f"{_hq:.0f} mm",',
    'meta={d("Project"): _pr or "—", "HQ (travel)": f"{_hq:.0f} mm",'),
   ('              "HGP (diseño)": f"{_hgp:.0f} mm", "Elevadores": str(len(results))},',
    '              d("HGP (design)"): f"{_hgp:.0f} mm", d("Lifts"): str(len(results))},'),
   ('        tablas=[("DSTS por elevador", filas)],', '        tablas=[(d("DSTS per lift"), filas)],'),
 ],
 "core/rail_cut_ui.py": [
   ('                "Corte de rieles — Caso 1",', '                d("Rail cutting — Case 1"),'),
   ('                "Corte de rieles — Caso 2",', '                d("Rail cutting — Case 2"),'),
   ('render_guardar(herramienta="rieles", titulo_pdf="corte de rieles",',
    'render_guardar(herramienta="rieles", titulo_pdf=d("rail cutting"),'),
   ('                tablas=[("Cortes por elevador", _tab)],',
    '                tablas=[(d("Cuts per lift"), _tab)],'),
 ],
}

fallos, hechos = [], 0
for rel, pares in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for viejo, nuevo in pares:
        c = s.count(viejo)
        if c < 1:
            fallos.append(f"{rel}: (0x) {viejo[:74]}")
            continue
        s = s.replace(viejo, nuevo)
        n += c
    # ⚠️ El módulo tiene que IMPORTAR `d`, o el NameError solo asoma al generar el PDF
    # (que es justo lo que nadie prueba al desplegar).
    if n and "from core.i18n import" in s and " d" not in s.split("from core.i18n import")[1].split("\n")[0]:
        s = s.replace("from core.i18n import t", "from core.i18n import t, d", 1)
    try:
        ast.parse(s)
    except SyntaxError as e:
        fallos.append(f"{rel}: NO COMPILA {e}")
        continue
    p.write_text(s, encoding="utf-8")
    hechos += n
    print(f"  {rel:26} {n} hechas")

print(f"\n{hechos} hechas")
if fallos:
    print("⚠️ ANCLAS QUE NO CASAN:")
    for f in fallos:
        print("   ", f)
    sys.exit(1)
