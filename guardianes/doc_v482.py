# -*- coding: utf-8 -*-
"""Documenta v482 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## FASE 0 de la ruta: la caché deja de acoplar clientes, y la app se mide (v482)

Primera versión de la ruta que cierra las brechas con los ERP del mercado. La fase 0 no
añade funciones: quita un acoplamiento y pone un número donde había una intuición.

### 0.1 · Una escritura de un cliente obligaba a releer a TODOS
`invalidar()` hacía `_lote.clear()` **sin argumento**, que borra la entrada de todos los
libros. Con N clientes activos, cada guardado costaba hasta N lecturas en vez de una —
contra el techo de 60/min de la **única** cuenta de servicio.
⚠️ **Verificado en vivo antes de escribir nada** (no leído en la documentación): con
Streamlit 1.57, `f.clear("LIBRO_A")` relee A y **deja B en caché**.

⚠️ **Y el argumento tiene que ser el TÍTULO, no el `sheet_id`.** Las hojas GLOBALES
(`Login`, `Groups`, `Rails`, `Manuals`, `Library`, `LibraryModels`) viven en el MAESTRO,
no en el libro del grupo: resolver «el libro de la sesión» tras escribir en una de ellas
habría limpiado **otro** libro y dejado el valor viejo hasta 120 s — el «lo guardé y no
sale» que v339 vino a evitar. Tres módulos escriben en globales (`auth`, `rails`,
`library`), así que no era un caso teórico.

⚠️ **Sin título se sigue tirando ENTERO**, a propósito: limpiar de más cuesta una
lectura, limpiar el libro equivocado enseña datos viejos. Un llamador que se olvide
degrada al comportamiento de antes, no rompe nada. Las **23 llamadas** de los 21 módulos
pasan el título de su propia hoja, **derivado** de lo que cada módulo lee (no escrito a
ojo).

⚠️ De paso se comprobó algo que parecía la fuga de v378 y **no lo era**: el
`sheet_id = sheet_id or …` que hay DENTRO de `_lote` sí sería un desastre… si alguien la
llamara sin argumento. `registros()` resuelve el libro FUERA y lo pasa como clave, así
que el diseño de v359 aguanta. Mirar el llamador antes de acusar.

### 0.2 · La app mide su propio consumo de la API
Decidir entre «más cuentas de servicio» y «salir de Sheets» es la decisión más cara de la
ruta y se habría tomado a ojo. `core/metrics.py` (módulo HOJA, solo stdlib) cuenta lo que
ya se hace: **no cuesta ni una llamada**.
- **El enganche va en `timeclock._ConReintento.request`**, que es NUESTRA subclase del
  cliente HTTP (nació en v290 para el reintento): el único punto por el que pasa todo el
  tráfico de gspread, sin instrumentar 90 módulos ni tocar las tripas de una librería.
- ⚠️ **Se apunta cada INTENTO, no cada llamada lógica**: un 429 reintentado son dos
  llamadas contra la cuota, y contar solo la lógica subestimaría justo la ráfaga que se
  quiere medir.
- ⚠️ **Lectura y escritura se clasifican por ENDPOINT, no por método HTTP**: tienen
  cuotas SEPARADAS (60/min cada una) y `values:batchGet` —la llamada que más usa la app
  desde v339— es un GET, mientras `values:append` es un POST igual que otras lecturas por
  lote.
- ⚠️ **El pico se busca con ventana DESLIZANTE**, no partiendo el tiempo en minutos de
  reloj: la ráfaga real es de 06:59:40 a 07:00:20 —cuando ficha la cuadrilla— y en cubos
  de reloj se repartiría entre dos minutos sin aparecer en ninguno.
- ⚠️ **Vive en memoria del proceso, no en una hoja**: escribir las métricas en Sheets
  gastaría justo la cuota que se quiere medir. Streamlit Cloud corre un proceso para
  todos, así que el contador mide exactamente lo que el techo limita.
- Pantalla en **Administración → 📈 Cuota** (propietario), con el veredicto en palabras
  además de en números: **manda el pico, no la media** — la media siempre tranquiliza.

### ⚠️ Tres fallos de MÉTODO, los tres míos y los tres ya documentados
Ninguno se vio leyendo; los tres los destapó la batería de roturas.
1. **Mi chequeo de «una lectura real incrementa el contador» medía CERO llamadas.**
   Llamaba a `auth.list_groups()` tras `hojas.invalidar()`, y esa función sale de la
   caché PROPIA de `auth`, que el lote no toca. O sea que no hubo ninguna llamada que
   contar y parecía que el enganche no funcionaba: **un cero medido sobre nada**, el paso
   en vacío de la trampa nº1, dentro del chequeo escrito para probar el enganche.
2. **Un chequeo INTERMITENTE**, que es el peor: el caso del pico anclaba sus eventos en
   `ahora − 300`, así que **pasaba o fallaba según el segundo en que se lanzara** (si ese
   instante caía al principio de un minuto, los dos grupos quedaban en el mismo). Es la
   familia del guardián que se ponía rojo todos los lunes (v443). Anclado al segundo :40
   de un minuto de reloj: cuatro corridas seguidas, cuatro verdes.
3. **La batería se provocó un 429 a sí misma.** Once corridas seguidas del guardián, cada
   una con una lectura real, y el CONTROL salió rojo — en solitario pasaba. Es la trampa
   nº19 («amontonarlos es provocarse un 429 y leer un rojo falso») cometida en el script
   que venía a verificar. Ahora van espaciadas.

Y la **trampa nº26 por séptima vez**: un heredoc convirtió los `\\n` de una rotura en
saltos reales y dejó el banco de pruebas roto. Se reescribe con la herramienta de
escritura o componiendo con `chr(10)`, nunca por heredoc.

### Verificación
`verif_v482.py`, **37 comprobaciones**. Las que valen: ⚠️ **primero se comprueba que los
dos libros son DISTINTOS** —con el mismo libro, «limpia solo el suyo» pasaría sin
significar nada—; después se EJECUTA `invalidar()` sobre la función REAL (sustituyendo
solo el lote, para no gastar cuota) y se exige que escribir en el grupo **no toque el
maestro** y al revés; el medidor clasificando sus seis casos; el pico viendo las 80
llamadas juntas; una lectura REAL de Sheets incrementando el contador; la pantalla del
propietario **ejecutada** en sus dos estados; y que el despacho del propietario deje
**exactamente una** sub-sección al `else` (la lección de v449).
Batería: **11 roturas, 11 cazadas + CONTROL verde**, con el verde de base comprobado
antes (sin ese paso una tanda entera sale «cazada» sin probar nada, v459).

### Y `NEGOCIO.md`, que llevaba 400 versiones desfasado
Decía «estado actual: **v75**» y colocaba en *fase futura* la nómina, el costeo por
proyecto y la gestión documental — **las tres llevaban meses desplegadas**. Puesto al día
el estado de hecho (funciones reales, lo que NO existe dicho sin adornos, y las fases 2-3
del roadmap marcadas), ⚠️ **sin tocar ni una decisión estratégica**: pricing, ICP, mercado
y diferenciación son del chat estratégico. Donde la realidad contradice una decisión, se
señala en vez de reescribirla.
"""

