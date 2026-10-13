# Survey App — IngDACO/P1  
## Referencia completa para Claude (leer siempre al inicio)

---

## ⚠️ REGLA DE ESTE DOCUMENTO — leer antes de escribir acá

Este archivo se inyecta **entero, en cada turno, de cada sesión**. Su tamaño es presupuesto de contexto:
lo que se escribe acá se paga siempre, aunque nadie lo lea.

- **Las secciones por versión (`## ... (vNNN)`) van a `HISTORIAL.md`, NO acá.**
- Un deploy nuevo agrega como mucho **una línea** en «Últimas versiones desplegadas» (al final), y se
  borra la más vieja para que esa lista no crezca.
- Acá solo va **lo que sigue siendo verdad hoy**: cómo se despliega, cómo está armado, qué módulo hace
  qué, y las trampas de verificación. Si algo describe una decisión ya reemplazada o revertida, su lugar
  es `HISTORIAL.md`.

_Por qué la regla: el 19/09/2026 este archivo llegó a 1,07 MB (~300k tokens; la ventana son 200k) y mató
la sesión — la compactación ya no podía ni resumirse («Prompt is too long — automatic compaction failed»).
Se partió el 20/09/2026: 1,07 MB → ~80 KB._

## Links
- **GitHub:** https://github.com/IngDACO/P1 (rama: main)
- **Streamlit:** https://dwl6s39d7u3yfwfkbpcpah.streamlit.app/
- **Drive:** https://drive.google.com/drive/folders/1PK7znRaCGWcycDJ6neUJPy72TqwgSxQW

## Deploy (siempre hacer esto al terminar cambios)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& "C:\Users\diego\P1\backup_survey.ps1" -Version N -Mensaje "descripcion"
```
Hace: git push → ZIP → rclone Drive. Streamlit redeploy es automático.

⚠️ **El script vive DENTRO del repo desde el 20/09/2026** (antes suelto en el home, sin historial:
se arregló un fallo suyo y el arreglo no dejaba rastro en ningún sitio). El `$repo` sale
de `$PSScriptRoot`, así que no puede apuntar a otro árbol. Y **si el `git commit` falla,
aborta**: antes cantaba «GitHub OK» igual y el ZIP y el Drive salían sin haber subido
nada — pasó en v504. Ahora el OK lleva el SHA al lado.

⚠️ **Streamlit NO recarga los `core.*` al desplegar**: el `app.py` nuevo corría con los
módulos viejos en memoria, y en v535 eso TUMBÓ la app (`AttributeError`). Desde v536
`app.py`, antes de importar nada de la app, compara `VERSION` con `core._VERSION_CARGADA`
y, si no coinciden, descarta todos los `core.*`/`extractors.*` y los reimporta en esa
pasada. Si aun así el chip del topbar dijera la versión vieja: **Settings → Reboot app**
(el chip lee la versión AL IMPORTAR justo para delatarlo, `home_ui._VERSION`).

## Guardianes: la suite de verificación (`guardianes/`)
`verif_*.py` (afirmaciones) · `romper_*.py` (baterías de roturas) · `run_suite.py` (la
suite ENTERA, regla v385) · `doc_v*.py` (documentar una versión) · `ejercitar_*_real.py`
(contra la hoja real, método v344). Los de un solo uso, en `guardianes/sueltos/`.

```powershell
cd C:\Users\diego\P1\guardianes ; $env:PYTHONIOENCODING="utf-8" ; python run_suite.py
```
⚠️ Se corren con `cwd=survey_app` (lo hace el runner) y **espaciados**: 16 leen la hoja
real y el techo son 60 lecturas/min. ⚠️ **Nunca en paralelo con una batería** (v455): las
baterías modifican el árbol y lo restauran. Lo que generan al correr está en `.gitignore`
— en especial las fotos de la hoja, que son **datos reales**.
⚠️ Las baterías viejas no llevan `if __name__`: **importarlas las EJECUTA**, y cortar su
salida (`Select-Object -First`) puede dejar un fichero roto a medias (v569: se libró).

### ⚠️ Entorno de Streamlit Cloud (NO romper) — v66
- **Python 3.12** en Streamlit Cloud (Settings → Python version). **NO usar 3.14**: solo tiene ruedas
  nativas de versiones bleeding-edge que **segfaultean** (pasó en v65 con pandas 3.0/reportlab 5.0/
  numpy 2.5/pyarrow 25 → `Segmentation fault`, no una excepción Python).
- **`requirements.txt` va PINEADO** con topes de major (pandas<2.3, numpy<2, reportlab<5, svglib<2,
  lxml<6, pillow<12, pyarrow<18). NO volver a dejar todo `>=` sin tope.
  ⚠️ **Los componentes de terceros van FIJOS (==)**, no con tope de major: `streamlit-drawable-canvas`
  pasó de 0.9 a 0.13 dentro de `<1` y dejó el Pre-Start caído (v537). El Cloud reinstala todo cada
  vez que la app despierta. Desde v538 lo vigila `verif_v538` (detecta los componentes por lo que
  instalan) y exige tope en todo lo demás salvo `tzdata`.
- **Streamlit va FIJO (`==1.64.0`, v531)**, la versión del Cloud: con un rango, cada reinicio reinstala la última. Desde v532 la app ya no usa `st.components.v1.html` (anunciado para quitarse): todo HTML incrustado pasa por `core/incrustar.py`. **El local tiene que estar en la misma** (en v531 estaba en 1.57): la suite prueba lo que tenga instalado.
- **El local tiene el Python del Cloud (3.12.10, v535)** con las librerías de `requirements.txt` (`py -3.12`): `run_suite.py` lanza los guardianes con él aunque se arranque con el 3.14, y lo dice en la primera y la última línea. Las baterías usan el Python con que se lanzan: `py -3.12 romper_vNNN.py`.
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
│   ├── estado_vivo.py      # pasada(): las entradas de las 5 herramientas sobreviven a cambiar de sección, mientras sea la MISMA obra (v534-v535); respetar(h, obra): lo cargado a propósito es de SU obra (v539); olvidar() ASIGNA el valor por defecto y vacía las tablas de lo medido con una tabla editable nueva (v540); al_pintar(): se olvida solo al pintarse con OTRA obra real, sin obra nunca (v541); tabla_nueva() al REEMPLAZAR una tabla editable, y el Survey empieza de cero de una obra a otra (cambio_de_obra) salvo lo duplicado (adoptar_siguiente) (v542); de_la_cuenta(): los datos de trabajo son de UNA cuenta (v535). Lista CERRADA
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
   ⚠️ También por SANGRÍA (v568): un `check` fuera del `for` solo mira el ÚLTIMO elemento —
   verif_v313 llevaba desde el 20/09/2026 sin comprobar dos de sus tres funciones.
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

24. ⚠️ **El `selectbox` de Streamlit ya NO es baseweb: es `react-aria`** (visto en
    v430, en el Cloud). No hay `data-baseweb="select"` ni
    `div[data-testid="stSelectboxVirtualDropdown"]` —el marcado que documentó
    v420—: hoy es `div.react-aria-ComboBox` con un `<input role="combobox">` y un
    `<button>` de chevron, y las opciones salen en un `[role="listbox"]`. Una sonda
    escrita contra el marcado viejo devuelve **cero opciones con el desplegable
    delante**. Es v304 y v375 otra vez: **el DOM de Streamlit cambia entre
    versiones**, así que al tocar una sonda vieja hay que volver a mirar el DOM.
    ⚠️ Y de paso: **las OPCIONES de un `selectbox` NO interpretan `:material/…:`** —
    se pintan como texto plano y el `:material/sick:` sale LITERAL en pantalla. En
    `st.radio` sí funciona (v234, verificado en vivo), así que la regla es POR
    WIDGET. Para afirmarlo hay que mirar el nodo: un icono de verdad es un
    `<span role="img">` con `font-family: "Material Symbols Rounded"`; si el texto
    trae los dos puntos y la fuente del cuerpo, es un literal (no una ligadura).
25. ⚠️ **Un clic que «no hace nada» puede ser que la pestaña esté OCULTA.** En v430
    ni el desplegable ni un checkbox respondían, y estuve a punto de reportar que el
    formulario no funcionaba. Lo que pasaba lo dijo una sola línea:
    `document.visibilityState === "hidden"` — con el panel del navegador no visible,
    los eventos sintéticos no llegan. → **Antes de culpar a la app, validar la
    entrada con un control conocido-bueno** (si el checkbox tampoco cambia, el
    problema es tuyo) **y mirar `visibilityState`**. Es la nº12 aplicada a la
    escritura en vez de a la lectura. ⚠️ Y `visibilityState` puede decir «visible» con
    el panel SIN pintar (v560: 0 `requestAnimationFrame` en 1 s): la animación de un
    desplegable no termina, su `<details>` se queda en 40 px con `overflow:hidden` y el
    clic cae en lo de DEBAJO (llevó dos veces a Finance desde «Generate the read»).
    Contar rAF en 1 s, y antes de clicar, `elementFromPoint` = el botón; una captura
    obliga a pintar.

26. ⚠️ **Un `\b` escrito dentro de un heredoc de bash se convierte en el
    carácter 0x08.** El regex queda pidiendo un backspace literal y **no casa
    nunca**, sin dar ningún error: en v436 dejó pasar un texto del Pre-Start en
    español y en v438 una etiqueta de plomada, las dos con un OK en verde. Se ve
    con `cat -A` (`^H`), no leyendo el fichero. → **Todo `\b`, `\n` o `\w` se
    escribe a un fichero con la herramienta de escritura, nunca por heredoc.** Es
    la familia de v429 (los `\n` escapados que rompieron un guardián dos veces).
27. ⚠️ **Un barrido del FUENTE no mide lo que se ve.** El volcado de literales por
    AST de v438 se dejó **cinco** etiquetas en español: filtraba cadenas de más de
    95 caracteres y exigía `>texto</text>` en una sola línea, así que no vio los
    títulos largos ni los que llevan entidades HTML (`&#183;`). Aparecieron al
    **generar el SVG y leer su texto**. → Para afirmar «no queda nada en X»,
    medirlo sobre la SALIDA, no sobre el código que la produce.

