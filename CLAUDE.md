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
baterías modifican el árbol y lo restauran. La suite NO (v573: `run_suite.py` pone en rojo
al guardián que cambie un byte del código de la app; un guardián valida sus sondas EN
MEMORIA). `run_suite.py verif_v57` filtra por nombre; para desplegar, siempre entera. Lo que generan al correr está en `.gitignore`
— en especial las fotos de la hoja, que son **datos reales**.
⚠️ Las baterías viejas no llevan `if __name__`: **importarlas las EJECUTA**, y cortar su
salida (`Select-Object -First`) puede dejar un fichero roto a medias (v569: se libró).
⚠️ Y una batería que no entiende `--anclas` se EJECUTA entera con él: nunca con `timeout`
(v600: cortada, dejó dos roturas en catalogo_ui y projects_ui — vistas en el diff y restauradas).
⚠️ `check_anclas_roturas` (con `anclas_lectura.py`, v575) sitúa el ANCLA de cada rotura por la
posición que le da su batería y exige CERO muertas, ilegibles o sin forma: una batería
nueva se escribe en una forma legible (o se le enseña la forma). Y una batería solo
restaura lo que RESPALDA: romper_v438 dejó `stages.py` roto al anclar fuera de su `F`.

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
(`render_topbar`: botón ← Atrás, buscador —solo gestión; busca de verdad desde v330, `home_ui.buscar`—, versión y campana).
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
    ⚠️ v600 · la regla de v582 los oculta solo con la pasada PARADA: durante otra se veían
    (en la lista de Inventory, el botón de una ficha). Medido en una mini-app: los deja un
    bloque con clave que desaparece tras un `st.rerun()` lanzado DESDE DENTRO; la acción
    diferida NO basta. Lo cura `theme.script_fantasmas` (marca al acabar cada pasada lo que
    sigue «stale», que con la pasada parada solo puede ser fantasma) + su CSS, para toda la
    app. Para medirlo: nodos (no claves: un fantasma comparte clave con el vivo) y
    `setInterval`, no `requestAnimationFrame` (con el panel sin pintar no corre).

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

41. ⚠️ **Un guion de prueba montado en OTRO orden que la shell aprueba lo que en producción
    falla.** La shell pinta los avisos de `flash` ANTES de la sección; los guiones de
    verif_v563/v564/v568/v569 los pintaban DESPUÉS, así que un aviso encolado sin
    `st.rerun()` (anular una factura, asignar una compra) salía en AppTest y en producción
    salía un clic tarde, ya en otra pantalla (v570). → El guion copia el ORDEN del
    llamador real, no solo sus datos. `verif_v570` vigila ese orden y barre la app: ningún
    `flash` sin un `st.rerun()` que se EJECUTE detrás (uno bajo el `if st.button` de OTRO
    botón no cuenta: con él como prueba, los dos fallos pasaban; ni uno bajo un `if` cuya
    condición se decide DESPUÉS del aviso, como el `if _sel:` de una tabla de más abajo).

42. ⚠️ **Un sustituto que contesta a un LITERAL hereda el error del literal — y una LECTURA
    puede ESCRIBIR.** `datos_asociados` (el aviso antes de BORRAR una obra) pedía «Gastos», nombre
    de antes del renombrado, y el sustituto de verif_v381 contestaba a «Gastos»: el guardián
    EXIGÍA el fallo mientras el recuento real salía 0. Y como `get_sheet` crea la pestaña que
    falta, leer una que no existe la fabricaba vacía (v590). → El sustituto contesta a la
    CONSTANTE del módulo, nunca a un literal; una lectura sin cabecera conocida pasa `None`
    (no crea); `verif_v590` barre los nombres viejos de pestaña en toda la app.

43. ⚠️ **Streamlit 1.64 CONSERVA el desplazamiento al cambiar de vista, y el markdown re-enlaza
    los emails.** (v603) Abrir una ficha, crear algo o tocar otra sección del menú dejaba la
    página donde estaba la anterior (la ficha nueva ~190 px abajo, en el móvil 917; un aviso de
    `flash` a -488 px): desde v603 la shell sube al cambiar de vista (`home_ui._vista`: sección,
    sub-pestaña, búsqueda y las claves `_…_open…`/`_…_nueva/o`) o a un aviso nuevo oculto; lo que
    se pidió BAJAR (`_bajar_a`) manda. ⚠️ Una marca de sesión nueva NO puede llamarse `_x_nuevo`
    ni `_x_open`: entraría en la firma de la vista (pasó con `_flash_nuevo`: subía siempre).
    Y un email como TEXTO de un `<a>` sale como un enlace VACÍO + otro (el autoenlace de GFM):
    un enlace con texto va por `maps.enlace_md`, y lo que va en HTML se escapa.

44. ⚠️ **AppTest LEE el `secrets.toml` local, con la clave de la API de PAGO.** (v607) Un guardián
    que pinta una pantalla que llama a un modelo lo llamaría DE VERDAD en cada suite —los de la
    tarjeta del parte (v523, v524, v525…) ya la pintaban—. `parte_agente.clave_api()` devuelve vacío
    si está cargado `streamlit.testing` (la app no lo importa nunca, lo vigila `verif_v607`); un
    guardián que quiera el agente sustituye `clave_api` y `_llamar` a propósito. Y la clave del
    examen (`sueltos/examen_agente_parte.py`) se pasa explícita: ese sí gasta, a mano y con permiso.

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

