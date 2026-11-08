# -*- coding: utf-8 -*-
"""Texto de la hoja dentro de un PDF de reportlab (v653).

Un `Paragraph` de reportlab lee su texto como MARCADO (`<b>`, `<font>`, `<img>`…). Un nombre,
una nota o una dirección que traiga «<b>» sin cerrar hacía fallar el PDF entero (medido: la
factura no se generaba), y un «<img src=…>» le hacía intentar abrir un fichero o una URL.
Todo lo que escribe una PERSONA (o llega de la hoja) entra por `esc_pdf`; el marcado que pone
el código (`<b>{d('Note:')}</b>`) se queda como está.

Módulo HOJA: solo la biblioteca estándar.
"""
from xml.sax.saxutils import escape


def esc_pdf(v) -> str:
    """`v` como TEXTO para un `Paragraph`: «<», «>» y «&» escapados (se ven tal cual)."""
    return escape("" if v is None else str(v))
