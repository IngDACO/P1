# Survey App — IngDACO/P1  
## Referencia completa para Claude (leer siempre al inicio)

---

## Links
- **GitHub:** https://github.com/IngDACO/P1 (rama: main)
- **Streamlit:** https://dwl6s39d7u3yfwfkbpcpah.streamlit.app/
- **Drive:** https://drive.google.com/drive/folders/1PK7znRaCGWcycDJ6neUJPy72TqwgSxQW

## Deploy (siempre hacer esto al terminar cambios)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& "C:\Users\diego\backup_survey.ps1" -Version N -Mensaje "descripcion"
```
Hace: git push → ZIP → rclone Drive. Streamlit redeploy es automático.

### ⚠️ Entorno de Streamlit Cloud (NO romper) — v66
- **Python 3.12** en Streamlit Cloud (Settings → Python version). **NO usar 3.14**: solo tiene ruedas
  nativas de versiones bleeding-edge que **segfaultean** (pasó en v65 con pandas 3.0/reportlab 5.0/
  numpy 2.5/pyarrow 25 → `Segmentation fault`, no una excepción Python).
- **`requirements.txt` va PINEADO** con topes de major (pandas<2.3, numpy<2, reportlab<5, svglib<2,
  lxml<6, pillow<12, pyarrow<18). NO volver a dejar todo `>=` sin tope.
- Un segfault en los logs = problema de dependencias/entorno, **nunca** del código Python.

---

## Estructura de archivos
```
C:\Users\diego\P1\survey_app\
├── app.py                  # UI Streamlit — login + navegación por rol (NO st.tabs, ver abajo)
├── VERSION                 # texto "vNN" — se actualiza solo en cada deploy, lo lee app.py (utf-8-sig)
├── requirements.txt        # streamlit, pypdf, pandas, numpy, openpyxl, reportlab,
│                           #   anthropic, svglib, gspread, google-auth
├── .streamlit/
│   ├── secrets.toml        # LOCAL (gitignored): ANTHROPIC_API_KEY, GMAIL_*, gcp_service_account, TIMECLOCK_SHEET_ID,
│   │                       #   [gdrive] (docs), TELEGRAM_BOT_TOKEN/USERNAME (avisos), APP_URL
│   └── config.toml         # enableStaticServing = true (para el manifest/íconos PWA)
├── static/                 # PWA: manifest.webmanifest + icon-192/512.png (COPEX) — versionados (ver .gitignore)
├── core/
│   ├── calculations.py     # calculate_limits(), apply_offsets(), analyze_matrix(), validate_inputs()
│   ├── optimizer.py        # optimize() — itera RL×FB (incluye frame_opening + FB extra preciso)
│   ├── highlighting.py     # cell_state(), streamlit_style(), reportlab_commands()
│   ├── bs_logic.py         # find_bs_step() — BSR vs BS (triangular)
│   ├── excel_io.py         # export/import survey Excel
│   ├── survey_ui.py        # render_survey_tab(_ROL,_GRUPO) — TODA la seccion Survey (v125)
│   ├── field_pack.py       # field_pack_pdf() — paquete de obra en 1 PDF (v126)
│   ├── plan_store.py       # plano UNICO de la sesion, compartido por 5 herramientas (v128)
│   ├── plan_data.py        # extraer_todo/guardar/del_proyecto — datos del plano EN el proyecto (v137)
│   ├── plan_ui.py          # selector_proyecto/aplicar — el plano segun el rol (v137)
│   ├── ui_common.py        # elegir() sin preseleccion + confirmar_borrado() (v139)
│   ├── clock.py            # now()/today() en la hora LOCAL del grupo (Grupos.Zona; UTC->local, v173)
│   ├── toolruns.py         # hoja Calculos: cada uso de una herramienta alimenta el proyecto (v129)
│   ├── tool_pdf.py         # PDF comun de las 4 herramientas de calculo (v129)
│   ├── tool_save_ui.py     # bloque compartido descargar + guardar en el proyecto (v129)
│   ├── survey_calc.py      # recalcular() — solucion determinista desde ParamsJSON (v128)
│   ├── diagrams.py         # floor_plan_svg() planta técnica a escala + shaft_iso_svg() isométrica (v119)
│   ├── schedule.py         # build_schedule/schedule_svg — cronograma Gantt + curva S (v51)
│   ├── report.py           # generate_report() — INFORME ADMIN (completo)
│   ├── user_report.py      # generate_user_report() — INFORME CLIENTE (limpio, COPEX)
│   ├── interpretation.py   # IA: interpretación admin (7 secc) + cliente (5 secc); anthropic LAZY import
│   ├── chat_agent.py       # get_chat_response() — asistente experto (sidebar), confidencialidad; anthropic LAZY
│   ├── email_notify.py     # send_usage_notification() — correo interno + informe admin adjunto
│   ├── plumb.py            # compute_plumb/plumb_svg/plumb_table — plomadas (LINE_NAMES v58)
│   ├── plumb_ui.py         # render_plumb_tab() — plomadas (lee PDF autocompleta, v57)
│   ├── rail_cut.py         # extract_lf + compute_case1/case2 — corte de rieles (v52)
│   ├── rail_cut_ui.py      # render_rail_cut_tab() — corte de rieles
│   ├── buffer_cut.py       # extract_hkp + compute_buffer_cut — corte de buffers (v96)
│   ├── buffer_cut_ui.py    # render_buffer_cut_tab() — corte de buffers
│   ├── prestart.py         # submit()/list — Daily Pre-Start: hoja PreStarts + Drive + alarma (v97)
│   ├── prestart_pdf.py     # generate_prestart_pdf() — PDF del pre-start (marca=grupo)
│   ├── prestart_ui.py      # render_prestart_tab() — pestaña 🦺 Pre-Start diario
│   ├── timeclock.py        # clock_in/out — fichaje por login+grupo (sin PIN, v54)
│   ├── timeclock_ui.py     # render_timeclock_tab() — fichaje (usa identidad del login)
│   ├── auth.py             # login, roles, grupos, sesión única, contacto (Sheets, PBKDF2) — v53+
│   ├── auth_ui.py          # render_login/user_bar/owner_panel(grupos/usuarios/proyectos/rieles)/group_panel + ficha 360 (v184) + credenciales
│   ├── home_ui.py          # LA shell de la app (v190-192, POR ROL desde v297-299): sidebar de 2 niveles + top bar (← atrás, buscador, versión, campana) + HOME del admin + router de secciones
│   ├── theme.py            # sistema de diseño COPEX (v283): inject() + kpi_row/chip/section + PALETA. USARLO en UI nueva
│   ├── route_ui.py         # 🗺 Ruta del día (v270): obras ordenadas para ir a terreno + link a Google Maps
│   ├── location_ui.py      # location_picker: dirección→coordenadas (Google Geocoding + respaldo OSM) + pin en mapa (v193/v268)
│   ├── clientes.py/_ui     # 👥 Contactos = CRM de clientes (hoja Clientes, v254-256)
│   ├── invoices.py/_ui     # facturas: cobrar + PDF (v257-261)
│   ├── payroll.py/_ui      # nóminas y colillas: pagar + PDF (v257-261)
│   ├── inventory.py/_ui    # 📦 Inventario de activos con QR, movimientos y depreciación (v263-265)
│   ├── expenses.py         # costos: compras + mano de obra + presupuesto + P&L (v105+)
│   ├── orders.py           # órdenes de compra = dinero COMPROMETIDO (hoja Ordenes, v343)
│   ├── auditoria.py        # rastro de cambios: quién tocó margen/tarifa/fechas (hoja Auditoria, v342)
│   ├── hojas.py            # lector por LOTES del libro (1 batchGet para todas las hojas, v339)
│   ├── num.py              # helpers únicos: num() / parse_date() / col_letter() (v323)
│   ├── flash.py            # mensajes que SOBREVIVEN a un st.rerun() (v365-v367). Módulo HOJA.
│   │                       #   flash.exito/aviso/error/info() encolan; la shell y el login
│   │                       #   los pintan con mostrar(). ⚠️ 87 mensajes se tiraban antes.
│   ├── tenant.py           # aislamiento por empresa cliente: puede_ver/exigir (v351). Módulo HOJA.
│   ├── credentials.py      # credenciales/tickets por usuario (hoja Credenciales): vencimiento, Drive, avisos (v104)
│   ├── session_cookie.py   # login persistente por cookie (extra-streamlit-components); manager unico por sesion (v188)
│   ├── projects.py         # gestión de proyectos: Proyectos/Actividades/Agrupaciones/Documentos (Sheets) — v65+
│   ├── projects_ui.py      # panel admin/propietario/campo + docs + alarmas + cronograma real vs plan
│   ├── drive_store.py      # documentos por proyecto en Google Drive (OAuth drive.file) — v74
│   ├── notify.py           # notificaciones email + Telegram (asignación, avisos) — v77
│   ├── alerts.py           # alarmas/avisos por proyecto (campo↔admin) — v88
│   ├── belting.py          # compute_belting/belting_svg — belting (DSTS) — v86
│   ├── belting_ui.py       # render_belting_tab()
│   ├── rails.py            # catálogo de rieles (referencia→medidas) para autocompletar RAIL — v84
│   ├── roster.py           # tablero de cuadrilla: catalogo Trabajos + hoja Roster (v159).
│   │                       #   DIAS (lun-vie) + DIAS_EXTRA (sab/dom) + DIAS_TODOS en orden
│   │                       #   de weekday(); `dias_con_datos` decide qué columnas se pintan (v390)
│   └── roster_ui.py        # 📅 Planificacion (admin): 3 vistas — Semana (rejilla editable en
│                           #   sitio, v217) · Día (la cuadrilla sobre un eje de horas, v390) ·
│                           #   Libres. + «Ver el día» de UNA persona con carriles (v387)
└── extractors/
    └── schindler.py        # extract_from_pdf() + extract_car_guide_rail() + extract_belting() — pypdf CAD PDF

C:\Users\diego\copex_mobile\   # App Android (Capacitor) — carga la URL de Streamlit; ver sección Móvil
```

**Versión (v35+):** `app.py` lee `survey_app/VERSION` con `utf-8-sig` (evita el BOM que agrega
PowerShell). `backup_survey.ps1` escribe `"vNN"` antes de cada commit → se actualiza sola.

## NAVEGACIÓN — una sola shell para los 3 roles (v299) ⚠️ ACTUALIZADO

⚠️ **La navegación vieja YA NO EXISTE.** Hasta v296 había DOS: la shell nueva (`core/home_ui.py`,
solo admin desde v190) y, en `app.py`, la cabecera COPEX + un `st.radio` horizontal (`main_nav`)
con su cadena `if/elif _seccion == _L_*` para propietario y campo. **v297-v299 migraron los tres
roles a la shell y borraron la vieja entera** (132 líneas de `app.py` + `auth_ui.render_owner_panel`).
Si lees `_L_SURVEY`, `_NAV_DISPLAY`, `main_nav`, `_nav_pending` o `render_group_panel` en algún
sitio: **son de la nav muerta**, están solo en el historial de git.

### Cómo se navega ahora
**Menú lateral de 2 niveles** (acordeón, `home_ui.sidebar_menu`) + **barra superior**
(`render_topbar`: botón ← Atrás, buscador —solo gestión, aún sin backend—, versión y campana).
`app.py` ya no enruta nada: llama a `render_topbar` + `render_admin_content` y se acabó.

**Las secciones dependen del ROL** (`home_ui._SECCIONES_ROL` / `_SUBSECCIONES_ROL`):

| Rol | Secciones (nivel 1) |
|---|---|
| **administrador** | Home · Fichaje · Planificación · Proyectos · Finanzas · Inventario · Herramientas · Contactos |
| **campo** | Mis proyectos · Fichaje · Pre-Start · Herramientas · Mis credenciales · Mis colillas |
| **propietario** | Administración · Pre-Start · Herramientas (no ficha, v93) |

- ⚠️ El **rol se resuelve DENTRO** de `home_ui` (`_rol()`, lee `session_state.auth`), no se pasa por
  parámetro: así ninguna firma cambió al migrar y el camino del admin quedó intacto.
- ⚠️ **El default de `_secciones()`/`_subsecciones()` es el del CAMPO, no el del admin.** Es a
  propósito: la shell sirve a todos, así que ese default decide qué ve un `Rol` que no
  reconozcamos (un typo en la hoja Login). Caer en la nav de gestión sería regalar acceso.
- **Sub-pestañas = (ID, display)** (v232): el ID conserva el emoji porque es el IDENTIFICADOR que
  usan los deep-links y el match en los `_seccion_*`; el display es lo único que cambia. La
  sub-key del propietario es **`owner_sec`**, la MISMA del radio viejo, para no romper el
  deep-link de `survey_ui`.
- **Deep-links**: SOLO `_admin_nav_pending` (`home_ui.navegar` / `projects_ui._ir_a`), aplicado en
  `_aplicar_nav_pending()` ANTES de instanciar los menús (regla v111).

### Lo que sigue vigente
**NO usar `st.tabs`** (v56): causaba mezcla de contenido. Toda sub-navegación va con `st.radio`
o con el sidebar.

**5 HERRAMIENTAS TÉCNICAS (v154):** 📐 Survey · 🔩 Plomada · ✂️ Rieles · 🛡 Buffers · 🎗 Belting,
dentro de la sección **Herramientas** (+ una página "Inicio" con una tarjeta por herramienta, v231).
El Survey es UNA MÁS (la más potente, no un caso aparte). El **🦺 Pre-Start NO es una herramienta
técnica**: es SEGURIDAD de obra → sección PROPIA para campo y propietario; para el admin está
dentro de Herramientas.

⚠️ **El rol `conductor` se ELIMINÓ en v163** (era un subconjunto del campo tras unificar el fichaje en
v150). Solo quedan 3 roles: propietario, administrador, campo.

---

## ⚠️ TRAMPAS DE VERIFICACIÓN (v289-v299) — leer antes de "verificar" algo

Un chequeo que pasa en falso es PEOR que no tener chequeo: da confianza sin dar evidencia.
Estas cinco mordieron en una sola tanda:

1. **El paso en VACÍO.** Un test comparó `None == None` y dio "OK": el regex no capturaba la rama
   del propietario, así que el rol que más importaba proteger **no se verificó**. → Todo test que
   compare dos cosas extraídas debe **primero afirmar que se extrajo algo** (`bool(antes) and
   bool(ahora)`).
2. **Grep ≠ uso.** Un guardián bloqueó un borrado por una referencia que era **mi propio
   comentario**; y un chequeo de "no queda `main_nav`" falló por lo mismo. → Para saber si un
   símbolo se usa, **AST** (Name/Attribute/import); para buscar en código, quitar comentarios con
   `tokenize`.
3. **Falsos positivos del chequeo de nombres libres**: argumentos de `lambda`, el **operador
   morsa** (`if x := ...`, `ast.NamedExpr`) y `__file__` salen como "sin definir" si no se
   contemplan.
4. **`key = f"..."` no es una key de widget.** Contar keys duplicadas por regex mezcla la variable
   local con el `key=` de la llamada. → Sacar los `keyword` de los `ast.Call`.
5. **El icono puede no ser un `<svg>`.** El chevron del `st.popover` es `expand_more`, un Material
   Symbol renderizado como **ligadura de fuente** (`span[data-testid=stIconMaterial]`). Un
   `button svg{display:none}` no hace nada. → Medir el DOM antes de escribir CSS (regla v121:
   *medir, no mirar*), y apoyarse en `data-testid` (contrato de Streamlit), NUNCA en las clases
   `st-emotion-cache-*`, que cambian de versión.

**Añadidas en v363-v368 (una tanda de simular datos reales):**

6. **El FALLO en falso, gemelo del OK en falso.** Comparar un total antes/después en dos
   ejecuciones dio 20 h de diferencia y parecía que el cambio movía cifras: era una sesión
   de fichaje ABIERTA acumulando contra el reloj. → Comparar las dos lógicas **sobre las
   mismas filas y el mismo instante**, no en dos corridas.
7. **Un epsilon simbólico hace fallar el test por su propia aritmética.** `1e-6` sobre una
   suma de 473 flotantes (3.309 h) daba FALLO por 0,02 s de ruido. → Tolerancia con sentido
   FÍSICO.
8. **Un guardián de EJECUCIÓN no sustituye a uno ESTÁTICO.** El de v306 cortaba
   `create_project` correctamente… pero solo al pulsar el botón, y como nadie creó un
   proyecto en 3 versiones, el fallo vivió escondido. → Si se puede comprobar sin tocar
   producción, hazlo estático.
9. **Al convertir un patrón en masa, mirar el DIFF antes de desplegar.** El parche de los
   mensajes convirtió una insignia de ESTADO (`st.success` + `if st.button()`), que habría
   desaparecido de pantalla y reaparecido como fantasma en otra. Se vio revisando, se
   revirtió desde el respaldo y se afinó la regla.
10. **Comprobar el ÁMBITO, no la presencia** (v342, repetido): un import local dentro de
    OTRA función hace creer que el módulo está disponible. Y el verificador no debe
    descender a los `def` al mirar el ámbito de módulo — ahí es donde se autoengaña.
13. ⚠️ **Correr un SUBCONJUNTO de guardianes es peor que no tenerlos** (v385). Venía
    ejecutando la lista que recordaba: «13 en verde» mientras la suite completa tenía
    48 y **13 fallaban**, dos de ellos introducidos ese mismo día. Un subconjunto
    curado da la sensación de cobertura sin la cobertura. → **La suite ENTERA, siempre.**
    Y cuando un guardián lleva tiempo en rojo, clasificarlo: *caducado* (el código
    cambió a propósito → se actualiza la afirmación **con la razón escrita**) o
    *regresión* (se arregla el código). Relajarlo porque molesta es taparse los ojos;
    y ⚠️ **antes de «arreglar» lo que denuncia, mirar el código acusado** — uno de
    ellos señalaba un fallo que no existía (`get_all_records` contiene `_records`).
12. ⚠️ **Una sonda NEGATIVA no vale hasta validarla con un caso conocido-bueno** (v375).
    Concluí que un modal «no se pintaba nunca» porque mi `MutationObserver` buscaba
    `div[role="dialog"]` —el marcado del Streamlit LOCAL— y el del Cloud es
    `[data-testid="stDialog"]`. El modal estaba ahí. Un observador que «no vio nada»
    suena a prueba y es solo una sonda mal apuntada. → Antes de afirmar «X no está»,
    comprobar que la sonda SABE ver X cuando X está; y mirar la captura antes de
    diagnosticar. Es la nº5 (ligaduras) y v304 (CSS caducado) otra vez: **el DOM de
    Streamlit cambia entre versiones y el entorno de prueba no es el que corre.**
11. ⚠️ **El `secrets.toml` LOCAL no es el del Cloud.** `telegram_configured()`,
    `app_url()`, `is_configured()`… medidos en local dicen qué tengo YO, no qué tiene
    producción. En v368 medí Telegram en local (`False`), lo presenté como el estado real
    y describí «7 usuarios encerrados sin salida»; en el Cloud el bot SÍ estaba y siempre
    tuvieron camino. Es la regla de v145 («auditar contra lo real») aplicada a la
    CONFIGURACIÓN: para afirmar algo del entorno real, mirarlo EN el entorno real.

**Añadidas en v387-v395 (la tanda de la vista por día y el fin de semana):**

14. ⚠️ **El navegador NORMALIZA el atributo `style`, y un selector literal falla.**
    Mi sonda buscaba `div[style*="position:absolute"]` y daba **cero resultados**
    con los bloques perfectamente pintados: el DOM guarda `position: absolute`
    **con espacio**. Iba a reportar «Streamlit sanitiza el CSS». → Para comprobar
    estilos, `getComputedStyle`, NUNCA una subcadena del atributo. Es la nº12
    (sonda negativa) otra vez: **antes de decir «no está», comprobar que la sonda
    ve el caso conocido-bueno.**
15. ⚠️ **`sorted()` es alfabético; el dominio casi nunca lo es.** Mi test de
    auto-poblado dio 4 FALLOS con el código correcto porque comparaba
    `['jue','lun','mar','mie','vie']` contra el orden de la semana. → Ordenar por
    la clave del DOMINIO (`key=DIAS_TODOS.index`). Gemelo del `"40"` vs `"40.0"`
    de v372: **un test que ordena o formatea distinto que el código genera fallos
    en falso**, y cada uno cuesta media hora de buscar un fallo que no existe.
16. ⚠️ **Un guardián atado a la FORMA caduca cuando la forma cambia a propósito.**
    `verif_panel` exigía literalmente que existiera la columna `b5`; al pasar la
    barra de 5 a 4 columnas (con la misma cantidad de chrome) se puso rojo sin que
    nada estuviera mal. Igual el de v302, atado al literal «Toda la semana
    (Lun–Vie)». → La afirmación se escribe sobre el PRINCIPIO (el chrome no vuelve
    a ser cuatro bandas; el atajo cubre los días visibles) y el número se DERIVA
    del propio código. Y al actualizarlo, la razón queda escrita al lado (v385).
17. ⚠️ **Todo componente de terceros trae un tamaño por defecto que no es el tuyo.**
    `st_canvas` nace con `width=600` y no tiene `use_container_width`: en un móvil
    de 375 px el lienzo salía de 600 dentro de un hueco de 343 y **la mitad derecha
    de la firma quedaba fuera de la pantalla**. Es el `st_folium` de 500 px de v307
    repetido. → Al integrar un componente, mirar su firma (`inspect.signature`) y
    medirlo EN EL TAMAÑO EN QUE SE VA A USAR — para el Pre-Start, el teléfono.

**Añadidas en v397-v399 (la tanda de facturar desde la cartera y el formato del dinero):**

18. ⚠️ **Lo que pinta `st.dataframe` NO está en el DOM: está en un canvas.**
    glide-data-grid pinta las celdas en `<canvas>` y su nodo accesible lleva el
    valor **CRUDO** (`27882.67`), no el formateado. Así que ninguna sonda del DOM
    puede responder «¿cómo se ve esta columna?». → La técnica que SÍ funciona es
    **interceptar `CanvasRenderingContext2D.prototype.fillText`** y forzar un
    repintado (mover el scroll de verdad, o un `resize_window` REAL — un
    `new Event('resize')` sintético no dispara nada, glide observa su contenedor).
    Con eso se lee exactamente lo que ve el usuario. Y ⚠️ los `[role="columnheader"]`
    miden **0×0 en (0,0)**: preguntarles por geometría da «está fuera de pantalla»
    hasta para la primera columna. Lo que sí informa es la **virtualización**: solo
    las columnas EN VISTA existen en el DOM (validado moviendo el scroll y viendo
    cambiar el conjunto entero).
19. ⚠️ **Un guardián lanzado desde el directorio equivocado da rojos que no existen.**
    Streamlit busca `.streamlit/secrets.toml` **relativo al CWD**, así que correr la
    suite desde `C:\Users\diego` tumbó 16 guardianes con «No secrets found» y
    parecían regresiones. Se corren con `cwd=survey_app`. Y ⚠️ **espaciados**: 16 de
    ellos leen la hoja real y el techo son 60 lecturas/min — amontonarlos es
    provocarse un 429 y volver a leer un rojo falso (es el error de v377, cometido
    en el script que venía a verificar).
20. ⚠️ **Antes de sustituir un especificador de formato, mirar qué hace con los
    decimales.** `%d` **trunca** y `%.0f` **redondea**: 3305.76 sale `$3,305` con uno
    y `$3,306` con el otro. «Unificar los formatos» habría movido cifras en pantalla
    sin que nadie lo pidiera. Se inserta la coma y cada columna conserva su semántica.

**Añadida en v408 (la tanda del barrido de pantallas):**

21. ⚠️ **`st.dataframe` recorta el texto por CLIP, sin elipsis — buscar «…» es una
    sonda ciega.** Al estrechar columnas, interceptar `fillText` y filtrar por `…` dio
    **0 truncados** con nueve textos cortados de verdad: glide llama a `fillText` con la
    cadena ENTERA y deja que el canvas la recorte, así que ni hay «…» ni el DOM lo
    delata. Lo que sí mide es **`this.measureText(t).width` dentro del propio hook**,
    comparado con el ancho declarado de esa columna menos el padding: ahí aparecieron
    los 60 px que se comía el nombre de obra y los 60 del cliente. Es la nº12 (sonda
    negativa sin validar) en su forma más cara, porque el «0 truncados» **invitaba a
    apretar más**. → Y la sonda quedó validada por el camino: el mismo medidor que
    encontró los 9 cortes es el que después dio 0, así que ese 0 significa algo.
22. ⚠️ **Encoger para que quepa puede cambiar un problema visible por uno invisible.**
    Con 12-13 columnas y nombres de obra reales NO hay reparto de anchos que entre en
    1054 px. «Que quepa todo» habría dejado la tabla sin scroll y con los nombres
    leídos a medias — peor que desplazarse, porque el corte no se anuncia. La cura es
    la de v398: **no achicar, PRIORIZAR** lo que se ve primero, y `pinned` para que la
    identidad no se escape por la izquierda mientras miras la derecha.
23. ⚠️ **Un rojo de la SUITE puede ser de la consola, no del código.** Cuatro
    guardianes salían con código ≠ 0 imprimiendo `TODO OK`: el hijo hereda un stdout
    en **cp1252** y morían con `UnicodeEncodeError` al pintar un emoji (🔩, 🌐). Se
    arregla en el runner (`env` con `PYTHONIOENCODING=utf-8`), no relajando a los
    guardianes. Misma familia que el CWD de v19: **el entorno de ejecución fabricando
    falsos rojos**, que es lo que empuja a «arreglar» código sano.

**Y la regla de siempre, que volvió a aplicar:** antes de borrar el LECTOR de un mecanismo, buscar
sus ESCRITORES y convertirlos. En v299 `_nav_pending` tenía dos vivos («Abrir proyecto» tras el
survey y «Reabrir cálculo»); borrar solo el lector los habría dejado como botones que no hacen
nada, sin ningún error (patrón v140/v146).

---

## Parámetros de entrada

### Del PDF (schindler.py los extrae)
`TKSW, BKS, TKA, TKS, TSW, BGS, BKF1, BKF2, BS, BT, BK, TK, TS, SF1, SF2, SG, TG`

⚠️ **BT = apertura de la puerta de rellano** (NO es el ancho de la cabina)  
⚠️ **BS = SF1 + BKS + 2×RAIL + SF2** = ancho total del hueco según plano  
⚠️ **Ancho del bloque cabina = BKS + 2×RAIL** (tratado como un solo bloque)

### Del usuario (app.py — USER_ONLY)
`BSR, FS, FRAME, RAIL, OFFSET_CABIN`  
⚠️ `BC` fue **eliminado** de inputs — ahora se calcula como `BC_CALC`  
⚠️ `WALL_LEFT` / `WALL_RIGHT` fueron **eliminados** — reemplazados por `OFFSET_CABIN` + `OFFSET_SIDE`  
⚠️ **BSR** = ancho real del hueco medido en obra (puede diferir de BS)

### Configuración
- `OMEGA_SIDE`: R o L (lado del Omega)
- `WALL_LIMITING`: True/False → **Caso 1** o **Caso 2**
- `WALL_STOP`, `WALL_SIDE`: solo si WALL_LIMITING=True
- `WALL_LEFT`, `WALL_RIGHT`: muros de la apertura

### Totales de survey (última fila)
`WRT, FRT, ORT, WLT, FLT, OLT`

---

## calculations.py — calculate_limits(p)

### Límites geométricos
```python
LIMIT_WR = SF2 + RAIL/2
LIMIT_WL = SF1 + RAIL/2
LIMIT_FR = TKSW - 150
LIMIT_FL = TKSW - 150
base     = BKS/2 + RAIL/2 - BT/2 - FRAME
LIMIT_OR = base + OFFSET_CABIN  (si OFFSET_SIDE=L)  |  base - OFFSET_CABIN  (si OFFSET_SIDE=R)
LIMIT_OL = base - OFFSET_CABIN  (si OFFSET_SIDE=L)  |  base + OFFSET_CABIN  (si OFFSET_SIDE=R)
```

### Límites Omega/Z (dependen de OMEGA_SIDE)
```
limit_ob_raw = (SG - TG/2) × 0.3

Omega=R → LIMIT_R = limit_ob_raw, LIMIT_L = SF1×0.3, Z_SIDE=L
Omega=L → LIMIT_R = SF2×0.3,      LIMIT_L = limit_ob_raw, Z_SIDE=R
```

### Restricción FB hacia atrás (NUEVO — v6/v7)
```python
BC_CALC     = TS - TKSW - (TK/2) - 25    # espacio libre detrás cabina
DIF_TSW_FS  = FS - TSW
FB_MAX_BACK = 0.0            if DIF_TSW_FS > BC_CALC or BC_CALC <= 0
            = float(BC_CALC) otherwise
```

### Offsets
```python
Offset_FR = LIMIT_FR - FRT
Offset_FL = LIMIT_FL - FLT
Offset_WR = LIMIT_WR - WRT + (BSR-BS)/2
Offset_WL = LIMIT_WL - WLT + (BSR-BS)/2
Offset_OR = Offset_WR    # igual que lateral
Offset_OL = Offset_WL
```

### apply_offsets — IMPORTANTE: OR y OL RESTAN el offset
```python
WR = row["WR"] + Offset_WR    # suma
FR = row["FR"] + Offset_FR    # suma
OR = row["OR"] - Offset_OR    # RESTA (no suma)
WL = row["WL"] + Offset_WL
FL = row["FL"] + Offset_FL
OL = row["OL"] - Offset_OL    # RESTA (no suma)
```

### Dimensiones
```python
CS   = TK + TKA
TL   = CS + TKS + TSW
TLBC = TL + BC_CALC
```

---

## optimizer.py — optimize(survey_adjusted, limits, params)

### Columnas activas según caso
```
Caso 1 (WALL_LIMITING=True):  cols = [WR, FR, OR, WL, FL, OL]
Caso 2 (WALL_LIMITING=False): cols = [WR, FR, WL, FL]   ← OR/OL NO cuentan como OFF
```

### Restricciones aplicadas en cada paso (en orden)
```
1. RL < 0 y |RL| > LIMIT_R  → SKIP
2. RL > 0 y |RL| > LIMIT_L  → SKIP
3. FB > FB_MAX_BACK          → SKIP   (restricción espacio trasero)
4. Pared limitante (si wall=True y RL va hacia la pared):
   a) OR/OL en WALL_STOP > LIMIT y FS > TSW
      → aplica FB extra para evadir el muro físicamente (ver fórmula abajo)
      → el nivel WALL_STOP queda evadido: OR/OL de ese nivel NO cuentan
      → NO hay SKIP duro (muro superado)
   b) fb_extra_applied=True Y |RL| > FRAME
      → SKIP [skip_type=frame_opening]
      (al empujar hacia la pared más que FRAME, la apertura de la cabina
       queda tapada por el muro limitante — apertura siempre debe ser visible)
   c) OR/OL en WALL_STOP > LIMIT y FS ≤ TSW (sin espacio para evadir)
      → SKIP duro
```

### FB extra — fórmula precisa (v28/v29) ⚠️ IMPORTANTE
El push extra NO es siempre `FS−TSW` completo. La posición objetivo es absoluta
(`FS−TSW` desde el neutro), y se descuenta lo que el piso limitante YA ganó en su
FR/FL gracias al `fb` del loop. Columna frontal del lado de la pared: FR si R, FL si L.
```python
fb_col   = "FR" if wall_side == "R" else "FL"
fr_at_wall = modified[wall_stop_idx][fb_col]      # FR/FL del piso limitante con (rl, fb) actual
excess     = fr_at_wall - LIMIT_fb_col            # cuánto ya supera el límite frontal
extra_needed   = max(0, (FS − TSW) − excess)
fb_applied     = min(fb + extra_needed, FB_MAX_BACK)
```
- **Caso 1** — el piso limitante es el más crítico en FR/FL (excess≈0) → extra completo.
- **Caso 2** — otro piso ya empujó `fb` más (piso limitante lleva ventaja) → extra reducido.
- **Caso 3** — sin violación FR/FL (fb=0), piso limitante ya sobre límite → extra = (FS−TSW) − excess.
- Solo se aplica cuando RL implica colisión (OR/OL en wall_stop > LIMIT).

### Cómo se aplican los desplazamientos en cada paso
```python
WR += rl;  FR += fb;  OR += rl
WL -= rl;  FL += fb;  OL -= rl
```

### Criterios de selección
1. **Criterio 1:** mínimo `total_off` (valores bajo su límite)
2. **Criterio 2 (desempate):** mínimo `|RL| + |FB|`

---

## Convención OR/OL — IMPORTANTE (no cambiar sin confirmar)
```
OR/OL son dimensiones que NO deben superar el límite máximo.
  fuera de límite = v > LIMIT   (la dimensión excede el máximo → requiere corte físico)
  dentro del límite = v ≤ LIMIT
  DIF = MAX(col) − LIMIT        (positivo = requiere corte, negativo = sin violación)
  OFF_COUNT = sum(v > lim)
  CUT = v − LIMIT               (cuánto hay que cortar, solo cuando v > lim)
```
⚠️ WR/WL/FR/FL usan el criterio OPUESTO: fuera de límite = v < LIMIT (clearance mínimo).
⚠️ Esta dirección (v > LIMIT) aplica en AMBOS casos (Caso 1 y Caso 2).
   La diferencia entre casos es solo el COLOR y si cuentan como OFF en el optimizador:
   - Caso 1: rojo claro (OR/OL cuentan como OFF completo)
   - Caso 2: naranja (OR/OL NO cuentan como OFF; se muestran columnas CUT OR/OL)

---

## Geometría física — los dos cajones

### El hueco (caja grande, fijo)
```
Ancho total  = SF1 + BKS + 2×RAIL + SF2  =  BS  (plano)  /  BSR  (obra)
Profundidad  = TS
Pared frontal → centro riel = TKSW (diseño) / FR·FL (campo, varía por nivel)
```

### El bloque cabina (caja chica, se posiciona)
```
Ancho        = BKS + 2×RAIL   (rieles + guías, tratado como un solo bloque)
Profundidad  = TL = TS − BC_CALC   (= CS + TKS + TSW)
```

### Sección transversal (vista superior)
```
PARED IZQ                                                    PARED DER
  │←── SF1 ──→│←─RAIL─│←────── BKS ──────→│─RAIL─→│←── SF2 ──→│
  │←─── WL ──→│←──────── BKS + 2×RAIL ───────────→│←─── WR ───→│
  │                      BLOQUE CABINA                            │
  │←───────────────────────── BS ────────────────────────────────→│
```

### OR / OL — apertura de la puerta de rellano (en cada piso)
```
  │←─ OL ─→│←──────── BT ────────→│←─ OR ─→│
             PUERTA DE RELLANO

  OR/OL se miden en la apertura donde va la puerta de rellano.
  Si OR o OL > LIMIT → la puerta no entra → hay que CORTAR físicamente ✂️
  BT = apertura de puerta (NO es el ancho de la cabina)
  CUT = v − LIMIT  (cuánto hay que cortar cuando v > LIMIT)
```

### Perfil longitudinal (vista lateral)
```
PARED FRONTAL                                          PARED FONDO
  │←── FR ──→● centro riel                                  │
  │           ├──────────── TL ────────────────┤←─BC_CALC─→│
  │           │        BLOQUE CABINA            │            │
  │←──────────────────────── TS ──────────────────────────→│

  FR/FL = distancia pared frontal → centro riel, medida en campo nivel a nivel
  LIMIT_FR = LIMIT_FL = TKSW − 150  (mínimo aceptable)
```

### Los 6 valores del survey
| Col | Mide | Fuera de límite |
|-----|------|-----------------|
| WR  | Espacio bloque → pared derecha | v < LIMIT (muy poco espacio) |
| WL  | Espacio bloque → pared izquierda | v < LIMIT (muy poco espacio) |
| FR  | Pared frontal → centro riel derecho | v < LIMIT (riel muy cerca de la pared) |
| FL  | Pared frontal → centro riel izquierdo | v < LIMIT (riel muy cerca de la pared) |
| OR  | Espacio derecho en apertura de puerta | v > LIMIT (hay que cortar) |
| OL  | Espacio izquierdo en apertura de puerta | v > LIMIT (hay que cortar) |

---

## Caso 1 vs Caso 2 — diferencias clave

| Aspecto | Caso 1 (WALL_LIMITING=True) | Caso 2 (WALL_LIMITING=False) |
|---|---|---|
| OR/OL en conteo OFF | Sí (v > lim) | **No** (se gestionan como restricción dura) |
| MAX_OFF_RL fórmula | max(DIF_WR, DIF_WL, max(0,DIF_OR), max(0,DIF_OL)) | max(DIF_WR, DIF_WL, max(0,DIF_OR), max(0,DIF_OL)) |
| Columnas optimizer | WR FR OR WL FL OL | WR FR WL FL |
| Color OR/OL en tabla | Naranja si v > lim | **Naranja si v > lim** (requiere corte) |
| Columnas extra | — | CUT OR = OR−LIMIT_OR, CUT OL = OL−LIMIT_OL |

---

## Colores en tablas (app y reporte)
- 🔴 Rojo oscuro `#c0392b`: valor mínimo fuera de límite (WR/WL/FR/FL)
- 🔴 Rojo claro `#f1948a`: fuera de límite (WR/WL/FR/FL, v < lim)
- 🟠 Naranja oscuro `#c0392b`: OR/OL — valor máximo requiere corte (v > lim)
- 🟠 Naranja `#e67e22`: OR/OL requieren corte (v > lim)
- 🟢 Verde `#d4efdf`: solución óptima en log

---

## DOS INFORMES (v46) ⚠️ importante

### Informe ADMIN — report.py :: generate_report() (COMPLETO, interno)
Se **genera y envía por correo automáticamente** al pulsar Calcular (adjunto al email).
NO se descarga en la app. Contiene todo el detalle técnico:
```
1. Parámetros entrada + 1.3 condiciones/configuración
2. Dimensiones cabina + diagrama perfil
3. Límites geométricos + diagrama transversal
4. Offsets
5. Matriz SURVEY original
6. Matriz ajustada + DIF por columna + 6.2 estado inicial
   + bloques 🤖 interpretación IA (parametros, estado_inicial, desplazamientos)
7. Optimización: params + diagramas RL/FB + LOG COMPLETO de pasos + soluciones
   + 🤖 interpretación (solucion_optima, evasion_pared)
8. DIAGRAMA DE POSICIONAMIENTO — planta por piso (SVG vía svglib)
9. BSR vs BS + 🤖 interpretación
10. Consideraciones finales (🤖 checklist)
```
- Bloques IA vía `_ia_block()`; SVG embebido vía `_svg_flowable()` (svglib.svg2rlg).
- Firma acepta `interpretation=` (dict admin de interpretation.py).

### Informe CLIENTE — user_report.py :: generate_user_report() (LIMPIO, descargable)
Botón "Generar informe del cliente" (Paso 5). Profesional, SIN lógica interna
(sin log, sin fórmulas, sin BSR/BS, sin parámetros crudos). Secciones:
```
Cabecera COPEX + datos proyecto/cliente/ingeniero/fecha
1. Resumen de la solución (IA)
2. Posicionamiento final: tarjetas RL/FB/valores-fuera + desplazamientos (IA)
3. Cortes necesarios (IA: qué cortar, cuánto, qué piso — o "ninguno")
4. Matriz de la solución por piso (celdas rojas donde requieren atención)
5. Diagramas de planta por piso (floor_plan_svg)
6. Implementación en obra (pasos IA) + 7. Verificación final (checklist IA)
```

### Regla importante
**Si cambias una fórmula en calculations.py → revisa report.py y, si aplica, diagrams.py.**

---

## diagrams.py — planta por piso (v39) ⚠️ SVG sin markers
`floor_plan_svg(params, limits, row, floor_idx, lim_map, ctrl_in_frame, ctrl_side, is_last)`
- Vista SUPERIOR (planta) esquemática, **una imagen por piso**, con la matriz solución.
- Cabina = caja rígida BKS+2·RAIL; se dibujan las 4 holguras (WL, WR, FL, FR) + apertura (OL/OR).
- **SVG sin `<marker>`/`<defs>`** (flechas como `<polygon>`) → compatible con Streamlit
  (`components.html`) Y con ReportLab (`svglib.svg2rlg`). NO usar markers.
- Color por estado `_state(value, lim, is_max)`:
  ```
  margin = (lim - value) if is_max else (value - lim)   # ⚠️ ojo: NO invertir
  margin < 0 → rojo (fuera) | < 10 → naranja (al límite) | else verde (OK)
  ```
  is_max=True para OR/OL (seguro = value ≤ lim); is_max=False para WR/WL/FR/FL (seguro = value ≥ lim).
- En app: `components.html(...)` (NO `st.markdown` — Streamlit elimina los `<svg>`).

---

## extractors/schindler.py — extract_from_pdf()

Usa **visitor_text de pypdf** para reconstruir texto con separación posicional.  
**NO usar:** pdfplumber (valores erróneos), pypdf layout mode (71s).

### _page_text_positional(page) — paso previo clave (v10)
```
- Recolecta (y, x, texto) de cada elemento via visitor_text callback
- Agrupa elementos por línea (Y ± 20 pts = misma línea)
- Dentro de cada línea, inserta espacio si gap horizontal > 50 pts
  (CHAR_W=8 pts/char → evita concatenar "SF1=51" con "1175" separado)
- Fallback a page.extract_text() si visitor no retorna datos
```
Esto resuelve: SF1=51 + anotación 1175 → "SF1=51 1175" (ya no "SF1=511175")
              TKS=30 + anotación 70 a distinto Y → líneas separadas (no "TKS=3070")

### VALID_RANGES importantes
- TKS: (5, 150) — umbral cabina→rellano, típico 20-80 mm (era (500,8000) → BUG)
- Truncación: intenta 4, 3, 2 dígitos si valor fuera de rango

### Pipeline de extracción (después de _page_text_positional)
```
Paso 1: CRLF → LF, unir dígito-\n-dígito  (fallback de seguridad)
Paso 2: separar parámetros pegados         (fix: TKSW=965TS=1750)
Paso 3: regex PARAM=VALUE                  (fix: BS=19981272 → truncar a BS=1998)
Paso 4: línea a línea:
  A) valor DESPUÉS del label  (PARAM=valor o PARAM valor)
  D) valor ANTES del label    (170BKF2 → BKF2=170)  ← Caso especial Schindler CAD
  B/C) label solo → buscar número en línea anterior/siguiente
```

---

## IA — interpretation.py + chat_agent.py (v26/v27/v30/v46)

**Modelo:** `claude-haiku-4-5` vía librería `anthropic`. Requiere `ANTHROPIC_API_KEY`.

### interpretation.py — dos generadores
- `generate_interpretation(calc_results, all_params)` → dict ADMIN (7 claves):
  parametros, estado_inicial, desplazamientos, solucion_optima, evasion_pared, bsr_vs_bs, consideraciones.
- `generate_user_interpretation(calc_results, all_params)` → dict CLIENTE (5 claves):
  resumen, desplazamientos, cortes, implementacion, verificacion. Orientado a IMPLEMENTACIÓN
  (qué desplazar, por qué, qué cortar), profesional, SIN fórmulas internas.
- Ambos retornan `_ok` (bool) y `_error`. Devuelven JSON (se extrae entre `{` y `}`).
- **`_ok=False` bloquea la generación de informes** (v38): el PDF requiere interpretación.
  Causa habitual del fallo en producción: falta `ANTHROPIC_API_KEY` en Streamlit Cloud.
- El user-payload calcula los cortes por piso (OR/OL − LIMIT > 0) y los pasa a la IA.

### chat_agent.py — asistente experto (sidebar desplegable)
- `get_chat_response(user_message, history, calc_results, all_params)`.
- System prompt = experto COPEX en instalación Schindler + **contexto del cálculo actual** (si existe).
- **Confidencialidad (v27):** NO revela fórmulas internas, algoritmos, lógica del optimizador,
  nombres de módulos/funciones ni flujo interno. Sí interpreta resultados y explica conceptos físicos.
- Historial en `session_state["chat_history"]` (máx 20 mensajes).

---

## email_notify.py — correo interno (v33/v34/v46)
`send_usage_notification(proyecto, ingeniero, all_params, analysis, opt_result, bs_result,
survey_df, pdf_bytes, pdf_name, admin_report)` — Gmail SMTP (`smtplib`, puerto 587 + starttls).
- Se dispara al **Calcular**. Envía a `NOTIFY_TO` un correo HTML con resumen técnico.
- **Adjuntos:** informe ADMIN (PDF completo), plano PDF del usuario, matriz survey (CSV).
- Requiere secrets `GMAIL_USER`, `GMAIL_APP_PASS` (App Password de Gmail), `NOTIFY_TO`.

---

## plumb.py — líneas de plomada (v40, PDF v57, nombres v58, encaje v61, eje-cero V4 v62)
Herramienta INDEPENDIENTE. `compute_plumb(inp)` + `plumb_svg(res)` + `plumb_table(res)`.
Entradas: BKS, RAIL, TKSW, LengthTemplate, SF1, SF2, BSR, BS (+ SG, TG, OMEGA_SIDE si BSR<BS).
**Vista SUPERIOR (planta), pared frontal como referencia:**
```
DBP  = BKS + RAIL           = distancia entre los plomos (separación lateral)
DBPW = TKSW − 150           = distancia del plomo a la pared frontal (profundidad)
RW   = DBPW − LengthTemplate = distancia del template a la pared frontal
P=(DBP/2, RW) = centro del template   C1=(0,DBPW), C2=(DBP,DBPW) = puntos de los plomos
d1,d2 = cuerdas diagonales del template a cada plomo (se miden en obra)
TKSW=pared frontal→centro riel · SG=centro contrapeso→pared omega · TG=grosor contrapeso
```
**6 líneas (claves internas V1..V6; nombres propios en `LINE_NAMES`, v58):**
```
V1=0  Plomo riel izq      V2=DBP  Plomo riel der
V3=−(SF1+RAIL/2) Pared teórica izq     V5=DBP+(SF2+RAIL/2) Pared teórica der
V4=V3−(BSR−BS)/2 Pared REAL izq        V6=V5+(BSR−BS)/2   Pared REAL der   ⚠️ FIJAS (shaft real)
```
**⚠️ EJE CERO = pared REAL izquierda (V4, v62):** al final se resta `x_v4` a todas las X →
V4=0 y el shaft real va de 0 a BSR. Referencia física fija en obra. Las X pueden ser negativas
(pared teórica por fuera de la real = sacrificio lado Z).
**Encaje del conjunto (v61) — ⚠️ modelo corregido:**
- Las paredes REALES **V4/V6 son FIJAS** (definen el shaft real, separadas BSR). NUNCA se mueven.
- Se mueve el **CONJUNTO rígido** = plomos V1/V2 + paredes teóricas V3/V5 + template P/C1/C2,
  conservando sus distancias internas (un solo desplazamiento `desp` aplicado a todos).
- **BSR > BS:** el conjunto se **centra** (holgura `(BSR−BS)/2` a cada lado) → `desp=0`, `{"centrado":True}`.
- **BSR < BS:** el conjunto **se acerca al lado Z** (Z opuesto al Omega: Omega R→Z izq, Omega L→Z der):
  `LIMIT_ZB=SF1×0.3` (Z izq) | `SF2×0.3` (Z der); `LIMIT_OB=(SG−TG/2)×0.3`; `dif=BS−BSR`.
  `z_sac=min(dif,LIMIT_ZB)` (Z primero), `omega_sac=max(0,dif−LIMIT_ZB)` (resto→Omega).
  Si `omega_sac>LIMIT_OB` → no cabe (`fuera_rango`). La pared teórica del lado Z queda `z_sac` por
  fuera de su pared real; `desp` = lo que haga falta para lograrlo.
- **BS se lee del plano** (no se deriva de BKS+2·RAIL+SF1+SF2, aunque esa igualdad se cumple).
- (histórico: hasta v60 movía V4/V6 con búsqueda lineal — ERA INCORRECTO, deformaba el shaft.)

**Integración con el survey (v63):** `compute_plumb(inp, survey_disp={"rl":..,"fb":..})`.
Cuando `survey_disp` viene del survey, NO usa Z/Omega: el conjunto se desplaza `−rl` (lateral,
rl<0=derecha) y la profundidad `DBPW = TKSW−150 + fb` (fb>0 aleja de la pared frontal). El survey
agrega input **LengthTemplate** (en `USER_ONLY`), tras calcular muestra el "plomado definitivo"
(`app.py`, guardado en `calc_results["plumb"]`) y lo embebe en ambos informes (`report.py` §12,
`user_report.py` §9) vía `_svg_flowable(plumb_svg(...))`. La pestaña de plomado manual sigue usando
`compute_plumb(inp)` (sin survey_disp) → modo independiente intacto.

**Verificación en campo (v64):** `res["verif"]` = distancias plomo↔pared real (pared real izq→plomo izq
= X final de V1; plomo der→pared real der = V6−V2). `plumb_checks(res)` da la tabla; `plumb_svg` dibuja
las cotas abajo. Se muestran en pestaña manual, survey y ambos informes. (di + DBP + dd = BSR.)
- `plumb_ui`: carga PDF autocompleta 📄 BKS/TKSW/SF1/SF2/BS/SG/TG; ✏️ RAIL/LengthTemplate/BSR/Omega manuales.
  Inputs inician en 0 (sin residuales, v59).

---

## rail_cut.py — corte de rieles (v52)
Herramienta INDEPENDIENTE. Lee **LFKK, LFGK** del PDF (`extract_lf`, reusa `_page_text_positional`).
Pregunta nº de elevadores y el caso:
- **Caso 1** (riel a cortar = primero instalado, abajo): `A = n2500·2500 + n5000·5000` (mismo para
  todos); por elevador `L` → `RC=L+LFKK`, `RCW=L+LFGK`, `CutRC=RC−A`, `CutRCW=RCW−A`.
- **Caso 2** (último instalado, arriba): usuario llena matriz RZ/RO/RF/RB por elevador. Sub-caso:
  penúltimo ENCIMA del FFL → `CutR* = LF − R*`; DEBAJO → `CutR* = LF + R*` (LFKK para RZ/RO, LFGK para RF/RB).
- Salida: matriz columnas=elevadores, filas=Cut*.

## buffer_cut.py / buffer_cut_ui.py — corte de buffers (v96)
Herramienta INDEPENDIENTE (pestaña 🛡 Corte de buffers). Sencilla. Del plano lee **HKP** (`extract_hkp`
= **1er** valor de la fila `HKP/HGP`; el 2º es HGP) = distancia sticker de cabina ↔ buffer de cabina
sirviendo el 1er nivel. El usuario indica **cuántos buffers** hay y el **HKPR** real de cada uno.
`compute_buffer_cut(hkp, hkpr_list)` → por buffer **CutBuffer = HKP − HKPR** (mm); marca `warn` si <0
(el real supera al plano → nada que cortar, revisar en obra). Solo pestaña (no va a los informes).

---

## maps.py — enlaces a Google Maps (v98)
Toda ubicación mostrada enlaza a Google Maps con la **URL de búsqueda** (`.../maps/search/?api=1&query=`,
sin API key ni coordenadas). Helpers: `maps_url(loc)`, `maps_link_md(loc,label)` (Streamlit markdown),
`maps_link_html(loc,label,color)` (cabeceras unsafe_allow_html / email / Telegram). Vacío → "". Aplicado en:
detalle de proyecto (cabecera HTML), 📋 Mis proyectos (campo), PDF del Pre-Start (hipervínculo), input de
Location del Pre-Start (preview), y la notificación de asignación (email/Telegram, ambos HTML).

## prestart.py / prestart_pdf.py / prestart_ui.py — Daily Pre-Start (v97)
Pestaña **🦺 Pre-Start diario** (herramienta común, todos los roles; el selector de proyecto se adapta:
campo=asignados, admin=grupo, propietario=todos). Digitaliza el formato "Daily Pre-Start" de CI Liftworx:
encabezado (Date/Time/Location/Facilitated by), **1** Planned work (4 checks YES/NO + notas SWMS),
**2** near miss/hazard (YES/NO + desc), **3** Shaft Protection (3 checks YES/NO/N-A), **4** General Notes,
**5** Attendees (Print Name + Initial). Checks en `prestart.CHECKS_S1`/`CHECKS_S3`.
- `submit(data)`: genera el PDF (`prestart_pdf`, **marca = nombre del grupo**) → lo sube a la carpeta del
  proyecto en Drive (`drive_store.upload` + `projects.add_document` tipo `prestart`, best-effort) → registra
  fila en la hoja **`PreStarts`** → si `near_miss==YES` abre alarma (`alerts.report_problem`). Devuelve pdf
  bytes para descargar. Nombre de archivo: **`ddmmyyyy AB CD.pdf`** (fecha + iniciales de asistentes,
  `filename_for`). Lecturas cacheadas (ttl 30). El historial de pre-starts se lista por proyecto.

## belting.py / belting_ui.py — belting (v86)
Herramienta INDEPENDIENTE (pestaña 🎗 Belting). Altura a la que dejar la cabina bajo el FFL del piso más
alto para instalar los belts. **DSTS = HGPR − HGP − HQ/1000** (todo mm; HQ/1000 = elongación del belt;
DSTS>0 = baja la cabina). **Por elevador** (HGPR por elevador). `compute_belting` + `belting_svg` (diagrama).
- Del plano (`extract_belting`, autocompleta): **HQ** (regex `HQ=\s*(\d+)`) y **HGP** (2º valor de la fila
  `HKP/HGP [mm]`; el 1º es HKP; regex de valor con tolerancia tipo `85 -20/0`). Validado: HQ 14045/13250, HGP 85.
- HGPR: manual, uno por elevador.

## schedule.py — gestión de proyecto: cronograma + curva S (v51)
En el survey, al Calcular. `build_schedule(ns, start_date, flags, custom_rows)` + `schedule_svg` + `schedule_table`.
- Actividades estándar de instalación; duraciones **escalan con NS**; peso con distribución en "S".
- `detect_flags()`: agrega "cortes" si OR/OL de la solución > límite, y "ajuste shaft" si BSR<BS.
- Curva S = % acumulado planificado por día (progreso lineal por actividad). Editable (fecha inicio + tabla).
- Se incluye en app + informe cliente + informe admin. SVG sin markers (svglib-compat).
- **Curva S REAL vs planificada (v70, fix v76):** `real_scurve(sched, avances, upto_day, windows)` =
  avance GANADO `Σ peso·(avance/100)` acumulado, **cortado en HOY**, que **llega al avance real total
  en HOY**. Reparte el ganado de cada actividad sobre su ventana REAL `[inicio_real, fin_real]` (de las
  fechas del campo, `windows`) o sobre `[inicio, hoy]` si no hay fechas. ⚠️ v76 corrigió el bug donde
  repartía sobre la ventana PLANIFICADA → descontaba al futuro el trabajo hecho antes de su fecha (o con
  el proyecto recién creado) y la curva daba ~0 aunque el avance fuera alto. `schedule_svg(sched,
  real_curve, today_day)` superpone la real (verde) sobre la planificada (naranja) + línea "HOY".
  `projects.project_schedule(pid)` reconstruye el plan de las actividades guardadas. Se ve en el
  detalle del proyecto del admin.
- **Real cortada en HOY (v71):** `real_scurve(..., upto_day)` no se extiende a la fecha final.
  Barras del Gantt se "llenan" según %avance (`schedule_svg(..., avances=)`, verde al 100%).
- **Proyección avance-vs-fecha (v72):** `schedule_projection(sched, avances, today_day)` (earned value):
  EV=Σpeso·avance/100, PV=curva S hoy, desvío=EV−PV, dias_gap=hoy−día(plan=EV) (brecha horizontal),
  SPI=EV/PV, fin proyectado=inicio+total/SPI. Tarjetas en el detalle del admin.

---

## projects.py / projects_ui.py — gestión de proyectos (v65)
**Proyecto = 1 elevador.** Se inicia con el survey (botón **💾 Guardar como proyecto** en app.py,
Paso 7, solo administrador/propietario). Persistencia en Google Sheets (misma hoja del fichaje):
- **Proyectos**: ID(PRJ-####)·Grupo·Nombre·Cliente·Ubicacion·Modelo·NS·Estado·EstadoManual·
  FechaInicio·FechaFinEst·Ingeniero·CampoAsignados(`;`)·Avance·AgrupacionID·PesoEnAgrupacion·
  **ParamsJSON·MatrizJSON·InterpJSON** (survey completo re-abrible; los derivados se recalculan)·CreadoPor·Creado.
- **Actividades**: ProyectoID·Orden·Nombre·DuracionDias·Peso·**Avance**·FechaInicioReal·FechaFinReal·Nota.
- **Agrupaciones** (AGR-####): varios proyectos con peso; `grouping_progress` = Σ(peso·avance)/Σpeso.
- **Avance proyecto** = `compute_avance` = Σ(peso_act·avance_act)/Σpeso (**escala-invariante** → agregar/
  eliminar actividades recalcula el % solo). **Estado**: auto (0=Planificado,1-99=En progreso,100=Completado)
  + override manual (En pausa/Cancelado) vía `derive_estado`.
- **Admin agrega/elimina actividades (v82):** `add_activity(pid,nombre,dur,peso)` / `delete_activity(pid,orden)`
  → `_recompute_project_avance` (compute_avance sobre las actividades actuales) + update_project. La curva S
  se reconstruye sola (project_schedule).
- **Tabla de actividades EDITABLE (v83):** `st.data_editor` (num_rows fixed) — editar Nombre/Días/Peso y
  reordenar (columna Orden editable); Avance de solo lectura (campo). `save_activities(pid, edits)` escribe
  todo en 1 `batch_update` (localiza cada fila por su Orden original `orden0`) + recomputa. Reordenar =
  cambiar el número de Orden (list_activities ordena por Orden).
- **Admin** (🛠 Mi grupo): **centro de control** (v94) — `auth_ui.render_group_panel` llama
  `projects_ui.render_group_header` (banda de marca del grupo + fila de KPIs: activos, avance promedio,
  **en riesgo** por proyección SPI, alarmas abiertas, horas) y una nav única de 3 (📊 Proyectos · 🗂
  Agrupaciones · 🔧 Usuarios de campo). Proyectos = **cartera de tarjetas** (`_portfolio_html`: punto de
  estado, nombre/cliente, **ubicación enlazada a Maps**, píldora de estado, barra de avance, horas, badge de
  alarmas, y **marca de retraso** —borde rojo + badge ⏰ N d, v99—) + selector "Abrir proyecto" →
  `_detalle_proyecto` (con cabecera de estado). Helpers: `_kpis`, `_delays` (proyección SPI: {pid: días de
  retraso}, reusado por el KPI "en riesgo" y las tarjetas), `_estado_colors`, `_ESTADO_COLOR`.
- **Propietario** (👑 Administración → 📁 Proyectos): tabla de TODOS los proyectos con **Ubicación** + columna
  🗺 (`st.column_config.LinkColumn` a Maps) + columna **⏰ Retraso** (días, v99). `render_owner_projects`.
- **Instrucciones + Inducciones (v100):** columnas `Instrucciones` e `InduccionLinks` en Proyectos (se migran
  solas vía `get_sheet`). Se llenan al crear (survey → Guardar como proyecto) y se editan en el detalle.
  `projects_ui._induccion_section` las muestra (links clickeables) en el detalle (admin, con botón "reenviar")
  y en 📋 Mis proyectos (campo, solo lectura). Los links de inducción se envían por Telegram/email a los
  usuarios de campo **al asignarlos** (`notify.notify_assignment` los incluye) y con `notify.notify_induction`
  (reenvío). `projects.parse_links` (uno por línea).
- **Campo** (📋 Mis proyectos): ve asignados; actualiza el avance en UNA tabla editable (`save_field_progress`, batch + fechas reales automaticas, v162); sub-pestañas 🏗 Avance/🚨 Avisos/💰 Recibos/📎 Archivos. `render_field_projects`.
- **Propietario** (👑 Administración → 📁 Proyectos): ve TODOS los proyectos de todos los grupos
  (`render_owner_projects`, `list_projects()` sin filtro). `_detalle_proyecto` toma el grupo del propio proyecto. (v73)
- **Horas**: del fichaje por nombre de proyecto (`project_hours`, `project_hours_bulk`=1 lectura).
- Reusa `timeclock._get_worksheet`; RAW + `numericise_ignore`; navegación con radio.
- ⚠️ **Lecturas CACHEADAS (v69):** `_records(title)`/`_fichaje_records()` con `@st.cache_data(ttl=30)`;
  las escrituras llaman `_invalidate()`. Sin esto, cada rerun/slider re-leía las hojas → APIError 429
  (rate limit). Las rutas de ESCRITURA (`_find_row`, `_next_project_id`, borrado) leen FRESCO.

## ⚙️ Reducción de llamadas a Google Sheets (v92)
Auditoría de call-sites → 3 optimizaciones sin cambiar funcionalidad:
- **Handle de worksheet cacheado** (`timeclock.get_sheet(title, headers)`, `@st.cache_resource`): crea la
  hoja y asegura/migra la cabecera UNA vez por proceso. Antes cada `_get_ws`/`_ws`/`_get_login_ws` hacía
  `ss.worksheet(title)` (metadata) + `row_values(1)` en CADA lectura (2 llamadas extra por lectura).
  Reconectados: auth (`_get_login_ws`,`_get_groups_ws`), projects (`_get_ws`), alerts (`_ws`),
  manuals (`_index_ws`), timeclock (`_get_users_ws`). El sheet1 del fichaje sigue con `_cached_ws`.
- **auth `list_users`/`get_user` cacheados** (`_login_records_cached`, ttl=30): se llamaban en CADA rerun
  de los paneles (dropdown de asignar campo, contacto) → 1 lectura por slider. Se invalidan al escribir
  (`_invalidate_login` en add/set_group/set_password/set_role/set_active/delete_user/set_contact). Las
  rutas de SESIÓN ("primero gana": start_session/heartbeat/end_session/verify_login) leen FRESCO.
- **ttl 20→30 s** en projects/alerts (menos re-lecturas en uso sostenido; escrituras invalidan al instante).
Efecto: render frío de un panel ≈19→≈7 llamadas; uso sostenido ≈57→≈21 lecturas/min (bajo el límite ~60/min).
El heartbeat de sesión ya estaba throttled a 50 s (app.py `_hb_last`).
- Fichaje con dropdown de proyectos asignados (v67). Curva S real vs planificada en el detalle (v70).

## drive_store.py — documentos de proyecto en Google Drive (v74)
OAuth de USUARIO (no service account) con scope **`drive.file`** (solo toca archivos que la app crea →
sin verificación de Google). Secrets `[gdrive]` client_id/client_secret/refresh_token (opc root_folder_id).
Usa **google-auth + requests** (sin deps nuevas). Estructura: `COPEX Proyectos / <PRJ-id> / archivos`.
- `upload(pid, filename, bytes, mime)` (multipart) · `download(id)` (cacheado 5min) · `delete(id)` ·
  `project_folder(pid)` (cacheado). Descargas pasan por la app (archivos privados en el Drive del dueño).
- Metadatos en hoja **Documentos** (`projects.list_documents/add_document/delete_document_record`):
  ProyectoID·Nombre·Tipo·DriveID·SubidoPor·Fecha. Tipos: plano/informe_cliente/informe_admin/matriz_survey/
  foto/certificado/otro.
- **Permisos** (`_documentos_section`, lee session_state.auth): admin/propietario = todo (subir/ver/borrar);
  **campo** = solo sube **fotos** y solo ve plano/informe_cliente/matriz_survey/foto. Aislamiento por grupo
  (solo acceden a proyectos de su grupo).
- **Auto-archivo** al "Guardar como proyecto" (app.py): plano (pdf_bytes) + matriz_survey (CSV) + informe_cliente (PDF).
- Token OAuth: script `C:\Users\diego\get_drive_token.py` (una vez). Consent screen en Producción (no expira).

---

## manuals.py — banco de manuales para el agente IA (v90/v91)
Fragmentos (chunks) de cada manual como `{nombre, chunks:[{manual,seccion,page,text}]}` (.json.gz).
`_index()` (cache_resource) fusiona **dos orígenes** y arma **BM25 en Python puro** (sin deps ni APIs):
1. **Pre-cargados** en el repo `survey_app/manuals/*.json.gz` (KONE Monospace 722 frags, S5500 358).
2. **Subidos por el propietario** (v91, self-service): PDF/ZIP → `_chunks_from_upload` (pypdf, ~180
   palabras/chunk, sección por heurística de título en mayúsculas, página) → `.json.gz` a **Drive**
   (`drive_store.folder("COPEX Manuales")` + `upload_to`), registrado en la hoja **`Manuales`**
   (ID,Nombre,DriveID,NumFrags,Fecha,SubidoPor). `_drive_chunks()` los descarga y los mete al índice.
`search(query,k)` / `context_for(query)` → fragmentos relevantes. Gestión: `add_manual`/`delete_manual`/
`list_uploaded`/`repo_manual_names`; `_refresh()` invalida `_drive_records` + `_index`. Panel propietario
**📚 Manuales** (`auth_ui._owner_manuales`): lista pre-cargados (solo lectura) + subidos (tabla, subir, quitar).
`chat_agent.get_chat_response` recupera los fragmentos de la pregunta, los agrega al system prompt y el
agente responde citando **manual · sección · página** (sin copiar páginas enteras).

## admin_digest.py + agente admin con radar del grupo (v101)
El **agente del administrador** vigila el grupo (empresa cliente) al que pertenece y da un resumen de
pendientes al ingresar. `core/admin_digest.py` (determinístico, todo sobre lecturas cacheadas):
- `group_digest(grupo)` → hechos pendientes: retrasos (SPI), alarmas abiertas, **vencidos/por vencer** (≤7 d
  por FechaFinEst), **near miss** de pre-starts ≤7 d, **campo sin contacto**, **sin asignar**, panorama.
- `digest_text(d)` (hechos en texto, fallback sin IA) · `group_snapshot_text(grupo)` (portafolio compacto en vivo).
`chat_agent.admin_briefing(grupo)` redacta el resumen con IA sobre los hechos (fallback = `digest_text`).
`get_chat_response(..., grupo)` inyecta `group_snapshot_text` al system del admin → responde preguntas del
portafolio, recomienda acciones, recuerda vencimientos y redacta mensajes (persona admin ampliada, "usa SOLO
los datos provistos, no inventes"). UI: `projects_ui.render_group_header` → `_resumen_del_dia` (expander
"🔔 Resumen del día": chips de pendientes + briefing IA cacheado por sesión en `st.session_state[_brief_<grupo>]`
+ botón actualizar). Solo el rol administrador (el propietario no tiene un único grupo).

## Agente separado por rol (v91)
`chat_agent._PERSONA` → persona según el rol de quien pregunta: **campo** (foco en ejecución en obra,
manuales, uso de la app en terreno: avance/alarmas/fichaje/documentos) vs **administrador/propietario**
(foco en gestión de proyectos: cronograma, curva S, EVM/SPI, actividades, asignaciones, interpretación).
`get_chat_response(..., rol=...)`; `app.py` pasa `rol=_ROL` y renombra el asistente ("de campo"/"de gestión").
Conocimiento base y regla de **confidencialidad** son comunes a ambos.

## alerts.py — alarmas/avisos por proyecto (v88)
Hoja **Alarmas** (`ID·ProyectoID·Grupo·Origen·Tipo·Mensaje·CreadoPor·Fecha·Estado·ResueltoPor·FechaResuelta`).
Dos flujos:
- **problema (campo→admin):** `report_problem` → alarma abierta + Telegram/email a admins del grupo + propietarios
  (`_admins_and_owners`). El campo lo reporta en 📋 Mis proyectos.
- **cambio (admin→campo):** `notify_change` (auto al guardar datos/actividades/agregar/eliminar en projects_ui) →
  aviso in-app + Telegram/email al campo asignado.
Estado abierta/resuelta; `resolve_alert` (batch). UI `projects_ui._alerts_section` (detalle admin + Mis proyectos
campo, resolver/apagar). Badge 🔴 N en las listas (`open_counts_all`, cacheado). Reusa notify.py.

## notify.py — notificaciones email + Telegram (v77)
Avisa a un usuario de campo al **asignarlo** a un proyecto (crear/editar), con los datos del proyecto.
- **Email**: Gmail SMTP (reusa `GMAIL_USER`/`GMAIL_APP_PASS`). **Telegram**: Bot API con
  `TELEGRAM_BOT_TOKEN` + `TELEGRAM_BOT_USERNAME` (secrets). Solo `requests`+`smtplib` (sin deps nuevas).
- Contacto por usuario en hoja Login: cols **Email, TelegramChatID** (`auth.get_user/set_contact`).
- `notify_assignment(usuario, prj)` → `notify_user` → envía por los canales configurados y con dato.
  Degrada con gracia (sin secrets/sin contacto → no envía, no rompe).
- **Vinculación Telegram** (sin webhook): el usuario abre `t.me/<bot>?start=<code>` (code=usuario saneado)
  → pulsa Start → la app llama `getUpdates` y matchea el code → guarda el chat_id (`telegram_find_chat_by_code`).
- **Contacto OBLIGATORIO para campo + solo el ADMIN lo edita (v79):** email+Telegram son requeridos para
  usuarios de campo. Email obligatorio al crear. El admin/propietario gestiona email y **vincula el Telegram**
  del usuario (tras que el usuario pulse Start) en `auth_ui._field_contact_ui` (en 🛠 Mi grupo → Usuarios y
  👑 Administración → Usuarios). **Bloqueo duro** en app.py: un campo sin ambos NO puede usar la app (pantalla
  de bloqueo con el link de Start; `_contact_ok` cachea). No hay self-service para el campo.
- Disparadores: `projects_ui._detalle_proyecto` (nuevos asignados al editar) y `app.py` (al crear proyecto).

## timeclock.py — fichaje (v41-v45; por login v54)
Google Sheets (cuenta de servicio). Hoja principal `sheet1`:
Nombre|PIN|Proyecto|Ubicacion|Clock In|Clock Out|Horas|Estado|**Grupo**.
- v54: **sin usuario+PIN** — usa la identidad del login (`session_state.auth`) + su Grupo.
  `clock_in(nombre, proyecto, ubicacion, grupo)` / `clock_out(nombre, grupo, nota)`.
  Empareja sesión abierta por Nombre+Grupo. (La antigua hoja `Usuarios`/PIN quedó obsoleta.)
- ⚠️ Textos como RAW + `get_all_records(numericise_ignore=['all'])` (conserva ceros).
- ⚠️ Conexión cacheada (`@st.cache_resource`); `is_configured()` solo revisa secrets (no API).
- Migración: `_cached_ws` agrega la columna Grupo al final si falta (resize + update_cell).

---

## auth.py / auth_ui.py — login, roles y grupos multi-empresa (v53/v54)
Login con **usuario+contraseña**, contraseñas **PBKDF2-SHA256** (nunca texto plano). Google Sheets:
- Hoja `Login`: Usuario|Password|Rol|Nombre|Activo|Grupo|**SessionToken|SessionTime** (cols nuevas al final = migración segura, `_get_login_ws` agrega faltantes).
- Hoja `Grupos`: Grupo|Descripcion|Activo.
- **Roles:** `propietario` (ve TODO, gestiona grupos+usuarios), `administrador` (solo su grupo:
  proyectos [vacío] + usuarios de campo), `campo` (4 secciones operativas, SIN descargar informes).
- **Multi-tenant:** grupos AISLADOS (cada empresa cliente). Admin/campo pertenecen a UN grupo;
  propietario global (sin grupo). Propietario crea grupos + admins; admin crea sus usuarios de campo.
- **Bootstrap:** si la hoja Login está VACÍA → formulario "crear propietario" (una sola vez).
  ⚠️ No vaciar la hoja Login (reabriría el bootstrap).
- `render_login()` (con **logo COPEX** = static/icon-512.png) devuelve True si hay sesión; si no, st.stop.
- Gate en app.py: `if not render_login(): st.stop()`. `_ROL`, `_GRUPO` de `session_state.auth`.
- Sesión en `session_state` (recargar página = re-login; sin cookies por ahora).
- **Sesión ÚNICA por cuenta (v75, licencias, "primero gana"):** `start_session` guarda un token +
  timestamp; un 2do login se BLOQUEA mientras la sesión activa siga viva (`_session_active`:
  token no vacío y heartbeat < `SESSION_TIMEOUT`=180s). `heartbeat(usuario, token)` (throttled 50s en
  app.py) marca vida; si el token fue desplazado → expulsión. `end_session` libera al salir. Botón
  "🔓 cerrar la otra sesión e iniciar aquí" (force) para recuperación legítima tras un refresh.
  Un usuario solo NUNCA es expulsado (no hay competidor); solo se expulsan cuentas compartidas.
- ⚠️ Paneles owner/admin usan sub-navegación con **radio** (NO st.tabs anidado → causaba mezcla).

---

## Móvil / PWA (Fase 1) + App Android Capacitor
**PWA (v47-v50):** CSS responsive (columnas se apilan en móvil), banner con `clamp()`,
manifest + íconos COPEX (`static/`, `enableStaticServing=true`), favicon COPEX vía `page_icon`
(imagen PIL). ⚠️ En Streamlit Cloud el ícono de app *instalada* es limitado (no controlamos el
`<head>` del servidor) → la app nativa real es el camino fiable.
**App Android (`C:\Users\diego\copex_mobile`):** Capacitor (Node + JDK 21 + Android SDK API 36).
`capacitor.config.json` con `server.url` = la URL de Streamlit (WebView que carga la web).
Ícono/splash COPEX vía `@capacitor/assets`. Build: `gradlew assembleDebug` → APK en
`android/app/build/outputs/apk/debug/`. Solo prueba local (sin publicar en tiendas).

---

## SECRETS requeridos (Streamlit Cloud → Settings → Secrets)
```toml
ANTHROPIC_API_KEY = "sk-ant-..."          # IA: interpretaciones + chat
GMAIL_USER        = "diegoaco93@gmail.com"
GMAIL_APP_PASS    = "..."                  # App Password de Gmail (no la contraseña normal)
NOTIFY_TO         = "diegoaco93@gmail.com"
TIMECLOCK_SHEET_ID = "..."                 # id de la hoja de fichajes
[gcp_service_account]                       # JSON completo de la cuenta de servicio
type = "service_account"
... (todos los campos del JSON) ...
```
Local: mismos valores en `survey_app/.streamlit/secrets.toml` (gitignored).
⚠️ Nunca commitear secrets. GitHub bloquea el push si detecta la API key (push protection).

---

## rails.py — catálogo de rieles + autocompletar RAIL (v84)
Hoja **Rieles** (`Referencia | AnchoDiente | AlturaDiente`), gestionada por el **propietario**
(👑 Administración → 🚆 Rieles: `auth_ui._owner_rieles`). `get_rail(ref)` → {ancho,altura} (cacheado).
`schindler.extract_car_guide_rail(pdf)` lee el código del **CAR GUIDE RAIL** del plano (misma fila que la
etiqueta en la extracción posicional; excluye COUNTERWEIGHT; regex `T\d{2,3}-\d/[A-Z]` tipo `T75-3/B`).
Al cargar el plano en el survey (app.py), autocompleta **RAIL = AlturaDiente** (altura del diente desde la
espalda) del catálogo; si el código no está o no se detecta → aviso + entrada manual. **RAIL = AlturaDiente**
(NO el ancho); AnchoDiente se guarda como dato secundario.

## Planificación: la celda es un BOTÓN nativo que abre el proyecto (v169)
El enfoque de v168 (celda = `<a href="?abrir_prj=…">`) tenía el riesgo de recargar la página. El usuario
pidió el plan B: **la celda como botón nativo**, que navega en la MISMA sesión, sin recarga ni riesgo de
deslogueo. Se revirtió v168 (handler de query param en app.py + el `clicable`/`<a>` de `_grid_html`).
### `roster_ui._tablero_editable(grupo, lunes, staff, datos, tidx)` (board del admin)
- El board del admin pasa de HTML a **botones `st.button`**: nombre + una celda por día. Cada celda no
  vacía es un botón; **navega solo si su trabajo enlaza a un proyecto** (`_prjsel_pending` +
  `_gruposec_pending` + rerun, en sesión). La nota (vehículo/equipo) va como `caption` bajo el botón.
- **Color por celda**: se inyecta `<style>.st-key-<key> button{background:…}</style>`. Streamlit (≥1.39)
  pone la clase `st-key-<key>` en el contenedor de cada widget con `key`. ⚠️ **Verificado EN VIVO** antes
  de construir (mini-app + inspección del DOM): `.st-key-celda_0 button` sale `background rgb(46,109,164)`.
  Por eso `requirements.txt` sube a `streamlit>=1.39`.
- El board del **campo** (`render_board_readonly`) sigue siendo el HTML de `_grid_html` (solo lectura, sin
  botones) — `_grid_html` volvió a su forma anterior a v168.
### ⚠️ Contra aceptada por el usuario
Con `st.columns` (nombre + 5 días) el board pierde el scroll horizontal del HTML y en móvil queda más
apretado. El usuario lo aceptó a cambio de que el clic sea 100% fiable en la sesión.
### Verificación
Mecanismo `st-key` probado en vivo (botón coloreado, clase presente). Modelo de la rejilla: 2 celdas no
vacías → 2 reglas CSS, 1 navegable (solo la enlazada a PRJ). v168 sin restos (`abrir_prj`/`clicable`),
plumbing en sesión (`_prjsel_pending`+`_gruposec_pending`), `_tablero_editable` 0 nombres libres, compila.

## Planificación: ir al proyecto desde LA CELDA del tablero (v168 — ⚠️ REEMPLAZADO por botones en v169)
El usuario rechazó los botones de v167: "quiero que sea desde la celda de la propia tabla". Se
REVIRTIÓ `_ir_a_proyecto` (los botones) y ahora **la celda misma es clicable**.
### ⚠️ El board es HTML, no un `st.dataframe` (no hay selección de celda)
El tablero se dibuja con `_grid_html` (celdas coloreadas por valor; por eso nunca fue un dataframe, y
`st.dataframe` solo selecciona filas/columnas, no celdas). Para que la CELDA navegue sin salir de
Streamlit, la celda enlazada a un proyecto se envuelve en **`<a href="?abrir_prj=PRJ-…">`** (query param).
- **`_grid_html(..., clicable=False)`**: en `clicable=True` (solo la Planificación del admin), la celda
  cuyo trabajo enlaza a un PRJ es un enlace con un hint "🔗 abrir". El board del campo
  (`render_board_readonly`) queda `clicable=False` (sin enlaces).
- **`app.py`** detecta `?abrir_prj=` ANTES del nav: fija `_prjsel_pending` (v126) + `main_nav = 🛠 Mi
  grupo` + `_gruposec_pending = 📊 Proyectos` (plomería de v167, que SÍ se conserva) + limpia el query
  param + rerun → abre el detalle del proyecto.
### ⚠️ Riesgo de deslogueo, mitigado
Un `<a href>` puede recargar la página; una recarga reinicia session_state. Pero el **login persiste por
cookie** (`auth_ui` restaura con `session_cookie.load()` al cargar), y el handler fija las claves aunque
la sesión venga fresca, así que la navegación funciona en recarga suave o dura. **Pendiente de validar
en el Cloud**: confirmar que el clic navega sin pedir login de nuevo; si la recarga molesta, el plan B
es un grid de `st.button` coloreados por `st-key-<key>` (misma sesión, sin recarga).
### Verificación
`_grid_html(clicable=True)` sobre datos sintéticos: exactamente 1 enlace `?abrir_prj=PRJ-0001` para la
celda enlazada; OFF/vacía no generan enlace; `clicable=False` (campo) sin enlaces. Handler lee
`abrir_prj` antes del nav; `_gruposec_pending` se lee antes del radio `grupo_sec`; `_prjsel_pending`
antes de `adminproj_sel`. Revert de `_ir_a_proyecto` sin referencias colgantes. Compila + import.

## Planificación: ir al proyecto desde el tablero (v167 — ⚠️ REVERTIDO en v168, ver arriba)
Peticion del usuario: "lo mismo con la tabla de planificacion; quiero poder ir al proyecto seleccionando
desde ahi". El board del roster es **HTML** (celdas coloreadas — por eso no es `st.dataframe`), asi que
no se puede hacer la celda clicable como en Archivos (v166); la adaptacion es un **botón por proyecto**.
### `roster_ui._ir_a_proyecto(grupo, staff, tidx, datos)` (bajo la rejilla, en 📅 Planificación)
- Recolecta los proyectos DISTINTOS enlazados en la semana visible (`R.proyecto_de` de cada celda;
  ignora estados OFF/Leave y trabajos sin enlace, dedupe). Solo ofrece los **navegables** (existen y no
  archivados, via `list_projects`).
- Un botón por proyecto → abre su detalle en **📊 Proyectos** con un clic, usando el patron de navegacion
  existente: `_prjsel_pending = pid` (v126, lo lee `_panel_proyectos` antes del selectbox `adminproj_sel`)
  + **`_gruposec_pending = "📊 Proyectos"`** (NUEVO) + rerun.
### ⚠️ Plomeria: cambiar de seccion del grupo necesita un pending (regla v111)
El radio `grupo_sec` (📊 Proyectos · 🗂 Agrupaciones · 📅 Planificación · …) se instancia en
`render_group_panel` ANTES de que corra `render_planificacion`, asi que no se puede escribir su clave
despues (StreamlitAPIException). Se añadio `_gruposec_pending`, que se aplica ANTES del radio — igual que
`main_nav` con `_nav_pending` en app.py.
### Verificacion
Recoleccion probada (funciones REALES `R.celda`/`R.proyecto_de` + datos sinteticos): distintos
`['PRJ-0001','PRJ-0003']`, sin duplicar, sin OFF ni trabajos sin enlace. `_gruposec_pending` se lee
(pop) ANTES del radio `grupo_sec`; `_prjsel_pending` ANTES de `adminproj_sel`. 0 nombres libres, import
OK. Alcance: solo la Planificacion del admin (el board del campo en 📋 Mis proyectos abre solo proyectos
asignados; pendiente si se pide).

## Archivos: descarga desde la tabla (fila clicable) + por foto (v166)
Peticion del usuario: "la descarga debe ser mas accesible; que este en la tabla donde se ven los
archivos". En v165 la descarga estaba en un selector aparte debajo de la tabla → habia que buscar el
archivo por segunda vez.
### ⚠️ Por que estaba en un selector y no en la tabla
`st.download_button(data=…)` evalua `data` al RENDERIZAR, no al pulsar: un boton por fila bajaria TODOS
los archivos de Drive en cada pasada (el problema que arreglo v147). La solucion que mantiene la
descarga LAZY es la **seleccion de fila** (`st.dataframe(on_select="rerun", selection_mode="single-row")`,
soportado desde Streamlit 1.35; el pin es `>=1.35`): tocas una fila y solo entonces se descarga ESA.
### Cambios
- **Tabla clicable**: al seleccionar una fila aparece debajo su ⬇️ descargar (+ ↩️ reabrir si es
  calculo, + 🗑 borrar si admin), via `_acciones_archivo`. Se **quito el selector "Abrir / descargar"**
  de v165 (redundante). ⚠️ Clamp del indice: si cambias el filtro con una fila elegida, el indice podria
  apuntar fuera de la lista actual — no se abre un archivo equivocado.
- **Fotos**: la miniatura YA baja los bytes para mostrarse (y `drive_store.download` cachea 5 min), asi
  que un **⬇️ bajo cada foto** reutiliza esos bytes — descarga directa sin segunda llamada a Drive.
### Verificacion
Compila + import real; tabla con `on_select`+`single-row` y accion desde `resto[_rows[0]]`; 0 restos del
selector viejo (`arch_sel`); 0 nombres libres nuevos (el `ex` es `except as ex`). La descarga sigue LAZY
(0 descargas hasta elegir fila; la galeria solo baja las fotos visibles y reutiliza sus bytes).

## Archivos: una lista ÚNICA y buscable (v165)
Peticion del usuario: "si tengo muchos archivos se convierte en un problema encontrar el que quiero".
El apartado 📎 Archivos eran DOS sub-secciones (Documentos y Calculos) con **tres selectores distintos**
y listas planas: con 40 archivos, encontrar uno era el problema.
### Decisiones del usuario (AskUserQuestion)
Unificar TODO en una sola lista buscable · mecanismo = **buscador + desplegable de tipo con contadores**.
### `_archivos_section(pid)` (reemplaza a `_documentos_section` + `_calculos_section`, borradas)
- **Fuente unica: `list_documents`**, que YA es la union de todo — `toolruns.registrar` archiva cada
  PDF de calculo como documento tipo "calculo" con el **MISMO DriveID** que su fila de calculo. Se casa
  cada calculo con su toolrun **por DriveID** → «reabrir en la herramienta» sin duplicar. Los calculos
  reabribles SIN PDF (Drive caido) se agregan como entradas reopen-only (no se pierden).
- **Barra para acotar**: 🔎 buscar (nombre · tipo · resumen · quien) · **Tipo con contadores**
  (`Todos (M) · 📄 Informe cliente (3) · 🧮 Calculos (5) · 📷 Fotos (12)…`) · **Orden** (reciente/
  antiguo/nombre/tipo) · *"Mostrando N de M"*. Reduce a la vez la galeria, la tabla y el descargador.
- **Render**: galeria de fotos (las que pasan el filtro, sigue LAZY) + tabla del resto. Accion sobre el
  elegido (lista ya corta): ⬇️ descargar (lazy) · ↩️ reabrir calculo (si tiene entradas) · 🗑 borrar (admin).
- Los 2 call-sites (detalle admin + 📋 Mis proyectos del campo) llaman a `_archivos_section`. El plano
  (`_plano_section`) y "🔄 Reconstruir en el Survey" siguen arriba en el detalle admin, intactos.
### Verificacion
Contra datos REALES: PRJ-0001 = 11 archivos (2 pre-start, 2 informe, 1 matriz, 3 plano, 3 foto), **0
DriveID duplicados**; PRJ-0003 = 3; PRJ-0002 vacio. La hoja Calculos sigue con 0 filas (runs=0), asi que
el dedup de calculos se probo SINTETICO: calculo con PDF = 1 entrada (no 2) reabrible · calculo sin PDF
= reopen-only sin perderse · calculo sin entradas ni PDF = no aparece. 0 nombres libres nuevos (el `ex`
es `except as ex`), 0 referencias a las funciones viejas, prompt del agente al dia (regla v133).

## Fichaje del campo: horas por día (medianoche) + olvidos accionables (v164)
Revision de ⏱ Fichaje desde el rol campo (tecnico/visual/integracion). La UI ya era solida (v150);
el hallazgo fue de DATOS, con evidencia real: **3 de 16 fichajes cruzan medianoche** (~8.6 h, entrada
~21:00 → salida ~05:00).
### ⚠️ Tecnico: las horas se atribuian TODAS al dia del Clock In
`resumen_hoy` y `group_hours` contaban la sesion entera en el dia de entrada (o la excluian entera de
la ventana). Consecuencias: (a) el campo veia *"🟡 Jornada abierta · cronometro 5:12"* pero
*"Jornada de hoy: 0.00 h"* (contradiccion, porque `resumen_hoy` filtraba por dia del Clock In); (b) el
reporte del admin en **"Hoy"/"Semana"** perdia el tramo trabajado de una sesion que entro el dia
anterior. **Decision del usuario: partir las horas por dia (medianoche).**
- **`timeclock._segmentos_dia(ci, fin)`** → `[(date, horas)]`, corta en cada medianoche.
  **`_row_segmentos(r)`** lo aplica a una fila (abierta = hasta ahora; cerrada = hasta Clock Out).
  ⚠️ Una fila cerrada de UN solo dia respeta las **Horas GUARDADAS** (no recomputa) → el total con
  `days=None` queda IDENTICO; solo las que cruzan medianoche se reparten.
- **`resumen_hoy`** cuenta el segmento de HOY. **`group_hours(grupo, days)`** suma solo los segmentos
  dentro de la ventana. **`proyectos_por_usuario_dia`** (roster) cuenta el proyecto en cada dia
  trabajado. **`expenses.spend_curve`** reparte la M.O. por dia real (total sin cambio).
### Olvidos: aviso ACCIONABLE + cierre honesto
`_aviso_olvido` deja de ser solo texto: para una sesion abierta de un dia anterior, pide **"a que hora
terminaste"** (date+time, sugerido = entrada+8 h) y cierra con ESA hora, no con "ahora" → no registra
las horas fantasma de la noche que nadie trabajo. Valida hora ∈ (entrada, ahora]. **`clock_out` gana
`out_ts`** opcional (por defecto = ahora); de paso se quito el parametro muerto `nota` (nadie lo pasaba
desde v150). Tarjeta "Sin asignar": el pie pasa a *"traslados, espera o proyecto sin fichar"* (para un
tecnico en una obra, sin_asignar grande casi siempre = olvido fichar el proyecto).
### Verificacion (contra datos REALES, gspread crudo)
`_segmentos_dia` unidad: mismo dia = total · **16/07 20:31→17/07 05:05 = 3.47+5.09 = 8.57** ✓ · 2 noches
= 28 h · entrada=salida/basura = []. **`group_hours(days=None)` OLD vs NEW: diff 0.0000 h** en los 4
usuarios reales (nada perdido). Ventana "Semana": NEW **recupera** el tramo del dia que OLD tiraba
(`lksdfkldsf` 0 → 5.09 h). 0 nombres libres nuevos (el `e` de clock_out es el `except as e`). Ningun
call-site pasa `nota`. Import real de los 3 modulos OK.

## Se elimina el rol conductor: era un subconjunto del campo (v163)
Peticion del usuario: "integrar el perfil del conductor dentro del campo y luego eliminar el conductor".
### Por que ya no aportaba
Tras **v150** (fichaje unificado: dos relojes jornada+proyecto para TODOS), el conductor quedo como un
SUBCONJUNTO del campo. Su unica funcion propia era `render_conductor_projects` (ver todos los proyectos
del grupo en solo lectura + cargar recibo a cualquiera). **Decisiones del usuario:** (a) mantener el
bloqueo de contacto de v79 para todo el campo; (b) NO trasladar por ahora lo de "recibo a cualquier
proyecto"; (c) el unico usuario conductor real (`conductor`/fijiofgjei, cuenta de prueba sin contacto)
se **ELIMINA**, no se migra.
### Cambios
- `auth.ROLES` pasa de 4 a **3 roles** (fuera "conductor"). Los selectores de rol que leen `ROLES`
  (creacion del propietario) dejan de ofrecerlo solos.
- `app.py`: fuera el label `_L_CONDPROJ`, la rama de nav del conductor y su enrutado.
- `projects_ui.render_conductor_projects` **eliminada** (borrada por AST, 27 lineas).
- `auth_ui`: "Crear usuario" pasa a **solo campo** (email obligatorio siempre); el panorama de usuarios
  filtra `== "campo"`.
- `plan_ui`: `rol in ("campo","conductor")` → `rol == "campo"`.
- `chat_agent`: fuera las 2 lineas del prompt que describian el rol (regla v133).
- Comentarios/filtros en roster_ui / expenses / timeclock ajustados. `timeclock_ui:9` se deja (es
  historia correcta: "hasta v149 solo el conductor tenia los dos relojes").
### Verificacion
Usuario de prueba borrado (verificado: 0 conductores antes/despues). Import REAL de los 8 modulos
tocados OK; `auth.ROLES` sin conductor; `render_conductor_projects` ausente y **0 referencias residuales**
a el / `_L_CONDPROJ` en todo el repo; la nav del campo queda IDENTICA (nada perdido ni ganado); 0 nombres
libres nuevos en las funciones tocadas de auth_ui; sin variable `rl` huerfana (la que queda es de otro
form, el del propietario). El prompt del agente ya no menciona el conductor.

## Mis proyectos (campo): sub-pestañas + tabla de avance + fechas reales automaticas (v162)
Peticion del usuario: revisar 📋 Mis proyectos del campo (tecnico/imagen/integracion). Eran **108
lineas apiladas en scroll unico** (mismo problema que el detalle del admin antes de v132) y su accion
NUCLEO —actualizar avance— era la mas incomoda: N expandibles, un guardado cada uno.
### ⚠️ Tecnico 1: el avance eran N escrituras (429 en potencia)
`update_activity_progress` hacia hasta 5 `update_cell` por actividad, y el campo lo llamaba una vez por
expandible. **`projects.save_field_progress(pid, cambios)`** escribe SOLO lo que cambio en 1
`batch_update` (el patron 429 de v80/v150). El campo edita el avance en UNA tabla (`st.data_editor`,
Actividad/Avance %/Nota) y guarda una vez; solo se mandan las filas que cambiaron.
### ⚠️ Tecnico 2: las fechas reales eran texto libre y casi nadie las llenaba
`FechaInicioReal`/`FechaFinReal` eran `text_input("YYYY-MM-DD")` (mismo fallo de v149) y alimentan la
curva S real (`windows`). En los 3 proyectos reales estaban TODAS vacias. **Decision del usuario:
automaticas** — no se teclean:
- Inicio real = el dia que el avance pasa de 0 (si estaba vacia). Sticky.
- Fin real = el dia que llega a 100 (si estaba vacia).
- **Reapertura**: si una actividad al 100% baja de 100, se BORRA el fin real (no dejar "terminada" una
  fecha que ya no es cierta). Cuando vuelva a 100, nueva fecha.
### Imagen: sub-pestañas (radio, como el admin) + KPI cards
Cabecera con tarjetas (estado, avance, cliente) + barra + Maps. Sub-navegacion **radio** (NO st.tabs,
v56): 🏗 Avance (instrucciones + tabla) · 🚨 Avisos (reportar/ver alarmas) · 💰 Recibos · 📎 Archivos
(calculos + documentos). Antes todo era un scroll; en el movil el campo va directo a lo suyo.
La planificacion (roster "hoy" + board, v160) sigue arriba, cross-proyecto.
### Verificacion
`save_field_progress` probado en 6 casos (arranca→inicio · ya arrancada→no toca · llega a 100→fin · ya
100→no re-escribe · reabre→borra fin · sigue en 0→nada): todos correctos. render_field_projects: 0
nombres sin resolver NUEVOS (AST vs commit anterior), los 8 helpers existen, las 4 ramas del radio
presentes. El batch real corre por primera vez en el Cloud.

## Tablero de cuadrilla — plan vs real (v161): feature COMPLETA
Ultimo incremento del roster. El admin ve, por dia, lo ASIGNADO contra lo FICHADO.
- **`timeclock.proyectos_por_usuario_dia(grupo, fecha)`** — {usuario: [{pid,nombre}]} de los proyectos
  que cada uno ficho ese dia (segmentos de tipo proyecto). Filtra fichajes sin proyecto (nada que
  comparar).
- **`roster_ui._plan_vs_real`** (expander en 📅 Planificacion): selector de dia (hoy por defecto si cae
  en la semana vista) + KPIs (🟢 donde tocaba · 🔴 en otro sitio · ⚠️ sin fichar) + una linea por
  persona con su estado. Seis ramas: 🟢 fichó donde tocaba · 🔴 asignado a X, fichó en Y · ⚠️ asignado
  sin fichar · — trabajo sin enlace a PRJ (nada que comparar) · ℹ️ OFF/Leave pero fichó · ❔ sin plan
  pero fichó.
- ⚠️ **Solo compara trabajos enlazados a un PRJ**: un delivery o un estado no tienen fichaje contra que
  medir. Es la razon de ser del enlace opcional a proyecto.
### Verificacion
Las 6 ramas simuladas con roster + fichajes: 🟢1/🔴1/⚠️1 y las 3 informativas, todas donde deben.
`proyectos_por_usuario_dia` contra los fichajes REALES: 16/07 lksdfkldsf→prueba1, 17/07 vacio (la
sesion cruzo medianoche, Clock In fue el 16), y el fichaje sin proyecto del 10/07 ya no aparece.
### Roster COMPLETO (v159–v161)
v159 base (catalogo + rejilla admin) · v160 campo (ve el board + atajo de fichaje) · v161 plan vs real.
PENDIENTE solo la validacion en el Cloud: crear trabajos, asignar una semana, copiar semana, y que el
campo vea su "hoy" — todo eso son escrituras que se estrenan alli.

## Tablero de cuadrilla — el campo lo ve + fichaje con la asignacion del dia (v160)
Segundo incremento del roster (v159 fue la base). Cierra el lado del CAMPO.
- **`roster.asignacion_dia(grupo, usuario, fecha)`** — que le toca a una persona un dia: {asig, nota,
  proyecto_id, etiqueta, color, es_estado}. Fin de semana (weekday>4) o dia sin asignacion → {}.
- **`roster_ui.render_board_readonly(grupo, resaltar_usuario)`** — el board en SOLO LECTURA (el campo ve
  toda la cuadrilla, decision del usuario), con su fila resaltada (👉 + fondo). Nav de semana, sin edicion.
- **Campo → 📋 Mis proyectos**: arriba, "📅 Hoy: <trabajo> · <nota>" destacado + expander con el board
  completo. Va ANTES del early-return por "sin proyectos", asi que se ve aunque el campo solo tenga
  trabajos NO enlazados a PRJ.
- **Fichaje**: si la asignacion de hoy enlaza a un PRJ que el campo tiene, aparece un boton
  **"🟢 Fichar a <trabajo> (tu asignacion de hoy)"**. ⚠️ Es una accion EXPLICITA (dice a que fichara),
  no una preseleccion silenciosa — respeta la regla de v138. Si la asignacion es un estado (OFF/Leave)
  no hay PRJ y no aparece boton.
### Verificacion
Sintaxis + import de los 4 modulos; `asignacion_dia` mapea bien el dia (martes→mar, sabado→{}). Todo
lo que ESCRIBE (guardar_persona, copiar_semana) y el board real siguen sin ejercitarse hasta el Cloud.
### PENDIENTE (ultimo incremento)
Plan vs real: en el admin, comparar la asignacion del dia (si enlaza a PRJ) contra donde ficho de
verdad cada persona, y marcar desvios.

## Tablero semanal de cuadrilla — base: catalogo + rejilla del admin (v159)
Feature nueva pedida por el usuario (mando un pantallazo de su hoja actual: persona×dia, color por
sitio, trabajos "89. Talavera", estados OFF/Leave/TAFE, notas de vehiculo/equipo). **Diseno acordado
antes de construir** (ver memoria feature-roster-planificacion). Decisiones firmes: catalogo de
trabajos propio con enlace OPCIONAL a PRJ · una asignacion por dia · semana Lun–Vie + copiar semana
anterior · estados OFF/Leave/Formacion + nota libre · el campo ve todo el tablero · conecta con fichaje.
### Esta version (la BASE)
- **`core/roster.py`** — dos hojas nuevas (multi-tenant, migran solas):
  - **Trabajos**: ID·Grupo·Numero·Nombre·Color·ProyectoID·Activo. CRUD + `trabajos_idx` (resuelve
    color/etiqueta aunque el trabajo se desactive).
  - **Roster**: ID·Grupo·Semana(lunes)·Usuario·**DatosJSON** = {lun:{asig,nota},...vie}. **1 fila por
    persona×semana** (compacto; se lee la semana entera). `get_semana`, `guardar_persona` (1 escritura),
    `copiar_semana`.
  - `ESTADOS` (OFF/LEAVE/FORMACION, claves reservadas que no colisionan con TRB-####), `PALETA` (12
    colores), utilidades de fecha (`lunes_de`, `fecha_de_dia`, `rango_label`).
- **`core/roster_ui.py`** — seccion **📅 Planificacion** en 🛠 Mi grupo: navegacion de semana + copiar
  semana anterior + **rejilla HTML coloreada** (como el board del usuario, verificada en navegador) +
  editar la semana de una persona (selector trabajo/estado + nota por dia, guarda en 1 escritura) +
  catalogo de trabajos (crear con color de la paleta y enlace opcional a PRJ, activar/desactivar).
### ⚠️ La rejilla es HTML, no st.data_editor
`st.data_editor` no colorea celdas por valor, y el color es clave para leer el board. Solucion: HTML
para VER (con `_texto_sobre` que elige negro/blanco por luminancia del fondo) + edicion persona a
persona debajo. Verificado en el navegador con datos tipo pantallazo: 9 personas, colores correctos,
notas, OFF/Leave, columna de nombres fija.
### Verificacion (logica pura, SIN tocar produccion)
Crear las hojas escribiria en el Sheet real, asi que se probo solo la logica: semana del miercoles 27/5
→ lunes 25/5 ✓; resolucion trabajo/estado → color+etiqueta+PRJ ✓; orden por numero ✓; JSON omite
celdas vacias ✓; los 3 modulos importan. Las escrituras (add_trabajo, guardar_persona, copiar_semana)
corren por primera vez en el Cloud.
### PENDIENTE (proximo incremento)
Campo → "mi semana" (donde voy cada dia) · fichaje pre-rellenado desde el roster · plan vs real
(asignado a X / ficho en Y, solo para trabajos enlazados a un PRJ).

## Ficha de usuario: 📊 Su trabajo ACTIVA + 🔑 Acceso a doble columna (v227)
Revisión de las SUB-pestañas de la ficha (`_ficha_usuario`). Auditoría honesta: 📇 Contacto y 🎫 Credenciales
(v185-189) ya sólidas → no se tocaron; 📊 Su trabajo era PASIVA y 🔑 Acceso estaba apilada.
- **📊 Su trabajo**: los proyectos asignados dejan de ser texto ("Asignado a: X · Y") y pasan a **botones
  CLICKEABLES** (rejilla 2 col) que **abren el proyecto** — set `_prjsel_pending` + `_admin_nav_pending=
  ("proyectos","📊 Proyectos")` (+ `_gruposec_pending` para la nav vieja) + rerun (mismo patrón que el board del
  roster). Además, **"Horas por proyecto"** de esa persona (de `group_hours(...)["por_proyecto"]`, el dato de
  v216): dónde puso su tiempo. Los 3 KPIs (horas/recibos/proyectos) se mantienen.
- **🔑 Acceso**: peinada a **doble columna** — contraseña | tarifa lado a lado (antes apiladas); rol/grupo del
  propietario ya iban en 2 col; activar/desactivar a ancho completo. ⚠️ Al mover la tarifa a la columna se
  BORRÓ el bloque de tarifa viejo (mismos keys `{k}_tar`/`{k}_savetar` → habría dado StreamlitDuplicateKey);
  verificado que cada key aparece 1 sola vez.
Verificado: compila + import + AST (0 libres) + keys sin duplicar. La ficha se renderiza a nivel top en
`_grupo_usuarios`, así que los `st.columns` nuevos son 1 nivel (sin anidación). Confirmación visual = Cloud.

## 👷 Usuarios: panorama ACTIVO (fila de salud + tabla clickeable → ficha) (v226)
Revisión de la sub-pestaña 👷 Usuarios (Planificación). La ficha 360° por persona (`_ficha_usuario`, v153/v184)
está sólida y NO se tocó. El problema era el PANORAMA: tabla pasiva + un desplegable aparte "elige un usuario"
para abrir la ficha — el mismo patrón pasivo que el usuario ya hizo cambiar en Proyectos/Finanzas. `_grupo_usuarios`
reescrita (decisión del usuario: **tabla clickeable**, no tarjetas):
- **Fila de salud del equipo**: 👥 personas · 🟢 activos · ⚠️ sin contacto · 🟡 cred. por vencer · 🔴 cred.
  vencida(s). La salud de credenciales por usuario sale de **`credentials.list_group(grupo)` (1 lectura cacheada)**,
  quedándose con el peor estado por persona.
- **Tabla CLICKEABLE** (`st.dataframe(on_select="rerun", selection_mode="single-row", key="gu_tbl")`): Usuario ·
  Nombre · Activo 🟢/🔴 · Contacto ✅/⚠️ · **Credenciales 🟢/🟡/🔴/—** · Tarifa/h. Al **seleccionar una fila** se
  abre la ficha de esa persona debajo. Se quitó el `ui.elegir` (desplegable) de v153.
- **Fuente de verdad `_gu_open`** (usuario): maneja (a) **deep-links** `gp_fichasel="Nombre (usuario)"` desde la
  agenda de HOME (v200) y Finanzas·Horas (v215) — que ya no encuentran el desplegable viejo; se parsea el usuario,
  se abre su ficha y se descarta la selección de tabla previa; (b) que la ficha persista entre sus reruns; (c) al
  **eliminar**, `_ficha_usuario` (sel_key por defecto `gp_fichasel`, inerte aquí) deja `_gu_open` apuntando al
  borrado → el bloque de arriba detecta que ya no existe y cierra la ficha (+ limpia `gu_tbl`).
- El form de alta se extrajo a **`_crear_usuario_form(grupo)`** (reusado en el estado vacío y en el expander).
  La matriz de credenciales (expander) y el alta quedan como secundarios abajo.
Verificado: compila + import + AST (0 libres) + parse del deep-link (todos los formatos). El panel del PROPIETARIO
(`_owner_usuarios`) NO se tocó (sigue con su selector). Confirmación visual = Cloud (necesita login+Sheets).

## Finanzas/Gastos: torta de gasto por rubro (v224)
El usuario pidió una **torta** del gasto por rubro debajo de los dos bloques de barras (reparto | compras por
categoría). Decisión del usuario: rubros = **Mano de obra + cada categoría de compra** (reparto COMPLETO del
gasto, opción A). Nuevo **`_torta_html(pares, total)`** (junto a `_barras_html`): pie con **CSS
`conic-gradient`** + leyenda (color · rubro · $ · %) — **sin dependencias de charting** (nada de plotly/
matplotlib), mismo enfoque HTML que las barras, se renderiza en `st.markdown`. En `render_group_expenses`,
debajo de los bloques de barras y antes de la tabla "Proyectos con presupuesto":
`_rubros = [("Mano de obra", ΣMO)] + sorted(por_categoria)` (solo >0), total = `sum(_rubros)` (así los % suman
100 exacto). ⚠️ **Verificado EN VIVO** que `st.markdown` NO recorta `conic-gradient` (mini-app + DOM: el círculo
tiene `background-image: conic-gradient(...)` computado; la nota de diagrams.py sobre "Streamlit elimina los
`<svg>`" aplica a SVG, no a un div con conic-gradient). Compila + import + AST (0 libres) + lógica (tramos
0→100%, formato $/%). Paleta de 12 colores; MO = azul (#2e6da4, como el reparto).

## Estética fase 3a: radios del detalle + headers de grupo (v234)
Sigue v232/v233. Chunk acotado del contenido:
- **Radios de sub-navegación** (`st.radio`): el detalle de proyecto (📊 Estado/✏️ Datos/💰 Costos/📎 Archivos) y
  el de 📋 Mis proyectos del campo (🏗 Avance/🚨 Avisos/💰 Recibos/📎 Archivos) ahora muestran iconos Material
  vía **`format_func`** — ⚠️ las OPCIONES siguen siendo el ID con emoji, así que el `if _sec == "📊 Estado"` y
  cualquier deep-link NO cambian (mismo patrón decouple que la nav). Verificado en vivo que `st.radio` renderiza
  `:material/` por `format_func`.
- **Headers**: `#### 💰 Gastos del grupo` / `#### ⏱ Horas del grupo` → `:material/payments:` / `:material/schedule:`.
Compila + import + matching intacto. PENDIENTE (fase 3 sigue siendo grande): más headers de paneles, botones
(💾/➕/🔎…) y captions repartidos por projects_ui/auth_ui/survey_ui/tools; estados 🟢🔴🟡 sin tocar; el prompt
del agente (chat_agent) menciona los emoji viejos — actualizar cuando se cierre la migración de esas etiquetas.

## Estética fase 2: iconos Material en el chrome del admin (v233)
Sigue v232. Se migró el CHROME (visible en cada página): topbar + barra de usuario.
- **`home_ui`**: campana 🔔 → `:material/notifications:` (label del popover + header); del buscador se quitó el
  emoji 🔎 (los placeholders son texto plano, no renderizan `:material/`).
- **`auth_ui.render_user_bar`** (sidebar, TODOS los roles): rol 👑/🛠/🔧 → `:material/shield_person:` /
  `:material/manage_accounts:` / `:material/engineering:`; 🏢 grupo → `:material/business:`; 🚪 Cerrar sesión →
  `:material/logout:`. Monocromo (color del tema), no azul COPEX (es chrome, no nav).
⚠️ **Verificado en vivo**: los `:material/` renderizan en label de POPOVER, en `st.markdown` (incluso con salto
de línea `  \n`) y en botón (sin texto literal). Compila + import. PENDIENTE fase 3: cabeceras de los paneles de
contenido (projects_ui, etc.) y botones (💾/➕/🔎…); los estados 🟢🔴🟡 siguen sin tocar.

## Estética: iconos Material (azul COPEX) en la nav, en vez de emoji (v232)
El usuario pidió reemplazar los emoji "infantiles" por iconos profesionales dentro de la paleta COPEX (se le
mostró un mockup; eligió empezar por la **navegación** y dejar los estados 🟢🔴🟡 por ahora). Fase 1 = el
sidebar del admin (`home_ui`):
- **Material Symbols nativos** de Streamlit (`:material/xxx:`), monocromo, sin dependencias. ⚠️ **Verificado en
  vivo** que: (a) renderizan en labels de botón (no solo markdown); (b) el icono es el ÚNICO `<span>` del `<p>`
  del botón (sin clase/testid) → se pinta SOLO el icono con `[class*="st-key-navsec_"] button p span{color:...}`
  dejando el texto en su color. Iconos en **azul COPEX #2e6da4**; sección/sub ACTIVA en #1e4e79 (icono+texto) +
  highlight.
- `_SECCIONES` labels → `:material/...:` (seguro: la lógica usa la CLAVE). Ej: home/schedule/calendar_month/
  folder/payments/inventory_2/build/contacts.
- ⚠️ **Sub-pestañas = (id, display)**: el ID conserva el emoji ("📊 Proyectos") porque es el IDENTIFICADOR que
  usan los deep-links (`_ir_a`/`_admin_nav_pending` en projects_ui/auth_ui/roster_ui) y el match en `_seccion_*`
  — NO se toca. `display` (`:material/...:`) es lo único que cambia (sidebar + `_sub_header` + hub). Cero cambios
  en deep-links. `_sub_header(seccion)` deriva el título de `_SECCIONES` y muestra el display de la sub. El hub
  toma el display de `_SUBSECCIONES` y navega con el ID.
Verificado: compila + import + AST (0 libres) + IDs de matching intactos + mecanismos CSS en vivo. Solo rol
admin. PENDIENTE (fases siguientes): cabeceras/botones del contenido, tablas, y decidir si los estados 🟢🔴🟡
se migran. Los emoji de otros contextos (chat_agent prompt, plan_data, toolruns, captions) NO se tocaron.

## Herramientas: hub/página de entrada (v231)
El usuario pidió un hub de entrada para 🛠 Herramientas (se le mostró un mockup vía visualize; eligió la versión
**simple**, sin el chequeo del plano). Se añadió **"🧰 Inicio"** como PRIMERA sub-pestaña de herramientas
(`_SUBSECCIONES["herramientas"]`), que es el default → al entrar a Herramientas ves el hub. `_hub_herramientas`
renderiza una **tarjeta por herramienta** (`st.container(border=True)` en rejilla de 3 col): título + qué hace
(1 línea) + botón «Abrir →» que hace `navegar("herramientas", <label>)`. Las 6: Survey · Plomada · Rieles ·
Buffers · Belting · Pre-Start. `_seccion_herramientas` ganó la rama `if sub == "🧰 Inicio": _hub_herramientas()`.
⚠️ Cambiar el default de Survey→Inicio no rompe nada: "Reconstruir en el Survey" (projects_ui) NO auto-navega
(solo carga session_state + avisa "ve a Survey"). Verificado: compila + import + AST (0 libres). El chequeo del
plano por herramienta (v175, `plan_data.por_herramienta`/`del_proyecto`) queda para una posible v2 del hub.

## Nav: desplegar ≠ navegar (no cargar la sub-pestaña al expandir) (v230)
El usuario notó que al tocar una sección (p.ej. Planificación) SOLO para desplegar sus sub-pestañas, la app ya
abría/cargaba la 1ª (Tablero). Fix: en `sidebar_menu` se separa **desplegar** de **navegar**.
- Nuevo estado `_admin_expanded` (sección desplegada en el sidebar), independiente de `admin_nav` (sección
  ACTIVA cuyo contenido se muestra). Por defecto la activa está desplegada; `""` = todo plegado.
- Tocar una sección **con** hijas → solo togglea `_admin_expanded` (`st.rerun`, SIN `navegar`) → el contenido
  actual NO cambia; las hijas se muestran/ocultan. Tocar una sección **sin** hijas → `navegar` directo. Tocar
  una **hija** → fija `_admin_expanded` + `navegar(sec, sub)` (ahí sí carga).
- `_aplicar_nav_pending` fija `_admin_expanded=seccion` en cada navegación (deep-links despliegan el destino).
- La sub activa solo se resalta si la desplegada == la activa (`_exp == _cur`); caret ▾ = desplegada, ▸ =
  plegada con hijas. Verificado: compila + import + AST (0 libres) + escenarios razonados.

## Navegación del admin: sidebar de 2 niveles (acordeón) (v229)
El usuario pidió que las sub-pestañas (nivel 2) se desplieguen en la PROPIA barra izquierda, para ir directo
a una sub-pestaña desde el sidebar. Se le mostró un mockup (visualize) de **acordeón** vs **árbol libre** →
eligió **acordeón** (solo la sección activa despliega sus hijas). Rediseño de `home_ui.sidebar_menu`:
- El nivel 1 pasa de `st.radio` a **botones** (para poder anidar las hijas debajo del padre activo). Se estilan
  como ítems de menú vía CSS `.st-key-…` (borde/fondo transparentes, texto a la izq; activo = fondo #e8eef6 +
  texto #1e4e79 + negrita). ⚠️ **Verificado EN VIVO** (mini-app + DOM: activo resaltado, sub indentada 26px,
  inactivas transparentes). La sección activa se guarda en `st.session_state["admin_nav"]` (ya NO es widget →
  asignación plana).
- **Sub-pestañas centralizadas** en `_SUBSECCIONES = {seccion: (clave_estado, [labels])}` (antes repartidas en
  cada `_seccion_*`); `_SUBKEY` se deriva de ahí. Bajo la sección activa se renderizan sus hijas como botones
  indentados (`navsub_<sec>_<i>`); tocar una → `navegar(sec, sub)`.
- El selector de nivel 2 **se quitó del contenido** (`_subnav` eliminado): ahora `_sub_header(titulo, seccion)`
  solo pone la cabecera "## Titulo · <sub actual>" y los `_seccion_*` leen la sub de `session_state`.
- ⚠️ **Colisión de clases evitada**: las claves de nivel 1 son `navsec_<k>` (NO `nav_<k>`) porque
  `[class*="st-key-nav_"]` también matchearía `st-key-nav_back_btn` (el botón ← del topbar v205) y lo
  restylearía. `navsec_`/`navsub_` no matchean `nav_back_btn`.
- Deep-links intactos (`_admin_nav_pending` → `_aplicar_nav_pending` fija `admin_nav` + la sub-key); back button
  y `_track_history` igual; `app.py` sin cambios (sidebar_menu devuelve la clave de sección como antes).
Verificado: compila + import + AST (0 libres) + 0 referencias a `_subnav` + CSS en vivo. Solo rol admin.

## Cartera de proyectos: toggle Tarjetas | Lista (v228)
El usuario pidió una vista alternativa: además de las tarjetas (v223), la típica **tabla** (proyectos por
filas, datos por columnas). En `_panel_proyectos` se añadió un **toggle `st.radio` "🃏 Tarjetas | 📋 Lista"**
(key `cart_view`, junto al header de la cartera). Nueva **`_cartera_lista(proys, alarmas, delays, aheads,
costos)`**: `st.dataframe` CLICKEABLE con columnas Proyecto · Estado · **Avance (ProgressColumn con barra)** ·
Cliente · Inicio · Fin · Ppto (% ejecutado, ⚠️ si over) · 👷 usuarios · Situación (🔴/🟢 retraso/adelanto) ·
🔔 alertas. Al **seleccionar una fila** se abre el detalle (`_admin_open_proj`) y se **popea `cart_tbl`** para
que al volver NO se re-abra solo (misma técnica anti-loop que v226). ⚠️ **Verificado en vivo** que la columna
🔔 no puede mezclar int y str (Arrow falla la serialización) → se fuerza a **string** (`str(_al) if _al else
""`); tras el fix no hay warning de Arrow. `ProgressColumn` existe en 1.57. Ordenación por urgencia igual que
las tarjetas. Compila + import + AST (0 libres). La cartera del propietario (`_portfolio_html`) no se tocó.

## Cartera de proyectos: tarjeta con resumen completo antes de abrir (v223)
El usuario pidió ver en el tablero (📊 Proyectos) toda la info del proyecto ANTES de abrirlo. Se le mostraron
2 opciones (mockup vía visualize) y eligió la **Opción A**: tarjeta con barra de progreso + botón «Abrir».
`_cartera_clickeable` reescrita (antes: botón-tarjeta con fondo=avance, v207/v208). Cada tarjeta =
**`st.container(border=True, key=f"cart_{i}")`** con `st.markdown` (HTML) + `st.button("Abrir →")` dentro, y
muestra los **7 datos**: nombre (+punto de salud) · estado (pill) + % avance (barra real) · cliente · fechas
inicio→fin (`_ddmm`) · **% presupuesto ejecutado** (⚠️ si over) · **nº de usuarios** (CampoAsignados) · alertas
(🔔) + retraso/adelanto. Se quitaron las horas (decisión del usuario). Borde IZQUIERDO por salud vía CSS
`.st-key-cart_{i}{border-left:4px solid <color>}` (⚠️ **verificado en vivo**: el contenedor con `border=True`+
`key` ES el elemento `.st-key-<key>` y su borde-izq se colorea; `st.container` acepta `key`+`border` en 1.57).
El **% de presupuesto** sale de **`expenses.group_expenses(grupo)` (1 lectura CACHEADA)** → `{pid:{pct,
presupuesto,over}}`, no N cálculos; de paso se **quitó la lectura `project_hours_bulk`** del panel (ya no se
muestran horas). Verificado: compila + import + AST (0 libres) + **render Streamlit real** (mini-app + DOM:
bordes 🔴/🔵/🟢, barras a %, pills, ⚠️ over, «Abrir» dentro del recuadro). Aplica solo a la cartera del ADMIN
(`_panel_proyectos`); el propietario sigue con `_portfolio_html`.

## Fix: la sesión recordada moría al cerrar/reabrir (cookie de sesión → persistente) (v222)
El usuario reportó que, aun tildando "mantener la sesión iniciada" (v221), al **cerrar y reabrir** la app le
pedía login otra vez (probando en la **PWA instalada** en escritorio y móvil). Diagnóstico: la cookie
sobrevivía al refresco pero moría al cerrar → se estaba guardando como **cookie de SESIÓN**. Causa: el `set`
de `extra-streamlit-components` no aplicaba la expiración de forma efectiva (su Python manda `expires_at` ISO,
pero el resultado en la PWA era una cookie sin persistencia). Fix (v222):
- **`session_cookie.save` reescrito**: ya NO usa el `set` de la librería. Escribe la cookie **persistente con
  `max-age`** directamente en el documento de la app vía **`window.parent.document.cookie`** (misma técnica que
  el mobile-back-trap v205): `copex_session=usuario|token; max-age=604800; path=/; SameSite=Lax`. El origen es
  el mismo que lee `load()` (el componente de la librería se sirve desde el host de la app), así que la lectura
  la sigue viendo. `clear()` sigue con el `delete` bloqueante de la librería (el logout hace `st.rerun()`
  inmediato, que descartaría un `components.html`). Se quitó el import `datetime` (ya no se usa).
- ⚠️ **Timing**: un `components.html` justo antes de `st.rerun()` se DESCARTA (el rerun tira los deltas del run
  en curso). Por eso la cookie NO se escribe en `_do_login`; se marca `st.session_state["_remember_session"]`
  y la escribe **`render_user_bar`** (sidebar, corre en cada página logueada, en un run que TERMINA;
  idempotente y 'rolling' → refresca los 7 días en cada visita). El restore por cookie también setea el flag;
  el logout lo limpia (`pop`).
- **Verificado EN VIVO** (mini-app en preview + inspección): `window.parent.document.cookie` desde el iframe de
  `components.html` **sí** escribe en el top document; **CookieStore API** confirma `persistent:true`,
  `expires` ≈ +7 días, `sameSite:lax`, valor `juan|abc123` con el `|` literal (lo lee `load()`). Compila +
  import + AST (0 libres). Confirmación final en la PWA del usuario = cerrar/reabrir sigue dentro.

## Login: "mantener la sesión iniciada" ahora es OPCIONAL (v221)
La persistencia por cookie (v107/v188) estaba **siempre activa**: cada login guardaba una cookie de 7 días y al
refrescar/reabrir la sesión se restauraba sin escribir nada. El usuario pidió que sea **un tick opcional**.
- **Check "Mantener la sesión iniciada en este dispositivo"** en el login (`auth_ui.render_login`), key
  `login_remember`, **por defecto SIN tildar** (decisión del usuario; más seguro para equipos compartidos).
- **`_do_login` solo llama `session_cookie.save` si el check está tildado**; el resto igual. Sin tildar → no hay
  cookie → la sesión dura solo esa pestaña (refrescar/reabrir pide login). Tildado → cookie 7 días, restaura sin
  reescribir usuario/contraseña en ese dispositivo. La restauración (`load`+`validate_session`) no cambia: sin
  cookie, no hay nada que restaurar. Duración (7 d) y sesión única (v75) sin cambios.
- ⚠️ **Cambia el comportamiento anterior**: quien antes se quedaba logueado por defecto, ahora debe tildar el
  check. Es lo pedido.
Verificado: compila + import + AST (0 libres) + 1 solo call-site de `save`, gated. ⚠️ Cookie/navegador: la prueba
REAL es en el Cloud (tildar → refrescar sigue dentro; sin tildar → refrescar pide login).

## Auto-poblar el planificador con el proyecto entre sus fechas (v220)
Deploy 2 de 2 de "asignar más inteligente" (feature 2). Al asignar campo a un proyecto, ahora **aparecen
automáticamente en el planificador**, en ese proyecto (asig=PRJ-####, directo desde v218), **Lun–Vie entre
FechaInicio y FechaFinEst**. Decisiones del usuario: **todo el rango**, **solo celdas vacías** (no pisa OFF ni
otro proyecto).
- **`roster.autopoblar_proyecto(grupo, pid, usuarios, fecha_ini, fecha_fin, solo_vacias=True)`** → {llenadas,
  ocupadas, actualizadas, nuevas, semanas}. **Eficiente**: lee la hoja UNA vez (`get_all_values`) y escribe en
  **1 `batch_update`** (filas persona×semana existentes) **+ 1 `append_rows`** (semanas nuevas) — así el span no
  dispara el rate limit (a diferencia de `guardar_persona`, 2 llamadas por persona/semana). Rellena solo los
  días Lun–Vie DENTRO de [ini,fin] y solo si la celda está vacía; cuenta las `ocupadas` (respeta OFF/otro
  proyecto). Tope de seguridad `_MAX_SEMANAS=104`. `_a_date` parsea ISO o date.
- **`roster.limpiar_proyecto(grupo, pid, usuarios=None)`** → quita del planificador todas las celdas asig==pid
  (1 batch_update); se usa al **desasignar**.
- **`projects_ui._autoagenda(grupo, pid, nuevos, quitados, fecha_ini, fecha_fin)`**: helper compartido —
  auto-puebla los NUEVOS y limpia los DESASIGNADOS, e informa (días asignados / ocupados respetados / sin
  fecha-fin no planifica). Cableado en crear (`_nuevo_proyecto_form`, tras notificar) y editar
  (`_detalle_proyecto`, tras guardar: `nuevos` = añadidos, `_quitados` = quitados).
Verificado: compila + import + AST (0 libres) + tests con worksheet simulado (roster vacío→5 días en fila nueva;
OFF respetado + fila existente actualizada, 4 llenados; limpiar quita solo el pid y deja OFF). Confirmación = Cloud.

## Asignar personal más inteligente: ya-en-otro-proyecto + certificados requeridos (v219)
Petición del usuario (facilitar la planificación al asignar campo). Deploy 1 de 2 (el auto-poblado del
planificador entre fechas del proyecto = feature 2, va aparte). Se amplió el flujo de asignación (crear
`_nuevo_proyecto_form` + editar `_detalle_proyecto`, ambos ya llamaban `_avisar_asignados` FUERA del form):
- **Feature 1 — "ya está en otro proyecto (y hasta cuándo)"**: `_avisar_asignados(usuarios, grupo,
  exclude_pid, certs_req)` ahora, por cada usuario, lista los **otros proyectos activos** del grupo donde ya
  está asignado + su **FechaFinEst** ("Juan → 🏗 Torre Norte (hasta 15/09)"). Informativo, no bloquea.
- **Feature 3 — certificados que EXIGE el proyecto**: campo nuevo **`CertsReq`** en Proyectos (tipos del
  `credentials.CATALOGO`, `;`; migra al final; `create_project` gana `certs_req=""`, +1 en `row` y HEADERS —
  verificado 28==28). Multiselect "🎫 Certificados que exige el proyecto" en crear y editar. Al asignar,
  **`credentials.compliance(usuario, requeridos)`** → `{por_tipo:{tipo: vigente|por_vencer|vencido|falta},
  cumple}`; **cumple = ningún requerido vencido ni faltante** (por-vencer SÍ cumple, solo 🟡; decisión del
  usuario). `_avisar_asignados` avisa 🔴 quién no cumple (falta/vencido) y 🟡 los por-vencer; los tipos
  requeridos se excluyen del aviso genérico de credenciales para no duplicar. Vista VIVA `_cumplimiento_equipo`
  (tabla asignados × certs, ✅/🟡/🔴/—) en 📊 Estado, solo si el proyecto define requeridos.
Verificado: compila + import + AST (0 libres) + alineación row/headers + lógica de compliance
(vigente/vencido/falta→no cumple; por_vencer→cumple). Confirmación final = Cloud.

## Planificación: un PROYECTO se asigna directo (ya es un trabajo) (v218)
El usuario notó redundancia: en el roster solo se podían asignar TRB-#### (catálogo) o estados; para poner a
alguien en un proyecto había que **crear un "trabajo" que lo enlazara** (`ProyectoID`). Pero **todo proyecto es
un trabajo en sí mismo** — duplicarlo en el catálogo es ruido. Fix (decisión del usuario; color de proyecto =
**automático**):
- **`roster.trabajos_idx(grupo)` se extiende**: además de los TRB-#### del catálogo, mete los **proyectos del
  grupo (PRJ-####) como entradas sintéticas** `{ID, Numero:"", Nombre, Color:_color_proyecto(pid), ProyectoID:
  pid}` (con `incluir_archivados=True` para que un histórico a un proyecto archivado siga resolviendo). Así
  `color_de`/`etiqueta_de`/`proyecto_de` resuelven un PRJ **sin tocar a ningún llamador** (board admin+campo,
  agenda de HOME, plan-vs-real, `asignacion_dia`/fichaje) — cascada limpia. `setdefault` no pisa un TRB real;
  TRB-#### y PRJ-#### nunca colisionan.
- **`roster._color_proyecto(pid)`**: color estable y distinto por proyecto, `hashlib.md5(pid) % PALETA`
  (⚠️ NO `hash()`, que va salteado por proceso → cambiaría el color en cada arranque).
- **`roster_ui._opciones`** ahora lista: neutro + **🏗 proyectos activos** (value=PRJ-####; excluye Completado/
  Cancelado; archivados ya los oculta `list_projects`) + 🔧 trabajos no-proyecto + estados.
- **`_catalogo` reencuadrado** a "lo que NO es un proyecto" (entregas, cursos, traslados…): se **quitó el campo
  "Proyecto (opcional)"** del alta de trabajo (ya es redundante). Los trabajos viejos que enlazan a un PRJ
  siguen mostrándose (🔗, compat); solo no se crean nuevos así. Import `ui_common` quedó sin uso → eliminado.
- **Compat**: `asig` puede ser PRJ-#### (directo), TRB-#### (catálogo) o estado; el histórico no se migra.
  Plan-vs-real y "→ Abrir proyecto" del popover (v217) funcionan igual (proyecto_de(PRJ)=el propio PRJ).
Verificado: compila + import + AST (0 libres) + tests (color estable y de la paleta; el proyecto entra al
índice y resuelve etiqueta/color/proyecto_de; `_opciones` incluye el activo y excluye el completado).

## Planificación: tablero EDITABLE EN SITIO + cobertura del día (v217)
Petición del usuario ("el de planificación es muy importante"). Auditoría: la rejilla era **solo de
lectura/navegación** — para asignar había que bajar a "✏️ Editar la semana de una persona", elegir a UNO en
un desplegable y editar sus 5 días en un formulario **separado del tablero**, persona por persona (el cuello de
botella). Rediseño de `roster_ui.render_planificacion` / `_tablero_editable`:
- **Cada celda es ahora un `st.popover` coloreado** (antes `st.button`). Al tocarla se edita AHÍ MISMO:
  selectbox de asignación (`_opciones`) + nota + **"Aplicar a toda la semana"** + 💾 Guardar, y si el trabajo
  enlaza a un proyecto, **"→ Abrir proyecto"** dentro. Una celda vacía (**＋**) también asigna en sitio. Se
  **eliminó** el editor por-persona de abajo (`_editar_persona` borrada) — el tablero es el editor.
- ⚠️ **Verificado EN VIVO antes de construir** (lección v169): `st.popover` acepta `key` (streamlit 1.57;
  pin `>=1.39,<2` resuelve a la última), su *trigger* recibe la clase `.st-key-<key>` (`data-testid=
  stPopoverButton`) → `.st-key-<key> button{background}` lo colorea (rgb medido), y el CONTENIDO se portalea
  FUERA del contenedor keyed (`stPopoverBody`) → el CSS de color NO toca los botones del editor. Mini-app en
  preview + inspección del DOM.
- **`_guardar_celda(grupo,lunes,usuario,datos,dia,asig,nota,toda_semana)`**: reusa la semana actual de la
  persona (de `datos`, sin mutarla) y escribe 1 día o los 5 vía `R.guardar_persona` (que omite vacíos =
  limpiar). Probado: 1 día no toca los otros, toda-la-semana llena los 5, `datos` intacto.
- **Cobertura del día** (`_cobertura_hoy`): línea sobre el tablero — 🟢 en obra · ⚠️ N sin asignar (nombres) ·
  ⬜ OFF/Leave del día en vista (hoy si cae en la semana), para ver huecos de un vistazo.
- **Fix de navegación**: "→ Abrir proyecto" fijaba `_gruposec_pending` (nav VIEJA); ahora fija además
  `_prjsel_pending` + `_admin_nav_pending=("proyectos","📊 Proyectos")` (nav NUEVA del admin) — funciona en las
  dos shells. ⚠️ NO se metió doble columna en los expanders secundarios: `_catalogo` usa `st.columns` interno,
  meterlo en una columna sería anidación de columnas (la "doble anidación" que el usuario prohíbe).
Verificado: compila + import + AST (0 nombres libres en las 4 funciones) + lógica de guardado + popover en vivo.
El board del campo (`render_board_readonly`/`_grid_html`) NO se tocó. Confirmación final = Cloud (login+Sheets).

## Horas por usuario × proyecto: se surfacea lo que ya existía (v216)
Petición del usuario: "quiero saber cuántas horas ha gastado cada usuario en cada proyecto ¿dónde lo veo?; y en
cada proyecto, quiénes han trabajado y qué tiempo". Auditoría (auditar, no adivinar): **ambos datos ya existían,
solo no se mostraban del todo**. (Q2, por proyecto → quién) `expenses.labor_breakdown(pid,grupo)` (usuario·horas·
tarifa·costo) ya alimentaba 💰 Costos → "Mano de obra por persona", pero enmarcado como COSTO. (Q1, usuario × cada
proyecto) `timeclock.group_hours(grupo,days)` ya devuelve por persona un `por_proyecto{nombre:horas}`, pero
⏱ Horas solo mostraba el TOTAL "En proyectos" y el reparto agregado del grupo — nunca el split por persona.
Cambios: (1) **`_equipo_proyecto(pid,grupo)`** — bloque "👷 Quién ha trabajado aquí" (persona·horas + total),
colocado en la columna DER de 📊 Estado junto a las alarmas (aprovecha la doble columna v211); usa
`labor_breakdown` sin el costo, degrada limpio si expenses no está configurado. (2) En **`render_group_hours`**,
al final, matriz **"🔍 Horas por persona y proyecto"** (`st.dataframe`): filas = personas (reusa `_etiqueta`, que
desempata homónimos), columnas = proyectos, celda = `por_proyecto.get(proyecto)` (vacío si 0). Sin datos nuevos:
solo mostrar `por_proyecto`. Verificado: compila + import + AST (el único "libre" es `_etiqueta`, def anidada).

## Finanzas: doble columna + tablas activas (v215)
Apartado 💰 Finanzas (Gastos + Horas). **Gastos** (`render_group_expenses`): (1) "Reparto del costo del grupo"
| "Compras por categoría" en **doble columna** (antes apiladas y separadas — se movió categorías arriba y se
quitó su bloque de abajo); (2) tabla **"Proyectos con presupuesto" CLICKEABLE** (`st.dataframe(on_select=
"rerun")`) → seleccionar fila muestra botón "→ Abrir [proyecto]" → `_prjsel_pending`+`_ir_a("proyectos")`
(navegación por botón, no auto, para no re-navegar al volver). Reusa `f["id"]` de `group_expenses`. **Horas**
(`render_group_hours`): tabla por persona CLICKEABLE → botón "→ Abrir ficha de [persona]" → `gp_fichasel`+
`_ir_a("planificacion","👷 Usuarios")`. Verificado: compila + import + AST. Siguiente apartado: los placeholders
📦 Inventario y 👥 Contactos (a diseñar), o Fichaje/Herramientas.

## Agrupaciones: cartera clickeable (v214)
Mismo patrón que Proyectos v207 (las agrupaciones tenían tarjetas pasivas `_agrupaciones_html` + un selector
aparte "📊 Abrir agrupación" + otro selector de "🗑 Eliminar" abajo). Nuevo `_cartera_agrupaciones(ags,grupo)`:
tarjetas-botón (fondo=avance consolidado `grouping_progress`, borde=salud por gap del elevador más lento
`projections_by_group`, label 🗂 nombre·nº elev·%·⏰/⏩·🔔·🎯entrega, rejilla 2 col, ordenadas por urgencia).
Al tocar → `_admin_open_agr=aid` → abre el dashboard (`_dashboard_agrupacion`) directo + "← Volver" +
"🔧 Proyectos" (miembros) + "🗑 Eliminar" (movido aquí). Se quitaron los 2 selectores. ⚠️ NESTING (avisado por
el usuario): verificado que `_dashboard_agrupacion` y `_miembros_editor` NO tienen expanders internos → el
dashboard va directo y los 2 expanders ("Proyectos"/"Eliminar") son HERMANOS con contenido sin expanders → sin
doble anidación. Verificado: compila + import + AST. Con esto Proyectos (📊 + 🗂) queda completo.

## Costos: doble columna + recibos activos (v213)
Revisión de la sub-pestaña 💰 Costos (`render_expenses`). (1) **Doble columna**: "Reparto del costo" (mano de
obra vs compras) | "Compras por categoría" — los dos gráficos de barras cortos, antes apilados, ahora lado a
lado (helpers `_blq_reparto`/`_blq_categorias`; si solo hay uno → ancho completo). KPIs, titular+barra de
presupuesto, tabla de mano de obra y curva de gasto siguen a ancho completo. (2) **Recibos ACTIVOS**: antes
mostraban una TABLA redundante + botones de solo-descarga; ahora cada recibo es un BOTÓN (fecha·categoría·$·
proveedor·desc) → al tocar muestra la FOTO inline (`st.image` para png/jpg; los PDF → descarga). Toggle
`{key_prefix}_rcb`. Se quitó la tabla redundante. Verificado: compila + import + AST. Siguiente sub-pestaña:
📎 Archivos (archivos como tarjetas clickeables), luego ✏️ Datos.

## Fix: % de avance duplicado en el detalle (v212)
El usuario notó que el % de avance salía 2 veces al abrir un proyecto: la CABECERA de `_detalle_proyecto`
(`c1.metric("Avance", X%)` + `st.progress`) y otra vez la KPI "Avance real" de la pestaña 📊 Estado. Se quitó
la KPI "Avance real" de `_estado_section` (la cabecera es la fuente persistente, visible en todas las
sub-pestañas). Las KPIs de Estado quedan: Debería ir · Desvío · Situación · Fin proyectado (se leen contra el
avance de la cabecera). Compila + import.

## Proyectos #5: doble columna en el detalle (📊 Estado) (v211)
Aplicado [[feedback-doble-columna]] al detalle. `_estado_section` reordenado: se mueve el chequeo de cronograma
arriba, se calculan titular + KPIs, y se ponen en **doble columna [3,2]**: IZQ = "cómo va" (titular + tarjetas
KPI) · DER = 🔔 alarmas (`_alerts_section`, que usa columnas internas — OK, Streamlit permite 1 nivel de
anidado). A ANCHO COMPLETO abajo (sin tocar): el ritmo, "📌 Tocaba hoy | 🔧 En curso" (ya era 2 col), el
diagnóstico 🩺, próximo hito y el CRONOGRAMA/curva S (SVG ancho). Verificado: compila + import + AST. Con esto
Proyectos queda 5/5 (falta solo el buscador GLOBAL de la barra superior, que es su propia tanda). Próximo
apartado a revisar: Finanzas (o el que elija el usuario).

## Fix: "Nuevo proyecto" doblemente anidado (v210)
El usuario notó que "➕ Nuevo proyecto" quedaba doblemente anidado. Causa: `_nuevo_proyecto_form` YA tiene su
propio `st.expander("➕ Nuevo proyecto")` (línea 695, se pliega solo), pero en v207 lo envolví en OTRO expander
en `_panel_proyectos` → dos expanders "Nuevo proyecto" anidados. Además, dentro del 695 había un expander de
ubicación (v194) → expander-en-expander (Streamlit no lo permite). Fix: (1) `_panel_proyectos` llama
`_nuevo_proyecto_form(grupo, key="adm")` DIRECTO (sin envolver); (2) el selector de ubicación en
`_nuevo_proyecto_form` pasa a INLINE (st.markdown + `location_picker`, sin su propio expander). Queda un único
expander "Nuevo proyecto" sin nada anidado. LECCIÓN: `_nuevo_proyecto_form` ya se auto-pliega; no envolverlo.
Verificado: compila + import; grep confirma un solo expander "Nuevo proyecto" y sin el de ubicación.

## Proyectos #4: filtro rápido de la cartera (v209)
Arriba de la cartera (`_panel_proyectos`), en DOBLE columna [2,3]: **búsqueda** por nombre/cliente (`cart_q`,
filtra al escribir) + **chips** (`st.radio` horizontal `cart_filt`): Todos · 🔴 Retraso · 🟢 Adelanto ·
⏸ En pausa. Filtra `proys` → `_proys_f` (search en Nombre+Cliente; retraso=delays, adelanto=aheads, pausa=Estado)
y pasa la lista filtrada a `_cartera_clickeable`. Header "Cartera — N de M". Radio (no st.pills) por el pin
streamlit>=1.39. Verificado: compila + import + AST. Quedan de Proyectos: #4b enganchar el buscador GLOBAL de la
barra superior (su propia tanda), y #5 revisar el detalle + doble columna en 📊 Estado (ya aprobado).

## Estética de la cartera + rejilla 2 columnas (v208)
El usuario notó que las tarjetas-botón (v207) se veían MUY VACÍAS y "de lado a lado" (ancho completo, texto
centrado). Fix en `_cartera_clickeable`: (1) **rejilla de 2 columnas** (`st.columns(2)`, 2 tarjetas por fila)
→ más densa/dinámica (aplica [[feedback-doble-columna]]); (2) **texto a la izquierda** de verdad — el
`justify-content` del botón NO alinea el texto interno; hay que tocar `.st-key-cart_<i> button>div` y
`button p` (`text-align:left;width:100%`); (3) nombre en **negrita** (`**...**`, markdown en el label del
botón). Verificado: compila + import + AST. SIGUIENTE (ya aprobado por el usuario): doble columna en el DETALLE
del proyecto — pestaña 📊 Estado: "cómo va" (titular+KPIs+diagnóstico) | 🔔 alarmas, cronograma a ancho completo.

## Proyectos: cartera CLICKEABLE (v207) — revisión apartado por apartado
Empieza la mejora de cada apartado con la visión del usuario (activo/compacto/consistente). Proyectos, #1:
la cartera era PASIVA (`_portfolio_html`, tarjetas HTML) + un selector aparte "🔎 Abrir proyecto" para abrir —
justo lo que el usuario no quiere. Ahora `_panel_proyectos` usa `_cartera_clickeable(proys,horas,alarmas,
delays,aheads)`: cada proyecto es un BOTÓN (fondo=avance vía linear-gradient `.st-key-cart_<i>`, borde por
salud, label nombre·cliente·%·retraso/alarmas/horas, ordenado por urgencia). Al tocar → `_admin_open_proj=pid`
+ rerun → abre el detalle COMPLETO directo (decisión del usuario: no resumen). "← Volver a la cartera" cierra.
`_prjsel_pending` (de HOME "ver completo"/crear) ahora setea `_admin_open_proj`. Se eliminó el selector
redundante; el form "➕ Nuevo proyecto" quedó plegado en un expander (crear no es lo diario). `_portfolio_html`
se conserva (lo usa el panel del propietario). Verificado: compila + import + AST. Próximo en Proyectos:
#4 filtro/buscador; luego revisar el detalle (Estado/Datos/Costos/Archivos). Pendiente global: Finanzas,
Inventario, Contactos, buscador topbar, más alertas campana.

## Pin/lista del mapa → resumen del proyecto en HOME (v206)
Antes el pin del mapa (y la lista de la vista Proyectos) saltaban al proyecto COMPLETO fuera de HOME. Ahora
abren un RESUMEN en la columna derecha (pestaña Proyectos), sin salir de HOME; el "ver completo" es un paso más.
Nuevo `home_ui._resumen_proyecto_home(grupo, pid)`: nombre + barra de avance + estado(semáforo) + cliente +
retraso/adelanto + alarmas + fechas + paradas + asignados + ubicación (maps_link_md) + botón "→ Ver proyecto
completo" (que sí hace `_prjsel_pending`+`navegar`) + "← Volver a la lista". Pin (`_mapa_proyectos`) y cada
ítem de la lista (`_proyectos_home`) ahora dejan `_home_proj_sel=pid` (+ `home_right_view="📁 Proyectos"` el pin)
y `st.rerun()` — se quedan en HOME. `_proyectos_home` muestra el resumen si `_home_proj_sel`, si no la lista.
Verificado: compila + import + AST; maps.maps_link_md existe.

## Fix móvil: el gesto de retroceso cerraba la app (v205)
El usuario reportó que en el móvil el gesto/botón de retroceso CIERRA la app. Causa: Streamlit es una sola
página → la nav interna no crea entradas de historial → el back del sistema "no tiene página anterior" → sale.
Fix (el camino más fácil, en la web, sirve para navegador y app instalada): `home_ui._mobile_back_trap()`
(llamado al final de `render_topbar`) inyecta un `components.html` con JS que accede a `window.parent`
(mismo origen: el iframe de components tiene allow-same-origin) y: (1) hace `history.pushState` una entrada
'trampa' para que el back nunca salga; (2) en `popstate` (gesto atrás) re-apila y hace click en el botón
interno `.st-key-nav_back_btn button` (mi "← Atrás") → el back del móvil = el botón atrás. Guard `__copexBack`
para montarlo una sola vez. ⚠️ NO probable desde aquí (comportamiento móvil): validar en el teléfono. Plan B si
falla: interceptar el botón físico en el código Capacitor (`copex_mobile`). Verificado: compila + import.

## Botón "← Atrás" en la navegación del admin (v204)
Pedido del usuario: opción de volver atrás para moverse más rápido. Historial de secciones en session_state:
`_track_history(cur)` (en `sidebar_menu`, tras resolver la sección) apila la sección anterior en `_nav_hist`
(tope 20) salvo que el cambio fuera un 'atrás' (flag `_nav_back`, para no rebotar); `puede_atras()` /
`ir_atras()` (desapila y `navegar(dest)` con `_nav_back`). Botón **"←"** arriba-izquierda de la barra superior
(`render_topbar`, columnas [1,8,1]), `disabled` cuando no hay historial. Multi-nivel (atrás, atrás…). Funciona
con cualquier forma de navegar (menú, "→ Ir a", pines, etc.) porque el tracking es sobre el cambio de sección.
Solo nav del admin (donde está la barra superior). Verificado: compila + import + lógica del historial simulada
(home→proy→fin, atrás→proy, atrás→home, se desactiva).

## HOME: columna derecha compartida Agenda/Proyectos (v203)
Pedido del usuario: la columna derecha de HOME (antes fija en "Agenda de hoy") ahora tiene un TOGGLE arriba
(`st.radio` horizontal, hace de título): **📋 Agenda** | **📁 Proyectos** → cambio rápido sin salir de HOME.
Agenda = lo de antes. Nuevo `home_ui._proyectos_home(grupo)`: datos importantes de los proyectos ACTIVOS
(Planificado+En progreso) en compacto — cada proyecto es un BOTÓN cuyo FONDO se llena según el % de avance
(`linear-gradient` vía `.st-key-hp_<i>` CSS), borde izq por salud (rojo=retraso `delays_of_group`,
verde=adelanto `aheads_of_group`, azul=en curso), label con % + retraso/adelanto + alarmas
(`alerts.open_counts_all`). Ordenados por urgencia (retraso desc → alarmas desc → avance asc). Al tocar →
abre el proyecto (reusa `_prjsel_pending` + `navegar`). Verificado: compila + import + AST; funciones existen.

## Cronómetro de fichaje en el sidebar (v202)
Pedido del usuario: ver el tiempo en vivo de fichaje desde cualquier sección, no solo en ⏱ Fichaje. Nuevo
`timeclock_ui.render_sidebar_chrono()` + `_chrono_mini()` (versión compacta del `_chronometer` JS client-side):
lee `open_sessions(nombre,grupo,usuario)`; si hay jornada general y/o proyecto abiertos, muestra el/los
cronómetro(s) en vivo ("🕐 Jornada" / "🏗 [proyecto]") en el sidebar. SOLO cuando estás fichado (si no, no
muestra nada — decisión del usuario). Solo LECTURA (el fichaje se sigue gestionando en la pestaña). Llamado en
`app.py` en el bloque del sidebar, tras `render_user_bar`, para `_ROL in (administrador, campo)` (owner no ficha).
Verificado: compila + import + AST (_AZUL/_VERDE son constantes de módulo reales). Visual = Cloud.

## Ajustes estéticos: logo de login + zona negra superior (v201)
Dos pedidos del usuario. (1) El **logo del login** era muy grande → columnas `st.columns([1,1,1])` → `[2,1,2]`
en `render_login` (el logo ocupa el tercio central, con `use_container_width`; pasar a [2,1,2] lo deja en ~20%
del ancho = ~40% más pequeño). (2) En la vista del admin, encima del buscador había una **zona negra** (la
cabecera por defecto de Streamlit + el hueco superior; en modo oscuro se ve negra). Fix en `home_ui.render_topbar`
(solo admin): CSS `header[data-testid='stHeader']{background:transparent}` (no se OCULTA para no perder el botón
de desplegar el sidebar) + `div.block-container{padding-top:2.4rem}`. Compila + import; visual = Cloud.

## Elementos activos: nombres en indicadores + mapa y agenda clickeables (v200)
Extiende v199 con el principio "todo activo". (1) Indicadores del resumen ahora muestran **nombre visible**
("🔴 En retraso · 1"), en 3 filas de 3 (`st.columns(3)`) en vez de icono+número en fila de 9. (2) **Pines
del mapa clickeables** (`home_ui._mapa_proyectos`): `st_folium(..., returned_objects=["last_object_clicked"])`;
al tocar un pin se busca el proyecto por lat/lng, se deja `_prjsel_pending` (mecanismo que YA usaba el panel
para abrir un proyecto) y se `navegar("proyectos","📊 Proyectos")` → abre ese proyecto. Guard `_home_map_click`
para no re-navegar con clics viejos. Cada fila lleva `pid`. (3) **Agenda clickeable** (`_agenda_hoy`): cada
persona es un BOTÓN (borde izq = color de su trabajo, vía `.st-key-agper_<i>` CSS) → deja `gp_fichasel` =
"Nombre (usuario)" y `navegar("planificacion","👷 Usuarios")` → abre su ficha. Se quitó `_fila_agenda` (HTML
pasivo) y el helper `_esc` (sin uso). Verificado: compila + import + AST. `ui.elegir` es un selectbox simple
(pre-seleccionar con la key funciona). ⚠️ Confirmación visual = Cloud.

## Resumen y métricas ACTIVOS/clickeables (v199)
Principio del usuario: nada de elementos pasivos; todo clickeable → lleva a una sección o muestra el detalle.
Aplicado al Centro de control (HOME). Mecanismo de navegación programática en la nueva nav del admin:
`home_ui.navegar(seccion, sub_label)` / `_ir_a(...)` en projects_ui deja `_admin_nav_pending` en session_state;
`home_ui._aplicar_nav_pending()` (llamado al inicio de `sidebar_menu`, ANTES de instanciar los radios, regla
v111) escribe `admin_nav` y la sub-key (`adm_plan_sub`/`adm_proy_sub`/`adm_fin_sub`) → salta a la sección+sub.
`_resumen_del_dia` rehecho: los **9 indicadores son botones** (colorea cada uno por severidad con `.st-key-<key>`
CSS, v169; opción c del usuario) en una fila (`st.columns(9)`, icono+número, label en tooltip); al clickear uno
se guarda `_res_sel` y abajo se muestra su detalle (los "cuáles") + botón **"→ Ir a [sección]"** que navega
(retrasos/vencidos/por vencer/alarmas/near→Proyectos; sin contacto/credenciales→Planificación·Usuarios;
sin asignar→Proyectos; sobre presup.→Finanzas·Gastos). Las **3 métricas** (Activos/Avance/Horas) también son
botones que navegan (Proyectos/Proyectos/Finanzas·Horas). Se quitó la rejilla pasiva y el "Ver detalle" único.
Verificado: compila + import + AST; mapeo sección→label y sub-key correctos. ⚠️ Confirmación visual = Cloud
(el coloreado de botones por CSS y la navegación solo se ven en vivo).

## Fusión KPIs + resumen (v197)
El Centro de control (`render_group_header`) mostraba "En riesgo" y "Alarmas abiertas" como tarjetas KPI Y
otra vez como indicadores en el resumen (v196) → duplicado. Fusionado: arriba quedan SOLO las métricas del
portafolio (Proyectos activos · Avance promedio · Horas registradas); "En riesgo"(=retrasos) y "Alarmas"
viven únicamente en la rejilla de 9 indicadores del resumen. Un solo bloque coherente: métricas del grupo
arriba + "qué necesita atención" (estado + rejilla fija) abajo. Solo se quitaron 2 tarjetas del display
(`_kpis` sigue calculando todo). Compila + import.

## Resumen del día con ESTRUCTURA FIJA (v196)
El resumen (en HOME, dentro de `render_group_header` → `_resumen_del_dia`) cambiaba de forma cada día: los
chips solo aparecían si había algo (3 un día, 6 otro), y el briefing IA es texto libre variable. Rediseño
(opción del usuario "b"): (1) **línea de estado** fija (🟢 en orden / 🟡 N pendientes / 🔴 N urgentes;
urgentes = retrasos+vencidos+alarmas). (2) **rejilla FIJA de 9 indicadores** en 3 columnas (📁 Proyectos:
retraso/vencidos/por vencer · 👥 Equipo: sin asignar/sin contacto/credenciales · 🔧 Obra-$: alarmas/near
miss/sobre presup.), SIEMPRE los mismos en el mismo orden, con su número (0 en gris, >0 rojo si urgente /
ámbar si no) — helper `_ind_card`. (3) **desplegable "📋 Ver detalle"** con los "cuáles". (4) el **briefing
IA en su propio desplegable colapsado "💬 Lectura del asistente" y BAJO DEMANDA** (botón ✨ Generar; antes se
generaba automático en cada carga → ahora no gasta IA salvo que se pida). Verificado: compila + import + AST;
lógica de indicadores/colores probada con digest simulado. group_digest da: retrasos/vencidos/por_vencer
[{nombre,dias/fin}], alarmas [{nombre,n}], near_miss [{proyecto,fecha}], sin_asignar [{nombre}],
campo_sin_contacto [usuario], cred_venc [{tipo,usuario,dias}], sobre_presupuesto [.].

## Fix: el mapa de HOME no mostraba proyectos recién creados (v195)
El usuario creó un proyecto y no aparecía en el mapa. Causa: `_mapa_proyectos` filtraba `Estado=="En progreso"`,
pero un proyecto recién creado tiene avance 0 → `derive_estado(0)`="Planificado" → quedaba EXCLUIDO tuviera pin
o no. Fix: el filtro ahora incluye los **activos** = ("Planificado","En progreso"); etiqueta "🗺 Proyectos
activos" (antes "en ejecución"). Verificado: compila + import; derive_estado(0)=Planificado (ahora incluido).

## Pin de ubicación también al CREAR el proyecto (v194)
Completa v193. NOTA: desde v135 el Survey ya NO crea proyectos (solo guarda en uno existente); el ÚNICO flujo
de creación es el formulario "➕ Nuevo proyecto" (`projects_ui._nuevo_proyecto_form`, única llamada a
`create_project`). Cambios: (1) `create_project` acepta `lat=""`,`lng=""` y su fila posicional se extendió con
`""`(PlanoJSON, que la fila OMITÍA y se llena aparte) + lat + lng → 27 valores = 27 headers. (2) el formulario
"➕ Nuevo proyecto" tiene el mismo expander "🗺 Ubicación en el mapa" con `location_ui.location_picker`
(fuera del st.form) y pasa lat/lng a `create_project`. Así el proyecto NACE con coordenadas. Verificado:
compila + import + AST; fila = 27 = headers; create_project acepta lat/lng. Con esto, ubicación con pin queda
completa (crear y editar).

## Ubicación de proyecto con búsqueda + pin en mapa (v193)
Antes el mapa de HOME geocodificaba el texto `Ubicacion` en cada dibujo (frágil, impreciso). Ahora se
GUARDAN coordenadas por proyecto. Cambios: (1) requirements +`folium`+`streamlit-folium` (sin API key,
OpenStreetMap; import perezoso con fallback). (2) `PROJECTS_HEADERS` +`Lat`,`Lng` (al final, migran solas).
(3) NUEVO `core/location_ui.py`: `location_picker(key,lat,lng,direccion)` = caja "buscar dirección"
(Nominatim) que centra el mapa + clic en el mapa para fijar/mover el pin (guarda el punto en session_state,
solo un clic NUEVO mueve el pin vía `_lastclick`); `geocode` (cacheado), `to_float`. Va FUERA de `st.form`.
(4) `projects_ui._detalle_proyecto`: expander "🗺 Ubicación en el mapa" con el picker ARRIBA del form de editar
(patrón asignados) + guarda Lat/Lng en `update_project`. (5) `home_ui._mapa_proyectos`: lee Lat/Lng guardadas
(respaldo: geocode del texto para proyectos viejos), mapa folium con pines etiquetados (popup=nombre,
returned_objects=[] para no re-renderizar); quitado el `_geocode` local duplicado. Verificado: compila +
import + AST; Lat/Lng en headers y _PCOL. ⚠️ RIESGO: dependencia nueva en el Cloud (vigilar el build). v194
pendiente: integrar el picker en CREAR proyecto (Survey → Guardar como proyecto y el "➕ Nuevo proyecto").

## Centro de control reubicado en HOME (v192)
Auditoría antes→ahora: 13/13 apartados reubicados; lo ÚNICO sin sitio era el "Centro de control del grupo"
(`projects_ui.render_group_header`: banda 🏢 grupo + KPIs [activos·avance·en riesgo·alarmas·horas] + resumen
del día con chips de pendientes y briefing IA), que salía arriba de "Mi grupo". Reubicado al tope de
`home_ui.render_home` (nueva landing), reusando la función tal cual, arriba del mapa y la agenda. Se quitó el
título "🏠 Home · fecha" redundante (el banner del grupo hace de cabecera). Verificado: compila + import.
Sigue pendiente: los saltos automáticos (`_nav_pending`/`_gruposec_pending`) no aplican en la nav del admin.

## Integración del contenido en la nueva navegación (v191)
Se cablearon los apartados de la nueva nav del admin a las funciones que YA existen (reconexión, no reescritura).
Mapeo (decisiones del usuario): **Fichaje**→`timeclock_ui.render_timeclock_tab`; **Planificación**→sub-menú
[📋 Tablero=`roster_ui.render_planificacion` · 👷 Usuarios=`auth_ui._grupo_usuarios`] (la gestión de usuarios
vive AQUÍ, no en Contactos); **Proyectos**→[📊 `PU._panel_proyectos` · 🗂 `PU._panel_agrupaciones`];
**Finanzas**→[💰 `PU.render_group_expenses` · ⏱ `PU.render_group_hours`]; **Herramientas**→sub-selector de 6
[Survey=`survey_ui.render_survey_tab(rol,grupo)` · Plomada · Rieles · Buffers · Belting · Pre-Start];
**Inventario** y **Contactos**→placeholders (nuevos, a desarrollar). Helper `_subnav(titulo,opciones,key)` =
sub-menú horizontal. `init_state()` corre incondicional en app.py:100, así que el Survey funciona desde aquí.
Verificado: compila + import + las 13 funciones existen como atributos. Confirmación visual = Cloud.
PENDIENTE/known: el `_nav_pending` (navegar tras crear proyecto desde el Survey) apunta al radio viejo — no
aplica en la nav del admin; revisar esos flujos "navegar tras acción" cuando se validen. Diseñar Inventario y
Contactos. Buscador aún sin backend.

## Nueva navegación del admin: shell + HOME (v190)
Rediseño de la UX de navegación (pedido del usuario), **solo rol administrador** por ahora (owner/campo
siguen con la nav vieja). Nuevo `core/home_ui.py`:
- **Menú lateral de iconos** (en el sidebar, `sidebar_menu()`): 🏠 Home · ⏱ Fichaje · 📅 Planificación ·
  📁 Proyectos · 💰 Finanzas · 📦 Inventario · 🛠 Herramientas · 👥 Contactos. (Decisión del usuario:
  Fichaje = icono propio; Pre-Start = una herramienta más dentro de Herramientas.)
- **Barra superior** (`render_topbar`): buscador (placeholder, aún sin backend) + **campana** (popover)
  con alertas — de momento credenciales por vencer/vencidas (`credentials.expiring`); más fuentes luego.
- **HOME real** (`render_home`, doble columna): IZQ mapa de proyectos "En progreso" (`st.map`, sin API key;
  geocodifica `Ubicacion` de texto con Nominatim/OSM, cacheado 1 día; los sin ubicación se listan aparte);
  DER agenda de hoy desde el roster (`get_semana`/`celda`/`etiqueta_de`/`color_de`, por persona de campo,
  con chip de color + nota + proyecto enlazado + resumen asignados/OFF/leave/sin asignar).
- Los otros 6 apartados son **placeholders** ("en construcción") — decisión del usuario, se integran uno a uno.
Wiring en `app.py`: en el sidebar, si `_ROL=="administrador"` se renderiza `sidebar_menu()`; y antes de la
cabecera principal, un branch admin llama `render_topbar`+`render_admin_content` y hace `st.stop()` (salta la
cabecera y el radio viejo). Verificado: compila + import + AST sin nombres libres. **Confirmación visual =
Cloud** (necesita login + Sheets; no renderizable local). PENDIENTE/decisiones futuras: Google Maps vs OSM,
campo de coordenadas por proyecto, qué busca el buscador, más fuentes de alertas, e integrar los placeholders.

## Formulario de credenciales sin clutter (v189)
Último ítem de la revisión de credenciales. En "➕ Agregar credencial", "Especifica (Otro)" y "Clase
(licencia)" se mostraban SIEMPRE aunque no aplicaran; dentro de un `st.form` no se puede condicionar (no hay
rerun hasta el submit). Fix: se sacó el selectbox **Tipo** FUERA del form → al cambiarlo hay rerun y se
muestran solo los campos que aplican: "Especifica el tipo" solo si Tipo="Otro"; "Clase" solo si
Tipo="Driver License" (si no, Número a ancho completo, sin columna vacía). El resto sigue dentro del form.
El Tipo queda seleccionado tras agregar (cómodo para varias del mismo tipo). Backend intacto. Compila +
import + AST OK. Con esto queda CERRADA la revisión de acceso+credenciales (login persistente v188 confirmado
por el usuario en el Cloud). Solo queda anotado como futuro: mensajes de login (enumeración de usuarios) y
la Opción B de `notify_expiring` (job programado).

## Fix login persistente al refrescar (v188)
El usuario confirmó en el Cloud que lo ÚNICO que falló del lote fue **mantener la sesión al refrescar** (F5
deslogueaba) — justo lo que quedó marcado para confirmar en vivo. Causa raíz: el enfoque v174→v187
BLOQUEABA con `time.sleep(0.2)` + `st.rerun()` forzado hasta 3 veces y se rendía (`_cookie_done=True`); pero
el componente `extra-streamlit-components` entrega la cookie en un rerun NATURAL (mensaje del navegador por
WebSocket) que durante el `sleep` no se procesa → llegaba SIEMPRE después de rendirse. Además `_mgr()` creaba
un CookieManager nuevo en cada llamada (re-montaba el componente). Fix: (1) `session_cookie._manager()` crea
el CookieManager UNA vez por sesión y lo guarda en `session_state` (`_cookie_mgr`); (2) `load()` usa
`get_all()`; (3) `render_login` ya NO bloquea ni reintenta — solo renderiza el componente y deja que dispare
su propio rerun (se ve el login un instante y al llegar la cookie se restaura sola); (4) tras logout se marca
`_no_cookie_restore` para no re-restaurar la sesión recién cerrada (evita la carrera con el delete de la
cookie). Verificado: compila + import + sin restos de `_cookie_done/_cookie_waits`. Confirmación definitiva =
F5 en el Cloud (no reproducible localmente: necesita el runtime + el navegador).

## Avisos de vencimiento desacoplados del panel (v187)
Antes `notify_expiring` se disparaba SOLO al abrir 🔧 Usuarios de campo (`_grupo_usuarios`), 1×/sesión/grupo
— frágil: si nadie abría ese panel, o el grupo no tenía admin, los vencimientos no se avisaban nunca.
Investigación: NO hay scheduler en el repo (ni cron, ni st_autorefresh; `ping.yml` es solo `on: push`);
el digest (`admin_digest`) solo arma datos para mostrar, no notifica; `notify` envía por Gmail SMTP + Telegram
leyendo `st.secrets`. Elegida la **Opción A** (pragmática, sin infra): el disparo se movió al **login**
(`app.py`, tras el heartbeat): si `_ROL` es administrador/propietario, corre `notify_expiring` — el admin
sobre su grupo, el propietario sobre todos —, deduplicado por día en `session_state`
(`_credaviso_{grupo}_{hoy}`) y por 25 d en la hoja (`UltimoAviso`), envuelto en try para no bloquear la
entrada. Quitado el disparo de `_grupo_usuarios`. Opción B (job programado con GitHub Action `on: schedule`
+ runner headless) queda ANOTADA como mejora futura (requiere duplicar secretos en GitHub y una capa de
compatibilidad porque el código lee `st.secrets`, que no existe fuera de Streamlit). Verificado: compila +
import; el único `_credaviso` restante está en app.py.

## KPIs de credenciales + descargas agrupadas (v186)
Estético de `render_credenciales`: arriba de la tabla, fila de `st.metric` (Credenciales · 🟢 Vigentes ·
🟡 Por vencer · 🔴 Vencidas) calculada con `status()` — mismo estilo que la pestaña "Su trabajo" de la ficha;
sirve al admin y al propio usuario en "Mis credenciales". Los botones de descarga (antes apilados sueltos
bajo la tabla) ahora van en un expander "⬇️ Documentos (n)". Backend intacto. Compila + import + AST OK.
Pendientes de la revisión de credenciales (NO hechos, dejados aparte a propósito): desacoplar
`notify_expiring` del render (hoy es el ÚNICO disparador de avisos → mover a un digest programado, verificar
scheduler antes); clutter del form (Clase/"Otro" siempre visibles → están dentro de `st.form`, no se puede
ocultar condicional sin sacarlo del form); unificar mensajes de login (enumeración de usuarios).

## Fechas de credenciales con calendario (v185)
Hallazgo de la revisión: las fechas de Emisión/Vencimiento eran **texto libre** "YYYY-MM-DD" sin validar;
un typo → `_parse` la ignora en silencio → esa credencial **nunca dispara la alerta de vencimiento** y sale
"—". Fix: helper `_fecha_input(col, label, valor_actual="", *, key)` que usa `st.date_input` (calendario,
opcional con `value=None`, rango 2000–2100), precarga el valor existente parseándolo con `credentials._parse`
(si estaba mal escrito queda vacío para corregir) y **devuelve siempre ISO `YYYY-MM-DD`** — justo lo que leen
`_parse`/`status`/alertas, así un typo ya no rompe el aviso. Aplicado a los formularios Agregar (Emisión +
Vencimiento) y Editar (Vencimiento) de `render_credenciales`. De paso, el form de **Editar** ahora incluye el
**ID de la credencial en las keys** (`_enum_{id}`, `_even_{id}`, `_enota_{id}`): antes tenían key fija y al
cambiar de credencial NO se refrescaban los campos (bug de precarga preexistente). Backend `credentials.py`
NO se toca; las credenciales ya guardadas se siguen leyendo igual (se re-guardan en ISO solo al editarlas).
Verificado: date→ISO→`status()` cierra; datos viejos DD/MM/YYYY precargan; basura/fuera de rango → vacío.
Pendientes de la revisión de credenciales: KPIs (vigentes/por vencer/vencidas), desacoplar `notify_expiring`
del render, unificar mensajes de login, clutter del form (Clase/"Otro" siempre visibles), botones de descarga.

## Panel del propietario unificado a la ficha 360° (v184)
Revisión estético/integración del bloque acceso+credenciales. Hallazgo gordo: el **administrador**
gestiona cada persona con la **ficha 360°** (`_ficha_usuario`: pestañas Acceso/Contacto/Credenciales/
Su trabajo/eliminar, una sola selección), pero el **propietario** (`_owner_usuarios`) seguía con el
estilo viejo disperso (elegir a la persona en 3 desplegables: modificar / contacto / credenciales).
La mejora v153 nunca se aplicó al panel del propietario. Unificado:
- `_ficha_usuario(u, grupo, owner=False, sel_key="gp_fichasel")`: nuevo modo `owner` que, en la pestaña
  🔑 Acceso, añade reasignar **Rol** y **Grupo** (lo que solo tenía el propietario). El admin la ve igual.
  `sel_key` parametriza la clave del selector externo a limpiar al eliminar.
- `_owner_usuarios` rehecho: tabla-resumen (con columna Contacto ✅/⚠️ + aviso de faltantes) → "➕ Crear
  usuario" (rol+grupo) → "👤 Gestionar un usuario" = filtro por grupo + selector → `_ficha_usuario(..., owner=True)`.
  Desaparecen los 3 desplegables sueltos ("Modificar usuario", "Contacto de campo", "Credenciales").
- Borrado el código muerto: `_field_contact_ui` y `_USER_COLS` (ya no se usan).
NO se tocó: `auth.py` (backend), el panel del administrador, la creación de usuarios ni las credenciales.
Verificado: compila + import + AST sin nombres libres; el admin sigue llamando `_ficha_usuario` con los
defaults. Confirmación visual = en el Cloud (necesita la hoja real). Pendientes de la revisión (no hechos
aún): fechas de credenciales con `date_input`+validación, KPIs de credenciales, desacoplar `notify_expiring`
del render, unificar mensajes de login.

## Belting: revisión técnico/estético/integración + diagrama replanteado (v183)
Última de las 5 herramientas técnicas. Tres arreglos:
- **Integración:** el proyecto se conocía (`_prj`) pero no iba al diagrama ni al PDF. Fix:
  `belting_svg(..., proyecto="")` lo dibuja arriba-derecha + "Proyecto" al `meta` del PDF.
- **Estético:** resultados iban directo a la tabla → añadidas tarjetas KPI (`_kpi`): HQ · HGP · nº elevadores.
- **Técnico/representación (como buffers):** el diagrama ponía la cabina SIEMPRE por debajo del FFL en
  posición fija, aunque DSTS fuera negativo (cabina por ENCIMA) o distinto entre elevadores —
  contradecía a la tabla. `belting_svg` reescrito: **FFL = línea de referencia común** y cada cabina
  a su **DSTS con signo** (debajo si +, encima si −), a escala ampliada común para comparar; valor
  DSTS con signo al pie (no se solapa con la cabina). `compute_belting` NO cambia.
Verificado renderizado en navegador (DSTS +40 debajo / 0 en FFL / −20 encima), sin `<defs>/<marker>`.
Con esto quedan revisadas las 5 técnicas: plomado (v179), rieles (v180), buffers (v181-182), belting (v183).

## Corte de buffers: diagrama replanteado (v182)
El usuario notó que el diagrama **no representaba bien la geometría**: HKP/HKPR no son alturas, son la
**holgura** (distancia) entre el **sticker de la cabina** y el **borde superior del buffer** —dos elementos
que no se tocan—; HKP de diseño (plano), HKPR medida. **Cortar el buffer baja su borde → agranda la
holgura**; el corte = HKP − HKPR es la rebanada que se quita del borde para pasar de HKPR a HKP.
`buffer_cut_svg` reescrito: sticker (barra fija arriba) + línea HKP común (borde superior de diseño) +
por buffer el borde real (a HKPR) y, si HKPR<HKP, la rebanada roja borde-real→línea-HKP = lo que se corta.
Casos: corte>0 (rebanada roja), corte≈0 ("sin corte" verde en la línea), HKPR>HKP ("revisar" ámbar, borde
bajo la línea). Holgura sticker↔buffer con "≈" (no a escala); corte a escala ampliada. `compute_buffer_cut`
NO cambia. Verificado renderizado en navegador (los 3 casos correctos), sin `<defs>/<marker>`, proyecto
arriba-derecha.

## Corte de buffers: revisión técnico/estético/integración (v181)
Revisión de 🛡 Corte de buffers — **idéntica a rieles v180** (ya era por buffer, diagrama v129, integración
compartida). Dos arreglos:
- **Integración:** el proyecto se conocía (`_prj`) pero no iba al diagrama ni al PDF. Fix:
  `buffer_cut_svg(..., proyecto="")` lo dibuja arriba-derecha + "Proyecto" al `meta` del PDF.
- **Estético:** `st.success("HKP = …")` plano → tarjetas KPI (`_kpi`): HKP · nº buffers · nº a revisar
  (rojo si hay cortes negativos).
- **Técnico:** sin gaps (por buffer + diagrama + reabrir/guardar-auto ya estaban).
Verificado: el diagrama muestra el proyecto, sin proyecto no rompe, escape OK, sin `<defs>/<marker>`;
compute_buffer_cut intacto (warn cuando HKPR>HKP). Compila + import.

## Corte de rieles: revisión técnico/estético/integración (v180)
Revisión dedicada de ✂️ Corte de rieles (ya estaba en buena forma: es por elevador desde v52, diagramas
rehechos v177/v178, e integración compartida). Salió ligera — dos arreglos.
### ⚠️ Integración (el MISMO fallo que plomado v179)
El proyecto se conocía (`_prj` del selector) pero **no iba al diagrama ni al PDF**: `rail_cut_svg` no
tenía `proyecto` y el `meta` del PDF no lo incluía. El corte iba a obra sin identificar el proyecto.
Fix: `rail_cut_svg(..., proyecto="")` dibuja el nombre arriba-derecha (ambos casos) + "Proyecto" al
`meta` del PDF (Caso 1 y 2).
### Estético
`st.success("A = …")` / `st.success("Sub-caso: …")` planos → **tarjetas KPI** (`_kpi`): Caso 1 = A · LFKK
· LFGK · nº elevadores; Caso 2 = fórmula · LFKK · LFGK · nº elevadores (+ el sub-caso como caption).
### Técnico: sin gaps
Ya es por elevador (matriz L / matriz RZ·RO·RF·RB); diagramas ya corregidos; reabrir cálculo y
guardar-auto-al-fichaje (v176) ya están. No se tocó nada técnico.
### Verificacion
Ambos diagramas muestran el proyecto ("North Syd"), sin proyecto no rompe, escape de `& < >` OK, sin
`<defs>/<marker>` (svglib-compat). Compila + import. Los números (compute_case1/2) intactos.

## Plomadas: revisión técnico/estético/integración — por elevador (v179)
Revisión dedicada de 🔩 Plomadas (la única herramienta técnica sin un pase con esa dinámica; tenía trabajo
de dominio v57-64 y el CAD v123, pero no la revisión). Tres hallazgos.
### ⚠️ Integración (fallo real): el nombre del proyecto se perdía
`plumb_ui` tenía **`_pr_ = ""` hardcodeado** y con eso dibujaba los 4 SVG y armaba el PDF — el replanteo
iba a obra SIN identificar el proyecto/elevador, aunque `_prj` estaba disponible del selector. Otro
"dato disponible que no se usa". Fix: `_pr_base` = nombre del proyecto → a los diagramas (cajetín) y al
`meta` del PDF.
### Estético: lenguaje inconsistente
- DBP/DBPW/RW eran `st.metric` planos → **tarjetas KPI** (`_kpi`, como v143).
- El encaje BSR<BS era un muro de números crudos (LIMIT_ZB/OB/sacrificios) → contado como ACCIÓN
  ("acerca X mm al lado Z"; abs para no mostrar "-3") con los umbrales internos en un desplegable.
### Técnico/dominio: POR ELEVADOR (decisión del usuario)
Rieles/buffers/belting son por elevador; plomadas era un solo cálculo. **Insight clave**: la PLANTILLA
(DBP, DBPW, RW, d1, d2) depende de BKS/RAIL/TKSW/LengthTemplate → es **la misma para todo el shaft** (una
plantilla). Lo que varía por elevador es el **BSR** (ancho real medido en cada hueco) → cambia el
**encaje** y la **verificación** (di/dd). Rediseño:
- Entradas compartidas del shaft (una vez) + **matriz BSR por elevador** (como la L de rieles).
- `compute_plumb` por cada BSR. La plantilla en tarjetas KPI **una vez**; una **tabla por elevador**
  (BSR · encaje · di · dd · cierre `di+DBP+dd=BSR`); un selector para ver el diagrama de cada elevador.
- PDF con el proyecto + la plantilla + la tabla por elevador + planta/ficha de cada uno.
- `plumb.py` NO se tocó (compute y SVG ya trabajan por-resultado); solo se reescribió `render_plumb_tab`.
### Verificacion
La plantilla (DBP/DBPW/RW/d1/d2) sale **IDÉNTICA** con 3 BSR distintos (1420/1426/1432) ✓; el encaje y
di/dd cambian y **cierre = BSR** en los 3 (identidad di+DBP+dd=BSR) ✓; 0 nombres libres; 0 restos del
estado viejo (plb_res/plb_bsr single → plb_res_multi/plb_bsr_df); compila + import.

## Corte de rieles: sin orden inventado (Caso 1) + esquema de rieles (Caso 2) (v178)
Dos apuntes del usuario sobre `rail_cut_svg`:
### Caso 1: "¿de dónde sacas el orden de los rieles?"
Tenía razón: la app solo tiene los **conteos** (n2500, n5000), NO el orden. El dibujo apilaba los 5000
abajo y los 2500 arriba — una **secuencia inventada**. `A = n2500·2500 + n5000·5000` es solo un total.
Fix: la pila estándar A se dibuja como **UN bloque** (altura = A, etiqueta "A · pila estándar"), sin
inventar la secuencia. La composición sigue en el subtítulo. El resto del Caso 1 (columna requerida,
corte al pie = primer riel, v177) intacto.
### Caso 2: "se ve poco profesional" → esquema de rieles (decisión del usuario)
El Caso 2 no tiene longitudes (RZ/RO/RF/RB se miden en obra), así que las barras comparativas no decían
mucho. Se rehízo como **esquema de rieles**: por elevador, 4 rieles agrupados —**cabina** (RZ, RO, azul)
y **contrapeso** (RF, RB, teal)— cada uno con una **banda de corte arriba** (el último riel instalado, el
que se corta) + línea de corte punteada + el valor del corte encima + etiqueta al pie. ⚠️ Las alturas son
**ILUSTRATIVAS** (uniformes, no a escala) — se declara en el subtítulo, porque el Caso 2 no tiene
longitudes reales.
### Verificacion (geometría medida en el SVG)
Caso 1: **1 solo bloque** de pila en x=30 (antes n2500+n5000 rects) ✓. Caso 2: 8 cuerpos de riel + 8
bandas de corte para 2 elevadores ✓, encabezados Cabina/Contrapeso, leyenda por color. Ambos SVG sin
`<defs>/<marker>` (svglib-compat). Compila. Los números (compute_case1/2) NO cambian, solo el dibujo.
⚠️ Se corrigió un error propio: `\'` dentro de un f-string de comillas simples (SyntaxError) → variables.

## Corte de rieles Caso 1: el corte va en el PRIMER riel (abajo) (v177)
Bug reportado: "en el Caso 1 se corta el primer riel instalado (el de más abajo), pero en el dibujo sale
como si se cortara el de arriba". Cierto: `rail_cut_svg` dibuja las columnas RC/RCW **desde la base
(piso) hacia arriba**, pero pintaba el corte ARRIBA (entre la punta de la barra y la línea A).
### Fix (solo el dibujo del Caso 1; los números no cambian)
- El corte se marca **AL PIE de la columna** (borde inferior en la línea de piso), que es donde está el
  primer riel instalado. Color por signo: **rojo = recorta** (corte<0) / **verde = añade** (corte>0).
- Se añadió una **línea de piso** (`base`) para que se vea dónde se apoya el primer riel.
- Leyenda reescrita: "recorta / añade al 1er riel · el corte va en el riel de ABAJO". Cierra el pendiente
  de v130 sobre la dirección del corte.
### Verificacion (geometría medida en el SVG, no a ojo — lección de v121)
Caso 1 con 2 elevadores (uno recorta CutRC=-1985/-2207, otro añade +515/+293): los 4 rects de corte
tienen su **borde inferior en el piso (y=270)** ✓; línea de piso en y=270; rojo para recortes, verde para
añadidos; SVG sin `<defs>/<marker>` (svglib-compat). Compila. Caso 2 (barras) intacto.

## Guardar un cálculo: el campo va SOLO a su proyecto del fichaje (v176)
Peticion del usuario: "al usar las herramientas, al final me da una lista de a cuál proyecto agregar el
resultado; no debe ser así: si ya fiché a un proyecto, se debería guardar ahí automáticamente".
### `tool_save_ui.render_guardar` — destino automático para el campo
Las 4 herramientas de cálculo (plomada/rieles/buffers/belting) comparten este bloque. Pedía el proyecto
en un `selectbox` para TODOS los roles. Ahora, para el rol **campo**:
- Si tiene **fichaje abierto** a un proyecto → destino AUTOMÁTICO = ese proyecto: "💾 Se guardará en X —
  donde fichaste" + un botón (un toque). Resuelve **ID primero, nombre de respaldo** (v145). Mismo
  criterio que el plano (v137), Mis proyectos (v138) y el Pre-Start (v170).
- Salida de emergencia: un expander plegado "¿Es de otro proyecto?" con la lista, por si el cálculo es
  de otra obra.
- Campo SIN fichar → cae a la lista (tiene que elegir). Admin/propietario → la lista (trabajan varias obras).
La lógica de guardado se extrajo a un helper interno `_guardar(prj)` para no duplicar `toolruns.registrar`.
### Verificacion
Matching probado: por ID (PRJ-0002→North), por nombre case-insensitive (Prueba1→prueba1), sin fichaje→
None (cae a la lista). `render_guardar` 0 nombres libres, compila + import. `registrar` intacto.

## El plano alimenta las 5 herramientas, mostradas POR IGUAL (v175)
Peticion del usuario: "al cargar el plano solo me muestra que leyo 17 parametros (los del survey); las
otras herramientas tecnicas las maneja como independientes cuando todas son de igual importancia".
### ⚠️ Era DISPLAY, no extraccion (verificado con evidencia)
`extraer_todo` YA lee todo para las 5 herramientas. Probado sobre los 2 planos REALES de Downloads:
NORTH SYD y AGECARE dan **17/17 params + NS + riel(+altura) + HQ + HGP + HKP + LFKK + LFGK, faltan=0**.
El problema era el framing: el mensaje al cargar lideraba con "17 parametros" (`plan_data.resumen`) y el
detalle mostraba tarjetas sueltas (HKP, HQ, LFKK…) sin decir a que herramienta alimenta cada una.
### `plan_data.por_herramienta(datos)` — el plano por herramienta
Invierte el mapa `USA` (dato→herramienta) para agrupar POR herramienta: devuelve, para cada una de las 5,
`[(label, valor|None)]`. `projects_ui._plano_herramientas_html` lo pinta como tabla (chip verde con el
valor / chip rojo "⚠️ falta" por herramienta). Se muestra AL CARGAR (nuevo proyecto + 📐 Datos del plano)
y en el detalle del proyecto, reemplazando las tarjetas sueltas y el mensaje de "17 parametros":
`📐 Survey (17/17 · NS · Riel) · 🔩 Plomadas (params · RAIL) · ✂️ Rieles (LFKK · LFGK) · 🛡 Buffers (HKP)
· 🎗 Belting (HQ · HGP)`. Floats redondos se muestran como enteros (2915.0→2915).
### Verificacion
`por_herramienta` con datos completos → las 5 con sus valores; con datos parciales → cada herramienta
marca lo que le falta. HTML valido. `resumen()` se conserva (aun la usa `plan_ui.py`). Compila + import.

## Fix: refrescar la página deslogueaba (v174)
Peticion del usuario: "cuando refresco se cierra la sesion". El login persistente por cookie existe
desde v107, pero no restauraba tras un refresco.
### Raiz: el componente de cookies + un gate de UN solo intento
`extra-streamlit-components` `CookieManager.get()` devuelve **None en el PRIMER run** tras un refresco
(el componente aún no recibió las cookies del navegador; las reporta en un rerun posterior). Pero
`render_login` marcaba `_cookie_tried=True` en ese primer intento y **nunca reintentaba** → siempre
caía al login.
### Fix
Se REINTENTA la lectura de la cookie unos pocos reruns (`_cookie_waits < 3`, con `time.sleep(0.2)`) antes
de rendirse, dándole al componente tiempo de reportar. Cuando la cookie llega, `auth.validate_session`
(que solo compara el token con el de la hoja Login, sin exigir heartbeat) restaura la sesión. El
heartbeat de sesión única no re-desloguea: el restore deja `_hb_last` fresco y el token no cambió.
### Verificacion
Compila + import; 0 `_cookie_tried` colgando (solo en un comentario). ⚠️ El timing del componente de
cookies solo se prueba de verdad en el navegador: PENDIENTE confirmar en el Cloud que refrescar YA no
desloguea. Si sigue fallando, plan B: montar un único CookieManager al inicio del app o cambiar el
mecanismo de persistencia.

## Zona horaria POR GRUPO — hora local correcta multi-país (v173)
Peticion del usuario: "los registros no coinciden con mi zona horaria" + "¿y si alguien usa la app en
otro país?". Raiz: **Streamlit Cloud corre en UTC**, asi que cada `datetime.now()`/`date.today()`
grababa en UTC (~10-11 h corrido para Australia). Y el proceso es COMPARTIDO por todos los usuarios, asi
que fijar una zona global (`tzset`) no sirve para multi-país (todos quedarian en una sola zona).
### `core/clock.py` — hora local resuelta POR GRUPO
- `clock.now(grupo=None)` / `clock.today(grupo=None)` → datetime/date NAIVE en la zona del grupo. Sin
  `grupo`, la toma del **grupo del usuario en sesión** (`session_state.auth.grupo`). Usa `zoneinfo`
  (per-sesión, seguro con usuarios concurrentes en distintos países — NO `tzset` global).
- La zona de cada grupo se guarda en **`Grupos.Zona`** (nueva columna, migra sola via `get_sheet`).
  `auth.group_timezone(grupo)` (lectura cacheada) + `auth.set_group_timezone`. Sin zona → `DEFAULT_TZ`
  = **Australia/Sydney** (por eso el grupo actual ya queda bien sin configurar nada).
- El propietario fija la zona de cada grupo en 👑 Administración → 🏢 Grupos → "🕐 Zona horaria".
- **`tzdata`** añadido a requirements (para que `zoneinfo` resuelva la zona seguro en el Cloud).
### Reemplazo masivo (~40 sitios en 22 archivos)
`datetime.now()`→`clock.now()`, `date.today()`→`clock.today()` en todo core/ (EXCEPTO `session_cookie.py`
—plomeria de cookies— y `clock.py`). El modelo multi-tenant garantiza que campo/admin solo tocan datos
de SU grupo, asi que el fallback por sesión da la zona correcta; el propietario (sin grupo) cae al default.
### ⚠️ Error que cometi y cace: el regex mordio los alias
`re.sub(r"\bdate\.today\(\)")` tambien matcheo dentro de `_dt.date.today()` y
`__import__("datetime").date.today()` → los dejo como `_dt.clock.today()` (roto: `clock` como atributo del
modulo datetime). Cazado con un grep de `algo.clock.now/today` y corregido a mano (projects.py:823,
projects_ui.py:671). Los alias que el regex NO matcheo (`_dt.now()`, `_date.today()`) se convirtieron
aparte. REGLA: tras un reemplazo por regex de `X.now()/X.today()`, grep de `\w\.clock\.` para cazar los
que quedaron como atributo de otra cosa.
### Verificacion
51/51 modulos importan; **per-grupo probado**: grupo sin zona→Sydney, grupo mock "usa"→America/New_York,
horas distintas (14 h). Migracion de la columna via `get_sheet`. 0 `datetime.now()/date.today()` sin
convertir, 0 `.clock.` mal formado. ⚠️ Arregla los registros DE AHORA EN ADELANTE; los ya guardados
quedaron en UTC (migracion aparte, opcional). Con esto los turnos normales dejan de "cruzar medianoche"
(v164), que era un sintoma de este bug.

## PDF del Pre-Start calcado al template CI Liftworx (v172)
Peticion del usuario: "que el pdf que se genera se vea mas como el que te pase de ejemplo". El ejemplo
es `Downloads/_Daily Pre-Start Template.pdf` (CI Liftworx): un FORMULARIO blanco y negro con bordes,
bandas grises por seccion y recuadros de notas. El PDF anterior era colorido/moderno (bandas azules).
### `prestart_pdf.generate_prestart_pdf` reescrito para calcar el template
- Blanco y negro, **bordes**, **bandas grises** (`#d9d9d9`) por seccion, recuadros de notas con borde.
- Fila **Date · Time · Location · Facilitated by** bordeada (como el template).
- ⚠️ **Reubicacion clave**: los 4 checks que la app llama "Seccion 1" (permisos/toolbox/subcontratistas/
  preop) en el TEMPLATE van en la **Seccion 3, sub-tabla "Circle one"**. La Seccion 1 del template es
  solo un recuadro de notas. El PDF ahora respeta eso: Seccion 1 = `activities_notes`; Seccion 3 = los 3
  shaft checks (`CHECKS_S3`) + la sub-tabla 2×2 "Circle one" con `CHECKS_S1`.
- **Respuesta marcada = cajita con fondo NEGRO** (helper `_ans`): el "formulario relleno". ⚠️ Sin glyphs
  Unicode de checkbox (Helvetica no los tiene) — se usa `Table` con `BACKGROUND` negro en la celda
  seleccionada, 100% fiable.
- Attendees en **3 pares** (Print Name · Initial), como el template.
- **Marca = nombre del grupo** (decision del usuario, no "CI Liftworx"); sin el logo skyline (la app no
  tiene logo por grupo). **Textos de los checks en ESPAÑOL** (decision del usuario: iguales a la pantalla
  del Pre-Start, para que app y PDF coincidan).
### Verificacion
PDF de prueba generado con datos realistas y **revisado visualmente** (render): cabe en 1 pagina A4,
estructura calcada, respuestas resaltadas correctas (YES/NO/N-A), notas en sus recuadros, 4 asistentes en
2 filas de 3 pares. Compila + import; firma `generate_prestart_pdf(data)` intacta (sin cambios en
`submit` ni call-sites). Los datos ya se capturaban desde v97/v158; solo cambia la MAQUETA.

## Pre-Start del campo: preselecciona el proyecto donde fichó + Time estructurado (v170)
Revision de 🦺 Pre-Start desde el rol CAMPO (quien lo llena en obra, en el movil, cada mañana). Ya era
solido tras v158; tres mejoras de la experiencia de campo.
### Integracion: preselecciona el proyecto del FICHAJE
El campo elegia el proyecto de una lista sin preseleccion cada dia. **Decision del usuario: "lo primero
que hace el usuario es fichar"** → cuando llega al Pre-Start ya tiene fichaje abierto, asi que se
preselecciona ESE proyecto (como 📋 Mis proyectos, v138). ⚠️ NO es "el primero de la lista" que evito
v139: es una señal FUERTE (donde esta trabajando), se MUESTRA ("⏱ Es el proyecto donde fichaste hoy;
cambialo si el pre-start es de otro") y sigue siendo cambiable. Resuelve **ID primero, nombre de
respaldo** (v145). Solo para el rol campo (admin/propietario no fichan).
### Tecnico: "Time" deja de ser texto libre
Era `text_input` (mismo fallo de las fechas antes de v149): un dedazo quedaba como hora rara en el PDF.
Pasa a **`st.time_input`** (se guarda como "%H:%M").
### Detalle: la inicial del asistente se autocompleta
Al generar, si un asistente tiene el "Initial" vacio se calcula de su nombre (`_initials`) — no hay que
teclear las dos cosas.
### Verificacion
Preseleccion (sintetico): por ID PRJ-0002→North, por nombre Prueba1→Prueba1, sin fichaje→None, ID
inexistente cae al nombre→Norte. `time_input` 17:16:00→"17:16". `render_prestart_tab` 0 nombres libres,
compila+import. (Con datos reales no hay fichajes abiertos ahora, asi que la preseleccion se estrena en
el Cloud cuando alguien fiche y abra el Pre-Start.)

## Pre-Start: lo que se captura por fin se ve + no se puede firmar sin leer (v158)
Revision del ultimo modulo del admin sin tocar, "con la misma dinamica" (tecnico/imagen/integracion).
### ⚠️ Tecnico 1: 7 columnas escritas desde v97 y NADIE las leia
`S1JSON`, `S3JSON`, `Asistentes`, `Location`, `ActividadesNotas`, `NotasGenerales` se guardaban y el
historial solo mostraba fecha/hora/facilitador/near-miss/archivo. **Un check en NO es una alerta de
seguridad y quedaba invisible** sin abrir el PDF. `prestart.leer(r)` descompone la fila (checks con su
estado, n_no, asistentes, notas). Octava aparicion del patron "se escribe y nadie lo lee".
### ⚠️ Tecnico 2 (el mas serio): el formato se podia FIRMAR SIN LEERLO
Los checks arrancaban en **YES** (index=0) y el near-miss en **NO** (index=1): entrabas, pulsabas
Generar y salia un pre-start con todo en verde sin revisar nada — vaciaba la charla de seguridad.
Decision del usuario: **sin respuesta por defecto** (`index=None`, soportado desde Streamlit 1.30). Hay
que responder cada check; el boton Generar queda `disabled` y lista lo que falta. Al generar, si hay
checks en NO se avisan aparte (revisar antes de trabajar).
### Imagen
- **KPIs de seguridad**: registrados, con near miss, con checks en NO, fecha del ultimo.
- **Historial como fichas desplegables** (antes tabla plana de 5 cols): cada pre-start con **semaforo
  🟢/🔴** (rojo si near miss o algun check en NO), y al abrir: asistentes, cada check con su estado
  (🟢 YES / 🔴 NO / ⬜ N/A), la descripcion del near miss, las notas y el PDF.
### Integracion (ya estaba, no se toco)
El near-miss abre alarma del proyecto y el "Resumen del dia" del admin cuenta los near-miss de la
semana. PENDIENTE que deje anotado: un check en NO NO abre alarma (solo el near-miss). Podria, pero
seria cambio de comportamiento — se dejo solo muy visible en la UI.
### Verificacion
`leer()` contra los 2 pre-starts REALES de PRJ-0001: PS-0002 (near_miss=YES, 7 checks YES, asistente
asfgjjd) → 🔴; PS-0001 (near_miss=NO, todo YES, lksdfkldsf) → 🟢. KPIs: 2 registrados, 1 con near miss,
0 con checks NO. 0 nombres sin resolver en las 3 funciones. Prompt del agente actualizado (regla v133).

## RAIL desde el proyecto: el codigo del riel se resuelve a su altura (v157)
Bug reportado por el usuario: "esta leyendo el tipo de riel pero no me da el valor que le corresponde;
RAIL sale en 0".
### La raiz: el plano da el CODIGO, no la altura
El plano trae el codigo del riel (p.ej. `T75-3/B`); el VALOR RAIL (altura del diente) sale del
catalogo de rieles (hoja Rieles, T75-3/B → AlturaDiente 62). El uploader DIRECTO del Survey si hacia
ese lookup (`rails.get_rail` → `inp_RAIL`, v84/v85), pero el camino **desde el proyecto** (v137,
`plan_ui.aplicar`) **no lo hacia**: `extraer_todo` guardaba solo el codigo y el mapa no incluia RAIL.
Asi que al cargar el plano desde el proyecto, RAIL quedaba en 0.
### Fix
- **`plan_data.extraer_todo`** consulta el catalogo con el codigo leido y guarda `rail_altura` (y
  `rail_ancho`) en el plano. Si el codigo no esta en el catalogo, lo pone en `faltan` con el motivo.
- **Los mapas de `aplicar`** vuelcan `rail_altura`: Survey → `inp_RAIL`, Plomada → `plb_rail`.
- **`_plano_section`** muestra el riel como "codigo · RAIL 62". Plomada marca RAIL como 📄 (del plano)
  y corrige los textos que decian que RAIL va a mano.
### ⚠️ Los planos ya cargados hay que RECARGARLOS
`rail_altura` se calcula en la extraccion, asi que un PlanoJSON guardado ANTES de v157 no lo tiene. Hay
que volver a cargar el plano (📎 Archivos → 📐 Datos del plano → Cargar) para que se resuelva la altura.
### Verificacion
Viaje completo con el plano REAL (PLANO NORTH SYD.pdf): `extraer_todo` → rail=`T75-3/B`,
**rail_altura=62.0**, rail_ancho=10.0, faltan=[]; `aplicar({"rail_altura":"inp_RAIL"})` sobre
session_state vacio → **inp_RAIL=62.0** ✓. Catalogo confirmado (T75-3/B=62, T127-2/B=89). El uploader
directo del Survey sigue intacto. NO se escribio en produccion (solo lecturas).

## Cargar el plano en un proyecto ya creado (v156)
Bug reportado por el usuario: "cuando cargo el plano desde Mi grupo → proyecto → Archivos, las
herramientas no lo ven".
### La raiz: subir el PDF ≠ extraer sus datos
Las herramientas leen **`PlanoJSON`** (`plan_data.del_proyecto`). Esa columna solo se poblaba **al
CREAR el proyecto** (v137, con `extraer_todo` + `guardar`). Subir el plano por el uploader generico de
📎 Documentos hacia solo `drive_store.upload` + `add_document`: guardaba el PDF pero **NO extraia a
PlanoJSON**, asi que el plano quedaba invisible para las herramientas. Y un proyecto creado sin plano
**no tenia NINGUNA forma** de recibirlo despues. Confirmado: los 3 proyectos reales tienen PlanoJSON
VACIO.
### Fix: `_cargar_plano(pid)` en el bloque 📐 Datos del plano
Hace lo mismo que la creacion: sube el PDF + **extrae a PlanoJSON** (barra de progreso ~80 s, guarda de
identidad `name:size` de v112) + registra el PDF como documento (best-effort). Es el sitio natural,
justo donde se ven esos datos; cuando estan vacios, invita a cargarlo en vez de dejar un callejon sin
salida ("se cargan al crear el proyecto").
### Se cierra la trampa del uploader generico
**"plano" sale de `_DOC_SUBIR`** (ya no se puede subir por el uploader generico, que no extrae) pero
sigue en `_DOC_TIPOS`/`_CAMPO_VER` (se VE si ya existe). Una sola forma de cargar plano, y siempre
extrae. Mismo criterio que v140: no dejar dos mecanismos para lo mismo, uno de los cuales falla en
silencio.
### Verificacion
`extraer_todo` sobre un plano REAL (PLANO NORTH SYD.pdf): 17/17 params, NS=6, T75-3/B, HKP=70,
HQ=14045, LFKK=2915, faltan=[]; la barra reporta 7 pasos; el JSON serializa (459 chars).
`guardar`+`del_proyecto` usan el camino ya probado en v137. `plano` fuera de `_DOC_SUBIR` pero visible
en `_DOC_TIPOS`. 0 nombres sin resolver en las 2 funciones. NO se escribio en produccion al verificar
(solo `extraer_todo`, que es lectura).

## El Survey ya no pide proyecto/cliente/ubicacion/ingeniero a mano (v155)
Apunte del usuario: "en el Survey tengo que escribir proyecto, cliente, ubicacion, ingeniero; estos
campos no son necesarios". Tenia razon: eran **entrada duplicada**. Desde v135 el survey alimenta un
proyecto que YA existe, y ese proyecto ya trae Nombre/Cliente/Ubicacion/Ingeniero. El survey tenia DOS
formas de identificar el proyecto a la vez: 4 `text_input` arriba + el selector de proyecto abajo.
### Que alimentaban esos campos (verificado antes de tocar)
Solo los INFORMES (portada cliente, informe admin) y el correo — **no el calculo** (no estan en
`_survey_signature`) y **no se escribian de vuelta al proyecto** (`attach_survey` solo toca
ParamsJSON/MatrizJSON/InterpJSON). O sea, puro dato de presentacion que el proyecto ya tiene.
### El cambio
- Se quitan los 4 `text_input`. La identidad se TOMA del proyecto al elegirlo en el selector del plano:
  `session_state["proyecto"/"cliente"/"ubicacion"/"ingeniero"]` = Nombre/Cliente/Ubicacion/Ingeniero.
- ⚠️ **Seguro escribir esas claves** porque dejaron de ser widgets (con los `text_input` vivos habria
  sido el error de v111). Y NO estan en la firma, asi que no disparan falsos "recalcular".
- El keep-alive de v118 (L122) ya cubre esas 4 claves → el valor escrito en la fase Datos sobrevive a
  la fase Resultados (donde los dibujos y el correo lo leen).
- **Modo «sin proyecto»** (calculo suelto del admin): el `else` limpia las 4 a "" → el informe va sin
  identidad, sin arrastrar la del proyecto anterior. (Decision del usuario: informe sin esos datos.)
- Confirmacion al elegir: "📋 El informe usara los datos de este proyecto: Cliente · Ubicacion ·
  Ingeniero" + enlace a Maps, puesto DONDE el valor esta fresco (no arriba, que iba un render por
  detras). El bloque de identidad de arriba se elimino (redundante con `_cabecera` del selector).
### Verificacion
Los 4 `text_input` fuera; **ningun widget usa ya key proyecto/cliente/ubicacion/ingeniero** (chequeo
regex); informes y correo siguen leyendo de session_state; de PRJ-0001 real se tomaria
prueba1 / ci / 259 clveland redfern / daco; sin referencias colgantes a `_id1..4`; importa OK.

## El Survey es una herramienta más; el Pre-Start no es técnico (v154)
Apunte del usuario: "cuando hablamos de las herramientas me nombras todas menos el survey; ahora el
survey es una herramienta mas, la mas potente y compleja pero una mas. Las herramientas TECNICAS son:
survey, plomado, corte de rieles, corte de buffers, belting".
### Que ya estaba bien
El Survey YA se trataba como herramienta en el nav (`_HERR`), en `toolruns.HERRAMIENTAS` (clave
`survey`) y en el prompt del agente ("es una herramienta que alimenta un proyecto, igual que Plomadas").
La incoherencia principal era **mi lenguaje** ("las 4 herramientas"), heredado de que toolruns/
tool_save_ui se construyeron para las otras 4.
### La incoherencia real: el Pre-Start estaba en el saco de las herramientas
`_HERR` se llamaba "herramientas comunes" e incluia Survey + los 4 calculos **+ Pre-Start diario**.
Pero el Pre-Start es un formato de SEGURIDAD de obra, no una herramienta tecnica. Decision del usuario:
separarlo en el nav.
- **`_HERR` pasa a ser las 5 TECNICAS** (Survey, Plomadas, Rieles, Buffers, Belting), contiguas.
- **El Pre-Start se coloca con lo operativo** (tras el panel del rol y el fichaje), antes de las tecnicas.
- Prompt del agente actualizado: distingue "5 herramientas tecnicas" de "Pre-Start (seguridad)".
### Verificacion
Solo cambia ORDEN y encabezado, no accesos: comprobado que propietario y campo conservan el MISMO
conjunto de secciones (nada perdido ni ganado) y el conductor queda intacto (nunca tuvo Pre-Start ni
tecnicas). Los defaults (1er item por rol) no cambian. El enrutado es por etiqueta (`if _seccion == _L_X`),
asi que reordenar la lista no lo afecta. Sintaxis + import OK.
### Pendiente menor (no se toco)
El Survey se "reabre" con "🔄 Reconstruir en el Survey" mientras las otras 4 usan "↩️ Reabrir en la
herramienta" (v148): dos nombres para el mismo concepto. Es defendible (el Survey guarda en ParamsJSON,
no en DatosJSON) pero conviene unificar el LENGUAJE algun dia.

## Usuarios de campo: una ficha 360 por persona (v153)
Peticion del usuario: la gestion de usuarios "debe ser lo mas completa posible y permitir ver y
gestionar TODO lo asociado con cada usuario; practica pero completa".
### ⚠️ El problema: estaba organizada por ACCION, no por PERSONA
Para gestionar UN usuario habia que elegirlo en **tres desplegables distintos** — uno para el contacto,
otro para modificar (contraseña/tarifa/activar) y otro para las credenciales — y la tabla de arriba era
solo lectura. Ademas habia datos de cada persona que **no se veian en ningun sitio de gestion** aunque
la app los tiene: proyectos asignados, horas, recibos que cargo, si esta fichando ahora.
### `_ficha_usuario(u, grupo)`: elegir a la persona y gestionarlo todo ahi
Sub-navegacion con radio (regla v56, NO st.tabs) dentro de la ficha:
- **🔑 Acceso**: contraseña, tarifa/hora, activar/desactivar.
- **📇 Contacto**: email + vinculacion de Telegram (reusa `_contacto_uno`, extraido de
  `_field_contact_ui` para no duplicar; el panel del propietario sigue usando la version con lista).
- **🎫 Credenciales**: `render_credenciales(editable=True)`, ya existia.
- **📊 Su trabajo** (nuevo, solo lectura): horas registradas, recibos cargados (`expenses.by_user`,
  nuevo — `CreadoPor` se guardaba desde v105 y no se leia por usuario) y proyectos asignados. El "todo
  lo asociado" que se pidio.
- **🗑**: eliminar con `ui.confirmar_borrado`.
La ficha **se adapta al rol** (decision del usuario, campo+conductor misma ficha): al conductor no le
exige contacto ni le muestra proyectos asignados (no van por `CampoAsignados`).
Arriba queda el **panorama**: tabla-resumen con semaforos de contacto + la matriz de compliance, y
"➕ Crear usuario" plegado. El selector de la ficha va **sin preseleccion** (`ui.elegir`, v139).
### Verificacion
Contra datos REALES: `campo1` (rol campo) muestra sus **3 proyectos asignados** (prueba1/north/norte),
`conductor` no muestra proyectos (correcto, no van por CampoAsignados); `by_user` cuenta recibos por
`CreadoPor`; los chips de estado (activo/fichando/contacto) derivan de datos reales. 0 nombres sin
resolver en las 4 funciones tocadas. **`_field_contact_ui` conserva su firma** para los 2 call-sites
del panel del propietario (extraje `_contacto_uno` sin cambiar la version con lista). Sin variable
`campo` huerfana tras la reescritura. Prompt del agente actualizado en el mismo lote (regla v133).

## Gastos del grupo: presupuesto, proyeccion y separar con/sin presupuesto (v152)
Peticion del usuario. La pestaña era de **v106** y no se habia vuelto a tocar: dos `st.bar_chart`
grises, una tabla y un `st.metric`. Se quedo atras respecto a Costos (v144), Estado (v143) y Horas
(v151).
### ⚠️ Respondia "cuanto llevas" en vez de "cuanto vas a gastar"
`cost_projection` (proyeccion al terminar = costo·100/avance) existe desde v144 y la vista de grupo
**no la usaba**, ni mostraba el presupuesto del grupo. La pregunta de gestion no es cuanto lleva
gastado el grupo sino **si se va a salir del presupuesto** — y eso se sabe hoy, no cuando ya paso.
`group_expenses` ahora añade por fila `avance`, `proyectado`, `over` y **`over_proj`** (se saldra al
ritmo actual aunque hoy aun este dentro). Es el UNICO consumidor, asi que enriquecerlo no afecta a nadie.
### Rehecha con el lenguaje de las otras pestañas
- **KPIs**: costo actual, presupuesto del grupo, % consumido (rojo si >100), **proyeccion al terminar**
  (rojo si supera el presupuesto), proyectos sobre presupuesto.
- **Dos alertas**: ⛔ los que YA se pasaron (`over`) y ⚠️ los que **se pasaran al ritmo actual**
  (`over_proj`, aun dentro hoy). El caso que importa: $6k de $10k al 30% proyecta $20k → avisa estando
  al 60% consumido, cuando aun se puede reaccionar.
- **Se separan** los proyectos CON presupuesto (costo/proyeccion/% + semaforo ⛔⚠️✅) de los SIN
  presupuesto (solo costo + aviso de que no hay contra que comparar). Antes se mezclaban en una columna
  "%" que salia vacia — con 2 de 3 proyectos a presupuesto 0, la tabla se veia a medias.
- Barras HTML (`_barras_html`, v144) para reparto MO/compras y por categoria, en vez de `st.bar_chart`
  grises. **Quitada la subtabla de categorias** (duplicaba las barras de justo encima).
- CSV de contabilidad ampliado con avance y proyeccion.
### Verificacion
Contra datos REALES: KPIs (costo $359, presup $10.000, proyeccion $778, 4% consumido), separacion
correcta (prueba1 con presupuesto / north+norte sin), proyeccion de prueba1 778.31. Las **3 ramas de
alerta** probadas con filas simuladas (sano / ya pasado / se pasara al ritmo / mezcla): ⛔ y ⚠️
disparan donde deben y el caso $6k→$20k avisa sin estar todavia sobre. 0 nombres sin resolver (el `x`
es de una lambda).

## Horas del grupo: costo de M.O., KPIs y el "sin asignar" deja de mentir (v151)
Peticion del usuario: revisar 🛠 Mi grupo → ⏱ Horas (tecnico, imagen y funcionalidad). Eran **dos
tablas planas** que solo respondian "cuantas horas".
### ⚠️ El "sin asignar" mostraba CEROS FALSOS
`sin_asignar` = jornada − Σproyectos, clampado a 0. Pero eso solo vale si todos abren jornada, y hasta
v150 el fichaje normal no la abria. En los datos reales, `lksdfkldsf` imputa **8.97 h a proyecto con 0
de jornada** → sin_asignar sale 0, cuando en realidad es **indeterminado**. La metrica parecia precisa
y no lo era. Ahora `group_hours` marca `sin_asignar_indet` (proyecto > jornada + 3 min de tolerancia)
y la tabla muestra **«—»** en vez del cero enganoso, con nota explicativa.
### El costo, que es lo que le faltaba a una vista de GESTION
`TarifaHora` por usuario y `labor_cost` ya existian, aqui no se cruzaban. `group_hours` añade
**`tarifa` y `costo`** (horas imputadas × tarifa) por persona + total del grupo. Aviso de quien tiene
tarifa 0 (su costo sale $0 sin explicacion). Mismo criterio que la pestaña Costos de v144.
### Imagen: KPIs + reparto por proyecto
Tarjetas arriba (personas activas, jornada, en proyectos, sin asignar con % en rojo si >25%, costo
M.O.) y **barras de horas del grupo por proyecto** — a que elevador va el tiempo, que antes estaba
enterrado en subtablas persona por persona dentro de un expander. Se quito la columna **Login** (ruido
tecnico) y las subtablas.
### ⚠️ Bug que introduje al quitar el Login y cace en la verificacion
El Login era el **desempate**: en los datos reales `conductor` y `fijiofgjei` tienen el MISMO Nombre,
asi que sin el Login salian como dos filas `fijiofgjei` **indistinguibles** (mismo colapso por homonimo
de v147/v150). Fix: se añade el login entre parentesis SOLO a los nombres que colisionan. REGLA (ya van
tres): al usar un nombre legible como identidad visual, comprobar que es UNICO; si no, desempatar.
### Verificacion
Contra los datos REALES: KPIs (4 personas, 9.9 h jornada, 17.7 h proyecto, $359 M.O.), costo de
`lksdfkldsf` 8.97×40=358.8, `sin_asignar_indet` True para quien imputo sin jornada y False para el
ruido de 1 centesima (admin1 8.68 vs 8.67), reparto por proyecto (prueba1 8.99 / north 8.65 / norte
0.02), y las dos `fijiofgjei` ya distinguibles. `group_hours` es el UNICO consumidor, asi que ampliar
su dict no afecta a nadie mas.

## Fichaje: dos relojes para TODOS, sin texto libre y con resumen del dia (v150)
Peticion del usuario: "mas dinamico, mas profesional; aun salen campos para llenar a mano; el proyecto
debe poder seleccionarse; y vamos a estandarizar el clock in/out para todos por igual, uno general y
uno especifico, con cronometro".
### ⚠️ El texto libre no era cosmetico: PERDIA HORAS
Habia tres sitios para teclear el proyecto a mano (`_OTRO`, `tc_proyecto`, `cd_prj_txt`). Al usarlos
el **`ProyectoID` quedaba vacio**, asi que esas horas dependian de que el nombre coincidiera exacto:
con un dedazo **no contaban para ningun proyecto** y desaparecian del costo de mano de obra, sin
aviso. Reabria justo el agujero que cerro v145. En los datos reales solo **6 de 12** filas tienen ID.
Ahora el proyecto SIEMPRE sale de una lista (`ui.elegir`, sin preseleccion).
### "Ubicacion / Nota": se pedia dos veces y no la leia NADIE
Verificado en todo el repo: todas las lecturas de `Ubicacion` son la **del proyecto**, no la del
fichaje. Y en los datos reales esta **vacia en las 12 filas**. Se pedia al entrar y otra vez al salir
(se anexaba como nota). Eliminada del formulario.
### Un solo fichaje: jornada + proyecto (decision del usuario)
`_render_normal` y `_render_conductor` eran dos flujos que divergian; ahora hay **una** funcion.
El modelo ya existia entero (TIPO_GENERAL/TIPO_PROYECTO, switch_project, `sin_asignar` = jornada −
Σproyectos, ya clampado a 0), solo lo usaba el conductor. Eso producia datos incoherentes: en la hoja
real, `lksdfkldsf` tiene **8.97 h de proyecto y 0 de jornada**.
- **`fichar_proyecto()`** abre la jornada SOLA si no estaba (decision del usuario: los dos relojes
  para todos, pero sin cobrar un toque extra cada mañana) y lo avisa. **`cerrar_jornada()`** cierra
  tambien el segmento de proyecto.
- **`resumen_hoy()`**: horas del DIA NATURAL (no ultimas 24 h) — jornada, imputado y sin asignar. El
  cronometro solo dice cuanto llevas desde que fichaste; esto dice cuanto llevas en el dia.
- **`mis_fichajes()`**: los propios, que el usuario no podia ver (el reporte de horas es del admin).
### ⚠️ `clock_out` hacia hasta 5 llamadas a la API por salida
3 `update_cell` + (si habia nota) 1 lectura y 1 escritura mas. Con el equipo fichando a la misma hora
es el escenario del 429 que v80 arreglo en los proyectos. Ahora **1 `batch_update`**.
### ⚠️ Bug que reintroduje y cace en la verificacion
El selector de proyectos lo arme con `{nombre: id for p in proys}`: **dos proyectos homonimos
colapsan y uno queda IMPOSIBLE de fichar**, en silencio. Es exactamente el fallo de v147, cometido
otra vez tres versiones despues. Desempatado con el ID. Los homonimos son posibles: `create_project`
solo AVISA de duplicados, no los impide.
### Verificacion
`resumen_hoy` probado con fichajes simulados: dia normal (8 h jornada, 3+2.5 imputadas → 2.5 sin
asignar) · sesion ABIERTA contando el tiempo transcurrido · lo de ayer NO entra · proyecto sin jornada
no deja `sin_asignar` negativo. `fichar_proyecto` y `cerrar_jornada` probados en los 3 escenarios
(sin nada abierto → abre general + proyecto, auto=True; jornada ya abierta → solo proyecto; cerrar con
proyecto abierto → cierra proyecto y luego general). `mis_fichajes` contra los datos REALES.
0 nombres sin resolver · 0 `text_input` en el modulo · sin referencias huerfanas a las 2 funciones
eliminadas · prompt del agente actualizado en el MISMO lote (regla v133).

## Pestaña Datos: archivar en vez de borrar, y fechas que no mienten (v149)
Revision de ✏️ Datos a peticion del usuario ("a mi no se me ocurre mucho, que propones?"). Tres
problemas reales, ninguno estetico.
### ⚠️ 1. Las fechas eran texto libre y falseaban el cronograma EN SILENCIO
`FechaInicio`/`FechaFinEst` eran `text_input`, y `project_schedule` hace `.split("-")` con un `except`
que **cae a `date.today()` sin avisar**. Comprobado: `16/07/2026`, `16-07-2026`, `2026/07/16` y `""`
todos caen a hoy. En PRJ-0001 real (dia 12 de 32, 46% real vs 33% plan), reescribir la fecha con barras
lo manda al **dia 0** y la app dice 46% real contra 0% planificado: *"vas adelantadisimo"*. Quedan
falseados curva S, retraso, fin proyectado y el radar del admin. Ahora `st.date_input` (+ `_a_fecha`
para leer lo ya guardado en cualquier formato y `_iso` para guardar siempre en ISO) y validacion de
que fin >= inicio.
### ⚠️ 2. Borrar era la accion mas destructiva y la PEOR protegida
Un clic, **sin casilla de confirmacion** — mientras que borrar UNA actividad si la exige desde v139.
Y `delete_project` solo quita proyecto + actividades: medido en PRJ-0001, dejaba huerfanos
**2 documentos (con sus archivos en Drive), 2 pre-starts, 6 alarmas y 4 fichajes**.
**Decision del usuario: archivar en vez de borrar.**
- `ARCHIVADO` entra en `ESTADOS_MANUAL` y en `derive_estado` (reusa la maquina de estados existente,
  sin inventar una paralela). `set_archivado(pid, bool)` archiva y restaura.
- **`list_projects(..., incluir_archivados=False)`**: el defecto OCULTA. ⚠️ Por eso las **busquedas
  por identidad** tienen que pedirlo explicitamente, o archivar las romperia en silencio. Clasificados
  los 30 call-sites: 4 son busquedas (`plan_data.del_proyecto`, el mapa nombre->ID de
  `project_hours_bulk`, el proyecto del clock-in en `plan_ui`, y el chequeo de duplicados) y 26 son
  listas.
- ⚠️ **Sin una forma de VER los archivados, archivar seria un viaje sin vuelta**: el proyecto
  desaparece de la cartera y no habria como abrirlo para restaurarlo. Casilla "📦 Ver también los
  archivados" en la cartera del admin y en la tabla del propietario, mas un contador de cuantos hay
  ocultos. Emoji y color de estado añadidos.
- **Borrar de verdad: solo propietario**, con el **inventario de lo que quedara huerfano** y hay que
  **teclear el nombre del proyecto** para habilitar el boton.
### 3. Asignar campo no avisaba de credenciales vencidas ni contacto faltante
`_avisar_asignados` existe desde v127 y **solo se usaba al CREAR** el proyecto. Asignar gente a un
proyecto existente es la accion diaria. La causa es la que v127 ya resolvio en el Survey: el selector
estaba **dentro del `st.form`**, y ahi los widgets no escriben hasta el submit, asi que el aviso en
vivo es imposible. Sacado fuera del form.
### ⚠️ ERROR MIO: `st.stop()` dentro del form, y otra vez la indentacion
Valide con `st.error(...)` + `st.stop()`. **`st.stop()` corta el render de TODO lo que va debajo**
(actividades, archivar, eliminar): la pagina se quedaria a medias. Se cambio por `_err` + `if/else`.
Y al reindentar el guardado bajo el `else` volvi a hacerlo a mano: el `else:` con 2 espacios dejaba las
9 sentencias del guardado FUERA del condicional, asi que habria guardado igual con el nombre vacio.
Rehecho **por AST**, midiendo el rango real del bloque, y **verificado por AST** que los 6 efectos
(`update_project`, las 3 notificaciones, `toast`, `rerun`) quedan DENTRO del else y ninguno fuera.
### Verificacion
0 nombres sin resolver nuevos y 0 usos-antes-de-asignar nuevos en los 4 modulos (AST vs commit
anterior) · `_ver_arch` asignado antes de usarse en las 2 funciones · `ag_id` asignado antes de su uso
dentro del else · la validacion de fechas compara ANTES de convertir a texto · las 4 ramas del detalle
intactas · `datos_asociados` probado sobre los proyectos reales.

## Reabrir un calculo guardado (v148)
Salido de una auditoria del patron "se escribe y nadie lo lee": **`toolruns.DatosJSON` no tenia
lector**. Cada plomada, corte o belting guardaba su JSON desde v129 y no habia forma de usarlo: de un
calculo de la semana pasada solo podias bajar el PDF, no abrirlo y cambiar un numero.
### ⚠️ Al ir a implementarlo, el dato guardado NO servia
`DatosJSON` guardaba los **RESULTADOS**, no las entradas: plomada metia dbp/dbpw/d1/d2/verif..., que
son salidas de `compute_plumb`, no BKS/RAIL/TKSW/BSR. **Faltaba justo lo necesario para reabrir.**
Se corrigio el formato a `{"entradas": {...}, "resultados": {...}}`. Como la hoja `Calculos` tiene
**0 filas** (nunca se guardo ni un calculo en produccion), no hay formato heredado que sostener; aun
asi `entradas_de()` devuelve {} con el formato viejo y entonces no se ofrece reabrir.
REGLA: antes de construir sobre un dato guardado, mirar **que contiene**, no que exista la columna.
### Como se capturan las entradas
`tool_save_ui._snapshot(herramienta)` recoge session_state **por PREFIJO** (`plb_`, `rc_`, `bc_`,
`belt_`) en vez de enumerar claves: asi las que nacen sobre la marcha (`belt_hgpr_2`) entran solas y no
hay una lista que mantener. Los `DataFrame` (matrices de rieles y buffers) viajan como
`{"__df__": records}`. Se saltan las claves `*_editor` (los `st.data_editor`): su contenido ya vive en
el `*_df` de al lado, que **NO es clave de widget** y por tanto es seguro restaurar.
Los widgets del propio bloque de guardado (`prj_*`, `dl_*`, `save_*`) no empiezan por el prefijo, asi
que quedan fuera solos — verificado.
### ⚠️ La restauracion escribe claves de WIDGET (regla v111)
`aplicar_restauracion()` va **antes de instanciar ningun widget** de la herramienta. Verificado por
AST en las 4: la llamada esta DENTRO de su `render_*_tab` y su linea es anterior a la del primer
widget (plumb 34<38, rieles 36<40, buffers 36<40, belting 39<43).
### ⚠️ ERROR MIO: volvi a romper la indentacion, como en v120
Mi parche sustituia el texto del ancla sin sus 4 espacios, asi que la linea reinsertada quedaba a
columna 0 → `IndentationError` en los 4 ficheros. Se revirtio con `git checkout` y se rehizo leyendo
la **indentacion real** de la linea ancla (`re.match(r"\s*", linea)`) y aplicandosela al bloque.
REGLA: al insertar codigo por texto, NUNCA reescribir la linea ancla; insertar lineas ANTES de ella
con su misma indentacion medida del fichero.
### Verificacion: viaje completo, no solo "compila"
Simulado el ciclo real de las 4 herramientas — session_state -> `_snapshot` -> `json.dumps` -> columna
-> `json.loads` -> `entradas_de` -> `aplicar_restauracion` -> session_state vacio:
plomada 11 claves, rieles 7 (con matriz), buffers 3 (con matriz), belting 6 (claves dinamicas).
En las 4: nada falta, nada sobra, valores identicos, **matrices reconstruidas** y `bc_editor` excluido.
Formato viejo y `DatosJSON` corrupto devuelven {} sin romper.

## Pestaña Archivos: el plano visible, fotos en galeria y descarga bajo demanda (v147)
Cuatro mejoras tras quitar el paquete de obra en v146.
### ⚠️ La descarga era ANSIOSA: se bajaba TODO Drive en cada render
`st.download_button(data=...)` evalua `data` **al renderizar**, no al pulsar. Con un
`download_button` por documento, abrir un proyecto se bajaba de Drive **todos** sus archivos antes de
que nadie tocara nada. Cacheado 5 min, asi que con 3 documentos no se nota — pero el campo **solo
puede subir fotos**, asi que ese numero crece sin techo. Estaba igual en Documentos y en Calculos.
Ahora: lista con metadatos + **`ui.elegir` sin preseleccion** (v139) y solo se descarga **el elegido**.
Medido con los documentos reales: **0 descargas al renderizar** (antes 2 en PRJ-0001 y 3 en PRJ-0003).
### Las fotos de obra, en galeria
El campo solo sube fotos: son la unica ventana del admin a la obra y salian como una fila de texto
(`📷 foto.jpg · foto`). `_galeria_fotos` las pinta en rejilla de 3 con su fecha y quien la subio.
**Paginada de 6 en 6 a proposito**: cada miniatura ES una descarga, y mostrarlas todas seria
reintroducir el problema que acabamos de arreglar.
### Quien subio cada documento y cuando
La hoja `Documentos` guarda `SubidoPor` y `Fecha` desde v74 y **la vista los tiraba**. Ya salen en la
tabla (`campo1 · 16/07 07:44`). Sexta aparicion del patron "se escribe y nadie lo lee".
### Lo que dijo el plano, dentro del proyecto (`_plano_section`)
`PlanoJSON` existe desde v137 y solo se veia **al crear el proyecto** o dentro de una herramienta: en
el detalle tenias el `plano.pdf` colgado sin saber que se extrajo ni si falto algo. Ahora hay tarjetas
(parametros n/total, NS, riel, HKP, HQ, LFKK/LFGK), **aviso de lo que el plano NO dio** y la tabla
completa desplegable. Claves verificadas contra `plan_data.extraer_todo` antes de usarlas (el error de
v135 fue inventarse un nombre de argumento).
### ⚠️ Bug que casi cuelo: dict comprehension que descarta en SILENCIO
Construi el mapa del selector con `{etiqueta: doc for doc in docs}`. **Dos documentos con el mismo
nombre y el mismo minuto** (subida masiva de fotos) colisionan y uno queda **imposible de descargar**,
sin ningun error. Desempate por los ultimos 6 del DriveID. REGLA: un dict comprehension sobre datos de
usuario necesita que la clave sea unica DE VERDAD, o pierde filas sin avisar.
### Verificacion
Simulada la pestaña con los documentos REALES de los 3 proyectos: iconos, tipos, autor y fecha
correctos; `_fecha_corta` probada con los 5 timestamps reales y con ''/None/fecha-sin-hora/basura;
selector sin colisiones; 0 nombres sin resolver nuevos (AST vs commit anterior; el unico "hallazgo"
era el `e` de un `except ... as e`, falso positivo de mi chequeo). Prompt del agente actualizado en el
MISMO lote (regla v133).

## Se elimina el paquete de obra: era un subconjunto del informe del cliente (v146)
El usuario, mirando la pestaña 📎 Archivos: "la opcion de paquete de obra no aporta mucho... aun no
veo claro si aporta algo tenerlo en la app". Tenia razon, y la comprobacion lo dejo sin defensa.
### La evidencia: no aportaba NI UN dibujo propio
`field_pack_pdf` metia `shaft_iso_svg` + `floor_plan_svg` + `plumb_svg`/`plumb_iso_svg`/
`plumb_card_svg`. **Los cinco estan en `user_report` (L408, L415, L477, L480, L483)**, con las mismas
funciones y los mismos argumentos — y el informe del cliente **ya se archiva solo** al guardar el
survey. Los tres del plomado ademas los genera por su cuenta el PDF de 🔩 Plomadas desde v130.
Su unico diferenciador era **lo que quitaba** (portada, veredicto, IA, glosario, conclusiones, firma):
una preferencia de formato, no una capacidad ausente.
### Por que sobrevivio tanto: el patron de v140, otra vez
Nacio en **v126**. Despues **v129/v130** dieron PDF propio a cada herramienta y **v134** se los hizo
visibles al campo. Entre las dos le vaciaron la razon de ser y nadie lo retiro. **REGLA (repetida):
al sustituir un mecanismo por otro mejor, quitar el viejo en el MISMO lote.**
### ⚠️ Una propuesta mia que RETIRE tras comprobarla
Propuse que el informe del cliente **degradara sin IA** (generarse sin las 5 secciones de la IA en vez
de bloquearse, regla de v38) para cubrir el unico caso en que el paquete ganaba: `survey_calc.
recalcular` es determinista y el informe se bloquea si falla la interpretacion. **Al verificar, la via
sin IA YA EXISTIA**: `diagrams.floor_plans_pdf` (v115), cuyo docstring dice literalmente "para enviar a
obra sin el informe completo", ya esta en el Survey. Abrir un modo de fallo nuevo en un documento que
va al CLIENTE para cubrir algo ya cubierto habria sido peor: el bloqueo de v38 es un control de calidad
deliberado. Se descarto y el informe no se toco.
### Eliminado
`core/field_pack.py` (152 lineas) · `_paquete_obra_section` (42) · sus 2 call-sites · el bloque del
Survey (29) · 2 imports. **~225 lineas.**
### Verificacion (borrar lineas DENTRO de funciones es lo que rompio v120)
1. **Diff estructural por AST contra el commit anterior**: en projects_ui solo desaparece
   `_paquete_obra_section` y solo cambia `render_field_projects` (32→31 sentencias); en survey_ui solo
   `_render_survey_results` (44→43). Ninguna otra funcion alterada.
2. **Las 4 ramas del detalle comparadas una a una**: Estado/Datos/Costos identicas, Archivos 4→3
   (exactamente la llamada quitada), ninguna rama perdida.
3. `best`/`lim_map`/`ctrl_in_frame_`/`all_params`/`limits`/`plumb_res` siguen asignados en
   `_render_survey_results` (las locales de las que dependia el bloque).
4. Cero referencias residuales en todo el repo; los 5 modulos importan de verdad.
5. **Prompt del agente actualizado en el MISMO lote** (regla v133): decia que el Survey ofrece un
   paquete de obra y que Archivos lo contiene. Ahora describe `floor_plans_pdf` y las pestañas reales.
   ⚠️ La regla de v133 aplica igual al QUITAR, no solo al añadir.

## El fichaje guarda el ProyectoID: trazabilidad que no se pierde al renombrar (v145)
Decision del usuario tras el hallazgo de v144: el fichaje cruzaba con el proyecto **por NOMBRE**, asi
que habia fichajes bajo `"Prueba1"` para un proyecto llamado `"prueba1"` cuyas horas **se caian del
costo EN SILENCIO**, y renombrar un proyecto desligaba todo su historico de mano de obra.
### Columna `ProyectoID` en la hoja del fichaje (migra sola, va al final)
- **`timeclock.es_del_proyecto(fila, pid, nombre)`** — regla unica: **ID primero, nombre de respaldo**
  (normalizado sin may/min ni espacios). Mismo criterio que `_matches` usa con `Usuario` desde v106.
  La usan `project_hours`, `project_hours_bulk`, `labor_breakdown` y `spend_curve`, para que el costo
  de mano de obra y las horas del proyecto **no puedan divergir**.
- **Escritura**: `clock_in(..., proyecto_id=)` y `switch_project(..., new_pid=)`; los 3 call-sites de
  `timeclock_ui` mandan el ID desde un mapa nombre→ID. Escribir el proyecto a mano deja el ID vacio
  (y cae al nombre), que es el comportamiento correcto.
- **`open_sessions`** devuelve tambien `proyecto_id` **sin quitar `proyecto`** (lo consumen plan_ui,
  projects_ui y timeclock_ui).
- **`group_hours`** resuelve el nombre ACTUAL via ID (`_nombre_actual`, import perezoso porque
  `projects` importa `timeclock` → seria circular): un proyecto renombrado deja de aparecer bajo dos
  etiquetas distintas.
### ⚠️ `project_hours_bulk` CAMBIA DE CLAVE: {nombre} → {ProyectoID}
Es el riesgo del lote: **8 call-sites lo indexaban por nombre** (tarjetas de cartera, agrupaciones,
KPIs, radar del admin, tabla del propietario) y si se escapa uno las horas salen **0 en silencio**.
Las filas anteriores a v145 no traen ID, asi que su nombre se resuelve contra los proyectos del grupo
y **tambien acaban sumando bajo el ID correcto** — el relleno del historico no hace falta para que las
cuentas salgan, solo para trazabilidad.
### Verificacion contra la base REAL
Horas totales **8.99 antes y 8.99 despues** (nada perdido); mano de obra **358.8 identica**; bulk y
`project_hours` coinciden proyecto a proyecto; los 5 casos de `es_del_proyecto` (ID manda sobre nombre,
ID distinto con nombre igual, fila vieja por nombre sin may/min, fila de otro, pid vacio); y
`group_hours`, `over_budget`, `group_expenses` y `admin_digest` siguen dando lo mismo. Ademas: **cero
nombres sin resolver NUEVOS** comparando por AST contra el commit anterior en los 5 modulos tocados
(los preexistentes son cierres anidados, no fallos).
### Relleno del historico EJECUTADO (22/07/2026, autorizado por el usuario)
Se escribio `ProyectoID` en **6 de las 12 filas** del fichaje real, en 1 sola llamada, recalculando
FRESCO al escribir y con asserts de que el plan seguia siendo el de la vista previa: filas 5/6/8/11 ->
PRJ-0001 (la 8 es la `"Prueba1"` que se caia), 12 -> PRJ-0003, 13 -> PRJ-0002. Las otras 6 no se
tocaron (5 sin proyecto, ninguna sin coincidencia). Verificado despues: horas 8.98/0/0.01 y suma 8.99
**sin cambios**, MO 358.8 sin cambios, y `group_hours` deja de partir `prueba1`/`Prueba1` en dos porque
`_nombre_actual` resuelve por ID. Comprobada la razon de ser del cambio: con el proyecto renombrado,
cruzar por ID conserva **8.98 h** y cruzar por nombre da **0.00 h**.

### ⚠️ ERROR MIO: una lectura local NO es solo-lectura si has tocado HEADERS
Dije que iba a auditar la hoja **sin escribir** y una ejecucion posterior escribio: al editar
`timeclock.HEADERS` y luego llamar a `project_hours_bulk`, la lectura pasa por **`_cached_ws()`, que
lleva la migracion de cabecera dentro**, y creo la columna `ProyectoID` en produccion sin avisar.
Fue benigno (solo la cabecera; las 12 filas de datos quedaron intactas, verificado) pero no era lo
acordado. **REGLA: `timeclock._cached_ws` / `projects._get_ws` / `alerts._ws` MIGRAN LA CABECERA en
cualquier acceso. Si has tocado HEADERS, cualquier "lectura" escribe.** Para auditar de verdad hay que
ir por gspread crudo, sin pasar por los helpers de la app.

## Pestaña Costos: de "cuanto llevas" a "cuanto vas a gastar" (v144)
Peticion del usuario: "esta muy simple, mas visual, con mas impacto y mas datos; es un apartado muy
importante". La pestaña eran **3 `st.metric`, una barra y una tabla plana**.
### ⚠️ El fallo de fondo: respondia la pregunta que ya no se puede accionar
La barra de presupuesto **solo se ponia roja al pasarse**, o sea cuando ya no hay nada que hacer.
- **`expenses.cost_projection(pid, grupo)`** — cuanto costara AL TERMINAR al ritmo actual:
  `proyectado = costo_actual / (avance/100)`. Es el gemelo de "fin proyectado" de v143.
  Con datos reales: *prueba1* lleva $358 al 46% → **$778 final** contra $10.000 de presupuesto.
  El caso que importa: **gastar $6.000 de $10.000 al 30% de avance proyecta $20.000** — hoy la barra
  seguia verde (60% consumido) y no decia absolutamente nada.
  Añade `por_punto` (costo por punto de avance).
- **`expenses.labor_breakdown(pid, grupo)`** — mano de obra POR PERSONA. `labor_cost` recorria los
  fichajes y devolvia **solo el total**, asi que quien consumia las horas era invisible aunque el dato
  estuviera ahi. `labor_cost` pasa a ser un wrapper (mismo total, verificado: 358.8 antes y despues).
  Marca **`sin_tarifa`**: con tarifa 0 las horas suman $0 y parecia que el proyecto no costaba MO.
- **`expenses.spend_curve` + `spend_svg`** — gasto acumulado dia a dia, mano de obra y compras
  **apiladas** (se ve el reparto, no solo el total), con el presupuesto en discontinua gris y la
  proyeccion al ritmo actual hasta donde acabas. Sale de datos que ya existian: las compras traen
  Fecha y cada fichaje aporta horas×tarifa en el dia de su Clock In.
- **Gasto por categoria: se calculaba desde v105 y la pestaña lo TIRABA.** `project_expenses` devuelve
  `por_categoria` y solo lo leia el informe de grupo. Quinta vez del patron "se escribe y nadie lo lee".
- `_barras_html(pares, total, color)` para los desgloses cortos: un `st.bar_chart` obliga a leer un eje
  para nada; la barra con su numero al lado se lee sola.
### ⚠️ El cruce de horas va por NOMBRE de proyecto, no por ID
Encontrado mirando los datos reales: hay fichajes bajo `"Prueba1"` para un proyecto llamado `"prueba1"`
y **esas horas se caian del costo EN SILENCIO**. `_mismo_proyecto()` normaliza may/min y espacios, lo
que tapa ese caso concreto — pero **renombrar un proyecto sigue borrando su historico de mano de obra**.
El arreglo de fondo es guardar el ProyectoID en la hoja de fichaje. PENDIENTE, es cambio de modelo.
### Verificacion
`spend_svg` **medido numericamente** sobre el XML (no mirado): linea de presupuesto en sy(6000)=136.0 ✓
· proyeccion termina en sy(9200)=72.1 y arranca en el ultimo punto x=652 ✓ · roja porque 9200>6000 ✓ ·
2 areas apiladas ✓ · 15 puntos de curva ✓ · sin `<defs>/<marker>` ✓ · degrada a "" con <2 fechas.
Las 4 ramas del titular probadas contra los 3 proyectos REALES + el caso sobre-presupuesto simulado.
`over_budget`, `group_expenses` y `projections_by_group` siguen dando lo mismo; firma de
`render_expenses` intacta para sus 3 call-sites (admin / campo / conductor).

## Pestaña Estado: la grafica deja de ser una imagen plana (v143)
Peticion del usuario: "las graficas se ven planas como simples imagenes, quiero algo mas integrado y
que impacte mas; y los valores, mas informacion mejor presentada".
### ⚠️ El problema de la grafica no era estetico
La **brecha entre plan y real —que es toda la historia— habia que deducirla comparando dos lineas
finas de 2.5 px**. `schedule_svg` reescrito con el lenguaje de los planos (v119-v123):
- **La brecha se RELLENA** entre las dos curvas: **roja si vas por detras, verde si por delante**. Se
  ve cuanto y desde cuando de un vistazo, en vez de estimarla a ojo.
- **HOY cruza TAMBIEN el Gantt** (antes solo la curva) → se ve que actividad cae bajo la linea.
- **Jerarquia en las barras**: terminada (verde) / en curso (azul) / **tocaba y sigue en 0% (roja
  achurada + ● en el nombre)** / futura (gris). Ese cuarto estado es el que senala el problema.
- **Proyeccion al ritmo actual** en trazo discontinuo hasta la fecha proyectada + area bajo la real.
- ⚠️ **`proj_dias` de `schedule_projection` es la DIFERENCIA contra el plan (+tarde/−antes), NO el dia
  absoluto.** Usarlo tal cual ponia el punto de proyeccion en el dia 32 en vez del 61.
- ⚠️ **Tope al eje (`total × 1.32`)**: el eje se estira para que quepa la proyeccion, pero sin tope un
  SPI malo (fecha lejanisima) **aplastaba el Gantt**, que es el contenido principal. Pasado el tope la
  proyeccion se dibuja hasta el borde y se rotula "03/09 ▸".
- ⚠️ **El eje siempre contiene HOY**: con el tope, un proyecto **pasado de fecha perdia su marca de
  HOY** — justo el que peor va.
### La informacion: `_diagnostico(ps)` + `_estado_section(pid, grupo, prj)`
"SPI 0.47" no le dice nada a nadie en obra. Lo que si, calculado de lo que ya habia en `ps`:
- **Ritmo real vs necesario**: "vas a **1,7 %/dia** y necesitas **6,4 %/dia**: hay que acelerar **×3,8**
  en los 11 dias que quedan". Mismo dato que el SPI, en unidades que se accionan.
- **Que tocaba hoy vs que se esta haciendo** (dos columnas) + el diagnostico: "el equipo sigue
  terminando Brackets, Rieles y Cabina, asi que Puertas de rellano aun no ha arrancado. **Ahi esta el
  retraso**". Es la causa, no la constatacion.
- **Proximo hito** con fecha, **titular en una frase** y **tarjetas KPI** (`_kpi_card`) en vez de los 3
  `st.metric` planos: avance real / deberia ir / desvio / situacion / fin proyectado.
- ⚠️ **`proj["today_day"]` viene CLAMPADO al total**: el titular habria dicho "dia 29 de 29" en un
  proyecto que lleva 40. Para mostrar el dia real hay que usar `ps["today_day"]`.
- ⚠️ **El dia en que se abre la ventana de una actividad NO cuenta como retraso** (`inicio < hoy`
  estricto): con `<=`, un proyecto **recien creado nacia con una actividad en rojo**.
### Verificacion
Geometria **medida en el DOM**, no mirada (leccion de v121): HOY dia 18 → x=339.9 ✓ · fin planificado
dia 29 → x=416.8 ✓ · proyeccion dia 61.5 → x=644 (borde) ✓ · punto real 30.2% → y=435.7 ✓ · la banda
de HOY cubre y 46→487 (Gantt + curva) ✓. Cinco escenarios (atrasado / adelantado / al dia / recien
empieza / sin avance) + la **llamada minima `schedule_svg(sched)`** que usan `report.py`,
`user_report.py` y `survey_ui.py` (sigue funcionando, sin HOY ni brecha).
⚠️ `timedelta` **no estaba importado en projects_ui.py** — lo caza el chequeo de nombres libres, y
habria sido NameError nada mas abrir la pestaña.

## Agrupaciones: cartera de tarjetas + creacion plegada (v142)
La lista de agrupaciones era una tabla plana (ID / nombre / nº proyectos / avance) que **no decia nada
util sin entrar**. Ahora usa el MISMO lenguaje que la cartera de proyectos (`_portfolio_html`):
- **`_agrupaciones_html(ags, grupo)`** — tarjeta por agrupacion: punto de estado, nombre, nº de
  elevadores, descripcion, **fecha de entrega del conjunto y que elevador la marca**, barra de avance
  consolidado, horas, costo, 🔔 alarmas y **borde rojo + ⏰ N d** si el elevador critico va retrasado
  (verde + ⏩ si va adelantado). Mismo criterio visual que los proyectos.
- **"➕ Nueva agrupacion" pasa a expander plegado**, como "➕ Nuevo proyecto": no es lo que se viene a
  hacer a diario.
### ⚠️ Rendimiento: la fecha de entrega es CARA
`project_schedule` reconstruye el cronograma de un proyecto y **NO esta cacheado**. Pintar la fecha en
una lista de N agrupaciones × M elevadores lo recalculaba todo en cada rerun — el mismo problema que
resolvio `gaps_by_group` en v107. Fix: **`projects.projections_by_group(grupo)`** cacheado 60 s
({pid: {fecha, spi, gap}}); las tarjetas y `grouping_projection` comparten ese calculo.
REGLA: antes de poner un dato derivado en una LISTA, comprobar cuanto cuesta calcularlo por fila.
### Verificado con datos simulados (render real en navegador)
fecha del conjunto = la del elevador MAS LENTO · señala al critico correcto · badge con el gap del
critico (no el del primero) · horas 210+180+410=800 · costo 3×18500=55.500 · alarmas · borde rojo/verde
· y **agrupacion SIN miembros no rompe** (0 elevadores + "sin cronograma para proyectar").

## Agrupaciones: se invierte el flujo + dashboard de conjunto (v141)
Peticion del usuario: "primero debe existir una agrupacion para que al crear el proyecto se seleccione;
quiero que sea al contrario". Tenia razon — el flujo estaba al reves de como se trabaja: para agrupar 4
elevadores habia que crear la agrupacion VACIA y luego abrir los 4 proyectos uno por uno, editar cada
uno y asignarlo. **Cuatro ediciones en cuatro pantallas, sin ver nunca el conjunto.**
### El flujo se invierte (solo UI: el modelo de datos NO cambia)
La relacion sigue viviendo en el proyecto (`AgrupacionID` + `PesoEnAgrupacion`); solo cambia DONDE se
edita, asi que **no hay migracion**.
- **`projects.set_grouping_members(gid, {pid: peso}, grupo)`** — define de una vez que proyectos la
  componen. Los que salen se DESAGRUPAN (no se borran). Solo escribe los que cambian.
- **`projects_ui._miembros_editor`** — tabla con casilla + peso, reusada al crear y al editar miembros.
  Marca los proyectos que **ya estan en otra agrupacion** para no moverlos sin querer.
- **Peso por defecto 1** (decision del usuario) en los DOS caminos. ⚠️ Motivo real: `grouping_progress`
  es `Σ(peso·avance)/Σpeso`, asi que **con todos los pesos en 0 el avance daba 0** aunque los elevadores
  estuvieran al 100%. Con el flujo viejo era facil que pasara (habia que ponerlo a mano en cada uno).
- El selector de agrupacion del **editar proyecto se mantiene** (decision del usuario): aqui los dos
  caminos son utiles — armar la agrupacion de golpe, o asignar estando dentro del proyecto. No es el
  caso de v140, donde uno era puro residuo.
### Dashboard de agrupacion, reescrito
⚠️ **El avance consolidado NO responde la pregunta que importa.** Un edificio se entrega cuando termina
**el ultimo** elevador, no el promedio. El dashboard decia "62%" y no decia cuando entregas.
- **`grouping_projection(gid)`** → fecha de entrega del CONJUNTO = max(`fecha_proj` por SPI) + **que
  elevador la determina** (el critico). Es lo accionable: ahi es donde rinde reforzar.
- **`grouping_curve(gid)`** → curva S consolidada plan vs real. ⚠️ Cada elevador tiene su propia fecha
  de inicio, asi que **no se pueden sumar por "dia N"**: se llevan todos a un eje de FECHAS y se
  combinan ponderando por peso. Interpolacion lineal entre puntos; 0 antes de empezar, ultimo valor
  despues; la real se corta en HOY. Topado a 100 (los scurve individuales redondean y sumaban 100.2).
  Verificado con dos cronogramas de inicios y pesos distintos: 0% al inicio, 100% al final.
- **Comparativa entre elevadores**: en un edificio son unidades casi gemelas, asi que la desviacion de
  horas/costo respecto al promedio delata al anomalo. Solo se marca si se desvia ≥15%.
- **Alarmas del conjunto** + **tarjetas KPI** (`_kpi_card`, ya existia) en vez de `st.metric` planos.
- **Sin agrupacion preseleccionada** (peticion del usuario; mismo criterio de v138/v139).
Agente IA actualizado en el mismo lote (regla v133).

## Se quita el doble selector de plano (v140)
Residuo mio de v137. v128 dio a las 5 herramientas un plano de SESION compartido; v137 movio el plano
AL PROYECTO (mejor), pero **no quito lo anterior**: quedaron dos cosas seguidas pidiendo el mismo plano.
El usuario abria 🛡 Corte de buffers y veia (1) el selector de proyecto, que rellena HKP solo, y justo
debajo (2) "PDF de planos (para HKP)" pidiendole un PDF **que ya no hace falta**. Ademas los `caption`
seguian describiendo el flujo viejo ("Carga el PDF para leer HKP").
- El uploader pasa a un **expander plegado**: "📄 ¿El proyecto no tiene plano? Cárgalo aquí".
  **NO se elimina**: sigue haciendo falta con un proyecto creado sin plano, o para calcular sin proyecto
  asignado. Solo deja de ser lo primero que se ve.
- Textos actualizados en las 4: ahora describen que los valores vienen del plano del proyecto.
### Verificacion (el plegado es una REINDENTACION, la clase de cambio que rompio v120)
1. Limites del bloque localizados por **AST** (la asignacion `pdf = plan_store.selector` + el `if pdf is
   not None` que lo consume), no por texto.
2. **Orden preservado**: `aplicar()` y las escrituras del uploader siguen ANTES de crear cada widget
   (regla v111) — verificado por linea en las 7 claves afectadas.
3. **Cero lineas de codigo perdidas** (multiconjunto ignorando indentacion); las unicas ausentes son los
   textos que se cambiaron a proposito.
4. Uso-antes-de-asignacion limpio en los 4 (chequeo de v138).
REGLA: al reemplazar un mecanismo por otro mejor, **quitar el viejo en el mismo lote o dejarlo
explicitamente como plan B**. Dos mecanismos vivos para lo mismo confunden y envejecen mal.

## Auditoria de los 38 desplegables (v139)
Pregunta del usuario: "casi todas las listas desplegables tienen un valor preseleccionado, revisa cuales
podemos dejar sin preseleccion". Auditoria completa → **38 selectbox/multiselect**, clasificados por lo
que pasa AL ELEGIR, no por consistencia estetica:
### A · Cuatro que BORRAN — lo serio
`Eliminar grupo` (auth_ui) · `Actividad a eliminar` (projects_ui) · `Manual` (auth_ui) ·
`Agrupación` (projects_ui). Los cuatro tenian el mismo patron: **destino ya elegido + boton de eliminar
al lado, SIN confirmacion**. Un clic de mas borraba algo que nadie eligio. (El de "Eliminar proyecto" si
avisaba; estos no.) Ahora: opcion neutra + **casilla de confirmacion** que habilita el boton.
### B · Seis que ESCRIBEN en un proyecto
Fichaje normal y de conductor, Pre-Start, recibo de gastos, guardar un calculo, destino del survey.
No destruyen, pero **atribuian datos al proyecto equivocado en silencio** — horas y costos al elevador
que no es. Todos con opcion neutra; el boton de guardar queda `disabled` sin destino.
### C · El resto se deja IGUAL (decision explicita)
Marca (Schindler es la unica), Tipo de documento, Categoria de gasto, Rol, Clase, Referencia de riel,
Estado manual y la navegacion por radio: son **valores de configuracion con defecto util**, no acciones.
Quitarles el defecto añadiria un clic sin evitar ningun error.
### `core/ui_common.py`
`elegir(label, opciones, key, vacio)` (acepta lista o dict; con dict devuelve el VALOR) y
`confirmar_borrado(key, texto)`. Viven en un sitio para que los 4 bloques de borrado no divergan.
⚠️ **`st.selectbox` no tiene estado "sin elegir"**: siempre devuelve su primer elemento. Cualquier
desplegable que dispare una ACCION necesita opcion neutra explicita.
### ⚠️ Repetido el chequeo de uso-antes-de-asignar (v138)
Al dejar `_prj = None` en el survey cuando no hay destino, el codigo de abajo seguia usandolo → se
protegio el bloque NS y el boton (`disabled=(_prj is None)`). Chequeo pasado en los 7 archivos tocados.

## Los selectores ya no abren un proyecto que nadie eligio (v138)
Pregunta del usuario: "cuando entro siempre tiene que haber un proyecto preseleccionado en Mi grupo?".
**No, y era un bug de UX real:** `st.selectbox("Proyecto", list(idmap))` **siempre devuelve el primer
elemento**, asi que `if sel:` era SIEMPRE cierto y al entrar se abria el detalle completo de un proyecto
arbitrario debajo de la cartera. Coste medido: **8 lecturas de datos** (proyecto, actividades, horas,
alarmas x2, cronograma, gastos, agrupaciones) que nadie pidio, mas el ruido visual.
- **Admin y propietario**: opcion neutra `_VACIO` como PRIMERA del selector → el detalle solo se abre al
  elegir. El `_prjsel_pending` de v126 (boton "Abrir proyecto ➜") sigue funcionando: escribe la clave
  del selectbox antes de instanciarlo y esa etiqueta sigue en la lista.
- **Campo**: si tiene **fichaje abierto**, se preselecciona ESE proyecto — es donde esta trabajando, y es
  el mismo criterio que usan las herramientas desde v137. Si no ha fichado, opcion neutra.
### ⚠️ Error que cometi + CHEQUEO NUEVO
Use `a.get("nombre")` en `render_field_projects`, cuya firma es `(usuario, grupo)`: **`a` se asigna 42
lineas MAS ABAJO** → `UnboundLocalError` seguro. Y **mi chequeo de nombres dijo "ninguno sin resolver"**,
porque solo comprueba que el nombre exista en la funcion, NO que exista ANTES del uso. Es la misma clase
de fallo que v126.
**Chequeo nuevo (añadir al set):** por cada funcion, comparar la linea del PRIMER uso contra la del
PRIMER asignamiento de cada nombre; si el uso va antes → error. ⚠️ Hay que **excluir variables de
comprension, de `for` y argumentos de lambdas anidadas**: su ambito no sigue el orden textual y dan
falsos positivos (`{f"{p...}" for p in xs}` usa `p` en la linea anterior a su `for`).

## El plano vive en el PROYECTO, no en la sesion (v137)
Cierra la idea de v135: si el proyecto es la entidad principal, **el plano es suyo**. Se lee UNA vez al
crearlo y sus valores alimentan las 5 herramientas para siempre.
- **Columna `PlanoJSON`** en Proyectos (migra sola). ⚠️ **Distinta de `ParamsJSON`**: PlanoJSON es lo que
  DICE el plano; ParamsJSON es el survey, que ademas lleva lo medido en obra (BSR, FS, FRAME, RAIL,
  OFFSET_CABIN). Mezclarlas romperia el paquete de obra (con solo el plano no se puede recalcular).
- **`core/plan_data.py`** — `extraer_todo(pdf, progreso)` corre los 6 extractores en una pasada
  (~75 s con el cache de v136) y devuelve: 17 params + NS + codigo de riel + HQ/HGP + HKP + LFKK/LFGK,
  mas **`faltan`** (lo que el plano NO dio) y `n_params`. Solo ~490 caracteres en la hoja.
  Probado con un plano real: **17/17 params, NS=6, T75-3/B, HKP=70, HQ=14045, LFKK=2915, faltan=[]**.
- **`core/plan_ui.py`** — `selector_proyecto(key)` da el plano segun el ROL (decision del usuario):
  - **admin/propietario**: eligen el proyecto DENTRO de cada herramienta (trabajan varias obras).
  - **campo/conductor**: el proyecto sale del **CLOCK-IN** (`timeclock.open_sessions`), que ya lo pedia
    desde v67 → **cero friccion añadida**. Si no ha fichado, la herramienta se lo pide.
  `aplicar(datos, mapa)` vuelca valores a `session_state` **solo si el campo esta vacio/en cero**, para
  no pisar lo que el usuario ajusto a mano.
- **Al crear el proyecto**: uploader del plano FUERA del `st.form` (dentro, los widgets no escriben hasta
  el submit y no se podria prellenar el NS), barra de progreso por extractor, guarda de identidad
  `name:size` (regla v112), prellenado de NS y modelo, y al guardar → `PlanoJSON` + PDF archivado en Drive.
- **Las 5 herramientas** (Survey, Plomadas, Rieles, Buffers, Belting) leen de ahi.
  ⚠️ `aplicar` escribe claves de widget → **verificado por linea que corre ANTES de crear cada widget**
  (regla v111): plumb 34<65, buffers 35<54, belting 38<66, rieles 35<55, survey 871<977.
- **Aviso de lo que falta**: si el plano no dio un valor se lista, en vez de dejar un cero silencioso.
- Agente IA actualizado en el MISMO lote (regla v133).
### Impacto real
Antes: el tecnico subia el mismo PDF en cada herramienta y esperaba 30-70 s **cada vez**.
Ahora: 0 s y 0 PDFs para el campo; el coste se paga una vez, en el escritorio del admin.

## Extraccion del plano: una sola lectura (v136)
⚠️ **Cada uno de los 6 extractores reparseaba el PDF ENTERO.** Medido sobre un plano real de 5 MB:
params 37 s · NS 28 s · riel 14 s · belting 51 s · HKP 29 s · **LFKK/LFGK 71 s** = **230 s**.
O sea: un tecnico que abria ✂️ Corte de rieles en obra esperaba **71 segundos**, cada vez.
- **`schindler.page_texts(pdf_file)`** — lee el PDF UNA vez y devuelve `[(texto_posicional,
  texto_plano)]` por pagina, cacheado por **md5 del contenido** (max 4 planos; se guarda el texto,
  no el PDF). El texto plano se calcula ahi tambien porque varios extractores lo usan como segunda
  fuente y era otra pasada completa.
- Los 6 extractores (5 en schindler + `rail_cut.extract_lf`) pasan a leer de ahi. **La logica de
  PARSEO no se toco**: mismos regex, mismo recorrido, solo cambia de donde sale el texto.
- **230 s → 79 s** (2.9x). El primero paga la lectura; los otros cinco salen en 0.0 s.
- ✅ **Verificado que los 6 resultados son IDENTICOS** a los de v135 (params, NS=6, T75-3/B,
  HQ=14045/HGP=85, HKP=70, LFKK=2915/LFGK=2693) y que el cache **no mezcla archivos** (un segundo
  plano distinto vuelve a leer y da su propio NS).
REGLA: al tocar los extractores, comparar SIEMPRE los valores contra una corrida previa; son codigo
delicado y un fallo silencioso ahi envenena todos los calculos.

## ⚠️ CAMBIO DE ARQUITECTURA: el survey deja de crear proyectos (v135)
**El PROYECTO pasa a ser la entidad principal y el survey una herramienta que lo alimenta**, igual que
Plomadas, Cortes y Belting. Antes el proyecto SOLO nacia del survey ("Guardar como proyecto"), asi que
no se podia dar de alta una obra hasta tener el survey hecho — pero la obra existe antes que el survey.
### Crear proyecto (nuevo)
`projects_ui._nuevo_proyecto_form(grupo, key)` — expander **➕ Nuevo proyecto** en 🛠 Mi grupo → 📊
Proyectos y en 👑 Administracion → 📁 Proyectos (el propietario elige grupo). Pide nombre, cliente,
ubicacion, modelo, ingeniero, **NS**, fecha de inicio, presupuesto, instrucciones e inducciones.
El **cronograma se genera solo con el NS** (`build_schedule(ns, fecha, {})` → 11 actividades estandar):
no necesita el survey. Incluye aviso de duplicados y el chequeo de credenciales/contacto de v127
(extraidos a `_avisar_asignados` / `_notificar_asignados`, compartidos).
⚠️ **El formulario va ANTES del `return` por lista vacia** en ambos paneles: si no, sin proyectos y sin
el survey como origen, la app se quedaria SIN forma de crear el primero (sin arranque posible).
### El survey alimenta un proyecto existente
`projects.attach_survey(pid, params, matriz, interp)` escribe ParamsJSON/MatrizJSON/InterpJSON en un
proyecto ya creado (via `update_project`), de las que dependen el paquete de obra
(`survey_calc.recalcular`) y "Reconstruir proyecto en el Survey" — **siguen funcionando igual**.
⚠️ `attach_survey` **NO toca las actividades**: el cronograma se crea con el proyecto y el campo ya
puede tener avances cargados; sobrescribirlo los borraria.
El survey ademas registra en la hoja `Calculos` (clave `survey`, añadida a `toolruns.HERRAMIENTAS`) y
archiva plano + matriz + informe del cliente. Si el NS del plano difiere del NS del proyecto, **avisa**
en vez de pisarlo en silencio (el cronograma se calculo con el del proyecto).
### Compatibilidad
Los proyectos existentes ya tienen su ParamsJSON: nada que migrar, solo cambia DONDE se escribe.
### ⚠️ Error que cometi
Al reescribir el bloque invente el kwarg `survey_matrix=` en `generate_user_report`, cuya firma real
lleva `lim_map=`. Habria sido **TypeError al archivar el informe**. Lo caza **validar cada llamada nueva
contra `inspect.signature` de la funcion real** — chequeo que conviene repetir tras reescribir bloques.
El agente IA se actualizo en el MISMO lote (regla de v133): ya no dice "Guardar como proyecto".

## Documentos invisibles + el campo recibe lo suyo (v134)
⚠️ **Bug de 36 versiones, encontrado auditando los modulos pendientes:** `_documentos_section` filtraba
por `_DOC_TIPOS`, asi que **todo documento generado por la app con un tipo ausente de esa lista
desaparecia EN SILENCIO — para TODOS los roles, incluido el admin**:
- **`prestart`** (v97): cada PDF de Pre-Start archivado en el proyecto llevaba 36 versiones invisible.
- **`calculo`** (v129): los PDF de las herramientas nacieron invisibles.
Fix de raiz (no parche): se separa **`_DOC_SUBIR`** (solo alimenta el desplegable de subida MANUAL) de lo
que se VE. El admin/propietario pasa a `ver_tipos = None` → **sin filtro**, asi un tipo nuevo generado por
la app no puede volver a desaparecer. `_CAMPO_VER` suma `prestart` y `calculo`; iconos 🦺 y 🧮.
REGLA: un filtro por lista blanca sobre datos que la propia app genera es fail-closed y falla en silencio.
Para VISUALIZAR, fail-open; la lista blanca solo para lo que el usuario elige al subir.
### El campo por fin recibe lo que se construyo para el
El **paquete de obra** se llama literalmente "PDF para terreno" y hasta ahora **solo podia bajarlo el
admin** (Survey y detalle de proyecto). Los **calculos** (plomada, cortes) los EJECUTA el campo y no los
veia. Ambos estan ya en 📋 Mis proyectos. El bloque del paquete se extrajo a
**`_paquete_obra_section(pid, prj)`**, compartido por el detalle del admin y la vista de campo, para que
las dos no diverjan.
### Auditoria de los modulos pendientes (Administracion / Fichaje / Mis proyectos)
NO tienen el bug v110: los bloques largos bajo `st.button` son ACCIONES que terminan en `st.rerun()`
(verificado distinguiendo accion de render). Ese patron esta agotado.

## Agente IA al dia + limpieza (v133)
⚠️ **El agente llevaba ~35 versiones desactualizado.** Auditoria de su SYSTEM_PROMPT contra las
funciones reales: **desconocia 11** — Corte de buffers (v96), Pre-Start (v97), Maps (v98),
instrucciones/inducciones (v100), rol conductor (v103), credenciales (v104), gastos y presupuesto
(v105-106), paquete de obra (v126), plano unico (v128) y la hoja Calculos (v129). Ademas **no
mencionaba ni una pestaña por su nombre**, asi que tampoco sabia guiar por la interfaz.
Es un fallo INVISIBLE: el agente no dice "eso no existe", responde con lo que sabe o improvisa, y
nadie nota que su conocimiento esta congelado. Afecta a los tres roles a diario.
- Reescrita la seccion "FUNCIONES DE LA APP COPEX" del prompt: las 5 herramientas de calculo (con sus
  dibujos, ficha de replanteo, plano compartido y guardado en el proyecto), gestion de proyectos
  (Mi grupo, detalle en 4 pestañas, Mis proyectos, Administracion) y obra/seguridad/costos (Pre-Start,
  credenciales, gastos, fichaje de 2 relojes, Maps, documentos, alarmas, inducciones).
- **Navegacion POR ROL**: el prompt indica que ve cada rol, para que el agente diga donde esta cada
  cosa segun con quien habla, y avise si esa persona no tiene acceso.
- Intactas: la regla de CONFIDENCIALIDAD y las personas por rol (`_PERSONA`, v91).
- Se elimino `toolruns.list_group`: escrita en v129 para una vista de grupo que nunca se construyo.
⚠️ **REGLA:** al anadir un modulo o pestaña, actualizar el SYSTEM_PROMPT del agente en el MISMO lote.
Un chequeo barato: buscar en `chat_agent.py` las palabras clave de cada funcion nueva.

## Detalle de proyecto: 11 secciones -> 4 pestañas (v132)
`_detalle_proyecto` eran **314 lineas con 11 secciones apiladas en un scroll unico** — el mismo problema
que tenia el Survey antes de v114. Misma solucion: sub-navegacion con **`st.radio`** (NUNCA `st.tabs`,
regla de v56), clave `prj_detalle_sec`.
- **Cabecera SIEMPRE visible** (nombre, cliente, ubicacion, estado, avance, horas, barra): es el
  contexto, no una seccion.
- **📊 Estado**: alarmas · cronograma (curva S real vs plan) · proyeccion EVM/SPI.
- **✏️ Datos**: instrucciones e inducciones · editar datos · actividades · eliminar.
- **💰 Costos**: gastos y compras.
- **📎 Archivos**: paquete de obra · reconstruir en el Survey · calculos de herramientas · documentos.
`_asig_now`/`_aviso_cambio` se mueven con **Actividades**, que es su unico consumidor (verificado antes
de mover, no despues).
### Verificacion del cambio (mecanico, sin tocar comportamiento)
1. **Particion del cuerpo comprobada ANTES de escribir**: los rangos cubren las 313 lineas sin solapes
   ni huecos (assert en el propio script; si no cuadra, no escribe nada).
2. **Cero lineas originales perdidas** (comparacion por multiconjunto ignorando indentacion); las 11
   anadidas son el selector y sus if/elif.
3. **Nombres resueltos** dentro de la funcion.
4. **Sin fugas entre pestañas**: ninguna rama usa un nombre que solo definan otras — el chequeo de la
   clase de bug de v114/v118, aplicado ahora a las 4 ramas del if/elif.

## Mi grupo: el historial de calculos por fin se ve (v131)
⚠️ **Cabo suelto de v129/v130 detectado al revisar Mi grupo:** las cuatro herramientas escribian en la
hoja `Calculos`, pero **NADIE la leia** — `toolruns.list_for()` no se llamaba en ningun sitio. Los datos
entraban y no habia forma de verlos, asi que "cada uso alimenta la base del proyecto" estaba a medias.
- **`projects_ui._calculos_section(pid)`**: en el detalle del proyecto, historial de calculos (fecha,
  herramienta, quien, resumen) con **descarga del PDF archivado** desde Drive. Mismo patron que
  `_documentos_section`.
REGLA: al anadir una tabla/hoja nueva, comprobar en el mismo lote que algo la LEE. Escribir sin leer
pasa los tests (la escritura funciona) y deja la funcionalidad muerta.
### Medicion del detalle de proyecto (pendiente de decidir)
`_detalle_proyecto` = **314 lineas con 11 secciones apiladas en un solo scroll** (instrucciones,
alarmas, cronograma, proyeccion, editar, actividades, paquete de obra, reconstruir, gastos, calculos,
documentos, eliminar). Es el mismo problema que tenia el Survey antes de v114 (7 pasos en scroll unico)
y la solucion conocida que funciono fue sub-navegacion con **radio** (NO st.tabs, regla de v56).

## Survey y primeros lotes (v102-v130) — comprimido en v401

⚠️ **Esto eran 29 secciones y 502 líneas de relato.** Se comprimió a lo que sigue VIVO: las reglas
que nacieron aquí y los contratos que no están documentados en ningún otro sitio. El relato completo
(quién rompió qué y cómo se cazó) está en `git log` y en el ZIP de cada deploy — **no se ha borrado
nada, se ha dejado de cargar en cada sesión**. Si una de estas reglas se rompe, el detalle de por qué
existe está a un `git log -S` de distancia.

### Reglas de Streamlit que nacieron aquí (todas siguen vigentes)
| | Regla |
|---|---|
| **v110** | Un `st.button` **solo COMPUTA** y guarda en `session_state`; el render vive FUERA, o desaparece con cualquier interacción. Los efectos CAROS (IA, correo, escrituras) sí van dentro, para que no se repitan en cada rerun. Era el bug estructural de las 5 herramientas |
| **v111** | **Nunca** escribir `st.session_state[clave_de_widget]` después de instanciar ese widget → patrón **pendiente + rerun** (aplicar antes de crear ningún widget). Es la regla más citada del documento |
| **v112** | Todo `st.file_uploader` que dispare efectos necesita **guarda por identidad de archivo** (`f"{name}:{size}"`): el uploader CONSERVA el archivo entre reruns, así que sin guarda el efecto se repite en cada pasada y pisa lo que el usuario escribió |
| **v117** | Si borras una clave de `session_state`: o la **reinicias** a su valor por defecto, o **todas** sus lecturas pasan a `.get()`. El acceso por atributo (`st.session_state.x`) lanza `AttributeError`; `.get()` no |
| **v118** | Streamlit **descarta el estado de un widget que no se renderiza** en ese rerun. Si puede dejar de dibujarse (fases, tabs, condicionales) hay que «tocar» su clave (`st[k] = st[k]`) o su valor se pierde |
| **v108** | Lecturas de **DISPLAY** siempre por lector cacheado; las rutas de **ESCRITURA** (`clock_in/out`, `add/delete`, `save_activities`, `_find_row`, `verify_login`) leen **FRESCO** a propósito |

### Chequeos que nacieron aquí (repetirlos, no reinventarlos)
- ⚠️ **v120 · `py_compile` no detecta un error semántico.** Un solo error de indentación sacó un bloque
  fuera de su fase y dejó *tres* síntomas (NameError, pasos en la fase equivocada, matriz invisible) con
  el fichero compilando perfecto. **Chequeo tras tocar el Survey:** por AST, los nombres que una fase USA
  y solo la otra ASIGNA — en ambas direcciones debe dar vacío.
- ⚠️ **v126 · dónde CAE la línea que insertas.** Un bloque metido fuera de `_render_survey_results` usaba
  locales de esa función → `NameError` seguro, y el chequeo global de nombres NO lo ve (existen en otra
  parte del árbol). Verificar la función contenedora y que sus locales estén asignadas ANTES de esa línea.
- ⚠️ **v128 · al insertar tras un import, `end_lineno`, no `lineno`.** Con un import multilínea entre
  paréntesis, `lineno` mete la línea DENTRO del paréntesis → SyntaxError.
- ⚠️ **v125 · dos formas de romper una extracción:** copiar el RANGO del primer al último import (arrastra
  lo que haya en medio — se coló la barrera de login entera, que se habría ejecutado AL IMPORTAR: hay que
  recoger las líneas de CADA nodo import), y renombrar la llamada sin la definición (`ImportError` que
  `py_compile` no ve → **importar el módulo de verdad** y resolver cada `from X import Y`).
- ⚠️ **v127 · validar la FIRMA, no el nombre.** `credentials.status_label(estado)` cuando recibe una
  FECHA devuelve `"—"` sin fallar: el aviso habría dicho «White Card: —» en vez de «🔴 vencido». Es el
  primer caso de la que luego se llamaría regla v135.
- ⚠️ **v121 · medir el SVG, no mirarlo.** En dos revisiones a ojo vi fallos que no existían y no vi el que
  sí: la cabina salía FUERA del hueco. Se caza midiendo el DOM del SVG, no observándolo.

### Dominio, del Survey y los planos (esto NO es historia, es cómo funciona)
- ⚠️ **`TL` NO es la profundidad útil de la planta; es `TK`.** `BC_CALC = TS − TKSW − TK/2 − 25`, así que
  desde la pared frontal TKSW (en obra, FL/FR) llega al **eje de rieles**, y ese eje está a **media
  profundidad del cuerpo** (TK/2). Usar TL metía la cabina 1.176 mm hacia atrás y no cabía en TS (v121).
- **OL/OR se miden desde el borde de la cabina** (`LIMIT_OL/OR = BKS/2 + RAIL/2 − BT/2 − FRAME`), así que
  la apertura se POSICIONA con ellos (`dx0 = cx0 + OL`), no se centra y luego se rotula. Comprobación que
  cierra: `OL + marco + BT + marco + OR = ancho de cabina` (v121).
- ⚠️ **v122 · el optimizador va en pasos de 0,5 mm**, así que todo display de RL/FB o de la matriz lleva
  **al menos 1 decimal**: con `.0f`, RL −6.0 y RL −6.5 daban la MISMA etiqueta y dos soluciones distintas
  eran indistinguibles en el desplegable. Helper `diagrams._mm(v)` (entero si lo es, 1 decimal si no).
- ⚠️ **v124 · el log del optimizador es SOLO del propietario** (ni el administrador del grupo cliente lo
  ve): expone los pasos, los descartes y el porqué — la lógica propietaria que el agente tiene prohibido
  revelar (v27) y que el informe del cliente excluye a propósito.
- **v124 · leyenda de color** bajo cada matriz, con las MISMAS palabras que los planos: WR·WL·FR·FL
  incumplen por DEBAJO del límite, OR·OL por ENCIMA.
- ⚠️ **v119 · isométrica: planta a escala real pero ALTURA COMPRIMIDA**, y declarado en el subtítulo (18 m
  contra 1,3 m sin comprimir es una astilla ilegible). El presupuesto reparte el alto entre el rombo de la
  base y la columna; **no poner un piso mínimo a `kz`**, desborda el lienzo. Y en isométrica con Z arriba
  solo se dibujan las caras que MIRAN al observador (esquina inferior = `x=max, y=max`).
- **v119 · escala real con DETALLE ampliado** cuando la holgura mínima del piso baja de 25 mm (×3 a ×40):
  es la razón de ser de la escala real — lo crítico se amplía en vez de falsear todo el plano. Las cotas
  con vano <36 px sacan el valor afuera con directriz.
- ⚠️ **v123 · `bs_check`** — BS del plano contra `SF1+BKS+2·RAIL+SF2`. Si no cuadran, el encaje usa
  (BSR−BS)/2 y **los plomos quedan mal ubicados EN SILENCIO**. Se avisa en la app y en el dibujo.
- **v123 · `di + DBP + dd = BSR` es una IDENTIDAD del modelo**, así que su valor no es como chequeo
  interno sino **como verificación de obra**: el instalador mide di y dd con cinta y comprueba el cierre.
- ⚠️ **v130 · el signo de `Cut*` no está definido en ninguna parte** y la UI solo mostraba el número
  crudo. La leyenda dice «diferencia contra A (mismo valor con signo que la tabla)» en vez de «material a
  cortar»: describe lo que se sabe sin afirmar una dirección de corte. **Sigue PENDIENTE de confirmar con
  el usuario** — es decisión de dominio y el corte es irreversible.

### Piezas que se construyeron en este tramo y siguen en uso
- **`core/plan_store.py`** (v128) — el plano ÚNICO de la sesión: `guardar()` / `actual()` / `selector()`.
  Antes había **cinco `file_uploader`** y el técnico subía el mismo PDF cinco veces. `selector` devuelve un
  `_Plano` (BytesIO **con `.name`**) para que sustituya al UploadedFile sin tocar la lógica de los
  llamadores, que usan `.name` como guarda de identidad (v112).
- **`core/survey_calc.py` → `recalcular(params, matriz)`** (v128) — rehace SOLO la parte determinista del
  cálculo (sin IA, sin correo, sin Streamlit) desde ParamsJSON+MatrizJSON, porque **la solución no se
  guarda: es derivada**. Verificado dando `best` y `lim_map` idénticos al camino del Survey.
- **`core/toolruns.py` + `tool_pdf.py` + `tool_save_ui.py`** (v129-v130) — lo que convirtió las 4
  herramientas de cálculo de islas en algo que alimenta el proyecto: hoja `Calculos`, un solo generador de
  PDF y un solo bloque de guardado. Drive en best-effort (si falla, la fila igual se guarda).
- **`plumb_iso_svg` · `plumb_detail_svg` · `plumb_card_svg`** (v123) — la isométrica con los dos hilos
  cayendo (el replanteo es una operación VERTICAL, que la planta no puede dar), el detalle 3D con caída de
  hilo real, y la **ficha de replanteo**: en el andamio no hace falta un plano bonito, hacen falta 5
  números legibles desde el móvil.
- **`shaft_iso_svg(params, limits, solution, ns, lim_map, proyecto, h_piso)`** (v119) — isométrica 30° del
  hueco completo, con los niveles con incidencia en rojo (reusa `floors_with_issues`).
- **`user_report.py` como presentación** (v116) — portada a sangre (`_portada`), pie «X de Y»
  (`_NumeradoCanvas`, 2 pasadas), **`numero_informe()` → `INF-AAAAMMDD-HHMM`** (único y ordenable, sin
  estado), veredicto con semáforo, tarjetas KPI, glosario, alcance y bloque de firma.
- **Solución ACTIVA elegible** (v115, `sol_activa`) — el optimizador propone varias óptimas y antes
  diagramas/plomado/informe usaban SIEMPRE `best`; al elegir otra se reescribe `best` y se RECALCULA el
  plomado, para que todo aguas abajo quede consistente. Con ella: `floors_with_issues` (filtro de pisos) y
  `floor_plans_pdf` (diagramas sueltos, la vía SIN IA que hizo innecesario el paquete de obra en v146).
- **Aviso de duplicados al crear proyecto** (v126) — un proyecto es un elevador y el survey se repite por
  elevador; sin aviso era fácil crear el mismo dos veces y repartir horas y gastos entre duplicados.
- **Survey en 2 fases** (v114) + **extraído a `core/survey_ui.py`** (v125, 1.243 líneas fuera de `app.py`)
  + **`_cfg_from_state()`**, obligado porque el cómputo usaba locales de una fase que puede no renderizarse.

### Módulos que nacieron en este tramo
- **`core/credentials.py`** (v104) — hoja `Credenciales`; catálogo AU (White Card, Forklift, Dogging,
  Rigging, EWP, Working at Heights, First Aid, Driver License + clases). `status(venc)` =
  vigente / por_vencer (≤30 d) / vencido; `expiring(grupo)`; `notify_expiring` deduplicado por
  `UltimoAviso` <25 d; `matrix(grupo)` para el cumplimiento del equipo (v107).
- **`core/expenses.py`** (v105) — hoja `Gastos`. **Costo total = compras + mano de obra**, con
  `labor_cost` = Σ(horas × tarifa/hora de cada persona) y la tarifa **por usuario** en `Login.TarifaHora`.
  `Proyectos.Presupuesto` + `project_cost` → {compras, mano_obra, total, presupuesto, pct, over}.
- ⚠️ **El fichaje se identifica por `Usuario` (login), no por Nombre** (v106): columna `Usuario` en la
  hoja; las filas ANTIGUAS (sin ella) caen al `Nombre`. Evita mezclar las horas de dos homónimos — el
  fallo que volvió en v151, v306, v319, v348 y que en v363 obligó a un resolvedor único (`clave_de`).
- **Dos relojes en el fichaje** (v103): columna `Tipo` = `general` | `proyecto`, `switch_project` (cerrar
  segmento + abrir otro en un toque) y `group_hours` con `sin_asignar = general − Σproyecto`. Nació con el
  rol `conductor`, **que se eliminó en v163** al comprobar que era un subconjunto del campo; el modelo de
  dos relojes se generalizó a todos los roles en v150.
- **`extract_number_of_stops`** (v102) — el NS se lee del plano; el default de init bajó de 6 a **2**
  (mínimo neutro), porque un 6 por defecto se quedaba pegado y nadie notaba que no se había leído.

### Símbolos que solo se nombran en este tramo
Se listan porque al comprimir eran las ÚNICAS menciones del documento; el detalle está en el código.
- **`diagrams`**: `_hatch` · `_dim_h` · `_dim_v` (achurado y cotas) — ⚠️ `plumb.py` los **importa**, no los
  duplica, y no hay ciclo porque `diagrams` NO importa `plumb`. Además `_leyenda_matriz()` y
  `render_floor_plans_html(floors=…)`.
- **`user_report`**: `_portada` · `_NumeradoCanvas` · `_section` · `_veredicto` · `_kpi_cards` ·
  `_callout` · `_zebra` · `numero_informe()`.
- **`plumb`**: `plumb_iso_svg` · `plumb_detail_svg` (caída de hilo `Hh = dbp*0.72`) · `plumb_card_svg` ·
  `bs_check`.
- **dibujos de corte**: `rail_cut.rail_cut_svg(res, caso, n2500, n5000)` (Caso 1 = alzado real contra la
  pila A; Caso 2 = barras, porque ahí no hay pila que dibujar sin inventarla) y `buffer_cut.buffer_cut_svg`.
- **`survey_ui`**: `_do_calculo()` · `_survey_signature()` · `_cfg_from_state()` · `SURVEY_COLS` ·
  `USER_ONLY` · `_GRUPOS_PARAM` · `_rebuilt_from` (marca de «reconstruido desde el proyecto»).
- **caché y helpers nacidos aquí**: `timeclock._cached_records` / `_invalidate_records` ·
  `auth._group_records` / `_invalidate_groups` · `auth.rate_map` · `timeclock.elapsed_seconds` ·
  `projects.gaps_by_group` · `projects._gaps_for` → `delays_for` / `aheads_for` · `expenses.over_budget` ·
  `expenses.CATEGORIAS` · `credentials.list_for` / `credentials.matrix` · `auth_ui.render_my_credentials` ·
  `projects_ui._dashboard_agrupacion` / `render_group_hours`.
- ⚠️ **v109 · la hoja `Usuarios` del Sheets ya no se usa y la app NO puede recrearla**: al sustituir el
  login por PIN con `auth` (v53) se borró su flujo entero (`timeclock.validate_user`, `_get_users_ws`,
  `USERS_SHEET` / `USERS_HEADERS`). Si algún día reaparece esa pestaña, no la ha creado esta app.
## HOME del admin: densidad + 3 columnas + fix de los deep-links del resumen (v303)
El usuario: *"la veo muy vacía; la agenda y los proyectos están arrinconados; el resumen del día
ocupa mucho espacio; y arriba del buscador hay un espacio en blanco"*. Además dejó dos decisiones
firmes: **la banda azul es SOLO para el nombre de la empresa cliente** (no se fusiona con nada:
"es algo importante que respetar y resaltar") y **la interfaz del admin es para PC**.
### ⚠️ Encoger no arregla "vacío"
La primera propuesta era bajar la altura de las 3 tarjetas KPI. El usuario la rechazó y tenía
razón: una caja grande con un número está vacía, y una caja pequeña con un número **también**,
solo que más pequeña. Lo que llena una tarjeta es INFORMACIÓN. `_kpis()` ya calculaba `total` y
`riesgo` y los tiraba desde v197 → cada tarjeta gana una 3ª línea de contexto (`los 12 en retraso`
· `de 12 obras` · `en todo el grupo`) con **cero lecturas nuevas** de Sheets.
- **`_kpi_pies(k)`** (puro, aparte a propósito) arma los 3 pies; `render_kpis(grupo)` los pinta.
  Se separó para que el chequeo de ancho llame a la FUNCIÓN REAL y no a una copia de su lógica.
- **`render_group_header` ya NO pinta KPIs**: quedan banda + resumen. Los KPIs se mudan a la
  cabecera de la columna del mapa (`home_ui.render_home`) — tres números estirados a 1400 px eran
  justo el vacío del que se quejaba el usuario.
- **La tarjeta de 3 líneas es un `st.button`** cuyo label va `etiqueta\n\nvalor\n\ncontexto`.
  ⚠️ VERIFICADO EN VIVO: `\n\n` da **tres `<p>`** estilables por separado; `  \n` da un `<p>` con
  `<br>` (inservible) y `\n` simple colapsa. CSS en `theme.py`, espejando `.cpx-kpi .lbl/.val/.sub`,
  con `:not(...)` para no tocar una tarjeta KPI de una sola línea.
### ⚠️ El límite del pie es de ANCHO, no de caracteres
`media de 12 obras` y `los 12 en retraso` tienen **17 caracteres los dos** y miden **94 px y 84 px**.
El hueco útil dentro de la columna del mapa es de **93 px** (tarjeta 124 − 28 de padding − borde),
así que el primero saltaba a 2 líneas y esa tarjeta crecía 20 px, descuadrando la fila. Contar
caracteres daba un OK falso. Dos medidas: el pie se acortó a `de N obras` (59 px) **y** el CSS
lleva `nowrap`+elipsis, que es lo que GARANTIZA que las 3 tarjetas midan igual pase lo que pase.
### El resumen del día, sin perder nada
Estructura fija (v196) y nombres visibles (v200) intactos; solo se comprime el envoltorio:
el estado sube al **título** del desplegable (`Resumen del día — :red[3 urgentes] · 5 pendientes`,
se lee aunque esté plegado), el `caption` de la pista pasa al **`help` de cada indicador**
(⚠️ `st.expander` NO acepta `help` — firma comprobada) y los botones bajan de ~52 a **35 px**.
### ⚠️ FALLO REAL encontrado de paso: los "→ Ir a" del resumen iban al sitio equivocado
Las tuplas de los 9 indicadores llevaban **displays** (`":material/bar_chart: Proyectos"`) donde
va el **ID** de la sub-pestaña. `_seccion_proyectos` compara `sub == "📊 Proyectos"` por igualdad
literal, así que **7 de los 9 indicadores abrían Agrupaciones** y "Sobre presup." abría Horas;
"Sin contacto"/"Credenciales" acertaban **por accidente** (Usuarios es el `else`). Corregidos a los
IDs de `home_ui._SUBSECCIONES`. **Guardián nuevo y permanente** en `verif_v303.py`: recorre por AST
TODOS los `_ir_a(...)`/`navegar(...)` con destino literal del repo (16 hoy) y falla si alguno apunta
a una sección o a un ID que no existe.
### Lo demás
`padding-top` del contenido 2.4rem → **1rem** (el hueco en blanco; lo que tapa la cabecera oscura es
la regla `background:transparent` de al lado, no el hueco) · HOME pasa de `[3,2]`+toggle a
**`[2, 1.5, 1.5]`: mapa | proyectos | agenda**, siempre los tres a la vista → muere
`home_right_view` (0 restos) y el pin del mapa ya no tiene que cambiar de pestaña.

## ⚠️ El menú lateral salía CENTRADO: CSS de v229 que Streamlit dejó sin efecto (v304)
El usuario pidió que se distinguiera mejor la cascada del sidebar. Al medirlo, el problema era otro:
**las reglas de alineación de v229 ya no aplicaban** y todo el menú salía centrado (sangría del texto
**99 px** en un botón con `padding-left:12px`). Dos causas, las dos de la misma familia:
1. **Alinear el `<button>` no alinea el texto.** El texto vive en
   `button > div > span > div[stMarkdownContainer] > p`, y ese `div` (234 px) **y su `span`** son flex
   con `justify-content:center` → recentran lo que el botón había alineado. Ese `span` lo metió
   Streamlit DESPUÉS de v229; el CSS se verificó en su día y envejeció en silencio.
2. **Las propiedades de TEXTO puestas en el botón no llegan al `<p>`.** El `font-size:.85rem` del
   nivel 2 y el `font-weight:600` de la sección ACTIVA llevaban versiones sin efecto: medido, los dos
   niveles salían a **16 px** y **peso 400**, activo incluido.
**Fix:** `justify-content:flex-start` + `width:100%` también en `button>div` y `button>div>span`, y
todo lo de texto (`font-size`/`font-weight`/`color`) movido al `p`. Cascada pedida: nivel 1 a **8 px
y peso 600** (activo 700), nivel 2 a **30 px, peso 400 y .85rem** (activo 600) → escalón de **22 px**.
**LECCIÓN (repetida, ver también las trampas de v289-v299):** un CSS "verificado en vivo" caduca
cuando Streamlit cambia el interior de sus widgets. Al retocar un estilo viejo, **volver a medir el
DOM antes de asumir que lo de al lado funciona** — el estilo no falla con un error, falla en silencio.
### De paso: los huecos del resumen del día
Medido el bloque entero: **246 px**, de los que solo 105 eran los 9 indicadores (cabecera 38 + IA 40 +
**46 de huecos**). Los huecos verticales bajan a `.3rem` → **232 px**. ⚠️ La regla va acotada a
`.st-key-cpxresumen` (el expander recibió `key`): suelta, apretaría TODOS los desplegables de la app.

## Resumen del día: de 3 filas a 2 (v305)
El usuario, tras v303/v304: *"entiendo que se redujeron de tamaño pero aún siento que ocupan mucho
espacio"*. El alto del botón ya estaba en su suelo (**35 px**; menos es ilegible), así que la única
palanca que quedaba era el número de FILAS. Medido en el navegador con las etiquetas reales:
| Reparto | Ancho de botón | Resultado |
|---|---|---|
| 9 en UNA fila | 132 px a 1400 de contenido | cabe **solo** con ≥1180 px; a 1150 se parten 4 etiquetas y la fila crece a 52 px → se pierde lo ganado |
| **2 filas (5+4)** | 228 px a 1400 · 179 px a 1150 | **nada se parte en ningún ancho probado** ← elegido |
| 3 filas (v303) | 403 px | lo que había |
**Bloque: 232 → 192 px** (cabecera 38 + 2 filas 75 + huecos + IA 40). Desde el original: 304 → 192.
- ⚠️ `st.columns(5)` en las DOS filas a propósito: el `zip` deja la 5ª celda vacía en la segunda y
  así los 9 botones miden IGUAL (con `columns(4)` la fila corta saldría más ancha).
- ⚠️ **`zip` TRUNCA en silencio**: si una fila tuviera más elementos que columnas, los sobrantes
  desaparecerían sin error. Guardián en `verif_v303.py`: por AST, ninguna fila puede superar el
  número de columnas y las filas deben cubrir los 9 índices sin huecos ni solapes.
- Se pierde el agrupamiento implícito de v196 (las 3 filas eran Proyectos / Equipo / Obra-$), pero
  el ORDEN no cambia y no había ningún rótulo que lo hiciera visible.

## Identidad por ID + tipo de proyecto + el ID a la vista (v306)
Cuatro reglas que fijó el usuario: **internamente todo se relaciona por el ID** (único, irrepetible,
lo pone el sistema); **el nombre es solo comodidad** para su gestión; hay que **distinguir instalación
/ delivery / ripout / otros**; y hay que **poder ver el ID de cada proyecto**.
### Los 3 sitios que aún iban por nombre (auditados a raíz de "¿qué pasa si repito el nombre?")
`create_project` avisa de duplicados pero **no los impide** (a propósito: dos elevadores de la misma
torre se llaman igual), así que un `{Nombre: ID}` colapsa homónimos EN SILENCIO. Ya había pasado en
v147 (documentos) y v150 (fichaje); quedaban tres:
| Sitio | Qué hacía |
|---|---|
| Panel → Asignar (`roster_ui`) | uno de los dos homónimos **desaparecía del desplegable** y no se le podía asignar gente |
| **Facturas** (`invoices_ui`) | el radio mostraba dos opciones idénticas, el filtro casaba con AMBOS y la línea se enlazaba al proyecto equivocado → **se facturaba mal**, no solo se veía mal |
| Inventario (`inventory_ui`) | guardaba el **nombre** en `UbicacionRef`: con homónimos no se sabía en qué obra está el activo, y renombrar dejaba el histórico colgando |
**Fix único:** `projects.etiqueta_proyectos(proys) → {ID: etiqueta}`, con el ID detrás **solo si el
nombre se repite** (sin colisión la pantalla queda limpia). La usan Panel, Facturas, Inventario y
también `timeclock_ui`, que tenía su propia copia y solo marcaba el SEGUNDO homónimo (el primero se
quedaba sin ID, así que seguían sin poder distinguirse).
- **Inventario** pasa a guardar `PRJ-####` en `UbicacionRef` y a resolverlo al mostrar
  (`inventory.ubic_ref_label`). Las filas anteriores guardan el nombre y se siguen leyendo tal cual —
  no hay migración. ⚠️ El **movimiento** (log) guarda el nombre YA RESUELTO: un histórico cuenta lo que
  pasó, no lo que hay ahora. Y `inventory_ui._ubic_txt` era una COPIA de `ubic_str`: ahora delega
  (si no, se habría arreglado el backend y la lista seguiría enseñando `PRJ-0007`; patrón de v140).
- ⚠️ **Guardián permanente** en `verif_v306.py`: por AST, ningún dict-comprehension sobre proyectos
  puede tener como CLAVE el nombre sin el ID. Se afinó para no gritar en falso con las claves
  `f"{Nombre} ({ID})"` (marcaba 5 sitios sanos) y **se probó contra el código roto de v305**, que sí
  detecta — un guardián que no se prueba contra su propio fallo no vale nada.
### Tipo de proyecto (columna `Tipo`, al final → migra sola)
`Instalación · Delivery · Ripout · Otro`. Los proyectos anteriores a v306 quedan **vacíos a
propósito** (no se escribió en la hoja): salen como "sin tipo" hasta que se marquen, en vez de fingir
que todos eran instalaciones.
- ⚠️ **No es cosmético:** al crear se llamaba SIEMPRE a `build_schedule(ns, …)`, así que un delivery
  nacería con las 11 actividades de instalación y una fecha de fin inventada — y ese plan alimenta
  avance, curva S, SPI y el indicador «En retraso». Ahora solo Instalación lo genera; el resto pide la
  fecha de fin a mano (campo nuevo, antes no existía porque siempre salía del cronograma).
- ⚠️ Los demás tipos nacen con **UNA** actividad genérica ("Ejecución"), no con cero: el avance es
  `Σ(peso·avance)/Σpeso` sobre las actividades, así que sin ninguna el proyecto se quedaría clavado en
  0% para siempre y el campo no tendría dónde reportar.
- El selector de tipo va **FUERA** del `st.form` (dentro, los widgets no escriben hasta el submit y el
  formulario no podría reaccionar) — misma razón que v127 y v189.
- `create_project` comprueba que la fila y la cabecera tengan el mismo tamaño y devuelve error si no:
  la fila es POSICIONAL y descuadrarla guarda cada dato en la columna de al lado, en silencio.
### El ID a la vista
En la tarjeta de la cartera (monoespaciada, bajo el nombre), como **primera columna** de la vista
Lista, en la cabecera del detalle, y **buscable** (pegar `PRJ-0007` en el buscador de la cartera lo
encuentra). La cartera gana filtro por tipo, que solo aparece si hay más de un tipo en el grupo.

## Ruta del día: el mapa llena, la ruta existe y se ve el plan CONTRA lo fichado (v307)
El usuario: *"se ve muy desaprovechada"*. Media pantalla en blanco a la derecha del mapa.
### ⚠️ La causa NO era de diseño: `st_folium` dibuja a 500 px FIJOS
Medido en vivo (mini-app + DOM, entrando al `contentDocument` del iframe): el iframe ocupaba
**1110 px** y el `.leaflet-container` de dentro **500** → **610 px de aire blanco DENTRO del mapa**.
`st_folium(..., use_container_width=True)` lo arregla (medido después: 634/634, cero aire). Afectaba
también al mapa de HOME, corregido en el mismo lote. ⚠️ El defecto de la librería es
`width=500, use_container_width=False`: cualquier `st_folium` nuevo tiene que pasarlo.
### Lo que faltaba, y ya estaba escrito
`ordenar_ruta()` y `gmaps_dir_url()` existen desde v270 y **solo las usaba el campo**: la vista del
ADMIN —la que se llama «Ruta del día»— no ordenaba las paradas, no dibujaba el recorrido ni ofrecía
navegación. Ahora sí: paradas numeradas por vecino-más-cercano, polilínea, «Cómo llegar» por sitio y
«Abrir la ruta completa en Google Maps». Otra vez el patrón "se escribe y nadie lo lee" (v131, v148).
### De plan a tablero de despacho
La tabla era Persona/Obra/Dirección: solo decía el PLAN. Ahora lleva **horario** (el roster guarda
`ini`/`fin` desde v277 y se tiraban) y **estado real** — 🟢 fichado aquí · 🔴 fichó en X · ⚠️ sin
fichar — con `timeclock.proyectos_por_usuario_dia`, el mismo dato cacheado que usa «Cumplimiento» en
el Panel. **Cero lecturas nuevas de Sheets.** La pregunta que responde pasa a ser "a las 9, ¿está
cada uno donde debe?".
### ⚠️ Bug de camino: la persona sin ubicación DESAPARECÍA
Si la obra no tenía coordenadas, el bucle hacía `continue` y esa fila **no entraba en la tabla**: el
KPI decía "1 sin ubicación" y no había forma de ver de quién se trataba. Ahora la fila entra igual
(solo queda fuera del mapa, que es lo único que necesita coordenadas).
### Estructura
Mapa (3) | tarjetas de sitio en orden de recorrido (2), y los 4 KPIs pasan a ser **botones activos**
con contexto ("2 · de 3 personas", "1 · sdkm") que llevan a Panel o a Proyectos — el «sin plan» era
un caption muerto al fondo.
⚠️ Chequeo que falló por mi propio comentario: `'[:18]' not in src` daba FALLO porque el comentario
que explica que se quitó ese corte contiene `[:18]`. Se rehízo por AST (trampa nº2 de este documento).

## Fichaje: fix del nombre guardado + la semana + dos columnas (v308)
### ⚠️ FALLO INTRODUCIDO EN v306 (encontrado al auditar esta pantalla)
`fichar_proyecto(nombre, proyecto, …)` escribe `proyecto` TAL CUAL en la columna `Proyecto` de la
hoja, y la UI le pasaba `next(k for k, v in idmap.items() if v == _pid)` — o sea, **la etiqueta del
desplegable**. Desde v306 esa etiqueta lleva el ID cuando hay homónimos, así que el fichaje habría
guardado `prueba (PRJ-0007)` como nombre del proyecto. No rompía las cuentas (manda el `ProyectoID`
desde v145) pero el dato quedaba inventado. Ahora hay un `_nom_de = {ID: Nombre}` aparte y la
etiqueta **solo se muestra**. LECCIÓN: al cambiar lo que muestra un selector, revisar qué se GUARDA
desde él — la etiqueta y el dato son cosas distintas.
- Hermano del mismo error, este anterior a v306: **«Cambiar de proyecto» excluía el actual comparando
  la etiqueta contra el nombre guardado** (`k != prj["proyecto"]`), así que con homónimos te ofrecía
  cambiar al proyecto en el que YA estabas. Ahora se excluye por `prj["proyecto_id"]` (que
  `open_sessions` devuelve desde v145 justo para esto), con respaldo al nombre para fichajes viejos.
### `timeclock.resumen_semana(nombre, grupo, usuario)`
La pregunta de quien ficha es "¿cuánto llevo esta semana?" y no se podía responder: `resumen_hoy`
solo cuenta el día. Nueva tarjeta **Esta semana** (lunes→hoy + nº de días con jornada). Sale de
`_cached_records` → **0 lecturas nuevas**. ⚠️ Semana NATURAL, no `group_hours(days=7)`: esa es una
ventana móvil (un lunes por la mañana arrastraría el viernes anterior) y además con `days=0` se
interpretaría como "todo el histórico".
### Estructura
El **estado deja de ser una tarjeta KPI** (no es una cifra, y sin fichar la pantalla eran cuatro
ceros): pasa a una franja de color con el detalle al lado. Jornada y Proyecto van ahora **lado a
lado** en vez de apilados con un divisor y botones de 1350 px (medido después: 523 px, y los
anidados 253 sin partir texto). ⚠️ En móvil Streamlit apila las columnas solo, así que el campo
—que es quien más usa esta pantalla— no pierde nada.
- ⚠️ La reindentación del bloque de Proyecto bajo su columna se hizo POR SCRIPT midiendo el rango
  (es la clase de cambio que rompió v120 y v148): 0 líneas perdidas y verificado por AST que cada
  columna se quedó exactamente con sus widgets (`col_jor`: tc_gen_*; `_prj_ctx`: tc_prj_*/tc_switch*)
  y que no hay keys duplicadas.
- ⚠️ Comprobado en vivo que `st.columns` DENTRO de una columna **no revienta** en Streamlit 1.57
  (ni dos niveles). La nota de v217 sobre "doble anidación de columnas" era cautela, no un límite
  real; lo que sí es error de Streamlit es el expander dentro de expander (v210).

## ⚠️ DOS `$` EN LA MISMA CADENA = LaTeX (fallo en las 3 pantallas de dinero) — v309
Encontrado al revisar el P&L, donde se veía `Por pagar (nóminas): ** 0.00** · pagado 1,287`.
**Streamlit trata lo que hay entre dos `$` de una misma cadena como fórmula.** Barrido del repo
por AST (no grep: cuenta comentarios) → **5 sitios**, y medido en vivo qué hacía cada uno:
| Sitio | Qué se veía |
|---|---|
| P&L «Por pagar» | los `$` **desaparecen** y los `**` salen literales |
| **Facturas** — Subtotal/Impuesto/Total (2 sitios) | **KaTeX de verdad**: la línea sale como fórmula ilegible |
| **Facturas** — `metric(help="Cobrado $X de $Y")` | pierde los símbolos: `3,145 de 3,145` |
| **Nóminas** — `38 h × $37.75 = base **$1,434.50**` | KaTeX |
**Fix:** `theme.dinero(valor, dec)` — formatea **y escapa** (`\$`). Vive en el sistema de diseño
porque el fallo vuelve cada vez que alguien escriba `f"${x:,.2f}"` a mano, y vuelve en las pantallas
de dinero. Con una sola cifra el escape es inofensivo (verificado), así que se escapa SIEMPRE en vez
de contar dólares. ⚠️ Verificado que imprime **idéntico** al formato anterior (incluido el redondeo
al par de Python) — si no, cada cifra de la app habría cambiado en silencio con el deploy.
**Guardián permanente** en `verif_v309.py`: por AST, ninguna cadena de `st.markdown/metric/caption/
button/…` puede llevar dos `$` sin escapar.
## P&L: periodo, desglose y enlaces (v309)
- **Periodo** (Este mes · Trimestre · Este año · Todo): `finance.pnl(grupo, desde, hasta)`. Qué fecha
  manda: factura→`Fecha`, nómina→**`PeriodoHasta`** (el coste se devenga en el periodo que cierra,
  no el día que se paga) y compra→`Fecha`. ⚠️ Una fila **sin fecha legible** entra solo cuando NO hay
  periodo: con periodo, contarla sería inventarse en qué mes ocurrió.
- ⚠️ Las compras pasan de `group_expenses` (agregado) a recorrer la hoja Gastos filtrando por los
  proyectos del grupo — **el mismo conjunto de filas**, para que sin periodo el total sea idéntico.
  Comprobado en el test, no supuesto.
- **Desglose honesto:** facturado **por cliente** (barras) y **composición del costo** (torta,
  nóminas vs compras). ⚠️ NO hay "ganancia por proyecto": las nóminas son por PERSONA y no por obra,
  así que repartirlas saldría inventado. Se dice en el código para que nadie lo "arregle" luego.
- «Por cobrar» y «Por pagar» dejan de ser texto: llevan a 🧾 Facturas y 👥 Nóminas.

## ⚠️ UNA sola definición de "gasto del grupo" — los archivados volvían a $0 (v310)
La pantalla de Gastos se contradecía: **`COSTO ACTUAL $0`** y justo debajo la torta con **$1.500**.
Auditada la hoja REAL en solo lectura (gspread crudo, sin pasar por los helpers: tras tocar
`PROJECTS_HEADERS` en v306, una "lectura" por ahí MIGRA la cabecera y escribe — regla v145):
las 2 compras del grupo son de **PRJ-0001, archivado**. Ni huérfanas ni IDs fantasma.
**Causa:** `group_expenses` recorría `list_projects(grupo)`, que **oculta los archivados desde
v149**, mientras `por_categoria` suma por la columna `Grupo`. Archivar un proyecto no des-gasta el
dinero → ahora las filas se sacan con `incluir_archivados=True` y el total del grupo es
`compras_grupo` (todas las del grupo). El KPI y la torta por fin dicen lo mismo.
- **Huérfanas visibles:** una compra sin `ProyectoID` (o de un proyecto borrado) se sigue contando
  en el costo del grupo y ahora **se avisa** ("$X en N compras sin proyecto"), en vez de sumarla a
  la torta y no verla en ninguna fila. Invariante que comprueba el test:
  `total del grupo == Σ compras por proyecto + huérfanas`.
- **El P&L usa la MISMA definición.** Había llegado a haber **tres** respuestas a la misma pregunta.
- **Se quitó el bloque de barras «Compras por categoría»**: mostraba exactamente los mismos números
  que la torta (mismas categorías, mismos $ y %). La torta se queda (la pidió el usuario en v224 y
  además incluye la mano de obra).
- **NO se le puso periodo** a esta pantalla, aunque estaba en el plan: «% consumido» y «proyección al
  terminar» son acumulados contra un presupuesto de toda la obra, y un filtro por mes los haría
  mentir. El P&L (v309) es el que responde "cómo fue agosto".
### ⚠️ Dos tests que dieron OK EN FALSO (y cómo se cazaron)
1. **v309 afirmó "sin periodo el total es idéntico" y era MENTIRA**: el mock de `list_projects`
   devolvía la misma lista con y sin `incluir_archivados`, así que no podía ver la diferencia. En
   producción las compras pasaron de $0 a $1.500 y la ganancia de $1.710 a $210 sin que el test se
   enterara. → **Un mock que ignora el parámetro que estás probando garantiza un OK falso.**
2. **`group_expenses` está CACHEADA (v108)**: el segundo caso del test devolvía el resultado del
   primero (1.500 en vez de 1.700). → Limpiar `st.cache_data` entre casos.

## Detalle de proyecto (Estado): se reordena para no dejar media pantalla vacía (v311)
### ⚠️ El markdown NO se procesa dentro de HTML
El titular salía literalmente como `Vas **54 puntos por debajo** del plan`: se emitía con
`**...**` **dentro de un `<div>`** (`unsafe_allow_html=True`), y ahí Streamlit no interpreta
markdown. Ahora va con `<b>`. Regla: si el texto viaja dentro de HTML, el énfasis va en HTML.
### Los tres desperdicios, medidos
1. **Columnas desparejas.** `[3,2]` con el bloque CORTO (titular + 4 tarjetas) enfrente del LARGO
   (6 alarmas + tabla de horas) → la izquierda quedaba vacía ~800 px. Y abajo otro `columns(2)` con
   «Tocaba hoy» (una línea) contra «En curso ahora» (10 actividades). **Ahora lo corto va arriba a
   ancho completo y abajo se enfrentan dos bloques LARGOS** (actividades | alarmas + equipo).
2. **El cronograma estaba topado a 760 px** (`VW=760` + `max-width` + `margin:0 auto`): centrado en
   1340 dejaba 290 px de margen a cada lado, y con `ML=214`/`MR=116` las 13 barras vivían en
   **430 px**. `vw` pasa a ser PARÁMETRO; la app pide 1280 → área útil **950 px**.
   ⚠️ **El default sigue en 760 a propósito**: este mismo SVG va a los informes PDF, donde svglib lo
   escala al ancho de página; con lienzo ancho y el mismo alto, las filas se aplastarían. Verificado
   que `report.py`/`user_report.py` no pasan `vw` y que svglib sigue convirtiendo el SVG.
3. **«Tocaba hoy» y «En curso ahora»** se fusionan en UNA lista de actividades con su estado.
### El pie del gráfico se recortaba
El `components.html` llevaba `height=300 + n*21` puesto a ojo: **18 px menos** que el alto real del
SVG. Nuevo `schedule.schedule_svg_alto(n)` con la MISMA fórmula que `VH`, así no pueden divergir.
### ⚠️ Tres chequeos que fallaron por el test, no por el código (en una sola tanda)
- Buscar los titulares por "texto que contenga 'puntos por'" pillaba **mi propio comentario** → 5 en
  vez de 3. Igual con «Tocaba hoy»: el único resto era el comentario que explica la fusión →
  hay que comparar sobre el código **sin comentarios** (`tokenize`).
- El alto se comparaba con `n` pedido (13, 25) mientras `build_schedule(6)` da **11** actividades:
  se comparaban dos `n` distintos. Usar el `n` REAL de la rebanada.
- El cronograma falso escrito a mano no tenía la clave `scurve` y el test petaba por su culpa →
  usar `build_schedule` de verdad en vez de inventarse la estructura.

## MODELO DE NEGOCIO (fijado por el usuario) y la conciliación de mano de obra (v313)
El usuario, al preguntársele qué cifra es "la buena":
> *"Yo pago las horas fichadas sean o no de un proyecto + lo de ley. Las horas fichadas en un
> proyecto se cargan a ese proyecto, es lo que se le cobra al cliente… más un factor de ganancia."*

**Verificado que el código YA lo implementa**: `timeclock.horas_por_usuario_rango` (base de la
nómina) usa las horas de **JORNADA**; `expenses.labor_cost(pid)` usa las **imputadas a esa obra**;
`finance.group_profitability` cobra `MO × (1+margen) + materiales`. No había que elegir entre dos
definiciones: **son dos preguntas distintas y las dos son correctas**.
| | Qué responde | Fuente |
|---|---|---|
| **Lo que pagas** | cuánto cuesta la empresa | jornada × tarifa **+ aportes de ley** |
| **Lo que cargas** | cuánto vale lo imputado a esa obra | horas del proyecto × tarifa |
Lo que faltaba era **el puente**. `finance.conciliacion_mo(grupo, desde, hasta)` (v313):
```
  cargado a obras (horas de proyecto × tarifa)
  − horas cobradas que NO se pagaron  (imputadas sin jornada abierta)
  + horas pagadas que NO se cargaron  (jornada sin imputar: traslados, espera)
  = base a pagar
  + aportes de ley (super)
  = costo real de la mano de obra
```
Con los datos REALES del usuario cierra exacto: `1.645,20 − 358,80 + 0,40 = 1.286,80`;
`+147,98 (super 11,5%) = 1.434,78`, que es justo el `costo_nomina` del P&L.
- ⚠️ **`sin_explicar` no se cuadra a la fuerza**: si una nómina se editó a mano la cadena deja de
  cerrar y **se dice**. Probado con una nómina alterada (delata los 286,80 de diferencia).
- **Los tres huecos son el margen real** y no se veían en ninguna pantalla: el **super** (lo pagas y
  no lo cargas), las **horas sin imputar** (traslados/espera: las pagas y no las cobras) y las
  **horas imputadas sin jornada** (las cobras y no las pagaste — 358,80 en el grupo real, y esas
  INFLAN el margen). Avisos nuevos para los tres, más "sin tarifa/hora → su trabajo cuenta $0".
- **Se renombran las cifras** para que no se llamen todas "costo": P&L → «Costos (lo que pagas)»,
  Gastos → «Costo cargado a obras», Rentabilidad → «Costo cargado» (con `help` explicando que NO
  incluye ley ni horas sin imputar: eso lo cubre el margen).
- **Aviso de margen 0%** en Rentabilidad: con margen 0 el "ingreso estimado" es idéntico al costo y
  la ganancia sale $0 — la pantalla parecía rota y solo faltaba poner el margen.
### ⚠️ Hallazgo de negocio (con los números del usuario)
El P&L decía **ganancia $1.710** en «Este mes». Con todo el histórico son **$210,42**
(`3.145,20 − 1.434,78 − 1.500`): la factura es del **09/08** y las compras del **28/07**, así que un
P&L por mes natural separa un ingreso de los costos que lo produjeron. No es un bug del filtro; es
que falta poder ver el resultado **por proyecto/factura** además de por mes.

## Ruta del día: el vacío de la cabecera (v314)
Tres causas, ninguna estética de fondo:
1. **Título duplicado.** `home_ui._sub_header` ya pinta «Planificación · Ruta del día» y la función
   repetía «Ruta del día de la cuadrilla» justo debajo. **Es la tercera vez que aparece este
   patrón** (v212 con el % de avance, v291 con el Panel): al escribir una vista nueva hay que
   recordar que la cabecera de sección YA la pone la shell.
2. **`date_input` a 1340 px** para una fecha. Se acota a ~305 px y a su lado van **saltos de día**
   (◀ ▶), que es como se usa la pantalla: "hoy, ¿y mañana?". ⚠️ El salto se aplica escribiendo
   `rutadia_fecha` **antes** de instanciar el widget (regla v111).
3. **Caption que explicaba el título** → al `help` del selector.
### ⚠️ Fin de semana: todos salían «sin plan» sin explicación
`roster.asignaciones_dia` devuelve `[]` en sábado y domingo (la rejilla es Lun–Vie), así que al
elegir un fin de semana la pantalla decía "N sin plan" y no había forma de saber por qué. Ahora se
dice y se corta ahí. Al lado del selector se muestra el día de la semana en texto.

## Detalle de proyecto: la CABECERA, densa (v315)
⚠️ **Esto se prometió en v311 y no se hizo**: se dijo "avance y horas se van dentro de la tarjeta"
y en aquel deploy solo se tocó la mitad de abajo de la pantalla. Aquí se cumple.
La cabecera eran: tarjeta del proyecto (con la mitad derecha vacía) + **dos `st.metric` de ~660 px
para dos números** + una **barra de progreso a ancho completo que repetía el mismo %**. Todo eso
entra ahora en la tarjeta: barra fina + `0% avance` + `0.0 h trabajadas` en una sola línea, usando
el hueco que la tarjeta ya tenía. Y fuera el `---` entre «← Volver a la cartera» y la tarjeta.
**Medido en vivo (mini-app con el tema real): 196 → 104 px, −92 px**, más ~35 del separador.
Verificado que no queda ningún `st.metric` ni `st.progress` en la cabecera.

## Sub-navegación del proyecto: al segmentado del kit (v316)
El usuario pidió "algo parecido a la fila del Panel (radar/asignar/trabajos)". ⚠️ **No es lo mismo**:
esa fila es un **acordeón de herramientas OPCIONALES** (se pueden cerrar todas); Estado/Datos/Costos/
Archivos son **secciones excluyentes** y siempre hay una abierta. Copiarla dejaría cerrar todo y
quedarse sin contenido. Para "una de N" el kit ya tiene la pieza: el **segmentado** de v292.
Medidos los tres candidatos con el tema real:
| | Ancho del control | Bolitas | Marco | Activo |
|---|---|---|---|---|
| `st.radio` de siempre | 430 px | **visibles** | no | no |
| **segmentado `cpxseg_`** | **412 px** | ocultas | sí | sí (`rgb(232,238,246)`) |
| fila de botones del Panel | **1120 px** (estirados) | — | — | requiere CSS propio |
Cambio: la KEY pasa a `cpxseg_prj_sec` / `cpxseg_fld_sec` (el CSS del kit engancha por el prefijo).
- ⚠️ **Las OPCIONES no se tocan**: siguen siendo los IDs con emoji, que son los que usan el matching
  y los deep-links (v232/v234). Verificado por AST que las 4 opciones y las ramas siguen igual.
- Se aplica también a 📋 Mis proyectos del CAMPO: la misma pieza en las dos pantallas.
- Fuera el `---` que iba debajo: el segmentado ya trae marco.

## Resumen financiero = torre de control (v317)
Petición del usuario: *"que el resumen de finanzas sea parecido al panel de planificación o al
home, en interacción y en ver mucha información en poco espacio de forma organizada"*. Se le mostró
un mockup y lo aprobó. La torta se probó FIJA (v317) y en cuanto la vio prefirió tenerla **como una
herramienta más** (v318): así la pantalla arranca en la rejilla y cada gráfico se pide al mirarlo.
Se reutilizan las dos mecánicas que ya funcionan, sin inventar patrones nuevos:
- **Rejilla FIJA de 8 pendientes clickeables** (patrón del «Resumen del día», v196/v199), en 2 filas
  de 4 (v305): Vencido · Por cobrar · **Sin facturar** · Por pagar / **Horas sin nómina** · Sin
  tarifa · Sin margen · Sobre ppto. Cada uno colorea por severidad, y al tocarlo muestra *cuáles* y
  un «→ Ir a» a la sub-pestaña donde se resuelve. **Cuatro de los ocho no existían en ninguna
  pantalla** y son los que cuestan dinero: trabajo sin facturar, horas que se cobran sin pagarse,
  gente sin tarifa y obras a margen 0%.
- **Fila de 4 herramientas que se abren debajo** (patrón del Panel, v287): Conciliación · Por
  cliente · Composición · **Por proyecto**.
### `finance.resultado_por_proyecto(grupo)` — lo que un P&L por mes NO puede decir
⚠️ **ACUMULADO a propósito: NO acepta fechas.** Con el grupo real, «Este mes» daba ganancia $1.710
porque la factura es del 09/08 y las compras del 28/07; la obra ENTERA dejó **$0** (se facturó
exactamente al costo, margen 0%). Una obra se mide de principio a fin, no por meses naturales.
El costo aquí es el **cargado** (horas imputadas × tarifa + compras), no lo que sale de caja: los
aportes de ley y las horas sin imputar no son de ninguna obra — los cubre el margen (`conciliacion_mo`).
- `finance.sin_facturar(grupo)`: obras con trabajo hecho y aún sin facturar. Antes había que entrar
  a CREAR una factura para enterarse de que había dinero sin pedir.
- Verificado por AST: 8 slugs sin repetir (una key duplicada revienta la página), las filas cubren
  los 8 sin huecos y **ninguna supera el nº de columnas** (`zip` trunca en silencio, lección v305),
  y los 8 destinos «→ Ir a» existen en `home_ui._SUBSECCIONES`.

## Nóminas: lo que la pantalla CALLABA (v319)
La revisión era de interfaz y lo grave estaba en los datos que la lista dejaba pasar:
1. **4 de 5 nóminas con base $0.** `asfgjjd` trabajó 8,7 h y su colilla decía **$0** porque esa
   persona **no tiene tarifa/hora**. ⚠️ `payroll.generar` YA lo detecta (devuelve `sin_tarifa`),
   pero eso se muestra UNA vez al generar y después la lista deja las colillas a cero como si
   estuvieran bien. Ahora se avisa en la lista, con nombres y botón a Usuarios.
2. **Dos filas `fijiofgjei` indistinguibles**: distinto login, mismo nombre, y la tabla solo
   mostraba `Nombre`. Nuevo **`auth.etiqueta_usuarios(users)`** → añade el login **solo si el
   nombre se repite**; es la misma regla que `projects.etiqueta_proyectos` (v306) aplicada a las
   personas, y el mismo fallo que el reporte de Horas ya había tenido en v151.
3. **Gente con horas y SIN nómina en el periodo** (el hueco de $358,80 que el resumen financiero
   marca como «Horas sin nómina»): se avisa AQUÍ, que es donde se arregla, usando
   `timeclock.jornada_y_proyecto` (v313).
4. **Columna `Tarifa/h`** (vacía = no la tiene puesta) para que «Base $0» tenga explicación, y pie
   con totales de base y neto.
5. **Filtro de periodo**: hoy son 5 filas del mismo periodo; en un año son 60.
⚠️ **NO se bloquea** generar una nómina con tarifa 0: solo se avisa. Cambiar eso altera el
comportamiento y el usuario no llegó a decidirlo.
### ⚠️ Título duplicado: CUARTA vez (v212, v291, v314, v319)
`_sub_header` ya pinta «Finanzas · Nóminas» y la función repetía «Nóminas». Deja de ser anécdota:
**al escribir cualquier vista nueva, la cabecera de sección ya la pone la shell.**

## Horas del grupo + BARRIDO de títulos duplicados (v320)
### El barrido que se prometió en v319
Escaneadas por AST **las 26 vistas** que despacha la shell. ⚠️ Solo son duplicado las que cuelgan de
una sección **con sub-pestañas** (ahí `_sub_header` pinta «Sección · Sub»); las del campo (Fichaje,
Mis colillas, Mis credenciales, Mis proyectos) son secciones SIN subs, así que su título es el único
y **debe quedarse**. Quitados 4: Gastos, Horas, Rentabilidad y Facturas.
⚠️ **Pre-Start NO se toca**: se despacha en los DOS sitios — sub de Herramientas para el admin (con
`_sub_header`) y sección propia para el campo (sin él). Quitarle el título dejaría al campo sin
cabecera. Las 4 herramientas técnicas tampoco: su título añade información («Cálculo de líneas de
plomada» ≠ «Plomada»).
### Horas: el KPI «sin asignar» daba una cifra que no era calculable
`En proyectos` (49,8 h) sale **MAYOR** que `Jornada` (42,1 h) porque alguien fichó a una obra sin
abrir jornada (comportamiento anterior a v150). La tabla ya marcaba «—» por persona (v151), pero el
**KPI del grupo seguía mostrando 1,2 h y un 3%** como si el dato fuera bueno. Ahora, si hay alguna
fila indeterminada, el KPI pone **«—»** y sale un error explicando quién y cuántas horas — que es,
además, el mismo hueco que el resumen financiero llama «horas sin nómina»: se cargan al cliente y
no entran en ninguna nómina.
- **«Costo M.O.» → «M.O. cargada a obras»**: tras v313 la app distingue lo que PAGAS de lo que
  CARGAS, y esta cifra es la segunda. Llamarla "costo" a secas la hacía indistinguible del «Costos»
  del P&L, que es otro número.
- Fuera los proyectos con **0,0 h** del reparto (barra vacía = ruido); se filtra por el valor
  REDONDEADO, que es el que se ve en pantalla.

## Rentabilidad: el margen se edita AQUÍ + estimado vs facturado (v321)
### ⚠️ Fallo introducido en v310: el margen del ARCHIVADO se ignoraba
`group_profitability` recorre `group_expenses`, que **desde v310 SÍ devuelve los archivados**, pero
construía el mapa de márgenes con `list_projects(grupo)` — que los excluye. `mmap.get(pid, "")` daba
`""` y esos proyectos caían al **default del grupo** en vez de usar el suyo, en silencio.
**LECCIÓN: al ampliar una fuente, revisar los mapas que se cruzan con ella** (mismo patrón que el
`project_hours_bulk` de v145). El test lo caza porque su mock **respeta `incluir_archivados`** — si
devolviera lo mismo siempre, daría OK en falso (la trampa de v309/v310).
### La pantalla
- **El margen se edita en la propia tabla** (`st.data_editor`, solo esa columna). El aviso decía "ve
  a Datos del proyecto" estando ya en la lista de márgenes. Se guarda solo lo que CAMBIÓ.
  ⚠️ Es **una escritura por proyecto cambiado**: con 6 obras da igual, con 60 hay que agrupar (429 de v80).
- **Estimado contra realidad**: columnas y KPIs de **Ya facturado** y **Por facturar**. `por_facturar
  = ingreso − facturado`, que es la MISMA fórmula de `invoices.pendiente_de_facturar` pero sin
  llamarla una vez por proyecto (se usa el mapa cacheado `facturado_por_proyecto`).
- Las obras **sin movimiento** (ni costo ni facturación) se van a un desplegable: eran 5 filas de
  ceros de 6. ⚠️ Una obra facturada SIN costo registrado NO se aparta (sigue siendo rentabilidad).

## Revisión de código: limpieza + archivar deja de deshacer un edificio (v322)
Petición del usuario: *"dale una revisión al código, que todo esté bien, que no haya líneas
muertas o mejoras al código"*.
### Lo muerto (verificado por AST, no por grep)
**8 funciones sin una sola referencia en todo el repo** (−124 líneas) y **27 imports sin usar**
en 20 archivos. Las 8: `projects_ui._agrupaciones_html` (−83, la sustituyó `_cartera_agrupaciones`
en v214), `home_ui._placeholder`, `roster.asignacion_dia` + `semana_str`, `session_cookie.available`,
`payroll.costo_empleador`, `plan_data.hay_datos`, `plan_store.hay_plano`.
⚠️ `grep` cuenta **mis propios comentarios** como uso (ya mordió 4 veces): la referencia solo vale
si aparece como `Name`/`Attribute` en el AST.
### ⚠️ EL HALLAZGO: archivar un ascensor DESHACÍA el edificio
`list_projects` oculta los archivados desde v149 — correcto para una lista, **falso para una
agrupación**. Las **6** consultas de miembros lo usaban por defecto, así que archivar un ascensor
de una torre cambiaba **en silencio** el avance consolidado, la fecha de entrega, la curva S y las
alarmas del conjunto. Es la misma familia que v145 (horas), v310 (dinero) y v321 (márgenes):
**archivar no des-construye el ascensor**, igual que no des-gasta el dinero.
### ⚠️ Y la regresión que ese arreglo introdujo (cazada en la verificación)
Al pasar `set_grouping_members` a leer los miembros CON archivados, el editor de miembros —que
lista solo activos— dejaba de tener casilla para el archivado, así que al guardar caía en el bucle
de **bajas y se desagrupaba solo**. Arreglado añadiendo a la lista del editor los miembros
archivados que faltaban. **Antes del cambio no pasaba** porque los dos lados lo ignoraban por igual:
ampliar UNA fuente sin mirar quién la cruza es justo el patrón de v145 y v321.
### ⚠️ Mi guardián solo veía UNA de las dos formas de escribir la consulta
Lo escribí buscando el kwarg `agrupacion_id=`, y `_cartera_agrupaciones` filtra **a mano**
(`[p for p in proys_all if p["AgrupacionID"] == aid]`) → se escapó, y la tarjeta contaba menos
elevadores que el `grouping_progress` de su propio %. El guardián ahora cubre las dos formas
(kwarg, comprensión inline y comprensión sobre una variable) y **se prueba contra el código ROTO**,
no solo contra el sano: un guardián que solo aprueba lo que ya funciona no demuestra nada.
### Falsos positivos de mi propio chequeo de nombres libres
Salieron **83** y **los 83 eran cierres**: una función anidada usa variables de la que la contiene.
Con el ámbito exterior en la cuenta quedan **0**. ⚠️ Y hay que subir el ámbito nivel a nivel: con
`ast.walk` un NIETO se compara contra el ámbito del abuelo y los parámetros del padre salen como
"sin definir" (pasó con `survey_ui.make_highlighter > _highlight`).
### Auditado y NO tocado (queda anotado)
Duplicación de helpers (`_num` en 14 módulos, `_records` en 12, `_ws` en 10, `_next_id` en 9,
`is_configured` en 15), ~100 `except: pass` silenciosos, y escrituras dentro de bucles (la peor,
`credentials.notify_expiring`, corre en cada login de admin). Son refactors de riesgo real sobre
código que funciona; van aparte, no en una limpieza.

## Los helpers duplicados NO eran cosmética: la divergencia ERA el fallo (v323)
Segunda pasada de la revisión: en v322 dejé anotada la duplicación de helpers como
"refactor sin beneficio visible". Al medirla, **estaba equivocado**: no eran 14 copias
del mismo código, eran **5 implementaciones DISTINTAS** de `_num`, 2 de `_parse_date` y
7 de `_col_letter`, y dos de esas divergencias son fallos de dinero.
### ⚠️ `_num`: cualquier importe con separador de miles valía $0,00
Las 5 variantes hacían `float(v)` o `float(str(v).replace(",", "."))`. Con `1,234.56`
—que es justo como Sheets formatea el dinero en AU/US— las **cinco** revientan y
devuelven **0.0 en silencio**. Medido: de 9 casos de formato, 13 resultados incorrectos
repartidos por costos, facturas, nóminas e inventario.
- **Auditada la hoja REAL en SOLO LECTURA** (gspread crudo con scope `readonly`: los
  helpers de la app migran cabeceras al acceder, regla v145): **0 casos hoy**. El fallo
  es LATENTE, no activo — todo lo que hay lo escribió la app (`number_input` → float
  plano). Por eso era el momento de unificar: **está demostrado que no cambia ningún
  número existente** (5000 importes en formato de la app, 0 diferencias).
- Vive en **`core/num.py`** (módulo HOJA, no importa nada de `core` → sin ciclos).
  Regla: con los dos separadores, el ÚLTIMO es el decimal; solo coma en grupos de 3 →
  miles; **solo punto → decimal SIEMPRE** (es lo que la app escribe: tarifas, horas).
### ⚠️ `_parse_date`: una fecha no-ISO desaparecía del P&L
`invoices`/`inventory` usaban `date.fromisoformat`, que solo acepta ISO. Un
`16/08/2026` —el formato de texto libre que hubo hasta v149— se leía `None`, y una fila
sin fecha legible **queda fuera de todo filtro por periodo** (v309): esa factura no
salía en «Este mes» ni en ningún otro, sin decir nada. `admin_digest` ya aceptaba los
dos formatos; ahora los tres comparten el mismo, día primero (AU).
### ⚠️ `_next_id` leía de la caché → podía repetir un ID
`invoices`, `clientes` e `inventory` lo calculaban sobre `_records()`, que está
**cacheado 120 s** (TTL subido en v290). Si la caché no se invalidó, el "siguiente" ID
sale **ya usado** — y aquí *el ID es la identidad*: dos facturas que se pisan, dos
clientes que confunden sus proyectos, dos activos compartiendo la etiqueta QR física.
`toolruns._next_id` ya leía fresco y lo documentaba; los otros tres no. ⚠️ Cuesta **1
lectura extra por creación**, aceptado: crear es una acción humana y rara, y la
alternativa es corromper la identidad.
### `notify_expiring`: N escrituras seguidas en cada login de admin
Era un `update_cell` por credencial DENTRO del bucle, y esta función corre en **cada
login de administrador** (v187). Con varias credenciales venciendo a la vez eran N
llamadas seguidas justo al entrar, contra el techo DURO de 60/min. Ahora **1
`batch_update`** pase lo que pase (el patrón de v80).
### Los silencios que escondían una escritura fallida
De los **128** `except: pass` del repo, solo **7** se tragaban una escritura; los otros
121 son lectura/display/opcional y el silencio ahí es correcto. Los 7 ahora dejan
rastro (sin cambiar el flujo). El peor con diferencia: **`timeclock.get_sheet`** — si
la migración de cabecera falla, los módulos siguen escribiendo por el índice CANÓNICO
de `HEADERS` y **cada dato cae en la columna de al lado**. Se registra como ERROR. Los
otros: el heartbeat y la liberación de sesión (v75/v289 — el silencio es deliberado,
pero sin rastro una racha de 429 parece "la sesión se cae sola"), y tres best-effort de
Drive donde el usuario creía haber guardado una foto o un PDF que no se subió (ahí
además se avisa en pantalla).
### Lo que sigo SIN tocar, y por qué
`_ws` (×10), `_records` (×12), `is_configured` (×15) e `_invalidate` (×11) **parecen**
duplicados pero cada uno se ata a su hoja, su cabecera y su clave de caché. Unificarlos
es construir un repositorio genérico de hojas sobre 12 módulos que tocan datos de
producción: mucho riesgo de regresión, cero cambio para el usuario. Se quedan.

## Revisión EN EL CLOUD: tres fallos que solo se ven con datos reales (v324)
Primera revisión de la app desplegada, con sesión de administrador real. v322 y v323
salieron intactas —y v322 resultó tener un caso VIVO, no hipotético— pero mirar las
pantallas con datos de verdad destapó tres defectos que ningún test local iba a dar.
### ✅ Lo que se confirmó funcionando
- **v322 con caso real:** `AGR-0001` («North») tiene **2 miembros y los DOS están
  archivados**. La tarjeta muestra ahora `2 elev · 21%` donde antes decía **0 elev · 0%**,
  y el editor de miembros lista `north` y `norte` **marcados** — sin el arreglo no
  habrían salido y guardar los habría desagrupado. El 21% cuadra solo: (8 + 34,6)/2.
- **v323 no movió un solo número:** Resumen $3.145 / $1.435 / $1.710 y la conciliación
  con periodo «Todo» cierra exacta (1.645,20 − 358,80 + 0,40 = 1.286,80), idénticas a
  lo documentado en v313. Gastos: KPI $3.145 = torta (1.645 + 1.000 + 500).
- v309/v312 (los `$` sin LaTeX), v311 (titular con negrita real), v315, v316, v321
  (el aviso de margen 0% incluye los archivados `north`/`norte`), v306 (ID en la lista).
### ⚠️ 1. El proyecto que peor va recibía el mensaje MÁS TRANQUILO
En `prueba 3` (0% de avance, 6 días de retraso) el banner decía *«Vas a 0.0 %/día,
**justo el ritmo que hace falta** (4.3 %/día)»*. Causa:
```python
factor = (ritmo_nec / ritmo_real) if (ritmo_real and ritmo_real > 0.01 and ritmo_nec) else None
```
Con avance 0, `ritmo_real` es 0 → la guarda contra división por cero deja `factor=None`
→ `factor and …` es **falsy** en las dos ramas de aviso → cae en el `else`, que es el
mensaje calmado. Rama nueva explícita para «sin avance», que además es la que más
alarma debe dar.
### ⚠️ 2. …y el proyecto pasado de fecha no mostraba NADA (rama inalcanzable)
La guarda exterior era `if ritmo_real is not None and ritmo_nec is not None:`, pero
`ritmo_nec` vale `None` **exactamente** cuando `dias_rest <= 0` → el `if dias_rest <= 0`
de dentro no podía cumplirse **nunca** y su aviso («la fecha de fin ya pasó») era
**código muerto**. Un proyecto vencido se quedaba sin banner de ritmo, en silencio.
⚠️ Lo cazó el test, no yo: al replicar el orden REAL de los `if` en vez de suponerlo,
un caso salió «sin banner» donde yo esperaba el aviso. **Replicar la estructura exacta
del código en el test es lo que convierte un test en evidencia.** Las 5 ramas se
comprueban ahora alcanzables.
### ⚠️ 3. La conciliación gritaba un descuadre que no existe
Con el periodo por defecto («Este mes») salía **«$1.262,80 sin explicar»**. No es un
descuadre: los dos lados de la cadena se filtran por fechas **distintas** —las horas por
el día trabajado, las nóminas por su `PeriodoHasta` (decisión deliberada de v309: el
costo se devenga en el periodo que cierra)—, así que en una ventana corta la cadena **no
puede cerrar por construcción**. Con «Todo» cierra al céntimo. Ahora la alarma roja solo
sale con periodo completo; con periodo acotado se explica por qué no cuadra.
### Detalle de formato
La fila restada mostraba `− horas cobradas … $-358.80`: el signo iba en la etiqueta **y**
en el importe. El signo se queda en la etiqueta (− / + / =, como cualquier estado de
cuenta) y el importe va en magnitud.
### Pendiente de ejercitarse en vivo
El `batch_update` de `notify_expiring` (v323) **aún no ha corrido**: la credencial que
vence tiene `UltimoAviso = 2026-08-10` y el deduplicado de 25 días lo suprimió
correctamente. Y `_ids_frescos` solo se estrena al crear una factura/cliente/activo.

## «Sin tarifa» eran DOS cosas distintas en el mismo aviso (v325)
Salió de la revisión en el Cloud: el aviso de Horas decía *«Sin tarifa/hora, así que su
costo sale $0: asfgjjd, fijiofgjei (conductor)»* y mandaba a **Usuarios** a arreglarlo.
Para `asfgjjd` era correcto —le faltaba la tarifa, se le puso 40—. Para `fijiofgjei`
**no existe fila que arreglar**: es la cuenta `conductor` que se eliminó en v163 al
quitar ese rol, y sus fichajes históricos quedaron huérfanos. El aviso mandaba a un
callejón sin salida y el pendiente no se podía cerrar nunca.
### `auth.claves_conocidas(grupo=None)` — la señal, en un solo sitio
Devuelve las claves (Usuario **y** Nombre) de quien sigue dado de alta. Sale de
`list_users`, que está cacheado → **0 llamadas nuevas a Sheets**. Se puso en `auth` y no
copiada en cada consumidor: es exactamente el patrón que causó los fallos de v323
(cinco `_num` divergentes), así que aquí se nace con una sola definición.
- ⚠️ **Sin `grupo` mira TODA la hoja**: alguien movido a otro grupo sigue existiendo y
  decir que «ya no está» sería falso.
- ⚠️ **Degrada a “sí existe”** si no se puede leer Login (`conocidas` vacío): un fallo de
  lectura no puede acusar de baja a nadie. Probado.
### Los tres consumidores, coherentes
`timeclock.group_hours` añade **`existe`** por persona; `expenses.labor_breakdown` y
`finance.conciliacion_mo` parten su `sin_tarifa` en **`sin_tarifa`** (accionable) y
**`de_baja`** (informativo). En pantalla: Finanzas·Horas y el detalle de Costos sacan dos
mensajes distintos, y el **indicador «Sin tarifa» del Resumen cuenta SOLO a quien se le
puede poner** —un pendiente que nadie puede cerrar no es un pendiente— mencionando a los
de baja en su detalle.
### Verificado contra la hoja real
`conductor`/`fijiofgjei` → «ya no está»; `admin1`/`asfgjjd`/`campo1` → de alta. Con los
datos del grupo: 1 de baja (`fijiofgjei`) y, en la conciliación, `Bobo` como el único
«falta tarifa» accionable.
### Dato de producción cambiado
`admin1` (nombre `asfgjjd`) pasó a **TarifaHora 40** vía `auth.set_rate`. Efecto: M.O.
cargada a obras del grupo $1.645 → **$1.992**, y el costo de la agrupación *North*
$0 → **$346**.

## Auditoría de DISEÑO y sus arreglos (v326–v329)
Auditoría midiendo el DOM en producción (no capturas): escala tipográfica, paleta,
densidad, áreas de clic, contraste WCAG y motion. Informe:
`https://claude.ai/code/artifact/a07de4cd-4e28-4454-888e-02e5b4062519`.
### Lo que se arregló
| Qué | Antes | Ahora |
|---|---|---|
| Contraste de indicadores en reposo | **2.26:1** | **4.62:1** |
| Ámbar como texto | 3.18:1 | **5.65:1** |
| Texto de diagramas (`fill=`) | 3.43:1 | **5.57:1** |
| Subtítulo de la banda de marca | 3.20:1 | **4.58:1** |
| Valor KPI en ámbar | 2.85:1 | **6.16:1** |
| Ancho útil por pantalla | 980 px | **1066 px** |
| Botones por debajo de 36 px | 9 de 17 | **0** |
| Transiciones propias | **0** | acuse de recibo + hover + atenuado |
### ⚠️ El hallazgo que no buscaba: el 40 % de los botones no recibía el kit
Los selectores del sistema de diseño usaban el combinador HIJO
(`div[data-testid="stButton"] > button`). Cuando un botón lleva `help=`, Streamlit lo
envuelve en `stTooltipHoverTarget`, así que **deja de ser hijo directo**: medido en
producción, **10 de 25 botones visibles** se quedaban sin radio, sin peso, sin hover
—y se habrían quedado sin el acuse de recibo nuevo—, incluido el ← de la barra y todos
los indicadores. Viene de v283 y nadie lo había visto. Descendiente, no hijo.
### ⚠️ Un color de ACENTO no es un color de TEXTO
`_kpi_card(label, valor, color)` teñía con el mismo color el borde y el valor, así que
pasarle `AMBAR` (#e67e22) daba un importe a **2.85:1**. Nueva `theme.texto_seguro()`:
el borde conserva el color vivo (no es texto) y el valor usa su equivalente legible.
Se resuelve en el kit, no en cada llamada — hay ~20 tarjetas y la siguiente que alguien
escriba tiene que salir bien sin acordarse.
### ⚠️ Tres falsos positivos de mi propio medidor (lección de método)
Medir contraste en el navegador tiene tres trampas, y caí en las tres antes de cazarlas:
1. **Degradados**: `background-image` no aparece en `backgroundColor` → hay que evaluar
   contra la PEOR parada del degradado.
2. **Alfa**: un fondo `rgba(28,131,255,.1)` tratado como opaco daba 2.05:1 cuando el
   valor real, compuesto sobre blanco, es **6.68:1**. Las alertas nativas de Streamlit
   pasan todas (4.66–7.55).
3. **Iconos**: los Material Symbols son texto para el DOM pero contenido no textual para
   WCAG (umbral 3:1, no 4.5).
Con las tres corregidas: **9 pantallas medidas, 0 fallos reales**.
### Lo que NO se tocó, a propósito
`stroke=` de los diagramas (líneas técnicas, no texto), fondos de pista, y `AMBAR` como
anillo/gráfico. Y el buscador de la barra superior sigue inerte: es decisión de producto
(conectarlo o quitarlo), no un arreglo de estilo.

## El buscador de la barra superior YA busca (v330-v331)
Era el hallazgo con más coste de credibilidad de la auditoría de diseño: **641 px del
control más prominente de cada pantalla de gestión, inertes** desde v190 — un
`text_input` cuyo valor no se leía en ningún punto del código.
### `home_ui.buscar(q, grupo)` — el motor
Busca en **proyectos** (nombre, ID, cliente, ubicación), **personas** (nombre, login,
email) y **trabajos** del catálogo (nombre, ID, número). Devuelve
`[{tipo, titulo, pie, id, orden}]`.
- **0 lecturas nuevas a Sheets**: las tres fuentes (`P.list_projects`, `auth.list_users`,
  `R.list_trabajos`) ya están cacheadas y se usan en otras pantallas. Con el techo duro
  de 60/min era condición, no preferencia.
- **Ranking**: 0 = ID exacto · 1 = empieza por · 2 = contiene; a igualdad, por tipo.
- `_norm_busq` quita acentos y mayúsculas → «grua» encuentra «grúa».
- **Mínimo 2 letras**: con una sola, todo coincide y no informa.
- ⚠️ Solo el catálogo TRB-#### en trabajos: `trabajos_idx` mete los proyectos como
  entradas sintéticas (v218) y usarlo aquí los DUPLICARÍA con la sección de proyectos.
- Los **archivados** se encuentran (`incluir_archivados=True`) y se marcan como tales:
  buscar algo viejo es justo cuando hace falta un buscador.
### La pantalla y la navegación
`_pantalla_busqueda` se engancha en **una línea al principio de `render_admin_content`**
(no en `app.py`) para que ningún llamador cambie. Con término escrito, los resultados
OCUPAN la pantalla: se ha ido a buscar, no a mirar la sección de debajo. Cada resultado
reusa los deep-links que YA existían — `_admin_open_proj`, `gp_fichasel`, `navegar()` —
en vez de inventar caminos nuevos.
- ⚠️ **Limpiar la caja va por bandera** (`_search_clear`), aplicada en `render_topbar`
  ANTES de instanciar el `text_input`: quien la pide es el clic, que ocurre más abajo en
  el MISMO run, y escribir la clave de un widget ya instanciado revienta (regla v111).
- Al **campo** no se le muestra: su nav es corta y todo lo suyo cuelga de Mis proyectos.
### ⚠️ v331: el indicador de versión mentía
Visto al verificar: la app era **v330** y el topbar decía **v324**. `_version()` llevaba
`@st.cache_data` **sin ttl**, así que se congelaba durante toda la vida del proceso, y
Streamlit Cloud recarga el código en caliente sin reiniciar siempre. Un indicador de
versión que miente es peor que no tenerlo — y este se usa a diario para saber qué hay
desplegado. Sin caché: es leer un fichero local de 5 bytes.
### Verificado en producción
Buscar «norte» → el proyecto archivado PRJ-0003, y al tocarlo abre su detalle con la
caja ya limpia. Buscar «campo1» → la persona, y al tocarla abre **su ficha** en
Planificación · Usuarios. El guardián de v303 (destinos de `navegar()` existentes) pasa.

## Estado de carga + los selectores del kit dejan de suponer la etiqueta (v332)
### ⚠️ El atenuado de v326 NUNCA funcionó (y lo di por bueno)
La regla era `div[data-testid="stMain"]` y **stMain es un `<section>`**, así que no
casaba con nada. Lo afirmé en el informe de diseño sin medirlo. Es el mismo error que
el combinador `>` de v327: **un selector supuesto en vez de medido**.
Al auditar TODOS los selectores del kit contra el DOM real apareció un segundo:
**`stMetricLabel` es un `<label>`**, así que el estilo de las etiquetas de métrica
(mayúsculas, peso 600, color secundario) llevaba muerto **desde v283**.
→ Se quitó el nombre de etiqueta de los **18** selectores del kit: el `data-testid` ya
es único, la etiqueta no aporta nada y es justo lo que se rompe cuando Streamlit cambia
su DOM. Verificado: 0 selectores con etiqueta.
### El estado de carga, por fin visible
Dos señales, que resuelven cosas distintas:
- **Barra superior animada** (3 px, degradado azul COPEX, `cpx-cargando` 1.05 s) →
  «te he oído y estoy trabajando». Aparece en el navegador, sin esperar al servidor.
- **Contenido atenuado a .55** → «lo que ves ya no es lo definitivo».
Medido en producción durante un rerun de 520 ms: barra visible con su animación,
`opacity` del main baja a 0.55, y **en reposo vuelve todo a 1 sin residuo**.
⚠️ No es un esqueleto literal (Streamlit no permite reservar la altura del contenido
que aún no existe); es la señal que resuelve el problema real, que era la pantalla
idéntica y quieta hasta 2,9 s.
### La lección, que ya va tres veces
Un selector CSS que no casa **no da error**: la app se ve "casi bien" y nadie lo nota.
Las tres veces (v326 `>`, v326 `div`/section, v283 `div`/label) se cazaron **midiendo el
DOM en vivo**, nunca leyendo el código. Comprobación barata que conviene repetir al
tocar el kit: para cada `tag[data-testid=X]`, comparar cuántos elementos casan con y sin
la etiqueta.

## Escala tipográfica + el deploy que no llega (v333-v335)
### La escala: de 31 tamaños a 9
Había **31 tamaños de fuente distintos para 102 usos**, 24 fuera de cualquier escala
(11.52, 12.48, 16.32, 17.92, 21.12… los residuos de escribir en `rem`). Eso no es una
escala: nadie la eligió, así que nadie la puede respetar.
Nueve pasos — **11 · 12 · 13 · 14 · 16 · 18 · 21 · 26 · 34** — y todo se ajusta al más
cercano. ⚠️ **Medido ANTES de tocar**: 30 de los 31 valores se mueven ≤1 px y solo
24→26 se mueve 2 px (3 usos). Por eso se pudo hacer de golpe sin romper maquetación.
- **Literales en px, no `var(--…)`**, a propósito: parte de este CSS viaja a
  `email_notify` (los clientes de correo no resuelven variables) y a los SVG que
  `svglib` pasa a PDF. Un token que no resuelve no avisa, deja el texto por defecto.
- **NO se tocan los `font-size="7.5"` de los SVG** (137): son atributos sin unidad con
  la escala del dibujo técnico; meterlos en la de la interfaz rompería las cotas.
- **Guardián** (`verif_v333.py`): falla si aparece un `font-size:` fuera de la escala.
  Cazó 6 en `app.py` que mi migración se había saltado por recorrer solo `core/`.
### ⚠️ EL HALLAZGO OPERATIVO: «desplegado» ≠ «corriendo»
Verificando v333 medí que la app **anunciaba v333 sirviendo el `theme.py` de v332**.
Causa: el fichero `VERSION` vive en disco y se actualiza con el deploy, pero Streamlit
Cloud recarga el script principal **sin re-importar los módulos `core.*`** ya cargados
en `sys.modules`. Hasta que el proceso reinicia, el código nuevo NO corre.
- Esto invalidó una verificación mía: la primera comprobación de maquetación de v333
  corrió contra el CSS de v332, así que **no probaba nada**. Hubo que repetirla.
- **v334 invierte el arreglo de v331**: la versión se lee **AL IMPORTAR** el módulo, no
  fresca en cada run. v331 la hizo fresca para que no se quedara vieja, pero eso la
  volvió más engañosa — anunciaba con confianza una versión cuyo código no se ejecutaba.
  Leída al importar, cambia exactamente cuando cambia el código. **Si la barra dice
  v334, se está ejecutando v334.**
### v335: una etiqueta truncada no informa
Streamlit recorta la etiqueta de `st.metric` con elipsis (`nowrap`+`overflow:hidden`).
En ventana estrecha eso deja «Dispon…». Ahora usa dos líneas: 12 px más de alto es mejor
que media palabra. ⚠️ **Honestidad sobre el hallazgo**: lo medí a 780 px porque
`preview_start` me había reseteado el viewport, no al tamaño de diseño. A 1440 las
columnas son de 202 px y **todas las etiquetas caben en una línea**, así que el arreglo
no cambia nada ahí — solo hace que degrade bien en un portátil o media pantalla.
### Comprobado en producción (1440×900, 7 pantallas)
0 desbordes horizontales · **0 tamaños fuera de la escala** · tarjetas KPI idénticas
entre sí (73 px, `kpiDesigual: 0`) · 0 etiquetas recortadas.

## Movimiento con sentido: la curva se traza, la cifra entra (v336)
Cierra el plan de la auditoría de diseño. Las dos piezas que quedaban, las dos
puramente de percepción.
### La curva S se traza de izquierda a derecha
`stroke-dasharray`/`stroke-dashoffset` animados 0.9 s. Aquí la animación **ES el dato**:
la curva avanza en el tiempo, así que el tiempo se lee como tiempo. La real entra 0.18 s
después de la planificada, que es el orden en que se comparan.
- ⚠️ **`schedule_svg(..., animar=False)` por defecto.** El MISMO SVG va al PDF por
  `svglib` (`report.py`, `user_report.py`), y ahí un `<style>` con `@keyframes` es, en
  el mejor caso, ignorado. Solo los dos call-sites de PANTALLA pasan `animar=True`.
- **Probado que el PDF no cambia**: quitando el `<style>` y las clases, el SVG de
  pantalla es **idéntico carácter a carácter** al del PDF, y `svg2rlg` lo sigue
  convirtiendo (570×412).
### Las cifras entran al recalcularse
Al cambiar un filtro, los números nuevos aparecían en el mismo sitio y con la misma
pinta que los viejos: no había forma de ver QUE habían cambiado. Ahora entran con
`cpx-entra` (220 ms, 3 px). ⚠️ **NO es un contador animado**: `st.markdown` no ejecuta
scripts, así que un count-up necesitaría un iframe por tarjeta y rompería la maquetación.
El gesto de entrada da la misma señal sin tocar el valor.
### ⚠️ Este navegador pide *reduced motion* — y por eso no se ve animar
Verificando en el Cloud, las curvas salían con `animation: none` y ya trazadas. No es un
fallo: `matchMedia('(prefers-reduced-motion: reduce)')` da **true** en el navegador de
automatización, así que la guarda hizo su trabajo. Comprobado por CSSOM que están los
`@keyframes`, la regla base, el retardo de la segunda curva y la anulación; y forzando
la animación a mano, aplica (`cpx-trazar`, 0.9 s). **Si tu Windows tiene activado
"mostrar animaciones" (lo normal), la verás.**

## Estado en la URL: «mira esta pantalla» (v337-v338)
Último punto del informe de diseño. La dirección refleja **sección · sub-pestaña ·
proyecto abierto**, así que se puede copiar y mandar:
`…/?s=proyectos&t=proyectos&p=PRJ-0003` abre ese detalle directamente.
### Cómo
- **`_slug(sub_id)`**: el ID interno lleva emoji porque ES el identificador (v232) y no
  se toca, pero en una URL sería ilegible. El slug se **deriva**, no se guarda: si mañana
  cambia el emoji, el enlace viejo sigue funcionando. Verificado: 0 colisiones dentro de
  una sección y las 18 sub-pestañas hacen ida y vuelta.
- **`_url_a_estado()`** solo en la PRIMERA pasada (`_url_leida`) y solo si no hay ya un
  `_admin_nav_pending`: los deep-links internos son más específicos y ganan. Sin esa
  guarda, cada rerun te devolvería a donde apunta la URL y no podrías moverte.
- **`_estado_a_url()`** solo escribe **si cambia**, para no actualizar la URL en cada
  pasada (y con ello arriesgar un bucle). Probado: estable 2,5 s sin tocar nada.
- **NO toca `activo`**, el deep-link del QR de inventario, que tiene su handler en
  `app.py` y se limpia solo.
### ⚠️ La URL NO es una vía para saltarse el rol
`_url_a_estado` valida la sección contra `_secciones()`, que es **por rol**. Probado:
un campo con `?s=finanzas` NO llega a Finanzas, y el propietario tampoco a Proyectos.
Y aunque llegara, el despachador de contenido también es por rol.
### ⚠️ v338: fallaba en 4 secciones y parecía intermitente
`sub = st.session_state.get(_subkey().get(seccion) or "")` → en una sección **sin**
sub-pestañas (Home, Fichaje, Inventario, Contactos) quedaba `get("")`, que lanza; mi
propio `except` se lo tragaba y la URL no se actualizaba **solo en esas cuatro**.
Finanzas y Proyectos sí funcionaban, que es lo que despistaba: se veía intermitente,
no roto. **Un `except` amplio alrededor de código nuevo esconde justo el fallo que
acabas de introducir** — el mismo patrón que v323 destapó en los silencios de escritura.

## El techo de cuota de Sheets: lector por LOTES (v339)
Lo que limitaba a cuántos clientes se le puede vender la app.
### Lo medido ANTES (instrumentando la capa HTTP de gspread, no suponiendo)
- arranque en frío: **12 llamadas**, 859 ms de media cada una
- recorrido por todas las secciones: **7 más** → 19 por sesión
- **15 de las 19 eran `values/{hoja}`: una por hoja.** La app lee 21 hojas con 30
  lectores cacheados y cada uno pedía la suya por separado.
- techo: **60 lecturas/min por cuenta de servicio** — y hay UNA para todos los grupos,
  así que no crece al añadir clientes, se reparte. Daba **~10 usuarios en paralelo**
  o **5 arranques por minuto** antes del 429.
### La palanca
`spreadsheets.values.batchGet` trae **muchos rangos en UNA petición**, y la cuota cuenta
peticiones. **`core/hojas.py`**: la primera hoja que alguien pida dispara UNA llamada
que se trae todas; el resto salen de ahí. Los 17 lectores cacheados de los 13 módulos
delegan en `hojas.registros(titulo, cabeceras)`.
### Medido DESPUÉS
| | Antes | Ahora |
|---|---|---|
| Arranque en frío | 12 llamadas | **6** |
| Recorrido por todas las secciones | 7 más | **0** |
| Total de una sesión | 19 | **6** |
⚠️ Y el lote es `@st.cache_data`, o sea **compartido por proceso**: mientras esté
caliente, TODOS los usuarios leen de él. La navegación deja de consumir cuota.
### Tres trampas que hubo que resolver
1. **Un rango inexistente tumba el lote ENTERO.** `MovimientosActivo` aún no existe
   (no hay activos) y `values_batch_get` devolvía 400 para toda la petición. Se piden
   solo las hojas que existen, según el índice que `timeclock._libro()` ya cachea
   (coste: 0 llamadas).
2. **⚠️ `_invalidate()` tenía que tirar TAMBIÉN el lote.** Cada módulo limpiaba su
   caché, pero el dato venía del lote compartido → tras guardar algo habría seguido
   saliendo el valor viejo hasta 120 s. «Lo guardé y no sale». Los 12 `_invalidate`
   llaman ahora a `hojas.invalidar()`.
3. **Ciclo de imports**: `hojas` importa `timeclock`, así que los lectores lo importan
   DENTRO de la función, no a nivel de módulo.
### Lo que NO cambia
Las rutas de **ESCRITURA siguen leyendo frescas** (`_find_row`, `_next_id`,
`_ids_frescos`): decidir dónde escribir o qué ID toca con una caché es como se corrompen
los datos (v323). El lote es solo para lectura de display.
### Verificado
`registros()` devuelve **idéntico fila a fila** a `get_all_records(numericise_ignore=
['all'])` en las **19 hojas** (incluidas las de 0 filas y la de 72), y contra una lectura
fresca e independiente con gspread crudo: Alarmas 18, Proyectos 6, Sheet1 30, Login 6,
Gastos 2, Nóminas 5 — todas idénticas. Las 7 pantallas del Cloud renderizan sin errores.

## Subir el techo de cuota: decidido y APLAZADO (16/08/2026)
v339 dio margen de sobra para los clientes actuales, así que **no se hace nada ahora**.
Las opciones, para cuando toque:
| | Qué resuelve | Coste |
|---|---|---|
| **A. Una cuenta de servicio por cliente**, mismo libro | Solo la cuota | **BAJO**: el libro se abre en UN solo sitio (`timeclock._cached_ws`, ~L89-93); sería cachear por grupo |
| **B. Un libro por cliente** (+ su cuenta) | Cuota **y aislamiento** | MEDIO-ALTO. ⚠️ Rompe las vistas del PROPIETARIO, que leen todos los grupos de una vez (`owner_digest`, `list_projects()` sin filtro): pasarían a abrir N libros |
| **C. Salir de Sheets** (Postgres/Supabase) | Todo | ALTO, pero es el final natural si crece |
**Disparadores acordados:** A → cuando entre el segundo cliente de verdad. B o C →
cuando un cliente pregunte por sus datos.
### ⚠️ El argumento no es la cuota, es el AISLAMIENTO
Hoy todos los clientes viven en el **mismo archivo**, separados por una columna `Grupo`.
Un fallo en ese filtro —de los que han salido varios— no muestra un número mal:
**enseña datos de otro cliente**. Es objeción de venta y es riesgo real.
### Palanca gratis sin usar
Subir "Read requests per minute per user" de 60 → 300 en Cloud Console → Sheets API →
Cuotas. No reduce consumo, da colchón. Se decidió no depender de ella porque Google
empezará a **facturar el exceso** más adelante en 2026.

## ⚠️ REGLA: si algo se puede archivar, tiene que poder VOLVER (v340)
Encontrado por el usuario al primer intento: **archivó un cliente y desapareció**.
`set_activo(cid, False)` marca `Activo=NO` y las 5 llamadas a `list_clientes` usaban el
default que los oculta — **sin casilla para verlos y sin botón para restaurar**. El dato
seguía en la hoja; la app no tenía forma de enseñarlo.
Es **exactamente** el fallo que v149 resolvió para los proyectos, aplicado a una entidad
que nació después y a la que nadie se lo aplicó. Al buscarlo apareció **el mismo en los
activos dados de baja** (`dar_de_baja` → `Activo=NO`).
### Las tres piezas, siempre juntas
1. La bandera existe en el modelo (`incluir_inactivos` / `incluir_baja` /
   `incluir_archivados`) — esta parte **ya estaba** en los tres casos.
2. La **interfaz ofrece verlos** (casilla) + dice **cuántos hay ocultos**.
3. Hay **botón de volver** (Restaurar / Reactivar) en la ficha.
Tener solo la (1) es peor que no tener nada: el dato existe pero es inalcanzable.
### Guardián
En `verif_v340.py`: por cada entidad con bandera de ocultar, su `_ui` tiene que
mencionar la bandera **y** una vuelta. Hoy pasan clientes, inventario y proyectos.
### ⚠️ Lo que esto dice del estado real
La app tiene **70 funciones públicas que escriben**; a fecha de v340 se ha ejercitado
**una** (`set_rate`). El usuario probó **una** escritura (crear+archivar un cliente) y
salió un fallo. No es mala suerte: es que la superficie de escritura está sin recorrer.
**Antes de decir que un rol "está listo", ejercitar sus escrituras, no solo sus
pantallas.**

## Los tres huecos del administrador, cerrados (v341-v343)
Salió de la pregunta del usuario: *«¿estamos ofreciendo las herramientas necesarias
para un administrador o falta algo?»*. La auditoría dio tres huecos reales — no
pantallas que faltaran, sino **preguntas que la app no podía responder**.

### v341 · «¿vamos mejor o peor que el mes pasado?»
El P&L daba una foto del periodo elegido y **nada con qué compararla**: $1.710 de
ganancia no dice si es bueno hasta saber qué dio el mes anterior. `finance` gana
`periodo_anterior(desde, hasta)` (ventana del MISMO número de días, pegada justo
antes), `variacion(actual, previo)` → `{dif, pct, mejor}` y `pnl_comparado`, y
`_kpi_card` acepta `var=` → ▲/▼ con el % bajo la cifra.
- **0 llamadas nuevas**: el periodo anterior sale de las mismas filas ya cacheadas.
- ⚠️ **En un COSTO, subir es PEOR**: `render_pnl` invierte `mejor` para la tarjeta de
  costos. Sin eso, gastar más saldría en verde.
- ⚠️ `pct=None` cuando el periodo anterior es ~0: un porcentaje contra cero no
  significa nada, así que se muestra la diferencia y no un «+∞%». Con «Todo» no hay
  periodo anterior y no se compara nada.
- Verificado con datos reales: agosto $1.710,42 contra julio −$1.500 → **+214%**, y la
  aritmética de ventana cuadra en rangos de 16 días, 31 días y un trimestre.

### v342 · «¿quién puso este margen al 0%?»
`CreadoPor` decía quién CREÓ una fila; **nada decía quién la cambió**. En una app donde
el margen, la tarifa, el presupuesto y las fechas deciden lo que se cobra y lo que se
paga, esa pregunta se hace tarde o temprano y no tenía respuesta.
`core/auditoria.py` (hoja `Auditoria`): `diff` · `registrar` · `historial`.
- **Acotado a lo que mueve dinero** (`CAMPOS_CLAVE`). Registrar los 70 puntos de
  escritura daría una fila por clic y una hoja ilegible; un cambio de nota no entra.
- **1 escritura por edición y solo si algo cambió de verdad**: toda la edición va en
  UNA fila (los campos en un JSON) y `diff` compara como texto, así que `40` y `40.0`
  no generan histórico. Guardar un formulario sin tocar nada no gasta cuota.
- ⚠️ **La anotación va FUERA del try del guardado y DESPUÉS de invalidar**: el cambio
  del usuario ya se hizo y no se puede deshacer porque falle el apunte. Verificado por
  AST en los dos enganches (`projects.update_project`, `auth.set_rate`).
- ⚠️ **El «antes» se captura ANTES de escribir**, de la caché (0 llamadas).
- ⚠️ `_records` llama a `hojas.registros(SHEET)` **sin cabeceras**: con ellas cae a
  `get_sheet`, que **CREA la hoja** — un lector que escribe (regla v145). La hoja la
  crea la primera anotación.
- ⚠️ **Fallo que cazó el chequeo de nombres libres**: `projects_ui` importa `theme`
  **dentro de cada función**, no a nivel de módulo, así que mi bloque nuevo lo usaba
  sin importarlo → NameError al abrir el desplegable. Mi primera comprobación dijo
  «importa theme: True» porque recorría el árbol entero con `ast.walk` y encontraba el
  import LOCAL de otra función. **Comprobar el ámbito, no la presencia.**

### v343 · «¿cuánto llevo comprometido?» — órdenes de compra
`expenses` responde «cuánto llevas GASTADO»: una compra existe cuando hay recibo. Pero
el material se encarga semanas antes de la factura, así que entre el pedido y el recibo
**el proyecto aparece dentro de presupuesto con el dinero ya comprometido**, y el
sobrecosto se descubre cuando ya no se puede hacer nada — el mismo problema que v144
resolvió para la mano de obra.
`core/orders.py` (hoja `Ordenes`, estados pendiente/recibida/cancelada).
- ⚠️ **UNA sola definición de gasto** (regla v310): una orden **no es** un gasto. Al
  recibirla se crea su fila en `Gastos`, así que el costo real sigue teniendo una sola
  fuente y aquí solo vive lo pendiente.
- ⚠️ **El orden de las dos escrituras importa.** Recibir = marcar + crear el gasto. Si
  se creara el gasto primero y fallara el marcado, al reintentar habría **dos gastos por
  la misma compra** y el costo saldría inflado sin que nadie lo vea. Se marca PRIMERO;
  si falla lo segundo, la orden queda `recibida` **sin GastoID**, `sin_gasto()` lo
  detecta y la UI ofrece completarlo. **Un hueco visible es mejor que un doble cargo
  invisible.** Probado simulando la caída de `expenses.add`.
- ⚠️ **`project_cost.total` NO cambia**: sigue siendo lo gastado, que es lo que leen la
  conciliación, el P&L, la rentabilidad y las alertas. Lo comprometido va en campos
  APARTE (`comprometido`, `total_comp`, `over_comp`). Probado contra la fórmula anterior
  en 6 casos: ni un número existente se mueve.
- **`over_comp`** es el caso que nadie veía: dentro de presupuesto hoy, pero con lo ya
  pedido se pasa seguro. No dispara si ya se pasó (manda `over`, sin duplicar el aviso)
  ni sin presupuesto (no se inventa un porcentaje).
- `atrasadas(grupo)` = pendientes cuya fecha esperada ya pasó → obra parada esperando
  material. ⚠️ Una orden **sin** fecha esperada nunca sale atrasada: no se puede afirmar
  que llega tarde si nadie dijo cuándo llegaba.
- Las vistas de grupo usan `comprometido_por_proyecto` (UNA pasada) en vez de consultar
  por proyecto dentro del bucle (patrón `project_hours_bulk`).
- ⚠️ Las dos hojas nuevas entran en `hojas.HOJAS_LECTURA`: fuera del lote, cada una
  costaría una llamada suelta por sesión (v339).

## ⚠️ EJERCITAR LAS ESCRITURAS: 4 fallos que ningún test vio (v344)
El usuario pidió «el ejercicio completo». Se ejercitaron las escrituras **contra la
hoja real** (código local de v343, datos de producción, con foto del antes y limpieza
después). Salieron cuatro fallos, y **ninguno lo habría encontrado un test**: los tests
usaban diccionarios inventados por mí, con MIS nombres de columna y sin caché real.

### ⚠️ 1. La caché de proyectos NO se limpiaba desde v339 — regresión mía, viva 4 versiones
```python
def _invalidate():
    hojas.invalidar()
    try:
        fn.clear()        # ⚠️ `fn` NO EXISTE → NameError
    except Exception:
        pass              # ⚠️ …y aquí se lo traga
```
El original era `for fn in (_records, _fichaje_records): fn.clear()`. Al reescribirlo en
v339 quité el bucle y dejé `fn.clear()` colgando. Confirmado con `git log -S` (commit
`70309d5`). **Efecto en producción: tras guardar un proyecto, una actividad o una
agrupación, la pantalla podía enseñar el valor viejo hasta 120 s** — el «lo guardé y no
sale» que v339 decía haber evitado. Lo mismo en `roster` (`f.clear()`), o sea el tablero
de planificación. Barrido por AST de las 17 funciones de invalidación: solo esas dos.
**Un `except Exception: pass` alrededor de código nuevo esconde justo el fallo que
acabas de introducir** (misma lección de v323 y v338 — van tres).

### ⚠️ 2. Y las cachés DERIVADAS tampoco
`group_expenses`, `over_budget`, `gaps_by_group` y `projections_by_group` cachean el
agregado: limpiar solo `_records` dejaba el total del grupo, la alerta de sobre
presupuesto y el retraso con el valor viejo hasta 120 s. Probado en vivo: añadir un
recibo de $77,77 y leer el agregado **inmediatamente** → $1.500 → $1.577,77.

### ⚠️ 3. El margen era el ÚNICO campo que la auditoría NO vigilaba
`CAMPOS_CLAVE` tenía `MargenPct`; la columna real es **`MargenMO`**. O sea que la
pregunta para la que se construyó la hoja —«¿quién puso este margen a 0?»— era
justamente la que no tenía respuesta. (`Pagada` era otro nombre fantasma; `Rol` sí
existe: mi primer chequeo lo marcó mal porque cogió `GROUPS_HEADERS` en vez de
`LOGIN_HEADERS` — **validar contra la constante EXACTA, no contra la que encuentre un
atajo**, regla v135.)

### ⚠️ 4. `update_project` anotaba cambios que nunca escribió
Una clave que no está en `_PCOL` se descarta **en silencio** y la función devolvía
igualmente «Proyecto actualizado.». Con la auditoría enganchada, eso además **anotaba un
cambio que la hoja nunca recibió**, y lo repetía en cada guardado (el «antes» no cambiaba
nunca porque no se escribía nada). Ahora: se audita `_escritos` (lo filtrado por `_PCOL`),
las columnas ignoradas se registran en el log, y si NINGUNA es válida se devuelve error
en vez de un éxito falso.

### Lo que SÍ funcionó a la primera, contra datos reales
- **Órdenes de compra (v343) enteras**: crear → comprometido $7.500 → el aviso
  «vas dentro pero con lo pedido te pasas» ($10.500 de $10.000, sin haber gastado un
  peso) → recibir por un importe distinto ($480 en vez de $500) → gasto creado y
  enlazado → comprometido baja solo → atrasadas detecta la de 4 días.
- **`set_grouping_members`** (el arreglo de v322, nunca clicado): los 2 miembros
  **archivados** sobreviven a un guardado, quitar y volver a poner funciona, y el
  avance consolidado (21,3%) no se mueve.
- **`create_project` + `delete_project`**: 11 actividades, fila alineada columna por
  columna, `datos_asociados` correcto y borrado limpio.
- La **auditoría** registra también los cambios de agrupación (`AgrupacionID` +
  `PesoEnAgrupacion`) sin haberlo programado aparte: van por `update_project`.

### Método (repetir tal cual la próxima vez)
1. Foto del estado **en solo lectura con gspread crudo** (los helpers migran cabeceras
   = escriben, regla v145). 2. Ejercitar sobre un proyecto de prueba. 3. Verificar
   leyendo. 4. **Devolver todo a su sitio** y comprobarlo. ⚠️ Mi propia foto del «antes»
   imprimía el margen por `MargenPct`, así que no probaba nada: lo que permitió afirmar
   que no toqué PRJ-0006 fue **el propio historial de auditoría**, que lista cada cambio.

## Fichaje y facturas ejercitados: un abono de $1 escondía una deuda vencida (v345)
Segunda tanda del ejercicio de v344, esta vez sobre las dos rutas que en v344 se
dejaron a propósito («no fabrico registros financieros por mi cuenta»), con el usuario
autorizándolo. Método idéntico: foto en solo lectura → ejercitar → verificar leyendo →
devolver todo a su sitio → segunda foto. **Rastro final: ninguno.**

### ⚠️ EL HALLAZGO: `estado_cobro` comprobaba `parcial` ANTES que `vencida`
```python
if cob > 0:            return "parcial"     # ← se comía el caso
venc = _parse_date(...)
if venc < hoy:         return "vencida"
```
O sea que **un abono de $1 sacaba a la factura de «vencida» para siempre**. Y los tres
sitios que miden la deuda vencida (`finance.pnl`, `invoices.resumen_cliente`, el
resumen de Facturas) filtran por `estado_cobro(f) == "vencida"`, así que ese saldo
**no lo veía nadie**: ni el indicador rojo del resumen financiero, ni el P&L.
Es el caso más común del mundo real: el cliente paga un anticipo y desaparece.
**Arreglo:** vencida gana a parcial — estar vencida es el hecho accionable, y los tres
consumidores ya suman `Total − Cobrado`, o sea el saldo, no el total. Probada la matriz
de 7 casos; los datos reales no cambian de estado (hoy no hay ninguna parcial vencida).

### Lo que aguantó, contra datos reales
- **Fichaje**: fichar a un proyecto **abre la jornada solo** (v150) · `switch_project`
  cierra el segmento y abre otro sin tocar la jornada · `cerrar_jornada` cierra los dos ·
  el `ProyectoID` se guarda (v145) · **cerrar con hora explícita** (el olvido de v164)
  da 3,0 h exactas · y el caso «3 h en obra con 0 de jornada» se marca
  `sin_asignar_indet=True` (v320) en vez de un 0 que parece bueno.
- **v325 en vivo**: la identidad de prueba no está en Login → sale como **«de baja»**
  (informativo) y no como «sin tarifa» (accionable). La distinción funciona.
- **Facturas**: subtotal 1.500 + GST 150 = 1.650 · cobro parcial → `parcial` · **intentar
  cobrar de más se topa al total** → `cobrada` · `CobrosJSON` acumula el historial · PDF
  de 1 página con cliente, número e importes · anular la saca de
  `facturado_por_proyecto` · y `pendiente_de_facturar` baja a 0 (no se cobra dos veces).

### ⚠️ Lo que NO era un hueco (comprobado antes de «arreglarlo»)
Una factura sin fecha de vencimiento nunca puede estar vencida — pero el formulario
usa `date_input(value=clock.today())`, así que **desde la app siempre lleva fecha**. El
hueco solo existía en mi script, que se saltaba la UI. Comprobarlo antes de tocar evitó
un cambio inútil.

### Método, otra vez: seguí suponiendo formas de retorno
`mis_fichajes` devuelve `{tipo, proyecto, entrada, salida, horas, abierto}`, no las
columnas crudas de la hoja; e `invoices._ws()` devuelve **`(worksheet, error)`**, no el
worksheet suelto (distinto de `orders`/`expenses`). Dos errores míos en una tanda, los
dos por no mirar. **Regla v135, van cinco veces.**

## Nóminas ejercitadas + la decisión de la tarifa 0 (v346)
Última ruta de escritura sin recorrer. Método de v344/v345 (foto → ejercitar → verificar
leyendo → devolver todo → segunda foto). **Rastro final: ninguno**; el P&L vuelve a
$1.434,78 / $210,42.

### La decisión que llevaba versiones pendiente
`generar` **detectaba** la falta de tarifa y creaba la nómina **igual, con base $0**. No
era hipotético: en la hoja real está **`NOM-0002`, 8,69 h de trabajo con colilla de $0**,
emitida antes de que esa persona tuviera tarifa. Una colilla de $0 por trabajo hecho es
un documento equivocado y se queda ahí. **Decisión del usuario: saltarlo y avisar.**
- No se crea la fila; se devuelve el **nombre** (`sin_tarifa` pasa de contador a lista) y
  la UI dice a quién y dónde arreglarlo.
- ⚠️ **Es reversible por construcción**: como no dejó fila, el salto de duplicados no la
  bloquea → al poner la tarifa y regenerar **el mismo periodo**, entra. Probado:
  `{creadas:0, sin_tarifa:['ZZZ PRUEBA']}` → tarifa 50 → `{creadas:1}`, base 2 h×50=100,
  retención 15 → neto 85, super 11,5 aparte.
- Al resto del equipo no le afecta: su nómina se genera igual.
- El aviso de la LISTA se queda (no se borra al cambiar el comportamiento): las colillas
  de $0 anteriores siguen en la hoja y hay que poder verlas para anularlas y regenerarlas.

### Lo que aguantó
Salto de duplicados (`creadas 1` → `omitidas 1`) · **neto = base + devengos − deducciones
con los APORTES sin descontar** (0+1000+200−180 = 1020, el super de 138 no resta) ·
marcar pagada con fecha · colilla PDF de 1 página con todos los conceptos · anular la
saca del resumen y del P&L.

### Dos confirmaciones que salieron de regalo
- **El reparto por medianoche de v164, en vivo**: mi turno de prueba cruzó las 00:00 y la
  nómina lo repartió solo — 6,37 h el 17 + 1,63 h el 18 = 8,0 h exactas. Ese arreglo
  nunca se había visto correr con datos reales.
- **La retención de impuesto se calculó por primera vez** en esa hoja: las 5 nóminas
  existentes solo llevaban el concepto de Superannuation.

## ⚠️ Una nómina anulada bloqueaba REEMITIR el periodo (v347) + corrección de NOM-0002
El usuario pidió arreglar `NOM-0002` (8,69 h de trabajo real emitidas en **$0**, porque
se generó antes de que esa persona tuviera tarifa). El camino obvio —anular y
regenerar— **no funcionaba**: `generar` construía el conjunto de duplicados con
`list_nominas(grupo, incluir_anuladas=True)`, así que **la fila anulada seguía
bloqueando**. O sea que la app no tenía NINGUNA forma de reemitir el periodo de nadie.
Es el principio de v340 otra vez: **si se puede deshacer, tiene que poder rehacerse**.
- Arreglo: el filtro pasa a `list_nominas(grupo)` (que ya excluye anuladas por defecto).
  La fila anulada se queda como **rastro de la corrección**; ni `resumen` ni el
  `costo_nomina` del P&L la cuentan, así que no se duplica nada. Probado en vivo:
  emitir → anular → reemitir el MISMO periodo = `{creadas: 1}`, dos filas (una anulada,
  una viva), `resumen.n` sin doble conteo.

### ⚠️ La conciliación ya lo estaba señalando y nadie la leyó
Antes de tocar nada, `conciliacion_mo` decía **«sin explicar $347,60»** — exactamente
8,69 h × $40, la colilla que faltaba. El puente que se construyó en v313 llevaba desde
entonces apuntando al fallo. **Cuando un número no cuadra, la app ya lo sabe: hay que
mirarlo antes de buscar a ciegas.**

### La corrección (datos de producción, autorizada por el usuario)
`NOM-0002` anulada + `NOM-0006` emitida: 8,69 h × $40 = **$347,60**, super 11,5%
(= $39,97). El 11,5% no se eligió a ojo: es **el mismo que se aplicó a `NOM-0003` en ese
mismo lote** (147,98 / 1.286,80). Los otros 4 del periodo se omitieron solos porque su
nómina sigue viva. Efecto en las cifras del grupo:
| | antes | después |
|---|---|---|
| costo_nomina | $1.434,78 | **$1.822,35** |
| costo_total | $2.934,78 | **$3.322,35** |
| ganancia | $210,42 | **−$177,15** |
| sin explicar (conciliación) | $347,60 | **$0,00** |
⚠️ **La ganancia pasa a NEGATIVA, y esa es la cifra correcta**: el costo estaba
subestimado justo en el trabajo que no se pagaba. La obra `prueba1` se facturó al costo
(margen 0%), así que al contabilizar la mano de obra que faltaba, el resultado es
pérdida. No es un fallo nuevo: es el fallo viejo dejando de esconderse.

## Limpieza de las colillas de $0 + homónimos en el aviso (v348)
Anuladas `NOM-0001` (Bobo, 0,01 h), `NOM-0004` y `NOM-0005` (`fijiofgjei`, la cuenta
eliminada en v163): colillas de $0 de gente a la que no se paga por hora.
⚠️ **Ninguna cifra se movió** (costo_nomina, ganancia y la conciliación idénticas), y esa
es justamente la comprobación de que se anuló lo correcto: si mover algo de $0 cambiara
un total, algo estaría mal. La lista de nóminas pasa de 5 filas a **2 con dinero de
verdad** (`NOM-0003` pagada $1.286,80 · `NOM-0006` emitida $347,60).
Y con v346+v347 juntos el ciclo cierra: regenerar ese periodo ahora da `creadas: 0` y
**nombra** a los tres, en vez de recrear las colillas de $0.

### ⚠️ El aviso no distinguía a dos personas distintas
Esa misma prueba sacó `sin_tarifa: ['Bobo', 'fijiofgjei', 'fijiofgjei']`: dos cuentas
distintas con el mismo Nombre, **en el mensaje que justamente te dice a quién ponerle la
tarifa**. Es la cuarta aparición del patrón (v151 horas, v306 proyectos, v319 nóminas).
Ahora el login se añade **solo cuando el nombre se repite** → `fijiofgjei (conductor)` y
`fijiofgjei (fijiofgjei)`, dejando limpio el caso normal.

## ⚠️ El LaTeX volvió: el guardián de v309 no miraba las VARIABLES (v349)
Verificando en el navegador que v348 corría, la pantalla de **Costos** mostraba
literalmente `Llevas **0** de 10,000`: los `$` desaparecidos y los `**` en crudo. Es
exactamente el fallo de v309 —dos `$` en la misma cadena y Streamlit la renderiza como
LaTeX— **en un sitio que el guardián de entonces no podía ver**.
- **La ceguera:** `verif_v309.py` inspecciona los argumentos LITERALES de
  `st.markdown/metric/caption/…`. Aquí la cadena se arma antes en una variable
  (`_l = f"Llevas **${...}** de ${...}"`) y solo después se pasa a `st.caption(_l + …)`.
- **Chequeo nuevo, más simple y más amplio:** por AST, **cualquier f-string del repo**
  con 2+ `$` sin escapar, se use donde se use. Barrido: **4 coincidencias**.
  - `auth.py:47` → el formato del hash PBKDF2 (`pbkdf2$sha256$…`). **Falso positivo**,
    no se muestra nunca; queda exento por (fichero, línea). Mirarlo antes de "arreglarlo"
    evitó romper el login.
  - Las **otras 3 están todas en la pantalla de Costos**: el titular «costará $X, $Y por
    encima» (2 ramas) y **el aviso de material comprometido que yo mismo escribí en
    v343**. Las tres a `theme.dinero` (formatea Y escapa).
- ⚠️ Las del titular estaban **latentes**: solo salen con un proyecto que tenga costos y
  presupuesto, y el que abrí no tenía ninguno. Sin el barrido por AST no aparecen.

**La lección de método:** un guardián acota el fallo a la forma en que lo viste. Este se
escribió mirando llamadas directas, así que la misma cadena movida a una variable pasa
por delante sin que salte nada. Cuando el mismo fallo reaparece, la pregunta no es solo
«¿lo arreglo?» sino **«¿por qué mi chequeo no lo vio?»**.

### De paso, verificado en el navegador con v348 ya corriendo
Las dos versiones coinciden (barra lateral **v348** = `app.py` fresco · topbar **v348** =
`home_ui._VERSION` congelado al importar) → el proceso reinició de verdad. Nóminas:
**POR PAGAR $348 · PAGADO $1.287 · 2 colillas**, sin el aviso de $0. El bloque
**«Órdenes de compra (0 pendientes)»** renderiza en Costos sin romper (primera vez que
ese código de v343 se dibuja). Y el aviso de v324 para 0% de avance sale correcto:
*«Sin avance todavía: necesitas 7.1 %/día en los 14 días que quedan»*.

## Inventario, credenciales y pre-start ejercitados (v350)
Cierre del recorrido de escrituras. Mismo método (foto en solo lectura → ejercitar →
verificar leyendo → devolver todo → segunda foto). **Rastro final: ninguno.**
El inventario estaba **completamente virgen**: 0 activos, 0 movimientos, y la hoja
`MovimientosActivo` ni siquiera existía.

### ⚠️ El traslado guardaba el ID crudo en el historial
`salida` resuelve el nombre (`ubic_ref_label`) y **`traslado` se quedó con el ID**, así
que el mismo sitio salía escrito de dos formas en el mismo historial:
```
MOV-0002 traslado  → proyecto: PRJ-0005     ← el ID
MOV-0003 mant.     ← proyecto: prueba2      ← el nombre, del MISMO sitio
```
Es media aplicación de la regla de v306: el ACTIVO guarda el ID (relación viva, sobrevive
a un renombrado) y el **historial guarda el nombre ya resuelto** (cuenta lo que pasó, no
lo que hay ahora). v306 lo arregló en `salida` y no en `traslado`. Guardián nuevo: en las
funciones de movimiento, todo f-string que use `hacia_ref` debe pasar por `ubic_ref_label`.

### Lo que aguantó
- **Inventario**: categoría · alta de activo · **depreciación** ($1.000 comprado hace 2
  años, vida 5 → $600,27 ✓) · QR PNG · los 4 movimientos (salida → traslado → manten. →
  entrada), que crearon la hoja `MovimientosActivo` · resumen y reporte de valor por
  categoría y ubicación · **dar de baja y reactivar** (v340: desaparece de la lista, se ve
  con la casilla, y el botón lo devuelve).
- **Credenciales**: alta · los 4 estados del semáforo (⚠️ «vence hoy» cuenta como *por
  vencer*, no vencida) · renovar la fecha · `expiring` casa con la credencial real
  (campo1, Driver License, 14 días) · matriz de cumplimiento 4 personas × 2 tipos ·
  `compliance` marca **falta** el certificado que el proyecto exige y no tiene · borrado.
- **Pre-start**: `filename_for` (`17082026 XY.pdf`) · PDF de 1 página con proyecto,
  ubicación y asistentes · fila registrada · `leer()` descompone bien (near miss, **2
  checks en NO**, asistentes).

### Tres falsas alarmas mías, comprobadas antes de "arreglar"
1. **La depreciación**: esperaba $800 y salió $600,27 — el activo era de hace **2** años,
   no 1. El cálculo estaba bien; mi comentario no.
2. **El QR**: `qr_data` devolvía solo el ID, no una URL... porque falta el secret
   `APP_URL` en local. **La UI ya avisa** («Configura el secret APP_URL para que el QR
   abra la app»). ⚠️ Conviene comprobar que ese secret esté puesto en el Cloud, o las
   etiquetas impresas no abren nada al escanearlas.
3. **`InvCategorias` con 0 filas** tras la prueba: las 6 categorías salen de `CAT_DEFAULT`
   (código), la hoja solo guarda las añadidas a mano. Estaba vacía antes y volvió a
   estarlo — mi «esperado 6» era una suposición.

### Lo que NO se ejercitó, a propósito
`credentials.notify_expiring` y un pre-start con `near_miss=YES`: los dos **mandan correo
y Telegram a personas reales**. Y la subida a Drive del PDF del pre-start no corre desde
local (no hay credenciales `[gdrive]`); en el código es best-effort.

### Standing item que sigue abierto (de v158)
**Un check en NO no abre alarma**, solo el near-miss. En la prueba salieron 2 checks en NO
y `alarma: False`. Está documentado como decisión deliberada, no como fallo.

## ⚠️ AISLAMIENTO ENTRE EMPRESAS: el cerrojo que faltaba (v351)
Petición del usuario: «separar todos los registros por empresa cliente». Al medir la
arquitectura antes de proponer nada salió algo más urgente que la separación física.

### El hallazgo: el aislamiento NO lo garantizaba el código
Lo garantizaba que la interfaz **nunca te ofreciera el ID de otra empresa**. Ninguna de
las vistas de detalle comprobaba el grupo del objeto, y `_detalle_proyecto` incluso lo
**adoptaba**:
```python
prj = P.get_project(pid)                       # busca en TODA la hoja
grupo = str(prj.get("Grupo", "")) or grupo     # ← adopta el del proyecto
```
Con los deep-links de v337 (`?p=PRJ-####`) bastaba **editar la URL** para abrir el
detalle completo de otro cliente: costos, horas, personal y archivos. El QR del
inventario (`?activo=ACT-####`) es la misma puerta.
Cuatro vistas afectadas: **proyecto, factura, nómina y activo** — las que traen el
objeto por ID GLOBAL. (`_detalle_cliente` y `_dashboard_agrupacion` ya estaban acotadas:
buscan dentro de una lista ya filtrada por grupo.)
**Hoy era latente: solo existe un grupo real (`cliente1`, con los 6 proyectos).** Deja
de serlo con el segundo cliente — que es justo lo que el usuario está preparando.

### `core/tenant.py` — la regla, en un solo sitio
Módulo HOJA (solo importa streamlit) → sin ciclos. Una sola definición a propósito:
cinco copias divergentes de un helper es lo que causó los fallos de v323.
- **propietario**: ve todos los grupos (es su función, no se le bloquea).
- **administrador / campo**: solo el suyo, comparando sin distinguir mayúsculas.
- **objeto sin grupo** (histórico): se deja pasar y se registra — bloquear por un campo
  vacío rompería registros legítimos anteriores a la columna.
- **sin sesión**: bloqueado.
- ⚠️ El mensaje **no dice de qué empresa es**: confirmar que un ID existe en otro grupo
  ya es filtrar información. Responde igual que si no existiera.
- ⚠️ La comprobación va en la **frontera de render**, NO en la capa de datos:
  `get_project` y compañía los llaman por dentro flujos que cruzan grupos a propósito
  (vistas del propietario, `project_hours_bulk`, el digest multi-grupo). Filtrar ahí
  rompería esos caminos y daría una falsa sensación de blindaje.

Probado con datos reales sobre `PRJ-0005` (grupo `cliente1`): admin de cliente1 **abre**,
admin de otra empresa **bloqueado**, campo de otra empresa **bloqueado**, propietario
**abre**. Guardián permanente (`verif_v351.py`): la regla existe en un solo fichero, las
4 vistas llaman a `tenant.exigir` DESPUÉS de traer el objeto y ANTES de pintarlo, y el
propietario nunca queda bloqueado.

### La decisión de arquitectura (tomada por el usuario)
Se le presentaron 4 caminos con su coste real. Eligió **el cerrojo ahora, un libro de
Google por cliente después, cuando entre el primer cliente real** — migrar un solo
cliente es media hora; con cinco, no.
- Coste de infraestructura: opciones sobre Sheets **$0**; salir a Postgres/Supabase
  **~25 USD/mes** en plan de producción (la capa gratis **pausa** los proyectos
  inactivos, inservible para una app que se vende). El coste real de esa opción no es el
  dinero: es reescribir la capa de datos y migrar 23 hojas.
- A favor de un libro por cliente cuando toque: **el libro se abre en UN solo sitio**
  (`timeclock.py:90-93`), y una cuenta de servicio por cliente **multiplica** el techo de
  60 lecturas/min en vez de repartirlo.
- ⚠️ Lo que romperá ese cambio, ya identificado: las vistas del PROPIETARIO, que hoy leen
  todos los grupos de una vez (`owner_digest`, `list_projects()` sin filtro) y pasarían a
  abrir N libros.

## COTIZACIONES — fase 1: el catálogo (v352)
Funcionalidad nueva pedida por el usuario. La app cubría **obra → costo → factura**; el
dinero empieza antes, en la cotización. Diseño acordado con él antes de escribir nada.

### Decisiones del usuario (firmes)
1. **Aceptar una cotización CREA el proyecto** con presupuesto, cliente y margen puestos.
2. **La mano de obra se cotiza en HORAS estimadas × tarifa**, no a precio cerrado — así
   se puede contrastar lo cotizado con lo fichado («cotizamos 120 h, llevamos 160»).
3. **El margen de la cotización manda** y rellena el `MargenMO` del proyecto al ganarla:
   una sola fuente de verdad, en vez de dos números que digan cosas distintas.

### `core/catalogo.py` + `core/catalogo_ui.py` (hoja `Catalogo`)
`ID(CAT-#####) · Tipo(producto|servicio) · Nombre · Unidad · Categoria · CostoUnit ·
HorasEst · TarifaHora · Activo`. El catálogo guarda el **COSTO**; el margen no vive aquí
—se pone línea a línea al cotizar, porque a un cliente le cobras 20% y a otro 35%.
- **`costo_de()` es LA fórmula única** (producto = `CostoUnit × cant`; servicio =
  `HorasEst × TarifaHora × cant`). La cotización, el PDF y la comparación contra lo real
  la llamarán a ella: cinco copias divergentes es lo que causó los fallos de v323.
- `horas_de()` → las horas que aporta cada línea, base del «cotizado vs real».
- **No se puede crear un artículo sin costo**: saldría en $0 y nadie lo notaría hasta ver
  el total (el fallo de las colillas de $0 de v346). Un servicio exige horas Y tarifa.
- Desactivar **con vuelta** (v340) y homónimos desempatados por ID (v306/v319/v348).
- Sub-pestaña **Finanzas · 📚 Catálogo**; hoja añadida al lote (v339) y cerrojo de
  aislamiento (v351) en la ficha.

### ⚠️ El fallo que cazó la prueba: el precio no se auditaba
Se cambió un costo de 185,50 a 199,90 y **el histórico quedó vacío**: el enganche a
`auditoria` estaba, pero `CostoUnit`/`HorasEst`/`TarifaHora` no estaban en
`CAMPOS_CLAVE`. **Es exactamente el fallo de `MargenPct` en v344** — el nombre del campo,
otra vez. Y el guardián de v344 no lo vio porque **solo miraba una dirección**: que cada
CAMPO_CLAVE existiera como columna real, no que los campos de dinero estuvieran en la
lista. Ahora comprueba las dos. Verificado en vivo: cambiar el precio deja rastro.

**Pendiente:** fase 2 (la cotización: selección, margen por línea, estados, PDF) y fase 3
(aceptar → crea el proyecto, y el bloque «cotizado vs real»).
⚠️ El grupo tiene **margen 0% e impuesto 0%** en `Grupos`: hasta ponerlos, toda
cotización saldrá al costo y sin GST.

## COTIZACIONES — fase 2: armar el precio (v353)
`core/quotes.py` + `core/quotes_ui.py` + `core/quote_pdf.py`, hoja `Cotizaciones`.
Estructuralmente hermana de `invoices` (líneas en JSON, totales con impuesto, PDF); lo
que cambia es que aquí el precio se **construye** (costo del catálogo + margen) en vez de
teclearse. Sub-pestaña **Finanzas · 📄 Cotizaciones**.

### Las tres reglas del documento
1. **La línea congela su precio.** Guarda `costo_unit`, `margen_pct` y `precio_total` del
   momento de cotizar, NO una referencia al catálogo. Probado: se sube el costo del riel
   de 185,50 a 250 y la cotización enviada no se mueve. `recalcular()` reaplica el margen
   sobre el costo **ya congelado**, nunca vuelve al catálogo.
2. **Enviada = documento.** En `borrador` se editan las líneas; a partir de `enviada` no,
   porque el cliente ya la tiene en la mano — se saca una **versión nueva** y la anterior
   se conserva.
3. **`vencida` se DERIVA** de la fecha de validez, no se guarda (igual que
   `invoices.estado_cobro`): un estado calculado no puede quedarse desactualizado.

### ⚠️ El PDF no filtra tus costos
El cliente ve concepto, cantidad y precio. **Nunca** el costo ni el margen. Verificado
extrayendo el texto del PDF: los 5 valores sensibles (costo unitario, los dos márgenes y
los dos costos de línea) no aparecen; el precio con margen sí.

### ⚠️ El fallo que cazó la prueba: la hoja no estaba en el LOTE
`crear` devolvió `COT-0001` y acto seguido `get_cotizacion` devolvía `{}`. Causa: olvidé
`Cotizaciones` en `hojas.HOJAS_LECTURA`. Y como el lector va **sin cabeceras** (para no
crear la hoja al leer, regla v145), `registros()` devuelve `None` → el módulo lee
**vacío para siempre, sin ningún error**. Es peor que la llamada suelta que documentaba
la regla de v339: aquello costaba cuota, esto es un silencio.
→ **Guardián nuevo**: todo módulo con `SHEET = "X"` que lea con `hojas.registros(SHEET)`
sin cabeceras debe tener `X` en `HOJAS_LECTURA`. Hoy pasan los 4 que usan ese patrón
(auditoria, catalogo, orders, quotes).

### Detalles que ya nacen bien
`resumen()` devuelve `conversion=None` —no 0%— cuando aún no hay cotizaciones decididas
(la trampa de v320 con «sin asignar»); el margen por defecto del grupo precarga cada
línea; `_ids_frescos` lee sin caché (v323); el cerrojo de aislamiento (v351) en la ficha;
y los cambios de estado quedan en `auditoria`.

**Pendiente — fase 3:** aceptar → crea el proyecto con presupuesto, cliente y margen; y
el bloque **«cotizado vs real»** (las horas ya viajan en cada línea para eso).

### Configuración del grupo puesta en producción (17/08/2026)
`MargenDefault = 20%` y `ImpuestoDefault = 10%` (GST de Australia; el usuario confirmó).
⚠️ Efecto colateral querido: los proyectos SIN margen propio pasan a heredar 20%, así que
Rentabilidad deja de mostrar ganancia estimada $0.

## COTIZACIONES — fase 3: ganarla y medirla (v354). MÓDULO COMPLETO
Cierra el ciclo: **cotización → obra → costo → factura**, sin teclear lo mismo dos veces.

### `aceptar_y_crear_proyecto(cid, …)`
Da de alta el proyecto con lo ya pactado: cliente, `ClienteID`, presupuesto, margen,
tipo y —solo si es Instalación con NS— el cronograma estándar (regla v306).
- ⚠️ **El presupuesto es el COSTO cotizado, NO el precio de venta.** Verificado en el
  código: `expenses.project_cost` compara `Presupuesto` contra compras + mano de obra.
  Con el precio de venta ahí, la alerta de sobre-presupuesto solo saltaría **cuando ya
  estás perdiendo dinero**; con el costo, salta cuando te estás comiendo el margen —
  que es cuando aún se puede reaccionar (la lección de v144).
- ⚠️ **Idempotente**: si la cotización ya generó proyecto, no crea otro. Probado — un
  segundo intento devuelve «Esta cotización ya generó el proyecto PRJ-0007».
- El margen efectivo de la cotización se escribe como `MargenMO` (decisión del usuario:
  una sola fuente de verdad).

### `comparacion(cid)` — cotizado vs real
Horas cotizadas contra fichadas, costo cotizado contra cargado, e ingreso fijo (lo que
el cliente aceptó).

### ⚠️ El fallo que cazó la prueba: «ganancia real» a mitad de obra
Con el proyecto al **0% y $900 de costo**, `ingreso − costo` daba **$3.499 «de ganancia»
contra $893 cotizados, en verde**. Técnicamente cierto, historia falsa: no has ganado,
es que **aún no has gastado**. Misma familia que v320 (el «sin asignar» que mentía) y
v324 (el proyecto al 0% con el mensaje más tranquilo).
**Arreglo, con el patrón de v144:** se proyecta al ritmo actual
(`costo × 100 / avance`) y la tarjeta se llama **«Ganancia proyectada»**; solo se llama
**«real»** cuando el avance llega a 100. Y **None, no 0**, mientras no haya avance ni
costo: sin base, proyectar es inventar.
```
avance   0% · costo     0 → —            (cotizada 893,20)
avance   0% · costo   900 → —
avance  25% · costo   900 → proyectada    799,20   ← ya avisa: por debajo de lo cotizado
avance  50% · costo 2.500 → proyectada   −600,80
avance 100% · costo 3.800 → real          599,20
```

### El módulo, de punta a punta (v352-v354)
Catálogo (costo) → cotización (margen por línea) → PDF sin filtrar costos → aceptada →
proyecto con presupuesto y margen → cotizado vs real. Todo ejercitado contra la hoja
real y con producción devuelta a su estado.

## Cotización: se escribe la GANANCIA, el margen % sale solo (v355)
Petición del usuario: *«el admin pone el valor que desea ganar sobre el costo base y el
% de margen se calcula de forma automática»*. Es **invertir la entrada**: antes se
tecleaba el % y salía el precio; ahora se teclea lo que se quiere ganar y sale el %.

- **`quotes.margen_de(costo, ganancia)`** es la única fórmula del %; `linea_de` y
  `recalcular` aceptan `ganancia=` (que **manda** sobre `margen_pct` si llegan las dos:
  es el dato que la persona escribió). **`ganancia_de(linea)`** la deriva del precio —
  no se guarda aparte, para que no pueda desacompasarse (lección de los helpers
  divergentes de v323).
- La tabla editable pasa a tener **«Ganancia $»** como única columna tecleable del
  precio; **Margen % y Precio quedan bloqueados** para que se lea que son consecuencia.
- `margen_pct` se conserva en la línea: lo consumen la columna Margen de la lista y el
  `MargenMO` del proyecto al aceptar. Solo cambia por dónde entra el dato.

### ⚠️ Al cambiar la CANTIDAD se conserva la ganancia, no el %
12 uds → costo 2.226, ganancia 150, margen 6,74%. A 24 uds → costo 4.452, **ganancia
sigue 150**, margen baja a 3,37%. Es lo correcto: la persona dijo cuánto quiere ganar,
no qué porcentaje.

### ⚠️ Redondeo: la invariante es `precio = costo + ganancia`, no el %
Reconstruir el precio desde el margen **redondeado a 2 decimales** da hasta 3 céntimos
de diferencia (2.376,00 vs 2.376,03). No es un fallo: el `margen_pct` es un número de
lectura y el precio se calcula siempre por la ganancia. Verificado: 36 combinaciones de
cantidad × ganancia con **0 desviaciones**, y por AST que **el único camino que aún pasa
por el margen es el alta de línea nueva** (que arranca con el default del grupo para dar
un punto de partida). El margen efectivo del total se calcula de las sumas, no de los %
por línea.

## ⚠️ Los precios de un borrador ya no cambiaban solos… porque SÍ cambiaban (v356)
Salió verificando v355 con la **cotización real del usuario**: la línea «Instalacion»
decía costo $960 (12 h × $40 × 2) y el artículo del catálogo hoy vale $40 (1 h). Lo
había editado después de cotizar. Eso **no era el fallo** —la línea congela su precio a
propósito (v353)— pero al mirar el editor apareció uno de verdad.

### El fallo: el editor refrescaba en silencio
`_editor_lineas` reconstruía cada línea desde el catálogo al guardar
(`Q.linea_de(base, cant, …)`). O sea que **tocar cualquier celda de un borrador adoptaba
los precios nuevos sin decir nada**: en su cotización, el total habría pasado de
$1.927,20 a otro número al cambiar una cantidad. Un precio que se mueve a espaldas de
quien cotiza es peor que un precio viejo.

### El arreglo, en dos piezas
1. **`quotes.escalar(linea, cantidad, ganancia)`** — cambiar la cantidad escala sobre el
   **costo unitario congelado**, sin volver al catálogo. Probado: la línea de $960 sigue
   en $960 al reescribir la cantidad (antes pasaba a $80).
2. **`desactualizadas(c)` + `actualizar_precios(cid)`** — la pantalla avisa
   («Instalacion: $960 → hoy $80») y el botón trae los precios nuevos **conservando la
   ganancia en dinero** (v355); el margen % se reajusta. Probado: 3 uds a $100 con $90
   de ganancia → sube el catálogo a $130 → tras pulsar, costo $390, **ganancia sigue
   $90**, margen baja de 30% a 23,08%.

⚠️ **Solo en borrador.** Una cotización enviada no se toca: devuelve «saca una versión
nueva» y el total no se mueve. ⚠️ Una línea cuyo artículo se borró del catálogo se
detecta, se dice y **se deja intacta** — no se descarta en silencio.

### Lo que enseña este caso
El comportamiento «correcto» (congelar el precio) y el fallo (refrescar al guardar)
convivían en el mismo módulo y se contradecían. Solo se vio **mirando datos reales del
usuario**: con mis artículos de prueba, catálogo y líneas siempre coincidían.

## Atajo: facturar desde el propio proyecto (v357)
Petición del usuario. Antes: Finanzas → Facturas → Nueva → elegir cliente → volver a
buscar el proyecto. Ahora, en 💰 Costos de la obra: **«Pendiente de facturar: $X»** +
botón **«Facturar esta obra»**, que abre el alta con cliente y proyecto ya elegidos.

⚠️ **Reutiliza el alta que ya existe** (`_fac_nueva` + `fac_cli`, el mismo camino que
Contactos desde v259). Verificado por AST: **1 formulario de alta y 1 sola llamada a
`create_factura`** en todo el repo — el atajo delega, no crea. Dos mecanismos para lo
mismo es lo que hubo que desmontar en v140 y v146.

### ⚠️ No se fija la etiqueta del proyecto desde fuera
`etiqueta_proyectos` calcula la etiqueta sobre los proyectos DE ESE CLIENTE y añade el
ID solo si el nombre se repite (v306). Fijar `fac_scope` desde el proyecto obligaría a
recalcularla con otro conjunto, y una opción que no existe **revienta el radio**. Se
pasa el **ID** en `_fac_prj_pending` y el formulario resuelve su propia etiqueta,
aplicándola ANTES de instanciar el widget (regla v111, verificado por AST: L205 < L208).

### ⚠️ El fallo que evitó mirar los datos reales
`Proyectos.Cliente` es **texto libre**. Preseleccionar el selectbox con un valor que no
está entre las opciones revienta el widget — y en producción hay dos obras con cliente
**«vd»** y **«ci»**, que no son fichas de Contactos… y las dos tienen importe pendiente,
así que el botón les habría salido. Ahora el cliente se resuelve **por `ClienteID`**
(la relación de verdad) y solo se preselecciona si el nombre existe entre las opciones;
si no, el formulario **lo explica** y deja elegir a mano.

### Detalle
El bloque no aparece si no hay nada pendiente ni facturado (no estorbar), el botón es
primario solo cuando hay algo que cobrar, y es **solo para gestión** (`can_delete`): el
campo ve sus costos pero no factura.
⚠️ De paso: al poner `MargenDefault=20%` (v353) el ingreso estimado subió, así que
`prueba1` pasó a tener **$330,48 pendientes** pese a estar facturada — es correcto, pero
conviene saber de dónde sale.

## ⚠️ Una obra ARCHIVADA se puede facturar (v358)
Encontrado verificando v357 **en producción**: el atajo de `prueba1` mostraba «Pendiente
de facturar $330», llevaba al alta de factura… y **esa obra no estaba entre las opciones
de alcance**, así que la preselección no hacía nada y el radio se quedaba en «Todo el
cliente». Causa: `_nueva_factura` arma la lista con `list_projects(grupo)`, que **oculta
los archivados** (v149), y `prueba1` está archivado.

**Archivar no es no-cobrar**: lo habitual es archivar al terminar y facturar después. Es
la cuarta vez que el default de v149 muerde donde no debía — v310 (los costos de los
archivados desaparecían del grupo), v321 (su margen se ignoraba), v322 (se caían de su
agrupación) y ahora la facturación.

**Arreglo:** si el atajo apunta a una obra que no está en la lista, se añade (validando
que sea del mismo grupo). Se mira el pendiente ANTES de calcular las etiquetas, para que
`etiqueta_proyectos` lo incluya y la preselección encuentre su opción. Verificado el
orden por AST: mirar L194 < etiquetas L203 < escribir `fac_scope` L220 < radio L226.

### ⚠️ Y mi guarda de v357 tenía un hueco MUDO
Contemplaba «el proyecto es de otro cliente» pero no «el proyecto no está en la lista»:
en ese caso `_et` era `None` y **no se decía nada**. El usuario acababa en «Todo el
cliente» sin entender por qué. Ahora ese caso también habla.

### Lo que sigue siendo limitación conocida
En el alta **manual** de factura (Finanzas → Facturas → Nueva) las obras archivadas
siguen sin aparecer: solo entran por el atajo. Si hiciera falta facturar una obra
archivada sin pasar por su ficha, haría falta una casilla «incluir archivadas» — es
decisión de producto, no se hizo por iniciativa propia.

## UN LIBRO DE GOOGLE POR EMPRESA CLIENTE (v359) — mecanismo
Decisión del usuario: **dejarlo listo sin migrar nada**, y **una sola cuenta de servicio**
(resuelve el aislamiento, que es lo que importa; la cuota ya no aprieta tras v339).

### El diseño que evita la migración
El libro actual sigue siendo **el maestro Y el libro de `cliente1`**. Los clientes nuevos
nacen con su propio archivo (`Grupos.SheetID`, columna que migra sola). Así **no se mueve
ninguna de las 21 hojas existentes** —el mayor riesgo desaparece— y el objetivo se cumple:
el segundo cliente tendrá sus datos en su propio fichero.

**Global, siempre en el maestro:** `Login`, `Grupos`, `Rieles`, `Manuales`. Son el
registro de la app, y `Login` además se lee ANTES de saber a qué grupo perteneces.
**Todo lo demás** (21 hojas) va al libro del grupo.

### Cómo se resuelve
`timeclock.sheet_id_para(title, grupo=None)`: si la hoja es GLOBAL → maestro; si no, el
libro del grupo **de la sesión** (mismo patrón que `clock.now()` con la zona horaria,
v173), con override explícito. Ninguna de las 21 llamadas a `get_sheet` cambió de firma.
- ⚠️ **El orden evita una recursión infinita**: la comprobación de GLOBAL va primero y
  devuelve sin consultar a `auth` — si no, `auth.group_sheet_id` leería `Grupos`, que es
  global, y se llamaría a sí misma. Verificado por AST (L99 < L111) y ejecutándolo.
- `_abrir/_cached_ws/_libro/get_sheet` y **`hojas._lote` se cachean POR LIBRO**. Con una
  sola entrada, el segundo cliente leería los datos del primero — justo lo contrario.
- `auth.set_group_sheet_id` acepta la **URL completa** además del ID (es lo que se copia
  del navegador) y **rechaza** enlazar dos grupos al mismo libro.

### ⚠️ Límite conocido, DICHO en la pantalla
Las cachés `_records` de cada módulo están indexadas por HOJA, no por libro. Admin y
campo van bien (siempre tienen grupo en sesión), pero los **resúmenes consolidados del
propietario** solo contarían el maestro. Hacerlo bien es tocar el `_records` de 13
módulos y **no se puede verificar sin un segundo libro real**. Se expone
`auth.grupos_con_libro_propio()` y la pantalla **avisa** de a quién le falta:
*un consolidado incompleto sin avisar es peor que no tenerlo*. Es la fase 2.

### ✅ AISLAMIENTO DEMOSTRADO CON UN SEGUNDO LIBRO REAL (18/08/2026)
La cuenta de servicio solo tiene scope `spreadsheets` y **no puede crear archivos** (403,
buena higiene), así que el libro de prueba lo creó el usuario y lo compartió con
`fichaje-bot@…`. Con él, la prueba completa:
- Enlazar **pegando la URL entera** funciona, y **rechaza** poner dos grupos en el mismo
  libro (*«Ese libro ya es de: zzz-cliente-prueba»*).
- El admin del cliente nuevo ve **0 proyectos, 0 cotizaciones, 0 artículos**: los de
  `cliente1` están en otro fichero y no se alcanzan.
- Lo que escribe cae **en SU libro**: se crearon ahí `Sheet1`, `Proyectos`, `Actividades`
  y `Catalogo`. El maestro **siguió con sus 6 proyectos**, sin mancharse.
- `cliente1` siguió viendo lo suyo entero (6 proyectos, 3 artículos, 1 cotización).
- **El cerrojo de v351 sigue valiendo entre libros**: pedir el ID del otro cliente
  devuelve 🔒, porque compara por grupo, no por ID.
- ⚠️ **Consecuencia del diseño**: los IDs son ahora **únicos por cliente, no globales**.
  Los dos libros tienen su propio `PRJ-0001`. No rompe nada —cada quien lee su libro y
  el cerrojo compara por grupo— pero hay que saberlo antes de asumir que un `PRJ-####`
  identifica algo en toda la instalación.
Limpieza verificada: grupo de prueba borrado, `Grupos` con solo `cliente1` y sin SheetID.

Cuenta con la que hay que compartir cada libro nuevo:
`fichaje-bot@gen-lang-client-0922870449.iam.gserviceaccount.com` (identificador, no clave).

## LA GANANCIA DEJA DE SER UN % (v360) — importe por rubro
Cambio de modelo pedido por el usuario: *«la ganancia ya no es un porcentaje sobre el
proyecto, es un valor sobre cada rubro (servicio, producto y trabajador)»*.

**Decisiones del usuario:** la ganancia del trabajador se mide **por hora**, se define
**por proyecto**, y los materiales cargados en obra (recibos) se facturan **a costo**.

```
ingreso  = Σ_persona( horas × (tarifa_costo + ganancia_hora) ) + materiales
ganancia = Σ_persona( horas × ganancia_hora )
```
El **porcentaje deja de ser la entrada** y pasa a ser consecuencia: se sigue calculando
para mostrarlo, pero ya no se teclea. Es v355 (cotizar por ganancia, no por %) extendido
al proyecto y a las personas.

### ⚠️ Respaldo: ninguna obra cambia de cifra en silencio
Las 6 obras tienen `MargenMO` (20-30%) y ninguna tenía ganancia por hora. Cambiar en
frío les habría desplomado el ingreso estimado —y con él **lo pendiente de facturar**—
sin que nadie lo pidiera. Así que **sin `GananciaHoraJSON` se sigue usando el modelo
viejo**, y `project_revenue` devuelve `modelo` (`"rubro"` / `"margen"`) para que la
pantalla diga cuál aplica. Verificado: las 6 siguen exactamente igual tras el cambio.

### Dónde vive y cómo se pone
`Proyectos.GananciaHoraJSON` = `{usuario: $/h}` — una columna, sin hoja nueva ni llamada
extra (misma solución que ParamsJSON/LineasJSON). Se edita en **💰 Costos → «Cuánto ganas
con cada persona»**, junto a «Mano de obra por persona», que es donde ya se ve quién
trabajó y cuánto costó. Solo se teclea la **Ganancia/h**; Precio/h y «Ganas» van
bloqueados porque son consecuencia (igual que en v355).

### Probado con datos reales (PRJ-0001)
```
antes  modelo=margen  costo 3.146,40 · ingreso 3.475,68 · ganancia 329,28 · margen 20%
$15/h  modelo=rubro   costo 3.146,40 · ingreso 3.763,80 · ganancia 617,40 · margen 37,5% (derivado)
       campo1 32,16 h × $15 = 482,40 · lksdfkldsf 8,97 h × $15 = 134,55 · admin1 0,03 h = 0,45
```
- ⚠️ **Quien no tenga ganancia puesta se factura A COSTO**, y se dice (`sin_ganancia`):
  el patrón de las colillas de $0 de v346 — un cero silencioso no se nota hasta el total.
- ⚠️ **Reversible**: quitar las ganancias devuelve la obra al modelo viejo y el ingreso
  vuelve **exactamente** a 3.475,68. Si migras una obra por error, se deshace.

### Pendiente
`MargenMO` y `Grupos.MargenDefault` quedan como respaldo, no se han retirado. Al aceptar
una cotización se sigue escribiendo `MargenMO`: la cotización tiene ganancia por LÍNEA
de servicio, no por persona, y al aceptarla todavía no hay nadie asignado — no hay mapa
que rellenar. Convertir una en otra (p. ej. ganancia_servicios ÷ horas cotizadas como
$/h por defecto) queda para cuando se vea con una obra real.

## ⚠️ Rentabilidad tenía su PROPIA fórmula del ingreso (v361)
Salió al poner 15 $/h a `campo1` en `prueba1` para probar v360: el detalle del proyecto
decía **ingreso 3.628,80** y la pantalla de Rentabilidad **3.475,68**. Dos cifras de
dinero para la misma obra, a la vez.

**Causa:** `group_profitability` **no llamaba a `project_revenue`** — reimplementaba la
fórmula (`ingreso = mo * (1 + m/100) + mat`). Mientras el único modelo era el %, las dos
coincidían por casualidad; con el modelo por rubro dejaron de coincidir. Es el fallo de
los cinco `_num` divergentes de v323, esta vez con importes en pantalla.

**Arreglo:** delega en `project_revenue`, que pasa a ser la ÚNICA definición del ingreso.
No cuesta llamadas nuevas (lee de las mismas cachés que `group_expenses`). La fila gana
`modelo` y `sin_ganancia` para que la pantalla pueda decir cuál aplica cada obra.
**Guardián**: por AST, solo `project_revenue` puede aplicar el `%` de margen.

### ⚠️ Y un fallo de método: un parche que no comprueba que se aplicó, miente
El patch de v360 intentaba añadir `"modelo"` a esa fila con un ancla que **no existía**,
y estaba envuelto en `if ... not in s:` — así que **no hizo nada y no dijo nada**. El
síntoma (`modelo=None`) solo se vio al mirar la salida con datos reales. Los parches
tienen que `assert` que el ancla existe, como los demás de esta tanda.

### Prueba en producción (a petición del usuario)
`PRJ-0001` con 15 $/h para `campo1`: modelo `rubro`, ingreso **3.628,80**, ganancia
**482,40**, margen **29,3%** derivado. `lksdfkldsf` y `admin1` siguen sin ganancia → su
trabajo se factura a costo y la pantalla los nombra. Lo pendiente de facturar sube de
**330,48 a 483,60**. Las otras 5 obras siguen en el modelo viejo, sin moverse.

## ⚠️ La misma persona salía PARTIDA en dos (v362)
Salió al poner ganancia a las tres personas de `prueba1`: al mirar quiénes eran,
`campo1` y `lksdfkldsf` **son la misma** — `campo1` es el usuario y `lksdfkldsf` su
nombre. En el fichaje hay **2 filas sin la columna `Usuario`** (anteriores a v106,
cuando el fichaje se identificaba solo por nombre) que caían bajo el NOMBRE, así que
`labor_breakdown` la partía: 32,16 h como `campo1` y 8,97 h como `lksdfkldsf`.

**Por qué no se había notado nunca:** mientras eso solo se SUMABA, el total salía bien.
Desde v360 hay que decidir la ganancia **por persona**, y partida significa ponérsela dos
veces — o, como pasó literalmente un turno antes, **dejarse 8,97 h facturándose a costo**
sin que nada lo delatara. Un cambio de modelo puede convertir en fallo algo que llevaba
años siendo inofensivo.

**Arreglo:** cuando la fila no trae `Usuario`, se resuelve por su `Nombre` contra las
cuentas del grupo. ⚠️ **Solo si ese nombre pertenece a UNA sola cuenta**: con homónimos
—los hubo, `fijiofgjei` tenía dos— adivinar mezclaría a dos personas, que es peor que
dejarlas separadas.

**Verificado con datos reales:** `campo1` pasa a 41,13 h en una sola fila y el **total no
se mueve** ($1.646,40 antes y después) — solo cambia cómo se agrupa. Con los tres a
$15/h: ganancia $617,40, ingreso $3.763,80, margen 37,5% derivado, nadie sin ganancia.
Es la misma familia que v145 (fichajes sin `ProyectoID`): filas viejas a las que les
falta una columna que se añadió después.

## ⚠️ CREAR PROYECTOS LLEVABA 3 VERSIONES MUERTO + el resolvedor único (v363)
Salió al poblar la app con una empresa simulada (el usuario autorizó simular datos:
todo lo del grupo `cliente1` es de prueba). Se intentaron crear 9 obras y **fallaron las
9**.

### El fallo: una fila de 31 valores para una cabecera de 32
En **v360** añadí `GananciaHoraJSON` a `PROJECTS_HEADERS` y **no añadí su valor** a la
fila posicional de `create_project`. El guardián de v306 corta con «Error interno» antes
de escribir, así que desde v360:
- **«➕ Nuevo proyecto» no creaba nada**
- **«Aceptar cotización» tampoco** (llama a `create_project`) → el módulo de
  cotizaciones no podía rematar su ciclo
⚠️ **Matiz que corrige lo que dije al principio**: 31 valores en 32 columnas **NO
desplazan los datos** — `append_row` deja vacías las de la cola (así escriben
`auth.add_user`, 6 de 11, y `add_group`, 4 de 9, a propósito). El daño no era corrupción
silenciosa: era que la función **no hacía nada**.

### Por qué vivió 3 versiones y el guardián nuevo
El de v306 es de **EJECUCIÓN**: solo salta cuando alguien pulsa el botón, y nadie creó un
proyecto entre v360 y v363. El nuevo (`verif_v363.py`) es **ESTÁTICO**: por AST cuenta los
elementos de **las 25 filas posicionales del repo** y los compara con su cabecera.
- Resuelve la cabecera de cada función en 5 pasos, y **la auto-validación manda**
  (`if len(row) != len(X_HEADERS)`): tenerla de último recurso hacía que una fila rota
  —que ya no casa por longitud— se reportara como «no resuelta» en vez de «esta función
  está MUERTA». Detectaba, pero diagnosticaba mal.
- Distingue **fila corta legítima** (cola vacía) de **función muerta** (la que se
  auto-valida con igualdad estricta).
- ⚠️ **Primera versión daba «✓ ninguna descuadra» habiendo comprobado 1 de 25** (las
  otras 24 salían «cabecera ambigua» y se saltaban): el paso en VACÍO de siempre. Ahora
  lo no resuelto cuenta como FALLO del chequeo, no como aprobado.
- Probado contra el código ROTO: señala `create_project` y sale con error.

### El resolvedor de identidad, en UN solo sitio
v362 arregló «la misma persona partida en dos» **solo en `expenses.labor_breakdown`**. El
patrón estaba copiado en **5 funciones más** y ninguna se tocó → la pantalla de Horas
seguía mostrando a `campo1` como dos filas (`campo1` 353,7 h y `lksdfkldsf` 9,0 h, con el
costo repartido), y la conciliación inflaba «horas cobradas sin pagar» con un fantasma.
⚠️ Y `existe` daba **True** para el fantasma, porque `claves_conocidas` incluye nombres
además de logins: ni siquiera se marcaba como cuenta de baja.
**`timeclock.clave_de(fila, por_nombre)` + `mapa_nombres(grupo)`** — una definición, la
usan las 6 (`group_hours`, `jornada_y_proyecto`, `horas_por_usuario_rango`,
`proyectos_por_usuario_dia`, `spend_curve`, `labor_breakdown`). Es el patrón de `num.py`
en v323 aplicado a la identidad.
- ⚠️ **La verificación obvia era una trampa**: comparar el total de horas antes/después
  en dos ejecuciones daba 20 h de diferencia… porque había una sesión ABIERTA acumulando
  contra el reloj (llevaba 33,6 h). Un **FALLO en falso**, gemelo del OK en falso. La
  comparación válida es vieja lógica vs nueva **sobre las mismas filas y el mismo
  instante**: diferencia 0,000006 h (0,02 s de ruido de flotantes sobre 3.309 h) y el
  dinero idéntico ($113.361,71 en las dos).
- ⚠️ Mi epsilon de `1e-6` hacía FALLAR el test por su propia aritmética. Tolerancia con
  sentido físico (< 3,6 s sobre 3.300 h).
- Los homónimos **siguen separados**: `Mei Chen` (`mchen`/`mchen2`) en dos filas, que es
  lo correcto — adivinar mezclaría a dos personas.

## ⚠️ SE PAGABAN LAS MISMAS HORAS DOS VECES: periodos que solapan (v364)
Encontrado con la empresa simulada, y de la forma más real posible: **dos personas
generando nóminas a la vez** (el usuario emitió 21/07→19/08 en la app mientras el
escenario creaba quincenas 20/07→02/08 y 03/08→16/08).

`generar` construye el salto de duplicados como la **terna EXACTA**
`(Usuario, PeriodoDesde, PeriodoHasta)`, así que un rango que **solapa** no se detectaba:
```
campo1:  22/06→05/07  72,5 h · 06/07→19/07  73,5 h · 11/07→09/08  32,2 h
         20/07→02/08 113,6 h · 21/07→19/08 198,7 h · 03/08→16/08  76,6 h
         pagado 567,01 h   ·   trabajó realmente 353,67 h   → 213 h de más
```
⚠️ **La conciliación de v313 YA lo estaba gritando** («sin explicar −$36.035,90»), pero
DESPUÉS de emitir. El error es invisible en la colilla individual —cada una sale bien— y
solo el total del periodo lo delata.

**Arreglo:** intersección de intervalos cerrados por persona; si cruza, **no se emite** y
se NOMBRA la nómina que estorba (id + fechas) para poder anularla o mover el rango.
- El **duplicado exacto** sigue tratándose como antes (`omitidas`), sin cambio.
- Las **anuladas no bloquean** (principio de v347: si se puede deshacer, se puede rehacer).
- **Quincenas contiguas SÍ pasan** (03/08 pegada a un 20/07→02/08): si no, el bloqueo
  sería inservible para el uso normal.
- ⚠️ **Sin fechas legibles NO se afirma que solapan**: no se bloquea a ciegas.
- Probado en 7 escenarios con la función REAL y worksheet simulado, y **en vivo contra la
  hoja**: 14 solapes detectados, **0 filas escritas**; y un periodo limpio (17-18/08)
  entró con 6 colillas.

### Estado de los datos tras la limpieza
Anuladas las 7 nóminas solapadas del 21/07→19/08. La conciliación pasa de **−$36.035,90
a −$1.634,40**, y esa cifra está explicada al céntimo: es el doble pago **histórico** de
`NOM-0003` + `NOM-0006` (periodo 11/07→09/08, que cruza las quincenas). Verificado
descomponiendo: $4.387,00 trabajados sin pagar − $1.634,40 pagados dos veces = $2.752,60,
que era exactamente el `sin_explicar` intermedio.

## ⚠️ 87 MENSAJES QUE NADIE VIO NUNCA: `st.rerun()` tira los deltas (v365-v367)
Salió de una verificación fallida, no de leer código: al comprobar v364 en el navegador,
**el mensaje de bloqueo no aparecía**. Pensé que era mi clic (el panel me daba una escala
de screenshot que no correspondía con las coordenadas CSS). No lo era.

### El mecanismo
`st.rerun()` **descarta los deltas del run en curso**, así que un `st.success(...)`
emitido justo antes NUNCA llega a la pantalla. Es el mismo principio que v222 documentó
para `components.html`, aplicado a los mensajes. Confirmado con `git show`: el
`st.rerun()` que se comía los mensajes de nóminas **es anterior** a mi cambio, así que
llevaba versiones tirando:
- «N nómina(s) creada(s)»
- el aviso de v346 sobre quien no tiene tarifa — **la razón de ser de esa versión**
- el bloqueo de solape de v364, recién estrenado

### `core/flash.py` — mecanismo ÚNICO
Módulo HOJA (solo importa streamlit → sin ciclos, como `num.py` y `tenant.py`). El
mensaje se ENCOLA y lo pinta la shell (`home_ui.render_admin_content`) y el login
(`auth_ui.render_login`, porque el bootstrap ocurre antes de la shell). Cola en LISTA:
generar nóminas deja tres mensajes a la vez.
⚠️ `st.toast` NO lo necesita: sobrevive al rerun por su cuenta.

### ⚠️ Mi guardián estaba CIEGO dos veces (19 → 87)
1. **Solo veía `st.success(...)` como atributo directo.** El idioma que más usa este
   repo es `(st.success if ok else st.error)(msg)`, donde el llamable es un `IfExp`.
   **El fichaje entero se escapó del barrido por eso.**
2. **Solo veía el rerun como HERMANO.** En el fichaje está anidado:
   `(st.success if ok else st.error)(msg)` / `if ok: st.rerun()`.
Con las dos corregidas: **19 → 87**. Lección de v349 otra vez — un guardián acota el
fallo a la forma en que lo viste; cuando reaparece, la pregunta es *por qué no lo vio*.

### ⚠️ Dos trampas que me habrían hecho ROMPER cosas
1. **La rama de ERROR no se convierte.** En `(st.success if ok else st.error)(msg)` con
   `if ok: st.rerun()`, solo muere el éxito: el error se pinta y se queda porque ahí no
   hay rerun. Convertir las dos habría hecho **desaparecer los mensajes de error** —
   peor que el problema original. Queda `(flash.exito if ok else st.error)(msg)`.
   El guardián también tuvo que aprenderlo: marcaba 68 falsos positivos (todos los
   `st.error` que SÍ se ven) y me habría empujado a romperlos.
2. **Las insignias de ESTADO tampoco.** Mi primer parche convirtió esto:
   ```python
   st.success("Telegram vinculado.")   # estado, se pinta SIEMPRE
   if st.button("Desvincular"):
       st.rerun()                       # solo al pulsar
   ```
   Habría borrado el estado y hecho aparecer un mensaje fantasma en otra pantalla. Lo vi
   revisando el diff, **reverté desde el respaldo** y afiné la regla: un rerun bajo
   `if st.button(...)` no mata nada, porque el mensaje de arriba se pinta en cada pasada.

### ⚠️ Y el chequeo de ámbito dio un OK EN FALSO — el error de v342, dentro del chequeo
`auth_ui` ya tenía `from core import flash` **dentro de `render_login`**, así que mi
patch lo dio por importado y no añadió el de módulo → **4 NameError** esperando en
producción. Y mi verificador dijo «✓ todos bien» porque su `importa_flash` **descendía
dentro de los `def`** y encontraba el import local de otra función. Es literalmente el
fallo que v342 documentó, cometido dentro del chequeo escrito para cazarlo.
**Comprobar el ÁMBITO, no la presencia** — y no descender a un `def` al mirar el módulo.

### Verificado en vivo
Nóminas: los tres mensajes en pantalla, incluido el de v346 que llevaba 20 versiones sin
verse. Fichaje: `✅ Clock IN Jornada (general) a las 21:31:46` y `✅ Clock OUT … Horas
trabajadas: 0.01` — las dos líneas que se generaban y se tiraban desde v150.
Guardián probado contra el código roto (revertir un sitio → lo caza).

## El bloqueo de contacto solo debe exigir canales que EXISTAN (v368)
⚠️ **Esta sección se reescribió: la primera versión exageraba el fallo.** Se dijo que 7
usuarios estaban «encerrados sin salida» en producción, y **no era cierto** — ver el
error de método al final, que es la parte que de verdad hay que recordar.

### El defecto (real, pero LATENTE)
`app.py` exigía email **Y** Telegram a todo usuario de campo (v79) **sin comprobar si el
canal existe**. En una instalación SIN bot en Secrets eso no tiene salida:
- la pantalla de bloqueo no puede mostrar el link de Start (ese bloque está condicionado
  a `telegram_configured()`) → el usuario ve «Pendiente: Telegram» y **nada más**;
- el admin tampoco tenía botón: su ficha decía «Telegram no configurado» y punto.
Es el patrón de v325 y v340: **un pendiente que nadie puede cerrar es peor que no
tenerlo**. Pero es un defecto de diseño para instalaciones sin bot, **no una avería que
estuviera ocurriendo**.

**Arreglo: solo se exige un canal que EXISTA.**
```python
_tg_hay   = notify.telegram_configured() and notify.bot_username()
_falta_tg = _tg_hay and not _has_tg        # sin bot, no se pide
```
Con bot, todo sigue igual. Además la pantalla dice **quién** lo resuelve: el email lo
carga el administrador y el usuario no puede ponerlo — antes decía «Pendiente: Email» y
lo dejaba adivinando. Y la ficha del admin ofrece meter el chat_id a mano.

⚠️ Verificado evaluando la condición **leída de `app.py` por AST**, no una copia (el OK
en falso de v324): 8 escenarios (bot × email × telegram) correctos y **ningún bloqueo sin
salida**. Probado contra el código roto.

### ⚠️ EL ERROR DE MÉTODO (esto es lo que hay que recordar)
Comprobé `notify.telegram_configured()` **en local**, salió `False`, y lo presenté como
el estado de PRODUCCIÓN: «7 usuarios encerrados, sin salida posible». Al entrar en el
Cloud con uno de ellos, la pantalla mostró *«abre el bot → t.me/**copex_avisos_bot**»*:
**el bot SÍ está en los Secrets del Cloud**, así que esos usuarios siempre tuvieron su
camino (pulsar Start + que el admin les vincule). Nunca hubo encierro.

**La regla que ya existía para las hojas vale igual para los SECRETS**: mi
`secrets.toml` local NO es el del Cloud. Un `is_configured()` / `telegram_configured()` /
`app_url()` medido en local dice qué tengo yo, no qué tiene producción. Para afirmar algo
del entorno real hay que mirarlo EN el entorno real — en este caso, la propia pantalla.

⚠️ Y tuvo consecuencia práctica: creyendo que el canal no existía, retiré los chat_id de
prueba «porque ya no hacían falta» → **volví a bloquear a los 7**, y hubo que reponerlos.


## Facturar una obra ARCHIVADA desde el alta manual (v369)
`list_projects` las oculta desde v149 — correcto para una lista, falso aquí: **archivar
no es no-cobrar**, lo normal es archivar al terminar y facturar después. v358 lo resolvió
solo para el atajo desde la ficha del proyecto; desde Finanzas → Facturas → Nueva seguían
siendo **inalcanzables**. Es la quinta vez que ese default muerde (v310, v321, v322, v358).

Se usa la pieza que la app ya tiene para esto (v149 en la cartera, v340 en Contactos e
Inventario): **casilla con contador**, desmarcada por defecto.
- La etiqueta marca **«· archivada»**: si no, en el radio son indistinguibles de las
  activas y no se entiende por qué aparece una obra que se creía cerrada.
- ⚠️ **Al desmarcar se suelta el alcance elegido ANTES de instanciar el radio.** Un
  `st.radio` cuyo valor guardado ya no está entre sus opciones revienta — es el mismo
  fallo que v358 esquivó por otro lado. Verificado en vivo: elegir «prueba1 · archivada»
  y desmarcar devuelve la lista a las activas **sin excepción**.
- El atajo de v357/v358 se conserva: debe seguir funcionando sin obligar a marcar nada.

**El dato que lo justifica**: `cliente 1` tenía **3 obras archivadas con dinero sin
facturar** — `prueba1` $618,15, `north` $415,20, `norte` $0,48.

## ⚠️ Una obra cotizada vale el PRECIO PACTADO, no costo+margen (v370)
Salió al mirar el pendiente «7 obras sin horas no admiten ganancia por rubro», que yo
había clasificado como *«dato, no fallo»*. **Lo era: había un agujero detrás.**

### Los materiales van a costo en LOS DOS modelos
`ingreso = mo × (1+m) + mat` (viejo) y `Σ(horas × (tarifa+ganancia)) + mat` (v360): el
margen solo se aplica a la mano de obra. Así que **una obra cuyo valor NO está en las
horas vale exactamente lo que costó**. Medido:
| Obra | Costo | La app decía | Realidad |
|---|---|---|---|
| Bespoke — Delivery Chullora | $380 | **$380** (ganancia $0) | facturado **$5.200** |
| Stockland Bankstown — Ripout | $0 | **$0** | cotización aceptada **$2.960** |
El resultado REAL salía bien (`resultado_por_proyecto` usa la factura); lo que mentía era
la **estimación**, y de ella cuelgan «ingreso estimado» y «pendiente de facturar». Daño
concreto: un delivery sin facturar aparecería como **$380 por cobrar** en vez de $5.200.

### El arreglo: usar el número que ya se tiene
Al aceptar, la cotización guarda su `ProyectoID` (v354) — pero **el enlace era de una sola
dirección** y `project_revenue` no lo miraba: estimaba el precio desde el costo teniendo
delante el que el cliente había firmado. Nueva `quotes.cotizacion_de_proyecto(pid)` y, si
existe, **ingreso = precio pactado** (`modelo: "cotizado"`, cita el ID de la cotización).
Misma regla que v361: **una sola definición del ingreso**, y un hecho gana a una conjetura.

- ⚠️ **La base es el `Subtotal`, NO el `Total`.** `invoices.facturado_por_proyecto` suma
  los IMPORTES DE LÍNEA, sin impuesto. Usar el total con GST habría inflado
  `pendiente_de_facturar` **exactamente en el impuesto** ($296 en el caso real) y nadie lo
  habría notado hasta cuadrar cuentas.
- **Sin columna nueva en el proyecto**: se busca sobre las cotizaciones, ya cacheadas
  (0 llamadas) y sin dos campos que puedan desincronizarse.
- **`sin_ganancia` se vacía** en este modelo: ese aviso dice «este trabajo se facturaría a
  costo», y con precio cerrado no puede pasar.
- **Rentabilidad lo recoge sola** porque delega en `project_revenue` desde v361, y
  «Sin facturar» pasó a avisar de los $2.960 que antes no existían.
- ⚠️ Ejercitando el `except` **de verdad** (simulando que las cotizaciones fallan)
  apareció un `logger` **inexistente en el módulo**: un `NameError` latente escondido justo
  donde nadie mira. Añadido el logger.

⚠️ **Lo que NO cubre**: una obra creada A MANO cuyo valor no está en las horas (el delivery
de Bespoke) sigue valiendo su costo. Para eso haría falta una **ganancia fija por obra**
(un importe a nivel de proyecto), que quedó ofrecida y sin decidir.

## ⚠️ EL AVANCE DEL CAMPO NO MOVÍA EL % DEL PROYECTO (v372)
Salió ejercitando la ÚNICA escritura del campo (`save_field_progress`, la tabla de
avance de 📋 Mis proyectos), que era el hueco de verificación que quedaba. Las 6 ramas
de v162 estaban perfectas; el fallo estaba en las dos líneas del final.

### El orden: recomputar antes de invalidar
```python
    aws.batch_update(batch, ...)        # las actividades se escriben BIEN
    _recompute_project_avance(pid)      # ← lee `list_activities`, CACHEADA 120 s
    _invalidate()                       # ← la caché se tira DESPUÉS
```
`_recompute_project_avance` recalculaba el % **con las actividades viejas**. Y la caché
está caliente **siempre**, porque la pantalla acaba de pintar esa misma tabla para
editarla. Medido contra la hoja real:
```
actividades escritas en la hoja → el proyecto debería ir al 26,0%
lo que la app escribió          →                            0,0%   (26 puntos atrás)
estado escrito: 'Planificado'   (con 26% debería ser 'En progreso')
```
**Prueba de causa** (no basta con leer el código): el MISMO guardado con la caché vacía
escribe 26,1% correctamente. Si con la caché fría cuadra y con la caliente no, la causa
es el ORDEN.
- **Es una regresión de v162**: el camino viejo (`update_activity_progress`) lo hacía
  bien — recomputaba **en memoria** sobre las filas que acababa de leer frescas. Al
  sustituirlo por el batch, ese recompute pasó a leer de la caché.
- **Un solo sitio**: los otros tres (`add_activity`, `delete_activity`,
  `save_activities`) ya invalidaban primero. El arreglo es intercambiar dos líneas.
- **A qué afectaba**: `Avance` y `Estado` del proyecto alimentan la cartera, la curva S
  real, el SPI/retraso, el KPI de avance promedio, el radar del admin y el avance
  consolidado de la agrupación. El campo actualizaba, la actividad cambiaba y **el
  proyecto se quedaba una pasada por detrás** — y si nadie más escribía, ahí se quedaba.

### Y dos de la tabla: la celda BORRADA
`int(r["Avance %"])` sobre una celda vaciada (`NaN`) lanza `ValueError` → **el botón
«Guardar avances» revienta y se pierde TODA la edición**, no solo esa fila. Ahora se
comprueba `pd.isna` y **vaciar no es poner 0**: la actividad se deja como estaba y se
dice cuáles. La nota vacía guardaba el texto literal `"nan"`; ahora guarda `""`.
- ⚠️ **El aviso tenía que ir por `flash`**: mi primera versión lo puso con `st.warning`
  justo encima de un `st.rerun()` — el fallo de v365, cometido dentro del arreglo. Va
  por la cola en la rama que recarga y directo en la que no (encolarlo sin rerun lo
  dejaría de fantasma en otra pantalla).

### ⚠️ Y un FALLO EN FALSO de mi propio test
La primera pasada dio 5 ✗ en ramas que estaban bien: comparé `"40"` contra lo que hay en
la hoja, que es `str(float)` → **`"40.0"`**. Los valores impresos eran correctos y el
veredicto decía lo contrario. **Comparar números como texto es un generador de fallos en
falso** — gemelo del OK en falso, y ya van dos (v363 fue el otro).

### Guardián
`verif_v372.py`: por AST, toda función que llame a `_invalidate` y a
`_recompute_project_avance` tiene que llamar a **invalidar primero** (4 revisadas; menos
de 4 = el chequeo pasó en vacío y falla), la guarda de `pd.isna` existe, el aviso va por
`flash` en la rama con rerun y directo en la otra, y `flash` está importado **a nivel de
módulo** (regla v342/v366: ámbito, no presencia). Probado contra el código roto: señala
`save_field_progress` **y solo a esa**.

## Un check en NO escala, y la obra sin horas ya puede valer algo (v373)
Las dos decisiones que quedaban pendientes, resueltas por el usuario.

### Un control en NO abre alarma (cierra el standing item de v158)
Hasta v372 **solo el near miss** abría alarma: un check en NO se veía con su semáforo
rojo en la ficha del pre-start y **no salía de ahí** — un control de seguridad sin
cumplir que solo conocía quien abriera ese registro. El mecanismo para escalarlo existía
desde v88. Estaba documentado como decisión deliberada; el usuario decidió cambiarlo.
- ⚠️ **UNA alarma con todos los checks, no una por check**: `report_problem` escribe
  **y notifica** por Telegram/email, así que N checks serían N avisos por un solo
  formulario.
- ⚠️ **Separada de la del near miss**: son dos cosas distintas — un near miss es un
  suceso, un check en NO es un control que falta poner. Se resuelven por separado.
- ⚠️ Solo cuenta `NO`: el `N/A` de la sección 3 es una respuesta legítima, y un check
  sin responder no puede llegar (la UI no deja generar el pre-start hasta que están
  todos, v158).
- La pantalla usa `res["checks_no"]`, lo que devuelve `submit`, **no una segunda cuenta**
  a partir de s1/s3: si divergieran, diría una cosa y la alarma otra.
- ⚠️ **NO ejercitado contra producción**, por la misma razón que `near_miss=YES` y
  `notify_expiring`: mandaría correo y Telegram a personas reales. Verificado por AST
  y con la lógica de conteo sobre datos.

### Ganancia FIJA por obra — el hueco que v370 dejó abierto
v370 arregló las obras que **nacieron de una cotización**. Una creada A MANO cuyo valor
no está en las horas seguía valiendo su costo, porque el margen solo se aplica a la mano
de obra y los materiales van a costo en los dos modelos. Columna nueva `GananciaFija`
(importe, al final → migra sola) + `ganancia_fija()` / `set_ganancia_fija()`.
```
Bespoke — Delivery Chullora   costo $380 · facturado $5.200
   antes:  ingreso estimado $380      ganancia $0        modelo «margen»
   ahora:  ingreso estimado $5.200    ganancia $4.820    modelo «margen+fija»
```
- **Se SUMA al modelo que aplique** (rubro o margen) porque responde a otra pregunta:
  «además de lo que gano con las horas, ¿cuánto vale esta obra por sí misma?».
- ⚠️ **A una obra COTIZADA no se le suma**: la cotización es el precio que el cliente
  firmó y añadirle algo encima inventaría un ingreso que nadie aceptó. Se devuelve
  `fija_ignorada` para poder **avisar** de que ese número no se está usando, en vez de
  ignorarlo en silencio.
- ⚠️ **`margen_pct` conserva su denominador.** Mi primera versión lo cambió a
  `ganancia_total / costo`, lo que habría movido el % de **todas** las obras que no usan
  la fija — justo lo contrario de la regla de v360. El margen del conjunto va en una
  clave APARTE (`margen_total_pct`). Verificado obra por obra: **las 16 dan la misma
  cifra que antes**.
- **La vuelta atrás existe** (regla v340/v346): poner 0 la quita y el ingreso vuelve
  EXACTAMENTE al valor anterior. Probado en vivo.
- ⚠️ **La pantalla donde ponerla no se dibujaba** para la obra que la necesita:
  `_ganancia_section` volvía si nadie había fichado, y un delivery no tiene horas. Ahora
  la tabla persona×ganancia solo se dibuja si hay gente (con la lista vacía,
  `disabled=[...]` apuntaría a columnas inexistentes) y la ganancia fija se ofrece
  siempre.
- ⚠️ **La fila posicional**: se añadió la columna Y su valor en `create_project` en el
  mismo cambio. Olvidarlo es exactamente lo que mató a esa función 3 versiones (v363).

### ⚠️ `GananciaHoraJSON` llevaba 13 versiones SIN auditar
Decide desde v360 lo que se le cobra al cliente por cada hora y **no estaba en
`CAMPOS_CLAVE`**: es el mismo hueco que `MargenMO` en v344 y `CostoUnit` en v352,
**tercera vez**. Añadidos los dos. Regla: si un campo mueve dinero, entra en
`CAMPOS_CLAVE` en el MISMO lote en que se crea.

### ⚠️ Y la regla v135, sexta vez
Llamé `historial("proyecto", PID)` cuando la firma es `historial(grupo, entidad,
entidad_id)` → el rastro salió **vacío** y por un momento pareció que la auditoría no
había registrado nada. Sí lo había hecho: las 3 anotaciones estaban ahí, con el
`'' → '4820.0'` y su vuelta. **Antes de denunciar un fallo, comprobar la firma.**

## Fichar desde el sidebar + el Pre-Start del día se recuerda solo (v374)
Petición del usuario: un atajo de Clock IN en la barra izquierda, el Clock OUT a mano
una vez fichado, y **un aviso al fichar** que recuerde hacer el Pre-Start del día.

### El sidebar deja de ser un mirador
v202 puso ahí el cronómetro en vivo y lo dejó **solo para mirar** («el fichaje se
gestiona en la pestaña»), y encima solo aparecía **si ya estabas fichado**: para la
acción más repetida del día había que ir a la sección. Ahora:
- **sin fichar** → botón de tu asignación de hoy (1 toque, del tablero) + selector con
  el resto de obras. Decisión del usuario entre tres opciones.
- **fichado** → los cronómetros de siempre + «Salir del proyecto» y «Cerrar jornada».
- **sin obras que imputar** → al menos «Abrir jornada», que es el tiempo pagado.
- ⚠️ El proyecto SIEMPRE de una lista y sin preselección silenciosa (v139/v150), y el
  **nombre limpio** aparte de la etiqueta: la etiqueta puede llevar el ID detrás y
  `fichar_proyecto` lo escribe TAL CUAL en la hoja (el fallo que corrigió v308).
- ⚠️ Todo mensaje por `flash`: estas acciones acaban en `st.rerun()`, que descarta los
  deltas de la pasada (v365). Un `st.success` ahí no se vería nunca.

### El aviso del Pre-Start
`prestart.hecho_hoy(pid, grupo)` — ⚠️ **por OBRA y DÍA, no por persona**: el Pre-Start
es la charla de seguridad del SITIO (una por obra y día, con sus asistentes), así que si
el facilitador ya la hizo, al resto de la cuadrilla no se le recuerda nada. Decisión del
usuario. Sale de registros ya cacheados y `PreStarts` está en el lote de v339 →
**0 llamadas nuevas** (comprobado en `HOJAS_LECTURA`, no supuesto).
- **Modal** (`st.dialog`) al fichar a una obra sin Pre-Start + **chip persistente** en el
  sidebar mientras falte: el modal se puede cerrar y perder; el chip no.
- ⚠️ Se dispara por **BANDERA**, en la pasada SIGUIENTE al fichaje: abrirlo en la misma
  pasada no serviría de nada porque el `st.rerun()` la descarta (v365 otra vez).
- ⚠️ Se llama al **TOP LEVEL** del script (`app.py`), NO dentro del `with st.sidebar:`:
  en Streamlit manda el contenedor activo.
- ⚠️ Se PARSEA la fecha en vez de compararla como texto: `submit` la escribe en ISO,
  pero una fila vieja podría traer `20/08/2026` y una comparación de cadenas diría
  «no hecho» con el Pre-Start delante (el fallo de v323 en las facturas del P&L).
- El destino depende del ROL: para el campo es sección propia (`prestart`, v154), para
  el admin una sub de Herramientas. Guardián: los dos destinos existen (regla v303).

### ⚠️ Verificado EN VIVO antes de construir encima
`st.dialog` existe en la 1.57, pero «existe en la API» no es «funciona ahí» — el CSS del
menú (v304) y el `st_folium` de 500 px (v307) ya enseñaron esa lección. Mini-app +
inspección del DOM, **con la estructura exacta del código final** (el modal abierto desde
una función de módulo mientras otra pinta el `with st.sidebar:`):
| Qué | Resultado |
|---|---|
| se pinta SOBRE la página disparado desde el sidebar | ✓ 500×254 |
| SOBREVIVE al `st.rerun()` del fichaje | ✓ |
| el botón de dentro navega y lo cierra | ✓ |
| **NO reaparece** en pasadas siguientes | ✓ (6 después, cerrado) |
| el chip del sidebar sigue tras cerrar el modal | ✓ |
- ⚠️ **Falsa alarma resuelta midiendo**: el título mostraba `health_and_safety` como
  texto. No era un fallo — los Material Symbols son **ligaduras de fuente** (trampa nº5),
  así que `innerText` da el nombre aunque el icono se pinte. Medido: `font-family:
  "Material Symbols Rounded"`, 24 px de ancho. Un glifo, no una palabra.

### Las dos direcciones de `hecho_hoy`
⚠️ Comprobar solo que devuelve `False` es el **paso en vacío** (trampa nº1): un
`return False` fijo lo pasaría, y el recordatorio saldría para siempre aun con el
Pre-Start hecho. Se movió el DÍA (parcheando `clock.today`) en vez de escribir filas en
producción: obra con pre-start ese día → **True**; otra obra el mismo día → False (es por
obra); la misma obra otro día → False.

## ⚠️ LA SONDA ESTABA CIEGA: diagnostiqué un fallo que no existía (v375)
Verificando v374 en producción, mi comprobación decía que **el pop-up no se pintaba
nunca** — ni siquiera un instante, según un `MutationObserver`. Diagnostiqué la causa,
la arreglé y desplegué v375. **Y el fallo no existía.**

### El error: la sonda buscaba un selector de OTRO entorno
Mi observador y todas mis comprobaciones buscaban **`div[role="dialog"]"`**, que es como
marca el modal el Streamlit **local** (1.57) donde probé la mini-app. El Streamlit que
resuelve el **Cloud** lo marca **`[data-testid="stDialog"]`**. Buscando el selector
equivocado, un modal perfectamente pintado daba «no existe» — y encima con la autoridad
de un observador que «no vio nada aparecer».

**REGLA NUEVA: una sonda NEGATIVA hay que validarla contra un caso conocido-bueno.**
Antes de concluir «X no se renderiza», comprobar que la sonda SABE ver X cuando X está.
Si hubiera buscado el modal con dos selectores, o hubiera mirado la captura antes de
diagnosticar, me habría ahorrado un despliegue y una alarma falsa al usuario. Es
familia de la trampa nº5 (las ligaduras de fuente) y de v304 (el CSS que dejó de
aplicar): **el DOM de Streamlit cambia entre versiones, y el entorno donde pruebo no es
el que corre.** La misma lección que v368 dio con los `secrets`, ahora con el DOM.

### Qué se queda de v375, y por qué
El rediseño se conserva **no como arreglo de un fallo probado, sino porque es más
robusto**: el aviso pasa de EVENTO de un solo uso (`pop`) a **CONDICIÓN de estado**, así
que cualquier rerun lo repinta en vez de poder matarlo, y gana la salida por la **X**
(`on_dismiss`), que con `pop` no existía. Verificado en producción: el modal sale con su
título, el nombre de la obra y los dos botones; «Hacerlo ahora» lleva a `?s=prestart` y
lo cierra.
- Se descarta de **tres** formas: «Hacerlo ahora», «Ahora no» y la **X**. ⚠️ Sin lo de
  la X, un modal por condición reaparecería en cada pasada **para siempre**.
- Se re-arma al volver a fichar en esa obra, y se calla solo si el Pre-Start ya está.
- Guardián: 3 pasadas seguidas → se abre 3/3.
- ⚠️ **NO está demostrado que v374 estuviera roto.** Muy probablemente funcionaba.

### Y un literal a la vista desde v233
Los cronómetros del sidebar mostraban **`:material/schedule: Jornada`** en crudo: la
etiqueta va DENTRO de `components.html`, donde `:material/...:` no es un icono sino
sintaxis de markdown de Streamlit, que ahí no se interpreta. Viene de la migración de
iconos (v233) y llevaba así desde entonces. **Se vio mirando la pantalla, no leyendo el
código** — ninguna prueba lo iba a cazar porque el HTML era válido.

### Lo que la verificación en producción SÍ confirmó de v374
Selector sin preselección (v139) y «Fichar» deshabilitado hasta elegir · el desplegable
ofrece exactamente las 3 obras de esa persona · el fichaje entra y el flash sobrevive al
rerun (v365) · el sidebar cambia a los dos cronómetros + «Salir del proyecto» +
«Cerrar jornada y proyecto» · **el chip persistente del Pre-Start** · y la tabla de
avance del campo (v372) renderiza con sus columnas.

## LA DEMO SE MUDA A SU PROPIO LIBRO — migración hecha (21/08/2026)
Decisión del usuario entre tres opciones. Los 838 registros de la empresa simulada
salen del maestro a un libro propio, y el **maestro queda limpio para el primer cliente
real**. Bonus buscado: **ensayar la migración con datos que no importan**, que es
exactamente la operación que habrá que hacer bien cuando el dato sí importe.

**Libro de la demo**: `1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y`, renombrado de
«PRUEBA aislamiento — borrar» a **«COPEX — DEMO (cliente1)»**. ⚠️ Lo del nombre no es
manía: un libro que se llama «borrar» y guarda la demo es un accidente con fecha.

### El orden, que es lo único que importa
**copiar → verificar → enlazar → verificar → borrar → verificar.** Nunca al revés.
| Paso | Qué | Salvaguarda |
|---|---|---|
| 1 | Respaldo CSV a disco de las 26 hojas | 852 filas en `C:\Users\diego\respaldo_sheets\`. Los ZIP del deploy guardan el CÓDIGO, no los datos |
| 2 | Copiar las **22 hojas de inquilino** | `value_input_option="RAW"`, como escribe la app entera |
| 3 | Comparar **celda a celda** | **9.617 celdas idénticas** en 22 hojas |
| 4 | `Grupos.SheetID` → libro de la demo | el mecanismo de v359, ya probado |
| 5 | Comprobar el **enrutado** | inquilino→DEMO, global→MAESTRO, sin grupo→MAESTRO |
| 6 | Vaciar el maestro **desde A2** | puerta previa: la demo tiene los datos AHORA |
| 7 | Prueba decisiva | maestro a 0 filas y la app sigue dando 16 obras · $101.157,21 |

⚠️ **Hasta el paso 6, ninguna cifra probaba nada**: los dos libros tenían lo mismo, así
que «la app muestra 16 obras» era compatible con leer del maestro. Solo con el maestro
VACÍO esa cifra demuestra de dónde sale. Es el paso en vacío (trampa nº1) aplicado a una
migración: **si el test pasaría igual sin haber hecho el trabajo, no es un test**.

- Se quedan en el maestro las 4 hojas **globales** (`Login`, `Grupos`, `Rieles`,
  `Manuales`): son el registro de la app, y `Login` se lee ANTES de saber de qué grupo
  eres. Verificado: 13 cuentas siguen ahí y el login funciona.
- Las cabeceras se conservan (se limpia desde `A2`), así el maestro queda listo para el
  primer cliente sin que `get_sheet` tenga que recrear nada.

### Tres errores míos en la propia migración
1. ⚠️ **Escribí el respaldo DENTRO del repo.** `git status` lo delató (`?? respaldo_sheets/`)
   y el siguiente deploy lo habría empujado a GitHub **con los hashes de contraseña, los
   emails y los chat_id de Telegram**. **REGLA: una exportación de datos nunca va dentro
   del repo** — el script de deploy hace `git add` de todo.
2. ⚠️ **El verificador reventó con un 429** por pedir `src.worksheet(t)` en cada vuelta
   (refetchea los metadatos del libro **cada vez**): ~88 llamadas contra el techo de
   60/min. Es el problema que v339 resolvió DENTRO de la app, cometido en el script que
   venía a verificarla. Rehecho con `values_batch_get`: **2 llamadas**.
3. ⚠️ `values_batch_clear(params, body)` — pasarle la lista suelta la mete como `params`
   y muere dentro de `requests` con «too many values to unpack», que no dice nada. Va en
   el `body`. Falló limpio: el maestro quedó intacto (comprobado antes de reintentar,
   porque **un borrado a medias es peor que no haber empezado**).

### ⚠️ CONSECUENCIA VIVA: la fase 2 ya no es teórica
Medido justo después: el **propietario ve 0 proyectos** (sus vistas leen el maestro, que
ahora está vacío) mientras el admin de cliente1 ve sus 16. Las **9 funciones** que hay
que tocar cuando se aborde la fase 2:
`admin_digest.owner_digest` · `auth_ui._owner_usuarios` · `alerts._admins_and_owners` ·
`credentials.notify_expiring` · y las cinco que dan «todos los proyectos» al propietario:
`plan_ui.selector_proyecto` · `prestart_ui._projects_for` · `timeclock_ui._proyectos_para`
· `tool_save_ui._proyectos_de` · `survey_ui.render_survey_tab`.
Que la limitación salga AHORA, con datos simulados, es justo lo que se buscaba.

## ⚠️ FUGA DE DATOS ENTRE INQUILINOS EN LA CACHÉ (v378)
Salió al ir a hacer la fase 2: la capa que había que tocar tenía un agujero peor que
el problema que veníamos a resolver.

```python
@st.cache_data(ttl=120)          # ← la clave es SOLO el título de la hoja
def _records():
    return hojas.registros(SHEET, HEADERS) or []   # ← el libro sale de la SESIÓN
```
`st.cache_data` se comparte **por PROCESO**, no por sesión. El primero que lee deja su
resultado memoizado y **el siguiente —de otro cliente— recibe datos que no son suyos**.
Demostrado con los dos libros reales, en los dos sentidos: el propietario leyendo el
maestro vacío dejaba al admin de cliente1 con 0 proyectos, y al revés el propietario
recibía las 16 obras del cliente.

⚠️ **El cerrojo de v351 no lo cubre**: aquel comprueba el grupo de un objeto que ya
trajiste; aquí **la lista entera es del inquilino equivocado**. `hojas._lote` y
`timeclock._libro` sí van por libro (v359 lo hizo a propósito) — el agujero estaba en
la caché de ENCIMA, que memoiza el resultado ya derivado.

**Alcance medido**: 22 lectores cacheados; 4 leen hojas globales (sin fuga posible) y
**18 leen datos de inquilino** en 16 módulos.

**El arreglo**, uniforme y sin tocar ninguno de los ~40 call-sites: la función cacheada
pasa a `X_cached(libro, …)` y se deja un envoltorio `X()` con el nombre de siempre que
resuelve el libro y delega.

### ⚠️ TRAMPA 1: el guión bajo hizo el arreglo INERTE
Llamé al parámetro **`_libro`**. `st.cache_data` trata los argumentos cuyo nombre
empieza por guión bajo como **no hashables y los deja FUERA de la clave** — es su
convención para pasar conexiones. Resultado: la firma decía lo correcto, el guardián de
AST daba ✓… y la fuga seguía **idéntica**.
Solo lo delató **instrumentar quién se ejecutaba de verdad**: al trazar las llamadas
reales a `hojas.registros`, la segunda lectura no aparecía — la caché la había servido.
**REGLA: un parámetro que existe para separar la clave de caché NO puede empezar por
`_`.** El guardián lo comprueba desde ahora.

### ⚠️ TRAMPA 2: importar un módulo NO ejecuta sus funciones
`compileall` ✓, los 79 módulos importan ✓, el guardián de AST ✓ … y **tres envoltorios
tenían un `NameError` dentro**: `roster` usaba `TRABAJOS_SHEET` (la constante es
`TRAB_SHEET`), `invoices` y `payroll` usaban `SHEET` (son `FACTURAS_SHEET` y
`NOMINAS_SHEET`). Habrían reventado la primera vez que alguien abriera el tablero, las
facturas o las nóminas. **Lo único que lo caza es LLAMARLOS**: smoke test que ejecuta
los 18 envoltorios y las 15 invalidaciones.

### ⚠️ TRAMPA 3: la de v344, otra vez
Al renombrar la función cacheada, los `X.clear()` de `_invalidate` quedan apuntando al
**envoltorio** → `AttributeError` → el `except` se lo traga → **la caché deja de
limpiarse y nadie se entera**. El guardián lo cazó en 2 sitios (`projects`, `roster`),
donde mi regex había arreglado el primer elemento de la tupla y dejado el segundo.

## FASE 2: el propietario vuelve a ver a todos sus clientes (v379)
Tras la mudanza de v377 el propietario veía **0 proyectos**: sus vistas leen el maestro
y los clientes viven en sus libros. Esta es la fase 2 que v359 dejó aplazada.

### El ámbito de grupo, en vez de hilar un parámetro por 40 funciones
`owner_digest` recorre grupos llamando a `group_digest(g)`, y por dentro eso lee
proyectos, alarmas, gastos y credenciales — todo con lectores que resuelven el libro
**desde la sesión**, y la del propietario no tiene grupo. Hilar un `grupo` por todas
esas firmas habría sido enorme.
**`tenant.como_grupo(g)`**: dentro del `with`, `sheet_id_para` consulta el grupo activo
antes que la sesión, así que TODA lectura cae en el libro de `g`. Un cambio, en el
único punto donde se decide el libro.
- ⚠️ Vive en `st.session_state`, **no** en un global del módulo: los globales se
  comparten por proceso y ahí un «grupo activo» se filtraría a otra sesión — la clase
  de fallo que acababa de cerrar v378.
- Reentrante y anidable; el guardián comprueba que al salir restaura lo anterior.
- Aplicado en 4 sitios: `owner_digest`, la ficha de usuario del propietario, el
  detalle de proyecto y el aviso de credenciales del login.
- ⚠️ En `_detalle_proyecto` se **re-entra una vez** bajo el ámbito en vez de envolver
  300 líneas en un `with`: reindentar un bloque así es lo que rompió v120 y v148. La
  propia condición corta la recursión.
- `auth.grupos_por_libro()` da UN grupo por LIBRO distinto. ⚠️ Si tres grupos comparten
  el maestro, leerlo tres veces **triplicaría las filas**: agrupar por libro no es una
  optimización, es lo que evita duplicar el consolidado. El guardián lo comprueba.

### ⚠️ EL ARGUMENTO NO PUEDE SER UNA LLAVE
Mi primera versión hacía que un `grupo` explícito seleccionara el libro **siempre**.
Con eso, un admin de otra empresa que pasara `grupo="cliente1"` **leía el libro de
cliente1**: convertí «manda la sesión» en «manda el argumento», debilitando justo lo
que v378 venía a cerrar. Ahora el grupo explícito solo elige libro **si quien pregunta
puede ver ese grupo** (`tenant.puede_ver`): propietario, o es el suyo.

### ⚠️ Y el test que había dejado de servir
El test de fuga de v378 comparaba «propietario» contra «admin de cliente1» y daba por
fuga que el propietario viera 16 obras. Con la fase 2 eso pasó a ser **lo correcto**,
así que el test ya no distinguía una fuga de la funcionalidad nueva — y falló en falso.
Reescrito para comparar **dos administradores de grupos distintos**, que es lo que el
aislamiento tiene que garantizar. **Solo la versión reescrita encontró la fuga real de
arriba.** REGLA: cuando una funcionalidad cambia lo que es «correcto», el test que lo
medía hay que rehacerlo, no relajarlo — si no, se queda dando veredictos de otra época.

### ⚠️ La cartera se compone de VARIAS fuentes, y solo probé una (v380)
Verificando la fase 2 **en pantalla** con la sesión de propietario: los proyectos ya
salían (12 activos de 16), el resumen por grupo cuadraba al dígito con lo previsto…
y **todas las tarjetas mostraban `0h`**. El demo tiene 484 fichajes.

Mis tests medían `list_projects`. Pero una tarjeta de la cartera se arma con **cuatro
fuentes distintas**, y cada una tiene su propio camino al libro:
| Dato | De dónde sale | Estado tras v379 |
|---|---|---|
| proyectos | `list_projects` | ✓ arreglado |
| **horas** | `project_hours_bulk` → hoja del fichaje | ✗ leía el maestro → **0 h** |
| **alarmas** | `open_counts_all()` — **no recibe grupo** | ✗ leía el maestro → **0** |
| costos / retrasos | `group_expenses`, `gaps_by_group` | ✓ ya cuadraban |

Los dos huecos se cierran con el mismo patrón (`_fichajes_visibles`, `_alarmas_visibles`).
**REGLA: cuando una pantalla se compone de varias fuentes, hay que comparar TODAS
contra lo que ve quien sí las tiene bien** — arreglar la principal y dar la pantalla
por buena deja ceros que parecen datos. Guardián nuevo: mide horas, alarmas, gastos y
retrasos del propietario contra los del admin del mismo grupo, y falla si difieren.

### ⚠️ Y v380 arregló la función EQUIVOCADA (v381)
Con la pantalla delante otra vez: las alarmas ya salían… y las **12 tarjetas seguían
marcando `0h`**. El arreglo de v380 fue a `project_hours_bulk` **dando por hecho** que
era la que alimentaba la cartera. No lo es: `render_owner_projects` llama a
**`project_hours()` una vez por obra**. El test daba ✓ sobre una función que esa
pantalla no usa.

**REGLA: antes de arreglar lo que pinta una pantalla, MIRAR qué función llama.** El
guardián de v381 lo comprueba primero (`project_hours_bulk: False · project_hours():
True`) y solo después mide — así no puede volver a validar el camino que no es.

De paso salió otro cero peligroso: **`datos_asociados`** —el recuento que se enseña
ANTES de borrar un proyecto— le daba **0 en todo** al propietario. «No cuelga nada»
cuando cuelgan 25 fichajes, 3 gastos y 11 actividades es el peor sitio imaginable para
un cero falso. Ahora se lee bajo el ámbito del grupo del proyecto.

## Firma DIBUJADA en el Pre-Start + el aviso que no se va (v383)
Tres peticiones del usuario. Decisiones suyas: **firma por asistente** (como el formato
en papel, donde cada uno firma su línea) y **solo en el PDF**.

### La firma
`streamlit-drawable-canvas` (dependencia nueva). ⚠️ Es un componente de **2023** y aquí
corre Streamlit 1.57 — con el historial de v66 (segfaults por ruedas bleeding-edge) eso
se prueba ANTES de prometerlo: importa, renderiza, **captura el trazo** (el PNG pasa de
543 B en blanco a 5.245 B firmado) y **reportlab lo acepta**.
- **Import PEREZOSO**: si el componente falta o falla, el Pre-Start NO se cae — se piden
  las iniciales tecleadas, como hasta v382. Una charla de seguridad no puede quedarse
  sin registrar porque una dependencia de terceros no cargue.
- El bloque de asistentes deja de ser un `st.data_editor` (una tabla no puede llevar un
  lienzo dentro): pasa a una lista de nombre + recuadro de firma, con botón de añadir.
- **Quien está en la lista, firma**: el botón de generar se bloquea y dice de quién falta
  la firma. Mismo criterio que v158 («no se puede firmar sin leer»): si se admiten
  asistentes sin firma, la firma deja de significar nada.

### ⚠️ Tres trampas, y las tres habrían pasado desapercibidas
1. **Detectar la firma por el canal ALFA no sirve.** Con fondo opaco, un lienzo VACÍO da
   alfa=255 en los 58.800 píxeles → **todo el mundo constaría como firmado**. Se compara
   contra el color de fondo. Lo delató instrumentar la mini-app, no leer el código.
2. **La firma no puede llegar a la hoja.** `json.dumps` **no serializa `bytes`**, así que
   sin filtrar, `submit` habría fallado ENTERO; y aunque serializara, seis firmas en
   base64 rondan los 40.000 caracteres contra un tope de celda de 50.000. La hoja guarda
   nombre, iniciales y un `firmado: true`; la imagen va al PDF, que es el documento que
   vale y ya se archiva en Drive.
3. **La columna de firma medía el 9% del ancho** —dimensionada para dos iniciales— y el
   propio encabezado se partía como «Signatur / e». Reequilibrada a 16,3%. Lo cazó
   **extraer el texto del PDF generado**; en el código no se ve.
- Y un `logger` inexistente en `prestart_pdf` dentro del `except` de la firma: el
  NameError latente de v370 otra vez. El guardián **ejercita esa rama** (firma corrupta).

### El aviso de arriba
Banda en la barra superior, visible desde CUALQUIER sección y que **no se puede
descartar**: solo desaparece cuando el Pre-Start está hecho. El chip del sidebar (v374)
se pierde de vista —el sidebar se pliega en el móvil— y el modal se cierra y no vuelve.
0 llamadas nuevas: `open_sessions` y `hecho_hoy` salen de registros ya cacheados.

## ⚠️ LA SUITE ENTERA: 13 rojos que nadie veía (v384-v385)
El usuario preguntó qué quedaba pendiente. Al auditar en serio salió que **yo venía
corriendo un subconjunto elegido por mí**: cuando reportaba «13 guardianes en verde»,
la suite completa tenía **48** y **13 fallaban**. Dos de esos rojos los había
introducido ese mismo día.

**REGLA: se corre la suite ENTERA, no la lista que uno recuerda.** Un subconjunto
curado da la sensación de cobertura sin la cobertura, y los rojos se acumulan fuera
del campo de visión — que es exactamente el modo de fallo que los guardianes existen
para evitar.

### Los 3 fallos REALES
| Guardián | Qué era | ¿Del día? |
|---|---|---|
| v333 | La banda del Pre-Start con `font-size:15px`, fuera de la escala de 9 pasos | sí, mío |
| v322 | `import pandas` muerto en `prestart_ui` al sustituir la tabla de asistentes por los lienzos | sí, mío |
| v323 | **5 `except: pass` se tragaban el apunte de auditoría** sin dejar rastro: `registrar` logea lo suyo, pero si revienta `diff` o el import, el histórico se queda con un hueco que nadie puede explicar | no: venían de v342/v352 |

### Los 9 CADUCADOS — actualizados, no relajados
Todos fallaban porque el código cambió **a propósito** y su afirmación envejeció:
- **v296 · v297 · v298** exigían que existieran la nav vieja, `_SHELL_NUEVA` y
  `render_owner_panel` — **borrados en v299**. Fallaban *por haber ganado*. Invertidos
  a «sigue borrado», que es lo que hay que proteger a partir de ahora (regla v140/v146).
- **v295 · v301**: el CSS de la cabecera del tablero, reescrito en v301 y normalizado
  por la escala de v333.
- **v306**: exigía que `Tipo` fuera la ÚLTIMA columna; v360 y v373 añadieron dos
  después — también al final, que es lo que la regla protege de verdad.
- **v309**: su fixture de gastos no llevaba `Grupo`, y **v310 cambió la definición** de
  las compras del P&L (de «los proyectos del grupo» a «la columna Grupo»); además
  buscaba enlaces literales que **v317 convirtió en datos**.
- **v313**: cuatro patrones viejos — v325 partió `sin_tarifa` en accionable y de-baja,
  el KPI pasó de `st.metric` a `_kpi_card`, el texto dice «obra(s)» y no «proyecto(s)»,
  y el `['e']` es el `except … as e` (falso positivo conocido desde v145).
- **v317**: exigía 3 herramientas; **v318 hizo la composición la cuarta**, a petición
  del usuario tras verla fija.
- **v321**: su mock esperaba 1.750 de ingreso, pero **v361 movió el cálculo** a
  `project_revenue`, que consulta cotización y ganancias. La regla que defiende se
  comprueba ahora contra **datos reales** (`check_v321_real.py`), que es más fuerte.

⚠️ En cada uno quedó escrito **qué cambió y por qué**: dentro de seis meses, un
guardián ablandado y uno actualizado se parecen mucho si nadie dejó la razón.

### ⚠️ Y un FALSO POSITIVO que casi rompe código sano
v323 acusaba a `catalogo` y `orders` de sacar el `_next_id` de la caché —lo que
repetiría un ID, y **el ID es la identidad**—. Los dos leen FRESCO y su docstring lo
dice: el guardián buscaba la subcadena `_records` y **`get_all_records` la contiene**.
Es la trampa nº2 (*grep ≠ uso*) dentro de un guardián. Corregido a AST por nombre de
llamada. **Antes de «arreglar» lo que un chequeo denuncia, mirar el código acusado.**

## VER EL DÍA de una persona: la celda no cabe, la línea de tiempo sí (v387-v389)
Petición del usuario: *«cuando alguien tiene más de una asignación por día, al dar clic
en ese día quiero ver solo ese día, cómo lo tiene organizado, de forma gráfica»*.

### ⚠️ Medir los datos ANTES de diseñar cambió la propuesta
La idea obvia era una línea de tiempo. Medido primero sobre la hoja real:
| | |
|---|---|
| días-persona con asignación | 34 |
| …con **más de una** | **1** |
| asignaciones **con** franja horaria | **3** |
| asignaciones **sin** hora | **32** |
Y el único caso real —`campo1`, martes, `PRJ-0005` y `PRJ-0006`— tiene las dos a
**07:00–15:30**, o sea SOLAPADAS. Con eso, un eje horario puro habría dibujado un
bloque encima de otro y el resto del eje vacío. El diseño se cambió: **carriles
paralelos** (el solape se VE) y las asignaciones sin hora como banda «todo el día»,
sin fingir una franja que nadie puso.

### Cómo se abre (decisión del usuario, entre tres opciones dibujadas)
La celda ya es un `st.popover` de edición (v217) y no se le pueden dar dos
significados al mismo clic. El popover gana **«Ver el día»** y el detalle se pinta
**debajo del tablero, a ancho completo** — a 300 px de popover, los nombres se cortan
y las horas no caben (medido antes de elegir).

### ⚠️ El resumen MENTÍA, y era mi propio fallo
Con las dos obras solapadas de 8,5 h, la cabecera decía **«17.0 h»** de una persona
que trabajó 8,5: el mismo rato contado dos veces — exactamente lo que el aviso de dos
líneas más abajo denuncia. `_ocupado()` calcula la **UNIÓN** de las franjas; la suma
solo aparece junto al aviso, como síntoma: *«Suman 17.0 h asignadas sobre 8.5 h de
día»*. Misma familia que el «sin asignar» de v320.

### Otros dos, cazados por el guardián y por la pantalla
- **Un turno que acaba cerca de medianoche** dejaba el eje por debajo del mínimo de
  4 h que la propia función declara: `hi` está topado en las 24:00, así que si no cabe
  hacia arriba hay que **bajar `lo`**.
- ⚠️ **El popover NO se cierra con el `st.rerun()`** (medido en producción: el estado
  de apertura vive en el frontend). Yo había escrito en el código que sí. Queda abierto
  sobre el tablero hasta que se toque fuera. No se fuerza: la única vía sería remontarlo
  cambiándole la `key`, y eso arrastra el CSS del color de cada celda a una key variable.

### Verificación
`_carriles` probado con el caso real, con día partido, con solape parcial de tres y con
franja mal tecleada; el eje comprobado en 6 rangos (madrugada, hasta las 24:00, 30 min);
y **ejecutado** en 6 escenarios (importar no ejecuta, v378). En el DOM: bloques a
9.1%/77.3% en carriles separados, ticks sin recortar, 0 desbordes. En producción con el
día doble real: «2 asignaciones · 8.5 h del día ocupadas» y los dos bloques en y=990 y
y=1023, coherente con el KPI «CHOQUES DE TURNO: 1» del propio panel.

## Vista por DÍA de la cuadrilla + sábado y domingo por semana (v390-v395)
Dos peticiones del usuario: ver el panel **por día** además de por semana, y poder
**añadir un día** cuando toca trabajar el fin de semana.

### La vista Día: lo único que ninguna pantalla daba
Ya había tres vistas de un día (Cumplimiento, Ruta del día, Disponibilidad) y ninguna
responde *a qué hora* está cada uno. La vista Día es la cuadrilla entera sobre un eje
de horas: una fila por persona, sus bloques a escala, los libres marcados. Reutiliza el
motor de v387 (`_eje_de`, `_carriles`, `_ticks_html` compartidos, para no tener **dos
aritméticas del eje** que mantener — la lección de los cinco `_num` de v323).
- Quien se pisa a sí mismo sale en **sub-carriles al 50%** dentro de su propia fila, así
  la rejilla sigue siendo una fila por persona.
- ⚠️ Con 32 de 35 asignaciones sin hora, hoy se llena de bandas «todo el día». Se dice
  en la propia pantalla; se afinará según se planifique con horario.
- ⚠️ **Fallo de contraste visto mirando, no midiendo**: el texto blanco sobre la trama
  de rayas era ilegible. Ahora va en una píldora de color sólido sobre la trama.

### El día extra, SIN configuración nueva (decisión del usuario)
`+ Sáb` / `+ Dom` añaden la columna **a la semana que se está viendo**, y la columna
**reaparece sola si hay algo asignado** (`dias_con_datos`). Así no hay ajuste que
mantener ni migración, y **el dato nunca queda escondido** — por eso mismo, quitar una
columna con trabajo dentro está bloqueado y dice de quién es (regla v340).
- ⚠️ `DIAS_TODOS` va en el orden de `weekday()`, así que `fecha_de_dia` sigue siendo
  `lunes + índice` y **ninguna fecha existente se mueve** (lo primero que comprueba el
  guardián: si eso se rompe, se desplaza toda la planificación histórica).
- Se movió con ello todo lo que asumía «la semana es Lun–Vie»: rango del encabezado,
  atajo «toda la semana», radar de choques y certificados (ahora escanea los 7 días),
  agenda de Home, Ruta del día, Cumplimiento, Asignar y el board del campo — que ve el
  fin de semana **solo si hay algo planificado**, que es justo cuando le importa.
- ⚠️ Los cuatro cortes de `weekday() > 4` ya no cortan por ser sábado: cortan si **no
  hay nada** ese día. Cortar por el día escondería lo que alguien acaba de planificar.

### Ejercitado contra la hoja REAL (v390)
Nadie había guardado nunca una asignación en sábado. Método de v344 (foto en solo
lectura → ejercitar en una semana vacía → verificar leyendo → devolver todo → segunda
foto): guardar en sábado, leerlo con su franja y su nota, que la columna se abra sola,
que el campo lo vea ese día (antes devolvía []), y que **`copiar_semana` lo arrastre**
—que era una afirmación mía sin probar—. Hoja idéntica: 14 filas antes y después.

### v393 · Auto-poblar respeta el fin de semana, pero no lo impone
Al asignar personal se rellena el planificador entre las fechas del proyecto. Rellenar
sáb/dom siempre convertiría la excepción en norma; no rellenarlo nunca obliga a añadir
a mano a cada persona en una semana que la cuadrilla SÍ trabaja. Regla: se rellena el
día extra **solo si en esa semana ya hay alguien trabajándolo**. La condición sale del
DATO, no de una preferencia que haya que mantener.

### v391-v394 · La barra del Panel, medida en vez de repartida a ojo
Con **tres** vistas el segmentado dejó de caber: a 780 px (media pantalla) se partía en
vertical y «Disponibilidad» salía cortada. Tres intentos, y solo el tercero salió de
MEDIR la fila en producción (406 px, con 48 comidos por el `gap`):
| Recorte | Ahorro |
|---|---|
| `gap="xxsmall"` (16 → 4 px) | 36 px |
| rango **sin año** (`rango_label(corto=True)`) | 75 px |
| menos padding, **acotado a este** segmentado | 36 px |
Resultado medido en producción: barra de **70 → 40 px**, las tres vistas en una fila,
rango en una línea, 0 recortes. ⚠️ El rango largo se estaba partiendo en **3 líneas**
dentro de 56 px — eso era lo que hinchaba la fila, y no se veía hasta medir su altura.

### v393 · ⚠️ La firma del Pre-Start no cabía en un móvil
`st_canvas` nace con `width=600` y no acepta `use_container_width`: en un viewport de
375 px el lienzo salía de **600 dentro de un hueco de 343**, así que **la mitad derecha
quedaba fuera de pantalla y ahí no se podía firmar**. Ahora son 300 px (medido: cabe
entero, sin scroll). El Pre-Start se llena EN OBRA, así que manda el móvil aunque en
escritorio el recuadro se vea más pequeño.
⚠️ **Sigue sin demostrarse** que un DEDO trace una firma completa: mis eventos
sintéticos dejan tinta pero no completan el trazo, y de eso no se concluye que falle
(regla v375). Necesita un teléfono real.

### v395 · Las alarmas que no le llegan a nadie
`report_problem` escribe la alarma **y notifica**. Un destinatario sin email ni Telegram
la recibe… dentro de la app: solo la ve si entra a mirar. Con el check en NO abriendo
alarma (v373) eso pasó a importar. Medido en la hoja real: de los **5** destinatarios de
una alarma de `cliente1`, a **3 no les llega** (`dacox`, `Arcantox`, `admin1`) — aunque
siempre llega a 2, así que ninguna se pierde del todo.
- El dato entra en `admin_digest.group_digest` (`avisos_sin_canal`) y se avisa **donde
  se arregla**: Planificación · Usuarios, encima de la tabla donde se carga el email.
- ⚠️ **Criterio distinto al del campo, a propósito**: al campo se le exigen los DOS
  canales (v79, requisito para usar la app); a un gestor le basta UNO. Mezclarlos sería
  el error de v325 («sin tarifa» eran dos cosas en el mismo aviso).
- ⚠️ **NO entra en `_PENDING_KEYS`**: la rejilla del resumen del día es de NUEVE
  indicadores fijos en 2 filas y su reparto tiene guardián (v305).
- 0 lecturas nuevas: sale de `list_users()`, ya cacheado.

### ⚠️ La regla v135 falló TRES veces en una sola tanda
`prestart.generate_prestart_pdf` (vive en `prestart_pdf`), `report_problem(pid, grupo,
tipo, …)` (no tiene `tipo`) y `CHECKS_S1` como lista de cadenas (son **tuplas
(clave, texto)**). Las tres se cazaron ejecutando, no leyendo. **Antes de escribir una
llamada nueva, mirar la firma y la FORMA del dato — no el nombre que parece lógico.**

### Y un error de manos
Sobrescribí `P1/.claude/launch.json` por leer la ruta equivocada antes de escribir
(`survey_app/.claude/`, que no existe). Restaurado desde git; los cambios locales sin
commitear que hubiera ahí se perdieron. **Leer el fichero que se va a escribir, no uno
parecido.**

## Facturar desde la cartera (v397-v398)
Petición del usuario: *«en la tabla de proyectos vamos a agregar una opción para que se puedan
generar los invoices de cada proyecto desde la tabla o ficha»*. Decisiones suyas: **botón en la
tarjeta** y las archivadas **con la casilla de siempre** (v149/v340/v369).
- **`invoices.pendiente_por_proyecto(grupo, incluir_archivados=True)`** — el mapa, en UN sitio.
  ⚠️ `finance.sin_facturar` DELEGA en él en vez de repetir el bucle: dos definiciones del mismo
  dinero es lo que produjo los fallos de v310, v321 y v361.
- **`_ir_a_facturar(pid, grupo)`** extraída para que el botón de la tarjeta y el de la ficha hagan
  EXACTAMENTE lo mismo (resolución del cliente por `ClienteID`, y sin preseleccionar un valor que
  no esté entre las opciones del selectbox — el fallo que v357/v358 ya habían pagado).
- Tarjeta: insignia con el importe + botón **Facturar** solo si `pendiente > 0` y el rol gestiona;
  sin pendiente, solo «Abrir →». Lista: columna **Sin facturar** como NÚMERO (ordenable), no texto.
- ⚠️ **v398: existir no es servir.** La columna se puso la décima de trece y, medido en producción
  con la tabla a ~520 px, **había que hacer scroll horizontal para encontrarla**. Se movió junto al
  nombre. Una columna que hay que buscar no cumple la función por la que se añadió.
- ⚠️ **Falsa alarma resuelta midiendo:** el botón «Facturar» aparecía DOS veces en el DOM. El
  segundo mide **0×0 en (0,0)** — es el nodo de medida que Streamlit añade a un botón con `help=`.
  Se pinta uno solo.

## El dinero tenía dos caras en la misma pantalla (v399)
Visto verificando v398: la celda pintaba **`$27883`** y la tarjeta de al lado **`$27,883`**. El pie
de esa misma tabla sale de `theme.dinero` (que sí agrupa), así que la contradicción estaba a dos
centímetros. Causa: `NumberColumn(format="$%.0f")` es printf, y `%f` no agrupa.
- **No era una columna, eran 39** en 7 módulos (`$%d`×20 · `$%.2f`×14 · `$%.0f`×5): Rentabilidad,
  Facturas, Nóminas, Inventario, Contactos, Catálogo, Cotizaciones y la cartera. Todas las TABLAS
  decían `$27883` mientras todos los KPI y pies decían `$27,883`. Arreglar solo una habría dejado
  esa columna como la única distinta.
- El printf de Streamlit **sí acepta `,`** (`"$%,d"`). ⚠️ Verificado, no leído: la documentación lo
  dice, pero lo que decide es lo que PINTA — mini-app + intercepción de `fillText` (trampa nº18).
- ⚠️ **`%d` no se cambió por `%.0f`**: uno trunca y el otro redondea (trampa nº20).
- ⚠️ **Las columnas EDITABLES se probaron tecleando** (Cotizaciones, Nóminas, Ganancia/h): el editor
  se siembra con el valor CRUDO (`1500`, no `$1,500.00`) y al escribir `3456.78` Python recibe
  `3456.78`. El separador no toca ni la edición ni el valor devuelto.
- Guardián `verif_v399.py`: por AST (no por texto — un formato en un comentario no es un uso), NINGUNA
  columna de dinero puede quedarse sin separador, y se comprueba que siguen conviviendo las que
  truncan y las que redondean. Probado contra el caso roto.

### RESUELTA en v405 — `use_container_width` → `width="stretch"`
200 sitios convertidos en 21 ficheros. **3 NO se tocaron**, y los tres a propósito: los
dos `st_folium` (su parámetro es del COMPONENTE — convertirlo rompe el mapa, que es el
arreglo de v307) y ⚠️ **un COMENTARIO** de `route_ui` que contiene el literal; un
reemplazo por texto lo habría reescrito y el comentario habría pasado a decir una
mentira sobre un parámetro que a propósito se conserva. Por eso la migración va por
**lista blanca de AST**: solo se toca lo que el árbol confirma como argumento real.
Medido antes de convertir: los 8 elementos implicados aceptan `width` (tipo `Width`,
que admite `"stretch"`). Guardián `verif_v405.py`: ningún elemento de Streamlit puede
volver a usarlo; los de terceros sí. Lo de abajo queda como el registro del problema.

### Deuda anotada (resuelta en v405): `use_container_width`
⚠️ **Corrección (v402):** escribí que era una retirada «sin versión anunciada» y es FALSO. El propio
runtime lo dice al arrancar: **«`use_container_width` will be removed after 2025-12-31»** — hay fecha,
y ya pasó. O sea que esto no es «algún día», está en tiempo de descuento y puede desaparecer en
cualquier versión que Streamlit publique. Lo vi en los logs de una mini-app, no leyendo la doc.

Streamlit 1.57 lo marca deprecado a favor de `width="stretch"` / `width="content"`.
La app lo usa en **200 sitios de 21 ficheros**. No se migró: es un cambio
que toca la maqueta de TODAS las pantallas por una retirada sin fecha, y no se puede verificar en
producción a bajo coste. ⚠️ Y tiene trampa: **`st_folium(..., use_container_width=True)`**
(`route_ui.py`, `home_ui.py`) es un parámetro DEL COMPONENTE, no de Streamlit — convertirlo lo rompe,
y es justo el arreglo de v307 que llenó el hueco blanco de la Ruta del día.

## Quien llega después también firma el Pre-Start (v403)
Duda del usuario: *«cuando alguien realiza el pre start y luego alguien llega y ficha en ese
proyecto, tiene que firmar también. ¿Esto está funcionando así?»*. **No lo estaba**, y el hueco
venía de una decisión propia de v374.
- `hecho_hoy` responde «¿hay que HACER la charla?» — por obra y día, correcto para el recordatorio.
  Pero el aviso colgaba SOLO de eso, así que en cuanto el facilitador emitía el Pre-Start, quien
  fichaba después **no recibía nada**: ni modal, ni chip, ni banda. Nunca se le pedía firmar y
  acababa trabajando en esa obra **sin constar en el documento de seguridad**.
- Y aunque hubiera querido, no podía: `prestart.py` solo tenía `submit`, sin forma de añadir un
  asistente a un Pre-Start ya emitido. La única salida era un SEGUNDO Pre-Start del mismo día y la
  misma obra — dos documentos para una charla, y nada lo impide.
- **`pendiente_de_firma(pid, grupo, persona)`** es la segunda pregunta: «¿tengo que firmarla YO?».
  Convive con `hecho_hoy`, no lo sustituye; confundirlas fue justo el fallo.
- **`firmar(ps_id, grupo, nombre, iniciales, firma_png, usuario)`** añade la firma.

### ⚠️ Por qué se ANEXA una hoja en vez de regenerar el PDF
Las firmas originales **no se guardan en ninguna parte**: la hoja guarda nombre, iniciales y un
`firmado: true`, y la imagen vive solo dentro del PDF ya emitido (v383, por el tope de 50.000
caracteres por celda). Así que regenerar el documento **borraría la firma de quien sí estuvo en la
charla**. Se compone `original + anexo` con `pypdf` (ya era dependencia), y cada firma tardía queda
con **su hora** y marcada `tarde: true`. Es además lo correcto de por sí: un documento de seguridad
firmado no se reescribe, se le añade una hoja — como circula la hoja en papel.

### Detalles que deciden
- ⚠️ **Orden de escrituras** (lección de v343): se sube el PDF nuevo → se actualiza la fila → y
  SOLO entonces se borra el viejo de Drive. Al revés, un fallo a mitad dejaría el Pre-Start sin
  documento; así, en el peor caso sobra un archivo, que se ve y se recupera. Verificado midiendo el
  orden real: `download → upload → add_document → delete`.
- ⚠️ **El nombre se compara normalizado** (sin acentos, sin dobles espacios, sin may/min) porque los
  asistentes se TECLEAN. Si aun así no casa, se pide firmar otra vez: ese es el fallo tolerable; el
  intolerable es no pedirlo nunca.
- ⚠️ **Al CAMPO se le corta el formulario** cuando solo le falta firmar: dejarle debajo el Pre-Start
  completo invitaría a emitir el segundo documento del día. Gestión sí sigue viéndolo, porque a
  veces hay una segunda charla de verdad (otro turno, otra cuadrilla).
- ⚠️ `io` **no estaba importado** en `prestart.py` y el `BytesIO` iba dentro de un `try/except`: el
  PDF se habría dejado de componer **en silencio**. Es el NameError latente de v370, cazado al releer.
- El aviso no desaparece, **cambia de motivo**: banda, chip y modal pasan de «Falta el Pre-Start» a
  «Fírmalo», con su propio `st.dialog` (el título va en el decorador, así que hacen falta dos).

## Barrido de las 24 pantallas del admin + lo que destapó (v408)
Se abrieron **las 24 pantallas del rol administrador** una a una, navegando por los
botones del sidebar dentro de la MISMA sesión (`st-key-navsec_*` / `navsub_*` con
`.click()`): la navegación por URL se descartó porque cada `location.replace` dentro del
iframe lo dejaba en blanco y cada recarga cuesta un arranque. Ninguna dio excepción ni
desborde de página.

### ⚠️ Un barrido a un viewport que no es el de diseño no prueba lo que parece
La primera vuelta corrió con el panel a **800×292**, que es lo que había. Sirve para «¿se
rompe en estrecho?» y **no dice nada del ancho de diseño**, que es donde vive el admin
(la interfaz del admin es para PC, decisión del usuario en v303). Es el error de v335,
donde medí a 780 px porque `preview_start` me había reseteado el viewport. Se repitió la
parte que depende del ancho —las que llevan tabla— a **1440×900**, midiendo el desborde
**DENTRO de cada tabla** (`scrollWidth` vs `clientWidth` del `.dvn-scroller`), no el de la
página: una tabla puede desbordar su caja sin que el documento se entere.

### El hallazgo: en `Proyectos · Lista` lo urgente estaba al otro lado del scroll
Contenido **1339 px** para **1054 visibles**. Moviendo el scroll y releyendo las
cabeceras (la rejilla VIRTUALIZA: en el DOM solo existen las columnas en vista, así que
el conjunto que aparece ES el visible), las tres que había que ir a buscar eran
**`Usuarios`, `Situación` y `Alertas`** — justo las tres señales de «esto necesita
atención». Y al desplazarte a verlas, **`ID` se salía por la izquierda**: mirabas qué
obra va mal sin saber cuál es, con el nombre pudiendo repetirse (v306).

### Lo que se probó y se DESCARTÓ, con el número delante
| Variante | Contenido | Visible | Oculto |
|---|---|---|---|
| como estaba | 1335 | 1064 | **271** |
| solo anchos, 13 columnas | 1164 | 1064 | **100** |
| anchos + quitar `Tipo` | 1064 | 1064 | **0**… y **9 textos cortados** |
La tercera «cabía» a costa de comerse 60 px del nombre de obra y 60 del cliente. Ver
trampas nº21 y nº22: sin medir `measureText` eso pasa por bueno.

### La cura, la de v398: no achicar, priorizar
`ID` · `Proyecto` (**`pinned`**) · `Sin facturar` · `Avance` · `Ritmo` · `Avisos` ·
`Estado` · `Equipo` · luego el contexto (`Cliente`, `Tipo`, `Inicio`, `Fin`, `Ppto`).
Medido tras el cambio: **10 de 13 columnas visibles de entrada** (antes las de atención
no estaban), **0 textos cortados**, y tras un scroll real de 255 px `ID` y `Proyecto`
**siguen en su sitio**. Los anchos salen de medir el texto real más largo de cada
columna, no de elegirlos a ojo.

### Y el aviso del Pre-Start que señalaba al vacío
El bloqueo de duplicado de v407 decía siempre *«fírmalo ARRIBA»*, pero colgaba de
`hecho_hoy` (¿hay charla?) mientras el bloque de firma cuelga de `pendiente_de_firma`
(¿me toca a mí?) — las dos preguntas que **v403 separó a propósito**, remezcladas en el
texto. A quien ya constaba se le señalaba un bloque que no se estaba pintando. Ahora el
texto se decide por `_pf`. ⚠️ Con una bandera **`_pf_ok`**: `_pf` también queda vacío si
la consulta FALLA, y ahí no se puede afirmar «ya constas» — es el fallo de v375 en la
otra dirección.

### ⚠️ CORRIGE a v334: la barra de versión NO garantiza que TODO el código sea nuevo
v334 dejó escrito que «si la barra dice v334, se está ejecutando v334». **Es demasiado
fuerte.** Tras desplegar v408 la barra decía **v408** y `Proyectos · Lista` seguía
pintando el orden de columnas de v407, con los mismos 285 px ocultos. Comprobado antes
de culpar a nadie: el commit subido SÍ lleva el cambio (`git show HEAD:…`) y esa tabla
la pinta una sola función (`cart_tbl` aparece solo en `_cartera_lista`, así que no es el
error de v381 de mirar la función equivocada). La explicación está en cómo se mide:
`_VERSION = _leer_version()` corre **al importar `home_ui`**, así que la barra prueba
que **`home_ui`** se re-importó — no que lo hayan hecho los otros 50 módulos. Streamlit
Cloud puede recargar unos y conservar otros en `sys.modules`.
→ **Para afirmar que un cambio está corriendo, hay que ver el CAMBIO, no la versión.**
La barra sirve para descartar («si dice la vieja, seguro que no»), no para confirmar.
Y hasta que el proceso reinicie de verdad, lo desplegado no es lo que se ejecuta.

### Verificación
Guardián `verif_v408.py` sobre el PRINCIPIO y no sobre la forma (v392): toda señal de
atención antes que todo contexto, `ID`/`Proyecto` pinned, y el texto «fírmalo arriba»
colgando de `_pf`. ⚠️ Su primera versión daba **FALLO con el código correcto**: contaba
también el `if _ya_hoy:` exterior, que es el PADRE del `if _pf:` — hay que mirar el `if`
**más interno** que envuelve el literal. Probado contra el código roto en 3 casos (los
caza). Suite entera: **58/58** (ver trampa nº23: 4 de los «rojos» eran de la consola).

## Rejilla en el Panel de planificación (v410)
Petición del usuario: *«ponle grid al panel de planificación para que sea más fácil la
visualización»*. El board eran celdas-popover **flotando sobre blanco**: con 9 personas
× 5-7 días, seguir una fila hasta el viernes o bajar por un día obligaba a ir contando
con el dedo. Ahora las filas llevan línea, los días llevan línea y la cabecera se ancla
con una más marcada.

### Cómo se implementó sin reindentar nada
La cabecera y las filas se envuelven en `st.container(key="roshead")` /
`st.container(key="rosgrid")`, y el CSS cuelga de esas clases. ⚠️ Los contenedores se
usan como **OBJETO** (`_head.columns(...)` / `_grid.columns(...)`), **no** con `with`:
así el bucle de filas no hay que reindentarlo, que es exactamente la clase de cambio que
rompió v120 y v148. Verificado en vivo que esa forma produce el MISMO DOM que el `with`.

### Lo que hubo que medir (y por qué)
Estructura real, medida antes de escribir una línea de CSS (v304/v332: un selector que
no casa **no da error**, la app se ve «casi bien» y nadie lo nota):
`.st-key-rosgrid` (**stVerticalBlock**) > **stLayoutWrapper** > **stHorizontalBlock**
(la fila) > **stColumn** (el día).
- ⚠️ **El borde inferior necesita `!important` y el derecho no.** Medido: sin él, la
  fila salía en `0px rgb(250,250,250)` — ganaba una regla de Streamlit. Que una de las
  dos reglas aplique no significa que apliquen las dos.
- ⚠️ **Lo de DENTRO de una celda no es rejilla.** Un popover **cerrado** ya lleva su
  `st.columns` (la franja horaria) en el DOM dentro de `.st-key-roscel_*`: sin excluirlo,
  el editor de la celda saldría cuadriculado. Se excluye por el contenedor de la celda y
  **no** con una cadena de hijos directos, porque el `stLayoutWrapper` intermedio es
  reciente y esa cadena se rompe en silencio si Streamlit mete otro nivel (fallo de v327).
  (El popover ABIERTO además se portalea fuera del contenedor, así que hay doble seguro.)
- El `st.columns(2)` de la franja horaria se queda como `st.columns` **a propósito**: va
  dentro de la celda y el CSS lo excluye.
- Las verticales se subieron de `#eef1f5` a `#dfe5ec`: al primer intento eran
  invisibles. ⚠️ Y para juzgarlo hubo que capturar a **escala 1:1** (viewport = tamaño de
  la captura) y en **tema claro**: el panel escalaba 1440→800 y se comía las líneas de
  1 px, y la mini-app arrancaba en tema oscuro, donde estos colores no dicen nada.

### Verificación
`verif_v410.py`: los contenedores existen con SU key, **todas** las columnas del tablero
cuelgan de `_head`/`_grid` (y las de dentro del popover se identifican y se excluyen del
chequeo), y el CSS trae sus reglas. ⚠️ Uno de sus chequeos daba **OK con la exclusión
BORRADA**, porque miraba dos subcadenas que existen por otros motivos
(`st-key-roscel_` está en el CSS de densidad y `border: none !important` en el de
`pnm_`); se cambió por el selector completo. **Lo delató probar el guardián contra el
código roto** — sin esa prueba habría quedado un chequeo que solo aprueba. Los 5 casos
rotos se cazan. Suite entera: **59/59**.

### Ofrecido y NO hecho (decisión del usuario)
Franjas alternas por fila (zebra) y resaltar la columna de HOY. Las dos ayudan a leer un
tablero largo, pero no se pidieron y la zebra compite con el color del trabajo, que es
la señal principal del board.

## Franjas alternas + columna de HOY en el Panel (v411)
Las dos las pidió el usuario tras ver la rejilla de v410, y las dos sirven a lo mismo:
**no perder el renglón** en un tablero de 8-20 personas × 5-7 días. La rejilla puso las
líneas; esto ancla la vista.

### La zebra va por KEY de fila, no por `nth-child`
Lo natural sería `.st-key-rosgrid > [data-testid="stLayoutWrapper"]:nth-child(even)`.
⚠️ **No se hace así**: ese wrapper es un nivel que Streamlit intercala y es reciente —
una regla atada a él se rompe **en silencio** si mañana mete otro (es el fallo de v327),
y una zebra que desaparece sola no da ningún error. Se usa un `st.container(key=
f"rosrow_{_wk}_{pi}")` por fila y se pinta por su key: el MISMO mecanismo que el módulo
ya emplea para el color de cada celda, que no depende de la estructura interna.

### «Hoy» solo si cae en la semana que se está viendo
`_hoy_idx` sale de comparar `R.fecha_de_dia(lunes, d)` con `clock.today(grupo)`. Si no
aparece, **no se resalta nada**: marcar una columna al navegar a otra semana sería peor
que no marcar, porque mentiría. Se tiñe la columna en el cuerpo y en la cabecera con
`nth-child(i+2)` — la 1ª columna es «Persona» —, y ⚠️ eso es fiable porque se midió en
producción que los hijos de una fila son **todos `stColumn`**, sin divs de separación.

### ⚠️ La celda vacía tenía que dejar de tener fondo
Con su `#f8fafc` propio tapaba la zebra y la franja de hoy **justo en las celdas
vacías**, que son la mayoría del tablero — o sea, en el único sitio donde esas dos
señales tienen espacio para verse. Pasa a `transparent`, conservando su borde punteado.

### ⚠️ «hoy» va en una segunda línea, y eso salió de medir
A 1440 la columna deja 136 px útiles y «Mié 26/08 · hoy» mide 85: cabría. Pero con la
ventana estrecha la columna baja a **55 px**, donde ni la fecha sola (53) va holgada. En
una segunda línea de 11 px no compite por ancho a ningún tamaño.
⚠️ La primera medición la tomé con el viewport restaurado a «desktop» y concluí que NO
cabía; repetida al ancho de diseño, cabía de sobra. Es el error de v335 otra vez —
**medir al ancho equivocado da una decisión equivocada**, en las dos direcciones.

### Dos guardianes que caducaron por este cambio (actualizados, no relajados)
- **v410** exigía que las columnas colgaran literalmente de `_head`/`_grid`; ahora las
  filas cuelgan de `_row`. Lo que la regla protege no es el nombre de la variable, sino
  que **ninguna columna cuelgue de `st` directamente** — si lo hiciera, caería fuera de
  los contenedores keyed y se irían rejilla, zebra y columna de hoy sin fallar nada.
- **v301** exigía que el literal `style='{_CAB}'` saliera **2 veces**; con la variante de
  hoy sale una. Lo que protege es que «Persona» y los días compartan el mismo estilo
  base (antes Persona iba a la izquierda y los días centrados, y la fila no cuadraba),
  y eso se comprueba ahora directamente.

### Verificación
`verif_v411.py`, probado contra el código roto en 4 casos (quitar el contenedor por
fila, marcar hoy sin comprobar la semana, devolverle el fondo a la celda vacía, colgar
la zebra del wrapper): los caza los 4. ⚠️ Uno de sus chequeos daba **FALLO con el código
correcto**: miraba `"stLayoutWrapper" not in ...` y ese nombre aparece en un **comentario
CSS dentro de la cadena de estilos**, que `tokenize` no quita porque para Python es parte
de un string. Es la trampa nº2 (grep ≠ uso) en su variante más escurridiza. Suite entera:
**60/60**.

## La celda del Panel deja de estirar su fila (v412)
Salió de mirar el tablero tras v411: una fila triplicaba a las demás. **Medido a 1440**
—el ancho donde vive el admin— antes de tocar nada:
```
filas de 36 a 116 px · tablero 546 px
peor fila = celda de 53 px (2 líneas) + NOTA de 61 px
```
⚠️ La primera medición la tomé al ancho del panel (~780) y daba **36–421 px y 1785 de
tablero**: un problema 7,5× peor que el real. Habría dimensionado el arreglo para un
caso que a la medida de diseño no existe. **Tercera vez en el día** que medir al ancho
equivocado cambia la conclusión (v335).

### El culpable no era la celda: era la nota
61 px la nota contra 53 la celda — **ocupaba más que el trabajo que anota**. Pasa a UNA
línea con elipsis y el texto completo en el `title` nativo: se acota lo que OCUPA, no lo
que se puede saber (y sigue entero en el editor de la celda). El label de la celda se
topa a 2 líneas.
```
antes:  108 · 144 · 38 px   (total 290)
ahora:   63 ·  63 · 38 px   (total 164, −43%)
```

### ⚠️ El clamp NO se sostiene solo
`-webkit-line-clamp` necesita las TRES propiedades (`display:-webkit-box`, `box-orient`,
`overflow`) — con una sola no recorta y no da ningún error. Y aun con las tres, el
navegador **blockifica** el `display` a `flow-root` porque el `<p>` vive dentro de un
contenedor flex: medido, la única regla que toca `display` es la nuestra y el computed
sale `flow-root`. En Chrome el clamp sigue recortando, pero la altura del tablero no
puede depender de un comportamiento que no controlamos → **`max-height` como respaldo**
(2 líneas × 1.2 × 12px = 28.8). Cinta y tirantes.

### ⚠️ Lo que había que descartar antes de desplegar
El selector `[class*="st-key-roscel_"] button p` **también alcanzaría a los botones del
editor** de la celda, y un `max-height` ahí les cortaría el texto. Verificado en vivo:
el popover ABIERTO se portalea FUERA de `.st-key-roscel_`, así que su `max-height` sale
`none` y su texto no se corta. El editor queda intacto.

### ⚠️ Y el `title` es un atributo, no solo texto
`_esc` escapa `&`, `<` y `>` pero **no las comillas**. Una nota con una comilla no solo
rompería el atributo: permitiría inyectar otros (`" onmouseover="…`). Se escapa también
la comilla, y el guardián lo comprueba **leyéndolo del código**.

### Verificación
`verif_v412.py`, probado contra el código roto en 4 casos: los caza los 4 — pero solo
tras arreglarlo. ⚠️ Su chequeo del escape **reproducía el `.replace` en el propio test**
en vez de leerlo del código, así que seguía en verde con el escape BORRADO: un chequeo
que pasa en vacío respecto a lo que dice auditar. Ahora comprueba por AST que la
expresión del `title` lleva el reemplazo. Suite entera: **61/61**.

## Homónimos en Planificación: dos personas, dos filas idénticas (v413)
Salió de una pregunta del usuario —«¿ya está todo cerrado?»— y de mirar el tablero en vez
de responder que sí. En el Panel había **dos filas «Mei Chen»**, dos personas distintas
que se veían EXACTAMENTE iguales: al asignar la obra no había forma de saber a cuál se le
estaba poniendo, en la pantalla cuyo único propósito es repartir el trabajo.

⚠️ **`auth.etiqueta_usuarios` existía desde v319 y solo la usaba Nóminas.** Su propio
docstring dice que el nombre PUEDE repetirse y que ya había mordido en Horas (v151). La
Planificación seguía pintando `Nombre or Usuario` en sus **8 vistas**. Sexta aparición del
patrón (v151 · v306 · v319 · v348): la regla se escribe una vez y no se lleva a las
pantallas nuevas.

### Hallazgo de propina: no era solo cosmético
En `_asignacion_inteligente` el nombre es **clave de un diccionario de opciones**
(`_opts = {f"{estado} {nom}": usr}`). Con dos homónimos del mismo estado la clave
**colisiona y una persona queda IMPOSIBLE de elegir**, en silencio — el fallo de v147 y
v150. El desempate no lo maquilla: lo arregla.

### Lo que NO había que tocar (y se vio auditando ANTES de editar)
- ⚠️ **`_ficha_rapida`** arma un deep-link con `gp_fichasel = f"{nom} ({usuario})"`. Con
  la etiqueta quedaría «Mei Chen (mchen) (mchen)» y el parseo del destino se rompería.
  Conserva el nombre CRUDO y pinta con una variable aparte. Es exactamente el fallo de
  v308: cambiar lo que se MUESTRA y romper lo que se GUARDA.
- ⚠️ El `nom` de **`_catalogo`** no es una persona: es el nombre de un TRABAJO
  (`R.add_trabajo(grupo, num, nom, …)`). Un reemplazo por patrón lo habría arrastrado.
Los dos se auditaron listando, por AST, **cada lectura de `nom` función por función**
antes de cambiar una línea.

### `_etq(staff, grupo)`
Delega en `auth.etiqueta_usuarios` (una sola definición de la regla) y ⚠️ **desempata
sobre TODO el grupo, no sobre la lista visible**: si se hiciera sobre `staff`, la misma
persona sería «Mei Chen» en una pantalla donde está sola y «Mei Chen (mchen)» en otra —
y una identidad que cambia de nombre según la pantalla no es una identidad. `list_users`
está cacheada (v92) → 0 lecturas nuevas; si falla, degrada a lo visible.

### Verificación
`verif_v413.py`: las 7 vistas de personas desempatan, `_ficha_rapida` conserva el crudo,
`_catalogo` queda fuera, y el ámbito es el grupo. Probado contra el código roto en 4 casos
(los caza). ⚠️ Uno de sus chequeos daba **FALLO con el código correcto**: buscaba el
literal `"{nom} ({usuario})"` y un f-string se descompone en trozos (`" ("`, `")"`) —
hubo que mirar el árbol, no el texto. Tercera vez en el día. Suite: **62/62**.

## El nombre de obra deja de ir al filo (v414)
Pendiente que quedó de v408: la columna `Proyecto` medía **248 px** (232 útiles) y el
nombre más largo del grupo («Stockland Wetherill Park — Instalación») ocupa **224**. Ocho
píxeles de margen: un nombre 2-3 caracteres más largo se cortaba.

### ⚠️ Y el corte es SILENCIOSO — comprobado, no supuesto
Antes de decidir el ancho había que responder algo que cambia la respuesta: ¿glide dibuja
«…» al no caber? Si la pusiera, el corte se notaría y el problema sería menor. Se montó
una mini-app con un nombre largo en una columna estrecha y **se miró**: pinta
`…Instalación y puesta en marcha fase` y ahí se acaba, **sin elipsis**. Un nombre a medias
parece un nombre completo.
⚠️ En v408 ya lo había afirmado, pero desde una prueba más débil (el hook recibía el texto
entero, lo que dice qué se le PASA a `fillText`, no qué se ve). Ahora está mirado.

### 272 es el máximo que no cuesta nada
| ancho | contenido | oculto | columnas en la vista inicial |
|---|---|---|---|
| 248 (antes) | 1320 | 256 | **10** |
| **272** | 1344 | 280 | **10** ← mismas |
| 300 | 1372 | 308 | 9 (se cae `Tipo`) |
El margen del nombre pasa de **8 a 32 px** (~5 caracteres) y no se pierde ninguna columna:
solo hay 24 px más de scroll hacia lo que YA estaba fuera (`Inicio · Fin · Ppto`).

### Lo que de verdad cierra el caso
Ningún ancho fijo puede garantizar que quepa cualquier nombre. Lo que lo cierra es que al
**seleccionar la fila**, la tira de acciones (v402) muestra el nombre **completo** — así
que el nombre siempre es recuperable con un clic, aunque en la tabla salga cortado.

## La nota del Panel: de UNA línea a HASTA dos (v415)
v412 acotó la nota a una línea y bajó el alto del tablero un 30%. Al ir a cerrar el
pendiente, **medir en producción cambió mi propia recomendación** (yo había dicho
«esperar a verlo en uso»):
```
3 notas reales · 2 CORTADAS
«cambia de obra a media mañana»   154 px de texto en 135 de caja  (faltan 19)
«⚠️ se pisa: dos obras a la vez»  138 px en 135                   (faltan  3)
«refuerzo de fin de semana»       136 px en 136                   (cabe justo)
```
A un **aviso** le faltaban **3 píxeles**. Y las notas de este tablero son avisos: cortarlas
es cortar justo lo que hay que leer de un vistazo.

### «HASTA dos», no «dos»
Con `-webkit-line-clamp:2` la nota corta **sigue ocupando una línea** (14 px, medido en la
mini-app), así que no se deshace lo que ganó v412: el alto extra solo lo pagan las filas
con nota larga — hoy 2 de 8, no las 8. Es la diferencia entre acotar y estirar.
⚠️ `max-height` de respaldo otra vez: el navegador **blockifica** el `display:-webkit-box`
(sale `flow-root`, medido), así que el tope real lo pone él, no el clamp. Misma lección
que el label de la celda en v412.

### ⚠️ La mini-app NO reproducía el ancho, y se vio a tiempo
En la mini-app la nota de 154 px cabía en una línea: sin el sidebar de 300 px, sus
columnas son más anchas que las de producción. Lo que la mini-app SÍ valida es el
mecanismo (clamp, tope, que la corta no crezca); el ancho sale de la medición en
producción. **Separar qué prueba cada banco es lo que evita el OK en falso.**

### Guardián caducado (actualizado, no relajado)
`verif_v412` exigía literalmente `nowrap` + `ellipsis`, o sea UNA línea. Lo que protege no
es el número de líneas: es que la nota **tenga un tope** y no pueda volver a estirar la
fila sin control (medía 61 px, más que la celda). Reescrito sobre eso y probado contra el
código roto: caza que la nota pierda el clamp o el `max-height`.

## Versiones desplegadas (v415 = actual)
⚠️ La tabla NO está completa: v241-v288 se desplegaron sin registrarse aquí (el documento se quedó
atrás). Lo que sí está descrito arriba, en sus secciones propias, es lo que se construyó en ese
tramo (Contactos/CRM, Finanzas, Inventario, geocoder, ruta del día, sistema de diseño). Para el
detalle exacto de una versión no listada: `git log`.

| Ver | Cambio principal |
|---|---|
| v415 | **La nota del Panel pasa de UNA línea a HASTA dos.** Medir cambió mi propia recomendación (yo dije «esperar a verlo en uso»): de las **3 notas reales, 2 se cortaban**, y a un aviso —«⚠️ se pisa: dos obras a la vez»— le faltaban **3 px** de 135. Las notas de este tablero son avisos: cortarlas es cortar lo que hay que leer de un vistazo. ⚠️ **«Hasta» dos, no dos**: con `-webkit-line-clamp` la nota corta sigue en una línea (14 px), así que el alto extra lo pagan las 2 filas que lo necesitan, no las 8 — no se deshace lo que ganó v412. ⚠️ `max-height` de respaldo, porque el navegador **blockifica** el `display:-webkit-box`. ⚠️ Y la mini-app **no reproducía el ancho** (sin sidebar, sus columnas son más anchas y la nota cabía): valida el MECANISMO, mientras que el ancho sale de medir producción. Guardián de v412 **caducado y reescrito** sobre lo que protege de verdad (que la nota tenga tope, no que tenga una línea) |
| v414 | **El nombre de obra deja de ir al filo** en `Proyectos · Lista` (pendiente de v408): la columna medía 248 px (232 útiles) y el nombre más largo ocupa **224** — ocho píxeles de margen. ⚠️ Y el corte es **SILENCIOSO**: comprobado MIRÁNDOLO en una mini-app, glide **no dibuja «…»**, recorta en seco, así que un nombre a medias parece completo (en v408 lo afirmé desde una prueba más débil: que el hook recibiera el texto entero dice qué se le PASA a `fillText`, no qué se ve). Medido el coste: a **272** entran las **mismas 10 columnas** que a 248 y el margen sube de 8 a **32 px**; a 300 se cae `Tipo`. ⚠️ Ningún ancho fijo garantiza que quepa cualquier nombre — lo que cierra el caso es que al seleccionar la fila la tira de acciones (v402) muestra el nombre **completo** |
| v413 | **Homónimos en Planificación**: en el Panel había **dos filas «Mei Chen»** —dos personas distintas idénticas en pantalla—, así que al asignar la obra no se sabía a cuál. ⚠️ `auth.etiqueta_usuarios` existía **desde v319 y solo la usaba Nóminas**; las 8 vistas de Planificación seguían pintando `Nombre or Usuario` (sexta aparición del patrón: v151·v306·v319·v348). Nuevo `_etq`, que delega en esa función y ⚠️ desempata sobre **todo el grupo**, no sobre la lista visible (si no, la misma persona cambiaría de nombre según la pantalla). **De propina**: en `_asignacion_inteligente` el nombre es CLAVE de un dict de opciones, así que dos homónimos del mismo estado **colisionaban y una era imposible de elegir** (v147/v150) — el desempate lo arregla, no lo maquilla. ⚠️ NO se tocaron dos sitios, vistos auditando por AST cada lectura de `nom` ANTES de editar: `_ficha_rapida` (su `nom` alimenta el deep-link `gp_fichasel`; con la etiqueta quedaría «Mei Chen (mchen) (mchen)» — el fallo de v308) y `_catalogo` (su `nom` es el nombre de un TRABAJO, no de una persona) |
| v412 | **La celda del Panel deja de estirar su fila**: una sola celda con dos asignaciones y franja horaria triplicaba su fila. Medido a 1440: filas de **36 a 116 px**, y el culpable no era la celda (53) sino **la NOTA (61)**, que ocupaba más que el trabajo que anota. La nota pasa a una línea con elipsis + texto completo en el `title`, y el label se topa a 2 líneas → filas de **108/144/38 a 63/63/38** (−43% de alto). ⚠️ La primera medición, tomada al ancho del PANEL, daba 36–421 px: habría dimensionado el arreglo para un problema 7,5× peor que el real — **tercera vez en el día** que medir al ancho equivocado cambia la conclusión (v335). ⚠️ El clamp necesita **tres** propiedades y aun así el navegador **blockifica** el `display` (el `<p>` está en un flex), así que el tope real lo garantiza un `max-height` de respaldo. ⚠️ Verificado que el selector NO alcanza a los botones del editor (el popover abierto se portalea fuera). ⚠️ El `title` escapa también las COMILLAS: `_esc` no las toca y una comilla permitiría inyectar atributos |
| v411 | **Franjas alternas + columna de HOY en el Panel** (pedidas por el usuario tras ver la rejilla): filas pares con fondo tenue y el día de hoy teñido en cuerpo y cabecera, con subrayado azul y la palabra «hoy». ⚠️ La zebra va por **key de fila** (`st.container(key="rosrow_…")`), NO con `nth-child` sobre el `stLayoutWrapper` que Streamlit intercala: atarla a ese wrapper la rompería **en silencio** si mañana mete otro nivel (v327). ⚠️ «Hoy» solo se marca si **cae en la semana visible** — al navegar a otra semana no se resalta nada, porque marcar un día cualquiera como hoy mentiría. ⚠️ La celda vacía pasa a **transparente**: su `#f8fafc` tapaba las dos señales justo en las celdas vacías, que son la mayoría del tablero. ⚠️ «hoy» va en **segunda línea** porque con la ventana estrecha la columna baja a 55 px y ni la fecha sola cabe holgada — y la primera medición, tomada al ancho equivocado, decía lo contrario (error de v335). Caducaron y se actualizaron los guardianes de **v410** y **v301**, con la razón escrita al lado |
| v410 | **Rejilla en el Panel de planificación** (pedida por el usuario): las celdas dejan de flotar sobre blanco — línea por fila, línea por día y cabecera anclada con una más marcada, para poder seguir una persona hasta el viernes o un día hacia abajo sin ir contando. Cabecera y filas envueltas en `st.container(key=…)`, usados como **objeto** (`_grid.columns(...)`) y no con `with`, para **no reindentar** el bucle (la clase de cambio que rompió v120/v148). ⚠️ Medido antes de escribir el CSS: el borde inferior necesita `!important` (sin él ganaba una regla de Streamlit y salía `0px`) y el derecho no; y **un popover CERRADO ya lleva su `st.columns` dentro de `.st-key-roscel_*`**, así que sin excluirlo el editor de la celda saldría cuadriculado. ⚠️ Para juzgar el resultado hubo que capturar a **1:1** y en **tema claro**: el panel escalaba 1440→800 y se comía las líneas de 1 px. Guardián `verif_v410.py` — ⚠️ uno de sus chequeos daba **OK con la exclusión borrada** (miraba subcadenas que existen por otros motivos); lo delató probarlo contra el código roto |
| v409 | Documentación de v408 en CLAUDE.md: el barrido de las 24 pantallas, las trampas 21-23 (el recorte por *clip* sin elipsis, «encoger cambia un problema visible por uno invisible», y los rojos de la suite que venían de la consola) y la **corrección de v334** sobre qué prueba la barra de versión |
| v408 | **Barrido de las 24 pantallas del admin.** ⚠️ La primera vuelta corrió a **800×292** y a ese ancho no prueba lo que parece (el error de v335): repetida a **1440×900** midiendo el desborde DENTRO de cada tabla, `Proyectos · Lista` ocupaba **1339 px en 1054**, así que `Usuarios`, `Situación` y `Alertas` —las tres señales de «esto necesita atención»— quedaban al otro lado del scroll, y al ir a buscarlas **se perdía el `ID`** por la izquierda. ⚠️ NO se arregló encogiendo: se probó y con 13 columnas y nombres de obra reales no cabe sin **CORTAR** texto — y el corte es INVISIBLE, porque glide recorta por *clip* sin elipsis (hubo que medir `measureText` del canvas: se comía 60 px del nombre de obra y 60 del cliente). La cura es la de v398: no achicar, **priorizar** — las de atención suben junto al nombre, el contexto baja a la derecha, y `ID`/`Proyecto` van **`pinned`** (verificado con un scroll real de 255 px: siguen en su sitio; 10 de 13 columnas visibles de entrada, 0 textos cortados). + el aviso de duplicado del Pre-Start decía siempre *«fírmalo arriba»* colgando de `hecho_hoy`, cuando el bloque de firma cuelga de `pendiente_de_firma`: a quien ya constaba se le señalaba algo que no estaba en pantalla (las dos preguntas que v403 separó, remezcladas en el texto). Con bandera `_pf_ok` para no afirmar «ya constas» tras un fallo de lectura |
| v407 | **Se bloquea el segundo Pre-Start del mismo día y la misma obra.** Hasta ahora nada lo impedía y era fácil emitir dos documentos para una sola charla — me pasó a mí sembrando datos. ⚠️ **Bloqueo con salida explícita, no bloqueo duro**: hay un caso legítimo (otro turno, otra cuadrilla) y negarse en redondo dejaría **sin registrar una charla que ocurrió**, que es peor que el duplicado; hay que marcar una casilla, igual que el aviso de proyectos duplicados de v126. El guardián va en `submit`, no en la UI, para que ningún camino lo esquive; el aviso sale **antes** del formulario, no después de rellenarlo |
| v406 | ⚠️ **`pendiente_de_firma` solo miraba la PRIMERA charla del día.** Nada impide dos Pre-Starts de la misma obra el mismo día (dos turnos, dos cuadrillas, o un duplicado), y con dos, **quien firmaba la segunda seguía viendo «te falta firmar» por la primera, para siempre**. Ahora se miran TODAS las del día: si firmó alguna, no se insiste; si no firmó ninguna se le ofrece **la más reciente** y se le DICE que hay más de una, porque cuál le tocaba no lo sabe la app y elegir en silencio sería peor. Salió de un error mío sembrando datos: metí sin querer un segundo Pre-Start en una obra que ya tenía el suyo, y la app lo aceptó |
| v405 | **`use_container_width` → `width="stretch"`**, 200 sitios en 21 ficheros. El runtime anunciaba la retirada **«after 2025-12-31»** — fecha ya pasada, así que podía desaparecer en cualquier versión. ⚠️ **3 no se tocaron**: los dos `st_folium` (parámetro del COMPONENTE; convertirlo rompe el mapa de v307) y **un comentario** que contiene el literal — por eso la migración va por lista blanca de AST y no por texto, o el comentario habría acabado mintiendo. Medido antes: los 8 elementos aceptan `width` |
| v404 | ⚠️ **El catálogo de rieles escribía en un libro y leía de otro** desde v359. `Rieles` es hoja GLOBAL (vive en el maestro), pero `rails._ws()` la abría con `timeclock._get_worksheet()`, que devuelve el libro **del grupo de la sesión** — mientras el lector va por `hojas.registros`, que resuelve con `sheet_id_para`. Medido en la demo: **2 rieles en el maestro, 0 en el libro donde escribía**. Efecto: un riel nuevo **no se encontraba nunca** → al cargar un plano **RAIL se quedaba en 0**, el síntoma que v157 dio por cerrado; y editar o borrar un riel real respondía «Referencia no encontrada». Ahora usa `get_sheet`, el mismo resolutor que el lector. + `_invalidate` tira **las dos** cachés (la del módulo y el LOTE de v339, o el riel nuevo no se ve en 120 s). ⚠️ Lo encontró el banco de pruebas nuevo en su primera vuelta completa — no una revisión de código |
| v403 | **Quien llega después firma el Pre-Start**: hasta ahora, en cuanto alguien registraba la charla, el que fichaba más tarde en esa obra **no recibía ningún aviso** y trabajaba sin constar en el documento de seguridad — hueco de una decisión propia de v374, que ató el recordatorio a «¿hay charla?» olvidando «¿consto yo en ella?». Nuevas `pendiente_de_firma` y `firmar`; el aviso no desaparece, cambia de motivo. ⚠️ **Se ANEXA una hoja, no se regenera el PDF**: las firmas originales solo viven dentro del documento emitido (v383), así que rehacerlo borraría la de quien sí estuvo en la charla — se compone `original + anexo` con `pypdf` y cada firma tardía lleva su hora. ⚠️ Orden de escrituras de v343 (subir el nuevo → actualizar la fila → borrar el viejo), verificado midiendo el orden real. ⚠️ `io` no estaba importado en `prestart.py` y el `BytesIO` iba dentro de un `try`: el PDF se habría dejado de componer en silencio (el NameError latente de v370) |
| v402 | **Facturar desde la LISTA**: el usuario avisó de que «desde la tabla de proyectos no puedo hacer los invoices, solo ver si ya está facturado o no» — y era una decisión mía de v397. Ahora elegir una fila **ya no abre el proyecto**: muestra las dos acciones explícitas («Abrir →» y «Facturar»), como Finanzas·Gastos (v215) y Usuarios (v226). Decisión suya sabiendo el coste: abrir pasa de 1 a 2 clics. ⚠️ **NO se hizo enlazando la celda**, que era la idea de partida, y eso se decidió MIDIENDO: un `LinkColumn` **ordena por la URL, no por el importe** (`$980 · $5,200 · $27,883 · $2,960` = el alfabético de los PRJ-####), y en el bundle que distribuye Streamlit su clic hace `window.open(url,"_blank")` + `preventDefault()` → no recarga la pestaña, pero **abre una pestaña nueva = sesión nueva**, o sea el login si no está tildada la cookie de v221. ⚠️ El guardián de v397 afirmaba «la lista NO factura»: **caducado**, reescrito sobre el principio que sigue vivo (ninguna acción puede colgar de la selección, todas bajo un botón) y probado contra el código roto |
| v401 | **Narrativa v102-v130 comprimida**: 29 secciones y 502 líneas → 137, conservando las 6 REGLAS, los avisos ⚠️, el dominio de los planos y un índice de los símbolos que solo se nombraban ahí. ⚠️ Se comprimió **solo** eso: de las 889 líneas «antiguas», más de la mitad son el CONTRATO de un módulo (`plumb.py`, `auth.py`, `timeclock.py`, `projects.py`…) y llevan versión en el título sin ser narrativa. ⚠️ El chequeo no fue «parece bien»: se extrajo cada span de código del texto viejo y se comprobó que siguiera existiendo en el documento — y hubo que **afinar la sonda**, porque comparar el span literal daba 128 falsos perdidos (`_do_calculo()` no casa con `_do_calculo`) y empujaba a inflar el texto nuevo sin motivo. Documento: 6.498 → 6.133 líneas (549 → 519 KB) |
| v400 | Documentación de v396-v399 en CLAUDE.md |
| v399 | **El dinero tenía dos caras en la misma pantalla**: la celda pintaba `$27883` y la tarjeta de al lado `$27,883` (y el pie de esa MISMA tabla también, porque sale de `theme.dinero`). No era una columna: eran **39 en 7 módulos** — todas las TABLAS de dinero de la app sin separador de miles frente a todos los KPI con él. ⚠️ El veredicto no se puede leer en el DOM: `st.dataframe` pinta en canvas y su nodo accesible lleva el valor CRUDO, así que se midió **interceptando `fillText`** (trampa nº18). ⚠️ `%d` NO se cambió por `%.0f`: uno trunca y el otro redondea, y unificarlos habría movido cifras (trampa nº20). ⚠️ Las columnas EDITABLES probadas tecleando: el editor se siembra con `1500`, no con `$1,500.00`, y devuelve el número intacto. Guardián `verif_v399.py` + suite **53/53** |
| v398 | **Existir no es servir**: la columna «Sin facturar» era la décima de trece y, medido en producción con la tabla a ~520 px, **había que hacer scroll horizontal para encontrarla** — no cumplía la función por la que se añadió. Se movió junto al nombre |
| v397 | **Facturar desde la cartera**: insignia con el importe + botón «Facturar» en la tarjeta (solo donde hay pendiente y solo para gestión), columna «Sin facturar» ORDENABLE en la lista, y el atajo en la cabecera de la ficha. `pendiente_por_proyecto` es la ÚNICA definición del mapa (`finance.sin_facturar` delega) y `_ir_a_facturar` la única de la navegación. ⚠️ Falsa alarma resuelta midiendo: el botón salía dos veces en el DOM y el segundo mide 0×0 — es el nodo del tooltip de `help=` |
| v396 | Documentación de v387-v395 en CLAUDE.md |
| v395 | **Se avisa de las alarmas que no le llegan a nadie**: un destinatario sin email ni Telegram recibe la alarma *dentro* de la app y solo la ve si entra a mirar — y desde v373 un control de seguridad en NO abre alarma. Medido en la hoja real: de los 5 destinatarios de `cliente1`, a **3 no les llega** (`dacox`, `Arcantox`, `admin1`), aunque siempre llega a 2. El aviso va **donde se arregla** (Planificación · Usuarios, sobre la tabla del email). ⚠️ Criterio distinto al del campo a propósito (a un gestor le basta UN canal; al campo se le exigen los dos, v79 — mezclarlos sería el error de v325) y ⚠️ **no entra en `_PENDING_KEYS`**: la rejilla del resumen es de nueve indicadores fijos con guardián (v305). 0 lecturas nuevas |
| v394 | La barra del Panel **cabe en una fila a media pantalla**, esta vez MIDIENDO: la fila da 406 px y el `gap` por defecto se comía 48. ⚠️ Y el rango largo se partía en **3 líneas** dentro de 56 px — eso era lo que hinchaba la fila, invisible hasta medir su altura. Tres recortes: `gap="xxsmall"` (−36), rango sin año (−75) y menos padding **acotado a este** segmentado (−36). Medido en producción: barra de 70 → **40 px**, las tres vistas en una fila, 0 recortes |
| v393 | ⚠️ **La firma del Pre-Start no cabía en un móvil**: `st_canvas` nace con `width=600` y no acepta `use_container_width`, así que en un viewport de 375 px el lienzo salía de 600 dentro de un hueco de 343 y **la mitad derecha quedaba fuera de pantalla** — el `st_folium` de 500 px de v307 otra vez. Ahora 300 px (medido: cabe entero). ⚠️ Sigue sin demostrarse que un DEDO complete el trazo: necesita un teléfono real. + **auto-poblar** rellena el fin de semana **solo si en esa semana ya hay alguien trabajándolo** (la condición sale del dato, no de una preferencia: ni impone sábados ni obliga a añadir a mano en una semana que la cuadrilla sí trabaja) |
| v392 | La barra del Panel pasa de 5 a 4 columnas («Copiar semana anterior» baja a la fila de la cobertura) para dar ancho al segmentado. ⚠️ Rompió el guardián de v291, que exigía literalmente la columna `b5`: **caducado, no regresión** — lo que aquella regla defiende es que el chrome no vuelva a ser cuatro bandas, y siguen siendo dos. Actualizado para DERIVAR el número de columnas del propio código |
| v391 | Etiquetas cortas en el segmentado (**Semana · Día · Libres**) porque «Disponibilidad» se recortaba con tres opciones. Solo el display: los valores son el estado guardado y no se tocan (v232) |
| v390 | **Vista por DÍA de la cuadrilla** (una fila por persona sobre un eje de horas — lo único que ninguna de las tres vistas de un día ya existentes daba) + **sábado y domingo por semana** con `+ Sáb`/`+ Dom`, sin configuración nueva: la columna reaparece sola si hay algo asignado, y quitarla con trabajo dentro está bloqueado (v340). ⚠️ `DIAS_TODOS` va en el orden de `weekday()`, así que **ninguna fecha existente se mueve**. Se movió con ello todo lo que asumía Lun–Vie (rango, atajo de semana, radar de 7 días, agenda de Home, Ruta del día, Cumplimiento, Asignar, board del campo). Los cortes de `weekday() > 4` ya no cortan por ser sábado, sino si NO hay nada. Ejercitado contra la hoja real (incluido que `copiar_semana` arrastra el sábado, que era una afirmación mía sin probar) |
| v389 | ⚠️ El popover **no** se cierra con el `st.rerun()` (medido en producción: su estado vive en el frontend). El comentario del código decía lo contrario — corregido, no el comportamiento: forzarlo exigiría remontarlo por `key` y eso arrastra el CSS del color de cada celda |
| v388 | ⚠️ **El resumen de la vista del día mentía, y era mi propio fallo**: con dos obras solapadas de 8,5 h decía «17.0 h» — el mismo rato contado dos veces, justo lo que el aviso de al lado denuncia. Las horas pasan a ser la **UNIÓN** de las franjas y la suma solo aparece junto al aviso, como síntoma. + plural («asignación»/«asignaciones» pierde la tilde) y keys con la misma tripleta |
| v387 | **Ver el día de una persona**: la celda solo cabe «primero +N» (v295), así que un día con varias obras esconde a qué hora es cada una y si se pisan. Línea de tiempo a escala **con carriles** (el solape se VE) bajo el tablero. ⚠️ **Medir los datos antes de diseñar cambió la propuesta**: 32 de 35 asignaciones no tienen hora y el único día doble real tiene las dos a la MISMA franja — un eje puro habría dibujado un bloque sobre otro con el resto vacío. Las que no tienen hora salen como «todo el día», sin fingir una franja. ⚠️ Un turno que acaba cerca de medianoche dejaba el eje bajo su propio mínimo (`hi` topado en 24:00 → hay que bajar `lo`) |
| v386 | Documentación de v383-v385 en CLAUDE.md |
| v385 | **Auditoría de la suite ENTERA**: venía corriendo un subconjunto elegido por mí, así que «13 en verde» ocultaba que de **48 guardianes fallaban 13** — dos introducidos ese mismo día. **3 fallos reales**: el `font-size:15px` de la banda nueva (fuera de la escala de v333), un `import pandas` muerto en `prestart_ui`, y **5 `except: pass` que se tragaban el apunte de auditoría** sin dejar rastro (de v342/v352). **9 caducados**, actualizados con la razón escrita al lado, no relajados: los tres de la nav exigían código que **v299 borró** (fallaban por haber ganado), y el resto miraba CSS, columnas, fixtures y enlaces que v301/v310/v313/v317/v318/v325/v333/v361 cambiaron a propósito. **Y un falso positivo del propio guardián**: acusaba a `catalogo` y `orders` de leer el `_next_id` de la caché porque buscaba la subcadena `_records`… y **`get_all_records` la contiene** (la trampa nº2, *grep ≠ uso*, dentro de un chequeo). REGLA: se corre la suite entera, no la lista que uno recuerda |
| v384 | Fix: la banda del Pre-Start usaba `font-size:15px`, fuera de la escala tipográfica de v333 |
| v383 | **Firma DIBUJADA en el Pre-Start** (una por asistente, solo en el PDF) + **banda de aviso en la barra superior** que no se puede descartar hasta que el Pre-Start esté hecho. La dependencia (`streamlit-drawable-canvas`, de 2023) se probó ANTES contra el Streamlit 1.57 que corre aquí: captura el trazo (543 B en blanco → 5.245 B firmado) y reportlab lo acepta; import perezoso, así que si falla se cae a las iniciales en vez de dejar sin registrar la charla. ⚠️ **Tres trampas**: detectar la firma por el canal ALFA daba **58.800 píxeles de trazo en un lienzo VACÍO** (todos «firmados»); `json.dumps` **no serializa bytes**, así que sin filtrar la firma el registro habría fallado entero (y en base64 seis firmas rozan el tope de 50.000 caracteres por celda); y la columna de firma medía el **9%** del ancho —dimensionada para dos iniciales— y partía el encabezado como «Signatur / e», lo que solo se vio extrayendo el texto del PDF generado. + `logger` inexistente en el `except` de la firma (el NameError latente de v370), con el guardián ejercitando esa rama |
| v381 | ⚠️ **v380 arregló la función equivocada.** Con la pantalla delante, las alarmas ya salían y las 12 tarjetas **seguían en `0h`**: el arreglo fue a `project_hours_bulk` dando por hecho que era la de la cartera, y `render_owner_projects` llama a **`project_hours()` una vez por obra**. El test daba ✓ sobre una función que esa pantalla no usa. **REGLA: antes de arreglar lo que pinta una pantalla, mirar QUÉ función llama** — el guardián lo comprueba primero y solo después mide. + otro cero peligroso: **`datos_asociados`**, el recuento que se enseña ANTES de borrar un proyecto, le daba **0 en todo** al propietario («no cuelga nada» con 25 fichajes, 3 gastos y 11 actividades colgando) |
| v380 | ⚠️ **La fase 2 se dejó dos huecos, y solo se vieron EN PANTALLA**: con la sesión de propietario los proyectos salían pero **todas las tarjetas marcaban `0h`** (el demo tiene 484 fichajes) y **0 alarmas** (el admin veía 19). Mis tests medían `list_projects`, pero una tarjeta se arma con **cuatro fuentes** y cada una tiene su propio camino al libro: las horas van por la hoja del fichaje y `open_counts_all()` **ni siquiera recibe grupo**. Cerrados con el mismo patrón. **REGLA: cuando una pantalla se compone de varias fuentes, compararlas TODAS contra quien las tiene bien** — arreglar la principal y dar la pantalla por buena deja ceros con pinta de dato. Guardián nuevo que compara horas, alarmas, gastos y retrasos del propietario contra los del admin |
| v379 | **FASE 2: el propietario vuelve a ver a todos sus clientes** (veía 0 desde la mudanza de v377). En vez de hilar un `grupo` por ~40 funciones, **`tenant.como_grupo(g)`**: dentro del `with`, `sheet_id_para` consulta el grupo activo antes que la sesión, así que toda lectura cae en el libro de ese cliente. Un cambio, en el único punto donde se decide el libro; aplicado en 4 sitios. ⚠️ Vive en `session_state`, no en un global (un global se comparte por proceso — el fallo que acababa de cerrar v378). ⚠️ `grupos_por_libro()` lee una vez por LIBRO, no por grupo: si tres comparten el maestro, leerlo tres veces **triplicaría** el consolidado. ⚠️ **Y una fuga que introduje yo**: hacer que el `grupo` explícito eligiera libro SIEMPRE convertía el argumento en una llave (un admin ajeno pasando `grupo="cliente1"` leía su libro) — ahora solo elige si `tenant.puede_ver`. La cazó el test de dos inquilinos, y **solo tras reescribirlo**: el de v378 comparaba propietario contra admin y con la fase 2 había dejado de distinguir una fuga de la funcionalidad nueva |
| v378 | ⚠️ **Fuga de datos ENTRE INQUILINOS en la caché.** `st.cache_data` se comparte por PROCESO y la clave era solo el título de la hoja, así que el segundo cliente recibía lo que memoizó el primero — demostrado con los dos libros reales en los dos sentidos. El cerrojo de v351 no lo cubre: comprueba el grupo de un objeto ya traído, y aquí **la lista entera es del inquilino equivocado**. 18 lectores de inquilino en 16 módulos: la función cacheada pasa a `X_cached(libro, …)` + envoltorio con el nombre de siempre, **sin tocar ninguno de los ~40 call-sites**. ⚠️ **Tres trampas**: (1) llamar al parámetro `_libro` dejó el arreglo **INERTE** — Streamlit excluye de la clave los argumentos que empiezan por guión bajo, y solo lo delató instrumentar qué se ejecutaba de verdad; (2) `compileall`, los imports y el guardián de AST daban ✓ con **3 `NameError` dentro de los envoltorios** (`TRABAJOS_SHEET`, `SHEET`×2) — **importar no ejecuta**, hubo que llamarlos uno a uno; (3) los `.clear()` de `_invalidate` apuntando al envoltorio, la regresión de v344 por tercera vez |
| v377 | **La demo se muda a su propio libro** (`COPEX — DEMO (cliente1)`) y el maestro queda limpio para el primer cliente real: 22 hojas de inquilino copiadas, **9.617 celdas verificadas una a una**, y solo entonces vaciado el maestro. Las 4 globales (`Login`, `Grupos`, `Rieles`, `Manuales`) se quedan. Orden sagrado: **copiar → verificar → enlazar → verificar → borrar → verificar**. ⚠️ Hasta vaciar el maestro ninguna cifra probaba nada (los dos libros tenían lo mismo) — el paso en vacío aplicado a una migración. **Tres errores míos por el camino**: el respaldo escrito DENTRO del repo (el deploy lo habría subido a GitHub con hashes y emails — lo cazó `git status`), el verificador reventando con un **429** por pedir hoja por hoja en vez de por lotes (el problema de v339 cometido en el script que venía a verificarlo), y `values_batch_clear` recibiendo la lista como `params` en vez de `body`. ⚠️ **La fase 2 dejó de ser teórica**: el propietario ve ahora 0 proyectos; quedan identificadas las 9 funciones que hay que tocar |
| v376 | Corrección del registro de v375 (documentación) |
| v375 | ⚠️ **Diagnostiqué un fallo que no existía: la sonda estaba ciega.** Verificando v374 en producción concluí que el pop-up «no se pintaba nunca» — mi `MutationObserver` y mis comprobaciones buscaban **`div[role="dialog"]`**, que es como lo marca el Streamlit LOCAL; el del **Cloud** usa **`[data-testid="stDialog"]`**. El modal estaba ahí, perfectamente pintado. **REGLA: una sonda NEGATIVA hay que validarla contra un caso conocido-bueno** — antes de decir «X no se renderiza», comprobar que la sonda sabe ver X cuando está. Familia de la trampa nº5 y de v304: el DOM de Streamlit cambia entre versiones y mi entorno no es el que corre. El rediseño se conserva por ROBUSTO, no como arreglo: el aviso pasa de evento de un solo uso (`pop`) a **condición de estado**, así que ningún rerun puede matarlo, y gana la salida por la **X** (`on_dismiss`) que antes no existía. ⚠️ NO está demostrado que v374 estuviera roto. + **el fallo que SÍ era real**: los cronómetros del sidebar enseñaban **`:material/schedule:` en crudo** desde v233 — la etiqueta va dentro de `components.html`, donde eso no es un icono sino markdown de Streamlit. Visto mirando la pantalla, no el código |
| v374 | **Fichar desde el sidebar** (v202 lo dejó de mirador y solo visible si YA estabas fichado): sin fichar, botón de tu asignación de hoy + selector del resto; fichado, los cronómetros + salir del proyecto / cerrar jornada. + **el Pre-Start del día se recuerda solo**: `prestart.hecho_hoy` — ⚠️ por OBRA y DÍA, no por persona (si el facilitador ya la hizo, al resto no se le recuerda; decisión del usuario) — con **modal al fichar** y **chip persistente** mientras falte (el modal se cierra y se pierde; el chip no). ⚠️ El modal va por BANDERA en la pasada siguiente y llamado al TOP LEVEL, no dentro del `with st.sidebar:` (v365 + el contenedor activo manda). ⚠️ **Verificado en vivo con la estructura exacta del código final** antes de construir: se pinta sobre la página, sobrevive al rerun, no reaparece. Falsa alarma resuelta midiendo: el icono del título parecía texto y era una **ligadura de fuente** (trampa nº5). ⚠️ Y las DOS direcciones de `hecho_hoy` probadas moviendo el día — comprobar solo el `False` es el paso en vacío |
| v373 | Las dos decisiones pendientes, resueltas por el usuario. **(a) Un check en NO abre alarma** (cierra el standing item de v158): hasta ahora solo lo hacía el near miss, así que un control de seguridad sin cumplir solo lo sabía quien abriera esa ficha. ⚠️ UNA alarma con todos los checks (no una por check: `report_problem` también notifica) y separada de la del near miss (un suceso vs un control que falta). NO ejercitada contra producción: mandaría correo y Telegram a personas reales. **(b) Ganancia FIJA por obra** (`GananciaFija`), el hueco que v370 dejó abierto: una obra creada a mano cuyo valor no está en las horas valía su costo — el delivery de Bespoke pasa de **$380 estimados a $5.200**, que es lo que se facturó. Se suma al modelo que aplique; ⚠️ a una obra COTIZADA **no**, porque ese precio lo firmó el cliente (se avisa de que el número no se usa). ⚠️ Mi primera versión cambiaba el denominador de `margen_pct` y habría movido el % de **todas** las obras sin fija: revertido, el margen del conjunto va en clave aparte y las 16 obras dan la misma cifra que antes. Vuelta atrás probada (0 la quita y el ingreso vuelve exacto). ⚠️ `GananciaHoraJSON` llevaba **13 versiones sin auditar** — el hueco de v344/v352 por tercera vez |
| v372 | ⚠️ **El avance que carga el campo no movía el % del proyecto.** `save_field_progress` recomputaba **antes** de invalidar, y `_recompute_project_avance` lee `list_activities`, que está cacheada 120 s — con la caché caliente (siempre lo está: la pantalla acaba de pintar esa tabla para editarla) recalculaba con las actividades VIEJAS. Medido en la hoja real: actividades al **26,0%** y el proyecto escrito en **0,0%**, estado «Planificado» en vez de «En progreso». Prueba de causa: el mismo guardado con la caché fría cuadra. Regresión de **v162** (el camino viejo recomputaba en memoria sobre filas frescas); un solo sitio, los otros 3 ya estaban bien. + la celda de avance **borrada** (`NaN`) reventaba el guardado ENTERO y la nota vacía guardaba el texto `"nan"` — ahora vaciar deja la actividad como estaba y se dice cuáles. ⚠️ Ese aviso tuve que pasarlo a `flash`: lo puse con `st.warning` sobre un `st.rerun()`, el fallo de v365 **dentro del arreglo**. ⚠️ Y mi test dio 5 ✗ EN FALSO por comparar `"40"` con `"40.0"` (la hoja guarda `str(float)`) |
| v371 | Documentación de v369 y v370 en CLAUDE.md (sin cambios de código) |
| v370 | ⚠️ **Una obra cotizada valía su COSTO, no el precio pactado.** Los materiales van a costo en los DOS modelos de ganancia, así que una obra cuyo valor no está en las horas (un delivery, un suministro) salía con ganancia $0: *Bespoke — Delivery* daba **$380 estimados habiendo facturado $5.200**, y una obra con cotización aceptada de $2.960 valía **$0**. El resultado REAL salía bien (usa la factura); lo que mentía era la estimación, y de ella cuelgan «ingreso estimado» y **«pendiente de facturar»**. La app **ya tenía** el número bueno —la cotización guarda su `ProyectoID` desde v354— pero el enlace era de una sola dirección: nueva `quotes.cotizacion_de_proyecto` y `project_revenue` usa el precio pactado (`modelo: "cotizado"`). ⚠️ La base es el **`Subtotal`**, no el Total: `facturado_por_proyecto` suma importes de línea sin impuesto, y el GST habría inflado lo pendiente **exactamente en el impuesto** ($296). Rentabilidad lo recoge sola (delega desde v361). ⚠️ Ejercitar el `except` de verdad destapó un `logger` **inexistente en el módulo** — NameError latente. Sigue sin cubrir la obra creada a mano sin cotización |
| v369 | **Facturar una obra ARCHIVADA desde el alta manual.** v358 lo resolvió solo para el atajo desde la ficha; desde Finanzas → Facturas → Nueva seguían inalcanzables — **quinta vez que el default de v149 muerde** (v310, v321, v322, v358). Archivar no es no-cobrar: lo normal es archivar al terminar y facturar después. Casilla con contador (la pieza de v149/v340), etiqueta «· archivada» para distinguirlas en el radio, y ⚠️ **al desmarcar se suelta el alcance elegido ANTES de instanciar el radio** (un `st.radio` con un valor guardado que ya no está entre sus opciones revienta). El dato que lo justifica: `cliente 1` tenía **3 obras archivadas con dinero sin facturar** ($618,15 · $415,20 · $0,48). Verificado en vivo, incluido elegir una archivada y desmarcar sin excepción |
| v368 | El bloqueo de contacto del campo exigía email **y** Telegram **sin comprobar si el canal existe**: en una instalación sin bot en Secrets eso no tiene salida (la pantalla no puede mostrar el link de Start ni el admin tiene botón). Ahora **solo se exige un canal que EXISTA**; con bot, todo igual. La pantalla además dice QUIÉN lo resuelve (el email lo carga el admin). Verificado por AST sobre la condición real de `app.py` en los 8 escenarios, 0 bloqueos sin salida, probado contra el código roto. ⚠️ **Y el error de método que importa más que el arreglo**: medí `telegram_configured()` en LOCAL y lo presenté como producción («7 encerrados sin salida») — en el Cloud el bot SÍ está, así que siempre tuvieron camino. El `secrets.toml` local NO es el del Cloud; afirmar algo del entorno real exige mirarlo EN el entorno real |
| v367 | Los **68 mensajes restantes** (el barrido de v366 decía 19 y estaba ciego dos veces: no veía `(st.success if ok else st.error)(...)` ni los `rerun` anidados — por eso el fichaje entero se escapó). ⚠️ Dos trampas evitadas: la rama de **error** NO se convierte (ahí no hay rerun, se ve; convertirla la haría desaparecer) y las **insignias de estado** tampoco (`st.success` + `if st.button(): st.rerun()` se pinta en cada pasada). La primera versión del parche rompió una insignia y hubo que revertir desde el respaldo |
| v366 | `core/flash.py` — mecanismo ÚNICO para los mensajes, pintado por la shell y por el login. 19 sitios convertidos. ⚠️ El chequeo de ámbito dio un **OK en falso**: `auth_ui` tenía el import DENTRO de `render_login`, mi patch lo dio por importado y dejó **4 NameError**; y mi verificador no lo vio porque descendía dentro de los `def` — el error exacto de v342, cometido dentro del chequeo escrito para cazarlo |
| v365 | ⚠️ **Ningún mensaje de generar nóminas se había visto NUNCA**: el `st.rerun()` que cierra el formulario descarta los deltas del run (mismo principio que v222 con `components.html`). Se perdían «N creadas», el aviso de v346 sobre quien no tiene tarifa —la razón de ser de esa versión— y el bloqueo de solape de v364 recién hecho. Confirmado con `git show` que el rerun era anterior a mi cambio |
| v364 | ⚠️ **Se pagaban las mismas horas DOS VECES**: el salto de duplicados de la nómina compara la terna EXACTA `(Usuario, Desde, Hasta)`, así que un periodo que **solapa** con otro ya emitido pasaba sin decir nada — a `campo1` se le pagaron 567 h habiendo trabajado 354. Salió de la forma más real: dos personas generando nóminas a la vez. Ahora se comprueba la intersección por persona, **no se emite** y se NOMBRA la nómina que estorba. El duplicado exacto y las anuladas siguen igual; las quincenas contiguas SÍ pasan; sin fechas legibles no se bloquea a ciegas. ⚠️ La conciliación de v313 ya lo gritaba, pero DESPUÉS de emitir — cada colilla suelta sale bien y solo el total delata |
| v363 | ⚠️ **Crear proyectos llevaba 3 versiones MUERTO** (y con ello aceptar una cotización): en v360 añadí `GananciaHoraJSON` a la cabecera y no su valor a la fila, así que el guardián de v306 cortaba con «Error interno» en cada intento. ⚠️ Matiz: una fila corta **no desplaza** datos (`append_row` deja la cola vacía, como hacen `add_user` y `add_group` a propósito) — el daño era que la función no hacía nada. Guardián nuevo **estático** sobre las 25 filas posicionales del repo (el de v306 solo salta al pulsar el botón, por eso vivió 3 versiones); la auto-validación manda al resolver, y lo no resuelto cuenta como fallo. + **el resolvedor de identidad, único**: v362 arregló «la misma persona partida en dos» solo en `labor_breakdown` y el patrón estaba en 5 funciones más — `timeclock.clave_de` lo unifica. ⚠️ Verificar comparando totales entre dos ejecuciones daba 20 h de diferencia por una sesión ABIERTA acumulando contra el reloj: **fallo en falso**; la comparación válida es sobre las mismas filas y el mismo instante (diferencia 0,02 s, dinero idéntico) |
| v362 | ⚠️ **La misma persona salía partida en dos**: `campo1` (usuario) y `lksdfkldsf` (su nombre) eran dos filas en el desglose de mano de obra, porque 2 fichajes anteriores a v106 no tienen columna `Usuario`. Inofensivo mientras solo se sumaba —el total era correcto— pero desde v360 hay que decidir la ganancia **por persona**, y partida significa **dejarse 8,97 h facturándose a costo** sin aviso (pasó un turno antes). Ahora se resuelve por nombre contra las cuentas, ⚠️ solo si ese nombre es de UNA sola cuenta (con homónimos, mezclar es peor). El total no se mueve: $1.646,40 antes y después |
| v361 | ⚠️ **Rentabilidad reimplementaba la fórmula del ingreso** y, con el modelo por rubro de v360, empezó a dar una cifra distinta que el detalle del proyecto (3.475,68 vs 3.628,80) — dos números de dinero para la misma obra. Ahora delega en `project_revenue`, la única definición, con guardián por AST. ⚠️ De paso, un fallo de método: el parche de v360 tenía un ancla inexistente envuelta en un `if not in`, así que **no aplicó y no avisó**; solo se vio mirando la salida con datos reales |
| v360 | **La ganancia deja de ser un % y pasa a ser un importe por rubro** — y el trabajador es un rubro: cada persona lleva su **ganancia por hora** en esa obra (`Proyectos.GananciaHoraJSON`), los materiales van a costo, y el % pasa a ser consecuencia en vez de entrada. ⚠️ **Respaldo**: sin ganancias puestas, la obra sigue con el modelo viejo, porque cambiar en frío habría desplomado el ingreso estimado de las 6 obras sin que nadie lo pidiera. ⚠️ Quien no tenga ganancia se factura **a costo** y se avisa (patrón v346), y quitar las ganancias devuelve **exactamente** a la cifra anterior |
| v359 | **Un libro de Google por empresa cliente** (mecanismo). El libro actual queda como maestro Y libro de `cliente1`, así que **no se migra ninguna hoja**; los clientes nuevos nacen con su archivo (`Grupos.SheetID`). `Login/Grupos/Rieles/Manuales` siempre en el maestro; el resto en el libro del grupo, resuelto desde la sesión como `clock.now()` (v173) — ninguna de las 21 llamadas a `get_sheet` cambió de firma. ⚠️ El orden GLOBAL-antes-que-auth evita una recursión infinita, y el lote se cachea **por libro** (si no, el 2º cliente leería los datos del 1º). ⚠️ Límite dicho en pantalla: los consolidados del propietario aún solo cuentan el maestro (fase 2). ⚠️ La cuenta de servicio no puede crear archivos (solo scope `spreadsheets`), así que el aislamiento de punta a punta queda pendiente de un libro real |
| v358 | ⚠️ **Una obra archivada no se podía facturar**: el atajo de v357 llevaba al alta y la obra no estaba entre las opciones (el formulario usa `list_projects`, que oculta archivados desde v149) → la preselección no hacía nada, **en silencio**. Archivar no es no-cobrar: lo normal es archivar al terminar y facturar después. Cuarta vez que ese default muerde (v310, v321, v322). + la guarda de v357 tenía un caso mudo, que ahora habla. Encontrado **verificando en producción**, no en tests |
| v357 | **Atajo: facturar desde el propio proyecto** — «Pendiente de facturar $X» + botón en 💰 Costos que abre el alta con cliente y proyecto ya elegidos. Reutiliza el alta existente (verificado: 1 formulario y 1 sola llamada a `create_factura`). ⚠️ No fija la etiqueta desde fuera —la resuelve el formulario, antes de instanciar el radio (v111/v306)— y ⚠️ mirar los datos reales evitó un crash: `Proyectos.Cliente` es texto libre y dos obras tienen «vd» y «ci», que no son fichas; preseleccionar eso reventaría el selectbox. Ahora resuelve por `ClienteID` y, si no hay ficha, lo explica |
| v356 | ⚠️ **El editor de borradores refrescaba los precios en silencio**: reconstruía cada línea desde el catálogo al guardar, así que tocar una celda habría cambiado el total de la cotización real del usuario de $1.927,20 a otro número sin avisar. Ahora la cantidad **escala sobre el costo unitario congelado** y adoptar precios nuevos es un **botón explícito**, que conserva la ganancia en dinero y recalcula el margen. Con aviso de qué cambió («$960 → hoy $80»), solo en borrador, y las líneas cuyo artículo se borró se dicen en vez de descartarse. Encontrado mirando **datos reales**: con artículos de prueba, catálogo y líneas siempre coinciden |
| v355 | **Se cotiza por GANANCIA, no por porcentaje**: el admin escribe cuánto quiere ganar en cada rubro y el margen % y el precio se calculan solos (Margen y Precio quedan bloqueados en la tabla). Nueva `margen_de()` como única fórmula y `ganancia_de()` derivada del precio, para que no puedan desacompasarse. ⚠️ Al cambiar la cantidad se conserva la **ganancia**, no el %, que es lo que la persona dijo. La invariante `precio = costo + ganancia` verificada exacta en 36 combinaciones; el margen redondeado es solo de lectura |
| v354 | **Cotizaciones, fase 3 — módulo COMPLETO**: aceptar la cotización **crea el proyecto** con cliente, presupuesto, margen y cronograma, y aparece el bloque **cotizado vs real** (horas, costo, ganancia). ⚠️ El presupuesto del proyecto es el **COSTO** cotizado, no el precio: `project_cost` compara contra compras+mano de obra, así que con el precio la alerta solo saltaría cuando ya pierdes dinero. Idempotente (un doble clic no duplica la obra). ⚠️ La prueba cazó que «ganancia real» a mitad de obra daba $3.499 contra $893 cotizados **en verde** —no has ganado, es que no has gastado—: ahora se **proyecta** al ritmo actual (patrón v144) y solo se llama «real» al 100% |
| v353 | **Cotizaciones, fase 2**: armar el precio desde el catálogo con **margen por línea**, estados (borrador→enviada→aceptada/rechazada, con `vencida` derivada de la validez), versiones y **PDF formal**. La línea congela su precio (subir el catálogo no mueve lo ya enviado) y una cotización enviada no se edita: se saca versión nueva. ⚠️ Verificado que el PDF **no filtra costos ni márgenes**. ⚠️ La prueba cazó que olvidé la hoja en `hojas.HOJAS_LECTURA`: como el lector va sin cabeceras, el módulo leía **vacío para siempre sin ningún error** — guardián nuevo para ese patrón. + margen 20% y GST 10% configurados en el grupo |
| v352 | **Cotizaciones, fase 1: el catálogo.** `core/catalogo.py` + pantalla en Finanzas · 📚 Catálogo: productos (costo × cantidad) y servicios (**horas × tarifa**, para poder comparar luego contra lo fichado). `costo_de()` es la fórmula única que usarán cotización, PDF y la comparación. No deja crear artículos sin costo (fallo de las colillas de $0 de v346), desactivar con vuelta (v340), homónimos por ID (v306). ⚠️ La prueba cazó que **el precio no se auditaba**: `CostoUnit` no estaba en `CAMPOS_CLAVE` — el mismo fallo que `MargenPct` en v344, y el guardián no lo vio porque solo miraba una dirección; ahora mira las dos |
| v351 | ⚠️ **Aislamiento entre empresas cliente.** El aislamiento no lo garantizaba el código sino que la interfaz nunca te ofreciera el ID de otro: **ninguna vista de detalle comprobaba el grupo**, y `_detalle_proyecto` lo ADOPTABA del proyecto → con los deep-links de v337 bastaba editar `?p=` para abrir el detalle completo de otro cliente (costos, horas, personal, archivos). Latente hoy porque solo hay un grupo real. Nuevo `core/tenant.py` (una sola definición, módulo hoja) aplicado a las 4 vistas por ID global: proyecto, factura, nómina y activo. El propietario sigue viendo todo; el mensaje no revela de qué empresa es el ID. Decisión del usuario: **cerrojo ahora, un libro por cliente cuando entre el primer cliente real** |
| v350 | **Inventario, credenciales y pre-start ejercitados** — el inventario estaba virgen (0 activos, la hoja `MovimientosActivo` ni existía). ⚠️ Un fallo: **`traslado` guardaba el ID crudo en el historial** mientras `salida` guardaba el nombre resuelto, así que el mismo sitio aparecía como «proyecto: PRJ-0005» al llegar y «proyecto: prueba2» al salir (v306 se aplicó a una función y no a la otra). Aguantaron depreciación, QR, los 4 movimientos, baja+reactivación, los 4 estados de credencial, `compliance`, y el pre-start con su PDF. Tres falsas alarmas mías comprobadas antes de tocar (depreciación de 2 años, `APP_URL` que la UI ya avisa, y las categorías que viven en el código). NO ejercitados a propósito: `notify_expiring` y `near_miss=YES`, que escriben a personas reales |
| v349 | ⚠️ **El LaTeX de v309 volvió en la pantalla de Costos** (`Llevas **0** de 10,000`, con los `$` comidos y los `**` literales). El guardián de v309 solo miraba los argumentos LITERALES de `st.*`, y aquí la cadena se arma antes en una variable → **ciego**. Chequeo nuevo por AST: cualquier f-string del repo con 2+ `$` sin escapar. Salieron 4 — una es el hash PBKDF2 (falso positivo, exento) y **las otras 3 están en Costos**, incluida la que yo escribí en v343. Dos de ellas estaban latentes (solo salen con costos y presupuesto). Lección: cuando el mismo fallo reaparece, preguntar por qué el chequeo no lo vio |
| v348 | Anuladas las 3 colillas de $0 que quedaban (`NOM-0001`, `NOM-0004`, `NOM-0005`): la lista de nóminas pasa de 5 filas a **2 con dinero real**. ⚠️ Ninguna cifra se movió — la comprobación de que se anuló lo correcto. + el aviso de tarifa faltante **distingue homónimos** (`fijiofgjei (conductor)` vs `fijiofgjei (fijiofgjei)`): salía dos veces el mismo nombre para dos personas distintas, justo en el mensaje que dice a quién arreglar. Cuarta aparición del patrón (v151/v306/v319) |
| v347 | ⚠️ **Una nómina anulada bloqueaba reemitir el periodo**: `generar` contaba las anuladas como duplicados, así que anular y regenerar no creaba nada y **la app no podía reemitir la nómina de nadie** (principio de v340: si se puede deshacer, tiene que poder rehacerse). Con eso arreglado se corrigió **`NOM-0002`** —8,69 h de trabajo real emitidas en $0— reemitiéndola a $347,60 + super 11,5% (el mismo del lote). ⚠️ La ganancia del grupo pasa de $210,42 a **−$177,15**, y esa es la cifra CORRECTA: el costo estaba subestimado en el trabajo que no se pagaba. Y la conciliación de v313 ya decía «sin explicar $347,60» — el dato llevaba ahí señalando el fallo |
| v346 | **Nóminas ejercitadas** (última ruta sin recorrer) y **decisión del usuario sobre la tarifa 0**: quien no tiene tarifa ya NO recibe una colilla de $0 — se salta, se le nombra y se dice dónde arreglarlo. ⚠️ Reversible por construcción: como no deja fila, al poner la tarifa y regenerar el mismo periodo entra sin duplicar (probado). Motivo con evidencia: en la hoja real está `NOM-0002`, 8,69 h de trabajo emitidas en $0. Aguantaron el salto de duplicados, el neto (aportes que no descuentan), marcar pagada, la colilla PDF y anular. De regalo, dos confirmaciones en vivo: el **reparto por medianoche de v164** (6,37 + 1,63 = 8,0 h) y la **retención de impuesto**, que nunca se había calculado en esa hoja |
| v345 | **Ejercitado el fichaje y las facturas** (lo que v344 dejó aparte). ⚠️ Hallazgo: `estado_cobro` miraba `parcial` ANTES que `vencida`, así que **un abono de $1 sacaba a la factura de «vencida» para siempre** — y el indicador rojo del resumen, el P&L y el estado de cuenta del cliente solo cuentan las `vencida`, o sea que ese saldo no lo veía nadie (el caso clásico: el cliente paga un anticipo y desaparece). Ahora vencida gana a parcial; los tres consumidores ya sumaban `Total − Cobrado`. Lo demás aguantó contra datos reales: jornada que se abre sola, cambio de proyecto, cierre con hora explícita (3,0 h), `sin_asignar_indet`, GST, cobro parcial, tope al cobrar de más, PDF y anulación. ⚠️ Y un falso hueco descartado a tiempo: la factura sin vencimiento solo era posible saltándose la UI |
| v344 | **Ejercitar las escrituras contra la hoja real destapó 4 fallos que ningún test vio.** ⚠️ El peor es mío y llevaba 4 versiones vivo: `projects._invalidate` llamaba a `fn.clear()` con `fn` inexistente (al reescribirlo en v339 quité el bucle y dejé el cuerpo), el `except Exception: pass` se tragaba el NameError y **la caché no se limpiaba nunca** → tras guardar un proyecto la pantalla enseñaba el valor viejo hasta 120 s. Igual en `roster`. + las cachés DERIVADAS (`group_expenses`, `over_budget`, `gaps_by_group`, `projections_by_group`) tampoco se limpiaban. ⚠️ Y la auditoría de v342 vigilaba `MargenPct`, que **no existe** —la columna es `MargenMO`—, así que el margen era el único campo sin rastro; encima `update_project` anotaba cambios que descartaba en silencio y devolvía «Proyecto actualizado.» igual. Guardián nuevo: ningún CAMPO_CLAVE sin columna real, ninguna invalidación con nombres libres, probado contra el código roto |
| v343 | **Órdenes de compra: el dinero COMPROMETIDO deja de ser invisible.** Entre que se pide el material y llega la factura, el proyecto salía dentro de presupuesto con el dinero ya comprometido — el sobrecosto se descubría cuando ya no se podía hacer nada. Nuevo `core/orders.py` (hoja `Ordenes`): al recibir una orden se crea sola su fila en `Gastos`, así que **el costo real sigue teniendo UNA fuente** (v310). ⚠️ `project_cost.total` NO se mueve (probado contra la fórmula anterior en 6 casos); lo comprometido va aparte, con el aviso **«vas dentro, pero con lo pedido te pasas»**. ⚠️ Se marca recibida ANTES de crear el gasto: al revés, un fallo a mitad daría **dos gastos por la misma compra**; así queda un hueco VISIBLE (`sin_gasto`) con botón para completarlo. + órdenes atrasadas (obra parada esperando material) |
| v342 | **Rastro de cambios**: `CreadoPor` decía quién creó una fila y **nada decía quién la cambió** — «¿quién puso este margen al 0%?» no tenía respuesta. Nuevo `core/auditoria.py`, acotado a lo que mueve dinero (margen, tarifa, presupuesto, fechas, avance, personal): **1 escritura por edición y solo si algo cambió de verdad** (`40` y `40.0` no generan histórico), con el historial en el detalle del proyecto. ⚠️ La anotación va FUERA del try del guardado: el cambio del usuario no se pierde porque falle el apunte. ⚠️ Leer el historial NO crea la hoja (regla v145). ⚠️ El chequeo de nombres libres cazó un NameError real: `projects_ui` importa `theme` **dentro de cada función**, y mi primera comprobación dio un OK falso porque `ast.walk` encontraba el import local de OTRA función |
| v341 | **Comparación con el periodo anterior en el P&L**: $1.710 de ganancia no dice nada hasta saber qué dio el mes pasado. `finance.periodo_anterior/variacion/pnl_comparado` + `_kpi_card(var=)` → ▲/▼ con el % bajo cada cifra, con **0 llamadas nuevas**. ⚠️ En un COSTO subir es PEOR (se invierte el sentido, si no gastar más salía en verde) y ⚠️ sin base no se muestra un «+∞%». Verificado con datos reales: agosto $1.710,42 vs julio −$1.500 → +214% |
| v340 | ⚠️ **Archivar era un viaje sin vuelta.** El usuario archivó un cliente y desapareció: `Activo=NO` + las 5 llamadas usando el default que los oculta, sin casilla para verlos ni botón para restaurar. El dato seguía en la hoja, pero la app no podía enseñarlo. Es el fallo que v149 resolvió para proyectos y que nunca se aplicó a las entidades nacidas después — al buscarlo apareció **el mismo en los activos dados de baja**. Los dos con casilla «Ver también…», contador de ocultos y botón Restaurar/Reactivar |
| v339 | **El techo de cuota de Sheets.** Medido: 15 de las 19 llamadas de una sesión eran `values/{hoja}`, una por hoja. Nuevo `core/hojas.py` las trae todas en UNA `values.batchGet` → sesión de **19 a 6 llamadas** y el recorrido por todas las secciones cuesta **0**; el lote es `cache_data`, o sea compartido por proceso. ⚠️ Tres trampas: un rango inexistente tumba el lote entero (se piden solo las hojas que existen), cada `_invalidate` debe tirar TAMBIÉN el lote (si no, «lo guardé y no sale») e import perezoso para no ciclar con `timeclock`. Las escrituras siguen leyendo frescas. Verificado idéntico fila a fila en las 19 hojas contra lectura fresca |
| v338 | Fix de v337: la URL no se actualizaba en las 4 secciones **sin** sub-pestañas (Home, Fichaje, Inventario, Contactos), por un `session_state.get("")` que lanzaba y que mi propio `except` se tragaba. Parecía intermitente porque Finanzas y Proyectos sí funcionaban |
| v337 | **Estado en la URL**: la dirección refleja sección · sub-pestaña · proyecto abierto, así que se puede mandar «mira esta pantalla». El slug se deriva del ID (que lleva emoji y no se toca), solo se lee en la primera pasada, solo se escribe si cambia, y no pisa el `?activo=` del QR. ⚠️ Valida contra las secciones **del rol**: una URL de otra sección no da acceso |
| v336 | **Cierra el plan de diseño**: la curva S se traza de izquierda a derecha al entrar (aquí la animación ES el dato: el tiempo se lee como tiempo) y las cifras KPI entran al recalcularse, que era la señal que faltaba al cambiar un filtro. ⚠️ `animar=False` por defecto porque el MISMO SVG va al PDF por svglib — probado que, quitando estilo y clases, el de pantalla es **idéntico carácter a carácter** al del PDF. ⚠️ El navegador de automatización pide *reduced motion*, así que ahí no se ve animar: verificado por CSSOM que el mecanismo está entero |
| v335 | Las etiquetas de `st.metric` dejan de truncarse con elipsis y usan dos líneas — «Dispon…» no informa de nada. ⚠️ Solo actúa en ventana estrecha: a 1440 px todas caben en una línea |
| v334 | ⚠️ **Invierte v331**: la versión del topbar se lee **AL IMPORTAR** el módulo. Leerla fresca la volvía más engañosa, porque el fichero VERSION se actualiza con el deploy pero los módulos `core.*` ya importados siguen en memoria — medido: la app anunciaba v333 sirviendo el `theme.py` de v332. Ahora, si la barra dice v334, se está ejecutando v334 |
| v333 | **Escala tipográfica**: de **31 tamaños distintos para 102 usos** (24 fuera de escala, residuos de escribir en `rem`) a **9 pasos elegidos**. Medido antes de tocar: 30 de 31 valores se mueven ≤1 px. Literales en px, no variables CSS (parte del CSS va a correo y a PDF). Los 137 `font-size=` de los SVG no se tocan: son la escala del dibujo técnico. + guardián que bloquea cualquier tamaño fuera de la escala |
| v332 | **Estado de carga visible**: barra superior animada + contenido atenuado mientras Streamlit re-ejecuta (medido: 520 ms de rerun, opacity 0.55, sin residuo en reposo). ⚠️ Y el hallazgo: **el atenuado de v326 nunca funcionó** — la regla decía `div[data-testid="stMain"]` y stMain es un `<section>`. Auditados TODOS los selectores del kit contra el DOM real apareció un segundo muerto **desde v283**: `stMetricLabel` es un `<label>`, así que el estilo de las etiquetas de métrica jamás aplicó. Los 18 selectores dejan de depender del nombre de etiqueta |
| v331 | El indicador de versión del topbar **mentía tras un deploy**: `@st.cache_data` sin ttl lo congelaba durante la vida del proceso y Streamlit Cloud recarga en caliente sin reiniciar. Visto en vivo: app v330, barra v324 |
| v330 | **El buscador ya busca.** Era el fallo con más coste de credibilidad de la auditoría: 641 px del control más prominente, inertes desde v190. Busca proyectos (nombre/ID/cliente/ubicación), personas (nombre/login/email) y trabajos, con ranking (ID exacto → empieza por → contiene), sin acentos ni mayúsculas, mínimo 2 letras, y los archivados marcados. **0 lecturas nuevas a Sheets** (las 3 fuentes ya estaban cacheadas). Cada resultado reusa los deep-links existentes; la caja se limpia por bandera aplicada antes de instanciar el widget (regla v111) |
| v329 | `theme.texto_seguro()`: un color de ACENTO deja de usarse como color de TEXTO. `_kpi_card` teñía borde y valor con el mismo color, así que el ámbar daba un importe a **2.85:1** («Por facturar»). El borde conserva el color vivo; el valor usa su equivalente legible (6.16:1). En el kit, no en cada una de las ~20 llamadas |
| v328 | Subtítulo de la banda de marca **3.2 → 4.58:1**. Solo el de pantalla: los otros 5 usos de ese tono van sobre el azul oscuro (PDF, email, cajetín), donde da 9.1:1 |
| v327 | ⚠️ **El 40 % de los botones nunca recibió el estilo del kit**: los selectores usaban combinador HIJO y un botón con `help=` va envuelto en `stTooltipHoverTarget`. Medido: 10 de 25. Viene de v283. + indicadores del resumen a 38 px (su `min-height:0` anulaba la altura del kit) |
| v326 | **Arreglos de la auditoría de diseño**: contraste WCAG en indicadores (2.26→4.62), ámbar de texto (3.18→5.65) y texto de diagramas (3.43→5.57); **96 px de ancho recuperados** en todas las pantallas (el relleno lateral heredaba los 5rem de Streamlit y nunca se había decidido); botones a 38 px; y las primeras transiciones propias de la app — acuse de recibo al pulsar, que ataca los 2,9 s de silencio tras un clic, con `prefers-reduced-motion` |
| v325 | El aviso «sin tarifa» mezclaba **dos cosas distintas**: a quien le falta la tarifa (se arregla en Usuarios) y a quien **ya no está dado de alta** (cuenta eliminada — no hay fila donde ponerla, y el aviso mandaba a un callejón sin salida). Nueva `auth.claves_conocidas()` —una sola definición, 0 lecturas nuevas, y degrada a «sí existe» si falla la lectura para no acusar de baja a nadie— consumida por `group_hours` (`existe`), `labor_breakdown` y `conciliacion_mo` (`sin_tarifa` / `de_baja`). El **indicador del Resumen cuenta solo lo accionable**. Caso real: `fijiofgjei` es la cuenta `conductor` borrada en v163 con fichajes huérfanos |
| v324 | **Revisión en el Cloud con datos reales.** ⚠️ El proyecto con **0% de avance y 6 días de retraso** mostraba el mensaje **más tranquilo** de los tres (*«justo el ritmo que hace falta»*): con `ritmo_real = 0` la guarda anti-división-por-cero deja `factor = None`, que es *falsy*, y las dos ramas de aviso se saltaban. ⚠️ Y el proyecto **pasado de fecha no mostraba NADA**: su aviso era **código muerto** porque la guarda exigía `ritmo_nec is not None`, que es `None` justo cuando la fecha ya pasó (lo cazó el test al replicar el orden real de los `if`). ⚠️ La **conciliación gritaba «$1.262,80 sin explicar»** con el periodo por defecto, y no era un descuadre: horas y nóminas se filtran por fechas distintas (v309), así que en una ventana corta no cierra por construcción — con «Todo» cierra al céntimo. + el importe restado ya no lleva el signo duplicado. **Confirmado en vivo**: v322 tenía un caso REAL (AGR-0001, 2 miembros archivados: `0 elev · 0%` → `2 elev · 21%`) y v323 no movió ningún número |
| v323 | Los helpers duplicados **no eran cosmética**: eran 5 implementaciones DISTINTAS de `_num`, 2 de `_parse_date` y 7 de `_col_letter`, y la divergencia era el fallo. ⚠️ **Cualquier importe con separador de miles (`1,234.56`, como Sheets formatea el dinero en AU) se leía como $0,00 en silencio** en las cinco variantes — costos, facturas, nóminas e inventario. Auditada la hoja real en SOLO LECTURA: 0 casos hoy (latente), así que unificar está probado que no cambia ningún número existente (5000 importes, 0 diferencias). Todo a `core/num.py`. + Una fecha no-ISO (`16/08/2026`) se leía `None` y esa factura **desaparecía del P&L**. + `_next_id` de facturas/clientes/inventario leía de la caché de 120 s y **podía repetir un ID** (y el ID es la identidad). + `notify_expiring` hacía N escrituras seguidas en CADA login de admin → 1 `batch_update`. + de los 128 `except: pass`, los 7 que se tragaban una escritura ya dejan rastro — el peor, `timeclock.get_sheet`: si la cabecera no migra, cada dato se guarda **en la columna de al lado** |
| v322 | **Revisión de código**: 8 funciones muertas (−124 líneas, 0 referencias en todo el repo, verificado por AST porque grep cuenta mis propios comentarios) + 27 imports sin usar en 20 archivos. ⚠️ Y el hallazgo de fondo: **archivar un ascensor cambiaba en silencio el avance consolidado, la fecha de entrega y la curva S de todo el edificio** — las 6 consultas de miembros de una agrupación heredaban el "ocultar archivados" de v149, que es correcto para una lista y falso para un conjunto (misma familia que v145/v310/v321: archivar no des-construye el ascensor). ⚠️ Ese arreglo introdujo una regresión que cazó la verificación: el editor de miembros no mostraba al archivado y al guardar lo **desagrupaba solo**; y mi guardián solo veía una de las dos formas de escribir la consulta, así que la tarjeta de agrupación contaba menos elevadores que su propio % |
| v321 | Rentabilidad: **el margen se edita en la propia tabla** (antes te mandaba a Datos de cada proyecto estando ya en la lista de márgenes) + columnas **Ya facturado / Por facturar** para contrastar el estimado con la realidad + las obras sin movimiento a un desplegable. ⚠️ Fix de un fallo de v310: el margen propio de un proyecto **archivado** se ignoraba y usaba el default del grupo, porque `group_expenses` pasó a incluir archivados y el mapa de márgenes no |
| v320 | **Barrido de títulos duplicados** por AST sobre las 26 vistas de la shell: quitados 4 (Gastos, Horas, Rentabilidad, Facturas). ⚠️ Las vistas del campo y Pre-Start NO se tocan: cuelgan de secciones SIN sub-pestañas, así que su título es el único. + Horas: el KPI «sin asignar» mostraba 1,2 h y un 3% cuando el dato **no era calculable** (hay más horas en obras que de jornada) — ahora pone «—» y explica quién fichó a proyecto sin abrir jornada; «Costo M.O.» pasa a «M.O. cargada a obras» (v313) y fuera los proyectos con 0,0 h |
| v319 | Nóminas: la lista dejaba pasar **4 colillas de $0** (esas personas no tienen tarifa/hora — `generar` lo detecta y solo se veía al generar), **dos filas homónimas indistinguibles** (nuevo `auth.etiqueta_usuarios`, la regla del ID aplicada a personas) y **gente con horas sin nómina**. Ahora las tres se avisan, con botón a Usuarios. + columna Tarifa/h, totales, filtro de periodo y KPIs con contexto. ⚠️ 4º título duplicado encontrado (v212/v291/v314) |
| v318 | La torta de composición del costo pasa de fija a **herramienta** (4ª): el usuario la vio fija en v317 y prefirió pedirla al mirarla. La pantalla arranca en la rejilla de pendientes |
| v317 | **Resumen financiero como torre de control**: rejilla fija de 8 pendientes clickeables (patrón del Resumen del día) + 3 herramientas que se abren debajo (patrón del Panel) + los 3 KPI con línea de contexto; la torta se queda fija. Cuatro indicadores NUEVOS que no estaban en ninguna pantalla: sin facturar, horas sin nómina, sin tarifa, sin margen. Y `resultado_por_proyecto` — ⚠️ acumulado a propósito — que revela que prueba1 se facturó **al costo** (margen 0%), no los $1.710 que sugería el mes natural |
| v316 | Estado/Datos/Costos/Archivos pasan del radio con bolitas al **segmentado del kit** (`cpxseg_`, la pieza de v292): 412 px, con marco y el activo resaltado. Igual en 📋 Mis proyectos del campo. ⚠️ NO se copió la fila de botones del Panel: aquella es un acordeón de herramientas opcionales (se pueden cerrar todas) y estas son secciones excluyentes; medida, además, salía a 1120 px estirados. Los IDs con emoji y el matching, intactos |
| v315 | Cabecera del detalle de proyecto: avance y horas se meten DENTRO de la tarjeta (barra fina + las dos cifras en una línea), fuera los dos `st.metric` de 660 px, la barra de progreso duplicada y el separador. **Medido: 196→104 px**. ⚠️ Era lo prometido en v311 y no entregado entonces |
| v314 | Ruta del día, cabecera: fuera el **título duplicado** (`_sub_header` ya lo pinta — 3ª vez que pasa, ver v212/v291), el selector de fecha deja de ocupar 1340 px y gana **saltos de día ◀ ▶** (aplicados antes de instanciar el widget, regla v111), y la caption se va al `help`. ⚠️ Además: en **fin de semana** todos salían «sin plan» sin explicación, porque la rejilla del roster es Lun–Vie; ahora se dice |
| v313 | **Conciliación de mano de obra**: nuevo `finance.conciliacion_mo` con la cadena `cargado a obras → −horas cobradas sin pagar → +horas pagadas sin cargar → base → +aportes de ley → costo real`, que cierra exacto con los datos reales. Las cinco pantallas dejan de llamar "costo" a cosas distintas («lo que pagas» vs «lo que cargas a obras») + avisos de horas imputadas sin jornada, gente sin tarifa y proyectos con margen 0%. ⚠️ Se verificó que el modelo del usuario (paga la jornada + ley; carga a la obra lo imputado; cobra eso × margen) ya estaba bien implementado: faltaba el puente entre las dos cifras |
| v312 | Fix de v310: las tarjetas KPI mostraban la barra del escape (`COSTO ACTUAL \$3,145`). `theme.dinero` escapa el `$` para MARKDOWN, pero `_kpi_card` emite HTML crudo. Ahora `theme._esc` deshace ese escape, así que cualquier pieza HTML del kit lo arregla sola y no puede repetirse |
| v311 | Detalle de proyecto (Estado) reordenado: lo corto (titular + KPIs) va arriba a ancho completo y abajo se enfrentan dos bloques largos (actividades \| alarmas), en vez de dejar la columna izquierda vacía ~800 px. El **cronograma pasa de 760 a 1280 px de lienzo** (área de barras 430→950) — ⚠️ `vw` es parámetro y el default sigue en 760 para NO cambiar los informes PDF. «Tocaba hoy» + «En curso ahora» se fusionan. ⚠️ Fix: el titular mostraba `**` literales porque el markdown no se procesa dentro de HTML; y el iframe del gráfico era 18 px más corto que el SVG, así que recortaba el pie |
| v310 | ⚠️ **Gastos decía `COSTO ACTUAL $0` con $1.500 en la torta**: `group_expenses` ocultaba los proyectos ARCHIVADOS (v149) y esas compras no contaban en ningún costo, presupuesto ni alerta. Auditada la hoja real (solo lectura): los $1.500 eran de PRJ-0001, archivado. Ahora hay UNA definición (todas las compras del grupo), el P&L usa la misma, las compras sin proyecto se avisan en vez de perderse, y se quitó el gráfico de barras que duplicaba la torta. Sin periodo a propósito (rompería «% consumido»). ⚠️ De paso: el test de v309 daba OK en falso porque el mock ignoraba `incluir_archivados` |
| v309 | ⚠️ **Fallo en las 3 pantallas de dinero**: dos `$` en la misma cadena hacen que Streamlit la renderice como **LaTeX** — en Facturas la línea de Subtotal/Impuesto/Total salía como fórmula ilegible, en Nóminas igual, en el P&L desaparecían los `$` y el `metric` de Facturas perdía el símbolo. Nuevo `theme.dinero()` (formatea + escapa, idéntico al formato anterior) en los 5 sitios + guardián AST. Y el **P&L gana periodo** (mes/trimestre/año/todo), desglose por cliente, composición del costo y enlaces a Facturas/Nóminas |
| v308 | Fichaje: ⚠️ **fix de un fallo introducido en v306** — se guardaba la ETIQUETA del desplegable (`prueba (PRJ-0007)`) como nombre del proyecto en la hoja; ahora va el nombre real. Y «Cambiar de proyecto» excluye el actual por ID (antes te ofrecía el que ya tenías abierto). + tarjeta **Esta semana** (lunes→hoy, sin lecturas nuevas) + el estado pasa de tarjeta KPI a franja + Jornada y Proyecto lado a lado (botones de 1350→523 px) |
| v307 | Ruta del día aprovechada: ⚠️ el hueco blanco era `st_folium` dibujando a **500 px FIJOS** dentro de un bloque de 1110 (medido dentro del iframe) → `use_container_width=True` (también en HOME). Mapa + tarjetas de sitio en orden de recorrido, con «Cómo llegar» y la ruta completa a Google Maps (`ordenar_ruta`/`gmaps_dir_url` existían desde v270 y solo las usaba el campo). La tabla gana **horario** y **estado real** (🟢 fichado aquí / 🔴 fichó en X / ⚠️ sin fichar) sin lecturas nuevas. KPIs activos con contexto. Bug de camino: la persona cuya obra no tenía ubicación **desaparecía de la tabla** |
| v306 | **Identidad por ID.** Los 3 sitios que aún casaban proyectos por NOMBRE pasan a ID vía `projects.etiqueta_proyectos` (Panel→Asignar hacía desaparecer un homónimo del desplegable; **Facturas enlazaba el importe al proyecto equivocado**; Inventario guardaba el nombre y ahora guarda `PRJ-####`). + **Tipo de proyecto** (Instalación/Delivery/Ripout/Otro): ⚠️ solo Instalación genera el cronograma estándar — antes un delivery nacía con 11 actividades falsas que ensuciaban avance, SPI y el radar. + **El ID a la vista** en tarjeta, lista (1ª columna), detalle y buscador. Guardián AST permanente contra volver a indexar proyectos por nombre |
| v305 | Resumen del día: los 9 indicadores pasan de 3 filas a **2 (5+4)** → bloque 232→192 px (del original 304). El alto del botón ya estaba en su suelo (35 px), así que la palanca era el nº de filas. Medido: en UNA fila solo caben con ≥1180 px de contenido y por debajo se parten 4 etiquetas. Guardián nuevo: `zip` trunca en silencio si una fila tuviera más elementos que columnas |
| v304 | Menú lateral: la cascada por fin se ve — nivel 1 pegado a la izquierda (8 px) y en seminegrita, nivel 2 a 30 px, más pequeño y más fino. ⚠️ El menú salía **centrado**: el CSS de v229 había dejado de aplicar porque Streamlit metió un `span` flex centrado dentro del botón, y porque `font-size`/`font-weight` puestos en el botón nunca llegan al `<p>` (los dos niveles salían a 16 px/peso 400, activo incluido). Además, los huecos del resumen del día bajan de 10 a 5 px (bloque 246→232), con la regla acotada al expander por `key` |
| v303 | HOME del admin: las 3 tarjetas KPI ganan una línea de contexto (con datos que `_kpis` ya calculaba → 0 lecturas nuevas) y se mudan a la cabecera de la columna del mapa; el resumen del día se comprime sin perder estructura ni nombres (estado al título, pista al `help`, indicadores 52→35 px); el fondo pasa a 3 columnas mapa \| proyectos \| agenda (muere el toggle); y el hueco sobre el buscador baja a 1rem. ⚠️ De paso se arregla un fallo real: los "→ Ir a" del resumen llevaban displays en vez de IDs → 7 de 9 abrían **Agrupaciones** y "Sobre presup." abría **Horas**. La banda azul del cliente NO se toca (decisión del usuario) |
| v302 | Panel: vuelve el atajo "Toda la semana (Lun–Vie)" como check que manda sobre el selector de días y lo deshabilita; sin `st.rerun` para no cerrar el popover |
| v301 | Panel: cabeceras de días y "Persona" más grandes y centradas; se puede planificar VARIOS días de una (multiselect de días en el popover); y un trabajo ya asignado se puede eliminar sin perder el historial (se marca ELIMINADO y `trabajos_idx` lo sigue resolviendo) |
| v300 | Trazabilidad: CLAUDE.md (navegación por rol, árbol de módulos, tabla de versiones, bloque de trampas de verificación), prompt del agente y memoria puestos al día tras la migración v296-v299 |
| v299 | **Fase 3 de la migración: se BORRA la navegación vieja.** Fuera de `app.py` la cabecera COPEX, los `_L_*`, `_HERR`, la cadena `_nav`, `_NAV_DISPLAY`, el radio `main_nav`, su if/elif de enrutado y `_nav_pending` (421→284 líneas), más `auth_ui.render_owner_panel`. ⚠️ ANTES se convirtieron sus 2 flujos VIVOS a `_admin_nav_pending` («Abrir proyecto» tras el survey y «Reabrir cálculo en su herramienta»; `_CALC_NAV` pasa a apuntar a las sub-pestañas reales) — borrar solo el lector los habría dejado sin efecto en silencio (patrón v140). La shell deja de ser condicional y un rol desconocido cae a la nav del CAMPO (menor privilegio) |
| v298 | Fase 2: el PROPIETARIO a la shell. Sus 6 pestañas de Administración pasan a sub-secciones con la MISMA clave `owner_sec` (el deep-link de `survey_ui` sigue vivo); el despacho se extrae a `auth_ui.render_owner_seccion` para que las dos shells lo compartan sin duplicar; su campana AGREGA alertas de todos sus grupos vía `owner_digest` |
| v297 | Fase 1: el CAMPO a la shell. `home_ui` gana secciones POR ROL (`_SECCIONES_ROL`), el rol se resuelve dentro (`_rol()`) para no cambiar ninguna firma. El campo gana el botón ← Atrás y la trampa del gesto de retroceso en móvil (que solo tenía el admin). Su campana pasa a mostrar SOLO sus credenciales (antes: las de todo el grupo). La versión va al topbar |
| v296 | Limpieza: se borra la shell VIEJA del admin («🛠 Mi grupo»), inalcanzable desde v190 — `render_group_panel` + `_L_GRUPO` + su rama de nav + los `_gruposec_pending`. ⚠️ NO se borró la nav vieja entera: propietario y campo aún dependían de ella (verificado que sus navs quedaban idénticas) |
| v295 | Panel: celda con varios trabajos legible (la hora SOLO si difiere del turno estándar; con 3+ → primero y contador), días de la semana centrados y con aire, y el catálogo permite EDITAR y ELIMINAR trabajos. ⚠️ El borrado se NIEGA si el trabajo está asignado en algún roster (rompería el histórico: el tablero resuelve nombre/color por ID) → criterio de v149 |
| v294 | Panel: la celda con choque Y certificado enseña los DOS anillos (v292 daba prioridad al rojo y eso ESCONDÍA el cert); fuera el chevron de las celdas vacías (⚠️ NO es un `<svg>`: es `span[data-testid=stIconMaterial]`, Material Symbol de fuente); muestra de color como cuadradito; cabecera "Persona" alineada |
| v293 | Panel: «En vivo» y «Plan vs real» se unen en UNA herramienta **Cumplimiento** (5→4 en la fila). Lo vivo va en CADA FILA (plan + real + cronómetro en una línea). ⚠️ Se rescató el caso «fichado en jornada pero SIN imputar obra», que solo existía en «En vivo» porque `proyectos_por_usuario_dia` descarta los fichajes sin proyecto |
| v292 | Panel: el tablero MARCA dónde está el conflicto (anillo rojo = choque de turno, ámbar = certificado que bloquea; `_radar_scan` devuelve además `marcas` por celda) y el toggle Tablero/Disponibilidad pasa a segmentado del kit (`cpxseg_`, con `@supports selector(:has())` para degradar) |
| v291 | Panel: quitado el título duplicado (`_sub_header` ya pinta "Planificación · Panel") y las 4 bandas de chrome (nav de semana, cobertura, toggle, caption) se unifican en UNA barra; el hint pasa al `help` del toggle |
| v290 | **Cuota de Sheets**: arranque frío de 30 → 12 lecturas (índice del libro en 2 llamadas —`worksheets()` + `values_batch_get` de las cabeceras— en vez de 2 por hoja), TTL de caché 30→120 s y reintento acotado ante 429/5xx. ⚠️ NO se usó `gspread.BackOffHTTPClient`: la librería lo marca "not production ready" y encadena hasta 254 s de sleep |
| v289 | Fix: un hipo de la API de Sheets tumbaba la app entera. `heartbeat` estaba blindado en el `_get_login_ws` y en el `update_cell`, pero NO en la lectura del medio → el 429 subía hasta `app.py`. Guardas en `heartbeat`/`validate_session`/`start_session`; el bloqueo por sesión ocupada se distingue del fallo de API (`auth.SESION_OCUPADA`) |
| v240 | Estética (fase 3g): las 5 herramientas técnicas (Plomada/Rieles/Buffers/Belting/Pre-Start) — header principal, botón Calcular/Generar, subtítulos de diagramas/resultados y descargas de PDF a iconos Material. Quedan sueltos el "¿No tiene plano?"/"Plano cargado" (secundarios) y survey_ui |
| v239 | Estética (fase 3f): cabeceras internas del detalle de proyecto a iconos Material — Datos del plano, Fotos, Archivos, Cumplimiento de certificados, Quién ha trabajado aquí, Tocaba hoy, En curso ahora, Próximo hito (caption), Avance del conjunto. Solo display |
| v238 | Estética (fase 3e): auth_ui — panel del propietario (radio owner_sec y del group panel grupo_sec vía format_func, IDs/deep-links intactos), headers (Administración, Manuales, Rieles), expanders/botones (zona horaria, subir/quitar manual, agregar/editar riel, eliminar grupo). Con esto auth_ui queda migrado |
| v237 | Estética (fase 3d): auth_ui — ficha 360° de Usuarios (radio Acceso/Contacto/Credenciales/Su trabajo/🗑 vía format_func, IDs intactos), expanders (Agregar/Editar credencial, Crear usuario, Matriz), botón Vincular Telegram, headers. Los botones Activar/Desactivar 🟢🔴 se dejan (usan color de estado a propósito) |
| v236 | Estética (fase 3c): botones de projects_ui a iconos Material (Guardar→save, Borrar→delete, Reabrir→replay, Crear proyecto→add_circle, Cargar en Survey→sync, Descargar/Exportar→download). Labels de botón/form_submit/download_button — display puro. Verificado que las 3 variantes renderizan Material |
| v235 | Estética (fase 3b): expanders y checkboxes de la sección Proyectos a iconos Material — "Nuevo proyecto"/"Nueva agrupación"/"Cargar recibo"/"Subir documento"/"Agregar-eliminar actividad" (icon= param), "Ver archivados" (admin+owner), y headers "Plano del elevador"/"Ubicación en el mapa". Solo display |
| v234 | Estética (fase 3a): los radios de sub-navegación del detalle de proyecto y de Mis proyectos (campo) muestran iconos Material vía format_func (las opciones siguen siendo el ID con emoji → sin romper matching); headers de Gastos/Horas del grupo a iconos |
| v233 | Estética (fase 2): el chrome del admin a iconos Material — campana (🔔→notifications), barra de usuario (rol 👑/🛠/🔧, grupo 🏢, cerrar sesión 🚪) y se quitó el 🔎 del buscador. Monocromo |
| v232 | Estética (fase 1): la NAVEGACIÓN del admin cambia los emoji por iconos Material profesionales en azul COPEX (sidebar: secciones + sub-pestañas + hub). Sub-pestañas decopladas en (id interno con emoji / display con icono) para no tocar los deep-links. Los estados 🟢🔴🟡 se dejan por ahora |
| v231 | Herramientas: página de entrada (hub) — nueva sub-pestaña "🧰 Inicio" (default) con una tarjeta por herramienta (qué hace + Abrir). Punto de partida claro al entrar a Herramientas. Versión simple (sin el chequeo del plano, que queda para después) |
| v230 | Nav: desplegar ≠ navegar — tocar una sección con sub-pestañas ahora SOLO despliega sus hijas en el sidebar (no carga la 1ª sub-pestaña de una); la carga ocurre solo al tocar una hija. Estado `_admin_expanded` separado del activo |
| v229 | Navegación del admin: el sidebar pasa a 2 niveles (acordeón) — bajo la sección activa se despliegan sus sub-pestañas indentadas y clickeables, para ir directo a una de nivel 2 desde la barra izquierda. El nivel 1 pasa de radio a botones-menú (CSS st-key, verificado). Se quitó el radio horizontal de sub-pestañas del contenido |
| v228 | Cartera de Proyectos: toggle de vista "🃏 Tarjetas \| 📋 Lista". La Lista es la tabla clásica (proyecto por fila; columnas estado/avance con barra/cliente/fechas/% presupuesto/usuarios/situación/alertas) y es clickeable (seleccionar fila abre el proyecto). Las tarjetas siguen como default |
| v227 | Ficha de usuario (sub-pestañas): 📊 Su trabajo pasa a ACTIVA — los proyectos asignados son botones que abren el proyecto + "horas por proyecto" de esa persona; 🔑 Acceso peinada a doble columna (contraseña\|tarifa). Contacto y Credenciales ya estaban sólidas, no se tocaron |
| v226 | 👷 Usuarios: panorama activo — fila de salud del equipo (personas/activos/sin contacto/credenciales por vencer o vencidas) + tabla CLICKEABLE (Usuario·Nombre·Activo·Contacto·Credenciales·Tarifa) que al tocar una fila abre la ficha 360° de esa persona (antes: tabla pasiva + desplegable aparte). Deep-links de HOME/Finanzas Horas manejados. La ficha no cambió |
| v225 | Torta de gasto por rubro CENTRADA: antes la leyenda (flex:1) se estiraba a todo el ancho y el monto/% se iban al borde ("todo separado"); ahora torta+leyenda se agrupan con justify-content:center y la leyenda se acota a 300px (márgenes iguales, verificado) |
| v224 | Finanzas → Gastos: diagrama de TORTA del gasto por rubro (Mano de obra + cada categoría de compra), debajo de los dos bloques de barras. Hecho con CSS conic-gradient (sin dependencias nuevas) + leyenda color·rubro·$·%. Verificado en vivo que st.markdown no lo recorta |
| v223 | Cartera de proyectos (📊 Proyectos): cada tarjeta ahora muestra ANTES de abrir — nombre, estado + % avance (barra real), cliente, fechas inicio→fin, % presupuesto ejecutado (⚠️ si se pasó), nº de usuarios y alertas; se abre con botón «Abrir». Borde izq por salud. % presupuesto de group_expenses (1 lectura cacheada); se quitaron las horas. Opción A elegida por el usuario tras ver un mockup |
| v222 | Fix: al tildar "mantener la sesión" y CERRAR/REABRIR la app (PWA) pedía login otra vez — la cookie se guardaba como "de sesión". Ahora se escribe persistente con max-age vía window.parent.document.cookie desde render_user_bar (no en _do_login, que hace rerun y la descartaría). Verificado en vivo: CookieStore confirma persistent + expira a 7 días |
| v221 | Login: "Mantener la sesión iniciada en este dispositivo" ahora es un check OPCIONAL (por defecto SIN tildar). Antes la cookie de 7 días se guardaba siempre; ahora solo si se tilda → si lo activas, no reescribes usuario/contraseña en tu dispositivo; sin tildar, la sesión dura solo la pestaña |
| v220 | Asignar personal (deploy 2/2): al asignar campo a un proyecto, aparecen AUTOMÁTICAMENTE en el planificador, en ese proyecto, Lun–Vie entre FechaInicio y FechaFinEst (todo el rango, solo celdas vacías — no pisa OFF ni otro proyecto). Al desasignar se limpian sus días de ese proyecto. Escritor eficiente (1 batch_update + 1 append_rows) para no disparar el rate limit |
| v219 | Asignar personal más inteligente (deploy 1/2): al asignar campo a un proyecto se avisa si el usuario YA está en otro proyecto (y hasta cuándo), y se pueden tildar los certificados que EXIGE el proyecto (campo CertsReq) → aviso + marca 🔴 quien no cumple / 🟡 por vencer, con tabla viva de cumplimiento del equipo en Estado. (Falta feature 2: auto-poblar el planificador entre fechas del proyecto) |
| v218 | Planificación: un PROYECTO se asigna DIRECTO en el tablero (aparece 🏗 en el desplegable) — ya no hay que crear un "trabajo" que lo enlace (todo proyecto es un trabajo en sí mismo). El catálogo queda solo para lo NO-proyecto (entregas/cursos/traslados) y pierde el campo "enlace a proyecto". Color de proyecto automático y estable (hashlib). Histórico compatible |
| v217 | Planificación: el tablero pasa a ser EDITABLE EN SITIO — cada celda es un popover coloreado donde asignas/editas ahí mismo (asignación + nota + "aplicar a toda la semana" + abrir proyecto); una celda vacía (＋) también asigna. Se quitó el editor por-persona de abajo. + línea de "cobertura del día" (en obra / sin asignar / OFF) sobre el tablero. Popover+color verificado en vivo (st.popover acepta key en 1.57) |
| v216 | Horas por usuario × proyecto (el dato ya existía, solo faltaba mostrarlo): matriz "persona × proyecto" al final de ⏱ Horas (usa el por_proyecto de group_hours), y bloque "👷 Quién ha trabajado aquí" (persona·horas) en 📊 Estado del proyecto, junto a las alarmas (labor_breakdown sin el costo) |
| v215 | Finanzas: Gastos con "Reparto" y "Compras por categoría" en doble columna + tabla de proyectos clickeable (→ abre el proyecto); Horas con tabla de personas clickeable (→ abre la ficha) |
| v214 | Agrupaciones clickeables (mismo patrón que Proyectos): tocar una tarjeta abre su tablero directo; se quitaron los selectores "Abrir" y "Eliminar" (Eliminar movido dentro). Cuidando no anidar expanders |
| v213 | Costos: "Reparto del costo" y "Compras por categoría" en doble columna; recibos clickeables que muestran la foto inline (antes: tabla redundante + solo descarga) |
| v212 | Fix: el % de avance salía 2 veces en el detalle (cabecera + KPI "Avance real"); se quitó la KPI redundante de la pestaña Estado |
| v211 | Detalle de proyecto (📊 Estado) en doble columna: "cómo va" (titular + KPIs) a la izquierda, alarmas a la derecha; ritmo, desglose y cronograma a ancho completo abajo |
| v210 | Fix: "➕ Nuevo proyecto" estaba doblemente anidado (yo lo envolví en un expander cuando ya tenía el suyo) + tenía el de ubicación anidado dentro. Ahora un solo expander, ubicación inline |
| v209 | Proyectos: filtro rápido arriba de la cartera (búsqueda por nombre/cliente + chips Todos/Retraso/Adelanto/En pausa), en doble columna |
| v208 | Estética de la cartera de proyectos: rejilla de 2 columnas (más densa, menos vacía) + texto alineado a la izquierda + nombre en negrita |
| v207 | Proyectos: la cartera ahora es clickeable (tarjetas-botón con avance/salud, mismo lenguaje que HOME) → tocar abre el detalle directo; se quitó el selector "Abrir proyecto" y el form Nuevo proyecto quedó plegado |
| v206 | El pin del mapa (y la lista de Proyectos en HOME) ahora abren un RESUMEN del proyecto en la columna derecha, sin salir de HOME; desde ahí un botón "→ Ver proyecto completo" |
| v205 | Fix móvil: el gesto de retroceso ya no cierra la app; se redirige al botón "← Atrás" interno (JS que atrapa el back con history.pushState + popstate → click en el botón). Validar en el teléfono |
| v204 | Botón "← Atrás" arriba-izquierda de la barra superior del admin: vuelve a la sección anterior (historial multi-nivel), se desactiva cuando no hay a dónde volver |
| v203 | HOME: la columna derecha ahora se comparte entre Agenda y Proyectos con un toggle arriba (cambio rápido sin salir de HOME). Vista Proyectos = lista compacta clickeable con avance (barra en el fondo del botón), retraso/adelanto y alarmas, ordenada por urgencia |
| v202 | Cronómetro(s) de fichaje EN VIVO en el sidebar (jornada + proyecto), visibles desde cualquier sección, solo cuando estás fichado. Admin y campo. Nuevo timeclock_ui.render_sidebar_chrono |
| v201 | Estética: logo del login ~40% más pequeño ([2,1,2]); quitada la zona negra superior en la vista del admin (cabecera de Streamlit transparente + menos padding arriba, sin ocultar el botón de desplegar el sidebar) |
| v200 | Más elementos activos: indicadores del resumen con NOMBRE visible; PINES del mapa clickeables (abren el proyecto); filas de la AGENDA clickeables (abren la ficha de la persona). Reusa _prjsel_pending y gp_fichasel para el deep-link |
| v199 | Resumen y métricas ACTIVOS: los 9 indicadores y las 3 métricas son botones clickeables → al tocar un indicador muestra el detalle ("cuáles") + botón "→ Ir a [sección]" que navega a resolverlo. Mecanismo de navegación programática en la nav del admin (home_ui.navegar/_aplicar_nav_pending) |
| v197 | Fusión KPIs + resumen: quitadas las tarjetas "En riesgo" y "Alarmas" de arriba (estaban duplicadas con la rejilla de indicadores del resumen); arriba quedan solo las métricas del portafolio (Activos·Avance·Horas). Un solo bloque coherente |
| v196 | Resumen del día con estructura FIJA: línea de estado + rejilla de 9 indicadores siempre igual (3 columnas, número 0 incluido) + detalle desplegable + la lectura de IA en su propio desplegable colapsado y bajo demanda (ya no se genera automático). Antes los chips aparecían/desaparecían según los datos |
| v195 | Fix: el mapa de HOME no mostraba proyectos recién creados (filtraba solo "En progreso"; un proyecto nuevo es "Planificado"). Ahora muestra los activos (Planificado + En progreso) → "Proyectos activos" |
| v194 | El pin de ubicación también al CREAR el proyecto ("➕ Nuevo proyecto"): nace con coordenadas. create_project acepta lat/lng. (El Survey ya no crea proyectos desde v135, así que era el único flujo). Completa v193 |
| v193 | Ubicación de proyecto con búsqueda de dirección + pin en mapa (folium/streamlit-folium, sin API key): guarda Lat/Lng por proyecto (columnas nuevas), se fija editando el proyecto → 🗺 Ubicación; HOME lee las coordenadas guardadas (respaldo: geocode del texto). Nuevo core/location_ui.py |
| v192 | Centro de control del grupo (KPIs + resumen del día) reubicado en HOME, arriba del mapa y la agenda (era lo único que había quedado sin reubicar al reorganizar la nav del admin) |
| v191 | Integrado TODO el contenido existente en la nueva nav del admin: Fichaje, Planificación (Tablero+Usuarios), Proyectos (Proyectos+Agrupaciones), Finanzas (Gastos+Horas), Herramientas (5 técnicas+Pre-Start). Inventario y Contactos quedan placeholders. Reconexión de funciones ya probadas |
| v190 | Nueva navegación del ADMIN (primer pase): menú lateral de iconos (Home/Fichaje/Planificación/Proyectos/Finanzas/Inventario/Herramientas/Contactos) + barra superior (buscador + campana de alertas) + HOME real (mapa de proyectos en ejecución + agenda de hoy del roster). Los 6 apartados restantes son placeholders. Solo rol admin; nuevo core/home_ui.py |
| v189 | Formulario de credenciales sin clutter: "Especifica" solo si Tipo=Otro, "Clase" solo para licencia de conducir (Tipo movido fuera del st.form para poder condicionar). Cierra la revisión de acceso+credenciales |
| v188 | Fix login persistente: refrescar (F5) ya no desloguea. El componente de cookies se creaba nuevo cada rerun y el login bloqueaba con sleeps que impedían procesar el mensaje del navegador con la cookie. Ahora CookieManager único por sesión + sin bloqueos (deja que el componente dispare su rerun) + no re-restaurar tras logout |
| v187 | Avisos de vencimiento de credenciales desacoplados del panel: antes solo se disparaban al abrir 🔧 Usuarios de campo (frágil); ahora corren al login de cualquier admin/propietario (app.py), 1×/día/grupo, deduplicado. No había scheduler; se eligió la opción pragmática sin infra (job programado queda anotado como futuro) |
| v186 | Credenciales: fila de KPIs (total · vigentes · por vencer · vencidas) arriba de la tabla + botones de descarga agrupados en un expander "Documentos" |
| v185 | Fechas de credenciales con calendario (`st.date_input`) en vez de texto libre: guarda siempre ISO, así un typo ya no desactiva en silencio la alerta de vencimiento. Precarga datos viejos; form de Editar ahora refresca los campos al cambiar de credencial (key con ID) |
| v184 | Panel del propietario (👑 Administración → Usuarios) unificado a la ficha 360°: se gestiona cada persona desde un solo lugar (Acceso/Contacto/Credenciales/Su trabajo) en vez de 3 desplegables sueltos, igual que el administrador. La ficha gana modo `owner` con Rol+Grupo. Borrado código muerto (`_field_contact_ui`, `_USER_COLS`) |
| v183 | Belting (revisión + diagrama replanteado): proyecto al diagrama/PDF + tarjetas KPI (HQ·HGP·nº) + el diagrama ahora respeta el SIGNO del DSTS (cabina por encima/debajo del FFL de referencia, a escala ampliada) en vez de ponerla siempre debajo en posición fija. Cierra las 5 técnicas |
| v182 | Corte de buffers: diagrama replanteado. HKP/HKPR son HOLGURAS (sticker↔buffer), no alturas. Ahora dibuja el sticker (arriba) + línea HKP de diseño + rebanada roja = lo que se corta del borde del buffer para pasar de HKPR a HKP. Casos corte/sin-corte/revisar |
| v181 | Corte de buffers (revisión, igual que rieles): el nombre del proyecto va al diagrama y al PDF (estaba disponible y no se usaba) + tarjetas KPI (HKP · nº buffers · nº a revisar) en vez del st.success plano. Ya era por buffer |
| v180 | Corte de rieles (revisión): el nombre del proyecto va ahora al diagrama y al PDF (estaba disponible y no se usaba, mismo fallo que plomado) + tarjetas KPI en vez de st.success planos. Ya era por elevador y los diagramas se rehicieron en v177/v178 |
| v179 | Plomadas por elevador (la plantilla DBP/d1/d2 es una sola del shaft; el BSR se mide por elevador y define el encaje/verificación) + arreglo de integración (el nombre del proyecto estaba hardcodeado vacío, ahora va a los diagramas y al PDF) + estética (tarjetas KPI, el encaje como acción no como muro de números) |
| v178 | Corte de rieles: Caso 1 deja de inventar el orden de los rieles (la app solo tiene conteos, no secuencia) — la pila A se dibuja como UN bloque; y el Caso 2 se rehace como esquema de rieles (cabina RZ/RO + contrapeso RF/RB, corte marcado arriba, alturas ilustrativas) en vez de las barras comparativas |
| v177 | Corte de rieles Caso 1: el corte se dibujaba arriba pero se corta el PRIMER riel (el de abajo); ahora se marca al pie de la columna (rojo recorta / verde añade) con una línea de piso. Solo el dibujo; los números no cambian |
| v176 | Guardar un cálculo de herramienta: el campo ya no elige el proyecto de una lista — se guarda AUTOMÁTICO en el proyecto donde fichó (ID primero, nombre de respaldo), con un expander "¿otro proyecto?" de emergencia; sin fichar o admin/propietario, la lista. Mismo criterio que plano/Mis proyectos/Pre-Start |
| v175 | El plano se muestra POR HERRAMIENTA (las 5 por igual): antes el mensaje lideraba con "17 parametros" del survey y el resto salia suelto. La extraccion ya leia todo (NS/riel/HQ/HGP/HKP/LFKK/LFGK, verificado en 2 planos reales); ahora plan_data.por_herramienta + una tabla muestran que le da el plano a cada herramienta (Survey/Plomadas/Rieles/Buffers/Belting) con ✓ o ⚠️ falta |
| v174 | Fix: refrescar la pagina deslogueaba. El componente de cookies (extra-streamlit-components) no entrega las cookies en el primer run tras el refresco, y render_login se rendia al primer intento (_cookie_tried); ahora reintenta unos reruns antes de mostrar el login, asi el login persistente de v107 por fin sobrevive al refresco |
| v173 | Zona horaria POR GRUPO (core/clock.py): Streamlit Cloud corre en UTC, asi que los registros salian ~10 h corridos. Ahora cada grupo tiene su zona (Grupos.Zona, la fija el propietario; default Australia/Sydney) y todos los datetime.now()/date.today() (~40 sitios) pasan por clock.now()/today() que resuelve la zona del grupo con zoneinfo (per-sesion, sirve multi-país). +tzdata |
| v172 | PDF del Pre-Start reescrito para calcar el template CI Liftworx: formulario blanco y negro con bordes, bandas grises por seccion, recuadros de notas, la respuesta marcada resaltada en negro, los 4 checks reubicados a la sub-tabla "Circle one" de la Seccion 3, y asistentes en 3 pares. Marca = grupo, textos en español |
| v171 | Pre-Start seccion 2 (Issues/hazard/near miss): el campo de texto libre pasa a estar SIEMPRE visible (antes solo aparecia al marcar YES), para describir un issue/hazard aunque no sea un near miss formal; si marca YES sin describir, se avisa |
| v170 | Pre-Start del campo: preselecciona el proyecto donde fichó (lo primero que hace el campo es fichar; señal fuerte y mostrada, sigue cambiable — no el "primero de la lista" que evitó v139), "Time" pasa de texto libre a st.time_input, y la inicial del asistente se autocompleta del nombre |
| v169 | Planificacion: la celda del tablero pasa a ser un BOTON nativo (st.button coloreado por la clase st-key-<key>, Streamlit>=1.39, verificado en vivo) que abre el proyecto en la MISMA sesion, sin recarga. Reemplaza el enlace HTML de v168 (que podia recargar). El board del campo sigue siendo HTML de solo lectura |
| v168 | (reemplazado en v169) Planificacion: celda como enlace `<a href="?abrir_prj=">` + handler de query param en app.py |
| v167 | (revertido en v168) Planificacion (roster): boton por cada proyecto enlazado en la semana (el board es HTML, no clicable como st.dataframe); navega con _prjsel_pending + un _gruposec_pending nuevo que cambia la seccion del grupo a Proyectos antes de instanciar el radio |
| v166 | Archivos: la descarga pasa a la propia tabla — se selecciona la fila (st.dataframe on_select, lazy: solo se baja la elegida) y aparecen descargar/reabrir/borrar; ademas un boton de descarga bajo cada foto que reutiliza los bytes ya bajados para la miniatura. Se quita el selector aparte de v165 |
| v165 | Archivos: una sola lista buscable (busqueda por nombre + filtro por tipo con contadores + orden) en vez de dos sub-secciones planas (Documentos y Calculos) con tres selectores; unifica documentos + PDF de calculos + plano casando cada calculo con su toolrun por DriveID (sin duplicar), y reduce a la vez galeria, tabla y descargador |
| v164 | Fichaje del campo: las horas se reparten por dia natural (medianoche) — antes una sesion que cruzaba medianoche se contaba entera en el dia de entrada, falseando "Jornada de hoy" y el reporte "Hoy"/"Semana" del admin (evidencia: 3/16 fichajes reales cruzan medianoche). El olvido de clock-out se cierra a la hora que el usuario indica (no "ahora", que registraba las horas fantasma de la noche). group_hours(Todo) queda identico |
| v163 | Se elimina el rol conductor: tras el fichaje unificado (v150) era un subconjunto del campo; se borra el rol, su vista de proyectos y todas sus ramas (nav, creacion de usuario, prompt del agente), y se elimina el unico usuario conductor de prueba. Quedan 3 roles: propietario/administrador/campo |
| v5 | Extractor: CRLF fix, caso D valor-antes-label, sin pdfplumber |
| v6 | BC_CALC + FB_MAX_BACK constraint en optimizer |
| v7 | BC eliminado de inputs usuario, calculado automáticamente |
| v8 | Diagramas ASCII en reporte PDF (secciones 2, 3, 7) |
| v9 | Caso 2: OR/OL naranja cuando requieren corte, sin rojo por debajo límite |
| v10 | Extractor: visitor_text con posiciones XY evita concatenación anotaciones CAD; TKS rango (5,150) |
| v11 | Extractor: two-pass (visitor + plain text) para recuperar BKF1/BKF2 caso-D |
| v12 | Optimizer: 4-step flow, FB extra wall, fb_applied tracking, MAX_OFF_RL = max(DIF_WR,DIF_WL) |
| v22 | Fix MAX_OFF_RL: incluye max(0,DIF_OR) y max(0,DIF_OL) para barrido correcto cuando OR/OL exceden límite |
| v23 | Fix wall limiting: FB extra evade el muro → quita SKIP duro y excluye OR/OL del nivel evadido del conteo |
| v24 | Refactor mayor: highlighting compartido (core/highlighting.py), excel guarda/restaura config completa, validate_inputs, max_by_col en optimizer, bs_logic refactorizado, diagramas ASCII corregidos, fix MAX_OFF_RL display, tiebreaker consistente |
| v25 | Optimizer: Paso 2b — cuando fb_extra_applied y \|RL\| > FRAME → SKIP (apertura cabina tapada por pared limitante) |
| v13-14 | Wall limiting: DIF OR/OL con MAX, fb_applied en soluciones y log |
| v16 | Fix OR/OL: fuera de límite = v > LIMIT, DIF = MAX − LIMIT, CUT = v − LIMIT |
| v17 | Fix OR/OL highlight Caso 1: v > LIMIT en ambos casos; rojo en Caso 1, naranja en Caso 2 |
| v18 | Fix optimizer _apply: OR -= rl, OL += rl (signos correctos) |
| v19 | Fix wall limiting: todas las comparaciones OR/OL corregidas a v > LIMIT |
| v20 | Estado inicial: sección 6.2 en reporte + "Niveles incumplidos" en app y reporte |
| v21 | Sección 1.3 en reporte: condiciones y configuración del proyecto (NS, pared, ctrl, omega) |
| v25 | Optimizer Paso 2b: SKIP frame_opening cuando fb_extra y \|RL\| > FRAME |
| v26 | Asistente IA experto (chat_agent.py) en pestaña/sidebar, con contexto del survey |
| v27 | Chat: reglas de confidencialidad (no revela lógica interna/propietaria) |
| v28 | Fix FB extra: posición absoluta FS−TSW (no fb+extra); corrige sub/sobre-aplicación |
| v29 | Fix FB extra preciso: extra = max(0, FS−TSW − excess_FR/FL_piso_limitante); 3 casos |
| v30 | Interpretación IA integrada en el PDF admin (7 secciones por Claude) |
| v31 | UI: branding COPEX, versión visible, chat en sidebar desplegable |
| v32 | chat_agent: system prompt con conocimiento físico completo |
| v33 | Notificación email al calcular (proyecto, ingeniero, resumen) vía Gmail SMTP |
| v34 | Email adjunta plano PDF del usuario + matriz survey CSV |
| v35 | Archivo VERSION: la versión se actualiza sola en cada deploy (la lee app.py) |
| v36 | Diagrama físico SVG (transversal + longitudinal) con datos de la solución |
| v37 | Fix diagramas: components.html en app + embebidos en PDF con svglib (sin markers) |
| v38 | Interpretación obligatoria: bloquea el PDF si falla (avisa configurar API key) |
| v39 | Diagrama planta por piso (vista superior) con matriz solución; fix color invertido |
| v40 | Pestaña Líneas de plomada (plumb.py + plumb_ui.py): tabla + diagrama SVG |
| v41 | Pestaña Fichaje (clock in/out) con Google Sheets: nombre+PIN, proyecto, horas |
| v42 | Fix fichaje: PIN como texto (RAW + numericise_ignore) conserva ceros a la izq. |
| v43 | Fichaje: autenticación real por PIN contra hoja Usuarios (rechaza no autorizados) |
| v44 | Fix fichaje intermitente: cachear conexión; is_configured solo revisa secrets |
| v45 | Fichaje: quitar registro visible en la app (privacidad); usuarios solo fichan |
| v46 | DOS informes: usuario (cliente, descargable) + admin (completo, auto-email) |
| v47 | Fase 1 móvil: CSS responsive (columnas se apilan), meta-tags PWA, fix BOM en VERSION |
| v48 | Robustez: anthropic import diferido (no tumba la app si la librería falla) |
| v49 | PWA completo: manifest + íconos COPEX + static serving (enableStaticServing) |
| v50 | Favicon COPEX como page_icon (imagen, lado servidor) |
| v51 | Gestión de proyecto: cronograma Gantt + curva S (auto por NS + cortes/shaft), editable, en app + informes |
| v52 | Pestaña Corte de rieles: lee LFKK/LFGK del PDF; Caso 1 y Caso 2 (encima/debajo) |
| v53 | Login con roles (propietario/administrador/campo); PBKDF2; primer-uso crea propietario |
| v54 | Multi-empresa: grupos aislados; paneles propietario/admin; fichaje por login+grupo (sin PIN); logo COPEX en login |
| v55 | Fix mezcla de pestañas: quitar st.tabs anidados en paneles (radio) |
| v56 | Fix DEFINITIVO mezcla: navegación con radio (solo renderiza sección activa) en vez de st.tabs |
| v57 | Plomadas: carga de PDF autocompleta BKS/TKSW/SF1/SF2/BS/SG/TG del plano |
| v58 | Plomadas: renombrar V1-V6 por nombres propios (plomos de riel, paredes teóricas/reales) |
| v59 | Plomadas: inputs inician en 0 (sin valores residuales de ejemplo) |
| v60 | Consolidar conocimiento (CLAUDE.md v47-v59) + agente IA con nuevas funciones |
| v61 | Plomadas ENCAJE: paredes reales V4/V6 fijas + conjunto rígido se centra (BSR>BS) o sacrifica Z→Omega (BSR<BS) |
| v62 | Plomadas: eje CERO = pared real izquierda (V4=0); shaft real de 0 a BSR |
| v63 | Integrar plomado al survey (input LengthTemplate; plomado definitivo con rl/fb del survey, en app + ambos informes); pestaña manual intacta |
| v64 | Plomadas: distancias de verificación en campo (plomo↔pared real) como cotas + tabla, en app y ambos informes |
| v65 | Gestión de proyectos: projects.py/projects_ui.py (Sheets), panel admin, "Guardar como proyecto" en survey, "Mis proyectos" para campo, agrupaciones con peso |
| v66 | Fix segfault: requirements pineado a majors estables + Python 3.12 en Streamlit Cloud |
| v67 | Fichaje: el proyecto se elige de desplegable de proyectos asignados (horas atadas al proyecto) |
| v68 | Limpieza (revisión completa): borrar carpetas muertas, imports sin usar, except:/f-strings, print→logging, projects append_rows batch |
| v69 | Fix rate-limit Sheets (APIError 429): cachear lecturas de proyectos con st.cache_data(ttl=20) + invalidar al escribir |
| v70 | Proyectos: curva S real vs planificada + línea HOY en el detalle del admin (real_scurve, project_schedule) |
| v71 | Proyectos: curva real se corta en HOY (upto_day) + barras del Gantt se llenan por %avance |
| v72 | Proyectos: proyección avance-vs-fecha (earned value: desvío hoy, días adelanto/retraso, fin proyectado por SPI) |
| v73 | Propietario ve todos los proyectos de todos los grupos (👑 Administración → 📁 Proyectos) |
| v74 | Documentos por proyecto en Google Drive (drive_store.py, hoja Documentos, permisos por rol, auto-archivo plano+matriz+informe) |
| v75 | Sesión única por cuenta (licencias, "primero gana"): token+heartbeat en Login; 2do login bloqueado; opción forzar |
| v76 | Fix curva S real: llega al avance real total en HOY (reparte sobre ventana real, no la planificada) |
| v77 | Notificaciones email + Telegram al asignar proyecto a usuario de campo (notify.py, contacto en Login) |
| v78 | Notificaciones: sección en la barra lateral (luego revertida en v79) |
| v79 | Contacto (email+Telegram) OBLIGATORIO para campo y gestionado SOLO por el admin; bloqueo duro; tabla usuarios sin hash |
| v80 | Fix: guardar proyecto borraba las actividades (rate limit por ~16 update_cell) → update_project usa batch_update (1 llamada) |
| v81 | Fix: list_users no devolvía Email/TelegramChatID → el admin veía "contacto falta" con datos ya cargados |
| v82 | Admin agrega/elimina actividades del cronograma con recálculo automático del % y de la curva S |
| v83 | Tabla de actividades totalmente editable (data_editor): nombre/días/peso + reordenar; guardado en 1 batch |
| v84 | Catálogo de rieles (hoja Rieles, gestión propietario); lee código CAR GUIDE RAIL del plano → autocompleta RAIL |
| v85 | Fix: RAIL = altura del diente desde la espalda (no el ancho) |
| v86 | Nueva pestaña Belting: DSTS = HGPR − HGP − HQ/1000 por elevador; HQ del plano, HGP/HGPR manual; diagrama |
| v87 | Belting: HGP también se autocompleta del plano (2º valor de la fila HKP/HGP) |
| v88 | Sistema de alarmas por proyecto: campo reporta problema→admin, admin cambia→campo; in-app + Telegram, resolver/apagar, badges |
| v89 | Respaldo: CLAUDE.md (estructura + módulos nuevos) + agente IA al día (belting, rieles, proyectos, docs, alarmas, sesión única) |
| v90 | Banco de manuales para el agente (BM25 en Python puro); pre-cargados KONE Monospace + S5500; cita manual/sección/página |
| v91 | Panel propietario 📚 Manuales (subir/quitar self-service en Drive + hoja Manuales, PDF/ZIP) + agente separado por rol (campo/gestión) |
| v92 | Reducción de llamadas a Sheets: handle de worksheet cacheado (get_sheet) + auth list_users/get_user cacheados + ttl 20→30 (menos APIError 429) |
| v93 | UI: sidebar sin "Valores del PDF" ni leyenda de colores; orden de pestañas por rol (panel del rol primero; propietario sin Fichaje) |
| v94 | UI "Mi grupo" como centro de control: banda de marca + KPIs (activos/avance/en riesgo/alarmas/horas) + cartera de tarjetas + nav única de 3 |
| v95 | Drive: `drive_store.is_available()` (chequeo OAuth cacheado) → un solo aviso limpio al archivar si Drive está desconectado (en vez de 3 errores crudos) |
| v96 | Nueva herramienta 🛡 Corte de buffers: lee HKP del plano (1er valor de HKP/HGP), N buffers + HKPR real, CutBuffer = HKP − HKPR |
| v97 | Nueva pestaña 🦺 Pre-Start diario (Daily Pre-Start CI Liftworx digitalizado): checks + asistentes → PDF (marca=grupo) archivado en Drive+hoja PreStarts; near miss=YES abre alarma |
| v98 | Ubicaciones enlazadas a Google Maps (maps.py, URL de búsqueda sin API key): detalle de proyecto, Mis proyectos, PDF+input del Pre-Start, notificación de asignación |
| v99 | Vista de lista: ubicación (Maps) en tarjetas del admin + tabla del propietario (LinkColumn); tarjetas marcan retraso (borde rojo + badge ⏰ días) vía `_delays` |
| v100 | Proyecto: campos Instrucciones particulares + Inducciones (links) al crear/editar; links enviados por Telegram/email a los campo asignados; visibles dentro del proyecto |
| v101 | Agente admin con radar del grupo (admin_digest): "Resumen del día" al ingresar (pendientes: retrasos/alarmas/vencimientos/near miss/sin asignar/sin contacto) + agente responde portafolio, recomienda, recuerda vencimientos, redacta |
| v102 | Fix: NS se lee del plano (NUMBER OF STOPS) al cargar el PDF; default de init 6→2 (ya no queda pegado en 6) |
| v103 | Rol conductor (2 relojes: jornada general + segmentos por proyecto, columna Tipo) + cronómetro en vivo para todos + reporte admin de horas del grupo (Mi grupo → ⏱ Horas) |
| v104 | Credenciales/tickets por usuario (White Card, Forklift, Dogging/Rigging, licencia…): vencimiento+estado, foto/documento a Drive, radar en Resumen del día, avisos email/Telegram a admin+usuario; usuario ve las suyas (🎫 Mis credenciales) |
| v162 | Mis proyectos (campo): sub-pestañas (Avance/Avisos/Recibos/Archivos como el admin) + el avance en UNA tabla editable con guardado en batch, y las fechas reales de inicio/fin se registran solas (inicio al pasar de 0, fin al llegar a 100) en vez de texto libre |
| v161 | Tablero de cuadrilla — plan vs real: el admin ve por dia lo asignado contra lo fichado (🟢 donde tocaba / 🔴 en otro sitio / ⚠️ sin fichar), solo para trabajos enlazados a un proyecto. Feature completa (v159 base + v160 campo + v161 plan-vs-real) |
| v160 | Tablero de cuadrilla: el campo ve el board completo (su fila resaltada) en 📋 Mis proyectos con su asignacion de hoy destacada, y en el fichaje un atajo «fichar a tu asignacion de hoy» cuando enlaza a un proyecto |
| v159 | Tablero semanal de cuadrilla (base): catalogo de Trabajos (numero/nombre/color/enlace opcional a PRJ) + seccion 📅 Planificacion del admin con rejilla coloreada como el board, editar semana persona a persona y copiar semana anterior |
| v158 | Pre-Start: el contenido que se capturaba (checks, asistentes, notas) por fin se ve en el historial con semaforo por check; y ya no se puede firmar sin leer (los checks arrancan sin respuesta, hay que responder cada uno) |
| v157 | RAIL sale en 0 al cargar el plano desde el proyecto: el plano da el CODIGO del riel y faltaba resolverlo a su altura por el catalogo; extraer_todo ahora guarda rail_altura y los mapas de survey/plomada lo vuelcan a RAIL |
| v156 | Cargar el plano en un proyecto ya creado (📐 Datos del plano): subir el PDF por Documentos no extraia a PlanoJSON, asi que las herramientas no lo veian; ahora hay un control que sube Y extrae, y «plano» sale del uploader generico |
| v155 | El Survey ya no pide proyecto/cliente/ubicacion/ingeniero a mano: eran entrada duplicada (el proyecto que alimenta ya los trae); se toman del proyecto elegido y alimentan el informe igual |
| v154 | El Survey es una herramienta tecnica mas (las 5: survey, plomado, rieles, buffers, belting); el Pre-Start se separa de ellas en el nav por ser seguridad de obra, no una herramienta |
| v153 | Usuarios de campo: ficha 360 por persona (acceso, contacto, credenciales y su trabajo —proyectos, horas, recibos— en un solo sitio) en vez de elegir al usuario en 3 desplegables distintos; se adapta al rol |
| v152 | Gastos del grupo: presupuesto y proyeccion al terminar (existia desde v144 y no se usaba), KPIs, alerta de los que se saldran al ritmo actual, y separar proyectos con/sin presupuesto; barras en vez de bar_chart grises |
| v151 | Horas del grupo: costo de mano de obra por persona (horas x tarifa), KPIs del grupo, reparto por proyecto en barras, y el «sin asignar» deja de mostrar ceros falsos (marca «—» cuando el dato es indeterminado por fichar sin jornada) |
| v150 | Fichaje unificado: dos relojes (jornada + proyecto) para todos los roles, el proyecto siempre de una lista (el texto libre dejaba las horas sin atribuir), fuera Ubicacion (nadie la leia), resumen del dia, historial propio y clock_out en 1 llamada |
| v149 | Datos: archivar sustituye a borrar (borrar dejaba huerfanos documentos, pre-starts, alarmas y fichajes, y sin confirmacion), fechas con calendario (el texto libre falseaba el cronograma en silencio) y aviso de credenciales al asignar campo |
| v148 | Reabrir un calculo guardado en su herramienta: DatosJSON no tenia lector y ademas solo guardaba los resultados; ahora guarda tambien las entradas y se puede retomar un calculo |
| v147 | Archivos: datos del plano visibles en el proyecto, fotos de obra en galeria, quien subio cada documento y cuando, y la descarga deja de bajarse TODO Drive en cada render |
| v146 | Se elimina el paquete de obra (~225 lineas): no aportaba ni un dibujo que no estuviera ya en el informe del cliente, que ademas se archiva solo. Residuo de v126 vaciado por v129/v130/v134 |
| v145 | El fichaje guarda el ProyectoID: las horas y el costo de mano de obra dejan de perderse al renombrar un proyecto (regla unica ID-primero-nombre-de-respaldo); project_hours_bulk pasa a indexarse por ID en sus 8 call-sites |
| v144 | Pestaña Costos: proyeccion de cuanto costara AL TERMINAR (la barra solo avisaba al pasarse), mano de obra por persona, gasto por categoria (se calculaba desde v105 y se tiraba), curva de gasto acumulado apilada vs presupuesto y aviso de tarifas en 0 |
| v143 | Pestaña Estado: la brecha plan-vs-real se RELLENA (antes habia que deducirla comparando dos lineas), HOY cruza el Gantt, barras que marcan lo que tocaba y no arranco, proyeccion al ritmo actual + diagnostico (ritmo real vs necesario, que tocaba hoy vs que se hace, proximo hito) |
| v142 | Agrupaciones con cartera de tarjetas (entrega del conjunto, elevador critico, retraso, alarmas, horas y costo sin entrar) + creacion plegada + projections_by_group cacheado |
| v141 | Agrupaciones al reves (se crean los proyectos y luego se eligen al armar la agrupacion) + dashboard con fecha de entrega del conjunto, elevador critico, curva S consolidada, comparativa y alarmas |
| v140 | Se quita el doble selector de plano: el uploader de PDF pasa a expander plegado (plan B) y los textos describen el flujo real; era residuo de v137 |
| v139 | Auditoria de los 38 desplegables: los 4 que BORRAN pasan a sin-preseleccion + confirmacion, y los 6 que escriben en un proyecto tampoco preseleccionan; los de configuracion se dejan igual |
| v138 | Los selectores de proyecto ya no abren uno arbitrario al entrar (8 lecturas que nadie pidio); al campo se le preselecciona el proyecto en el que ficho |
| v137 | El plano se lee UNA vez al crear el proyecto (columna PlanoJSON) y alimenta las 5 herramientas: el campo ya no sube el PDF — su proyecto sale del clock-in, el admin lo elige en la herramienta |
| v136 | Extraccion del plano 2.9x mas rapida (230s -> 79s): los 6 extractores comparten una sola lectura cacheada del PDF; resultados verificados identicos |
| v135 | ARQUITECTURA: el survey deja de crear proyectos y pasa a alimentarlos como una herramienta mas; el proyecto se crea en Mi grupo/Administracion y genera su cronograma del NS |
| v134 | Fix de 36 versiones: los PDF de Pre-Start (v97) y de calculos (v129) eran INVISIBLES en Documentos para todos los roles + el campo ya puede bajar el paquete de obra y ver los calculos |
| v133 | Agente IA al dia: desconocia 11 funciones (todo desde v96) y no sabia guiar por la interfaz; ahora tambien navega por rol. Quitada toolruns.list_group (huerfana) |
| v132 | Detalle de proyecto reorganizado: 11 secciones en scroll unico -> 4 pestañas (Estado/Datos/Costos/Archivos) con cabecera fija |
| v131 | Mi grupo: historial de calculos de herramientas en el detalle del proyecto (la hoja Calculos se escribia desde v129 pero nadie la leia) |
| v130 | Herramientas 2/2: Plomadas, Rieles y Belting con resultados persistentes (fix v110), diagrama nuevo de corte de rieles, PDF y guardado en el proyecto |
| v129 | Herramientas 1/2: hoja Calculos (cada uso alimenta el proyecto) + PDF y guardado comunes + fix del bug v110 en las 4 + Corte de buffers completo con diagrama nuevo |
| v128 | Plano UNICO de la sesion (se subia el mismo PDF en 5 herramientas) + paquete de obra descargable desde el detalle del proyecto (survey_calc.recalcular) |
| v127 | Survey: aviso de credenciales vencidas y contacto faltante al asignar campo (fuera del form) + notificacion deja de fallar en silencio + numeracion 1-7 eliminada |
| v126 | Survey lote 3: paquete de obra en 1 PDF (field_pack.py) + boton que abre el proyecto recien creado (navegacion real) + aviso de proyecto duplicado |
| v125 | Survey lote 2: extraido de app.py a core/survey_ui.py (1243 lineas, cuerpo identico); app.py 1650->321 lineas; imports huerfanos podados |
| v124 | Survey lote 1: el log del optimizador pasa a ser solo del propietario (era visible para campo) + leyenda de color en las tablas (faltaba desde v93) |
| v123 | Plomado con tratamiento CAD: planta a escala real (antes vertical 1.7x distorsionada) + isometrica con los hilos cayendo + detalle 3D + ficha de replanteo + cierre di+DBP+dd=BSR + aviso de BS incoherente |
| v122 | Fix: los displays redondeaban a entero valores que el optimizador da en pasos de 0.5 mm (dos soluciones distintas daban la misma etiqueta); cotas con formato adaptativo `_mm` |
| v121 | Fix CRITICO geometria de los planos: FL/FR van al eje de rieles (cuerpo TK centrado), la cabina ya no se sale del hueco; apertura posicionada con OL/OR reales + marcos |
| v120 | Fix CRITICO: indentacion de v118 rompia las 2 fases del Survey (NameError sc2, matriz invisible, import de Excel inalcanzable) |
| v119 | Dibujos del survey rehechos: planta a escala real con cotas/achurado/cajetin + detalle ampliado automatico + ambos desplazamientos + vista isometrica del hueco |
| v118 | Fix: al cambiar de fase se perdian parametros/NS/config (Streamlit descarta widgets no renderizados) + el Excel ya no pisa los valores del PDF salvo que lo pidas |
| v117 | Fix: crash (AttributeError) tras 'Empezar un survey nuevo' — el reset borraba claves leidas por atributo |
| v116 | Informe del cliente rediseñado como presentacion: portada a sangre, pie con paginacion, nº de informe, veredicto, KPIs, glosario, alcance, conclusiones+firma |
| v115 | Survey pro: solucion activa elegible, resumen ejecutivo, checklist, filtro de pisos, validacion temprana, duplicar, comparar soluciones, exportar diagramas |
| v114 | Survey en 2 fases (Datos / Resultados) con salto automatico al calcular; config leida de session_state |
| v113 | Survey: marca de origen PDF/manual por campo + parametros agrupados + boton nuevo survey + aviso al reconstruir |
| v112 | Fix CRITICO: el import de Excel se repetia en cada rerun y pisaba los valores del PDF (faltaba guarda por archivo) |
| v111 | Fix: importar la matriz desde Excel fallaba (escribia claves de widgets ya instanciados) |
| v110 | Survey: los resultados dejan de borrarse al interactuar (render fuera del boton + aviso de calculo obsoleto) |
| v109 | Limpieza de codigo muerto (flujo PIN viejo + 6 funciones sin uso); sin imports muertos |
| v108 | Auditoria de llamadas #2: cachear open_sessions/group_hours (fichaje) + list_groups + group_expenses; escrituras siguen leyendo fresco |
| v107 | Lote 2: matriz de compliance + tarjetas y resumen multi-grupo del propietario + dashboard de agrupacion + reconstruir proyecto + briefing por Telegram/email + login con cookies + ronda de optimizacion |
| v106 | Fichaje identificado por USUARIO (no por nombre) + adelantos marcados + presupuesto al crear + graficas de costos + reenvio de inducciones al editar |
| v105 | Control de costos por proyecto: recibos (foto/PDF+valor+categoría, los cargan admin/campo/conductor) + mano de obra (tarifa/hora POR USUARIO) + presupuesto+alerta; reporte de gastos del grupo (💰 Gastos) con CSV; radar sobre-presupuesto |
