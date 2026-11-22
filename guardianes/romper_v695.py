# -*- coding: utf-8 -*-
"""Batería de roturas de v695. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v695"
TOPE_S = 400
PL = "core/plantas.py"
ST = "core/stages.py"
SP = "core/stage_progress.py"
MEM = "core/agente_memoria.py"
DLU = "core/daily_log_ui.py"
SPU = "core/stage_progress_ui.py"
TH = "core/theme.py"

ROTURAS = [
    ("D2 · un rango («2-5») no se expande", PL,
     [("            if prev is not None and _RANGO.search(sep) and n >= prev:\n", "            if False:\n")]),
    ("⚠️ D2 · «L2» (el ascensor 2) cuenta como planta", PL,
     [('_PAL = r"(?:levels?|lvls?|floors?|stops?|landings?)"', '_PAL = r"(?:levels?|lvls?|floors?|stops?|landings?|L)"')]),
    ("D2 · «all levels» no es entera", PL,
     [("    if _TODAS.search(s):\n        return list(range(1, ns + 1))\n", "")]),
    ("D2 · una planta que no existe (12 de 8) cuenta", PL,
     [("    return sorted(x for x in out if 1 <= x <= ns)\n", "    return sorted(out)\n")]),
    ("⚠️ D2 · Landing Doors deja de ser por plantas", ST,
     [("POR_PLANTAS = {(PISTA_INSTALL, 7)}            # Landing Doors", "POR_PLANTAS = set()")]),
    ("D2 · la fila nueva sin Levels (no cuadra con la cabecera)", SP,
     [('str(c.get("nota", "")), str(origen), str(quien), _ahora, _dia, _nv])',
       'str(c.get("nota", "")), str(origen), str(quien), _ahora, _dia])')]),
    ("D2 · una entera guarda plantas", SP,
     [('               if c.get("niveles") and 0 < _pc < 100 else "")', '               if c.get("niveles") else "")')]),
    ("⚠️ H14 · deshacer a mano no corrige la memoria", SP,
     [('            _deshechos.append((str(_pr.get("Note", "")).strip(), _ac))\n', "            pass\n")]),
    ("H14 · también desaprende lo que pone a 0 un parte (no a mano)", SP,
     [("        if (origen == MANUAL and _pc <= 0 and _pr and", "        if (_pc <= 0 and _pr and")]),
    ("H14 · desaprender toca las reglas de la oficina", MEM,
     [('        if _es_olvidada(r) or str(r.get("Kind", "")) == REGLA:\n            continue\n',
       "        if _es_olvidada(r):\n            continue\n")]),
    ("H14 · desaprender no suma el rechazo", MEM,
     [('"values": [[str(x + 1)]]}', '"values": [[str(x)]]}')]),
    ("⚠️ D2 · las plantas de otro parte no se suman", DLU,
     [('"todas": sorted(set(nv) | _ya.get((int(orden), str(act)), set())),',
       '"todas": sorted(set(nv)),')]),
    ("⚠️ D2 · Confirm acredita entera (sin `_a_medias`)", DLU,
     [("_a_medias(PP.creditos(ticks, lid), _plantas_d.get(d))", "PP.creditos(ticks, lid)")]),
    ("D2 · `_a_medias` no toca nada", DLU,
     [("        x = (plantas or {}).get((int(c[\"etapa\"]), str(c[\"actividad\"])))\n        if x:\n",
       "        x = (plantas or {}).get((int(c[\"etapa\"]), str(c[\"actividad\"])))\n        if x and False:\n")]),
    ("D2 · la casilla no dice las plantas", DLU,
     [('if st.checkbox(f["actividad"] + (("  ·  " + _etq_plantas(_pl)) if _pl else ""), value=_seg,',
       'if st.checkbox(f["actividad"], value=_seg,')]),
    ("H12 · lo ya enviado cuenta como no enviado", DLU,
     [('if f.get("clase") == "problem" and f.get("texto", "") and f.get("texto", "") not in _ya]',
       'if f.get("clase") == "problem" and f.get("texto", "")]')]),
    ("H12 · lo empezado sin «Add to To-do»", DLU,
     [("        if todo:\n            for _ie, x in enumerate(_emp):\n",
       "        if False:\n            for _ie, x in enumerate(_emp):\n")]),
    ("H16 · el To-do sin mayúscula", DLU,
     [("    return tx[:1].upper() + tx[1:]          # v695 · H16", "    return tx")]),
    ("H16 · el To-do sin la fecha del parte", DLU,
     [('        _tx = pet["texto"] + ((" " + t("(from the log of {d})", d=_dmy(_dl.get("Date")))) if _dl.get("Date") else "")\n',
       '        _tx = pet["texto"]\n')]),
    ("H16 · con la fecha, el botón se ofrece otra vez", DLU,
     [('    if any(TA.normaliza(r.get("Text")).startswith(TA.normaliza(tx)) for r in TA.pendientes(pid)):',
       '    if any(TA.normaliza(r.get("Text")) == TA.normaliza(tx) for r in TA.pendientes(pid)):')]),
    ("H22 · la oficina, «desde hoy» en vez de a los 2 días", DLU,
     [("_dtm.timedelta(days=DL.DIAS_OFICINA)", "_dtm.timedelta(days=0)")]),
    ("H17 · un parte anterior al inicio, sin aviso", DLU,
     [("                if _ini and dia and dia < _ini:\n", "                if False:\n")]),
    ("D2 · Progress no dice que está a medias", SPU,
     [('    if not 0 < _num(pct) < 100:\n        return ""\n    _lv =', '    return ""\n    _lv =')]),
    ("D2 · el «?» de una a medias desaparece", SPU,
     [("    if _num(pct) <= 0:                         # v695 · D2: también a medias (las plantas)\n",
       "    if _num(pct) < 100:\n")]),
    ("H11 · «(1 changes)» otra vez", SPU,
     [('(t(":material/save: Save stage {n} (1 change)", n=e["orden"]) if _n_pend == 1 else\n',
       '(t(":material/save: Save stage {n} ({c} changes)", n=e["orden"], c=1) if _n_pend == 1 else\n')]),
    ("⚠️ D3 · el aviso tapa los toques (pointer-events)", TH,
     [("  pointer-events: none; background: #fff; border-radius: 10px;\n",
       "  background: #fff; border-radius: 10px;\n")]),
    ("⚠️ D3 · el aviso vuelve al flujo (empuja la página)", TH,
     [("  position: fixed !important; top: 58px; right: 16px; left: auto !important;\n",
       "  position: relative !important; top: 58px; right: 16px; left: auto !important;\n")]),
    ("D3 · el envoltorio deja su hueco", TH,
     [("  position: absolute !important; height: 0 !important; margin: 0 !important; padding: 0 !important;\n",
       "  height: auto;\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PL,
           [('"""De la columna `Levels` de StageProgress («3,4,5») a {3, 4, 5}."""',
             '"""De la columna `Levels` de StageProgress («3,4,5») a {3, 4, 5} · control."""')])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
