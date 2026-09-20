# -*- coding: utf-8 -*-
"""v498 · el tipo de credencial se guardaba como la FUNCIÓN de traducción."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")


def rep(p, old, new):
    s = io.open(p, encoding="utf-8").read()
    assert s.count(old) == 1, (p, s.count(old), old[:70])
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))


# ── 1 · el fallo: se pasaba `t` (la función de i18n) donde va el TIPO ──
rep("core/auth_ui.py",
    "                ok, msg = C.add(usuario, grupo, t, num, clase, emi, ven, did, fname, nota, admin_usr)",
    "                # ⚠️ `_tp` es el tipo elegido. Aquí ponía `t`, que desde la migración de\n"
    "                # i18n es la FUNCIÓN de traducción: la credencial se guardaba con\n"
    "                # «<function t at 0x…>» como tipo (v498).\n"
    "                ok, msg = C.add(usuario, grupo, _tp, num, clase, emi, ven, did, fname,\n"
    "                                nota, admin_usr)")

# ── 2 · la guarda en el backend: un tipo que no es TEXTO no entra ──
rep("core/credentials.py",
    '''    if not str(tipo).strip():
        return False, t("The credential type is required.")''',
    '''    # ⚠️ v498: `str(tipo)` de una FUNCIÓN da «<function t at 0x…>», que pasa esta guarda
    # tan campante — y así se guardaron dos credenciales. El tipo tiene que ser TEXTO.
    if not isinstance(tipo, str) or not tipo.strip():
        return False, t("The credential type is required.")''')

# ── 3 · «falta»/«vencido» se veían en español en el aviso al asignar ──
rep("core/projects_ui.py",
    '''                    no_cumplen.append(f"**{u}**: " + ", ".join(
                        f"{t} ({'falta' if comp['por_tipo'][t] == 'falta' else 'vencido'})"
                        for t in faltan))''',
    '''                    # ⚠️ El valor es el DATO en español; se traduce al PINTAR (v442).
                    no_cumplen.append(f"**{u}**: " + ", ".join(
                        f"{_c} ({_etq(comp['por_tipo'][_c])})" for _c in faltan))''')
print("v498 parcheado")
