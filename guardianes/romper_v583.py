# -*- coding: utf-8 -*-
"""Bateria de roturas de v583 (lo visto verificando v582: el alta delante de la cotización y
su borrador). ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455). Anclas en
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
G = "verif_v583"
CU = "core/catalogo_ui.py"
QU = "core/quotes_ui.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ el botón de «Used in» ya no cierra el alta (sale delante de la cotización)", CU,
     [('            st.session_state.pop("_cot_nueva", None)\n            st.session_state["_cot_open"]',
       '            st.session_state["_cot_open"]')]),
    ("⚠️ el borrador ya no devuelve el nombre ni la nota", QU,
     [("        if _k in _borr and _k not in st.session_state:\n            st.session_state[_k] = _borr[_k]\n",
       "        pass\n")]),
    ("…ni el cliente elegido", QU,
     [('        st.session_state["cot_new_cli"] = _borr["cot_new_cli"]\n', "        pass\n")]),
    ("⚠️ el borrador deja de guardarse", QU,
     [('    st.session_state["_cot_borrador"] = {\n', '    st.session_state["_cot_borrador_roto"] = {\n')]),
    ("«Cancel» deja el borrador", QU,
     [('"cot_new_cli_tel", "cot_new_cli_mail", "_cot_borrador")\n',
       '"cot_new_cli_tel", "cot_new_cli_mail")\n')]),
    # v583 · RETIRADA, con su razón: se ESCAPABA, y tenía razón. Tras «Cancel» el alta ya no
    # se pinta y Streamlit borra la nota solo; la línea que la tiraba a mano no protegía
    # nada (la había pedido un andamio de la prueba que repintaba el alta) y se quitó.
    ("el impuesto entra en el borrador (aviso de Streamlit)", QU,
     [('_BORRADOR = ("cot_new_cli_nom",', '_BORRADOR = ("cot_new_imp", "cot_new_cli_nom",')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", QU,
           [("def _limpiar_nueva():\n", "def _limpiar_nueva():   # (control)\n")])


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
