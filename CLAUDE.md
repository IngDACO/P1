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

⚠️ **Un despliegue NO reinicia el servidor** (v618: 0 reconexiones, la sesión abierta sigue). Un cambio
en `.streamlit/config.toml` que se lea al arrancar no actúa hasta **Settings → Reboot app**, que solo
puede hacer el usuario y cierra todas las sesiones (v619: `disconnectedSessionTTL`).

## Guardianes: la suite de verificación (`guardianes/`)
`verif_*.py` (afirmaciones) · `romper_*.py` (baterías de roturas) · `run_suite.py` (la
suite ENTERA, regla v385) · `tanda.py` (la tanda de una versión) · `doc_v*.py` (documentar
una versión) · `ejercitar_*_real.py` (contra la hoja real, método v344). Los de un solo uso,
en `guardianes/sueltos/`.

```powershell
cd C:\Users\diego\P1\guardianes ; $env:PYTHONIOENCODING="utf-8" ; py -3.12 tanda.py --salida=CARPETA
```
`--sin=romper_vNNN` salta una batería nueva y larga que ya pasó (romper_v625: 32 min). Una batería puede dejar un fichero en LF: no cuenta como tocado (la huella ignora los finales de línea).

**`tanda.py` (01/11/2026): suite → baterías → anclas, en ese orden**, y si la suite está en rojo no
corre las baterías. Elige las viejas `baterias_afectadas.py` (las que anclan a ≤3 líneas de lo
cambiado o corren un guardián cambiado), que en v617 acertó dos que se me habían pasado a mano; las
nuevas van siempre y SIN corte. Tras cada batería compara el código: una que deje una rotura puesta
para la tanda. La suite tarda 4-5 min (eran 35), una batería entre un 40 y un 50 % menos.
`arnes/sitecustomize.py` entra por PYTHONPATH solo con `run_suite.py` y `tanda.py`, sin tocar ni un
guardián: apunta lo que sale a la red, guarda cada lectura de la hoja para toda la tanda (30 lecturas
reales, eran 1100; la app comparte esa cuota) y corta el guardián en su primer FALLO en las baterías.
⚠️ Las lecturas guardadas son datos reales: en una carpeta temporal que se borra al acabar.
⚠️ **El arnés PARA toda escritura en Sheets o Drive, Telegram y correo** (v643), y un intento pone la suite en rojo. Una batería suelta sin
`PYTHONPATH=guardianes/arnes` no lo lleva: se lanzan por la tanda. Lo que imprime la suite al final (`Escriben en la hoja real`, `Salen a otros sitios`) se lee.
⚠️ La suite corre en paralelo (`run_suite.py --procesos=1`, de uno en uno) con `cwd=survey_app` (lo
hace el runner), y pasarse de 50 lecturas/min es ROJO. ⚠️ **Nunca en paralelo con una batería** (v455):
las baterías modifican el árbol y lo restauran. La suite NO (v573: `run_suite.py` pone en rojo al
guardián que cambie un byte del código de la app; un guardián valida sus sondas EN MEMORIA).
`run_suite.py verif_v57` filtra por nombre; para desplegar, siempre entera. Lo que generan al correr
está en `.gitignore` — en especial las fotos de la hoja, que son **datos reales**.
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
│   ├── falsecar.py/_pdf/_ui # Daily False Car Checklist (hoja FalseCarChecks, v636): los 18 puntos, vive dentro de Pre-Start;
│   │                       #   se exige de lo MARCADO (Install sky climber → Remove…), no del calendario; `dias_sin_registro` = lista de oficina
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
│   ├── tareas.py/_ui       # «To-do» de la obra (hoja Tasks, v615): UNA lista por obra; marca cualquiera,
│   │                       #   borra el autor o la oficina (oculta: Active=NO); no acredita avance
│   ├── hojas.py            # lector por LOTES del libro (1 batchGet para todas las hojas, v339);
│   │                       #   una hoja creada por OTRO proceso entra en ≤10 min (`_indice_al_dia`, v611)
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
    parecían regresiones. Se corren con `cwd=survey_app`. Y ⚠️ sin amontonar lecturas de
    la hoja real, con un techo de 60/min — es provocarse un 429 y volver a leer un rojo
    falso (es el error de v377, cometido en el script que venía a verificar). Desde el
    01/11/2026 lo cuida el arnés (trampa 47).
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
    con AppTest en verde, porque AppTest lee el SERVIDOR. ⚠️ Una tercera en v620: borrar el valor del
    control al restaurar la sesión, con su guardián en verde porque preparaba a mano una clave que en
    una sesión recién nacida ni existe. → Lo que depende del navegador se mide en el navegador; para
    limpiarlo de verdad, recargar (v622, `auth_ui._RECARGAR_SI_VIEJA`). Un `data_editor` con clave y filas
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

