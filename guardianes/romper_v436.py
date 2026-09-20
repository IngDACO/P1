"""Prueba el guardián de v436 contra el CÓDIGO ROTO (lección v410)."""
import subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
GUARD = Path(__file__).with_name("verif_v436.py")

CASOS = [
    ("vuelve la comparación por TEXTO traducido (el fallo de la etiqueta QR)",
     "core/asset_label_pdf.py", "        elif key is None:", '        elif lbl == "Make/Model":'),
    ("la factura pasa a usar t() (saldría en español si traduces la pantalla)",
     "core/invoice_pdf.py", 'Paragraph(d("TAX INVOICE"), ti)', 'Paragraph(t("TAX INVOICE"), ti)'),
    ("d() deja de ignorar el idioma de la interfaz",
     "core/i18n.py", "def d(texto: str, **kw) -> str:", "def d(texto: str, **kw) -> str:\n    return t(texto, **kw)\n\n\ndef _d_viejo(texto: str, **kw) -> str:"),
    ("el estado de la factura deja de traducirse",
     "core/invoice_pdf.py", "Paragraph(i18n.etiqueta(est), H)", "Paragraph(est, H)"),
    ("se traduce una CLAVE del Pre-Start (rompería todo el histórico)",
     "core/prestart.py", '("permisos",        "Permits', '("permits",        "Permits'),
    ("un texto del pre-start vuelve al español",
     "core/prestart.py", '"Shaft penetrations adequately covered"', '"Penetraciones del hueco cubiertas"'),
    ("la colilla vuelve a mostrar el tipo interno",
     "core/payslip_pdf.py", 'Paragraph(i18n.etiqueta(c.get("tipo", "")), H)', 'Paragraph(str(c.get("tipo", "")), H)'),
]

def correr():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(RAIZ), capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, [l.strip() for l in (r.stdout or "").splitlines() if "FALLO" in l]

print("Estado SANO:"); rc, f = correr()
if rc != 0:
    print("  !! ya falla sin romper nada:", f); sys.exit(1)
print("  OK\n")
malos = []
for i, (tit, rel, a, b) in enumerate(CASOS, 1):
    p = RAIZ / rel; orig = p.read_text(encoding="utf-8")
    if a not in orig:
        print(f"{i}. {tit}\n     !! ANCLA AUSENTE"); malos.append(tit); continue
    try:
        p.write_text(orig.replace(a, b, 1), encoding="utf-8"); rc, fa = correr()
    finally:
        p.write_text(orig, encoding="utf-8")
    if rc == 0:
        print(f"{i}. {tit}\n     !! NO SE CAZA"); malos.append(tit)
    else:
        print(f"{i}. {tit}\n     cazado: {fa[0][:86] if fa else '(sin línea)'}")
print("\nEstado restaurado:"); rc, f = correr()
print("  " + ("OK" if rc == 0 else f"!! {f}"))
print(f"\n{len(CASOS)-len(malos)}/{len(CASOS)} roturas cazadas" + ("" if not malos else f"\nSE ESCAPAN: {malos}"))
sys.exit(0 if (not malos and rc == 0) else 1)
