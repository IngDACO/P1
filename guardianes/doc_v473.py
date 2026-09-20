# -*- coding: utf-8 -*-
"""Documenta v473 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## El icono LITERAL de la biblioteca, y v472 verificada contra la hoja real (v473)

### ⚠️ `T.section` emite HTML: ahi `:material/…:` NO se interpreta
La cabecera de la galeria pintaba **`:material_photo_library: Photos`** en pantalla.
`theme.section` compone HTML y lo saca con `unsafe_allow_html`, y ahi Streamlit no
procesa la sintaxis de icono (v443, el markdown tampoco). ⚠️ Y **los dos unicos sitios
del repo que le pasaban `:material/` a una pieza HTML del kit eran mios**: la
convencion es texto plano, y la incumpli yo.
- Lo destapo **MIRAR LA PANTALLA** en produccion. Ningun guardian lo veia, como el
  `:material/schedule:` en crudo de v375 y los KPI invisibles de v424: no hay error
  que atrapar, solo algo feo a la vista.
- Chequeo nuevo y **general** (no acotado a la biblioteca): ninguna llamada a
  `section`/`chip`/`kpi_row`/`_kpi_card` de TODO el repo puede llevar `:material/`,
  con la sonda validada contra un caso construido antes de creerse su cero.

### v472 ejercitada CONTRA LA HOJA REAL (lo que faltaba)
El ciclo entero, con foto del antes y del despues y produccion devuelta a su sitio
(metodo de v344). Lo que quedo demostrado y no se podia demostrar de otra forma:
- las dos hojas se crean **en el MAESTRO** con sus 12 y 3 columnas exactas;
- ⚠️ y son GLOBALES **de verdad**: con una sesion de `cliente1`, `Projects` resuelve al
  libro de la demo y `Library` al maestro — dos libros DISTINTOS. Comprobarlo con la
  sesion del propietario no habria probado nada: no tiene grupo, asi que su sesion cae
  en el maestro de todos modos (el paso en vacio, trampa nº1);
- alta de catalogo → el mensaje **sobrevive al `st.rerun()`** (v365) y los KPI se
  actualizan, o sea que la invalidacion de caches tambien corre;
- archivar con archivo: **LIB-0001 → LIB-0002**, IDs secuenciales, dos DriveID
  distintos, y la miniatura bajandose de Drive para pintarse;
- **el BORRADO, que era lo critico**: tras quitar los dos, la hoja queda en 0 filas y
  el propio inventario de Drive de la app responde **«Drive is already empty»** — o
  sea que desaparecen **la fila Y el archivo**, que es exactamente lo que protege el
  orden de escrituras de v456;
- y el borrado **exige confirmacion**, con el boton deshabilitado hasta marcarla (v139).

### ⚠️ DOS TRAMPAS DE METODO NUEVAS, las dos del banco de pruebas
**29. El arbol de accesibilidad muestra la etiqueta CRUDA: no dice lo que se ve.**
`read_page` reporto `:material/archive: Show deactivated ones too` **con los dos
puntos** y estuve a punto de apuntarlo como un literal en pantalla. Es el `aria-label`.
Medido en el DOM, el mismo elemento pinta un icono de verdad: `span[role="img"]` con
`font-family: "Material Symbols Rounded"`, glifo `archive`, y `innerText` **sin** los
dos puntos. Es el reverso de la trampa nº5 — alli el texto accesible ocultaba un icono,
aqui enseña marcado que no se pinta. Y la misma fuente engaña con los VALORES: mostraba
el `placeholder` («Choose an option») de unos desplegables que estaban rellenos.
→ Para afirmar que algo sale en pantalla: `innerText` y el DOM. `read_page` sirve para
localizar, no para juzgar lo que se ve.

**30. Un checkbox de Streamlit se marca clicando el TEXTO de la etiqueta, no la caja.**
Un clic en la casilla (13×13) aterrizaba EXACTO —instrumentado con un listener: pedi el
marco (329,532) y llego a CSS (348,563), justo encima— y **no la marcaba**; tampoco
`.click()`, ni la secuencia de eventos de v417, ni foco + espacio. Clicando el TEXTO de
su `<label>`: marcada a la primera.
⚠️ Antes de concluir nada probe el metodo contra **otro checkbox distinto de la app**
(v431: *si el control tampoco cambia, el problema es tuyo*), y tampoco se marcaba — o
sea que era mio, no de la app. Sin esa comprobacion habria reportado un fallo inexistente
en la casilla de confirmar el borrado, que es de lo mas delicado que hay en la pantalla.
⚠️ Y ojo con las coordenadas: el marco de la captura (800×660) NO es el de CSS
(846×698), factor 0,9456. Un clic por `ref` sobre un blanco de 13 px **falla** por ese
desfase, y sobre uno grande acierta — por eso «a veces funciona».

### ⚠️ Y una falsa alarma que casi reporto como fallo de la app
El primer item guardo `Brand` **vacio** habiendo seleccionado la marca. No era la app:
`form_input` sobre un combobox de **react-aria** cambia el texto visible sin avisar a
React, asi que el widget se quedo en su valor por defecto. Seleccionando la opcion con
un **clic real**, `LIB-0002` guardo la marca correctamente. Es la leccion de v431 otra
vez: **validar la entrada antes de acusar al codigo**.
"""

FILA = ("| v473 | ⚠️ **El icono salia LITERAL** en la cabecera de la biblioteca: "
        "`T.section` emite HTML y ahi `:material/…:` no se interpreta (v443) — y los dos "
        "unicos sitios del repo que se lo pasaban a una pieza HTML del kit eran mios. Lo "
        "destapo **mirar la pantalla**, no un guardian (como v375/v424); chequeo nuevo y "
        "general. + **v472 ejercitada contra la hoja REAL**: las hojas se crean en el "
        "maestro, son GLOBALES ⚠️ *probado con una sesion de inquilino* (con la del "
        "propietario no habria probado nada), IDs secuenciales, Drive subiendo y "
        "descargando, y **el borrado deja la hoja en 0 filas y Drive vacio** — la fila Y el "
        "archivo, que es lo que protege v456. Produccion devuelta a su sitio. ⚠️ Dos "
        "trampas de metodo nuevas: **el arbol de accesibilidad muestra la etiqueta CRUDA** "
        "(`read_page` daba `:material/…:` y placeholders de campos que estaban rellenos — "
        "el reverso de la nº5) y **un checkbox de Streamlit se marca clicando el TEXTO de "
        "la etiqueta, no la caja** (el clic aterrizaba exacto y no marcaba; validado contra "
        "otro checkbox de la app, asi que era mio). Y una falsa alarma descartada a tiempo: "
        "el `Brand` vacio era `form_input` sobre un combobox react-aria, no la app |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v472 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))

s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v473 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v473 + fila + cabecera (v473 = actual)")
