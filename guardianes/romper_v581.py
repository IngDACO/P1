# -*- coding: utf-8 -*-
"""Bateria de roturas de v581 («no dejes nada pendiente»: IDs que no se reciclan y la rejilla
de cifras). ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455). Anclas en
LÍNEA y literales (v570). `--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v581"
TOPE_S = 400


def _sin_helper(pref, mx, hoja, mod, ancho=4, extra=""):
    """El `try` del helper → el `max + 1` a pelo de antes de v581."""
    a = "" if ancho == 4 else f", ancho={ancho}"
    return [(f"    try:\n        from core import hojas\n"
             f"        return hojas.siguiente_id_libre(\"{pref}\", {mx}, propia={hoja}{a})\n"
             f"    except Exception as e:\n"
             f"        logger.warning(\"{mod}: no se pudo comprobar IDs referenciados: %s\", e)\n"
             f"        return f\"{pref}{{{mx} + 1:0{ancho}d}}\"\n",
             f"    return f\"{pref}{{{mx} + 1:0{ancho}d}}\"\n")]


ROTURAS = [
    ("⚠️ COT vuelve a `max + 1` (la primera cotización real sería otra vez la COT-0001)",
     "core/quotes.py", [("    cid = _id_libre(mx_id)\n", '    cid = f"COT-{mx_id + 1:04d}"\n')]),
    ("ALR vuelve a `max + 1`", "core/alerts.py", [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("ALR-", mx, propia=ALERTS_SHEET)\n    except Exception as e:\n        logger.warning("alerts: no se pudo comprobar IDs referenciados: %s", e)\n        return f"ALR-{mx + 1:04d}"\n', '    return f"ALR-{mx + 1:04d}"\n')]),
    ("PS vuelve a `max + 1`", "core/prestart.py", [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("PS-", mx, propia=SHEET)\n    except Exception as e:\n        logger.warning("prestart: no se pudo comprobar IDs referenciados: %s", e)\n        return f"PS-{mx + 1:04d}"\n', '    return f"PS-{mx + 1:04d}"\n')]),
    ("CAT vuelve a `max + 1`", "core/catalogo.py",
     [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("CAT-", mx, propia=SHEET, ancho=5)\n    except Exception as e:\n        logger.warning("catalogo: no se pudo comprobar IDs referenciados: %s", e)\n        return f"CAT-{mx + 1:05d}"\n', '    return f"CAT-{mx + 1:05d}"\n')]),
    ("ORD vuelve a `max + 1`", "core/orders.py", [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("ORD-", mx, propia=SHEET, ancho=5)\n    except Exception as e:\n        logger.warning("orders: no se pudo comprobar IDs referenciados: %s", e)\n        return f"ORD-{mx + 1:05d}"\n', '    return f"ORD-{mx + 1:05d}"\n')]),
    ("FAC vuelve a `max + 1`", "core/invoices.py",
     [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("FAC-", mx, propia=FACTURAS_SHEET)\n    except Exception as e:\n        logger.warning("invoices: no se pudo comprobar IDs referenciados: %s", e)\n        return f"FAC-{mx + 1:04d}"\n', '    return f"FAC-{mx + 1:04d}"\n')]),
    ("ACT vuelve a `max + 1`", "core/inventory.py",
     [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("ACT-", mx, propia=ACTIVOS_SHEET)\n    except Exception as e:\n        logger.warning("inventory: no se pudo comprobar IDs referenciados: %s", e)\n        return f"ACT-{mx + 1:04d}"\n', '    return f"ACT-{mx + 1:04d}"\n')]),
    ("MOV vuelve a `max + 1`", "core/inventory.py",
     [('    try:\n        from core import hojas\n        return hojas.siguiente_id_libre("MOV-", mx, propia=MOV_SHEET)\n    except Exception as e:\n        logger.warning("inventory: no se pudo comprobar IDs referenciados: %s", e)\n        return f"MOV-{mx + 1:04d}"\n', '    return f"MOV-{mx + 1:04d}"\n')]),
    ("⚠️ las nóminas vuelven a numerar fila a fila sin comprobar", "core/payroll.py",
     [('        return hojas.siguientes_ids_libres("NOM-", mx, n, propia=NOMINAS_SHEET)\n',
       '        return [f"NOM-{mx + k:04d}" for k in range(1, n + 1)]\n')]),
    ("⚠️ el roster en lote vuelve a numerar por NÚMERO DE FILAS", "core/roster.py",
     [("    next_n = 0\n    for _r in vals[1:]:\n", "    next_n = len(vals) - 1\n    for _r in []:\n")]),
    ("…o sin saltar los referenciados", "core/roster.py",
     [('            _ids = hojas.siguientes_ids_libres("ROS-", next_n, len(nuevas),\n'
       '                                               propia=ROSTER_SHEET)\n',
       '            _ids = [f"ROS-{next_n + k:04d}" for k in range(1, len(nuevas) + 1)]\n')]),
    ("⚠️ `siguientes_ids_libres` da UNO aunque se pidan varios", "core/hojas.py",
     [("    for _k in range(max(1, int(cuantos or 1))):\n", "    for _k in range(1):\n")]),
    ("⚠️ `ids_referenciados` vuelve a la LISTA (sin PreStarts)", "core/hojas.py",
     [("        titulos = [h for h in _titulos(sheet_id) if h.strip().lower() != propia_l]\n",
       '        titulos = [h for h in tuple(HOJAS_LECTURA) + ("Auditoria",)\n'
       "                   if h.strip().lower() != propia_l]\n")]),
    ("⚠️ el lote vuelve a pedir `'{h}'` a mano (un apóstrofo lo tumba entero)", "core/hojas.py",
     [("        r = lib.values_batch_get([absolute_range_name(h) for h in titulos])\n",
       "        r = lib.values_batch_get([f\"'{h}'\" for h in titulos])\n")]),
    ("…o excluye la propia por el nombre NUEVO (con el viejo, se colaría)", "core/hojas.py",
     [("            propia_l = timeclock.titulo_real(str(propia).strip(), sheet_id).strip().lower()\n",
       "            pass\n")]),
    ("⚠️ facturas: lectura fresca fallida → desde CERO (FAC-0001, que existe)", "core/invoices.py",
     [('        return [str(r.get(col, "")) for r in _records()]\n', "        return []\n")]),
    ("…inventario", "core/inventory.py",
     [('        return [str(r.get(col, "")) for r in _records(title)]\n', "        return []\n")]),
    ("…órdenes", "core/orders.py",
     [('        for r in _records():\n            i = str(r.get("ID", ""))\n            if i.startswith("ORD-"):\n',
       '        for r in []:\n            i = str(r.get("ID", ""))\n            if i.startswith("ORD-"):\n')]),
    ("…catálogo", "core/catalogo.py",
     [('        for r in _records():\n            i = str(r.get("ID", ""))\n            if i.startswith("CAT-"):\n',
       '        for r in []:\n            i = str(r.get("ID", ""))\n            if i.startswith("CAT-"):\n')]),
    ("…cotizaciones", "core/quotes.py", [("        recs = _records()\n", "        return 0, 0\n")]),
    ("…nóminas", "core/payroll.py",
     [('        ids = [r.get("ID", "") for r in _records()]\n', "        ids = []\n")]),
    ("⚠️ el NÚMERO de factura vuelve a salir de la caché (dos facturas con el mismo)",
     "core/invoices.py",
     [("        recs = columnas.canonizar(w.get_all_records(numericise_ignore=[\"all\"]))\n"
       "    except Exception as e:\n        logger.warning(\"invoices._next_numero:",
       "        recs = _records()\n"
       "    except Exception as e:\n        logger.warning(\"invoices._next_numero:")]),
    ("⚠️ MOV vuelve a sacar el máximo de la CACHÉ", "core/inventory.py",
     [("    for mid in _ids_frescos(MOV_SHEET):\n",
       '    for mid in [r.get("ID", "") for r in _records(MOV_SHEET)]:\n')]),
    ("⚠️ StageProgress vuelve a la posición en el lote (IDs repetidos)", "core/stage_progress.py",
     [('"SP-%s-%d-%d" % (pid, _et, _sp_n + len(_nuevas))', '"SP-%s-%d-%d" % (pid, _et, len(_nuevas))')]),
    ("⚠️ `.cpx-kpis` vuelve a flex (la huérfana a todo el ancho)", "core/theme.py",
     [("  display: grid; gap: 10px; margin: 2px 0 12px;\n",
       "  display: flex; gap: 10px; flex-wrap: wrap; margin: 2px 0 12px;\n")]),
    ("…o la rejilla sin la base de la tarjeta", "core/theme.py",
     [("minmax(min(100%, var(--cpx-min, 150px)), 1fr)", "minmax(min(100%, var(--cpx-min, 104px)), 1fr)")]),
    ("⚠️ Timeclock vuelve a su flex propio", "core/timeclock_ui.py",
     [("""    st.markdown('<div class="cpx-kpis" style="--cpx-min:132px;margin:0 0 12px">'\n""",
       """    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px">'\n""")]),
    # ⚠️ v595 · Re-anclada con su razón: la fila HTML de Belting (`_kpi_row`, base 96 px) ya no
    # existe — sus tres cifras son BOTONES activos en la rejilla del tema (`T.por_fila`), como
    # la plomada, Rails y Buffers desde v592-v594. La rotura rompe lo que ahora la sostiene.
    ("…o Belting fuera de la rejilla del tema", "core/belting_ui.py",
     [("""    st.markdown(T.por_fila("cpx_belt_kpis", 3), unsafe_allow_html=True)\n""",
       """    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap">', unsafe_allow_html=True)\n""")]),
    ("…o Status de la obra con su flex propio", "core/projects_ui.py",
     [("""    st.markdown('<div class="cpx-kpis" style="margin:8px 0 10px">'\n""",
       """    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 10px">'\n""")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", "core/hojas.py",
           [("def _titulos(sheet_id: str = \"\") -> list:\n",
             "def _titulos(sheet_id: str = \"\") -> list:   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc))
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