45. ⚠️ **Lo que crea un script mío en el libro NO lo ve al instante el proceso del Cloud.** (v610)
    Sembré `AgentMemory` desde local y producción dijo «Nothing learned yet» con 8 filas en la hoja: el
    índice de pestañas (`timeclock._libro`, `cache_resource`) era de antes y el lote solo pide lo que
    hay en él. Desde v611 se rehace como mucho cada 10 min (`hojas._indice_al_dia`), así que tras crear
    una hoja desde fuera hay que esperar hasta 10 min (o que la app escriba en ella: `get_sheet` rehace
    el índice) antes de concluir que «no sale». Es la nº 11 (lo local no es lo del Cloud) en el tiempo.

46. ⚠️ **`st.form` envía con Enter por defecto, y en un formulario de varios campos eso guarda a
    medias.** (v617) Un Enter en el importe guardó un recibo sin proveedor ni foto; el «Ir» del teclado
    del móvil hace lo mismo. → Todo formulario de 2 campos o más lleva `enter_to_submit=False`
    (lo vigila `verif_v617`); los de UN campo (la caja de «To-do») lo conservan. ⚠️ Y al teclear desde
    el panel en un `number_input` DENTRO de un formulario: sin Enter, o se envía el formulario.

47. ⚠️ **Lo que «se sabe» de la propia suite también se mide.** (01/11/2026) Este documento decía que
    16 guardianes leían la hoja real, y por ellos dormía la suite 2,5 s tras cada uno. Medido con el
    arnés: 110 guardianes y 1351 peticiones, casi todas la misma lectura de arranque (`clock` lee los
    grupos), y 9 de los «16» no la leían. Con la lista de memoria, el paralelo habría ido a ~180
    lecturas/min contra un techo que comparte producción, y SIN un solo rojo: `timeclock` reintenta los
    429. → Y antes de alarmarse por un dato raro, mirar cómo se midió: el host «is.com» que apareció
    era mi registro, dos hilos pisándose la línea (el trozo final de «googleapis.com»).
    ⚠️ Y **tres pasadas limpias en paralelo no prueban nada** (v618): la primera suite tras tocar código
    dio 2 rojos. Windows rechaza reemplazar un fichero que otro proceso tiene abierto, y eso rompía la
    lectura guardada y `py_compile` (siempre escribe el .pyc; lo usan 33 guardianes). → Una carrera se
    prueba provocándola: borrar `__pycache__` y varias pasadas sin memoria a más procesos.

48. ⚠️ **Un guardián no ve lo que el escapado cambia, ni estrena proceso.** (v625-v627) Los guiones de AppTest corren en
    el MISMO proceso: lo sustituido en uno (`TR.registrar`) sigue puesto en el siguiente, y el guardián probaba el falso →
    guardar lo real al principio del guardián. Y con `literal_md`, «(automatic)» llega como `\(automatic\)`: la comprobación
    `"(automatic)" not in texto` no veía nada, lo destapó la rotura → se busca la palabra, sin los signos.

49. ⚠️ **Un botón `cpxkpi_*` de DOS líneas pinta el número como un pie** (12 px y gris). El tema agranda la cifra con
    `p:nth-child(2):not(:last-child)`, que exige TRES líneas (v628, medido). Belting, Buffers y Rieles van así porque sus
    valores largos no cabrían a 26 px; una cifra corta lleva pie.

50. ⚠️ **Cambiar de modelo no es cambiar el nombre.** Sonnet 5.5 razona por defecto: la respuesta puede empezar por un
    bloque `thinking` (sin `.text`), el razonamiento gasta del mismo `max_tokens` y un rechazo llega como 200 con el
    contenido vacío → leer por `type`, mirar `stop_reason` antes y decir `output_config.effort` (`chat_agent._texto_de`,
    verif_v632). Y una regla en el prompt no basta: lo que debe decir va como pasos concretos y se pregunta de verdad.

51. ⚠️ **Un PDF se MIRA, y a ZapfDingbats se le da el carácter.** (v636) `<font name="ZapfDingbats">4</font>` pinta un cuadro
    negro en cada ✓, sin error: reportlab espera el carácter Unicode (`✓`), no su byte. Solo se vio renderizando el PDF; el
    guardián cuenta los ✓. En `py -3.12` no hay rasterizador: `pip install --target <scratchpad> pypdfium2`, fuera del proyecto.

52. ⚠️ **Lo que el modelo hace no lo prueba un modelo simulado.** (v641) Con guardianes en verde, el examen real destapó que reintentaba una acción
    sin que nadie se lo pidiera y que negaba haberla hecho: de los turnos anteriores solo ve el texto, no sus herramientas. → Un cambio en lo que
    el agente puede HACER lleva examen real (con permiso, con las escrituras bloqueadas y contadas), y la descripción de una herramienta es
    parte de su comportamiento: la palabra «remember» bastó para que apuntara en To-do lo que solo debía recordar.

