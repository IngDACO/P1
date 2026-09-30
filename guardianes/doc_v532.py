# -*- coding: utf-8 -*-
"""Documenta v532 — los 22 usos de `st.components.v1.html` pasan a `st.iframe`."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
NEG = "C:/Users/diego/P1/NEGOCIO.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
PROD = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## LOS 22 USOS DE `st.components.v1.html` PASAN A `st.iframe` (v532)

Decisión del usuario: hacer los 22 ya (tras explicarle que hoy no se gana nada visible: lo que
se gana es poder volver a subir de Streamlit). Nace **`core/incrustar.py`** y todo HTML
incrustado pasa por ahí: `dibujo(html, alto, scroll=False)` y `script(js)`.

### ⚠️ Lo que se midió antes de tocar nada
En Streamlit 1.64 `components.v1.html` y `st.iframe` generan el **mismo elemento** (un iframe
con el HTML en `srcdoc`, el mismo sandbox, el mismo acceso a la página): el riesgo que se le
había descrito al usuario para los scripts era MAYOR que el real. Pero `st.iframe` cambia dos
cosas, y `incrustar` las neutraliza en un solo sitio:
- **Siempre permite scroll** (`scrolling="auto"`, leído en el componente del navegador). Los
  dibujos iban con `scrolling=False`: lo que se salía se recortaba sin barra. `dibujo()` inyecta
  `overflow:hidden` DENTRO del `<body>` (delante de un `<!DOCTYPE>` lo anularía y el documento
  pasaría a modo quirks), así que se ven igual. La planta por pisos del survey ya tenía scroll y
  lo conserva (`scroll=True`).
- **No admite altura 0**, y los tres scripts iban a 0. `script()` usa 1 px transparente: con
  «content» el recuadro vale 150 px hasta la primera medida (un salto al cargar).

⚠️ Los scripts NO van a `st.html`: sin recuadro, `window.parent` sería la página que envuelve
el Cloud y escribirían —la cookie del login, la cabecera de la PWA, la trampa del «atrás»— en
el documento equivocado.

Las alturas no cambian (los SVG miden como mucho su tamaño de diseño, `max-width`); lo que
llega al navegador es el mismo HTML más ese estilo. `verif_v532` lo comprueba anotando lo que
recibe `st.iframe` y EJECUTANDO los cronómetros, la trampa del «atrás», la cookie y el survey
real.

__PROD__ · 26 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v532 | **Los 22 usos de `st.components.v1.html` pasan a `st.iframe`**, por `core/incrustar` "
        "(decisión del usuario). ⚠️ En 1.64 los dos generan el MISMO elemento; `st.iframe` solo "
        "cambia que siempre permite scroll (se neutraliza con `overflow:hidden` dentro del "
        "<body>, sin romper el DOCTYPE) y que no admite altura 0 (los 3 scripts van a 1 px). "
        "Los scripts NO van a `st.html`: sin recuadro, `window.parent` sería otro documento. "
        "__PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v531 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v531 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
ENT_VIEJA = ("reinicio reinstala la última y `st.components.v1.html` (22 usos) ya está "
             "anunciado para quitarse.")
ENT_NUEVA = ("reinicio reinstala la última. Desde v532 la app ya no usa `st.components.v1.html` "
             "(anunciado para quitarse): todo HTML incrustado pasa por `core/incrustar.py`.")
NEG_VIEJA = "- **Migrar los 22 usos de `st.components.v1.html`**"
NEG_NUEVA = "- ~~**Migrar los 22 usos de `st.components.v1.html`**~~ → ✅ **hecho en v532 (30/09/2026)**."


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v532.py "<suite>" "<bateria>" "<produccion>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE), ("__PROD__", PROD)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v532 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v532 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
unica(c, ENT_VIEJA, "entorno", "CLAUDE.md")
c = c.replace(ENT_VIEJA, ENT_NUEVA)
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v532 = actual)")
c = c.replace(CAB, CAB + FILA)
lineas = c.splitlines(True)
idx = [i for i, l in enumerate(lineas) if l.startswith("| v")]
if len(idx) != 16:
    raise SystemExit("esperaba 16 filas tras insertar: %d" % len(idx))
vieja = lineas[idx[-1]][:10]
del lineas[idx[-1]]
c = "".join(lineas)
m = re.search(r"_\(y (\d+) versiones anteriores", c)
if not m:
    raise SystemExit("no encuentro la nota de cierre")
c = c.replace(m.group(0), "_(y %d versiones anteriores" % (int(m.group(1)) + 1))
escribir(CLAUDE, c)
print("CLAUDE.md: fila v532 + entorno · se cayo %s · %d bytes" % (vieja.strip(),
                                                             len(c.encode("utf-8"))))

n = io.open(NEG, encoding="utf-8").read()
_R_VIEJO = ("migrar esos 22 usos queda pendiente, sin urgencia de\n"
            "cliente pero sin olvidarlo.")
_R_NUEVO = ("y en v532 (30/09) se migraron los 22\n"
            "usos, así que la app ya no depende de esa función.")
unica(n, _R_VIEJO, "riesgo", "NEGOCIO.md")
n = n.replace(_R_VIEJO, _R_NUEVO)
unica(n, NEG_VIEJA, "pendiente", "NEGOCIO.md")
_i = n.index(NEG_VIEJA)
_fin = n.index("\n\n", _i)
n = n[:_i] + NEG_NUEVA + n[_fin:]
escribir(NEG, n)
print("NEGOCIO.md: pendiente de la migracion tachado")
