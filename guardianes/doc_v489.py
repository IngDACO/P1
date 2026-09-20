# -*- coding: utf-8 -*-
"""Documenta v489 en CLAUDE.md: la prueba de Xero en produccion y los dos arreglos de pantalla."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## Xero probado EN PRODUCCIÓN contra la Demo Company, y dos arreglos de pantalla (v489)

### La prueba de punta a punta (15/09/2026)
El usuario creó la app en `developer.xero.com`, puso los cuatro secretos y conectó. Antes de
que pulsara nada se comprobó, **sin iniciar sesión**, que Xero aceptaba la configuración:
el enlace de autorización mostraba «Log in to Xero **to continue to COPEX**» (con un client
ID o una redirect URI mal, Xero da error antes del login).
- ⚠️ **La primera conexión fue a la organización «COPEX»**, no a la Demo Company: es la que
  nació con la cuenta. Se detectó **leyendo la fila guardada** antes de mandar nada, y el
  usuario eligió reconectar a la Demo para no crear datos de prueba en una organización suya.
- Conexión guardada verificada en SOLO LECTURA (gspread con scope `readonly`, nunca los
  helpers de la app): pestaña en el MAESTRO, token en formato Fernet de 2.084 caracteres,
  **sin ningún JWT en claro**, `ShortCode` recibido.
- **Envío**: factura `0001` de 33,33 + 33,33 + 33,34 al 10 % → «1 invoice(s) sent to Xero»,
  `XeroInvoiceID` y `XeroSentAt` guardados, y la hoja `Invoices` migró sola a 21 columnas.
- ⚠️ **Sin duplicados, probado de verdad**: se borró la marca en COPEX y se reenvió → «already
  in Xero with the same number and were linked», con **el MISMO InvoiceID** que el primer
  envío. Es la protección que más importa y solo podía probarse contra un Xero real.
- **El lado de Xero lo verificó el usuario** (yo no inicio sesión): borrador, contacto,
  número, las tres líneas, cuenta 200, GST on Income, **GST 10,00 y total 110,00** — no el
  9,99 que daría recalcular línea a línea. Y **el enlace directo** (`go.xero.com/app/
  {ShortCode}/invoicing/view/{id}`) abrió la factura, que era lo único no verificable antes.
- Limpieza con doble guarda (ID **y** marca «ZZ PRUEBA»): `cliente1` vuelve a 0 facturas y 0
  clientes. `Auditoria` no se toca. El borrador de Xero lo borra el usuario (la Demo además
  se reinicia cada 28 días).
- ⚠️ **Queda SIN ejercitar en producción el refresco del token** (dura 30 min y la prueba
  entera cupo dentro): ocurrirá en el primer envío pasado ese tiempo. Está cubierto por el
  guardián con la red sustituida, pero no contra Xero.

### ⚠️ 1. «Desconectar no desconecta» — y el botón funcionaba
Era un desplegable **titulado «Disconnect Xero»** con una casilla y el botón dentro: el
título parece el botón y solo abre el desplegable. El usuario lo pulsó y no pasaba nada.
Antes de tocar código se comprobó en la hoja que **no se había escrito nada** (o sea, que no
era un fallo a medias) y se reprodujo hasta el botón: funcionaba. Ahora es un **botón de
verdad que pregunta** («Disconnect «X»?» con Yes, disconnect / Cancel). ⚠️ En el guardián,
`c1.button(...)` es un método del CONTENEDOR y no pasa por `st.button`: sin simular también
`st.columns`, el chequeo del «Yes, disconnect» habría pasado en vacío.

### ⚠️ 2. «Ya están todas en Xero» a quien no tenía NINGUNA
`_pendientes` devolvía solo la lista vacía, y un periodo sin facturas y uno con todas ya
mandadas daban lo mismo. Visto en producción con `cliente1` vacío. Ahora cuenta también
las enviables. ⚠️ La sonda del guardián dio primero un **rojo que no existía**: buscaba
«already in Xero» y esa frase también está en el aviso de desconectar — se compara la frase
ENTERA.

### ⚠️ El rojo de la suite era un FALSO POSITIVO del guardián de v365
Marcaba la pregunta «Disconnect X?» como un mensaje que muere en el `st.rerun()`. No muere:
se pinta en cada pasada mientras la pregunta está abierta, y el rerun cuelga de un BOTÓN
—justo la excepción que v367 le enseñó—. Pero `_test_es_widget` exigía que el receptor se
llamara `st`, y el botón es `c1.button(...)`, de una columna. Se amplió el RECEPTOR (nunca
la lista de widgets) y se validó en las dos direcciones: con un `st.success(msg)` metido
antes de ese mismo rerun **lo sigue cazando**, y el código real pasa.

### Verificación
`verif_v488` pasa a **105 comprobaciones**, con los chequeos nuevos validados contra el
comportamiento viejo (el texto engañoso vuelve a ponerlo rojo). Suite: **126 verde · 0 rojo**.
"""

FILA = ("| v489 | **Xero probado EN PRODUCCIÓN contra la Demo Company** + dos arreglos de pantalla. "
        "Envío real verificado (factura en borrador, GST 10,00 y total 110,00 — no 9,99 —, "
        "comprobado por el usuario en Xero, y el **enlace directo abre la factura**), y ⚠️ **sin "
        "duplicados probado de verdad**: borrada la marca en COPEX y reenviada, se ENLAZÓ con el "
        "mismo InvoiceID. ⚠️ La primera conexión fue a la organización «COPEX» del usuario, "
        "detectado leyendo la fila antes de mandar nada. **(1)** «Desconectar no desconecta»: el "
        "título del desplegable parecía el botón — ahora es un botón que pregunta. **(2)** «Ya "
        "están todas en Xero» a quien no tenía ninguna. Refresco del token aún sin ejercitar "
        "contra Xero (la prueba cupo en 30 min). 105 comprobaciones |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v488 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v489 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v489 + fila + cabecera")
