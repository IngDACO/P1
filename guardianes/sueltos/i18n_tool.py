"""Herramienta de traducción por POSICIÓN. Se usa en todas las fases.

Extrae los literales que se PINTAN y los reescribe por offset exacto (AST), así que
no toca ni una coma del resto del fichero — a diferencia de `ast.unparse`, que
reescribiría comentarios y formato.

Dos modos, y la diferencia importa:
  · cadena SUELTA  → se envuelve en `t("English")`  → traducible al español después.
  · parte de un F-STRING → se traduce EN SITIO, sin envolver. Envolverla exigiría
    reestructurar la llamada a `t("... {n} ...", n=…)`, que es un cambio de forma y
    no de texto. Quedan en inglés fijo: es justo «lo que implique menos esfuerzo»
    que pidió el usuario para el español.
"""
import ast
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# lo que PINTA texto: Streamlit + los helpers propios de la app
DISP_ATTR = {
    "write", "markdown", "caption", "info", "success", "warning", "error", "header",
    "subheader", "title", "button", "download_button", "form_submit_button", "checkbox",
    "radio", "selectbox", "multiselect", "text_input", "text_area", "number_input",
    "date_input", "time_input", "slider", "metric", "expander", "popover", "toast",
    "file_uploader", "toggle", "segmented_control", "dialog", "pills", "link_button",
    "status", "exito", "aviso", "elegir", "confirmar_borrado", "chip", "section",
    "kpi_row", "data_editor", "dataframe", "progress", "form", "container", "tabs",
}
DISP_KW = {"label", "help", "placeholder", "body", "title", "icon", "text", "value"}

# ⚠️ Su PRIMER argumento posicional NO es una etiqueta:
#   st.form(key)  ·  st.data_editor(data)  ·  st.dataframe(data)  ·  st.progress(value)
#   ·  st.container(...)
# Traducir ahí renombraría la CLAVE del widget — y envolverla en `t()` la haría depender
# del idioma de la pantalla, así que el estado del formulario se perdería al cambiarlo.
# Sus kwargs (`label`, `help`, `text`) sí se traducen.
SIN_LABEL_POS = {"form", "container", "data_editor", "dataframe", "progress"}

# ⚠️ Cuántos posicionales del PRINCIPIO hay que saltarse porque NO son etiqueta.
# `ui.confirmar_borrado(key, texto)`: el 1º es la clave del widget y el 2º sí es el
# texto. Traducir la clave la haría depender del idioma y la casilla perdería su estado.
SALTAR_POS = {"confirmar_borrado": 1}

# Helpers de DISPLAY propios de la app: lo que reciben es texto que se pinta.
PROPIOS = {"_kpi", "_kpi_card", "_kpi_pies", "_tarjeta", "_totales_html", "_chip_estado",
           "kpi_row", "chip", "section", "_ind_card", "_barras_html", "_torta_html"}

# ⚠️ SOLO en estos se desciende a listas/tuplas: `T.kpi_row([("Subtotal", …, "antes de
# impuesto"), …])` lleva las etiquetas DENTRO de una lista de tuplas y el extractor no
# las veía. NO se desciende en los widgets de Streamlit: la lista de un `selectbox` son
# sus OPCIONES, y esas se guardan en la hoja — traducirlas rompería la lectura.
DESCENDER = {"kpi_row", "_kpi_pies", "_barras_html", "_torta_html"}

ES = re.compile(
    r"[áéíóúÁÉÍÓÚñÑ¿¡]|\b(el|la|los|las|del|con|para|por|que|una|un|en|su|al|lo|es|son|"
    r"no|de|se|y|como|desde|hasta|obra|hueco|pared|riel|cabina|proyecto|proyectos|usuario|"
    r"usuarios|fecha|fechas|guardar|eliminar|borrar|crear|nuevo|nueva|cliente|clientes|"
    r"horas|dias|día|días|más|sin|todos|todas|este|esta|hay|ver|tiene|puede|debe|ya|"
    r"aún|solo|cada|otro|otra|nada|algo|cuando|donde|quien|cuál|qué|añadir|elegir)\b",
    re.I)