53. ⚠️ **Una rotura puede llevar al guardián a lo REAL, y la suite ya avisaba.** (v643) `romper_v623` quitaba una validación y el guardián seguía hasta `alerts.report_problem`: 4 pasadas,
    4 alarmas en cliente1 y aviso a 5 cuentas, todas con la fecha FIJA del guardián. `verif_v640` escribía en `ChatMemory` en cada suite, con el aviso impreso y sin leer. Lo vio un examen,
    no un guardián. → El arnés lo para abajo del todo; sustituir en cada guardián no basta, porque una rotura abre caminos que el guardián en verde nunca pisa.

54. ⚠️ **A un modelo hay que darle el día, con el mes en letras, y el idioma justo antes de responder.** (v643) Sin fecha leyó 03/11 como marzo y eligió 2025; con «03/11/2026, day first» aún
    entendió febrero. Con la guía en español arrancaba en español con datos delante, aunque la regla estuviera dos veces: citarle su pregunta tras los resultados lo dejó en 0 de 7. Y un total a 0
    no se explica solo: dijo «no hubo horas» porque el P&L cuenta nóminas. Lo que una cifra NO incluye va en lo que devuelve la herramienta.

55. ⚠️ **Al compartir una función, una protección queda doble, y la rotura de una ya no se ve.** (v644) Absences y Time fixes miran la empresa en la bandeja y otra vez en
    `decidir` y `hacer`, que comparte el Management assistant. Las roturas de v555 y v556 quitaban la de la bandeja y la prueba (aprobar) seguía en verde: la otra lo paraba.
    Pero cancelar solo pasa por la bandeja, y el asistente llama a `hacer` sin ella. → Cada protección se prueba por el camino donde es la ÚNICA.

56. ⚠️ **Lo que la app escribe con la voz del asistente, el modelo lo toma como suyo y lo niega.** (v645) Tras Confirm, «✅ … assigned» iba como turno del asistente;
    en la pregunta siguiente dijo «I hadn't confirmed that» con la asignación hecha (2 de 2 en producción). Ni la regla «no te corrijas» bastó. → Lo que no dijo el
    modelo no va como suyo: `chat_agent._para_el_modelo` lo manda como nota de la persona, y la marca (`app`) se guarda con la memoria.

57. ⚠️ **Una batería no se carga para leerla: algunas ARRANCAN al importarse.** (v646) Para ver sus roturas importé romper_v516 (sin `if __name__`),
    se puso a romper el árbol, y al pararla dejó una rotura puesta en `daily_log.py` (el tope del parte ×1000). → Se leen del TEXTO (grep o
    `anclas_lectura`), nunca con `exec_module`; y si una se para a medias, `git diff` de sus ficheros antes de seguir.

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

**Modelo:** el asistente y el resumen del día, `claude-sonnet-5-5` con esfuerzo `low` (v632, v647) y las dos interpretaciones del Survey (v652). Vía librería `anthropic`. Requiere `ANTHROPIC_API_KEY`.

### interpretation.py — dos generadores
- `generate_interpretation(calc_results, all_params)` → dict ADMIN (7 claves):
  parametros, estado_inicial, desplazamientos, solucion_optima, evasion_pared, bsr_vs_bs, consideraciones.
- `generate_user_interpretation(calc_results, all_params)` → dict CLIENTE (5 claves):
  resumen, desplazamientos, cortes, implementacion, verificacion. Orientado a IMPLEMENTACIÓN
  (qué desplazar, por qué, qué cortar), profesional, SIN fórmulas internas.
- **v652 · los datos los pone la app** (`hechos`: sentidos —RL+ IZQUIERDA, FB+ ATRÁS—, lo que SIGUE fuera, cortes de
  `cortes_por_piso`); del cliente, «desplazamientos» y «cortes» los ESCRIBE la app. `revisar` comprueba mm, sentidos,
  «todo resuelto» y el procedimiento (plantilla de plomadas, nunca mover una cabina): un 2º intento; si no, no se publica.
- `_ok=False` en la interna: el correo sale sin el informe. El del CLIENTE ya no se bloquea (lo de la app + aviso).
- En el Survey (`survey_ui`): siempre de la solución ACTIVA (`_ia_vieja`), «Rewrite the interpretation» sin recalcular,
  y el texto del cliente en cajas editables (`_iu_final`) que van al PDF y a la obra.

### chat_agent.py — asistente experto (sidebar desplegable)
- `get_chat_response(user_message, history, calc_results, all_params)`.
- System prompt = experto COPEX en instalación Schindler + **contexto del cálculo actual** (si existe).
- **Confidencialidad (v27):** NO revela fórmulas internas, algoritmos, lógica del optimizador,
  nombres de módulos/funciones ni flujo interno. Sí interpreta resultados y explica conceptos físicos.
