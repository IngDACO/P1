# -*- coding: utf-8 -*-
"""La pantalla de vincular Telegram dice POR QUE falla y da la salida que funciona."""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\auth_ui.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''        st.caption(t("1) The user opens the bot and presses **Start** (send them this link):"))
        st.code(f"https://t.me/{bot}?start={code}")
        st.caption(t("2) Once they have, press:"))
        if st.button(t(":material/link: Link this user's Telegram"), key=f"{key_prefix}_tgl"):
            cid = notify.telegram_find_chat_by_code(code)
            if cid:
                auth.set_contact(sel, telegram=cid)
                flash.exito(t(":material/check_circle: Telegram linked."))
                st.rerun()
            else:
                st.error(t("I could not find their message. Make sure they pressed Start and try again."))
'''

NUEVO = '''        st.caption(t("1) The user opens the bot and presses **Start** (send them this link):"))
        st.code(f"https://t.me/{bot}?start={code}")
        # ⚠️ Telegram SOLO manda el `/start <código>` cuando el chat es NUEVO. Si esa
        # persona ya había hablado con el bot, al abrir el enlace no hay botón Start
        # —hay caja de texto— y no se envía nada: por eso «ya di start» y no conecta.
        # El emparejado es por subcadena, así que mandar el código a secas sirve igual.
        st.caption(t("If they had already used the bot there is no **Start** button: "
                     "then they just send this text as a normal message in the chat:"))
        st.code(code)
        st.caption(t("2) Once they have, press:"))
        if st.button(t(":material/link: Link this user's Telegram"), key=f"{key_prefix}_tgl"):
            _d = notify.telegram_diagnostico(code)
            if _d.get("chat_id"):
                auth.set_contact(sel, telegram=_d["chat_id"])
                flash.exito(t(":material/check_circle: Telegram linked."))
                st.rerun()
            elif _d.get("motivo") == "webhook":
                # ⚠️ El caso que no daba NI TRAZA: con un webhook activo Telegram
                # responde 409 y `getUpdates` no puede leer nada, nunca.
                st.error(t("The bot has a **webhook** active, so the app cannot read its "
                           "messages: linking will never work until it is removed "
                           "(deleteWebhook). Meanwhile you can enter the chat_id by hand."))
            elif _d.get("motivo") == "sin_token":
                st.error(t("There is no bot configured (TELEGRAM_BOT_TOKEN)."))
            elif _d.get("motivo") == "sin_mensajes":
                st.error(t("Telegram has no pending message for the bot: nothing arrived. "
                           "Check they opened THIS bot and sent the text above."))
            elif _d.get("motivo") == "sin_codigo":
                st.error(t("{n} message(s) arrived, but none carries the code **{c}**. "
                           "The most common reason: they had already used the bot, so "
                           "pressing the link sends nothing — ask them to send the text "
                           "above as a normal message.", n=_d.get("n_updates", 0), c=code))
            else:
                st.error(t("Telegram could not be reached: {e}",
                           e=_d.get("detalle", "") or "?"))
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/auth_ui.py: motivo concreto + la salida que siempre funciona")
