# -*- coding: utf-8 -*-
"""El campo ve que le vence una credencial y no sabe si alguien mas lo sabe.

⚠️ La primera lectura fue MIA y era incompleta: di por hecho que era un callejon sin
salida. Medido en el codigo, `credentials.notify_expiring` YA avisa por email/Telegram
**al admin y al propio dueño**, en cada login de administrador y sin repetir dentro de
~25 dias (v104/v187). El aviso sale solo.

Lo que falta es de INFORMACION, no de mecanismo: en su pantalla no hay ni una palabra
de eso, asi que quien ve «vence en 8 dias» no sabe si tiene que perseguirlo. Una linea
lo cierra; construir un canal nuevo sobre una premisa equivocada habria sido peor.

⚠️ Tres cosas de este parche estaban MAL y se cazaron mirando las firmas antes de
aplicarlo (regla v135): `list_for` toma UN argumento (no dos), la columna es
`ExpiryDate` (no `Expiry`/`Vencimiento`) y **`auth_ui` no tiene `logger` de modulo** —
usarlo habria sido el NameError latente de v370/v423, en una pantalla del campo.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\auth_ui.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''    st.caption(t("Your tickets and credentials as recorded by your administrator. Show them on site if you are asked for them."))
    render_credenciales(a.get("usuario", ""), a.get("grupo", ""), editable=False, key_prefix="mycr")
'''

NUEVO = '''    st.caption(t("Your tickets and credentials as recorded by your administrator. Show them on site if you are asked for them."))
    # ⚠️ v478 · Quien ve «vence en 8 días» no puede hacer NADA desde aquí —las carga el
    # administrador— y la pantalla no decía si alguien más lo sabía. Sí lo sabe:
    # `notify_expiring` avisa al admin Y al propio dueño (v104/v187). Decirlo evita que
    # esa persona tenga que ir a preguntar. Solo si hay algo que vence: con todo en
    # regla sería ruido en la pantalla de quien trabaja desde el móvil.
    try:
        from core import credentials as _C
        _pdte = [c for c in _C.list_for(a.get("usuario", ""))
                 if _C.status(c.get("ExpiryDate", "")) in ("por_vencer", "vencido")]
        if _pdte:
            st.info(t("{n} of them need renewing. Your administrator is warned "
                      "automatically (and so are you), so you do not have to chase it: "
                      "bring the new one and they will update it here.", n=len(_pdte)))
    except Exception:
        pass          # es DISPLAY opcional: si no se puede mirar, la pantalla sigue
    render_credenciales(a.get("usuario", ""), a.get("grupo", ""), editable=False, key_prefix="mycr")
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/auth_ui.py: aviso solo si hay algo que vence, con las firmas correctas")
