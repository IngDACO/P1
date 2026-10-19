# -*- coding: utf-8 -*-
"""Bateria de roturas de v586 (los partes que no movían la curva). ⚠️ Verde de BASE primero
(v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas`
solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v586"
DU = "core/daily_log_ui.py"
VO = "core/vocabulario.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ el campo vuelve a no decir que la obra no tiene plan", DU,
     [('    _sp = _sin_plan(pid)\n    if _sp:\n        st.caption(t(":material/info: This job has no stage plan, so the app cannot suggest "',
       '    _sp = _sin_plan(pid)\n    if False:\n        st.caption(t(":material/info: This job has no stage plan, so the app cannot suggest "')]),
    ("⚠️ el admin vuelve a no decirlo", DU,
     [('    _sp = _sin_plan(pid)\n    if _sp:\n        st.caption(t(":material/info: This job has no stage plan, so the crew\'s daily logs "',
       '    _sp = _sin_plan(pid)\n    if False:\n        st.caption(t(":material/info: This job has no stage plan, so the crew\'s daily logs "')]),
    ("⚠️ un parte sin nada que confirmar vuelve a callarse", DU,
     [("        _nada_que_confirmar(_prev)      # v586 · antes, nada debajo\n", "        pass\n")]),
    ("«Go to Progress» deja de llevar", DU,
     [('                      type="tertiary", on_click=ir_avance)\n', '                      type="tertiary")\n')]),
    ("una localización interna pasa a decir que no tiene plan", DU,
     [("    if P.es_interno(prj):\n        return \"\"\n", "")]),
    ("un plan de catálogo ANTERIOR deja de decirse", DU,
     [('    return SP.version_desfasada(prj) or ("" if SP.plan_de_obra(prj) else "sin")\n',
       '    return "" if SP.plan_de_obra(prj) else "sin"\n')]),
    ("⚠️ «got delivery» deja de reconocerse", VO,
     [('    "delivery": ["Receive lift delivery", "Other deliveries"],\n', "")]),
    ("⚠️ «got toolbox» deja de reconocerse (sin el alias)", VO,
     [('    (re.compile(r"\\b(?:got|get|gets|getting)\\s+(?:(?:the|a|my|our|his|her|their)\\s+)?"\n'
       '                r"tool\\s*-?\\s*box(?:es|s)?\\b(?!\\s*talks?\\b)", re.I), " receive toolbox "),\n', "")]),
    ("⚠️ vuelve «toolbox» a secas (el bloqueo del documento propondría la caja)", VO,
     [('    "delivery": ["Receive lift delivery", "Other deliveries"],\n',
       '    "delivery": ["Receive lift delivery", "Other deliveries"],\n'
       '    "toolbox": ["Receive toolbox", "Toolbox/gear delivery for installer"],\n')]),
    ("⚠️ la logística vuelve a tapar la contrapartida (quitar el kit = recibirlo)", VO,
     [("            elif a in CONTRAPARTIDA:\n                prop.extend(CONTRAPARTIDA[a])\n"
       "            elif a in LOGISTICAS:\n                prop.append(a)\n",
       "            elif a in LOGISTICAS:\n                prop.append(a)\n"
       "            elif a in CONTRAPARTIDA:\n                prop.extend(CONTRAPARTIDA[a])\n")]),
    ("«got delayed» / «pushed back» vuelven a acreditarse", VO,
     [('    r"|delayed|pushed\\s+back|postponed)\\b", re.I)', '    r")\\b", re.I)')]),
    ("«Set tools up» deja de proponer Set Up", VO,
     [('    "set up tools": [("install", 1), ("ripout", 0)],\n', "")]),
    ("entra «started rip out» (casaría con «started ripping out»)", VO,
     [('    "setup for ripout": [("ripout", 0)],\n',
       '    "setup for ripout": [("ripout", 0)],\n    "started rip out": [("ripout", 1)],\n')]),
    ("Expenses sin obras vuelve a no ofrecer nada", "core/projects_ui.py",
     [('        if st.button(t(":material/add_circle: New project"), key="ge_vacio_nueva",\n',
       '        if False and st.button(t(":material/add_circle: New project"), key="ge_vacio_nueva",\n')]),
    ("⚠️ el libro de la foto deja de APUNTAR las escrituras (un `try` las escondería)",
     "../guardianes/libro_foto.py",
     [('        self.spreadsheet.intentos.append("%s.%s" % (self.title, n))\n', "")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", DU,
           [("def _nada_que_confirmar(p) -> None:\n", "def _nada_que_confirmar(p) -> None:   # (control)\n")])


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
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
