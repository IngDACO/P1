# -*- coding: utf-8 -*-
"""Vincular Telegram fallaba SIN decir por que.

`telegram_find_chat_by_code` devolvia `None` para **cuatro causas distintas** y la
pantalla siempre decia lo mismo («no encontre su mensaje»), asi que no habia forma de
avanzar. Es el patron de v325/v340: un pendiente que nadie puede cerrar.

⚠️ Y una de las cuatro no daba ni traza: Telegram responde **409** cuando el bot tiene
un *webhook* activo, `requests` **no lanza** con un status de error y el codigo hace
`.json().get("result", [])` → lista vacia. Ni excepcion, ni log, ni pista.

⚠️ La causa MAS probable de «ya di start y no conecta» es otra, y ahora se explica en
pantalla: Telegram **solo manda el `/start <codigo>`** cuando el usuario abre el enlace
con el chat NUEVO. Si esa persona ya habia hablado con el bot antes, al abrir el enlace
no hay boton Start —hay caja de texto— y **no se envia ningun payload**. La salida que
siempre funciona es enviar el codigo como un mensaje normal, y el emparejado ya es por
subcadena, asi que casa igual.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\notify.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''def telegram_find_chat_by_code(code: str):
    """Busca en getUpdates un mensaje '/start <code>' y devuelve el chat_id (vinculación)."""
    try:
        r = requests.get(_tg("getUpdates"), params={"timeout": 0}, timeout=15)
        for u in reversed(r.json().get("result", [])):
            m = u.get("message") or {}
            if str(code) in str(m.get("text", "")):
                return str(m.get("chat", {}).get("id", ""))
    except Exception as e:
        logger.warning("telegram getUpdates: %s", e)
    return None
'''

NUEVO = '''def telegram_diagnostico(code: str) -> dict:
    """Busca el chat_id **y dice POR QUÉ** si no lo encuentra.

    Devuelve {chat_id, motivo, detalle, n_updates}. `motivo` es una de:
      · ''            → encontrado
      · 'sin_token'   → no hay bot configurado en los secrets
      · 'webhook'     → ⚠️ hay un webhook activo: `getUpdates` NO puede leer nada
      · 'sin_mensajes'→ Telegram no tiene ningún mensaje pendiente para el bot
      · 'sin_codigo'  → llegaron mensajes, pero ninguno trae el código
      · 'error'       → la llamada falló (red, token inválido…)

    ⚠️ Existe porque antes las CINCO situaciones devolvían `None` y la pantalla decía
    lo mismo para todas, así que no había forma de saber qué arreglar (v325/v340).
    """
    if not telegram_configured():
        return {"chat_id": None, "motivo": "sin_token", "detalle": "", "n_updates": 0}
    try:
        r = requests.get(_tg("getUpdates"), params={"timeout": 0}, timeout=15)
        j = r.json()
    except Exception as e:
        logger.warning("telegram getUpdates: %s", e)
        return {"chat_id": None, "motivo": "error", "detalle": str(e), "n_updates": 0}

    # ⚠️ `requests` NO lanza con un status de error, así que un 409 —el que devuelve
    # Telegram cuando hay un WEBHOOK activo— llegaba aquí como una respuesta normal
    # con `result` vacío: sin excepción, sin log y sin pista de qué pasaba.
    if not j.get("ok", False):
        _cod = j.get("error_code")
        _des = str(j.get("description", ""))
        _motivo = "webhook" if (_cod == 409 or "webhook" in _des.lower()) else "error"
        logger.warning("telegram getUpdates no ok (%s): %s", _cod, _des)
        return {"chat_id": None, "motivo": _motivo, "detalle": _des, "n_updates": 0}

    ups = j.get("result", []) or []
    for u in reversed(ups):
        m = u.get("message") or {}
        if str(code) in str(m.get("text", "")):
            return {"chat_id": str(m.get("chat", {}).get("id", "")), "motivo": "",
                    "detalle": "", "n_updates": len(ups)}
    return {"chat_id": None,
            "motivo": "sin_mensajes" if not ups else "sin_codigo",
            "detalle": "", "n_updates": len(ups)}


def telegram_find_chat_by_code(code: str):
    """El chat_id de quien mandó '/start <code>', o None.

    ⚠️ UNA sola definición de la búsqueda: delega en `telegram_diagnostico` en vez de
    repetir el recorrido (la lección de los cinco `_num` divergentes de v323).
    """
    return telegram_diagnostico(code).get("chat_id")
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/notify.py: telegram_diagnostico + find delega en el")