28. ⚠️ **Un detector por IDIOMA no sirve para decir «ya no queda español».** El
    barrido de i18n busca acentos y palabras funcionales, así que **«Fichar», «Firma»,
    «Iniciales», «Pendientes», «Sitios», «Registrados», «Planificado» o «Mis ausencias»
    son invisibles para él**: no llevan ni acento ni artículo. Con ese detector di F2
    por terminada y quedaban **47 etiquetas**; el mismo agujero dejó pasar una etiqueta
    de plomada en v438 y una rotura del guardián en v439 — **tres veces**. → Para
    afirmar «no queda nada sin traducir» hay que medir por **POSICIÓN**, no por idioma:
    todo literal que llega a una función de display y NO está envuelto en `t()`, y
    revisarlo a mano para separar ETIQUETA de DATO (una clave de dict y un texto se ven
    igual en el AST). Y para los chequeos, **afirmaciones POSITIVAS**: que el inglés
    esperado ESTÉ, en vez de que el español no esté.
29. ⚠️ **«Compila e importa» no verifica NADA de una traducción.** Los dos
    `UnboundLocalError` de v439 —uno dejaba «Mis ausencias» sin abrir— y las 47
    etiquetas convivieron con `compileall` en verde y los cuatro módulos importando sin
    queja. **Importar no ejecuta** (v378). Lo que las encontró fue LLAMAR a las
    funciones con las dependencias de Sheets sustituidas y mirar lo que pintan. Si al
    traducir aparece una llamada `t(...)` en una función donde `t` ya era una variable,
    Python la marca local en el ámbito ENTERO y revienta — y nada de lo anterior lo ve.
30. ⚠️ **Un invariante mide una FORMA, no el fenómeno — y su «0» solo cubre esa forma.**
    El de v440 («toda cadena de display envuelta en `t()`») daba **0** con **230 frases
    en español** delante: mira el ARGUMENTO de la llamada, así que un trozo de f-string
    y una cadena armada antes en una variable (`msg = f"…"; st.success(msg)`) pasan por
    delante sin que salte nada. Es **literalmente** el guardián del LaTeX de v309, que
    tampoco veía las variables, y el aviso de v349 («cuando el mismo fallo reaparece, la
    pregunta no es solo ¿lo arreglo? sino **¿por qué mi chequeo no lo vio?**») aplicado
    al i18n. → Un «0» hay que leerlo como *«0 de lo que esta red puede ver»*, y por eso
    hacen falta VARIAS redes cuyos huecos no coincidan: en v441, posición (etiquetas
    sueltas) + idioma sobre frases largas (lo que la posición no alcanza) + un barrido
    propio para lo que no es display (el PDF de las herramientas). ⚠️ Y el corolario
    incómodo: **cada red nueva descubre una bolsa nueva** — tras las dos primeras
    quedaban aún ~215 etiquetas CORTAS dentro de listas de tuplas, invisibles para las
    dos. «No queda nada» solo se puede afirmar de la forma que se ha medido.

31. ⚠️ **Borrar el valor de un widget EN PANTALLA no le llega al navegador.** Streamlit
    1.64 identifica `number_input`/`radio` solo por su clave, y el navegador solo recibe un
    valor cuando el código lo ASIGNA (`proto.set_value`): con `del`/`pop` se queda con el
    viejo y lo devuelve en el clic siguiente. Mordió DOS veces —la caja del parte (v529) y el
    cambio de obra sin salir de la herramienta (v535, visto en v540 con el admin)— y las dos
    con AppTest en verde, porque AppTest lee el SERVIDOR. Un `data_editor` con clave y filas
    fijas, además, conserva sus ediciones mientras la forma de los datos no cambie: para
    vaciarlo hace falta OTRA clave. → Para «vaciar», ASIGNAR; y el guardián mira
    `proto.set_value`, no solo `.value`.

