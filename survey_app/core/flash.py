"""Mensajes que SOBREVIVEN a un `st.rerun()`.

⚠️ El problema que resuelve (v365): `st.rerun()` **descarta los deltas del run en
curso**, así que un `st.success(...)` emitido justo antes nunca llega a la pantalla. El
patrón `mensaje → rerun` estaba en **19 sitios** del repo, y en todos la app hacía la
acción y no la confirmaba:

  · el fichaje  → «✅ Clock OUT … Horas trabajadas: 8.0»
  · nóminas     → el aviso de v346 sobre quien no tiene tarifa (¡la razón de ser de
                  esa versión!) y el bloqueo de solape de v364
  · usuarios, clientes, catálogo, cotizaciones, proyectos, planificación, survey

Es el mismo principio que v222 documentó con `components.html`: lo que se emite justo
antes de un rerun se tira. Se descubrió porque, verificando v364 en el navegador, el
mensaje no aparecía **y no era culpa del clic**.

## Cómo se usa
    from core import flash
    flash.exito("Documento subido.")
    st.rerun()                       # el mensaje sobrevive y lo pinta la shell

`mostrar()` se llama UNA vez, en la shell (`home_ui.render_admin_content`) y en el
login, así que sirve a cualquier pantalla sin que cada una tenga que acordarse.

⚠️ **Módulo HOJA**: solo importa streamlit. Nada de `core.*` → no puede haber ciclos,
y cualquier módulo puede usarlo (es lo mismo que se hizo con `num.py` y `tenant.py`).
⚠️ `st.toast` NO necesita esto: es una notificación flotante del navegador y sobrevive
al rerun por su cuenta.
"""
import streamlit as st

_CLAVE = "_flash_cola"
_TIPOS = ("success", "warning", "error", "info")


def poner(tipo: str, texto: str) -> None:
    """Encola un mensaje para pintarlo DESPUÉS del rerun."""
    if not texto:
        return
    if tipo not in _TIPOS:
        tipo = "info"
    # ⚠️ Se acumulan en LISTA: una acción puede dejar varios (crear nóminas deja el
    # «N creadas» + el aviso de sin-tarifa + el de solape). Con una sola ranura, los
    # dos últimos se perderían igual que antes.
    st.session_state.setdefault(_CLAVE, []).append((tipo, str(texto)))


def exito(texto: str) -> None:
    poner("success", texto)


def aviso(texto: str) -> None:
    poner("warning", texto)


def error(texto: str) -> None:
    poner("error", texto)


def info(texto: str) -> None:
    poner("info", texto)


def mostrar() -> int:
    """Pinta y VACÍA la cola. Devuelve cuántos mensajes se pintaron.

    ⚠️ Se vacía siempre, aunque falle el pintado: una cola que no se limpia dejaría el
    mensaje pegado en todas las pantallas siguientes.
    """
    cola = st.session_state.pop(_CLAVE, None) or []
    for tipo, texto in cola:
        getattr(st, tipo, st.info)(texto)
    return len(cola)
