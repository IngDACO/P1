# -*- coding: utf-8 -*-
"""Manda el resumen del día a quien lo pidió (v648). Lo lanza `.github/workflows/resumen_manana.yml` cada hora; cada
empresa recibe el suyo cuando en su hora local son entre las 7 y las 11 (`core/resumen_envio.py`).

    python resumen_manana.py                 # lo que toque a esta hora
    python resumen_manana.py --ignorar-hora  # ya, sin esperar a la mañana (sigue siendo una vez al día por persona)

⚠️ El repositorio es PÚBLICO y lo que sale de aquí queda en el registro de Actions: SOLO cuentas. Los avisos de la
app (llevan usuarios y mensajes de error) se apagan, y un fallo se dice por su tipo, nunca por su mensaje.
"""
import logging
import os
import sys

_RAIZ = os.path.dirname(os.path.abspath(__file__))
os.chdir(_RAIZ)                         # ⚠️ `.streamlit/secrets.toml` se busca relativo al CWD (trampa 19)
sys.path.insert(0, _RAIZ)
logging.disable(logging.CRITICAL)


def main(argv) -> int:
    try:
        from core import resumen_envio as RE
        c = RE.enviar_todo(ignorar_hora="--ignorar-hora" in argv)
    except Exception as e:
        print("No se pudo enviar: %s" % type(e).__name__)
        return 1
    print(" | ".join("%s %d" % (k, c.get(k, 0)) for k in RE.CUENTAS))
    return 1 if (c.get("fallos") or c.get("errores")) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
