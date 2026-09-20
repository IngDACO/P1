# -*- coding: utf-8 -*-
"""Documenta v498 en CLAUDE.md: el tipo de credencial se guardaba como la función t."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## ⚠️ EL TIPO DE CREDENCIAL SE GUARDABA COMO LA FUNCIÓN DE TRADUCCIÓN (v498)

Lo reportó el usuario: «en los tipos de credenciales sale un texto que no corresponde».
En la hoja, las dos credenciales cargadas tenían como tipo **`<function t at 0x…>`**.

```python
ok, msg = C.add(usuario, grupo, t, num, clase, ...)   # ← `t` es la FUNCIÓN de i18n
_tp = tipo_otro.strip() if (_es_otro and tipo_otro.strip()) else tipo   # ← esto es el tipo
```

### Por qué vivió tanto, y por qué mis pruebas no lo vieron
- `git log -S` lo data en **v104**, cuando la variable del tipo se llamaba `t` y la llamada
  era correcta. **v189** la renombró a `tipo` (y añadió `_tp`), y la llamada se quedó con
  `t`; entonces `t` no existía en `auth_ui`, así que habría sido `NameError`. Cuando
  **v445** metió `from core.i18n import t`, ese nombre volvió a resolver — pero a la
  FUNCIÓN. Desde ahí, guardar una credencial escribe la función como tipo, en silencio.
- ⚠️ **En v350 ejercité `credentials.add` y pasó**, porque el fallo no está en la función
  sino en **lo que la pantalla le pasa**. Es la lección de v452 con un caso caro: el
  inventario de «75 de 75 escrituras ejercitadas» medía las FUNCIONES; el formulario es
  otra cosa. Por eso el guardián de v498 **ejecuta el formulario** y mira qué recibe `add`.
- Y `str(tipo)` de una función **no está vacío**, así que la guarda del backend
  («el tipo es obligatorio») la dejaba pasar tan campante.

### Lo arreglado
1. El formulario manda `_tp` — el tipo elegido, o lo escrito en «Specify the type».
2. `credentials.add` exige que el tipo sea **TEXTO** (`isinstance(tipo, str)`), y lo
   comprueba **antes de abrir la hoja**: un dato inválido no merece una llamada a Sheets.
3. ⚠️ Chequeo nuevo y GENERAL: **ninguna llamada del repo puede pasar `t` como argumento
   de datos**. Barrido: 5 candidatos, 3 legítimos (`format_func=t`) y 2 que eran variables
   de comprensión — ⚠️ la comprensión tiene ÁMBITO PROPIO (trampa nº3), así que la sonda
   lo contempla; aun así esas dos se renombraron a `_c`, porque usar el nombre `t` para
   otra cosa es pedir el accidente de v447 (donde tapó `t` y **dejó de restar las
   deducciones del neto**).
4. De paso: el aviso de certificados al asignar pintaba «falta» y «vencido» **en español**
   dentro de una f-string. Ahora se traducen al pintar; ⚠️ el literal `'falta'` SIGUE en la
   comparación, porque ahí es el DATO (v442).

### Verificación
`verif_v498.py`, **14 comprobaciones**: el formulario EJECUTADO (tipo normal, «Other» con
texto y «Other» sin texto), la guarda del backend en cuatro formas (función, None, número,
espacios), el barrido del repo **con la sonda validada contra el fallo real reconstruido**
(trampa nº12) y el aviso de certificados. Batería: **4/4 roturas + CONTROL**, incluida la
rotura que reintroduce el fallo exacto del usuario. Suite entera: **131 verde · 0 rojo**.

⚠️ **Las dos credenciales ya guardadas no se tocan por mi cuenta**: el tipo correcto lo sabe
el usuario, y escribir uno inventado en un registro de seguridad es peor que dejarlo roto a
la vista. Se le preguntó cuál era cada una.
"""

FILA = ("| v498 | ⚠️ **El TIPO de credencial se guardaba como la FUNCIÓN de traducción** (lo reportó "
        "el usuario: en la hoja ponía «<function t at 0x…>»). El formulario pasaba `t` donde va el "
        "tipo: nació correcto en v104 (la variable se llamaba `t`), v189 la renombró y v445 hizo que "
        "ese nombre volviera a resolver… a la función de i18n. ⚠️ **Mis pruebas de v350 no lo vieron "
        "porque ejercitaron `add`, no el FORMULARIO** — el fallo estaba en lo que la pantalla le "
        "pasa. Arreglado + `add` exige que el tipo sea TEXTO (antes de abrir la hoja) + chequeo "
        "general: nadie puede pasar `t` como dato (la comprensión tiene ámbito propio, trampa nº3) "
        "+ «falta»/«vencido» del aviso de certificados, traducidos. 14 comprobaciones · **4/4 "
        "roturas + control** · suite 131 verde |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v497 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v498 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v498 + fila + cabecera")
