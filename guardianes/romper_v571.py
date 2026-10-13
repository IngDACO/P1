# -*- coding: utf-8 -*-
"""Bateria de roturas de v571. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en la ficha del cliente verificando v570.
⚠️ Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v571"
CU = "core/clientes_ui.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── el resumen activo ──
    ("⚠️ el resumen vuelve a no tocarse (desaparecen las cifras-botón)", CU,
     [("        _cifras_cliente(key, len(proys), activos, av, hrs, cost, al, _con_gx, _con_al)\n", "")]),
    ("⚠️ tocar una cifra deja de abrir el desglose", CU,
     [('                st.session_state[f"_cls_vista::{key}"] = "" if _cur == _s else _s\n', "")]),
    ("«Active» deja de filtrar (salen también las completadas)", CU,
     [('        filas = [f for f in filas if f["estado"] not in ("Completed", "Cancelled", "Archived")]\n',
       "        pass\n")]),
    ("«Hours» deja de ordenar por horas", CU,
     [('        filas.sort(key=lambda f: -f["hrs"])\n', "        pass\n")]),
    ("⚠️ el desglose del coste deja de abrir la obra en Costs", CU,
     [('"💰 Costos" if _v == "cost" else "📊 Estado")', '"📊 Estado")')]),
    ("⚠️ la vista deja de bajar al desglose (queda fuera de la pantalla)", CU,
     [('                st.session_state["_cls_bajar"] = _cur != _s\n', "")]),
    ("las alertas vuelven a no ser una cifra", CU,
     [('    if con_alertas:\n        _K.append(("al", t("Open alerts"), str(al), t("on its jobs")))\n', "")]),
    ("la cifra de alertas deja de ir en rojo", CU,
     [('    if al:\n        st.markdown("<style>.st-key-cpxkpi_cls_al',
       '    if False:\n        st.markdown("<style>.st-key-cpxkpi_cls_al')]),
    ("⚠️ lo abierto deja de ser de ESA ficha (otra lo hereda)", CU,
     [('    return st.session_state.get(f"_cls_vista::{key}", "")\n',
       '    return st.session_state.get("_cls_vista", "")\n'),
      ('                st.session_state[f"_cls_vista::{key}"] = "" if _cur == _s else _s\n',
       '                st.session_state["_cls_vista"] = "" if _cur == _s else _s\n')]),
    # ── los textos ──
    ("⚠️ «… project(s) linked.» vuelve a un f-string sin `t()`", CU,
     [('flash.exito(t("{n} project(s) linked.", n=len(_sel)))',
       'flash.exito(f"{len(_sel)} project(s) linked.")')]),
    ("el pie de archivados vuelve sin `t()`", CU,
     [('st.caption(t(":material/inventory_2: {n} archived client(s) hidden.", n=_n_arch))',
       'st.caption(f":material/inventory_2: {_n_arch} archived client(s) hidden.")')]),
    ("el enlace al mapa vuelve sin `t()`", CU,
     [('t("See the address on the map")', '"See the address on the map"')]),
    ("el estado de cada obra vuelve a salir CRUDO", CU,
     [("{_etq(p.get('Status', ''))}", "{p.get('Status', '')}")]),
    # ── la lista ──
    ("⚠️ el coste de la lista vuelve a dólares enteros (valor)", CU,
     [('**({"Costo": round(r["cost"], 2)} if _hay_costo else {}),',
       '**({"Costo": round(r["cost"], 0)} if _hay_costo else {}),')]),
    ("⚠️ …y el formato vuelve a `$%,d`", CU,
     [('_colcfg["Costo"] = st.column_config.NumberColumn(t("Cost"), format="$%,.2f")',
       '_colcfg["Costo"] = st.column_config.NumberColumn(t("Cost"), format="$%,d")')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           CU, [('    """«0 h» y no «0.0» (como las tarjetas de Locations, v565)."""',
                 '    """«0 h» y no «0.0» (como las tarjetas de Locations, v565). (control)"""')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
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
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g))

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
