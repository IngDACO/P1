# -*- coding: utf-8 -*-
"""Documenta v506 — el expediente de entrega."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL EXPEDIENTE DE ENTREGA: qué tiene la obra y qué le falta (v506)

Primera de las tres oportunidades que el estudio de mercado del 20/09/2026 marcó como
imposibles de copiar. La app reúne lo que la empresa tiene que conservar **cinco años** y
dice, con nombre, **qué falta para poder entregar**.

### ⚠️ Lo que NO es, y está escrito en el código y en la pantalla
**No certifica nada.** No sustituye al certificado del certificador, al eléctrico ni al
*Safe-to-Operate*: esos los emite un tercero y la app no puede fabricarlos. Prometer
cumplimiento en la interfaz metería al cliente en un problema, así que hay un guardián
que lo vigila (ver «Verificación»).

### La lista es REAL, no inventada
Los trece ítems (a–m) salen del estándar técnico de lifts del **Departamento de Educación
de NSW** —un cliente de verdad del mercado de arranque— sección «Lift Documentation and
Support», lo que el instalador entrega en *practical completion*. Un expediente con una
lista inventada no sirve para lo único que tiene que servir.

De los trece, la app **evidencia cinco** con datos que ya guardaba:

| Ítem | De dónde sale |
|---|---|
| (a) Project specification check sheets | La solución de posicionamiento y los cortes del survey |
| (c) Commissioning records | Fechas reales de inicio y fin por actividad |
| (f) As-built dimensional | Matriz del survey, posicionamiento y verificación de plomada |
| (j) Hazard and risk assessment | Los pre-starts firmados de la obra |
| (l) Installer's statutory certificates | Credenciales de quien trabajó, **vigentes el día que trabajó** |

Los otros ocho son de terceros. ⚠️ **Nunca pasan por cálculo**: solo si alguien adjunta el
documento. Con la obra perfecta, los ocho siguen faltando — decir lo contrario sería que
la app afirmara algo que no sabe.

### Lo que lo hace imposible de copiar no es juntar PDFs
Es **cruzar** el registro técnico con el de personas y el de fechas, que solo puede hacer
quien hace el cálculo. En la primera ejecución contra la hoja real, sin que nadie lo
provocara, salió esto:

> *Hours were booked to this job by people not assigned to it: admin1*

Y el cruce que motivó la función: *«Ana firmó el pre-start del 15/08, pero su ticket venció
el 12/08»*. Un competidor puede juntar los mismos archivos; no puede sacar esa frase.

Los cuatro cruces: certificado vencido el día que firmó · obra cerrada sin verificación de
plomada · fichó gente no asignada · actividad cerrada antes de empezar.

### Dónde vive
`core/handover.py` es **módulo HOJA**: no importa nada de `core`, no toca Sheets, recibe
un contexto y devuelve el estado — así se puede ejercitar de verdad. `core/handover_ui.py`
reúne los hechos y pinta, **cada fuente en su propio `try`**: el expediente es justo la
pantalla que se abre cuando algo va mal, así que una hoja caída le resta un dato, no la
tumba. Columna `HandoverItem` al final de `Documentos` (v363), opcional.

Decisión del usuario: **índice y huecos primero, el expediente completo embebido después**,
y **avisa sin bloquear** — en obra real siempre falta algo de un tercero, y un botón que
nadie puede pulsar no sirve.

### ⚠️ Y un fallo que no era de esta versión: 14 guardianes en rojo
La suite dio **14 rojos** que parecían una regresión grande y no lo eran. Al traer la suite
al repo esa misma mañana, los ficheros se clasificaron **por su nombre** (`verif_`,
`check_`…) y ocho módulos auxiliares —`i18n_tool`, los `barre_*`, `fixture_survey`,
`riesgo_claves`— no encajaban en ningún patrón y se fueron a `sueltos/`. No eran scripts de
un solo uso: son **librerías que la suite importa**, hasta seis guardianes cada una.
`ModuleNotFoundError`, catorce veces.

**Un guardián que no puede ni importarse no dice nada de lo que vigila, y se disfraza de
código roto.** Red nueva `check_suite_integra.py`: ningún guardián puede importar algo que
no esté. Mira solo lo resoluble estáticamente —importar ejecuta— y se valida contra un
caso conocido-malo.

⚠️ La lección de método: al mover la suite se dijo «verificado que funciona desde su
ubicación nueva» habiendo corrido **tres guardianes y el enumerador**. La suite entera
desde ahí no se corrió hasta el despliegue siguiente. Un subconjunto no vale (v385), y eso
incluye el subconjunto que uno usa para comprobar una mudanza.

### Verificación
`verif_v506.py`, **36 comprobaciones**, ejecutando la lógica de verdad. Batería:
**12 roturas, 12 cazadas + CONTROL** ⚠️ (dos escaparon primero: el guardián **volvió a
morir en vez de denunciar** —cuarta vez en el día— y una rotura no rompía nada porque la
guarda del invitado **funcionaba por accidente**: nadie tiene credenciales bajo la clave
vacía, y una sola fila con el usuario en blanco habría acusado a todo el mundo; ahora la
guarda es explícita). Suite completa: **138 verde · 0 rojo · 0 roto**.

⚠️ Uno de los chequeos falló por su propia construcción: buscar «compliance certificate»
en la pantalla caza el **descargo honesto** («this is **not** a compliance certificate»).
Ahora la red exige que la frase esté AFIRMADA, y se valida en las dos direcciones.

**Ejercitado contra la HOJA REAL** (método v344): la columna se creó sola (**6 → 7**, al
final), el recolector leyó la obra real sin lanzar, el ítem de tercero pasó a OK **solo**
al adjuntar el documento, ningún otro se contagió, y la hoja quedó como estaba.
"""