# ⚠️ v439 — EL FILTRO POR IDIOMA ES EL AGUJERO. `ES` busca acentos y palabras
# funcionales, así que «Fichar», «Firma», «Guardar», «Nombre», «Pendientes», «Sitios»
# o «Mis ausencias» NO casan y quedaban FUERA de la extracción: con él di F2 por
# terminada y quedaban 47 etiquetas. Por defecto se extrae TODO lo que se pinta y la
# decisión de qué es etiqueta y qué es dato se toma al construir el diccionario, que
# es donde se puede mirar. `ES` se conserva solo para ordenar/priorizar.
_NO_TEXTO = re.compile(
    r"^\s*(</?\w|;|\{|\}|:gray\[|:red\[|:blue\[)"          # HTML / markdown de color
    r"|style=|font-|border|background|margin|padding|flex|display:"
    r"|^https?:|^#[0-9a-fA-F]{3,8}$|^:material/[\w_]+:$|^[\W\d_]+$")


def _es(t):
    return bool(t) and bool(t.strip()) and bool(ES.search(t))


def _pintable(t):
    """¿Es texto que ve una persona? (no HTML, no CSS, no un token de icono suelto)."""
    v = (t or "").strip()
    return len(v) >= 3 and not _NO_TEXTO.search(v) and bool(re.search(r"[A-Za-zÁ-ú]{3}", v))


def piezas(ruta: Path, solo_es: bool = False):
    """[{lin, col, elin, ecol, txt, fstr}] de cada literal PINTADO.

    `solo_es=True` recupera el comportamiento viejo (solo lo que parece español) y no
    debe usarse para decidir si una fase está terminada: es justo lo que falló en F2.
    """
    _quiero = _es if solo_es else _pintable
    src = ruta.read_text(encoding="utf-8")
    tr = ast.parse(src)
    out = []
    for x in ast.walk(tr):
        if not isinstance(x, ast.Call):
            continue
        f = x.func
        nom = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        # ⚠️ `st.column_config.NumberColumn("Importe", …)` — la CABECERA de una columna
        # de tabla es de lo más visible de la app y no estaba en la lista: 71 en el repo.
        # Se traduce solo la ETIQUETA (primer posicional / `label`); la CLAVE del dict
        # `column_config={"Importe": …}` es el nombre de la columna del dataframe y NO
        # se toca, o `st.data_editor` devolvería columnas que nadie sabe leer.
        _es_columna = isinstance(f, ast.Attribute) and nom.endswith("Column")
        if nom not in DISP_ATTR and nom not in PROPIOS and not _es_columna:
            continue
        # ⚠️ `logger.warning` / `logger.error` / `logger.info` comparten NOMBRE con
        # `st.warning` y compañía. Sin esta guarda, el traductor envolvería mensajes
        # de LOG en `t()` — texto que no ve ningún usuario y que además se lee en los
        # registros del servidor. Se descarta por el receptor, no por el nombre.
        if isinstance(f, ast.Attribute):
            recv = f.value
            rid = recv.id if isinstance(recv, ast.Name) else (
                recv.attr if isinstance(recv, ast.Attribute) else "")
            if rid.lower() in {"logger", "logging", "log", "_log", "_logger"}:
                continue
        if _es_columna:
            # solo el 1er posicional (la etiqueta) + label/help; nunca `format` ni `width`
            args = (list(x.args)[:1]
                    + [k.value for k in x.keywords if k.arg in ("label", "help")])
        else:
            _pos = [] if nom in SIN_LABEL_POS else list(x.args)[SALTAR_POS.get(nom, 0):]
            args = _pos + [k.value for k in x.keywords if k.arg in DISP_KW]
            if nom in DESCENDER:
                _plano = []
                _marcados_f = set()
                for a in args:
                    if isinstance(a, (ast.List, ast.Tuple, ast.Set)):
                        # ⚠️ Fuera los literales que son el ÍNDICE de un subíndice
                        # (`_tot["margen_pct"]`, `f["a_pagar"]`): son CLAVES de dict,
                        # no texto — y aparecen en la misma tupla que la etiqueta.
                        _claves = {id(n_.slice) for n_ in ast.walk(a)
                                   if isinstance(n_, ast.Subscript)}
                        # ⚠️ y fuera lo que YA está dentro de `t(...)`: al descender por
                        # la lista se recogían también los traducidos, así que el
                        # recuento de «sin envolver» salía inflado y no medía nada.
                        for _c in ast.walk(a):
                            if (isinstance(_c, ast.Call) and isinstance(_c.func, ast.Name)
                                    and _c.func.id in ("t", "d", "_d")):
                                for _cc in ast.walk(_c):
                                    if isinstance(_cc, ast.Constant):
                                        _claves.add(id(_cc))
                        # ⚠️ Y hay que conservar QUIÉN vive dentro de una f-string: al
                        # aplanar se perdía y 7 trozos de f-string se contaban como
                        # cadenas sueltas «sin envolver», que es justo lo contrario.
                        _en_f = {id(v) for n_ in ast.walk(a)
                                 if isinstance(n_, ast.JoinedStr) for v in n_.values
                                 if isinstance(v, ast.Constant)}
                        _marcados_f |= _en_f
                        _plano += [n_ for n_ in ast.walk(a)
                                   if isinstance(n_, ast.Constant) and id(n_) not in _claves]
                    else:
                        _plano.append(a)
                args = _plano
        _mf = _marcados_f if nom in DESCENDER else set()
        for a in args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) and _quiero(a.value):
                out.append({"lin": a.lineno, "col": a.col_offset,
                            "elin": a.end_lineno, "ecol": a.end_col_offset,
                            "txt": a.value, "fstr": id(a) in _mf})
            elif isinstance(a, ast.JoinedStr):
                for v in a.values:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str) and _quiero(v.value):
                        out.append({"lin": v.lineno, "col": v.col_offset,
                                    "elin": v.end_lineno, "ecol": v.end_col_offset,
                                    "txt": v.value, "fstr": True})
    # de atrás hacia delante, para que un reemplazo no mueva los offsets del siguiente
    out.sort(key=lambda p: (p["lin"], p["col"]), reverse=True)
    return out


