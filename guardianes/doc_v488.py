# -*- coding: utf-8 -*-
"""Documenta v488 en CLAUDE.md (seccion + fila + cabecera) y el estado de hecho en NEGOCIO.md."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## FASE 2.3-A: conexión con Xero por API — conectar y mandar facturas (v488)

El usuario creó su cuenta de Xero y decidió tres cosas: **tokens cifrados en el libro
maestro**, **facturas primero**, y **los permisos de nómina desde la primera conexión**
(así el parte de horas de 2.3-B no obliga a volver a autorizar).

### Lo verificado en la documentación de Xero, no de memoria
| | |
|---|---|
| OAuth | autorizar en `login.xero.com/identity/connect/authorize`, canjear en `identity.xero.com/connect/token` (Basic auth), y `GET api.xero.com/Connections?authEventId=` para saber QUÉ organización se autorizó |
| ⚠️ Scopes | una app creada desde marzo de 2026 **solo** tiene los GRANULARES: facturas = `accounting.invoices`, **no** `accounting.transactions` — que la especificación OpenAPI de GitHub todavía lista. Se comprobó en su changelog antes de fijarlo |
| Tokens | acceso 30 min; refresco **rota en cada uso** y caduca a los 60 días sin usarse |
| Facturas | `PUT /Invoices` crea (no actualiza), acepta `Idempotency-Key`, `summarizeErrors=false` da un resultado por factura |
| Enlace | `go.xero.com/app/{ShortCode}/invoicing/view/{InvoiceID}` — el formato del servidor MCP **oficial** de Xero; necesita el `ShortCode` de `GET /Organisation` |

### Dónde viven los tokens: pestaña PROPIA en el maestro, no columnas de `Groups`
`XeroConnections` (global en `SHEETS_GLOBALES`), con el paquete del token cifrado con
**Fernet** (`XERO_TOKEN_KEY`). ⚠️ No en `Groups`, aunque era lo planeado: esa hoja se lee
en CADA pantalla y se cachea para todos (v339), y el token rota cada media hora de uso —
cada rotación invalidaría la caché de medio mundo— además de meter un token en una caché
compartida. Esta pestaña se lee **fresca y solo cuando se usa Xero**, y la caché de
pantalla (`_estados_cached`) **no lleva el token**.
⚠️ Un lector de PANTALLA no crea la pestaña (`_ws(crear=False)`): la crea la primera
conexión. Si la creara el estado de la pantalla, sería un «lector que escribe» (v145).

### Las cinco cosas que fallarían en silencio, y cómo se cierran
1. ⚠️ **El `state` va FIRMADO (HMAC)**, no guardado: la vuelta desde Xero llega en una
   pestaña NUEVA, o sea en otra sesión de Streamlit, así que `session_state` no sirve para
   comprobarlo. Lleva empresa + usuario + hora; una autorización de otro usuario o de otra
   empresa no se canjea, y **no llega a llamar a Xero**.
2. ⚠️ **El token de refresco ROTA**: dos sesiones refrescando a la vez perderían una
   rotación. Cerrojo por empresa + token vigente en memoria del proceso (sin él, cada
   llamada a la API releería la hoja). Probado con 4 hilos: **un solo refresco**. Y si
   falla GUARDAR el token ya rotado, se queda en memoria y se persiste en la siguiente
   llamada, en vez de perder la conexión.
3. ⚠️ **No duplicar en Xero**: antes de crear, `GET /Invoices?InvoiceNumbers=`. Si el
   número ya existe (venta viva; una BORRADA o una de PROVEEDOR no cuenta) se **enlaza**
   en vez de crear otra. Y si esa comprobación **falla, no se envía nada**: crear a ciegas
   es como aparecen dos facturas con el mismo número en la contabilidad del cliente.
4. ⚠️ **Lo que llega a Xero suma al centavo lo mismo que la factura emitida**: importes
   `Exclusive` y el impuesto de cada línea el REPARTIDO de v483 (`TaxAmount`), no el que
   Xero recalcularía línea a línea (3,33 · 3,33 · 3,34 = 10,00, no 9,99).
5. ⚠️ **Una definición de «factura repartida en líneas»**: `contable.documento_venta` la
   usan el CSV Y la API. Si cada uno repartiera el impuesto o eligiera el contacto a su
   manera, la misma factura llegaría con dos importes según por dónde entrara.
   El CSV se comprobó **idéntico byte a byte** contra la versión anterior en 32
   combinaciones (perfil × seguimiento × ABN × periodo × cuentas), con la prueba validada
   contra una rotura (32/32 detectadas).

### Lo que NO hace, a propósito
- **No crea la CATEGORÍA de seguimiento** en Xero: admite solo dos activas y ocupar una
  en la contabilidad del cliente no es cosa de COPEX. Crea las **opciones** que falten; si
  la categoría no existe, las líneas van sin seguimiento y se dice.
- **No manda una factura con un GST que no sea 10 %**: el código `OUTPUT` es «GST on
  Income» al 10 %, y un `TaxAmount` de otro porcentaje es contabilidad torcida.
- **No manda los cobros** (fase siguiente) ni el correo del contacto: Xero casa el
  contacto por NOMBRE, y enviar el email a un contacto existente podría sobrescribirlo.
- Borrador o aprobada lo decide la empresa (`AccountingJSON.xero_estado`), **borrador por
  defecto**: que el contable apruebe en Xero lo que llega.

### ⚠️ Un fallo real que cazó el propio guardián
El payload mandaba la categoría de seguimiento con el nombre de COPEX («Project») aunque
en la organización se llamara «project». Las opciones ya usaban el nombre exacto de Xero y
la categoría no. Ahora `_seguimiento` devuelve también el nombre real.

### Verificación
`verif_v488.py`, **99 comprobaciones**, todo **ejecutando** con la red sustituida (nunca
sale nada a Internet) y hojas falsas: el oráculo del CSV **escrito en el guardián** (huellas
de la versión anterior; sacarlo de `git show HEAD` dejaría el chequeo vacío tras el commit,
v484), state y cifrado, conectar, refresco/rotación/cerrojo, 401, envío completo con
enlace/errores/429, `marcar_xero` con **1 lectura y 1 escritura** y sin escribir en una hoja
vieja sin las columnas, desconectar **primero en Xero**, la caché sin token, las tres
pantallas y la vuelta, y que **ni el client secret, ni los tokens, ni la clave aparecen en
el log** (con la sonda comprobando que el log sí registra). Batería: **16/16 roturas +
CONTROL**, con el verde de base confirmado antes.

### Los dos rojos de la suite: CADUCADOS por la pestaña global nueva
`verif_v465` exigía respaldo en `LEGADO` a toda hoja, y `XeroConnections` **nació en
inglés** (el caso de `Library` en v472); `verif_v482` fija el conjunto EXACTO de globales
para cazar que alguien **saque** una. Actualizados con la razón escrita — ⚠️ el segundo
conserva la IGUALDAD y no pasa a «contiene», para que la próxima global también obligue a
decidirlo — y **validados en las dos direcciones** tras reanclarlos: quitar `library` de
las globales y dar a `xero.SHEET` un nombre viejo los siguen poniendo rojos. Suite:
**126 verde · 0 rojo**.

### Lo que falta para usarla (del usuario)
Crear la app en `developer.xero.com` (tipo Web app) con la redirect URI **exacta** que
enseña la pantalla, y poner en los Secrets del Cloud `XERO_CLIENT_ID`, `XERO_CLIENT_SECRET`,
`XERO_TOKEN_KEY` (generada en local con `Fernet.generate_key()`, nunca pegada en el chat) y
`XERO_REDIRECT_URI`. Conectar exige iniciar sesión en Xero, y eso lo hace el usuario.
"""

