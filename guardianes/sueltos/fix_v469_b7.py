# -*- coding: utf-8 -*-
"""El bloque 7 medía «la hoja en español llega en inglés». Migrada la hoja, esa
afirmación pasó a ser la IDENTIDAD y el verde dejó de probar la canonización — un
chequeo que dice una cosa y mide otra (trampa nº1). Se parte en las dos direcciones.
"""
import io
import os

p = os.environ["SCRW"] + "/verif_v469.py"
s = io.open(p, encoding="utf-8").read()

VIEJO = '''print("7. Contra la hoja REAL: el rol llega en ingles con la hoja en español")
try:
    u = auth.get_user("dacox")
    if not u:
        print("   ⚠️ no hay usuario 'dacox': el chequeo no puede afirmar nada")
        sys.exit(2)
    if u.get("Role") in ("owner", "administrator", "field"):
        ok("get_user('dacox').Role = %r" % u.get("Role"))
    else:
        fallo("el rol llega %r: la canonizacion no aplica" % u.get("Role"))'''

NUEVO = '''print("7. Contra la hoja REAL: el rol llega canonico, venga como venga")
# ⚠️ Este bloque decia «con la hoja en español» y media eso. Al MIGRAR la hoja (v469,
# 5 celdas de Login.Role) la afirmacion se convirtio en la IDENTIDAD, asi que su verde
# dejo de probar la canonizacion sin que nada lo dijera — un chequeo que afirma una
# cosa y mide otra es la trampa nº1. Ahora se comprueban las DOS direcciones, y la de
# la fila sin migrar con un caso CONSTRUIDO, porque en la hoja ya no queda ninguna.
try:
    u = auth.get_user("dacox")
    if not u:
        print("   ⚠️ no hay usuario 'dacox': el chequeo no puede afirmar nada")
        sys.exit(2)
    if u.get("Role") in ("owner", "administrator", "field"):
        ok("hoja MIGRADA: get_user('dacox').Role = %r (identidad)" % u.get("Role"))
    else:
        fallo("el rol llega %r: no es canonico" % u.get("Role"))
    # y la fila SIN migrar, que es lo que la capa de compatibilidad existe para cubrir
    _vieja = valores.canonizar([{"Role": "propietario"}, {"Role": "campo"}], "Login")
    if [r["Role"] for r in _vieja] == ["owner", "field"]:
        ok("hoja SIN migrar: 'propietario'/'campo' -> 'owner'/'field' (canonizacion)")
    else:
        fallo("una fila vieja de Login no canoniza: %r" % _vieja)'''

assert s.count(VIEJO) == 1, "ancla ausente o ambigua (%d)" % s.count(VIEJO)
io.open(p, "w", encoding="utf-8", newline="").write(s.replace(VIEJO, NUEVO))
print("bloque 7 partido en las dos direcciones")
