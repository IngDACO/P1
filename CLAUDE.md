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

41. ⚠️ **Un guion de prueba montado en OTRO orden que la shell aprueba lo que en producción
    falla.** La shell pinta los avisos de `flash` ANTES de la sección; los guiones de
    verif_v563/v564/v568/v569 los pintaban DESPUÉS, así que un aviso encolado sin
    `st.rerun()` (anular una factura, asignar una compra) salía en AppTest y en producción
    salía un clic tarde, ya en otra pantalla (v570). → El guion copia el ORDEN del
    llamador real, no solo sus datos. `verif_v570` vigila ese orden y barre la app: ningún
    `flash` sin un `st.rerun()` que se EJECUTE detrás (uno bajo el `if st.button` de OTRO
    botón no cuenta: con él como prueba, los dos fallos pasaban; ni uno bajo un `if` cuya
    condición se decide DESPUÉS del aviso, como el `if _sel:` de una tabla de más abajo).

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


## Últimas versiones desplegadas (v588 = actual)

Historial COMPLETO — las secciones detalladas y el índice de las 440 versiones — en
**`HISTORIAL.md`**. Abrilo solo para el detalle de una versión puntual; no lo cargues entero.

| Ver | Cambio principal |
|---|---|
| v588 | **Tools → Home, probada.** Tarjetas apretadas a 846 px (136 px, títulos partidos, alturas 228/225/183) → por ancho, fila igualada; la tarjeta ENTERA tocable con su último uso («Last used DD/MM/YYYY · obra»; Pre-Start, los de hoy); Pre-Start con su rama. CSS medido antes en una mini-app. PRODUCCIÓN (19/10/2026, cuenta admin, v588 en la etiqueta): a 846 px con el menú, 2 por fila de 228 × 140 px, todas iguales, títulos en una línea y nada recortado; «Not used yet» (las obras de prueba aún no tienen cálculos) y en Pre-Start «None done today»; tocar la DESCRIPCIÓN de Buffers lleva a Tools · Buffers; en el móvil (375), 2 por fila de 168 px, filas iguales (155 · 137 · 137) y las seis en una pantalla (antes 1.259 px) · romper_v588 12/12 + control · verif_v588 17/17 (una comprobación del CSS era un «or» que pasaba siempre: afinada, trampa 1) · re-corridas: romper_v566 25/25 (re-anclada), v544 22/22 · check_anclas_roturas: 1670 vivas, 0 muertas, 0 repetidas · suite 215 verde con Python 3.12.10 (1702 s; la vuelta anterior dio 1 rojo de VERDAD, check_anclas_roturas: un ancla repetida por el CSS nuevo — arreglado y la suite repetida) |
| v587 | **Las obras con desmontaje no se podían crear.** ⚠️ «New project» borraba la respuesta tracción/hidráulico (la pregunta dejaba de pintarse) y «Create project» decía «Answer this first» siempre → se queda pintada. ⚠️ Desde cotización: pregunta tracción/hidráulico, NS ≥ 2 y fecha de fin, en pantalla y motor. Lo destapó poblar la app (10 obras por los 3 caminos, en estados distintos, los 10 de campo asignados). PRODUCCIÓN (19/10/2026, cuenta admin, v587 en la etiqueta): «New project» → Ripout + Installation → «Is the lift being removed traction or hydraulic?» → «Traction» SE QUEDA marcada tras cambiar NS a 10 (fin estimado recalculado a 45 días), la fecha (14/09/2026), el cliente y la dirección (Google: «1 Parramatta Sq, Parramatta NSW 2150, Australia») → «Create project» → «Project PRJ-0034 created with 18 activities.» y el diagrama con «Set Up (rip-out)», «Take Possession», «Tirak Installation», «Full Rip-Out»; en la hoja, el plan con «Rip out mechanical components - traction». La cotización 0003 aceptada: «Turn it into a project» con el tipo fuera del form, «Stops (NS) *» con mínimo 2; Ripout + Installation pregunta tracción/hidráulico; Delivery enseña «Estimated finish date» y no NS; «Undo — back to sent» la devolvió («Quote marked as sent.»), sin crear nada. Chatswood (Ripout hidráulico) creada por el mismo formulario (AppTest), con su plan hidráulico · romper_v587 9/9 + control · verif_v587 22/22 (la 1ª vuelta, 3 rojos del ANDAMIO: el guion de la sección 3 dejaba `aceptar_y_crear_proyecto` sustituido — AppTest comparte proceso, la lección de v574) · re-corridas: romper_v470 13/13, v580 36/36, v451 5/5 · check_anclas_roturas: 1657 vivas, 0 muertas · suite 214 verde con Python 3.12.10 (1718 s, a la primera) |
| v586 | **Los partes que no movían la curva.** Obras sin plan (anteriores a v512) y la tarjeta callada: el usuario borró todas las obras (95 filas + 51 del roster, copia en D:). ⚠️ Una obra sin plan lo DICE (campo, con botón a Progress, y admin); un parte sin nada que confirmar lo dice; vocabulario de entregas y caja de herramientas medido contra el corpus (39,2 → 40,2 %); al quitar, la contrapartida antes que la logística; Expenses vacío con «New project». verif_v559 sobre la FOTO del libro (`libro_foto`). PRODUCCIÓN (19/10/2026, cuenta admin, v586 en la etiqueta): Finance → Expenses sin obras: «There are no projects in this company yet. Costs are recorded against a project: create one first.» y «New project» lleva a Projects; una obra de PRUEBA «ZZ Prueba v586» (PRJ-0026, Delivery, sin plan, sin asignados) enseña en Status → Daily logs «This job has no stage plan, so the crew's daily logs cannot suggest progress: it is marked by hand in «Progress».» — borrada después, 0 filas en ninguna pestaña. La pantalla del CAMPO (aviso + botón) no se ve con esta cuenta: la cubre verif_v586 con AppTest · romper_v586 15/15 + control (la 1ª tanda 13/14: escapó «la logística tapa la contrapartida» con razón — «Removed the inex kit» llega por su sinónimo; la sonda nueva pasa por la contrapartida) · verif_v586 51/51 · re-corridas: romper_v517 28/28, v522 17/17, v523 30/30 (re-anclada), v483 15/15, v559 35/35 sobre la foto · ejercitar_v517_corpus 0 errores · check_anclas_roturas: 1647 vivas, 0 muertas · suite 213 verde con Python 3.12.10 (1702 s; la vuelta anterior dio 2 rojos por los DATOS borrados — verif_v483 y v559 —, curados con la compra construida y la foto) |
| v585 | **Lo visto verificando v584: la vista baja a lo que se abre.** ⚠️ «Tracking options» y «Lines» abrían lo suyo y la vista se quedaba en un bloque VACÍO delante → el bloque envuelve la lista y la tabla, como en Quotes. verif_v585 barre la app: ninguna marca de bajar en un bloque vacío o ajeno. PRODUCCIÓN (19/10/2026, cuenta admin, v585 en la etiqueta, 846×646): con el periodo en «All», «Tracking options · 1 · 1 job involved» → la vista baja de 0 a 876 px y «Jobs that must exist first (1)» queda ENTERA en pantalla (488–646 de 646; en v584, a 459 con 450 de vista), con «PRUEBA MOVIL - Bondi Junction Lift 1»; con la tabla del parte FUERA de la vista (734–849) «Lines» la baja de 1322 a 1524 y queda entera (531–638 de 646: cabecera, «Bobo» y «hjg,ujgjg»; en v584 solo asomaba la cabecera). Sin datos de prueba · romper_v585 5/5 + control (las dos de Accounting, la marca de Quotes sola en su bloque, la de Hours en un bloque ajeno y bajar en CADA pasada) · verif_v585 15/15 a la primera · re-corrida romper_v584 18/18 (sus anclas del parte, dentro del bloque ahora) · check_anclas_roturas: 1631 vivas, 0 muertas · suite 213 verde con Python 3.12.10 (1693 s, a la primera) |
| v584 | **Finance → Accounting, probada acción por acción.** ⚠️ Dos avisos de ABN y uno a «Administration → Companies», que no existe → uno, con el sitio real. ⚠️ El error de Xero Payroll con sus dos causas. Cifras activas, plurales, periodo y formato recordados, «…_all.csv», «From» después de «To» avisa, «Payroll ID» solo si alguien lo tiene, avisos de Xero que dicen lo que cambia. ⚠️ TODO `date_input` en DD/MM/YYYY (10). Las baterías borran sus copias y `.gitignore` las tapa. PRODUCCIÓN (19/10/2026, cuenta admin, v584 en la etiqueta): UN aviso de ABN, «…The account owner sets it in Administration → Groups → «Tax identity and payment terms».»; las seis cifras son botones; con «All»: «1 row», «1 job involved» y «with this option»; «Tracking options» abre «Jobs that must exist first (1)» con su obra; «Expenses» lleva a Finance → Expenses y, de vuelta por el menú, el periodo sigue en «All»; «Approved» → «Invoices will now arrive in Xero approved.» y de vuelta «…as drafts.» (dejado en Draft); «Bring payments» → «No invoice has been sent to Xero yet…» sin botón; las fechas del parte «06 / 10 / 2026»; la tabla del parte SIN «Payroll ID»; Xero Payroll: «Xero did not let COPEX into Payroll. Either … or whoever connected Xero has no payroll access there…». ⚠️ Visto: «Tracking options» y «Lines» NO bajan la vista a lo que abren (la marca de bajar va en un bloque vacío ANTES, no envolviéndolo: la lista quedó a 459 px con 450 de vista y la tabla a 417) — propuesto para v585. Sin datos de prueba · romper_v584 18/18 + control · verif_v584 32/32 (la 1ª vuelta, 4 rojos del ANDAMIO: un expander con icono AppTest lo llama «Status», la última tabla era el editor de nombres, mi comentario citaba la ruta vieja y la prueba de la pantalla dejaba `render_conexion` sustituida para la siguiente — AppTest comparte proceso) · re-corridas: romper_v484 17/17, v492 8/8, v486 «0 mal» · check_anclas_roturas: 0 muertas · suite 212 verde con Python 3.12.10 (1653 s, a la primera) |
| v583 | **Lo visto verificando v582.** ⚠️ «Used in N quotes» abría Quotes con el ALTA a medias delante de la cotización pedida → el botón cierra el alta. ⚠️ El borrador del alta perdía el cliente y la nota al salir de Quotes (Streamlit borra los widgets no pintados) → `_cot_borrador`. PRODUCCIÓN (19/10/2026, cuenta admin, v583 en la etiqueta), con un servicio, una ficha y una cotización de PRUEBA (el servicio nació CAT-00002: la auditoría nombra CAT-00001 y 00003 de las ediciones de v582, la regla de v581 con datos reales): «New quote» → «➕ New client», «ZZ Borrador v583», «0400 583 583» y una nota → «Price it from the drawing» → «Set it in Catalogue» → el servicio → «Used in 1 quote» → abre «Quote No. 0001» (en v582, el alta delante) → «Back to quotes» → «New quote»: vuelven el cliente nuevo, el nombre, el teléfono y la nota, sin aviso de Streamlit. Datos: borrados (COT-0004, CLI-0001, CAT-00002) · romper_v583 6/6 + control (una 7ª rotura, «Cancel deja la nota», se escapaba y tenía razón: retirada con su razón y la línea quitada) · verif_v583 11/11 con su sonda (salir de Quotes SÍ borra los widgets) · re-corridas romper_v582 30/30 y v580 36/36 · check_anclas_roturas: 0 muertas · suite 211 verde con Python 3.12.10 (1625 s; repetida tras quitar la línea redundante) |
| v582 | **Finance → Catalogue, probada acción por acción.** ⚠️ Formularios FANTASMA (trampa 37) ocultos en TODA la app con una regla del tema. ⚠️ Un doble toque creaba dos artículos → alta que se vacía y avisa del nombre repetido. ⚠️ La edición aceptaba costo $0 → una validación. ⚠️ La regla de cantidad del plano no se podía poner → «Quantity from the drawing». Tabla con toque y costo delante, cifras que filtran, servicio sin unidad (salía «hora»), dónde se usa, tipo editable. PRODUCCIÓN (19/10/2026, cuenta admin, v582 en la etiqueta), con artículos de PRUEBA «ZZ Prueba v582…»: en una cotización nueva, «Price it from the drawing» avisa antes de subir el plano y «Set it in Catalogue» lleva al catálogo; la tabla «Item · Cost · Type · Category · Unit · Hours» sin casillas, el servicio con unidad «—» y «Service»/«Product»; un toque en la CELDA abre el artículo; «Services» filtra («1 item»); una búsqueda sin nada dice «Nothing matches this search or filter.» y «Show all» lo devuelve («3 items»); el riel a $0 guardado tal cual → «The unit cost must be greater than 0.» y con 50 → «Item updated.»; pasarlo a servicio sin horas → «A service needs estimated hours and an hourly rate greater than 0.» y con 2 h × 40 → «Service · cost $80.00»; la regla «One per stop» guardada (en la hoja: per_stop); «Item deactivated.» con el aviso nuevo y «Item reactivated.» — ⚠️ y ese cambio de forma dejó 6 fantasmas en la página, 0 visibles; el menú con un artículo abierto vuelve a la lista; el alta nace con «Materials», «zz prueba v582 riel» avisa de CAT-00001 y CAT-00002 y no crea, con la casilla crea («Item «zz prueba v582 riel» created.») y el formulario queda VACÍO; con una cotización de prueba (COT-0004) el montaje dice «Used in 1 quote» y su botón la abre; en el móvil el costo se ve junto al nombre. ⚠️ Visto: el botón abrió Quotes con el ALTA delante (seguía abierta desde «Set it in Catalogue») — propuesto para v583. Datos: todo borrado (COT-0004, CLI-0001, CAT-00001…00004) · romper_v582 30/30 + control · verif_v582 70/70 · re-corridas: romper_v463 11/11, v510 14/14, v580 36/36, v487 y v486 «0 mal», v440 ok · check_anclas_roturas: 1568 vivas, 0 muertas · suite 210 verde con Python 3.12.10 (1653 s, a la primera) |
| v581 | **«No dejes nada pendiente»: IDs que no se reciclan y la rejilla de cifras.** ⚠️ Ocho generadores (ALR, CAT, ACT, MOV, FAC, ORD, PS, COT) y las nóminas reciclaban el ID borrado (la primera cotización real habría heredado el historial de COT-0001) → `siguiente_id_libre`. ⚠️ `ids_referenciados` mira TODAS las hojas (se le escapaba PreStarts). ⚠️ El roster en lote numeraba por número de filas; lectura fallida = desde cero → a la caché; SP- repetidos; el NÚMERO de factura salía de la caché. ⚠️ La tarjeta huérfana se estiraba a todo el ancho → rejilla. Anclas repetidas vigiladas. PRODUCCIÓN (18/10/2026, cuenta admin, v581 en la etiqueta): a 846 px con el menú abierto, Status de PRJ-0015 «151+151+151 / 151» (antes la cuarta a 472 px), Costs «111×4 / 111» (antes la quinta a 472) y Timeclock «151×3 / 151»; en el móvil Costs «3 + 2» de 111 sin scroll horizontal; ninguna cifra partida. Con la ficha y el artículo de PRUEBA «ZZ … v581»: «New quote» → las cifras «151×3 / 151» («YOUR PROFIT» ya no a todo el ancho) → «Quote No. 0001 created.» y en la hoja real el ID es **COT-0004** (la auditoría guarda COT-0001…0003: saltadas). Antes, solo lectura con el código nuevo: `ids_referenciados` ve COT-0001…0003 y las 32 pestañas, PreStarts incluida. Datos: borrados COT-0004, CLI-0001 y CAT-00001 · romper_v581 29/29 + control (la 1ª tanda 27/27 antes de añadir el apóstrofo y el número de factura) · verif_v581 46/46 · romper_v559 35/35 (34 + la rotura que se saltaba) · check_anclas_roturas: 1567 vivas, 0 muertas, 0 repetidas donde se exige una · verif_v323 probado contra dos roturas · ⚠️ un parche por heredoc falló otra vez (trampa 26): a fichero · suite 209 verde con Python 3.12.10 (1607 s; la 1ª vuelta dio 1 rojo de VERDAD, verif_v323, arreglado) |
| v580 | **Finance → Quotes, probada acción por acción.** ⚠️ Una instalación creada desde una cotización nacía SIN cronograma (tipos viejos) → los de la app y el motor canoniza. ⚠️ Aceptar/rechazar sin vuelta atrás → «Undo». ⚠️ Español en producción («cotizaste», «Nº» en el nombre de la obra). ⚠️ En un borrador ya creado «Add to the quote» no añadía. «expired», cifras que cuadran y filtran, tabla con toque, fechas y color, «Markup %», la versión nueva conserva el número, nota visible y editable, obra borrada se suelta. PRODUCCIÓN (18/10/2026, cuenta admin; v580 cargado al abrir Quotes desde el menú) con datos de PRUEBA (artículos «ZZ Prueba v580» A y B, ficha «ZZ Cliente prueba v580», cotizaciones 0001 borrador, 0002 enviada y 0003 vencida): «OUT WITH CLIENTS $539 · 2 sent · 1 expired» (antes «1 sent»), las 4 cifras 2 + 2 a 846 px (antes 3 + 1 estirada) y de 168 px en el móvil con los pies dentro (87 en 137), el aviso de la vencida con «No. 0003 · ZZ Cliente prueba v580 · $396», el filtro All · Draft · Sent · Expired · Accepted · Rejected · Decided; la tabla «No. · Client · Status · Total · Expires · Date» con «🔴 expired», «🔵 sent», «⚪ draft», 13/10/2026 y la más nueva primero, sin casillas; tocar la CELDA del cliente de la 0002 la abre: «issued 18/10/2026 · valid until 17/11/2026» y «Note for the client: B enviada v580»; ⚠️ aceptarla: «Undo — back to sent», «Project name = ZZ Cliente prueba v580 — No. 0002» y los tipos «Installation · Ripout + Installation · Delivery · Ripout · Other»; con 5 paradas, «Project PRJ-0025 created from this quote.» y PRJ-0025 con CATORCE actividades (Set Up, Prepping, Plumbing & Survey…; en v579 PRJ-0024 nació con UNA, «Execution»); la comparación «you quoted $100 · nothing yet» (antes «cotizaste $100 (-100%)»); «Open» lleva a la obra con «0 h worked» (antes «0.0 h»); borrada PRJ-0025 desde el motor, la 0002 dice «The project PRJ-0025 created from this quote no longer exists.» y «Unlink it» → «Project PRJ-0025 unlinked from the quote.» y vuelven «Undo» y «Create the project»; «Undo» → «Quote marked as sent.»; tocar «Quotes» en el menú con la 0002 abierta vuelve a la lista; ⚠️ el borrador 0001: impuesto y nota editables, «Add to the quote» con el artículo B SE QUEDA (subtotal $298 = $250 + $48) con «Save changes» / «Discard changes», el selector vacío y «effective markup 24.2%»; cambiada la nota y guardado: «Quote updated.» y en la hoja «Nota cambiada v580», total $327.80 y las dos líneas; la 0003 «expired» (no «overdue»): rechazarla saca «Undo» y deshacerla la devuelve a «expired»; «New version» → «Version 2 of No. 0003 created.», «Quote No. 0003 v2» y «new version of v1»; crear una nueva → «Quote No. 0004 created.». ⚠️ Truco del entorno: un clic «fuera» para soltar un campo cayó en «Fork» de la cabecera de Streamlit y llevó la pestaña a share.streamlit.io («create-from-fork», en blanco): «back» al momento, nada hecho allí, y la cookie restauró la sesión — para confirmar un campo, Ctrl+Enter, no un clic. Datos: todo lo de prueba borrado (5 cotizaciones, la ficha, los 2 artículos y PRJ-0025); quedan sus líneas en la auditoría · romper_v580 36/36 + control, a la primera · verif_v580 73/73 (el único rojo de su 1ª vuelta era MI cuenta: 3 aceptadas de 4 son 75 %, no 67 %) · guardianes al día con su razón: verif_v451 (exigía la lista vieja de tipos: protegía el fallo), verif_v420 (las dos salidas limpian con un helper) y verif_v452 (la celda pasa por `_est_celda`); y dos rojos de VERDAD arreglados en el código: verif_v570 (el aviso «la ficha ya existía» se encolaba antes de saber si la cotización se creaba) y verif_v452 (`_etq` importado dentro de una función de `quotes.py`) · cinco anclas re-ancladas (romper_v440, v450, v452, v563, v564) y 14 baterías re-corridas: v440 6/6, v450 7/7, v451b 5/5, v452 7/7, v563 24/24, v446 7/7, v453 5/5, v455 3/3, v470 13/13, v471 5/5, v509 12/12, v512 22/22, v547 6/6 y v564 38/38 — romper_v470/v471 no arrancaban sin la variable `SCRW` (su carpeta por defecto) y romper_v564 retira, con su razón, la rotura de la cabecera «Hours» (desde v579 la traducción la pone `tabla.cfg`) · check_anclas_roturas: 1538 vivas, 0 muertas · ⚠️ dos parches por heredoc fallaron otra vez (trampa 26): escritos a fichero · suite 208 verde con Python 3.12.10 (1620 s, a la primera) |
| v579 | **Finance → Profitability, probada acción por acción.** ⚠️ Una obra con ganancia FIJA salía «sin ganancia» (también en el «No margin» del Resumen) → por el modelo; margen sobre el ingreso. ⚠️ Horas facturadas a costo sin aviso → aviso con nombres. ⚠️ Cabeceras en español (también en la tabla de avance del campo) → `tabla.cfg` conserva la etiqueta traducida. Céntimos, cifras y avisos activos, un toque abre la obra en Costs. PRODUCCIÓN (14/10/2026, cuenta admin; v579 cargado al tocar Profitability en el menú): las cabeceras «Project · Cost · Est. revenue · Est. profit · Margin % · Invoiced · To invoice» (antes «Costo», «Ingreso estimado», «Ganancia», «Facturado») y los importes con céntimos ($134.40, $132.55, $3.15; antes $134, $133, $3); cinco cifras-botón, 2 / 2 / 1 con 690 px de contenido, 3 + 2 a 1300 px y 2 / 2 / 1 de 168 px en el móvil (antes «To invoice» sola a 353), con todos los pies dentro (el más largo, 119 px en 137); el aviso de obras sin ganancia con un botón por obra. ⚠️ Con $50 FIJOS en PRJ-0015 (motor, obra de prueba): «2 job(s) with no profit set» SIN ZZ PRUEBA (en v578, 3 con ella), «ESTIMATED PROFIT $50 · 15.6% of revenue» en verde, su fila «$3.15 · $53.15 · $50.00 · 94.1%» (antes 0.0%) y el Resumen «No margin · 2 jobs» (antes 3). ⚠️ Con ganancia por hora solo para Admin2: «Hours invoiced at cost» con «ZZ PRUEBA v519 - pantalla del campo · hjg,ujgjg» (el NOMBRE de campo000), y el botón la abre en Costs (`&p=PRJ-0015`, con los editores de ganancia). «To invoice» abre lo pendiente («88 walker st · $134», «PRUEBA MOVIL … · $133», «ZZ PRUEBA … · $4») y «PRUEBA MOVIL» abre el alta de factura de esa obra (sin ficha de cliente lo dice y ofrece crearla; se canceló sin crear nada); un segundo toque cierra la lista. Un toque en la tabla abre la obra en Costs (`&p=PRJ-0002`). ⚠️ Truco del entorno: con la vista EMULADA del panel, el clic cae ~45 px por ENCIMA de lo que marca la captura — tocando la fila de ZZ se abrió 88 walker, y antes, el botón «ZZ PRUEBA · $4» de encima (el alta de factura): que cada fila abra la suya lo prueba verif_v579. La tabla de avance del CAMPO no se ve con esta cuenta: la cubre verif_v579. Datos: PRJ-0015 vuelta a como estaba (las dos celdas de ganancia vacías; quedan sus líneas en la auditoría); nada creado · romper_v579 23/23 + control, a la primera · re-corrida romper_v566 (su guardián, al día con su razón: el «No margin» por `a_costo`): 25/26 — escapó «una cabecera de By project vuelve a la clave en español», y con razón: desde v579 `tabla.cfg` pone la traducción aunque la columna pierda su etiqueta → retirada con su razón (la causa la vigilan romper_v579 y el barrido de verif_v579) y re-corrida, 25/25 · check_anclas_roturas: 1502 vivas, 0 muertas · verif_v579 45/45 a la primera · suite 207 verde con Python 3.12.10 (1620 s, a la primera) |
| v578 | **Lo visto verificando v577.** Las cifras de Horas 2 / 1 / 2 a 1024 px → una fila que parte sola (`theme.por_fila`); «Person» de ~57 px cortando nombres → ancho del nombre; la matriz alineada a su aire → a la derecha; ⚠️ tocar a un administrador llevaba a Users sin abrir nada → Users dice por qué (para todos los que enlazan) y su tarifa, al propietario. PRODUCCIÓN (14/10/2026, cuenta admin; v578 cargado al desplegar el menú de Finance —la «r» no relanzó—): con 640 px de contenido las cinco cifras de Horas en 2 / 2 / 1, seguidas y de 296 px (antes 2 / 1 / 2 con un hueco), y a 1200 px en 3 + 2, todas de 365 px; «Person» de 96 px en la tabla por persona y en la matriz, con «hjg,ujgjg» (51 px) entero (antes ~57 px y cortado); las celdas de la matriz pintadas con `textAlign: right` todas («3.36» y «0.14» salían a la izquierda); el periodo «All» recordado de la sesión anterior; tocar «Bobo» (administrador) en la matriz lleva a Users con «Bobo is not a field user (administrator): their record and hourly rate are kept by the owner, in Administration → Users.» (antes, Users sin abrir nada). A 640 px la matriz se desplaza en horizontal con «Person» fijada: los nombres de obra son largos y con obras reales siempre habrá más columnas de las que caben (trampa 22: priorizar, no encoger). Datos: nada escrito · romper_v577 ampliada a 35/35 + control, a la primera (9 roturas nuevas: las cifras partidas fila a fila, la regla de 700 px delante, la persona sin ancho o con ancho fijo, la matriz con números sueltos o sin alinear, el administrador mandado a Planning, Users perdiendo en silencio y alguien sin cuenta dado por administrador; dos anclas viejas re-ancladas a la sangría nueva) · check_anclas_roturas: 1479 vivas, 0 muertas · ⚠️ el parche de las cifras falló una vez por un heredoc (trampa 26): escrito a fichero, a la primera · suite 206 verde con Python 3.12.10 (1576 s, a la primera) |
| v577 | **Finance → Hours, probada acción por acción.** ⚠️ Un periodo vacío dejaba la pantalla en blanco → cifras a 0 y el periodo más amplio a un toque. ⚠️ Los periodos contaban un día de más → «Last 7/30 days» exactos, segmentado y recordado. ⚠️ Las horas por obra sumaban por NOMBRE → por ID. Cifras que ordenan, «$40.00», un toque abre la persona, la obra o la localización (también en la matriz), textos con `t()`, y Horas con su rama en el menú. PRODUCCIÓN (14/10/2026, cuenta admin, 1024 px; v577 cargado con «r» en la sesión abierta): «Today» vacío enseña las cinco cifras a 0, «No time entries in this period.» y «See last 7 days» / «See all» (antes, la pantalla en blanco); «See last 7 days» cambia el periodo: 1 persona y «UNALLOCATED 0.1 h · 53% of the workday» en rojo (#c0392b en borde y cifra); «All»: «PEOPLE 3 · WORKDAY 3.9 h · ON PROJECTS 3.8 h · UNALLOCATED 0.1 h · LABOUR CHARGED TO JOBS $142», la tabla con «$40.00», «—» y «$138.00», y las horas por obra con el nombre ENTERO («PRUEBA MOVIL - Bondi Junction Lift 1»: 218 px de texto en 235) y su barra; un toque en «hjg,ujgjg» abre su ficha en Planning → Users y «←» vuelve a Horas en «All» sin reabrirla (12 s mirando); un toque en «ZZ PRUEBA v519» abre PRJ-0015 (`&p=PRJ-0015`); en la matriz, la celda de Bobo en ZZ PRUEBA abre PRJ-0015. ⚠️ Vistos verificando (arreglados en v578): a 1024 px las cifras salen 2 / 1 / 2 con un hueco; «Person» mide ~57 px y corta «hjg,ujgjg» (51 px de texto + relleno, medido interceptando `fillText`); la matriz alinea cada columna a su aire (la que tiene huecos, texto a la izquierda); y tocar a «Bobo» (administrador) en la matriz lleva a Users y NO abre nada: Users solo tiene fichas del campo. Datos: nada escrito · romper_v577 26/26 + control, a la primera (y otra vez tras el arreglo) · re-corridas las que rompen lo tocado: romper_v544 22/22 (Horas desde el Home: su guardián, al segmentado `cpxseg_gh_per` con su razón) y romper_v483 15/15 (verif_v483: «ninguna sub-sección cae al else», antes «exactamente una», con su razón) · check_anclas_roturas: 1469 vivas, 0 muertas · verif_v577 55/55 (los 3 rojos de su 1ª vuelta eran de la SONDA: las filas falsas del motor no traían la columna «Project» de la que sale el nombre) · suite 206 verde con Python 3.12.10 (1578 s), en su 2ª vuelta: la 1ª dio 203 + 3 rojos de VERDAD — check_colcfg y verif_v444 (la columna «On overhead (h)» configurada siempre y la fila solo la trae con estructura → su formato, solo entonces) y verif_v450 (un mapa espejo `{"general": "general", …}` usado de lista blanca → una tupla); arreglado el código, romper_v577 y la suite enteros otra vez |
| v576 | **Lo visto verificando v575.** A 640 px las cifras de Contacts (y las del resumen del cliente y de Payroll) se apilaban una por fila → `theme.dos_por_fila`, 2 por fila en estrecho. PRODUCCIÓN (13/10/2026, cuenta admin, panel emulado a 640 px; v576 cargado con «r»): la lista de Contacts con sus cuatro cifras 2 por fila (301 px cada una, en dos filas; antes una por fila de 607), la ficha de «Cliente de prueba» —abierta tocando su celda— con las seis cifras del resumen 2 por fila (tres filas de 301), y Payroll con las suyas 2 + 1. Datos: nada escrito · romper_v576 5/5 + control · romper_v571 15/15 y romper_v575 10/10 re-corridas (cambió la estructura de las cifras) · suite 205 verde con Python 3.12.10 (1605 s, a la primera) |
| v575 | **Nada pendiente.** La cotización con nombre legal, ABN y DD/MM/YYYY; la lista de Contacts con cifras que filtran y un toque; el panel del propietario al día y sin español suelto. ⚠️ Las anclas de TODAS las baterías leídas por su posición: 27 muertas (la deuda decía 10), re-ancladas; el comprobador exige cero. PRODUCCIÓN (13/10/2026, cuenta admin; v575 cargado con «r»): la lista de Contacts con cuatro cifras-botón «CLIENTS 2 · WITH RECORD 0 · NO RECORD 2 · PROJECTS 3» (ningún `st.metric`) y el selector All · With record · No record · With jobs; «With record» → «No client matches the search or the filter.»; «No record» → los 2 clientes. ⚠️ Visto verificando (arreglado en v576): a 640 px las cuatro cifras se APILABAN una por fila (607 px de ancho cada una, 400 de alto). La cotización y el panel del propietario no se pueden ver con esta cuenta (no hay cotizaciones en cliente1; el panel es del propietario): los cubre verif_v575. Datos: nada escrito · romper_v575 10/10 + control · las 12 baterías re-ancladas, re-corridas: romper_v430 26/26, v438 12/12, v440 6/6, v445 7/7, v446 7/7, v450 7/7, v455 3/3, v461 11/11, v463 11/11, v472 15/15, v544 22/22 y v560 26/26 — y lo que salió al correrlas: ⚠️ romper_v438 solo RESPALDA los ficheros de su `F` y la rotura re-anclada en `stages.py` se quedó APLICADA al fallar la restauración (visto en `git diff`, restaurado desde git; `stages` entra en `F`); romper_v446 dejaba escapar «se traduce el ESTADO que se escribe en la hoja» porque con el inglés de base `t("In progress")` devuelve lo mismo → verif_v446 mira también el CÓDIGO de derive_estado; romper_v463 retira «'Otros' fuera del mapa» con su razón (desde v469 la categoría se canoniza al leer: la entrada ya no protegía nada); romper_v461 cayó por la consola cp1252 (trampa 23) y con UTF-8 caza 11/11. check_anclas_roturas, a la primera: 1436 vivas, 0 muertas, 0 ilegibles, 0 sin forma, y su sonda ve los cuatro huecos · suite 204 verde con Python 3.12.10 (1593 s, a la primera) |
| v574 | **Finance → Payroll, probada acción por acción.** ⚠️ Anular: un clic sin preguntar ni avisar → confirma, diferida y avisa; una pagada no se anula. ⚠️ «Mark as paid» sin vuelta atrás → deshacer. ⚠️ Las anuladas desaparecían; homónimo falso; dinero sin céntimos; la tarifa TRUNCADA al generar. Cifras que filtran, DD/MM/YYYY, estado traducido, conceptos a la vista y legibles, la colilla con nombre legal y ABN. PRODUCCIÓN (13/10/2026, cuenta admin, 1024 px; v574 cargado al reabrir el panel —la cookie restauró la sesión—): dos colillas de PRUEBA de un usuario ficticio (NOM-0001 $320.78 → neto $288.70 con retención y super; NOM-0002 $122.20); cifras «TO PAY $410.90 · 2 issued and unpaid · PAID $0.00 · PAYSLIPS 2 · 2 period(s)», filtro All · To pay · Paid · Voided, «All periods»; la tabla entera a 660 px: «ZZ Prueba nomina» (sin el login), «🟠 issued», «$288.70», «01/09/2026 → 07/09/2026», «$320.78», «$30.55», y el pie «base pay $442.98 · net $410.90»; un toque abre la colilla: «Period 01/09/2026 → 07/09/2026 · 10.5 h × $30.55 = base pay $320.78 · issued», fecha de pago 13/10/2026 y los conceptos a todo el ancho («Deduction $32.08», «Employer contribution $36.89»); «Mark as paid» → «Payslip marked as paid.» y «Paid on 13/10/2026.», sin «Void» y con los conceptos bloqueados; ⚠️ «Undo payment» PREGUNTA y, con «Yes, undo it», «Payment undone: the payslip is unpaid again.» a los 2 s; ⚠️ «Void this payslip» PREGUNTA («It cannot be undone.») y «Payslip voided.» a los 2 s en el propio detalle; la anulada, en «Voided» («⚫ voided») y fuera de las cifras («TO PAY $288.70 · 1 issued»); generar: frecuencia segmentada, «07/10/2026 → 13/10/2026», ⚠️ «No hourly rate: hjg,ujgjg — they will be skipped…» ANTES de generar y con el botón a Users, y la vista previa con céntimos (base 7.65; salía «$8»); no se generó nada. El PDF (generado en local con las filas reales): «01/09/2026 → 07/09/2026» y «issued» / «voided»; la cabecera dice «cliente1» porque ese grupo NO tiene nombre legal ni ABN (se ponen en el panel del propietario: Groups → «Tax identity and payment terms»); con ellos, lo prueba verif_v574. Truco: con el panel del navegador sin pintar, un toque en una tabla (canvas) se PIERDE —3 de 3 tras «Back»—; tras una captura, que obliga a pintar, abre a la primera: era el entorno, no la app. Datos: las dos colillas, borradas desde el motor · romper_v574 22/22 + control (verif_v574: los rojos de su 1ª vuelta eran de la SONDA —el guion de AppTest corre en el mismo proceso y dejaba `payroll.anular` sustituido, así que «el motor» probaba el doble → se recarga el módulo; y `ast.walk` visita cada constante dos veces, «Payslip_» contaba 4 → por las f-string—) · baterías viejas: romper_v486 9/9 (y ahora borra sus copias `_v486r_*`, que se quedaban sin ignorar), romper_v452 7/7, romper_v440 5/5 vivas, romper_v436 7/7, romper_v441 9/9 y romper_v442 6/6 — estas tres, re-ancladas: «All periods» (y la frase de la conciliación, desde v566) están hoy dentro de `t()`, y el selector de estado y la etiqueta QR eran anclas MUERTAS que check_anclas_roturas tenía por «ilegibles»; verif_v436 dejaba de comprobar los PDF con la demo vacía (paso en vacío) → usa una factura, cotización y colilla CONSTRUIDAS · suite 203 verde con Python 3.12.10 (1582 s, a la primera) |

_(y 512 versiones anteriores en `HISTORIAL.md`)_
