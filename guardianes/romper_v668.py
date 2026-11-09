# -*- coding: utf-8 -*-
"""Batería de roturas de v668. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v668"
TOPE_S = 300
SC = "core/session_cookie.py"
AU = "core/auth_ui.py"
H = "core/home_ui.py"

ROTURAS = [
    ("⚠️ el componente vuelve a pedirse con default={} (no se sabe si contestó)", SC,
     [('_todas = m.cookie_manager(method="getAll", key="copex_cookie_get", default=None)',
       '_todas = m.cookie_manager(method="getAll", key="copex_cookie_get", default={})')]),
    ("respondio() dice siempre que sí", SC,
     [("st.session_state[_RESPONDIO] = _todas is not None", "st.session_state[_RESPONDIO] = True")]),
    ("⚠️ render_login vuelve a la clave del componente", AU,
     [("            _resp = _sc.respondio()\n", '            _resp = "copex_cookie_get" in st.session_state\n')]),
    ("vuelve «archivado»", H,
     [('t("archived") if _arch else ""] if x)   # v668', '"archivado" if _arch else ""] if x)   # v668')]),
    ("vuelve «nº»", H,
     [('t("No. {n}", n=_num) if _num else "",', 'f"nº {_num}" if _num else "",')]),
    ("vuelve «inactivo»", H,
     [('else t("inactive")] if x)', 'else "inactivo"] if x)')]),
    ("⚠️ el estado del activo vuelve en crudo", H,
     [('_mayus(_etq(str(a.get("Status", "")).strip()))] if x)   # v668', 'str(a.get("Status", "")).strip()] if x)   # v668')]),
    ("el estado de la cotización vuelve en crudo", H,
     [('_mayus(_etq(str(c.get("Status", "")).strip()))] if x),', 'str(c.get("Status", "")).strip()] if x),')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", SC,
           [('_RESPONDIO = "_ck_respondio"', '_RESPONDIO = "_ck_respondio"  # (control)')])


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