FILA = ("| v482 | **FASE 0 de la ruta ERP.** ⚠️ `invalidar()` hacía `_lote.clear()` **sin "
        "argumento**, que borra la caché de TODOS los libros: una escritura de un cliente "
        "obligaba a releer a los demás contra el techo de 60/min de la única cuenta de "
        "servicio. Ahora recibe el **TÍTULO** de la hoja — ⚠️ no el `sheet_id`, porque las "
        "GLOBALES viven en el maestro y resolver «el libro de la sesión» limpiaría otro—, y "
        "**sin título sigue tirando entero**: un llamador que se olvide degrada, no rompe. "
        "+ **la app mide su propio consumo** (`core/metrics.py`, enganchado a NUESTRA "
        "subclase del cliente HTTP): cada INTENTO (un 429 reintentado son dos llamadas), "
        "lectura/escritura por **endpoint** y no por método, y el pico con **ventana "
        "deslizante** porque la ráfaga real va de 06:59:40 a 07:00:20. Pantalla en "
        "Administración → 📈 Cuota. ⚠️ Tres fallos de método MÍOS, los tres cazados por la "
        "batería y no leyendo: un chequeo que medía **cero llamadas** sobre una caché que "
        "no había tocado, uno **intermitente según el segundo** en que se lanzara (v443), y "
        "la batería **provocándose un 429** (trampa nº19 en el script que venía a "
        "verificar). 37 comprobaciones · **11/11 roturas + control** · + `NEGOCIO.md` puesto "
        "al día tras **400 versiones** desfasado |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v481 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v482 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v482 + fila + cabecera")
