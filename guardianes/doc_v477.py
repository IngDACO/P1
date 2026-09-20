# -*- coding: utf-8 -*-
"""Documenta v477 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## Vincular Telegram fallaba SIN decir por que (v477)

Reportado por el usuario: *«no estoy pudiendo conectar el Telegram con un usuario de
campo; ya di start y aun no conecta»*.

### ⚠️ Un mensaje para CUATRO causas distintas
`telegram_find_chat_by_code` devolvia `None` y la pantalla decia siempre lo mismo —«no
encontre su mensaje»— tanto si no habia bot configurado, como si el bot tenia un
**webhook** activo, como si no habia llegado ningun mensaje, como si habian llegado
pero ninguno traia el codigo. Sin distinguirlas no habia forma de avanzar: es el
patron de v325/v340, un pendiente que nadie puede cerrar.

⚠️ Y una de las cuatro **no dejaba ni traza**: Telegram responde **409** cuando el bot
tiene un webhook activo, `requests` **no lanza** con un status de error y el codigo
hacia `.json().get("result", [])` → lista vacia. Ni excepcion, ni log, ni pista — y con
un webhook puesto, vincular no funcionaria NUNCA, se hiciera lo que se hiciera.

### ⚠️ La causa mas probable no es un fallo del codigo: es como funciona Telegram
**El payload `/start <codigo>` solo se envia cuando el chat con el bot es NUEVO.** Si
esa persona ya habia hablado con el bot alguna vez, al abrir el enlace no hay boton
Start —hay caja de texto— y **no se manda nada**. De ahi el «ya di start y no conecta»:
el mensaje nunca llego. La salida que SIEMPRE funciona es que escriba el codigo a secas
como un mensaje normal, y el emparejado ya era por subcadena, asi que casa igual. Ahora
la pantalla lo dice de entrada, sin esperar a que falle.

### Lo que se hizo
`notify.telegram_diagnostico(code)` distingue las **cinco** situaciones (`sin_token`,
`webhook`, `sin_mensajes`, `sin_codigo`, `error`) y devuelve tambien cuantos mensajes
llegaron; `telegram_find_chat_by_code` **delega** en ella en vez de repetir el recorrido
(v323). La pantalla explica cada caso y que hacer.
⚠️ Las cinco ramas se EJERCITARON interceptando `getUpdates`, no se leyeron: el 409 del
webhook, la lista vacia, el mensaje que no trae el codigo y el que si.
⚠️ Y se descarto la otra hipotesis mirando el codigo acusado: `auth.set_contact` deriva
las columnas de `LOGIN_HEADERS` (v433) y escribe en `Email`/`TelegramChatID`, que
existen — el camino de guardado esta sano, el fallo estaba en la busqueda.

⚠️ **No se pudo diagnosticar contra el bot real**: el `TELEGRAM_BOT_TOKEN` vive en los
secrets del CLOUD, no en los locales (v368). Por eso el arreglo es que **la app lo diga
en pantalla** en vez de adivinarlo desde aqui.

### ⚠️ Y la suite cazo un rojo que solo pudo salir por la migracion de roles de v475
`verif_v381` —el guardian de *lo que se enseña antes de un borrado irreversible*— decia
que al propietario le saldria `Fichajes: 0` donde el admin ve 1. **No era un fallo**, y
se comprobo antes de tocar nada: estaba anclado a `PRJ-0007`, que dejo de existir al
vaciarse la demo, y con un pid inexistente `datos_asociados` no puede resolver el grupo
y cae a la sesion (el propietario, sin grupo, al maestro vacio). Con un proyecto que SI
existe, los dos devuelven lo mismo.
Ese rojo **solo pudo aparecer porque v475 migro los roles**: antes el guardian simulaba
`"propietario"`, que desde v469 no resuelve, asi que ni siquiera entraba en el camino
del propietario — estaba verde sin comprobar nada.
⚠️ Y al reanclarlo se vio que la comprobacion vieja era **mas debil de lo que parecia**:
comparaba dos recuentos que hoy son **los dos CERO**, y comparar 0 con 0 no distingue
una lectura buena de una rota. El caso construido trae datos que contar y **exige que
los haya** antes de comparar.
"""

FILA = ("| v477 | **Vincular Telegram fallaba sin decir por qué** (lo reportó el "
        "usuario): un solo mensaje para CUATRO causas. ⚠️ Una de ellas **no dejaba ni "
        "traza** — con un *webhook* activo Telegram responde **409**, `requests` no lanza "
        "y el código se quedaba con la lista vacía, así que vincular no funcionaría NUNCA. "
        "⚠️ Y la causa más probable no es del código: **el `/start <código>` solo se envía "
        "si el chat es NUEVO**, así que quien ya había hablado con el bot no manda nada al "
        "abrir el enlace — la salida que siempre funciona (escribir el código como mensaje "
        "normal) ahora sale en pantalla de entrada. `telegram_diagnostico` distingue las "
        "cinco situaciones y `find` delega en ella (v323); las cinco ramas **ejercitadas** "
        "interceptando `getUpdates`. ⚠️ El token vive solo en los secrets del Cloud (v368), "
        "así que el arreglo es que **la app lo diga**, no adivinarlo. + la suite cazó un "
        "rojo que **solo pudo salir por la migración de roles de v475**: `verif_v381` "
        "anclado a un proyecto que ya no existe — y su comparación vieja eran **dos ceros** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v476 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v477 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: sección v477 + fila + cabecera")