32. ⚠️ **Una pasada cortada por `st.rerun()` no es «haber salido» de la pantalla.**
    `estado_vivo` decidía si una herramienta «volvía» mirando si se pintó en la pasada
    anterior; los botones del fichaje del menú lateral terminan en `st.rerun()` ANTES de que
    se pinte la herramienta, así que cerrar la jornada desde Rieles contaba como salir y
    volver (v541). AppTest lo reproduce si el botón del guion hace `st.rerun()`; uno que solo
    cambie el estado no. → No deducir navegación del contador de pasadas.

33. ⚠️ **Streamlit 1.64 pinta en UNA línea la etiqueta de un botón que va EN COLUMNAS.**
    El contenedor del markdown lleva `white-space:nowrap` + elipsis y los `<p>` salen `inline`;
    el texto entero se va a un `title`. Un botón de varias líneas (`a\n\nb\n\nc`) se queda en
    «AC…». Fuera de columnas (los resultados del buscador) no pasa. Lo destapó el recorrido del
    Home (v544): las tarjetas KPI llevaban así desde la subida a 1.64 sin que nada fallara. Es
    el parámetro `wrap` de `st.button`/`st.popover` (1.64): `None` = «decide Streamlit» = en una
    columna, recortar. → Desde v549 la app pone `wrap=True` POR DEFECTO (`core/botones`,
    instalado en app.py); `wrap=False` explícito para una línea a propósito. Y una CIFRA
    dentro de un botón que parte líneas necesita `nowrap` (v550: «0» / «%» en 62 px).

34. ⚠️ **`st_folium` devuelve el ÚLTIMO clic en CADA pasada, no solo en la del clic.** Por eso
    el Home filtra los repetidos — y un filtro que no se reinicia deja ese pin muerto para
    siempre (v544: pin → «Back» → mismo pin = nada). → Para «otra vez el mismo», la clave del
    componente lleva generación y el recuerdo se borra cuando el componente vuelve sin clic.

35. ⚠️ **Un `st.expander` SIN clave se cierra solo cuando cambia lo que tiene encima.**
    Cada acción deja un aviso por `flash`, que se pinta una pasada y se va: al aparecer o
    irse, Streamlit crea de nuevo el desplegable de debajo y nace CERRADO. Con controles
    dentro, el usuario pone la hora y el botón desaparece (v546, el panel «Did you forget…»
    de Fichaje, 3 veces; y la lectura de la IA del Home). Comprobado en una mini-app 1.64:
    CON clave sigue abierto. → Un desplegable con controles dentro lleva `key=`.

36. ⚠️ **«X no aparece» dentro de datos ALEATORIOS falla por azar.** `verif_v488` buscaba el
    refresh token de prueba «R1» dentro del token cifrado (Fernet = base64url con IV al azar):
    medido, el 11,9 % de los cifrados lo contienen, y la suite de v552 dio un rojo sin tocar
    `xero.py`. → La aguja tiene que ser IMPOSIBLE por azar (caracteres fuera del alfabeto:
    `|`, espacios) y larga; y antes de «arreglar» un rojo intermitente, medir su tasa.

37. ⚠️ **Un bloque CON CLAVE puede quedarse FANTASMA en el navegador.** Streamlit 1.64 deja
    en pantalla un contenedor o desplegable con `key=` que la pasada ya no pinta cuando la
    acción que lo quita es LENTA (escribir en la hoja + avisar) y corre DENTRO de él con un
    `st.rerun()`, y lo que ocupa su sitio tiene otra forma (v555: «Reject» en Absences).
    AppTest NO lo ve (lee el servidor). → ACCIÓN DIFERIDA: el botón solo apunta y relanza;
    la acción se ejecuta arriba, antes de pintar la lista. Quitar la clave también lo
    cura, pero la trampa 35 la exige. Revisarlo en cada lista de tarjetas con acciones.

38. ⚠️ **Un dict literal con una clave REPETIDA no avisa: la segunda pisa a la primera.**
    La migración al inglés (v444) tradujo «Situación» y «Estado» las dos a `"Status"`, y la
    columna del ritmo dejó de existir en dos tablas sin un solo error: Python lo acepta, el
    DataFrame sale con una columna menos y los guardianes que buscaban la clave la
    encontraban… la otra (v558). → Al renombrar claves en masa, buscar colisiones;
    `verif_v558` barre la app entera (ningún dict literal con una clave repetida).

39. ⚠️ **Un componente que se MONTA relanza la página, y lo que vive una pasada se pierde.**
    La firma `st_canvas` del Pre-Start manda su valor al montarse y Streamlit relanza ~100 ms
    después: el aviso de `flash` (que se pinta UNA pasada) salía un instante y desaparecía
    (v560: «Clock OUT…» cerrando la jornada desde el Pre-Start). En AppTest no se ve: no
    hay componente que relance. → `flash.mostrar` repite lo recién pintado 2,5 s si no
    llega nada nuevo; y al verificar un aviso en producción, mirarlo a los ~5 s, no solo
    justo tras el clic.
    ⚠️ Y el CLIC (v561, reproducido en una mini-app): si el componente pide su pasada
    mientras corre la de un clic, la corta y el clic se pierde (0 de 8; con `on_click`,
    que corre antes del cuerpo, 4 de 4). Al medirlo, ⚠️ un contador pintado ARRIBA de la
    página lleva UNA pasada de retraso: dio «el primer clic se pierde» con la cura puesta
    hasta que un rastro por pasada enseñó que cada clic se ejecutaba una vez.
    → Desde v562 `core/botones` lo cura (nota en `on_click`, True una vez en la pasada
    siguiente). ⚠️ Un `st.button` nuevo lleva SIEMPRE `key=`: sin clave la cura no lo
    reconoce (`verif_v562` lo vigila).

40. ⚠️ **AppTest clasifica un `st.expander` CON icono como `Status`, no como `Expander`.**
    `at.expander` no lo encuentra y una sonda de «empieza abierto» da `[]` con el código bien
    (v563: 2 de los 9 rojos del primer `verif_v563` eran esto; los otros 7, también sondas:
    el JSON de columnas lleva espacios, la gráfica es `vega_lite_chart`, y un `setdefault` en
    el guion reabría en cada pasada lo que el botón acababa de cerrar). → Buscar en
    `list(at.expander) + list(at.status)`, y antes de tocar el código ante un rojo nuevo,
    preguntarse si es la sonda.
    ⚠️ Otra del mismo tipo (v564): el proto de `multiselect` guarda `select_all` como NÚMERO
    (False = 0; por defecto 1000, el umbral; True = -1) y `is False` daba rojo con el código
    bien. Y `py_compile` en verde dejó pasar un `pid` usado en la MISMA asignación que lo
    define (`pid, nom = …, … or pid`): lo vio `pyflakes` → pasarlo por lo tocado.

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
  **ParamsJSON·MatrixJSON·InterpJSON** (survey completo re-abrible; los derivados se recalculan)·CreadoPor·Creado.
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


