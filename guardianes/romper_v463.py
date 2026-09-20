# -*- coding: utf-8 -*-
"""Rompe v463 de 7 formas + 1 CONTROL. El guardian tiene que cazar las 7 y dejar
pasar el control: uno que grita con cualquier edicion no distingue nada."""
import io, os, shutil, subprocess, sys, tempfile

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v463.py")

ROTURAS = [
    ("inventory_ui.py", '"Category":   _etq(str(a.get("Categoria", ""))) or "—"',
     '"Category":   a.get("Categoria", "") or "—"', "celda de inventario cruda", True),
    ("catalogo_ui.py", '"Tipo": _etq(str(i.get("Tipo", "")))',
     '"Tipo": str(i.get("Tipo", ""))', "celda de catalogo cruda", True),
    ("i18n.py", '"Otros": "Other",', "", "'Otros' fuera del mapa", True),
    # ⚠️ prueba que el chequeo 3 DESCUBRE las listas:  se define por
    # NOMBRE, asi que la version con lista fija ni la miraba.
    ("i18n.py", '"recibida": "received",', "", "'recibida' fuera del mapa (lista descubierta)", True),
    ("i18n.py", '"disponible": "available", "en_uso": "in use", "mantenimiento": "maintenance",',
     "", "estados de inventario fuera del mapa", True),
    ("inventory.py", 'ESTADOS = ["disponible", "en_uso", "mantenimiento", "dañado", "baja"]',
     'ESTADOS = ["available", "in use", "maintenance", "damaged", "written off"]',
     "se traduce el DATO", True),
    ("inventory_ui.py", '_EST_COLOR = {"disponible": "green", "en_uso": "blue", "mantenimiento": "orange",',
     '_EST_COLOR = {"disponible": ":green[available]", "en_uso": "blue", "mantenimiento": "orange",',
     "el TEXTO vuelve al modulo", True),
    ("inventory_ui.py", '"Estado":      _etq(str(a.get("Estado", ""))),',
     '"Estado":      _est_lbl(a.get("Estado", "")),', "markdown de color en una celda", True),
    ("i18n.py", '"bodega": "warehouse", "usuario": "user", "reparacion": "under repair",',
     "", "'bodega' fuera del mapa", True),
    # la peor: traducir DENTRO de ubic_str -> el historial guardaria ingles
    ("inventory.py", "def ubic_str(a: dict, etq=None) -> str:",
     "def ubic_str(a: dict, etq=__import__('core.i18n', fromlist=['x']).etiqueta) -> str:",
     "ubic_str traduce por defecto (metería ingles en la HOJA)", True),
    ("catalogo_ui.py", '"Unidad": _etq(str(i.get("Unidad", ""))) or "—",',
     '"Unidad": i.get("Unidad", "") or "—",', "unidad cruda", True),
    # CONTROL: cambio inocuo -> el guardian NO debe saltar
    ("inventory_ui.py", "def _est_lbl(estado) -> str:",
     "def _est_lbl(estado) -> str:  # comentario inocuo", "CONTROL (debe pasar)", False),
]

cazadas = escapadas = 0
for fich, viejo, nuevo, desc, debe_fallar in ROTURAS:
    p = os.path.join(RAIZ, "core", fich)
    orig = io.open(p, encoding="utf-8").read()
    if orig.count(viejo) != 1:
        print("[!! ] ancla no unica (%d) en %s -> %s" % (orig.count(viejo), fich, desc))
        escapadas += 1
        continue
    bak = tempfile.mktemp(suffix=".bak")
    shutil.copy2(p, bak)
    try:
        io.open(p, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, GUARD], capture_output=True, env=env)
        fallo = r.returncode != 0
        if fallo == debe_fallar:
            print("[ok ] %s" % desc)
            cazadas += 1
        else:
            print("[!! ] %s  (returncode=%d)" % (desc, r.returncode))
            escapadas += 1
    finally:
        shutil.copy2(bak, p)
        os.remove(bak)

print("")
print("cazadas: %d · escapadas: %d" % (cazadas, escapadas))
sys.exit(1 if escapadas else 0)
