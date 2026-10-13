"""Roturas de la DUODECIMA red. La nº2 es la que de verdad importa: es el fallo
que yo mismo introduje y que compilaba — traducir el estado que se ESCRIBE en la
hoja de Google."""
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
    # v569 · la celda lleva ahora un punto de color delante: la rotura es la misma (el
    # estado vuelve a salir en crudo), anclada a la forma nueva.
    ("invoices_ui.py", "'')} \" + _etq(I.estado_cobro(f))",
     "'')} \" + I.estado_cobro(f)",
     "la celda de Facturas vuelve a mostrar el estado en crudo"),
    # v564 · al día con la columna de AHORA («Status»; desde la migración al inglés el
    # ancla «Estado» no casaba y era deuda declarada). La misma rotura.
    ("projects_ui.py", '"Status": P.derive_estado(0, est, tipo),',
     '"Status": _etq(P.derive_estado(0, est, tipo)),',
     "⚠️ se traduce el estado que se ESCRIBE en la hoja (guardaria ingles en Sheets)"),
    ("quotes_ui.py", '"Estado": _etq(Q.estado_de(c))', '"Estado": Q.estado_de(c)',
     "la celda de Cotizaciones vuelve al crudo"),
    # v570 · re-anclada: `clientes_ui` ya no usa `_etq` (su tabla de facturas es la de
    # Invoices) y quitarle el import no rompería nada. La misma rotura, en un módulo que
    # SÍ lo usa (dos veces).
    ("payroll_ui.py", "from core.i18n import t, etiqueta as _etq",
     "from core.i18n import t",
     "un modulo usa _etq sin importarlo (NameError al abrir la pantalla)"),
    # v564 · el ternario de la cabecera de la localización ya NO es un ternario (pasó a
    # `_loc_estado_lbl`, con tres estados e `if`): la red de los ternarios no tiene nada
    # que vigilar ahí, y la rotura «se escapaba». Se ancla al ternario que SÍ queda en
    # Locations —el titular del gasto—, con la misma rotura: una rama vuelve al español.
    ("projects_ui.py", 't("No spend has been recorded at this location yet."))',
     '"Aún no hay gasto registrado en esta localización.")',
     "un ternario ASIMETRICO: una rama traducida y la otra en espanol"),
    ("auth_ui.py", 'else t("missing")))', 'else "falta"))',
     "la columna Contacto vuelve a mezclar `yes` y `falta`"),
    # ⚠️ v563 · RETIRADAS dos roturas, no muertas por descuido: protegían la leyenda del
    # `st.line_chart` consolidado de Groupings y la del `st.bar_chart` de avance, y v563
    # quitó los dos (la curva pasó a Altair con el lenguaje de la ficha; el avance, a una
    # barra DENTRO de la tabla). La leyenda en inglés de la curva nueva la vigila verif_v563
    # (y romper_v563 la rompe).
    # v564 · al día con la forma de AHORA (un `t()` con marcadores; el ancla vieja no
    # casaba y era deuda declarada). La misma rotura: la rama hermana vuelve al español.
    ("quotes_ui.py", 'st.success(t(":material/check_circle: You are at **{m} below** what was quoted, with "',
     'st.success((":material/check_circle: Vas **{m} por debajo** de lo cotizado, con "',
     "vuelve el «Vas» espanol en la rama hermana de `You are at`"),
]

cazadas = 0
for i, (mod, viejo, nuevo, desc) in enumerate(ROTURAS, 1):
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    n = bak.count(viejo)
    if n == 0:
        print(f"{i}. ANCLA MALA (0) — la rotura no probaria NADA: {desc}")
        continue
    p.write_text(bak.replace(viejo, nuevo, 1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "verif_v452.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = r.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else 'SE ESCAPA'} — {desc}")

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
