# -*- coding: utf-8 -*-
"""Bateria de roturas de v557. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Users en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v557"
AU = "core/auth.py"
AUI = "core/auth_ui.py"
TOPE_S = 420


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ «driver 1» vuelve a pasar por correo", AU,
     [("    if not _EMAIL_RE.match(e):\n", "    if False:\n")]),
    ("las erratas («hotmai.com») dejan de detectarse", AU,
     [("cutoff=0.78)", "cutoff=0.99)")]),
    ("⚠️ set_contact vuelve a guardar lo que no es un correo", AU,
     [('    if email is not None and str(email).strip() and not revisar_email(email)["ok"]:\n'
       '        return False, revisar_email(email)["motivo"]\n', '')]),
    ("⚠️ add_user vuelve a aceptar contraseñas cortas", AU,
     [('    if len(str(pw)) < MIN_PW:                 # v557 · tras rol y grupo\n'
       '        return False, t("The password must have at least {n} characters.", n=MIN_PW)\n', '')]),
    ("set_password vuelve a aceptar contraseñas cortas", AU,
     [('    if len(str(pw)) < MIN_PW:                 # v557\n'
       '        return False, t("The password must have at least {n} characters.", n=MIN_PW)\n', '')]),
    ("⚠️ el alta vuelve a borrar lo escrito al dar error", AUI,
     [('with st.form(f"form_campo_{_g}", clear_on_submit=False):',
       'with st.form(f"form_campo_{_g}", clear_on_submit=True):')]),
    ("el alta deja de preguntar por la errata", AUI,
     [('    if _rv["sugerencia"] and not confirmado:\n', '    if False:\n')]),
    ("⚠️ cambiar la contraseña deja de pedir repetirla", AUI,
     [('                elif np_ != np2:\n', '                elif False:\n')]),
    ("la contraseña nueva se queda escrita al guardar", AUI,
     [('                        st.session_state[f"{k}_pwgen"] = _pg + 1\n', '                        pass\n')]),
    ("la ficha guarda la errata sin confirmar", AUI,
     [('        if _rv["sugerencia"] and not _forzar:\n', '        if False:\n')]),
    ("la tabla deja de señalar el correo inválido", AUI,
     [('        if _ce == "invalido":\n            return t("invalid email")\n', '')]),
    ("⚠️ el filtro de salud deja de filtrar", AUI,
     [('    vista = _f[_filtro][2] if _filtro else gente\n', '    vista = gente\n')]),
    ("⚠️ una sola tabla para todos los filtros (la selección se cruza)", AUI,
     [("key=f\"gu_tbl_{_filtro or 'todos'}\"", 'key="gu_tbl"')]),
    ("la tarifa vuelve a salir sin «$»", AUI,
     [('        return f"${x:,.0f}" if x.is_integer() else f"${x:,.2f}"\n',
       '        return str(v)\n')]),
    ("el selector de la ficha vuelve a las bolitas", AUI,
     [('key=f"cpxseg_{k}_sec"', 'key=f"{k}_sec"')]),
    ("la fecha de alta vuelve al ISO", AUI,
     [('key=f"{k}_fing", format="DD/MM/YYYY"', 'key=f"{k}_fing", format="YYYY-MM-DD"')]),
    ("la ficha deja de avisar del correo inválido", AUI,
     [('t("Invalid email") if _ce == "invalido" else', '"" if _ce == "invalido" else')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           AUI, [("    # v557 · el correo que NO es un correo (o parece una errata) se dice aquí también",
                  "    # v557 · el correo que NO es un correo (o parece una errata) se dice aquí también (control)")])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


print("0. Verde de base")
_base = corre()
if not _base:
    print("   ⚠️ el guardian YA esta %s: la tanda saldria «cazada» sin probar nada"
          % ("COLGADO" if _base is None else "rojo"))
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
saltadas, colgadas = [], []
for desc, rel, cambios in ROTURAS:
    _ok, bak, p, det = aplica(rel, cambios)
    if _ok is None:
        print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
    if verde is None:
        colgadas.append(desc)
        print("  COLGADA  %s" % desc)
        continue
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

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