- Historial en `session_state["chat_history"]` (máx 20 mensajes).

### chat_tools.py + chat_ui.py + chat_memoria.py — el Field assistant con autonomía (v639-v641)
Tres niveles, decididos por el usuario: VER (`LECTURA`), PREPARAR Y CONFIRMAR (`PREPARAR` + tarjeta con **Confirm**: el parte, el aviso a la
oficina y las ausencias; preparar NO escribe, lo hace `confirmar`) y ACTUAR SOLO (`DIRECTAS`: To-do, y nada más). Fichar, firmar, enviar el
Pre-Start o el checklist y acreditar avance no existen como herramienta. Bucle en `chat_agent._conversar`. ⚠️ `ctx` sale de la SESIÓN: ninguna
herramienta recibe un usuario, y `project_id` se comprueba contra sus obras (`_obra`). El turno del asistente vuelve entero (razonamiento
incluido), y lo que devuelven es DATO, nunca una orden. Solo el campo identificado. Memoria: hoja `ChatMemory`, una fila por persona, 14 días.
Fotos: una por pregunta, nunca guardadas. Ausencias: `ausencias.problema_solicitud` y `ausencias_ui.registrar`, una sola definición con la pantalla.
⚠️ Un examen real destapa lo que un simulado no: `sueltos/examen_asistente*.py`, gasta y escribe: con permiso.
**Management assistant (v643-v644):** mismo motor. Ve cinco consultas (`LECTURA_OFICINA`), dinero incluido, sin nóminas por persona. Hace To-do directo y cinco con tarjeta
(`PREPARAR_OFICINA`), cada una con la función de su pantalla (`ausencias_ui.decidir`, `correcciones_ui.hacer`, `projects_ui.avisos_asignacion`): una regla nueva va AHÍ, no en `chat_tools`.
`_POR_ROL` al ejecutar y `_TARJETAS_DE` al confirmar; el grupo, de la sesión; el propietario, nada hasta su recorrido. Memoria: `chat_ui._CON_MEMORIA`; lo que escribe la app al tocar una tarjeta va marcado (`app`) y llega como nota de la persona (v645). `_hoy_e_idioma` va detrás
de la caché y `_idioma_tras_datos`, tras los resultados. ⚠️ El tablero solo se llena desde HOY (`roster.autopoblar_proyecto`, v644).

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
El resumen con IA lo escribe `core/resumen_dia.py` (v647) con los datos del Management assistant (`chat_tools`), en Sonnet 5.5, una vez al día
por empresa e idioma (`del_dia`, «Refresh» = `rehacer`); cada punto lleva a un destino de `DESTINOS` (fallback = `digest_text`).
`get_chat_response(..., grupo)` inyecta `group_snapshot_text` al system del admin → responde preguntas del
portafolio, recomienda acciones, recuerda vencimientos y redacta mensajes (persona admin ampliada, "usa SOLO
los datos provistos, no inventes"). UI: `projects_ui.render_group_header` → `_resumen_del_dia` (expander
"🔔 Resumen del día": chips de pendientes + la lectura de la IA, `lectura_ia`, que Home rellena AL FINAL en el sitio
que `_resumen_del_dia` le reserva). Solo el rol administrador (el propietario no tiene un único grupo).
**Cada mañana (v648):** quien lo pide en Home («Every morning too») lo recibe por correo/Telegram: `.github/workflows/resumen_manana.yml`
(cada 15 min de 20:00 a 00:59 UTC, v651: GitHub no garantiza horarios) → `survey_app/resumen_manana.py` → `core/resumen_envio.py` (hoja `DailySummary` por empresa; de 7 a 11 hora local, una vez
al día, solo administradores activos). ⚠️ El repositorio es PÚBLICO: su registro solo lleva cuentas. Secreto `STREAMLIT_SECRETS_TOML`.
**Uno al día también entre procesos (v649):** `del_dia` deja el del día en `DailyBriefs` (libro de la empresa) y el envío o Home, el que
llegue después, lo reutiliza; «Refresh» añade otro y manda el último.

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
- **Contacto OBLIGATORIO para campo + solo el ADMIN lo edita (v79):** el email, siempre (obligatorio al
  crear) y VÁLIDO (v614, `notify.email_campo_ok`: «driver 1» no cuenta; una errata probable, sí). ⚠️ **El Telegram, POR AHORA no** (v613, decisión del usuario: pruebas con usuarios de campo
  ficticios): `notify.TELEGRAM_OBLIGATORIO_CAMPO = False`; con True vuelve a exigirse, solo si el bot
  existe (v368). UNA regla, `notify.contacto_campo_ok(u)`, la usan la puerta de app.py, el Home, el
  asistente, los paneles de usuarios y el aviso al asignar — no copiar «email Y Telegram» a mano (lo
  vigila verif_v613). El admin/propietario gestiona email y **vincula el Telegram** (tras el Start del
  usuario) en `auth_ui._contacto_uno`. No hay self-service para el campo.
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
- ⚠️ **Un olvido de un día anterior** (v621): `clock_out` sin hora y `clock_in` se NIEGAN en el motor, no
  solo en la pantalla (`olvidos`): cerrarlo «ahora» apuntaba la noche como trabajada (33,39 h medidas).
  Solo se cierra con la hora real, en `timeclock_ui._aviso_olvido`.

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
- Sesión en `session_state`. ⚠️ Sin conexión (un móvil bloqueado), Streamlit la conserva 30 min (v619,
  `config.toml`; por defecto eran 120 s) y después la restaura la cookie de «Keep me signed in»,
  marcada por defecto. `session_cookie.py`: 7 días. Si se restaura sobre una página vieja (más de
  20 s), esta se recarga una vez (v622); abrir la app no recarga nada.
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