## Últimas versiones desplegadas (v569 = actual)

Historial COMPLETO — las secciones detalladas y el índice de las 440 versiones — en
**`HISTORIAL.md`**. Abrilo solo para el detalle de una versión puntual; no lo cargues entero.

| Ver | Cambio principal |
|---|---|
| v569 | **Finance → Invoices, probada acción por acción.** ⚠️ Anular no preguntaba ni avisaba → confirma, diferida y avisa. ⚠️ Una anulada seguía debiendo (pantalla y PDF) → «nothing to collect» y «VOID» con $0. El detalle dice emisión, vencimiento y días de retraso; DD/MM/YYYY en todo (también el PDF); un solo nombre de estado; cifras que filtran; un toque abre; el cliente lleva a Contacts. PRODUCCIÓN (13/10/2026, cuenta admin, 724 px de contenido con el menú; v569 cargado con «r» en la sesión abierta; panel del navegador oculto: clics por el DOM y, en la tabla —un canvas—, por coordenadas tras una captura): datos de PRUEBA en cliente1 — ficha «ZZ Cliente prueba v569» y tres facturas (0001 $110 con un cobro de $50, 0002 $44 anulada, 0003 $22 vencida hace 6 días); «New invoice» con ese cliente sin obras: «This client has no jobs: the invoice lines are free text.» y ningún «Scope», fechas 13/10/2026 y 27/10/2026; cifras «INVOICED $132 · COLLECTED $50 · OUTSTANDING $82 · OVERDUE $22» (la anulada fuera), 2 por fila de 316 px, Overdue con borde y cifra #c0392b; cada cifra aplica su filtro (Overdue → solo 0003; Collected → «No invoices in this filter.»; Outstanding; Invoiced → All); «Voided» se recuerda al ir a Summary y volver; la tabla «No. · Client · Status · Outstanding · Due · Total · Collected · Date» con «🔴 overdue», «⚫ voided», «🟠 partial» y DD/MM/YYYY; un toque en la celda Status abre la 0002: «Issued 19/09/2026 · due 03/10/2026», «Voided: there is nothing to collect.» y sin bloque de anular; la 0003: «… · 6 days overdue» en rojo; ⚠️ «Void this invoice» PREGUNTA («Void invoice No. 0003? It cannot be undone.»), «Keep it» la deja (el desplegable sigue abierto) y «Yes, void it» la anula: «voided», sin saldo ni «Send to Xero», y Overdue pasa a $0 sin rojo; la 0001: cobros «13/10/2026: $50.00» y, registrado el resto ($60 por defecto), «Payment recorded.» al momento, «collected» e «Invoice fully collected.»; el cliente abre su ficha en Contacts (?s=contactos) con «$110 · $110 · $0 · $0». ⚠️ Vistos verificando (propuestos para v570): el aviso «Invoice voided.» NO sale al anular —sale en el clic SIGUIENTE, ya en la lista—: la acción diferida encola el aviso después de que la shell pinte la cola y no relanza (Absences y Time fixes sí); lo mismo en la asignación de compras sin obra de v568 (por eso «el mensaje no se llegó a leer»); un barrido por AST no encuentra más (los dos de Xero que marca corren antes de pintar la cola); la tabla da «Outstanding $44.00» a la ANULADA; y la de facturas de la ficha del cliente sigue en ISO («2026-09-23»), con «Nº» sin traducir, casillas para abrir, dólares truncados (`%,d`) y sin vencimiento ni saldo. Datos: los cuatro de prueba, borrados desde el motor (Invoices vuelve a «No invoices yet») · romper_v569 18/18 + control (verif_v569: los rojos de su 1ª vuelta eran de la SONDA —«Nº» va escapado en el JSON de columnas y «Factura_» se buscaba en el texto, comentarios incluidos (trampa 2)— → por las constantes del AST) · baterías viejas al día: romper_v443 7/7, romper_v452 7/7, romper_v449 7/7 y romper_v483 15/15; ⚠️ esas dos últimas tenían un ancla MUERTA que check_anclas_roturas daba por «ilegible» (la carpeta «COPEX Activos», renombrada en v467, y el impuesto de Xero `[0]` → `[1]`): reparadas, ilegibles 53 → 52 · suite 198 verde con Python 3.12.10 (1558 s, a la primera) |
| v568 | **Finance → Expenses, probada acción por acción.** ⚠️ «Projected at completion» sumaba el coste de hoy de obras sin avance → «Forecast» solo de las que la tienen. ⚠️ Compras sin obra: el aviso mandaba asignarlas y no había forma → se listan y se asignan. Estado en inglés con cabecera, dinero con $, tarjetas y avisos activos, un toque abre la obra, filas de 4. ⚠️ verif_v313 solo miraba la última de sus tres funciones (sangría). PRODUCCIÓN (13/10/2026, cuenta admin, 714 px con el menú; v568 cargado con «r» en la sesión abierta; panel del navegador oculto: sin pintar, clics por el DOM): tarjetas «COST CHARGED TO JOBS $270 · BUDGET $87,000 · % USED 0.3% · FORECAST — no progress yet · OVER BUDGET 0», 2 por fila de 317 px sin estirar la última; «Over budget» abre «No job is over budget.»; «Cost charged to jobs» baja la vista a la tabla (de 786 a 653 en 768 de alto). ⚠️ La escritura nueva contra la hoja REAL: compra de prueba G-00002 ($1.23, de una obra inexistente) creada desde el motor («Receipt added (1.23).»); producción la lista («$1 across 1 purchase(s) with no job… assign each one to its job below», «$1.23 · 13/10/2026 · ZZ prueba v568 · Other · huerfana de prueba», «Assign» desactivado); elegida PRJ-0015 en el selector (comprobado antes con el motor que la opción 3 era ZZ PRUEBA, no 88 walker) y «Assign»: el aviso desaparece y la hoja tiene G-00002 con ProjectID = PRJ-0015 (el mensaje de confirmación no se llegó a leer: la lectura fue a los 8 s); borrada después y la tabla vuelve a $0/$3.15 tras la caché. La lista del selector con el panel oculto solo pinta 1 de sus 4 opciones (virtualizada, ancho 0) — de ahí manejarla con el teclado · romper_v568 24/24 + control (la 1ª vuelta 23/24: escapó «el coste vuelve sin $» — la sonda buscaba «$%,.2f» en toda la config y Committed lo tiene igual: hueco REAL → el formato de CADA columna, y cazada; la rotura nueva de render_pnl la caza ya verif_v313) · romper_v566 y romper_v567 re-ancladas (el script se mudó a `_bajar_a`; dos anclas casaban 3 veces) y cazadas · suite 197 verde con Python 3.12.10 (1491 s), en su 2ª vuelta: la 1ª dio 196 + 1 rojo de verdad — verif_v436 (ninguna comparación con un texto que también se traduce): el identificador de la tarjeta «over» coincidía con la etiqueta `t("over")` del estado → «sobrep», y la suite entera otra vez porque cambió el código |
| v567 | **Lo visto verificando v566.** Tarjetas-botón con texto corto centradas → a la izquierda (kit, toda la app); la herramienta abierta desde una tarjeta quedaba fuera de la vista → la vista baja a ella una vez; margen «None» → «—»; By project se abre tocando cualquier celda. PRODUCCIÓN (13/10/2026, cuenta admin, 846 px con el menú; v567 cargado con «r» en la sesión abierta): las tres tarjetas del Resumen con sus tres líneas a 16 px del borde (antes centradas) y las del Home igual, sin cortes; «Profit» con la vista arriba: el panel pasa de y=1190 a 296–699 en una ventana de 698, y en la pasada siguiente (cambiar el periodo) la vista NO se mueve; el margen de las tres obras sin facturar, «—»; tocar la CELDA de PRUEBA MOVIL (sin casillas en la tabla) abre PRJ-0001 en Costs. Mini-app local 1.64 (lanzador temporal, quitado después): `None` y `NaN` se pintan los dos «None»; texto a la derecha «—/12.5%/-4.0%»; `single-cell` → `cells=[(0, "Proyecto")]` con un toque. Datos: nada escrito · romper_v567 9/9 + control (verif_v567: los 2 rojos de su 1ª vuelta eran de la SONDA —quitaba los espacios pero no los saltos de línea de la regla CSS—, y se añadió que el recuadro lleve la clave que busca el script, que ninguna comprobación miraba) · suite 196 verde con Python 3.12.10 (1501 s, a la primera); verif_v532 (inventario EXACTO de scripts: el 5º entra con su razón) y verif_v566 («single-row» → «single-cell») puestos al día antes |
| v566 | **Finance → Summary, probada acción por acción.** ⚠️ Lo pendiente (por cobrar, vencido, por pagar) solo contaba lo emitido en el periodo → saldos a hoy. ⚠️ Un mes sin movimiento dejaba la pantalla en blanco → lo pendiente sigue, «See All», periodo recordado. Comparación con el mismo tramo del año/mes anterior, «-$128» en toda la app, tarjetas y detalles activos (cada obra abre su factura), By project legible, «Go to», 2 por fila en estrecho. PRODUCCIÓN (13/10/2026, cuenta admin, 846 px con el menú y 390 px; v566 cargado con «r» en la sesión abierta): el periodo «All» se recordó tras el relanzamiento y al volver de Invoices con «←» («This year» seguía); «This month» (vacío) enseña el aviso, «See All» y los 8 pendientes con saldos a hoy («No rate 1 person» de quien trabajó antes); «See All» pasa a «All»; «This year»: «compared with 01/01/2025 → 13/10/2025»; tarjetas «INCOME $0 · WHAT YOU PAY $128 · PROFIT -$128»; «What you pay» abre el desglose y «Profit» el resultado por obra; pendientes en dos líneas, 228 px (846) y 181 px (390), 2 por fila, sin cortes; «Not invoiced»: «PRUEBA MOVIL · $133» abre la factura nueva de esa obra (sin ficha de cliente lo explica y ofrece crearla; se canceló sin crear nada); «No rate»: «hjg,ujgjg» abre su ficha en Users con «Hourly rate» (nada guardado); «No margin»: PRUEBA MOVIL abre su ficha en Costs (`&p=PRJ-0001`); «→ Go to Invoices/Profitability»; By project: «Project / Result / Margin % / Invoiced», «-$132.55», la casilla de la fila abre la obra en Costs y al volver la tabla no salta sola. ⚠️ Vistos verificando (propuestos para v567): las tarjetas KPI con texto corto salen CENTRADAS (un span flex encoge al texto: 43 px en 146); la herramienta que abre una tarjeta se pinta fuera de la vista (y=1168 con 698 de alto); el margen de una obra sin facturar sale «None»; y una fila de By project solo se abre con su casilla, no tocando la celda («Tap a row» promete otra cosa). Datos: nada escrito · romper_v566 26/26 + control (a la primera; verif_v566 53/53 a la primera, validado por la batería) · suite 195 con Python 3.12.10 (1507 s): 194 verde + 1 rojo CADUCADO (verif_v422 exigía que `sin_facturar` leyera las obras, y la lectura se mudó a `sin_facturar_ids` → la entrada al día con su razón, y verde); verif_v309 (el «$-80.20» fijado a propósito) y verif_v313 («Costs (what you pay)» → «What you pay», mismo principio) puestos al día antes, con su razón |
| v565 | **Lo visto verificando v564.** ⚠️ Archivada, «Do today's Pre-Start here» llevaba a un Pre-Start sin ella → ya no se ofrece (se dice cómo reabrirla) y el Pre-Start avisa si la pedida no está. Pies KPI que caben (medidos), «· 1 archived» en la cabecera, «0 h», y una recién creada se abre en Team. PRODUCCIÓN (13/10/2026, cuenta admin, 846 px con el menú; v565 cargado con «r» en la sesión abierta): con la sección recordada en Pre-Start, crear «ZZ Prueba v565» (PRJ-0023) la abre en TEAM («Who has worked here»); en la lista, las tres tarjetas sin recorte (ancho del texto = ancho visible: 97/97, 99/99 y 70/70; antes 136 en 115) con «not charged to jobs», «assigned here» y «0 h» (también en la tarjeta de la localización); archivada desde el motor: «Show archived (1)» y, activado, «Locations — 0 · 0 open · 1 archived»; su Pre-Start ya no ofrece el botón y dice «Archived: it does not appear in the Pre-Start. Reopen it in Data to use it.». El aviso del Pre-Start cuando la pedida no está no se puede provocar desde la pantalla (el botón ya no sale para una archivada): lo cubre verif_v565, con el nombre solo si es de esta empresa. Datos: PRJ-0023 de prueba, borrada desde el motor · romper_v565 9/9 + control (a la primera) · suite 194 verde con Python 3.12.10 (1503 s, a la primera) |
| v564 | **Locations, probada acción por acción.** ⚠️ Expenses de una localización enseñaba beneficio, «Invoice» y reclamaciones de obra → fuera. ⚠️ La archivada seguía en la lista como «closed» → «Show archived». ⚠️ «Select all» en los selectores de personas (asignaba y avisaba a todo el campo) → fuera en toda la app. Nombres en vez de logins, dirección y pin en Data, «Do today's Pre-Start here», KPI activos, `&l=`, alta que se vacía, textos con `t()`. PRODUCCIÓN (12/10/2026, cuenta admin, 846 px con el menú; v564 cargado con «r» en la sesión abierta): con PRJ-0022 archivada la lista no la enseña — «Show archived (1)», «No locations yet…» y «New location» abierto; con el interruptor, su tarjeta a todo el ancho (481,6 de 481,6 px) y «archived» (antes «closed»); al abrirla, `&l=PRJ-0022`; Expenses solo con costes, aviso, órdenes y recibos (sin beneficio, «Invoice» ni reclamaciones); Data con «Where it is (map pin)» abierto (no tiene pin) y «Who normally works here» por nombre («apprentice 1», «hjg,ujgjg»…) y sin «Select all»; reabierta desde el motor, «Do today's Pre-Start here →» lleva al Pre-Start con «ZZ Prueba oficina v564 (PRJ-0022)» elegida (no se envió); «←» vuelve a la ficha en Pre-Start (sección recordada); desde otra sección «Locations» abre la ficha y, dentro, vuelve a la lista (URL sin `&l=`); 3 tarjetas KPI-botón y «Locations — 1 · 1 open»; «People» abre «ZZ Prueba oficina v564: nobody» y se cierra; crear «ZZ Prueba alta v564» (PRJ-0023) abre su ficha con `&l=PRJ-0023` y el alta vuelve VACÍA (clave nloc_nom_1); con dos, una por fila (471 px). ⚠️ Vistos verificando (propuestos para v565): ARCHIVADA, «Do today's Pre-Start here» llevaba al Pre-Start sin ella (el Pre-Start no lista archivadas); el pie «assigned on a regular basis» se recorta (136 px en 115); la cabecera «Locations — 0 · 0 open» con «Show archived» enseñando una; «0.0 h»; una recién creada se abre en la sección de la anterior. Datos: PRJ-0022 y PRJ-0023 de prueba, borradas desde el motor; 88 walker nunca se tocó · romper_v564 39/39 + control (la 1ª vuelta 38/39: escapó «vuelve Interno» — la sonda buscaba '"Interno"' en `ast.unparse`, que escribe comillas SIMPLES: hueco REAL del guardián → por las constantes del AST, y re-corrida, cazada) · baterías viejas al día: romper_v452 7/7 (antes 5/7: sus 2 anclas de deuda, al día; la del ternario, re-anclada al que queda en Locations), romper_v459 8/8 (antes 5/8: tres roturas con «Usuario»/«Rol»/«campo» de antes de la migración —una escapaba sin probar nada—), romper_v443 7/7 y romper_v559 re-ancladas; deuda de anclas 15 → 11 · suite 193 verde con Python 3.12.10 (1522 s, a la primera) |
| v563 | **Groupings, probada acción por acción.** ⚠️ «Delete group» dejaba los ascensores con el ID de la agrupación borrada (visto en la hoja) → el motor desagrupa antes. ⚠️ El alta se quedaba con el nombre y las obras marcadas → se vacía. Tarjetas en rejilla, horas con decimal, curva S Altair (naranja/verde, HOY, %), fuera la gráfica vacía, $, fechas con año, «lifts», `&g=` y el menú vuelve a la lista. PRODUCCIÓN (12/10/2026, cuenta admin, 1280 px con el menú; v563): la lista con UNA agrupación a todo el ancho (916 px) «ZZ Prueba agrupacion v563 · 2 lifts · 0% · 14 d · 10/11/2026»; el tablero con `&g=AGR-0002` en la URL, las 7 tarjetas en rejilla de 173 px (5 + 2, sin estirar), «HOURS 0.4 h», UNA gráfica (Altair: plan naranja discontinuo, real verde, HOY, 0–100 %, DD/MM) y la tabla con el ascensor delante, avance en barra, «30/10/2026» y «$132.55»; tocar «Groupings» en el menú con el tablero abierto vuelve a la lista (URL sin `&g=`); ⚠️ «Delete group» de AGR-0002: «Grouping deleted; 2 lift(s) ungrouped.» y, leído en la hoja (solo lectura), PRJ-0001 y PRJ-0015 con GroupingID vacío y peso 0 (antes quedaban con el ID de la borrada); sin agrupaciones, «New group of lifts» se abre solo; crear «ZZ Prueba alta v563» (AGR-0003) deja el formulario VACÍO (clave nueva_agr_nom_1) y se borró («0 lift(s) ungrouped»). Datos: AGR-0001..0003 de prueba, todas borradas; 88 walker nunca se tocó · romper_v563 24/24 + control (verif_v563: los 9 rojos de su 1ª vuelta eran SONDAS, el código estaba bien — trampa 40) · romper_v452: retiradas con su razón las 2 roturas de las gráficas que v563 quitó (5/5 vivas cazadas; sus otras 2 son deuda ya declarada) · suite 192 con Python 3.12.10: 189 verde + 1 rojo CADUCADO (verif_v452 afirmaba la forma vieja de la leyenda, `{t("Planned"): cur["plan"], …}` del `st.line_chart` → la forma nueva de Altair, con su razón escrita, y verde) + 2 rotos por tiempo (verif_v297 y verif_v488, cortados a 240 s en una suite que tardó 6465 s por un parón de la máquina; sueltos, 9 s y 6 s, verdes) |
| v562 | **El clic que sobrevive a una pasada cortada.** ⚠️ Un componente que se monta cortaba la pasada de un clic y el clic se perdía (el primer «Not now», «Generate», la primera pregunta del chat). `core/botones` anota el clic en un `on_click` y lo ejecuta UNA vez en la pasada siguiente (botones con clave, entregas de formulario, chat); notas tiradas al final de cada pasada completa y a los 15 s. Mini-app: 0 de 8 → 5 de 5. PRODUCCIÓN (11/10/2026, cuenta admin, 1280 px; v562): el redespliegue reinició el proceso del Cloud («Error during DNS resolution», como en v552), se recargó y la cookie restauró la sesión sin contraseña — pasando por la pantalla de acceso, el caso del gestor de cookies; un clic en el indicador «Overdue» abre su detalle («PRUEBA MOVIL - Bondi Junction Lift 1 (02/10/2026)») y el siguiente lo cierra (un doble disparo no cambiaría nada); en el Pre-Start, fichar entrada en ZZ PRUEBA saca el modal y «Not now» lo cierra al primer clic; la salida da UN «Clock OUT at 19:30. Hours worked: 0.01.» (un segundo disparo diría que no hay jornada abierta). La carrera en sí no se puede provocar a mano desde el panel (milisegundos): la prueban la mini-app con el `core/botones` real (5 de 5, sin dobles) y verif_v562. Datos: un fichaje de Admin2 en ZZ PRUEBA 19:29-19:30, cerrado · romper_v562 13/13 + control (la 1ª vuelta 12/13: escapó «la nota no se gasta» —el cierre de pasada del guion la tiraba igual—, hueco REAL: en los caminos con `st.stop()` el clic se repetiría 15 s → el guardián lo mira ahora SIN cierre de pasada, y re-corrida, cazada) · suite 191 verde con Python 3.12.10 (1472 s, a la primera) |
| v561 | **Lo visto verificando v560.** «TODAY» con aire de verdad (y=31). ⚠️ Home a ≤1280 px con menú: KPI + mapa a todo el ancho y Projects | agenda debajo (`@container` por el ancho de la fila; tarjetas de 37 px → 145); indicadores 3 por fila sin partir palabras. La IA lee DD/MM/YYYY, nombres e inglés. ⚠️ El clic perdido, REPRODUCIDO (un componente que se monta corta la pasada del clic: 0 de 8); cura propuesta aparte. PRODUCCIÓN (11/10/2026, cuenta admin, menú abierto; v561 cargado con «r» en la sesión abierta): Home a 840 px → KPI + mapa a 466 px (tarjetas de 145; antes 37) y Projects | agenda debajo a 217; a 1024 → 650 (tarjetas de 206; antes 62) y 309; a 1280 → 906 (tarjetas de 291) y 437; a 1600 → 3 columnas 448/325/325 (tarjetas de 139); en los cuatro, 0 palabras partidas en indicadores y tarjetas y 0 textos recortados, con el estilo aplicado (`container-type: inline-size`); indicadores a 133 px (3 por fila) a 840 y 110 a 1024. Cronograma de PRJ-0015 a 466 px: la caja del subtítulo acaba en 22,2 y la de «TODAY» empieza en 24,5 (antes se pisaban 0,3); recuadro 409 para 407 de dibujo. «Refresh» de la lectura: «ended 02/10/2026», sin fechas ISO, logins ni «VENCIDA»/«en N d»/«s/d». Una llamada más a la IA; nada escrito · romper_v561 15/15 + control (anclas comprobadas antes: una no casaba —la regla del 100 % lleva una llave, no dos— y se corrigió) · suite 190 verde con Python 3.12.10 (1467 s, a la primera) |
| v560 | **Los pendientes del recorrido, todos («Todo ya»).** ⚠️ Los avisos se perdían si un componente relanzaba la página (Pre-Start: «Clock OUT») → 2,5 s de gracia. ⚠️ Cuatro formularios borraban lo escrito al dar error → generación de claves; ningún `clear_on_submit=True`. Gasto por tiempo, «TODAY» sin pisar, filtro en su fila, recuadros que se re-miden, campana de 64 px, «Refresh» que genera, `&p=`, «Record», «at 16:36». PRODUCCIÓN (11/10/2026, cuenta admin; v560 cargado con «r» en la sesión abierta): en el Pre-Start, «Clock IN Project at 17:21.» y, cerrando la jornada desde el menú lateral, «Clock OUT at 17:22. Hours worked: 0.01.» SIGUE en pantalla más de 30 s (antes se iba antes de 9 s); el modal del Pre-Start se cerró con «Not now» al primer clic; a 846 px con el menú abierto la barra en UNA fila («←» 44, buscador 273, versión 43, campana 64, el «4» entero: 24 de 24) y a 390 px también (campana 64, la fila acaba en 379 de 390); la cartera a 846 con menú: las 4 opciones del ritmo en una fila de 34 px («On hold» 91 px); «See the full project» del Home → `&p=PRJ-0001` y `&p=PRJ-0015`; Costs de PRJ-0015: 30/09→06/10 = 315,3 y 06/10→07/10 = 52,5 (6 a 1), etiquetas a ≥ 52; el recibo sin importe conserva «Prueba v560» y «sin importe» con «Enter the value of the receipt.» (nada escrito); Contacts: «Record»; «Refresh» deja en un clic una lectura NUEVA y distinta. ⚠️ El cronograma a 472 px: «TODAY» ya no pisa el subtítulo pero queda a menos de 1 px debajo de «14 activities» (propuesto para v561). Datos: un fichaje de Admin2 en ZZ PRUEBA 17:21-17:22, cerrado · romper_v560 26/26 + control (anclas comprobadas antes: una casaba 2 veces —el «Generate» repite la línea del «Refresh»— y se alargó) · romper_v558 26/26 con su ancla al día (el «All types» pasó a la columna de la búsqueda) · suite 189 verde con Python 3.12.10 (1444 s, a la primera) |
| v559 | **La ficha de una obra, probada acción por acción.** ⚠️ «Delete» borraba de Drive con un clic → pregunta (acción diferida). ⚠️ Asignados y certificados no se guardaban hasta «Save changes» sin decirlo → «Not saved yet». Cronograma legible (3 lienzos y media query), cifras sin partir, nombres en vez de logins y DD/MM/YYYY en las 4 pestañas, gráfico de gasto sin marcas repetidas, un solo «Invoice». PRODUCCIÓN (11/10/2026, cuenta admin, 1024 px; v559): Status a 950 px el lienzo de 1000 (escala 0,95, etiquetas ~9,6 px) y a 650 px el de 700 (escala 0,93, etiquetas 8,8 px; antes ~4,8) con el recuadro a la medida (568 de 568); «09/11/2026» a 21 px y «13 d behind» a 18 px en una línea; partes «26/09/2026 · hjg,ujgjg · 29/09/2026 16:35» y «1 log · 1 day covered»; Data con los asignados por nombre, «Staff and certificates are saved with Save changes», inicio 28/09/2026 a la izquierda, «until 02/10/2026», «— automatic (from the progress) —»; Costs con las 5 tarjetas en UNA fila a 950 y a 650 (122 px), ejes «$0.0 $0.5 $1.0 $1.5 $2.0», leyenda «Cumulative cost day by day.», «Set the budget in Data» y «Go to Users», sin «v360»; Files «Survey matrix» y «Uploaded by: Bobo»; ⚠️ «Delete» de matriz_survey.csv PREGUNTA («…cannot be recovered») y «Keep it» lo deja. Una vez, tras cambiar el ancho en plena carga, el recuadro del cronograma se quedó en 150 px (se corrige con un resize); no se reprodujo en 3 montajes ni en una recarga. ESCRITURAS contra la hoja real (ejercitar_v559_real, 23/23): obra de prueba sin asignados — guardar (Model v559, Budget 100, historial «· Bobo» con fecha DD/MM/YYYY), añadir/borrar actividad con confirmación, tabla, plan base, beneficio fijo 50, archivar; borrada y sus 4 alertas cerradas. En PRJ-0015: pedido con fecha ISO en la hoja y «due 20/10» en pantalla (queda CANCELADO: los pedidos no se borran) y recibo de $5, borrado · romper_v559 35/35 + control (la 1ª vuelta 33/35: escaparon «los asignados vuelven a salir por login» y «la tarifa vuelve sin $» — huecos REALES del guardián, que no miraba las opciones del selector y daba por bueno el $ con una sola columna → reforzado, y esas dos re-corridas y cazadas) · suite 188 verde con Python 3.12.10 (la 1ª vuelta 183 + 5 rojos, todos de esta versión: verif_v523/v526 esperaban ISO y login → nombre y DD/MM/YYYY con `auth.list_users` sustituido; verif_v333 la escala tipográfica → 21/18 px; verif_v453 dos avisos concatenados → `t()` con marcador; check_anclas_roturas 3 anclas movidas → romper_v471 5/5, romper_v498 4/4, romper_v526 9/9 re-corridas) |
| v558 | **Projects: la cartera y el alta, probadas acción por acción.** ⚠️ «Pace» no salía (dos claves «Status» desde v444; barrido de dicts con clave repetida). ⚠️ Una obra homónima no se podía crear nunca. ⚠️ Un Delivery reventaba tras escribirse. ⚠️ La fecha estimada no seguía al NS. Crear abre la obra; tarjetas sin «\\$» ni «33.0d»; «Invoice» sin fichas lleva a Contacts; mapa a lo ancho; contadores activos; vista y filtros recordados; Home → cartera filtrada. PRODUCCIÓN (10-11/10/2026, cuenta admin; v558): la Lista con «Pace» («33 d behind», «20 d behind», «12 d behind»), selectores segmentados, «All types» y «3 behind schedule» como botón que aplica Behind; Tarjetas con «$133», «33 d», «0% of budget» / «no budget»; «Invoice» de PRUEBA MOVIL dice «This job's client, Cliente de prueba, only exists as text…» y su botón abre esa ficha en Contacts (no se guardó); al volver a Projects por el menú tras Finance y Contacts sigue en Tarjetas y Behind; alta: icono del buscador por icon=, mapa 616 de 616 px, fechas 11/10/2026, NS 2 → 3 mueve la estimada a «02/11/2026 (23 days)» sin enviar; ⚠️ un Delivery con el nombre de PRJ-0015: aviso y casilla DENTRO del form, marcada sigue marcada, «Create» crea PRJ-0021 sin error y la abre (&p=PRJ-0021) con «Project PRJ-0021 created with 1 activities»; el alta vuelve vacía; PRJ-0021 borrada desde el motor (era de prueba); Home «Overdue · 1 → Go to Projects» abre «From Home: only Overdue (1)» y «Show all» vuelve a 3 of 3 · romper_v558 26/26 + control (la 1ª vuelta 25/26: la rotura de la fecha estimada no rompía nada —la duración sale de las filas de etapas con el NS— → rehecha y cazada) · romper_v444 7/7 con su ancla al día · verif_v408 reanclado con su razón · suite 187 verde con Python 3.12.10 |
| v557 | **Users, probada acción por acción.** ⚠️ Correos que no lo son («driver 1», «hotmai.com») se guardaban → validación (motor y pantalla) y «Did you mean…?». ⚠️ El alta borraba todo al dar error → conserva lo escrito. ⚠️ Contraseñas de 1 carácter → mínimo 8, repetirla al cambiar. Salud que filtra la tabla, «Contact», «$», selector segmentado, DD/MM/YYYY. PRODUCCIÓN (10/10/2026, cuenta admin, 1024 px; v557): la línea de salud ofrece «9 with no contact details» y «4 invalid or suspicious email»; esta deja SOLO a helper 1, helper 2 y electritian 1 («check email») y driver 1 («invalid email»), con cabecera «Contact» y la tabla con su clave (gu_tbl_correo); la fila 4 de la tabla FILTRADA abre a driver 1 (no se cruza): «No contact details · Invalid email», selector de secciones segmentado (sin bolitas) y en Contact ««driver 1» is not an email address.»; helper 1 (…@hotmai.com): «Check the email» y «Did you mean …@hotmail.com?» con la casilla «The address is correct as written»; el alta sin correo da «Email is required…» y CONSERVA usuario, nombre y contraseña — siguen siendo 10 personas: no se creó, cambió ni borró a nadie · romper_v557 17/17 + control · suite 186 verde con Python 3.12.10 |
| v556 | **Time fixes, probada acción por acción.** ⚠️ Dos correcciones sobre el mismo fichaje dejaban la vieja sin salida («no longer exists») → «superseded». ⚠️ Revertir que choca no tenía salida → «Set the right time» en todas y aviso de solape neutro. ⚠️ La persona no se enteraba → aviso al revertir o fijar. Día del fichaje, dd/mm, antiguo primero, tarjetas activas, acción diferida. PRODUCCIÓN (09/10/2026, cuenta admin, 1024 px; v556 cargado con «r»): COR-0001 sale primero, con «Thu 08/10/2026 · workday», «Asked on 08/10/2026 18:27» y «Superseded by COR-0002…», solo con «Close as superseded»; «Revert» en COR-0002 se rechaza con «Bobo · Thu 08/10/2026: … overlaps the workday entry from 18:24 to 18:26…» (neutro); ⚠️ cerrar la PRIMERA (COR-0001) con la de otra forma ocupando su sitio (el caso del fantasma): queda SOLO COR-0002, «Closed: superseded by COR-0002.», y sigue así tras otra pasada; «Set the right time» (18:27) en COR-0002: «Time set to 18:27.», bandeja vacía, Approved 2 (y el aviso «Time correction adjusted: 08/10/2026» a la persona, Admin2); «Approved» abre su lista con el día de cada una; el histórico, con «Fri 09/10/2026» / «Thu 08/10/2026» y «Reviewed by: Bobo» (antes «Admin2») · romper_v556 14/14 + control · suite 185 verde con Python 3.12.10 |
| v555 | **Absences, probada acción por acción.** ⚠️ Tras «Reject» la tarjeta quedaba FANTASMA (Streamlit 1.64 + bloque con clave + acción lenta dentro) → acción DIFERIDA, trampa 37. ⚠️ La baja por enfermedad no llegaba al admin y nada aprobado se podía deshacer → sección de bajas y «Cancel» con confirmación. Aviso en inglés, urgente primero, dd/mm/aaaa, tarjetas activas, saldo tras la solicitud. PRODUCCIÓN (09/10/2026, cuenta admin, 1024 px; v555 cargado con «r»): con tres solicitudes de prueba de campo000 (AUS-0004..0006) — lo pendiente sale en orden (12/10 antes que 13/10), con fechas «12/10/2026» y «13/10/2026 → 14/10/2026» y el saldo «20 of 20 … → 18 after this request»; ⚠️ «Reject» en la PRIMERA tarjeta, con la de otra forma ocupando su sitio (el caso del fantasma): queda SOLO AUS-0005, «Request rejected.», Pending 1, y sigue así tras otra pasada; «Approve» de AUS-0005: «Absence approved. 2 day(s) marked in the planner.» (ROS-0014: LEAVE 13 y 14/10), «No pending requests.», ningún fantasma; «Next 7 days» = 1 y abre AUS-0005; la baja AUS-0006 sale en «Sick leave recorded» con «Cancel», que PREGUNTA («Cancel this absence? Its days are freed on the board and hjg,ujgjg is told.») y «Keep it» la deja; el histórico ofrece «Cancel» en las dos aprobadas. «Yes, cancel it» no se pulsó en producción (avisaría a campo000): lo cubre verif_v555. Pruebas canceladas o rechazadas desde el motor; ROS-0014 limpia · romper_v555 14/14 + control · suite 184 verde con Python 3.12.10 |

_(y 493 versiones anteriores en `HISTORIAL.md`)_