FILA = ("| v506 | **El expediente de entrega: qué tiene la obra y qué le falta.** Primera de las "
        "tres oportunidades del estudio de mercado. Trece ítems sacados del estándar REAL de lifts "
        "del Depto. de Educación de NSW (a–m, *practical completion*), no inventados: la app "
        "**evidencia cinco** con lo que ya guardaba y los ocho de terceros ⚠️ **nunca pasan por "
        "cálculo** —solo si alguien adjunta el documento—. ⚠️ **No certifica nada** y lo dice en el "
        "código y en pantalla; hay un guardián que vigila que la interfaz no prometa cumplimiento. "
        "Lo imposible de copiar no es juntar PDFs sino **cruzar** el registro técnico con el de "
        "personas y fechas: en su primera ejecución contra la hoja real salió solo «*hours were "
        "booked to this job by people not assigned to it*». ⚠️ Y la suite dio **14 rojos que no eran "
        "de esta versión**: al traer la suite al repo, ocho módulos auxiliares se clasificaron por "
        "su nombre y acabaron en `sueltos/` — un guardián que no puede importarse se disfraza de "
        "código roto. Red nueva `check_suite_integra`. 36 comprobaciones · **12/12 roturas + "
        "control** · suite 138 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v505 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v505 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v506 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v506 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v506 = actual)")
c = c.replace(CAB, CAB + FILA)

lineas = c.splitlines(True)
idx = [i for i, l in enumerate(lineas) if l.startswith("| v")]
if len(idx) != 16:
    raise SystemExit("esperaba 16 filas tras insertar: %d" % len(idx))
vieja = lineas[idx[-1]][:10]
del lineas[idx[-1]]
c = "".join(lineas)

m = re.search(r"_\(y (\d+) versiones anteriores", c)
if not m:
    raise SystemExit("no encuentro la nota de cierre")
c = c.replace(m.group(0), "_(y %d versiones anteriores" % (int(m.group(1)) + 1))
escribir(CLAUDE, c)
print("CLAUDE.md: fila v506 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