### parte_agente.py — el agente del parte diario (v607)
`leer(texto, plan, …)` → lectura validada o `(None, motivo)`; `propuestas(lectura, plan, mapa,
texto, lineas)` → la forma de `parte_propuestas.propuestas` + `empezadas/problemas/aparte/no_entendido`.
**Claude Sonnet 5.5** (lo eligió el usuario), esfuerzo bajo, salida con esquema, respaldo
`fallbacks="default"`. Una lectura por parte en `DailyLogs.Reading`; la pantalla en
`daily_log_ui` (`_leer_pendientes`, `_relectura`, `_hablar`). El modelo solo PROPONE códigos del plan;
acredita el autor. Medir con `guardianes/sueltos/examen_agente_parte.py A|B|C` (gasta: con permiso).
**Memoria (v610, `agente_memoria.py`)**: hoja GLOBAL `AgentMemory` (maestro), aprende al confirmar
(marcado = confirmada, sin marcar = rechazada) y `para_el_agente()` va PRIMERO en el mensaje, en orden
fijo (caché). Panel «What the assistant has learned» en los partes del admin. ⚠️ Está en
`hojas.HOJAS_LECTURA`: su lector va sin cabeceras y fuera del lote leería vacío para siempre.

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


## Últimas versiones desplegadas (v610 = actual)

Historial COMPLETO — las secciones detalladas y el índice de las 440 versiones — en
**`HISTORIAL.md`**. Abrilo solo para el detalle de una versión puntual; no lo cargues entero.

