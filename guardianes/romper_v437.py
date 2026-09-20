"""Prueba el guardián de v437 contra código ROTO a propósito.

Un guardián que solo aprueba lo que ya funciona no demuestra nada (regla v410).
Cada rotura es un fallo que este cambio PODRÍA haber introducido de verdad.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
VERIF = Path(__file__).with_name("verif_v437.py")
UR = RAIZ / "core" / "user_report.py"
IN = RAIZ / "core" / "interpretation.py"

ROTURAS = [
    ("una CLAVE de USER_SCHEMA se traduce (deja el informe en blanco)",
     IN, '"resumen":        "Executive summary', '"summary":        "Executive summary'),
    ("las descripciones del esquema vuelven al español",
     IN, '"implementacion": "Concrete, ordered steps',
     '"implementacion": "Pasos concretos y ordenados para implementar la solución en obra'),
    ("el veredicto vuelve a deducirse del TEXTO de la IA",
     UR, '_cortes = bool(cortes_por_piso(calculated or {}, best or {}))',
     '_cortes = "requiere cortes" in str(ia.get("cortes", "")).lower()'),
    ("el veredicto se cae al except (el fallo REAL de v437: `limits`)",
     UR, 'cortes_por_piso(calculated or {}, best or {})',
     'cortes_por_piso(limits or {}, best or {})'),
    ("el informe pasa a usar t() en vez de d() (idioma de la pantalla)",
     UR, 'd("TECHNICAL REPORT")', 't("TECHNICAL REPORT")'),
    ("un título de sección vuelve al español",
     UR, '_section(d("3. Cuts required"), styles)', '_section("3. Cortes necesarios", styles)'),
    ("la firma vuelve al español",
     UR, "d('PREPARED BY')", "'PREPARADO POR'"),
    ("el prompt de la IA vuelve a pedir español",
     IN, 'Each value must be a string of professional ENGLISH text.',
     'Cada valor es una cadena de texto en español profesional.'),
    ("la variable del glosario vuelve a llamarse `d` (tapa la función)",
     UR, 'for i, (_term, _def) in enumerate(_terms):\n'
         '        _fila_t.append(Paragraph(f"<b>{_term}</b><br/><font size=8 color=\'#555555\'>{_def}</font>",',
     'for i, (t, d) in enumerate(_terms):\n'
     '        _fila_t.append(Paragraph(f"<b>{t}</b><br/><font size=8 color=\'#555555\'>{d}</font>",'),
    ("el payload de la IA deja de compartir la definición de cortes",
     IN, 'cortes = cortes_por_piso(lim, best)', 'cortes = []'),
]


def corre():
    r = subprocess.run([sys.executable, str(VERIF)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


tmp = Path(tempfile.mkdtemp())
for f in (UR, IN):
    shutil.copy2(f, tmp / f.name)

print("Estado SANO:")
print("  OK" if corre() == 0 else "  ⚠️ el guardián ya falla SIN romper nada — arreglar antes")

cazadas = 0
for desc, fich, viejo, nuevo in ROTURAS:
    src = fich.read_text(encoding="utf-8")
    if src.count(viejo) != 1:
        print(f"  ⚠️ ANCLA MALA ({src.count(viejo)}×): {desc}")
        continue
    fich.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    rc = corre()
    shutil.copy2(tmp / fich.name, fich)
    if rc != 0:
        cazadas += 1
        print(f"  cazada   {desc}")
    else:
        print(f"  !! NO SE CAZA  {desc}")

print("\nEstado restaurado:")
print("  OK" if corre() == 0 else "  ⚠️ NO restauró")
print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