def aplicar(ruta: Path, trad: dict, envolver="t"):
    """Sustituye por posición. Devuelve (n_hechos, [no_traducidos])."""
    src = ruta.read_text(encoding="utf-8")
    lin = src.splitlines(True)
    hechos, faltan = 0, []
    for p in piezas(ruta):
        eng = trad.get(p["txt"])
        if eng is None:
            faltan.append(p["txt"])
            continue
        if p["lin"] != p["elin"]:      # multilínea: se deja, hay que mirarla a mano
            faltan.append(p["txt"])
            continue
        i = p["lin"] - 1
        l = lin[i]
        crudo = l[p["col"]:p["ecol"]]
        if p["fstr"]:
            # ⚠️ dentro de un f-string se cambia SOLO el texto; las llaves y el resto
            # del literal se quedan como están.
            nuevo = eng
        else:
            q = '"' if '"' not in eng else "'"
            nuevo = f'{envolver}({q}{eng}{q})' if envolver else f'{q}{eng}{q}'
        lin[i] = l[:p["col"]] + nuevo + l[p["ecol"]:]
        hechos += 1
    if hechos:
        ruta.write_text("".join(lin), encoding="utf-8")
    return hechos, faltan


if __name__ == "__main__":
    RAIZ = Path(r"C:\Users\diego\P1\survey_app")
    if sys.argv[1] == "extraer":
        todo, ns, nf = {}, 0, 0
        for rel in sys.argv[2:]:
            ps = piezas(RAIZ / rel)
            for p in ps:
                todo.setdefault(p["txt"], None)
                ns += 0 if p["fstr"] else 1
                nf += 1 if p["fstr"] else 0
        print(json.dumps(list(todo), ensure_ascii=False, indent=0))
        print(f"### {len(todo)} únicas · {ns} sueltas · {nf} en f-string", file=sys.stderr)
    elif sys.argv[1] == "contar":
        ns = nf = 0
        for rel in sys.argv[2:]:
            for p in piezas(RAIZ / rel):
                if p["fstr"]:
                    nf += 1
                else:
                    ns += 1
        print(f"sueltas={ns}  f-string={nf}")