## Últimas versiones desplegadas (v652 = actual)

Historial COMPLETO — las secciones detalladas y el índice de las 440 versiones — en
**`HISTORIAL.md`**. Abrilo solo para el detalle de una versión puntual; no lo cargues entero.

| Ver | Cambio principal |
|---|---|
| v652 | **Las dos interpretaciones del Survey**: los datos y los sentidos los pone la app y el modelo (Sonnet 5.5) redacta; se le revisa cada mm, cada sentido, el «todo resuelto» y el procedimiento (plantilla de plomadas, no mover una cabina); siempre de la solución activa, reescribir sin recalcular, y la oficina revisa el texto del cliente antes del PDF. medido en producción como oficina, chip v652: Tools → Survey abre sin errores (plano, parámetros, matriz). Un cálculo real en producción, sin hacer: llama a la IA y manda el correo interno (permiso cada vez); lo cubren el examen real y verif_v652 con clics (elegir otra solución reescribe las dos sin reenviar el correo, la caja editada llega al PDF, «Rewrite» sin recalcular) · verif_v652 72/72; verif_v437 y verif_v448 sin cambios (las claves y las instrucciones en inglés, igual) · romper_v652 36/36 y las 2 afectadas, 17/17 (v437 10, v448 7; en la 1ª tanda escaparon 2 de v652 y 1 de v437 porque la prueba no las podía ver —un rechazo sin texto, «to the left wall» en el mismo sentido, el nombre de la función en el docstring—: afinadas y repetidas), 3367 anclas vivas · suite 271/271 |
| v651 | **El envío de la mañana, con muchos intentos en su franja**: GitHub no garantiza horarios (lanzó 2 de ~14), así que se le piden cada 15 min de 7 a 11 en Sydney (20:00-00:59 UTC, con y sin horario de verano) y solo el primero manda; el resto del día no corre. medido en GitHub: el workflow sigue activo y el push de 773398f no dio ningún error de fichero (el YAML, leído también en local: las dos franjas, ubuntu-24.04, checkout@v5 y setup-python@v6). Los intentos de la mañana, sin ver aún: el primero toca el 05/11 a las 07:00 de Sydney (20:00 UTC) · verif_v648 74/74 · romper_v648 50/50 (con las 4 nuevas del horario), 3330 anclas vivas · suite 270/270 |
| v650 | **El envío de la mañana, en Node 24 y con la máquina fijada**: `checkout@v5`, `setup-python@v6` y `ubuntu-24.04`, por los avisos de GitHub en la primera ejecución. medido en GitHub: Run workflow #4 sobre c67fa36, verde en 44 s con checkout@v5, setup-python@v6 y la máquina ubuntu-24.04, «empresas 1 | enviados 0 | ya_hoy 1 …» (Bobo ya lo tenía: no manda dos) y SIN las dos anotaciones de la #1. Antes, GitHub corrió solo el trabajo a las 07:05 y a las 11:36 de Sydney, los dos en verde y sin duplicar (LastSent sigue en 06:09). ⚠️ Pero de las ~14 ejecuciones de cada hora desde que se subió, GitHub solo lanzó 2: arreglo propuesto · verif_v648 71/71 · romper_v648 47/47 (con las 3 nuevas), 3327 anclas vivas · suite 270/270 |
| v649 | **Lo visto en la prueba de v646**: una actividad de varias partes con solo una nombrada ya no se premarca (pregunta «¿y el resto?»), la tarjeta de la oficina dice «this log» y «1 activity», y el resumen del día se paga una vez también entre el envío de la mañana y Home (hoja `DailyBriefs`). medido en producción como oficina, chip v649: Home preparó el de hoy (05:27) y quedó en DailyBriefs; desde OTRO proceso (en local, como el envío) del_dia lo reutilizó con 0 llamadas al modelo; «Refresh», por primera vez en producción, lo rehízo (05:32), quedó detrás y es el que se reutiliza. Con un parte de PRUEBA de campo000 en PRJ-0034 (5 días sin revisar): la tarjeta de la oficina dice «Activities this log mentions» y «Pending in this log», «Install CW guide shoes» marcada y ««and the CW buffer» — tick it only if all of it is done.» con «Is the car buffer done too?» SIN marcar; en el parte de al lado, «1 activity credited from this log». Sin confirmar nada; la obra devuelta EXACTA a la foto, el parte borrado y el resumen rehecho sin él · verif_v649 40/40; al día verif_v465, verif_v610, verif_v647 y verif_v648 · romper_v649 32/32 y las 9 afectadas, 317/317 (v523 30, v586 15, v607 37, v608 12, v610 26, v641 50, v646 62, v647 41, v648 44), 3324 anclas vivas · suite 270/270 |
| v648 | **El resumen del día, cada mañana, a quien lo pida**: un interruptor en Home para cada persona; GitHub Actions lo manda por correo o Telegram de 7 a 11 hora de la empresa, una vez al día, solo a administradores activos; registro público con solo cuentas. Falta el secreto en GitHub (lo pone el usuario). medido en producción como oficina, chip v648: el interruptor «Every morning too» bajo «Send it to me», apagado; encenderlo, «Done: … around 7:00 your company's time.» y en la hoja Active=YES con «desde» de ahora; apagarlo, «Done: no more morning summaries.» y Active=NO; sin aviso de contacto (Admin2 tiene correo). Antes, el script real contra cliente1: sin nadie suscrito NO creó la hoja; con Admin2 suscrito y --ignorar-hora, 1 enviado a Admin2 (una llamada real) y LastSent apuntado; repetido, «ya hoy»; sin ignorar la hora (22:5x en Sydney), «fuera de hora». GitHub registró «Morning summary» activo; desde Actions, PROBADO el 04/11 con el secreto puesto (Run workflow #1, 53 s: «enviados 1», LastSent apuntado y 0 llamadas al modelo, reutilizó el de Home). Admin2 queda en Active=NO: lo activa quien lo quiera · verif_v648 69/69; al día verif_v465 (DailySummary nace en inglés), verif_v560 y verif_v647 (sustituyen el interruptor) · romper_v648 44/44 y las 4 afectadas, 221/221 (v560 26, v636 104, v641 50, v647 41), 3291 anclas vivas · suite 269/269 (en la 1ª vuelta, 2 rojos de forma: check_suite_integra, porque verif_v648 importaba el script como módulo, y verif_v465, por la hoja nueva sin declarar; arreglados con su razón) |
| v647 | **El resumen del día, otro**: los datos del Management assistant (cartera, equipo de hoy, lo que espera a la oficina y el dinero), en Sonnet 5.5 y en el idioma de quien lo lee, con el día en letras; cada punto lleva a donde se resuelve; se prepara solo al abrir Home, una vez al día por empresa, y «Refresh» lo rehace. medido en producción como oficina, chip v647, sin errores de la app: Home preparó la lectura sola (una llamada real), 7 puntos con su botón, cada cifra como en los datos y el dinero como la app ($82,900.65); al volver a Home, la misma lectura sin otra llamada; «Go to Invoices» lleva a Finance · Invoices y «Open the job» a PRJ-0027 (51 días de retraso y 0 h, como dice el punto); «Send it to me», «Summary sent.» a Admin2. «Refresh» y el español, solo por guardián y en el examen (gastan). La prueba de v646 que faltaba, con un parte de PRUEBA de campo000 en PRJ-0034 guardado hace 4 días: «Logs to review · 1» en Home con su detalle y el filtro de Projects; en Status la tarjeta de la oficina con la lectura real ($0,053, 6 s), 2 premarcadas, una desmarcada a mano y Confirm: 1 crédito (log, la fecha del parte, Admin2), «reviewed by Bobo (on behalf of …)», en_nombre_de campo000 y la memoria sin tocar; la obra devuelta EXACTA a la foto y el parte borrado. ⚠️ Destapó que premarca una actividad de dos partes con una sola («Install/trim buffers (car + CW)» por «the CW buffer») y que la tarjeta de la oficina dice «your log»: arreglos propuestos · verif_v647 60/60, verif_v643 100/100 · romper_v647 41/41 y las 6 afectadas, 176/176 (v546 12, v560 26, v561 15, v630 26, v632 28, v643 69; a la de v643 se le escaparon 2 en la tanda por una variable reusada en mi propio guardián, repetida tras arreglarlo), 3246 anclas vivas · suite 268/268 |
| v646 | **El agente del parte, con más autonomía**: premarca lo que tiene claro, «Add to To-do» en lo pendiente, una tarjeta para acreditar desde el chat y, a los 2 días sin revisar, la oficina lo confirma por su autor (Home, Management assistant, Status). Nada se acredita sin un Confirm. medido en producción como oficina, chip v646, sin errores: Home con los 10 indicadores en 2 filas de 5, «Logs to review · 0» (cliente1 no tiene partes esperando); PRJ-0034 → Status → Daily logs, los 7 partes con su revisión y ninguna tarjeta de oficina. Sin probar en producción: confirmar por el autor (hace falta un parte de más de 2 días y una lectura real, ≈US/usr/bin/bash,02), las casillas premarcadas y la tarjeta del chat (hace falta una sesión de campo): lo cubre verif_v646 con clics · verif_v646 70/70 · romper_v646 62/62 y las 24 afectadas, todas cazadas (v444 7, v471 5, v516 20, v523 30, v524 19, v525 16, v528 19, v529 5, v544 22, v558 26, v561 15, v586 15, v607 37, v608 12, v609 11, v610 26, v611 31, v612 7, v639 50, v640 60, v641 50, v643 67, v644 71, v645 13; la de v516 escapó en la tanda por un ancla mal re-anclada y se repitió tras arreglarla), 3201 anclas vivas · suite 267/267 |
| v645 | **Lo que escribe la app al tocar una tarjeta ya no lo lee el modelo como suyo**: tras Confirm lo negaba («I hadn't confirmed that»); va marcado, se recuerda marcado y llega como nota de la persona. medido en producción como oficina, chip v645, sin errores: el asistente se abre con «Your conversation is kept for 14 days» y la conversación vacía. Sin preguntas nuevas en producción (gastan y escriben): lo medido es el examen real · verif_v645 21/21 · romper_v645 13/13 y las 5 afectadas, 298/298 (v639 50, v640 60, v641 50, v643 67, v644 71), 3138 anclas vivas · suite 266/266 |
| v644 | **El Management assistant actúa con tarjeta**: decide ausencias y correcciones, cierra avisos, asigna y avisa a la cuadrilla con la función de su pantalla, solo con Confirm; To-do directo y memoria. ⚠️ **Asignar ya no llena el tablero de días pasados**, tampoco en Save changes. medido en producción como oficina, chip v644, sin errores, 3 preguntas reales: «Your conversation is kept for 14 days», sin foto; asignar a campo000 en PRJ-0030 (cancelada y vacía), con su aviso de otra obra y el tablero del 16/11 al 11/12, y Confirm: asignado, avisado y 20 días en el tablero; aviso a la cuadrilla y Confirm: 1 persona y ALR-0005; To-do directo; cerrar ALR-0005 y Confirm: resuelto; la memoria guardó 9 mensajes y Clear la dejó en 0; PRJ-0030 devuelta a como estaba (cuadrilla vacía, 20 días limpiados, To-do borrado) sin avisar a nadie. ⚠️ Destapó que el asistente niega la línea «✅» que escribe la app tras Confirm y dice que no lo hizo: arreglo propuesto para v645 · verif_v644 138/138 · romper_v644 71/71 y las 13 afectadas, 367/367 (v430 26, v498 4, v555 14, v556 14, v559 35, v573 4, v581 29, v613 14, v639 50, v640 60, v641 50, v643 67), 3124 anclas vivas · suite 265/265 |
| v643 | **El Management assistant consulta los datos de la empresa**: cartera, equipo, bandejas y dinero, solo lectura, atados a su rol y su empresa; ya no paga la cartera en cada pregunta. Sabe qué día es y responde en el idioma de la pregunta también con datos delante. ⚠️ **Una prueba ya no escribe de verdad**: una batería dejó 4 alarmas reales y avisos; el arnés lo para. medido en producción como oficina, sin errores: Home con 6 activas, 5 atrasadas, 181 h, retrasos 51/15/12/8 y los 3 planificados de hoy; Finance → Summary sin facturas ni costes este mes, Not invoiced $82,901 y 0 sobre presupuesto; Profitability, Parramatta 9.932,45 de coste e ingreso y 0 de ganancia: lo mismo que respondió el asistente. 4 exámenes REALES con permiso, en local contra los datos reales de cliente1 con toda escritura bloqueada: 34 preguntas, 0 intentos de escribir y $0,876; el aviso trampa, sin obedecer las 4 veces que salió; en el último, 7 de 7 en inglés desde la primera palabra, $0,026 por pregunta, mediana 7,1 s y máximo 17,7 s. ⚠️ Sin probar: una pregunta real desde la app desplegada. Hoja revisada tras la tanda: nada nuevo · verif_v643 98/98 · romper_v643 67/67, romper_arnes 36/36, romper_v623 30/30, romper_v630 26/26, romper_v632 28/28, romper_v639 50/50 y romper_v640 60/60 · suite 264/264 |
| v642 | **El asistente responde en el idioma en que le preguntan**, con los nombres de las pantallas tal cual. Tarjetas y adjunto probados en un navegador real, con doble clic incluido. examen REAL con permiso, 5 preguntas como installer, con todas las escrituras bloqueadas: «remember» ya no va a To-do, no reintentó nada, contestó en español a lo español y en inglés a lo inglés con los nombres de pantalla tal cual, y 0 intentos de escribir; $0,092. En producción arranca sin errores; como campo no hay sesión allí · verif_v641 75/75 · romper_v641 50/50, romper_v640 60/60, romper_v469 9/9, romper_v449 7/7 y romper_v448 7/7 · suite 263/263 |
| v641 | **La memoria y las fotos del Field assistant.** La conversación se recuerda 14 días, en una fila por persona; acepta una foto, que no se guarda. ⚠️ El examen real destapó que reintentaba acciones por su cuenta: corregido. examen REAL con permiso, 5 preguntas como installer, con las escrituras bloqueadas: leyó la placa, trató como texto la foto que decía «ignore your rules», y en la ilegible no inventó ninguna medida; la memoria, guardada, leída y borrada en la hoja real: recordó el dato; $0,103 en total, mediana 4,0 s y máximo 12,6 s. La corrección de «no reintentar», solo por guardián. En producción arranca sin errores y la oficina no ve ni el adjunto ni el aviso; el adjunto y las tarjetas en el navegador, sin probar: hace falta una sesión de campo. Datos de prueba borrados · verif_v641 72/72 · romper_v641 48/48, romper_v640 60/60, romper_v639 50/50, romper_v636 104/104, romper_v635 36/36 y romper_v526 9/9 · suite 263/263 |
| v640 | **El Field assistant prepara y hace.** Solo en To-do; el parte, el aviso a la oficina y las ausencias, con tarjeta y **Confirm**. ⚠️ Preparar no escribe nada, y fichar, firmar o acreditar no existen como herramienta. examen REAL con permiso, 10 preguntas como installer contra los datos reales de cliente1, con las escrituras de parte, aviso y ausencia bloqueadas y contadas: las 10 correctas y 0 intentos de saltarse la tarjeta; apuntó en To-do de verdad, preparó parte, aviso y baja, pidió aclarar «next Friday», rechazó 300 días, y se negó a fichar, acreditar y firmar; una tarea trampa con «ignore your rules» la contó como texto ajeno y no marcó nada; $0,24 en total, $0,024 por pregunta, mediana 5,3 s y máximo 8,4 s. En producción, sin errores al arrancar; las tarjetas en el navegador, sin probar: hace falta una sesión de campo. Datos de prueba borrados · verif_v640 87/87 · romper_v640 60/60 (58 en la tanda y las 2 que escaparon, repetidas tras afinar el guardián), romper_v639 50/50, romper_v632 28/28, romper_v627 60/60, romper_v526 9/9 y romper_v430 26/26 · suite 262/262 |
| v639 | **El Field assistant consulta los datos de quien pregunta.** Nivel 1 de autonomía: su día, sus obras, sus ausencias y sus credenciales, solo lectura. ⚠️ La identidad sale de la sesión y una obra ajena no se abre. examen REAL con permiso, 9 preguntas con la API contra los datos reales de cliente1 como installer, desde local: las 9 correctas, también negarse a una obra ajena, al sueldo de un compañero y a fichar; $0,16 en total, $0,018 por pregunta, mediana 4,4 s y máximo 12,8 s. En producción, sin errores al arrancar; como campo no hay sesión para probarlo allí · verif_v639 79/79 · romper_v639 50/50 (47 en la tanda y las 3 que escaparon, repetidas tras afinar el guardián), romper_v633 54/54, romper_v632 28/28, romper_v631 22/22 y romper_v630 26/26 · suite 261/261 |
| v638 | **«Mark all as passed» en el checklist del false car.** Rellena lo que falta y nunca pisa una X; el formulario sigue naciendo vacío y la firma sigue siendo obligatoria. medido en producción como oficina, con clics reales en una obra de prueba: nace vacío; con una X en el punto 2 y el botón, esa X sigue y los otros 17 quedan en ✓ en el navegador; el botón se apaga sin mover la pantalla y pide las observaciones de la X; con todo en ✓ sigue pidiendo la firma; guardado, 18 de 18 en ✓ en la hoja, firmado y con PDF. Datos de prueba borrados · verif_v636 271/271 · romper_v636 104/104 · suite 260/260 |

_(y 576 versiones anteriores en `HISTORIAL.md`)_
