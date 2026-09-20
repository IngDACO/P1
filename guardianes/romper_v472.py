# -*- coding: utf-8 -*-
"""Roturas de v472: se reintroduce cada fallo que el guardian dice proteger.

⚠️ Verde de base PRIMERO (v459/v461): sin ese paso, una tanda entera sale «cazada»
sin probar nada — pasa si el guardian esta rojo, y tambien si REVIENTA (v463).
⚠️ Y NUNCA en paralelo con la suite (v455): este script modifica ficheros del repo.
"""
import io
import os
import subprocess
import sys

SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def corre(g):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    ("las hojas dejan de ser GLOBALES (una biblioteca vacia por cliente)",
     "core/timeclock.py", '"library", "librarymodels"}', '"librarymodels"}'),

    ("`Library` sale del LOTE (se leeria vacio PARA SIEMPRE, sin error)",
     "core/hojas.py", '    "Library", "LibraryModels",\n', '    "LibraryModels",\n'),

    ("`_ws` vuelve a `_get_worksheet` (escribe en un libro y lee de otro, v404)",
     "core/library.py", "return timeclock.get_sheet(SHEET, tuple(HEADERS)), None",
     "return timeclock._get_worksheet()[0], None"),

    ("un `download_button` por foto en la galeria (baja TODO Drive, v147)",
     "core/library_ui.py", '            _c.caption("**%s**" % it.get("Title", ""))',
     '            _c.download_button("d", data=b"", key="x%s" % it.get("ID", ""))\n'
     '            _c.caption("**%s**" % it.get("Title", ""))'),

    ("la galeria deja de paginar",
     "core/library_ui.py", "_vis = fotos[_pag * _POR_PAGINA:(_pag + 1) * _POR_PAGINA]",
     "_vis = fotos"),

    ("el alta deja de colgar de `_puede_subir()` (sube cualquiera)",
     "core/library_ui.py", "    if _puede_subir():\n        st.markdown(\"---\")\n        _alta()",
     "    if True:\n        st.markdown(\"---\")\n        _alta()"),

    ("al FILAR se escribe la fila ANTES de subir el archivo (v343)",
     "core/library_ui.py", "    drive_id = filename = mime = \"\"\n    if up is not None:",
     "    ok, msg = LIB.add_item(titulo, seccion, tipo)\n"
     "    drive_id = filename = mime = \"\"\n    if up is not None:"),

    ("al BORRAR se quita la fila ANTES que el archivo (huerfano, v456)",
     "core/library_ui.py", "                if _did and dr is not None:",
     "                ok, msg = LIB.delete_item(lid)\n"
     "                if _did and dr is not None:"),

    ("`_next_id` vuelve a contar FILAS (el fallo REAL de v428)",
     "core/library.py", 'return hojas.siguiente_id_libre("LIB-", mx, propia=SHEET)',
     'return "LIB-%04d" % (len(ws.get_all_values()))'),

    ("`siguiente_id_libre` con los argumentos CAMBIADOS (ValueError que el except se traga)",
     "core/library.py", 'hojas.siguiente_id_libre("LIB-", mx, propia=SHEET)',
     'hojas.siguiente_id_libre(SHEET, "LIB", mx)'),

    ("la fila posicional pierde un valor (el fallo que mato a create_project, v363)",
     "core/library.py", '            str(filename or ""), str(mime or ""), str(creado_por or ""),\n',
     '            str(filename or ""), str(creado_por or ""),\n'),

    ("`t` vuelve a usarse como fila en el buscador (el fallo real de v440)",
     "core/home_ui.py", '_num = str(_trb.get("Number", "")).strip()',
     '_num = str(t.get("Number", "")).strip()'),

    ("la seccion desaparece de la nav del CAMPO",
     "core/home_ui.py", '    ("biblioteca",   ":material/menu_book: Library"),\n', ''),

    ("el despachador compara contra el DISPLAY en vez del ID (v303/v423)",
     "core/home_ui.py", 'elif key == "biblioteca":',
     'elif key == ":material/menu_book: Library":'),

    ("un tipo vuelve al español (saldria crudo en la tabla, v462/v463)",
     "core/library.py", 'TIPOS = ["photo", "manual", "datasheet", "diagram", "other"]',
     'TIPOS = ["foto", "manual", "datasheet", "diagram", "other"]'),
]

# ⚠️ Un cambio INOCUO que debe seguir pasando. Sin el, un guardian que revienta o que
# grita con cualquier edicion no se distingue de uno que funciona (v461/v463).
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/library.py", "TIPOS = [", "# comentario inocuo del control\nTIPOS = [")


def prueba(desc, fich, viejo, nuevo, espera_rojo=True):
    p = os.path.join(RAIZ, fich.replace("/", os.sep))
    orig = io.open(p, encoding="utf-8").read()
    if orig.count(viejo) < 1:
        return "  ??       ancla ausente en %s -> %s" % (fich, desc)
    try:
        io.open(p, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        verde = corre("verif_v472")
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(orig)
    if espera_rojo:
        return "  %s %-70s" % ("CAZADA  " if not verde else "ESCAPADA", desc)
    return "  %s %-70s" % ("ok      " if verde else "FALSO+  ", desc)


print("0. Verde de base (sin esto, el recuento de abajo no probaria nada)")
if not corre("verif_v472"):
    print("   ROJO -> se arregla el guardian ANTES de correr las roturas")
    sys.exit(2)
print("   verde")

print("\n1. Roturas (cada una debe ponerse ROJA)")
res = [prueba(*r) for r in ROTURAS]
for r in res:
    print(r)

print("\n2. Control (debe seguir VERDE)")
_ctrl = prueba(*CONTROL, espera_rojo=False)
print(_ctrl)

cz = sum(1 for r in res if "CAZADA" in r)
esc = sum(1 for r in res if "ESCAPADA" in r or "??" in r)
print("\n=== %d de %d roturas cazadas · %d escapadas · control %s ===" % (
    cz, len(ROTURAS), esc, "ok" if "ok " in _ctrl else "MAL"))
sys.exit(0 if (cz == len(ROTURAS) and "ok " in _ctrl) else 1)