FILA = ("| v488 | **FASE 2.3-A: conexión con Xero por API** (decisiones del usuario: tokens "
        "cifrados en el maestro, facturas primero, permisos de nómina desde el principio). "
        "OAuth con `state` **firmado** (la vuelta llega en otra sesión, así que no se puede "
        "guardar), token Fernet en una pestaña **propia** del maestro —⚠️ no en `Groups`, que se "
        "cachea para todos y rotaría cada media hora—, refresco con **cerrojo** (4 hilos → 1 "
        "refresco) y token rotado que no se pierde si falla guardarlo. Envío por lotes: "
        "comprueba el número en Xero y **enlaza** en vez de duplicar, y si no puede comprobar "
        "**no envía**; importes sin impuesto con el impuesto REPARTIDO de v483. ⚠️ Una sola "
        "definición (`documento_venta`) para CSV y API, con el CSV **idéntico byte a byte** "
        "en 32 combinaciones. ⚠️ Scopes GRANULARES verificados (la especificación OpenAPI "
        "aún lista los viejos). ⚠️ El guardián cazó un fallo real: la categoría de "
        "seguimiento iba con el nombre de COPEX y no el de Xero. 99 comprobaciones · "
        "**16/16 roturas + control** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v487 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v488 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v488 + fila + cabecera")

N = "C:/Users/diego/P1/NEGOCIO.md"
n = io.open(N, encoding="utf-8").read()
VIEJO = ("| **Contabilidad** | ⚠️ **Parcial desde v483 (08/09/2026)**: hay **exportación a CSV** para "
         "Xero y MYOB (facturas y gastos, con el proyecto como categoría de seguimiento), así que la "
         "factura ya no se teclea dos veces. Lo que NO hay es **integración por API**: el fichero se "
         "importa a mano, y que los dos lo acepten no está probado contra una cuenta demo real |")
NUEVO = ("| **Contabilidad** | ⚠️ **Parcial desde v483 (08/09/2026)**: hay **exportación a CSV** para "
         "Xero y MYOB (facturas y gastos, con el proyecto como categoría de seguimiento). **Desde v488 "
         "(15/09/2026) las facturas van a Xero por API** (conectar la organización y enviarlas, sin "
         "duplicar). Falta: activarla (app de Xero + secrets), probarla contra la Demo Company, y "
         "llevar por API los cobros, los gastos y el parte de horas; MYOB sigue solo por CSV |")
if n.count(VIEJO) == 1:
    n = n.replace(VIEJO, NUEVO)
    io.open(N, "w", encoding="utf-8", newline="").write(n)
    print("NEGOCIO.md: estado de hecho de contabilidad")
else:
    print("NEGOCIO.md: ancla no encontrada (%d) — sin tocar" % n.count(VIEJO))
