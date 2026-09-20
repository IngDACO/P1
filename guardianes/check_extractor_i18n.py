"""Valida el extractor NUEVO contra el agujero que dejó pasar 47 etiquetas en F2.

⚠️ La prueba que importa es la NEGATIVA sobre el filtro viejo: si `_es` diera True para
estas palabras, el agujero no habría existido y esta corrección no probaría nada.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from i18n_tool import _es, _pintable                               # noqa: E402

# los que F2 se dejó: el filtro viejo NO los ve, el nuevo SÍ
CIEGOS = ["Fichar", "Firma", "Iniciales", "Pendientes", "Sitios", "Registrados",
          "Planificado", "Mis ausencias", "Guardar", "Nombre", "Descargar PDF",
          "Nueva factura", "Aprobar", "Rechazar", "Motivo"]
# lo que NO debe extraerse nunca (no es texto de persona)
NO = ["</div>", "#2e6da4", ":material/save:", 'style="color:red"', "  ", "12", "· ",
      "display:flex;gap:10px", "https://x.y", "{}"]

ok = True
print(f"{'texto':26} {'viejo(_es)':>11} {'nuevo':>7}")
for c in CIEGOS:
    v, n = _es(c), _pintable(c)
    print(f"{c[:26]:26} {str(v):>11} {str(n):>7}")
    if not n:
        print("   ⚠️ el extractor NUEVO tampoco lo ve")
        ok = False
_ciegos_viejo = [c for c in CIEGOS if not _es(c)]
print(f"\n  el filtro VIEJO era ciego a {len(_ciegos_viejo)}/{len(CIEGOS)}: {_ciegos_viejo[:6]}")
if len(_ciegos_viejo) < 8:
    print("   ⚠️ si el viejo los viera, esta corrección no probaría nada")
    ok = False

print()
for c in NO:
    if _pintable(c):
        print(f"  ⚠️ se extraería algo que NO es texto: {c!r}")
        ok = False
print(f"  {len(NO)} no-textos correctamente descartados"
      if ok else "  hay no-textos que se colarían")


# ⚠️ Las CLAVES de widget no se extraen: `st.form("cli_nuevo")` recibe la key como
# primer posicional, y envolverla en `t()` la haría depender del idioma de la pantalla
# → el estado del formulario se perdería al cambiarlo. Sus kwargs sí se traducen.
import ast                                                        # noqa: E402
import tempfile                                                   # noqa: E402
from i18n_tool import piezas                                      # noqa: E402

CODIGO = '''
import streamlit as st
with st.form("cli_nuevo"):
    st.text_input("Nombre del cliente")
    st.form_submit_button("Guardar ficha")
st.data_editor(df, help="Edita las horas")
st.progress(0.5, text="Cargando datos")
st.dataframe(df, column_config={
    "Importe": st.column_config.NumberColumn("Importe cobrado", format="$%,.2f")})
'''
_tmp = Path(tempfile.gettempdir()) / "_i18n_probe.py"
_tmp.write_text(CODIGO, encoding="utf-8")
_txt = {p["txt"] for p in piezas(_tmp)}
_tmp.unlink(missing_ok=True)
for _k in ("cli_nuevo",):
    if _k in _txt:
        print(f"  ⚠️ se extrae una CLAVE de widget: {_k!r}")
        ok = False
# ⚠️ La CLAVE `"Importe"` del `column_config` es el nombre de la columna del dataframe:
# traducirla dejaría a `st.data_editor` devolviendo una columna que nadie sabe leer.
# La ETIQUETA de la columna sí se traduce.
if "Importe" in _txt and "Importe cobrado" not in _txt:
    print("  ⚠️ se extrae la CLAVE del column_config en vez de la etiqueta")
    ok = False
for _e in ("Nombre del cliente", "Guardar ficha", "Edita las horas", "Cargando datos",
           "Importe cobrado"):
    if _e not in _txt:
        print(f"  ⚠️ NO se extrae una etiqueta que sí se pinta: {_e!r}")
        ok = False
print("  claves de widget fuera y etiquetas dentro" if ok else "  el filtro de keys falla")

print("\n" + ("EXTRACTOR OK" if ok else "EXTRACTOR CON FALLOS"))
sys.exit(0 if ok else 1)
