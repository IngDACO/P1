# -*- coding: utf-8 -*-
"""Bateria de roturas de v588 (Tools → Home). ⚠️ Verde de BASE primero (v459) y NO en paralelo
con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba que cada
ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v588"
HU = "core/home_ui.py"
TH = "core/theme.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ vuelve el «Open →» pequeño: la tarjeta deja de ser el botón", HU,
     [('key=f"cpxtool_{_CLAVE_HERR.get(_id, _id)}"', 'key=f"hubherr_{_CLAVE_HERR.get(_id, _id)}"')]),
    ("⚠️ las tarjetas pierden el reparto por ancho", HU,
     [('    st.markdown(T.por_fila("cpx_herr_hub", 3), unsafe_allow_html=True)\n', "")]),
    ("la tarjeta deja de decir su último uso", HU,
     [("                                         _uso.get(_id) or t(\"Not used yet\"))\n",
       "                                         t(\"Not used yet\"))\n")]),
    ("el último uso sale con la fecha ISO", HU,
     [('d=dmy(str(r.get("Date", ""))[:10])', 'd=str(r.get("Date", ""))[:10]')]),
    ("el último uso deja de nombrar la obra", HU,
     [('p=_p)', 'p="")')]),
    ("el último uso coge el de OTRO grupo", "core/toolruns.py",
     [('        if str(r.get("Group", "")).strip().lower() == g:\n            out[str(r.get("Tool", ""))] = r\n',
       '        out[str(r.get("Tool", ""))] = r\n')]),
    ("el último uso coge el MÁS VIEJO", "core/toolruns.py",
     [('    for r in sorted(_records(), key=lambda r: str(r.get("Date", ""))):\n',
       '    for r in sorted(_records(), key=lambda r: str(r.get("Date", "")), reverse=True):\n')]),
    ("los Pre-Start de hoy cuentan los de cualquier día", "core/prestart.py",
     [('            and str(r.get("Date", ""))[:10] == hoy]\n', "]\n")]),
    ("⚠️ un fallo del registro tumba la portada", HU,
     [('        logger.warning("home_ui: último uso de las herramientas: %s", e)\n',
       '        raise\n')]),
    ("⚠️ el Pre-Start vuelve a ser el «si no» de Tools", HU,
     [('    elif sub == "🦺 Pre-Start":\n        from core.prestart_ui import render_prestart_tab\n        render_prestart_tab()\n    else:\n',
       '    else:\n')]),
    ("⚠️ la fila deja de igualar alturas", TH,
     [('.st-key-cpx_herr_hub [data-testid="stColumn"] [data-testid="stButton"] {{ height: 100%; }}\n', "")]),
    ("el título de la tarjeta vuelve a partirse", TH,
     [("  margin: 0 0 4px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;\n",
       "  margin: 0 0 4px !important;\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", HU,
           [("def _ultimos_usos(grupo, ids) -> dict:\n", "def _ultimos_usos(grupo, ids) -> dict:   # (control)\n")])


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