| Ver | Cambio principal |
|---|---|
| v610 | **La memoria del agente del parte (global, automática).** Aprende de lo que se marca y se deja sin marcar al confirmar, recibe las lecciones firmes delante del plan (en la caché), y la oficina las ve, las borra y enseña reglas; el cero de la auditoría. ⚠️ Cazado antes de desplegar (romper_v430, rojo de base): `AgentMemory` fuera del lote de lectura, o sea la memoria escrita y leída VACÍA para siempre (regla v461/v507/v514, cuarta vez) → en el lote. PRODUCCIÓN (27/10/2026, v610 en la etiqueta, cuenta admin): la siembra en seco y después con `--aplicar`: `AgentMemory` creada en el maestro con las 7 lecciones de LOG-0003 y LOG-0005 (lo que el usuario marcó: «isntalled the tank» → Install CW tank, «finished headroom wiring» → Install electrical boxes y Wire all boxes, «installed rails» → las 3 de rieles, «span the motor» → Spin motor) y la regla del propietario «installed motor» → Install motor (machine), leído con gspread de solo lectura; en los partes de PRJ-0034, el panel «What the assistant has learned» ⚠️ decía «Nothing learned yet» con las 8 filas en la hoja: el índice de pestañas del proceso (`timeclock._libro`, `cache_resource`, no caduca) se construyó antes de que la siembra —OTRO proceso— creara la hoja, y el lote solo pide las pestañas del índice (visto verificando, propuesto para v611); una regla de prueba con «Teach it a rule» («zz prueba v610» → Spin motor) → «Rule saved: «zz prueba v610» → Spin motor.», y como `get_sheet` refresca el índice al no encontrar la hoja, el panel enseña las 9 (Phrase · Activity · Kind · Confirmed · Rejected · Updated); «Forget these» ofrece las 8 del grupo y NO la regla del propietario; olvidada la de prueba → «Forgotten: 1.», la página sube al aviso, la tabla vuelve a 8 y en la hoja MEM-0009 con Active=NO (Admin2, cliente1: queda como rastro). La lectura CON memoria no se pidió al modelo en producción (gasta y no había parte nuevo): la midió el examen con los partes del usuario y la prueba verif_v610. ⚠️ Visto también (propuesto para v611): «Forget» no tiene vuelta atrás en la pantalla, y con «Select all» se olvida todo en dos clics · verif_v610 51/51 (la de `AgentMemory` en el lote, añadida tras el rojo de verif_v430: su sonda de pantalla sustituye `_records_cached` y no podía verlo) · al día con su razón: verif_v482 (11 globales, con agentmemory), verif_v465 (`AgentMemory` nace en inglés), verif_v607 y v608 (el `_llamar` sustituido acepta `memoria`) · romper_v610 26/26 + control (la 1ª tanda vio ESCAPAR «bajo AppTest se lee la hoja REAL»: la sonda era débil porque la hoja no existía → `_records_cached` sustituido con datos conocidos, trampa 12; y una rotura más, `AgentMemory` fuera del lote) · re-ancladas romper_v488 (detrás de «xeroconnections» va «agentmemory») y romper_v607 (la relectura y `PROMPT_V = 2`) · romper_v469 arranca sin `SCRW` · re-corridas: romper_v430 26/26 (la 1ª vez, ROJO DE BASE: el hallazgo del lote), v445 7/7, v461 11/11, v469 9/9, v472 15/15, v482 11/11, v488 0 mal, v510 14/14, v514 15/15, v516 20/20, v523 30/30, v524 19/19, v525 16/16, v526 9/9, v528 19/19, v529 5/5, v546 12/12, v556 14/14, v559 35/35, v560 26/26, v577 35/35, v581 29/29, v586 15/15, v607 37/37, v608 12/12, v609 11/11 · check_anclas_roturas: 2127 vivas, 0 muertas · suite 237 verde con Python 3.12.10 (2025 s; la vuelta anterior dio 1 rojo de una afirmación CADUCADA, verif_v465: `AgentMemory` nace en inglés y no tiene nombre viejo que respaldar → al día con su razón, y la suite repetida entera) |
| v609 | **El motor en el catálogo y la primera migración a propósito.** «Install motor (machine)» 5 % sacado de «Install motor bedplate» (17 → 12) y la etapa «Shaft Climb, Bedplate & Motor»; juego «2026-10-27» y `migrar_catalogo` para pasar las obras existentes (sin él quedaban en solo lectura); `StagePlanJSON`, auditado. PRODUCCIÓN (27/10/2026, v609 en la etiqueta): la migración EN SECO primero —se mueven 2 obras, las dos por el motor sin acreditar: PRJ-0026 84,3 → 83,6 % (etapa 100 → 95) y PRJ-0034 67,3 → 66,9 % (etapa 66 → 61)—, después con copia en D:: las 6 obras en «2026-10-27», las 5 con la etapa renombrada en su cronograma (PRJ-0026 y PRJ-0034 sin fin real: ya no están completas) y 6 líneas en AuditTrail de «migracion-v609» con su acción y el plan; en la ficha de PRJ-0034, «Shaft Climb, Bedplate & Motor — 61% (carried over)» y ningún aviso de catálogo antiguo. ⚠️ Visto en ese rastro (arreglado en v610): «Progress 0.0 → 0.0» anotado como cambio en PRJ-0030 y PRJ-0032 · verif_v609 34/34 (la 1ª vuelta cazó un fallo de VERDAD: `StagePlanJSON` sin auditar desde v512) · al día con su razón: verif_v512 (174 actividades), v514 (los números, del catálogo: trampa 16), v519 (la huella del juego nuevo, y contra la de HOY) y v449 (los marcadores del mensaje) · romper_v609 11/11 + control (`stages.py` va en CRLF: sus anclas, sin el salto) · re-corridas: romper_v430 26/26, v448 7/7 y v449 7/7 (re-ancladas: el nombre de la etapa), v512 22/22 (re-anclada: la versión), v514 15/15, v519 13/13, v523 30/30, v525 16/16, v528 19/19, v581 29/29 · check_anclas_roturas: 2100 vivas, 0 muertas (la migración copiaba 5 frases de `acreditar` y sus anclas salían REPETIDAS: renombradas sus variables) · suite 236 verde con Python 3.12.10 (2023 s, a la primera) |
| v608 | **La cita una vez y «Tell the office».** Dos casillas del mismo trozo repetían la cita → una vez; lo que el agente marca como problema se veía y nadie se enteraba → «Tell the office» (el autor corrige el texto y lo manda como alarma + Telegram/correo; lo enviado no se ofrece otra vez). PRODUCCIÓN (27/10/2026, v608 en la etiqueta, cuenta admin): PRJ-0034 y sus 5 partes se pintan sin error. «Tell the office» NO se pulsó en producción (avisaría a los admins y propietarios reales) y los partes de prueba no tienen trozos de problema: lo prueba verif_v608 con la alarma interceptada; la cita una vez, también en verif_v608, con la tarjeta del agente y la del vocabulario · verif_v608 23/23 (la 1ª vuelta, 2 rojos de la SONDA: el modelo sustituido contestaba con un problema a CUALQUIER texto, y «Installed sills and frames» el vocabulario solo lo parte en uno —justo lo que v607 vino a arreglar— → «Installed headers and installed frames») · romper_v608 12/12 + control, a la primera · re-corridas: romper_v607 37/37, v523 30/30, v524 19/19, v525 16/16, v586 15/15, v559 35/35 · check_anclas_roturas: 2088 vivas, 0 muertas · suite 235 verde con Python 3.12.10 (2004 s, a la primera) |
| v607 | **El agente del parte diario (Sonnet 5.5).** El parte se leía con una lista de palabras: «Installed yoke, platform, walls, and ceiling» daba solo el yoke y lo demás parecía ignorado → un modelo lo lee entero con el plan, lo acreditado y el documento del oficio, lo reparte en trozos (nada sin casilla), PREGUNTA lo que no entiende y relee con las respuestas; el autor sigue marcando. Examen A 14/14 (vocabulario 2/14), B 34/40 sin errores (23/40), C 1070 notas a US$0,0068. PRODUCCIÓN (27/10/2026, v607 en la etiqueta; el usuario como campo000 en PRJ-0034): la hoja creó `Reading` al final; LOG-0003 («Isntalled the tank…», del que el vocabulario no sacaba nada) leído EN EL CLOUD por claude-sonnet-5-5 en 2,7 s con el documento del oficio entero (ref 40366): «Install CW tank» propuesto y marcado; un parte NUEVO («Installed rails, installed bedplate, installed motor, finished headroom wiring, span the motor, starting beling») leído en 3,9 s LEYENDO DE LA CACHÉ (18433 tokens, ≈US$0,009): 3 hechos (electrical boxes, wire all boxes, spin motor), 2 preguntas (los rieles; el bedplate, ya acreditado), «installed motor» no entendido con su pregunta y «starting beling» empezado SIN acreditar; el usuario marcó 6 y StageProgress tiene las 6 con origen «log», el ID del parte y su día; el registro dice `lector` claude-sonnet-5-5/p1. Antes, el ensayo como campo000 con los datos reales (modelo de verdad, sin escribir) dio la misma tarjeta para LOG-0003. ⚠️ Visto en el ensayo (propuesto y hecho en v608): la misma cita repetida bajo dos casillas del mismo trozo · verif_v607 94/94 (la 1ª vuelta, 3 rojos de la SONDA: 12 caracteres contra un texto de 13, y los avisos de `flash` son st.success/st.warning, que no miraba) · verif_v524 al día con su razón (`Reading` va detrás de `Proposals`) · romper_v607 37/37 + control (35 en la 1ª tanda; las dos de las atribuciones y de `ref`, añadidas después) · re-corridas: romper_v516 20/20, v523 30/30 (3 re-ancladas + la fila), v524 19/19 (re-anclada), v525 16/16 (re-anclada), v526 9/9, v528 19/19, v529 5/5, v537 8/8, v538 6/6 (re-anclada; verif_v538 al día: `anthropic` fijo vale como tope), v559 35/35, v586 15/15 · check_anclas_roturas: 2075 vivas, 0 muertas · suite 234 verde con Python 3.12.10 (2062 s, a la primera) |
| v606 | **Library: las píldoras, solo las que tienen piezas (Library cerrada).** Con un filtro salían secciones a cero que en la fila del móvil solo estorbaban → las que tienen piezas, más la elegida. PRODUCCIÓN (26/10/2026, cuenta admin, v606 en la etiqueta), con las 750 piezas reales: sin filtros, las 16 secciones; con «Documents», solo las 11 que tienen documentos y ninguna a cero (suman 218; en v605 salían también «Controller · 0», «Shaft · 0»…); «Documentation» elegida (3 documentos) y después «Photos»: «Documentation · 0» SIGUE a la vista y marcada —para poder soltarla— junto a las 15 con fotos, con «Nothing matches those filters.» y «Show all». Library, cerrada · romper_v606 3/3 + control, a la primera · verif_v606 6/6 a la primera · romper_v520 re-anclada (la lista de secciones), 12/12 · re-corridas: romper_v605 11/11, v604 35/35 · check_anclas_roturas: 2037 vivas, 0 muertas · suite 233 verde con Python 3.12.10 (1933 s, a la primera) |
| v605 | **Lo visto verificando v604 en Library.** ⚠️ El «(n/m)» se cortaba en títulos largos (la tabla y 9 de 9 miniaturas en el móvil) → columna «Page», la primera, e insignia sobre la foto; ⚠️ las 16 píldoras ocupaban ~320 px en el móvil → una fila que se desliza, con la elegida la primera. PRODUCCIÓN (26/10/2026, cuenta admin, v605 en la etiqueta), con las 750 piezas reales: las 9 insignias de la 1ª página a 6 px de la esquina de su foto («1/2», «2/2», «1/3»…); en el móvil (375) las secciones en UNA fila de 66 px que se desliza (2011 en 353; en v604, ~320 px) y la galería a 758 px (en v604, 958); elegir «Signalling» la pone la PRIMERA de la fila y filtra («2 items»); la tabla de documentos con «Page» primera («1/7», «2/7»…, leído del canvas) y el título limpio al lado. ⚠️ Visto verificando (propuesto): con un filtro, las píldoras enseñan secciones a CERO («Controller · 0») que en la fila del móvil solo estorban · romper_v605 11/11 + control, a la primera · verif_v605 12/12 · verif_v604 al día con su razón (la página ya no va al final del título) · ⚠️ romper_v604 dejó escapar «la galería vuelve a apilarse»: verif_v604 buscaba «nowrap» en el FICHERO y v605 lo puso también en el CSS de las secciones (trampa 2) → la regla exacta de la galería, 35/35 · re-corridas: romper_v598 10/10 · check_anclas_roturas: 2033 vivas, 0 muertas · suite 232 verde con Python 3.12.10 (1958 s, a la primera) |
| v604 | **Library, probada (con las 750 piezas reales).** ⚠️ Los 218 documentos (JPEG) se abrían sin imagen → por el archivo; ⚠️ 101 títulos repetidos → «(3/30)» y «Previous / Next»; ⚠️ 9,1 s al abrir y 4-6 s por página → miniaturas en paralelo y guardadas; ⚠️ una foto por fila en el móvil → 3 y la pieza entera se toca; ⚠️ filtros perdidos y página de otro conjunto; ⚠️ el alta repetía; ⚠️ Drive sin tiempo máximo y un borrado que mentía; cifras activas, secciones en píldoras, DD/MM/YYYY. PRODUCCIÓN (26/10/2026, cuenta admin, v604 en la etiqueta), con las 750 piezas reales: cifras 2 por fila (Items 750 · Photos 532 · Documents 218 · Sections 16); 12 miniaturas de 360×360 por página (45 páginas, eran 89); una página NUEVA (miniaturas sin hacer) en 2,5 s —en v603, 5,9 s por 6 fotos enteras— y una ya vista en 0,65 s, y «Next» deja la galería ARRIBA (0 px); «Documents» filtra (218) y baja a la tabla; una página de manual se abre CON su imagen (1200×1600; en v603, sin ella), «Download» encima (372 / 420 px), «3 of 218», el título «… — installation steps (2/7)», «Manual» y «28/09/2026 17:56»; «Next» → «(3/7)» en 1,3 s; volver deja «All documents» y baja a la tabla; «governor» → 52 piezas, tocar la FOTO (el centro y las esquinas son su botón) abre «2 of 38», y al volver sigue «governor» en «Page 1 of 4» con la galería arriba; en el móvil (375) 3 miniaturas por fila (112×152), «Next» a 1659 px y los documentos a 1713 (en v603, 4416 y 4543) y sin scroll horizontal. Lo del propietario no se hizo en producción (esta cuenta es admin): lo prueba verif_v604, y se ensayó con los datos reales en solo lectura. ⚠️ Vistos verificando (propuestos para v605): el número de página se CORTA donde el título es largo —en la tabla (340 px: «… — installation ste…») y en el móvil en las 9 de 9 miniaturas que lo llevan—; y en el móvil las 16 píldoras de sección ocupan ~320 px y la galería empieza a 958 (en v603, 766) · romper_v604 35/35 + control (la 1ª tanda vio ESCAPAR dos roturas: las guardas de «un valor recordado que ya no vale» eran de más —Streamlit lo suelta solo, medido— y se quitaron) · verif_v604 48/48 (la 1ª vuelta, 6 rojos de la SONDA: AppTest da las píldoras ya formateadas, las fotos repetidas estaban en la página 3, …; y la sonda del giro EXIF, con una foto de un solo color, no sabía verlo: ahora mitad roja, mitad azul) · ⚠️ verif_v478 cazó un ancho fijo de 380 px (> 375, el móvil) → 340 · verif_v520, v521 y v598 al día con su razón (píldoras, las cifras nuevas, la tabla por generación) y romper_v472, v520, v521 y v598 re-ancladas: 15/15, 12/12, 4/4, 10/10 · re-corridas: romper_v449 7/7, v590 28/28 · check_anclas_roturas: 2020 vivas, 0 muertas · suite 231 verde con Python 3.12.10 (1918 s; la vuelta anterior dio 1 rojo de VERDAD, verif_v463: el tipo salía de un diccionario propio y la regla es UNA definición, `etiqueta()` → la mayúscula es solo presentación —no en VALORES: «other» y «manual» son también datos de Inventory y del parte diario—, y la suite repetida entera) |
| v603 | **Lo visto verificando v602, en toda la app.** ⚠️ Streamlit conservaba el desplazamiento al cambiar de vista (ficha nueva ~190 px abajo, en el móvil 917, el menú donde estaba la lista) → arriba al cambiar de vista, en la shell; ⚠️ un aviso al final de una página larga no se veía (-488 px) → sube a él; ⚠️ el email con un enlace VACÍO delante → markdown; direcciones tal cual; ⚠️ avisos por correo/Telegram sin escapar el texto de las personas → `notify.html_seguro`; «Issue invoice» avisa. PRODUCCIÓN (26/10/2026, cuenta admin, v603 en la etiqueta), con datos de PRUEBA: «Create client» desde el final de la lista → al acabar la pasada la ficha nueva en scrollTop 541 con «Client created.» a -415 px (lo de v602) y 170 ms después en 0, el aviso a 126 y «Back to clients» a 243; en el móvil (375) un toque en Meridian abre su ficha en 0 con el nombre a 231 (en v602, 917 abajo y el nombre a -686); las cifras siguen BAJANDO (la subida no las pisa): «No record» al máximo de su página y «Clients» a 222 con la tabla a 332, como en v602; desde Contacts bajado 254 px, «Inventory» en el menú → 0; en la ficha de Meridian el email con UN solo enlace `mailto:` y su texto (en v602, uno vacío delante); vincular Mascot desde el final de la ficha: «1 project linked.» a -586 al acabar la pasada y la página sube (suave) a 0 con el aviso a 126; CONTROL: con la ficha a 60 px y «Save record», el aviso nace a la vista (66) y la página NO se mueve; «Issue invoice» desde el final del alta → «Invoice No. 0001 issued.» y la factura arriba (0, el aviso a 126). Limpio después (copia en D:): la factura, el cliente de prueba y PRJ-0028 de vuelta a «Northline Logistics». Los avisos por correo y Telegram no se mandaron: los prueba verif_v603 con los envíos interceptados (lo de Telegram, por su documentación: no medido con un envío real); las direcciones con «*» o «<…>», en la mini-app y en verif_v603 (cliente1 no tiene ninguna) · romper_v603 25/25 + control, a la primera · verif_v603 39/39 (⚠️ la 1ª vuelta cazó un fallo MÍO: la marca `_flash_nuevo` casaba con «lo abierto» y un aviso contaba como cambio de vista —subía SIEMPRE— → `_flash_recien`; y un rojo de la sonda: un trozo de f-string, «_open_», no es una clave) · verif_v532 y v602 al día con su razón y romper_v589 y v602 re-ancladas · re-corridas: romper_v602 36/36, v589 19/19, v560 26/26, v439 8/8, v532 7/7, v600 41/41, v567 9/9, v585 5/5, v590 28/28, v562 13/13, v569 18/18, v570 15/15, v571 15/15, v575 10/10, v576 5/5 · check_anclas_roturas: 1984 vivas, 0 muertas · suite 230 verde con Python 3.12.10 (1913 s; la vuelta anterior dio 3 rojos de las SONDAS, no del código: verif_v532 cuenta los scripts de página —uno más, el de subir, con su razón—, verif_v602 esperaba el email en un <a> y check_anclas_roturas vio muertas las anclas de romper_v589 y v602 en las líneas cambiadas → al día y la suite repetida entera) |
| v602 | **Contacts → la lista, probada.** ⚠️ Un cliente archivado no se podía recuperar (la ficha buscaba solo activas y por nombre) → por su ID, archivadas incluidas, con «Restore»; ⚠️ Enter enviaba el alta a medias → sin Enter, por generación, abre por ID; ⚠️ archivar sin aviso → «Client archived.»; el archivado se distingue, filtros recordados, teléfono sin espacios, «Show all», cifras que bajan, columnas por prioridad, avance sin canceladas, «Open alerts», `tel:`/`mailto:` y email validado. PRODUCCIÓN (26/10/2026, cuenta admin, v602 en la etiqueta), con un cliente de PRUEBA archivado (CLI-0006): «1 archived client hidden — show it» marca la casilla y enseña los 8; la búsqueda «zz prueba» → «(1 client)» y en Record «Archived» (y «Hours 0.0 h», «Open alerts»); un toque abre su ficha con su nombre y «This record is archived» (en v601, «no record yet» y sin «Restore»); en la ficha, Enter NO envía, «abc» → «That email does not look right (it should be like name@company.com).», con un email bueno «Record saved.» y el teléfono `tel:0290001099` y el email `mailto:`; «Restore this record» → «Client restored.» y en la hoja Active=SI; «Archive this record» → «Client archived.» y de vuelta a la lista con la búsqueda y la casilla RECORDADAS; «0290001003» encuentra «Ryde Retail Holdings · 02 9000 1003» (en v601, nada); «No client matches the search or the filter.» y «Show all» lo devuelve todo; la cifra «No record» filtra («(2 clients)») y suelta la búsqueda; en el móvil (375) la tabla con Client · Active · Projects · Progress primero y sin scroll horizontal, y la cifra «Clients» baja la tabla de 555 a 332 px (el máximo de la página); el alta: Enter NO crea, «Create client» → «Client created.» y abre la ficha nueva por su ID, y al volver el formulario nace vacío. Los dos clientes de prueba, BORRADOS de la hoja (copia en D:). ⚠️ Vistos verificando (propuestos para v603): el email de la ficha sale con un enlace VACÍO delante (el markdown vuelve a enlazar el email que va dentro del `<a>`; medido en una mini-app: un enlace markdown con la etiqueta escapada da uno solo, también con «zz_prueba+obra*1@…», que el texto suelto enlaza MAL); y la ficha nueva se abre DESPLAZADA ~190 px (el «Client created.» y «Back to clients», fuera de la vista; abierta desde la tabla, sí sale arriba) · romper_v602 36/36 + control, a la primera · verif_v602 35/35 · verif_v440, v571 y v575 al día con su razón (el alta por generación, los plurales, abrir por ID) y romper_v440 y v571 re-ancladas · ⚠️ romper_v575 dejó escapar «el filtro deja de recordarse»: su sonda buscaba «persist_state» en el FICHERO y v602 lo puso también en la búsqueda y la casilla (trampa 2, grep ≠ uso) → la llamada del filtro, por AST, 10/10 · re-corridas: romper_v440 6/6, v446 7/7, v452 7/7, v471 5/5, v558 26/26, v569 18/18, v570 15/15, v571 15/15, v572 2/2, v576 5/5, v589 19/19 · check_anclas_roturas: 1958 vivas, 0 muertas · suite 229 verde con Python 3.12.10 (1876 s, a la primera) |
| v601 | **Lo visto verificando v600, en toda la app.** ⚠️ La 2ª petición seguida de bajar a una sección no bajaba (el mismo script, sin recargar) → un número por petición; ⚠️ la última fila de una tabla pequeña tapada por la barra horizontal → altura con la barra en toda tabla de 1–10 filas; ⚠️ vaciar una fecha guardada no la quitaba → `ui.fecha_opcional`. PRODUCCIÓN (25/10/2026, cuenta admin, v601 en la etiqueta): la lista de Inventory con 4 activos y scroll horizontal: marco 188, contenido 176 = vista 176, SIN barra vertical (en v600, 175 en 165 y la última fila tapada); «Current value» abre los informes, la fila «Consumable» filtra y baja a la tabla, y a continuación —en la pasada SIGUIENTE— la píldora «Tool» filtra («(1 asset)») y vuelve a bajar: la tabla de -52 a 17 px, a la vista (en v600 se quedaba a -164); en la ficha de ACT-0001 la próxima revisión trae su «Clear date» (⊗), y con él y «Save changes»: «Asset updated.», en la hoja NextService vacío (en v600 seguía 2026-10-01) y la campana de 8 a 7 avisos. Donde una tabla pequeña no tiene scroll horizontal queda una franja vacía de ~12 px bajo la última fila: es el sitio de la barra, el coste medido de la cura · romper_v600 41/41 + control (seis roturas nuevas: el script de bajar siempre igual, la altura sin la barra, la altura que pisa la propia, la tabla de Streamlit, la fecha creada con valor y Inventory sin el ayudante) · verif_v600 71/71 · verif_v557 al día (la fecha de alta por `fecha_opcional`) y romper_v557 re-anclada, 17/17 · re-corridas: romper_v599 36/36, v598 10/10, v487 «0 mal», v430 26/26 · ⚠️ romper_v430 dejaba en CRLF siete ficheros en LF cada vez que corría (restauraba con `write_text`, que en Windows escribe CRLF; sin cambiar una letra, pero matando el ancla en LF de romper_v599 en home_ui): ahora restaura con sus finales — medido, 11380 CRLF antes y después · check_anclas_roturas: 1920 vivas, 0 muertas · suite 228 verde con Python 3.12.10 (1885 s; la vuelta anterior dio 1 rojo de VERDAD, verif_v584: `ui.fecha_opcional` recibía el formato por `**kw` y su barrido exige DD/MM/YYYY escrito en toda llamada → el ayudante lo fija, y la suite repetida entera) |
| v600 | **Lo visto verificando v599.** ⚠️ Fantasmas que se VEÍAN durante las pasadas en toda la app → un marcador al acabar cada pasada (medido: 0 vistos); ⚠️ un 2º toque repetía el movimiento y su costo → campos por generación, paneles que nacen con lo de ahora y el motor que rechaza lo repetido; ⚠️ «bodega»/«baja» en la hoja → inglés y migración; ⚠️ un activo de baja se editaba a «available» → «written off» ⇔ Active=NO; filtros recordados, por ubicación, todo activo. PRODUCCIÓN (25/10/2026, cuenta admin, v600 en la etiqueta), con los activos de PRUEBA: el marcador instalado en la página (un <script> en su <head>: la página lo admite); en la ficha de ACT-0003, salida y devolución hasta que nace un fantasma — 6 (los campos de la salida de la generación anterior) y los 6 MARCADOS —; en dos pasadas (volver a la lista y «Assets»), 0 vistos (30 muestras con la pasada en marcha; lo viejo legítimo, visible: hasta 82 elementos); CONTROL en producción: quitada la marca, los 6 se VEN en la pasada siguiente y al acabar vuelven a marcarse; en la hoja, las devoluciones nuevas dicen «warehouse: Store» y las 5 celdas viejas migradas («written off», copia en D:); la búsqueda «foto» SIGUE al volver de la ficha («(1 asset)»); el traslado nace en «warehouse · Store», desactivado y con «The asset is already there.»; «Record service» desactivado con costo 0, con 40 se activa, «Maintenance recorded.» y el panel renace con 0 y desactivado; ACT-0002 (de baja) con el estado FIJO en «written off» y «Reactivate»; «1 written-off asset hidden — show it» marca la casilla y enseña los 4; «Service overdue» cabe en su columna (93 px de 117; en v599, cortado); una fila «Consumable» de los informes deja la lista con esa categoría y baja a la tabla; la píldora «Tool» filtra («(1 asset)»); «Nothing matches these filters.» y «Show all» lo devuelve todo; el enlace del QR (`?activo=`) abre la ficha; en el móvil, los cuatro filtros a ancho completo y sin scroll horizontal. ⚠️ Vistos verificando (arreglados en v601): una 2ª petición SEGUIDA de bajar a la tabla no bajaba (la píldora tras la fila del informe: la tabla 164 px por encima); la última fila de una tabla pequeña TAPADA por la barra horizontal (contenido 175, vista 165); y vaciar una fecha guardada no la quitaba (la revisión de ACT-0001 siguió en la hoja tras «Asset updated.») · romper_v600 35/35 + control, a la primera (también «la búsqueda se olvida al abrir una ficha»: AppTest SÍ purga el widget, la prueba vale) · verif_v600 63/63 · ⚠️ verif_v598 dio un rojo de la SONDA: su barrido no seguía un ayudante PASADO en `on_select` (`functools.partial(_tocar_informe…)`) — aprendido, 15/15; ⚠️ verif_v487 marcó la preselección del traslado (`index(...) if ... else 0`): no es un valor que se reescriba, pero eximir `_detalle` dejaba sin vigilar su formulario → un ayudante `_indice_de`, eximido con su razón · verif_v599 al día (claves con generación) y romper_v599 re-anclada (la baja escribe `BAJA`; las cifras filtran por `_filtrar`) · re-corridas: romper_v599 36/36, v598 10/10, v441 9/9, v463 11/11, v469 9/9, v487 «0 mal» · ⚠️ una batería vieja que no entiende `--anclas`, cortada con `timeout`, dejó dos roturas (catalogo_ui, projects_ui): vistas en el diff y restauradas, y los tres ficheros de vuelta a LF · check_anclas_roturas: 1914 vivas, 0 muertas · suite 228 verde con Python 3.12.10 (1926 s, a la primera) |
| v599 | **Inventory, probada.** ⚠️ «Save changes» deshacía el último mantenimiento (fechas con clave fija); ⚠️ Enter mandaba el alta y creó dos iguales → generación, sin Enter y aviso de repetidos; ⚠️ la baja pisaba la nota → confirma, avisa, motivo en la ficha, reactivar con movimiento; estado editable sin in use/written off; obras abiertas; reparación = mantenimiento; acciones bajo el título; cifras activas; ID en la tabla; campana a la ficha. PRODUCCIÓN (25/10/2026, cuenta admin, v599 en la etiqueta), con activos de PRUEBA «ZZ Prueba v599…»: a 859 px las cinco cifras, 2 por fila de 234×65 sin partir palabras; «1 written-off asset hidden.» y «(2 assets)»; la tabla con el ID primero y un toque abre la ficha, con las acciones justo bajo el título; la salida ofrece las 7 obras ABIERTAS (ni Mascot ni Chatswood, completadas, ni Penrith, cancelada), el responsable «Bobo (Admin2)» y una devolución en el pasado sale en rojo con los días anteriores en gris; «Check-out recorded.» y «Assigned to: Bobo (Admin2) · due back 05/11/2026»; «Return recorded.»; un servicio con 85.50 y la próxima revisión 15/04/2027, y después «Save changes» con una nota: en la hoja NextService SIGUE en 2027-04-15 (en v598 volvía a la vencida) y la nota guardada; a reparar → «maintenance», de vuelta al almacén → «available»; la baja con casilla → «Asset written off.», la nota intacta y «Reason: …» en la ficha; «Asset reactivated.»; una revisión vencida → «Maintenance OVERDUE: 01/10/2026», la campana pasa de 7 a 8 y su alerta abre la ficha; «Service overdue» filtra la lista; «Current value» abre los informes arriba del todo (ancho completo, traducidos); una categoría con espacios de más se guarda limpia, la misma con otras mayúsculas → «That category already exists.» y quitar ofrece solo la propia («Category deleted.»); en el alta, Enter NO envía, el nombre repetido avisa con ACT-0001 y ACT-0002 y no crea, con la casilla «Asset ACT-0004 «zz prueba v599 — taladro» registered.» y abre su ficha; «Photo saved.»; el QR en su desplegable. En el móvil (375), la lista sin scroll horizontal y la ficha con las acciones primero (un toque táctil abre la ficha; el clic de ratón sobre el móvil EMULADO no — es la emulación). ⚠️ Vistos verificando (propuestos para v600): fantasmas que se VEN durante una pasada (el «Record check-in» de una ficha aparece en la lista, reproducido en una mini-app: lo cura un `st.empty()`); un 2º toque repite el movimiento y su coste (los paneles conservan lo tecleado); la devolución y la baja escriben «bodega»/«baja» en la hoja; en un activo de baja el formulario deja poner «available»; la lista olvida sus filtros al abrir una ficha; «Service overdue» cortado en su columna · romper_v599 36/36 + control (la 1ª tanda escapó «la condición vuelve sin su etiqueta»: la sonda miraba la variable de la lista — ahora por la etiqueta) · verif_v599 46/46 (la 1ª vuelta, rojos de la SONDA: «Helper One» sin «(helper1)», el formato de `min`, un elemento de AppTest viejo y las comillas de `ast.unparse`) · verif_v449, v463, v559 y check_v487_smoke al día con su razón · ⚠️ romper_v449 dejaba escapar una rotura desde v577 (traducir un ID de Finanzas): los IDs del `else` se NOMBRAN, 7/7 · romper_v441, v487 y v598 re-ancladas (v598 10/10) · check_anclas_roturas: 1878 vivas, 0 muertas · suite 227 verde con Python 3.12.10 (1901 s; la vuelta anterior dio 4 rojos de VERDAD — verif_v547, v548, v570 y v559 — arreglados y la suite repetida entera) |
| v598 | **Un toque en la celda elige la fila en toda la app.** La cartera de Projects, Users, Inventory y Library pasan a `single-cell` (tocar el nombre solo enmarcaba; hacía falta la casilla), como Files en v592; barrido de la app entera. PRODUCCIÓN (21/10/2026, cuenta admin, v598 en la etiqueta): la cartera de Projects ya sin columna de casillas; UN toque en el NOMBRE de «Bondi Junction Tower — Lift 1» → la tira con su nombre y «Open →» (en v597 el mismo toque no hacía nada); «Open →» abre PRJ-0026 y, de vuelta por el menú, la lista LIMPIA (sin tira ni selección colgada); Planning → Users, un toque en «helper 1» abre su ficha (Access · Contact · Credentials · Their work), sin tocar nada dentro; Library (218 documentos), un toque en el título de la 2ª fila abre «Traveling cable for CWT with safety gear — installation steps» y «Back to the library» vuelve a la tabla sin reabrirlo. Inventory no se tocó en producción: cliente1 no tiene activos (no hay tabla); el mismo widget y la misma lectura se vieron funcionar en las otras tres y lo prueba verif_v598 — queda para el recorrido de Inventory · romper_v598 10/10 + control, a la primera (las cuatro tablas en `single-row` o leyendo solo `.rows`, el ayudante `_tabla_abre_obra` leyendo solo `.rows`, y Quotes en `single-row`, que solo vigila el barrido) · verif_v598 15/15 (la 1ª vuelta, 2 rojos de la SONDA: el barrido no seguía al ayudante — trampa 2 — y una prueba de «la casilla sigue valiendo», sin sentido en `single-cell`, que no tiene casillas: retirada con su razón) · re-corridas: romper_v557 17/17, v568 24/24, v567 9/9, v592 21/21, v575 10/10 · check_anclas_roturas: 1841 vivas, 0 muertas, 0 repetidas · suite 226 verde con Python 3.12.10 (1841 s, a la primera) |
| v597 | **Un decimal en las cuatro herramientas.** ⚠️ Rails guardaba «650» con «650.5» en la tabla → el decimal de la tabla; HGPR, HKPR, cortes y dibujos de la plomada con un decimal (`tabla.mm1`), cotas del plano enteras; Rails avisa lo que no encuentra en el PDF; ⚠️ el PDF de la plomada con «Línea · X inicial…» → en inglés; el rótulo HKP con sitio; check_ceros separa jornadas abiertas. PRODUCCIÓN (21/10/2026, cuenta admin, v597 en la etiqueta): Rails, Bondi L1, A 20000 y L 19500.5 / 18200 tecleadas en la tabla → «650.5 · -650.0 · 480.5 · -820.0» en la tabla y el diagrama con «L 19500.5» y «L 18200.0»; guardado como CAL-0008 con «Case 1 · A 20000 · Lift 1: 650.5/480.5, Lift 2: -650.0/-820.0» (en v596 se habría guardado «650/480»); el Caso 2 con medidas (por primera vez en producción): RZ 100, RO 120.5, RF 90, RB 95 → 1050.0 · 1029.5 · 890.0 · 885.0 en la tabla y el dibujo; un PDF de PRUEBA sin cotas → «LFKK and LFGK were not found in the drawing. Enter them by hand.» en amarillo (en v596, «Found in the PDF: none.» en verde) y uno con cotas → «From the drawing: LFKK=1150, LFGK=980 mm.»; Buffers 500 / 512.5 → «500.0 · 512.5» y «20.0 · 7.5», «cut 20.0», «HKPR 500.0» y «HKP design 520»; Belting 120 / 70.5 → «120.0 · 70.5» y «HGPR 120.0»; la plomada de Bondi L1 con BSR 1985 → «DBP 1834.0», «LT 300.0», «69.0 + 1834.0 + 82.0» en los dibujos como en las cifras; y en Files de PRJ-0026, «Reopen in the tool» sobre el PDF de Belting → «Reopened calculation CAL-0006…», la obra elegida, 120 / 70 y, como bajo quedaba el cálculo anterior, el aviso y sin descarga. El PDF de la plomada no se descargó de producción: lo prueba verif_v597 generándolo con `tool_pdf` y leyéndolo. ⚠️ Visto verificando (propuesto para v598): en la cartera de Projects tocar el NOMBRE de una obra solo enmarca la celda (`single-row`, el fallo de Files hasta v592) y «Open →» sale solo con la casilla; igual Inventory, Library y una tabla de `auth_ui` · romper_v597 22/22 + control (la 1ª tanda 20/21: escapó «X final a dos decimales» con razón — con BSR 1985.5 solo «X inicial» tenía dos decimales; la sonda pasa a BSR 1985.25 y exige las DOS columnas, y se añadió la rotura gemela) · verif_v597 33/33 (endurecida antes de fiarme: la tarjeta TIENE medidas, las X tienen dos decimales crudos, un HGPR de dos decimales llega al PDF al décimo) · verif_v589 y v593 al día con su razón · romper_v589 y v596 re-ancladas · re-corridas: romper_v596 4/4, v595 20/20, v594 12/12, v593 18/18, v592 21/21, v589 19/19, v534 37/37, v533 7/7, v532 7/7, v441 9/9, v438 12/12, v581 29/29, v540 11/11 · ⚠️ verif_v533 cazó una regresión MÍA (con 5 buffers «10.0» pisaba «HKP design 120») y verif_v441 marcó una CLAVE dentro del PDF (`f["Línea"]`): resuelto en `plumb.py` · check_anclas_roturas: 1830 vivas, 0 muertas, 0 repetidas · una batería vieja dejó projects.py con solo-CR (diff vacío): restaurado desde git · suite 225: 224 verde y 1 rojo de un DATO real (check_ceros: una jornada abierta de hoy), con el código de la app intacto — la sonda arreglada (cuenta las cerradas) y verde por separado · Python 3.12.10 (1815 s) |
| v596 | **Lo visto verificando v595: el DSTS con un decimal.** La tabla y el diagrama decían «21» y la posición, el resumen y el PDF «21.0» → un decimal en todas partes; la columna con su etiqueta (regla de v579). PRODUCCIÓN (21/10/2026, cuenta admin, v596 en la etiqueta): Bondi L1, 2 ascensores, HGPR 120 y 70.5 → la columna «DSTS (mm)», con su cabecera, enseña «21.0» y «-28.5» (en v595, «21»); la posición «21.0 mm below the top FFL» y «28.5 mm above the top FFL»; el diagrama «DSTS 21.0 mm» y «DSTS -28.5 mm» (antes «DSTS 21 mm»). Sin guardar (el resumen ya llevaba un decimal: lo prueba verif_v596) · romper_v596 4/4 + control (la etiqueta, una rotura más tras el rojo de v579) · verif_v596 8/8 · re-corridas: romper_v595 20/20, v438 12/12, v534 37/37, v532 7/7, v441 9/9, v581 29/29, v592 21/21 · check_anclas_roturas: 1807 vivas, 0 muertas, 0 repetidas · ⚠️ un parche por heredoc falló otra vez (trampa 26: los «\n» salieron como saltos de línea): a fichero · suite 224 verde con Python 3.12.10 (1815 s; la vuelta anterior dio 1 rojo de VERDAD, verif_v579: el formato de la columna iba sin etiqueta — arreglado y la suite repetida entera) |

_(y 534 versiones anteriores en `HISTORIAL.md`)_
