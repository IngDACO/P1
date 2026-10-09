# -*- coding: utf-8 -*-
"""Bateria de roturas de v556. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Time fixes en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v556"
CU = "core/correcciones_ui.py"
CO = "core/correcciones.py"
TC = "core/timeclock.py"
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
    ("⚠️ aprobar vuelve a ejecutarse DENTRO de la tarjeta (trampa 37)",
     CU, [('            _apuntar(_id, "aprobar", nota=_nota)\n',
           '            C.aprobar(_id, quien, _nota)\n            st.rerun()\n')]),
    ("la acción apuntada no se ejecuta antes de pintar",
     CU, [('    _accion_pendiente(grupo, quien, _etq_us)          # v556 · ANTES de pintar nada\n', '')]),
    ("⚠️ la corrección sustituida deja de detectarse",
     CO, [('                and str(o.get("OldValue", "")).strip() == str(r.get("NewValue", "")).strip()):\n',
           '                and False):\n')]),
    ("la sustituida vuelve a ofrecer Approve/Revert",
     CU, [('                _apuntar(_id, "sustituida", por=por)\n            return\n',
           '                _apuntar(_id, "sustituida", por=por)\n')]),
    ("⚠️ «Set the right time» vuelve a salir solo en los cierres olvidados",
     CU, [('        h1, h2 = st.columns(2, vertical_alignment="bottom")   # el botón, a la altura del campo\n',
           '        if str(r.get("OldValue", "")).strip():\n            return\n'
           '        h1, h2 = st.columns(2, vertical_alignment="bottom")\n')]),
    ("el aviso de solape vuelve a decir «your» al admin",
     TC, [('overlaps the {what} entry', 'overlaps your {what} entry')]),
    ("⚠️ fijar la hora deja de avisar a la persona",
     CU, [('            _avisar_persona(r, "ajustar", nota, _h.strftime("%H:%M"))\n', '            pass\n')]),
    ("⚠️ la tarjeta pierde el DÍA del fichaje",
     CU, [('                    + f" · **{_dia(r)}** · {_tipo_txt(r)}"\n',
           '                    + f" · {_tipo_txt(r)}"\n')]),
    ("«Asked on» vuelve al ISO",
     CU, [('x=_fdmh(r.get("Created"))', 'x=str(r.get("Created", ""))[:16]')]),
    ("lo más nuevo vuelve a salir primero",
     CU, [('                  key=lambda r: str(r.get("Created", "")))\n',
           '                  key=lambda r: str(r.get("Created", "")), reverse=True)\n')]),
    ("las tarjetas vuelven a ser pasivas",
     CU, [('            st.session_state["_cor_kpi"] = "" if _ver == k else k\n', '            pass\n')]),
    ("el tipo vuelve a salir crudo",
     CU, [('    return (t("workday") if str(r.get("Type", "")) == timeclock.TIPO_GENERAL\n'
           '            else t("project"))\n', '    return str(r.get("Type", ""))\n')]),
    ("el revisor vuelve a salir por su login",
     CU, [('                "Revisor": (_etq_us.get(str(r.get("ReviewedBy", "")))\n'
           '                            or str(r.get("ReviewedBy", ""))),\n',
           '                "Revisor": str(r.get("ReviewedBy", "")),\n')]),
    ("⚠️ la acción vuelve a buscar por ID GLOBAL (otra empresa)",
     CU, [('    r = _de_grupo(grupo, cid)\n', '    r = C.get(cid)\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           CU, [("        # ⚠️ Las DOS horas juntas: sin la anterior, el admin no puede juzgar nada.",
                 "        # ⚠️ Las DOS horas juntas: sin la anterior, el admin no puede juzgar nada. (control)")])


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
