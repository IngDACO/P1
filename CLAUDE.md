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
│   ├── roster.py           # tablero semanal de cuadrilla: catalogo Trabajos + hoja Roster (v159)
│   └── roster_ui.py        # 📅 Planificacion (admin): rejilla coloreada + editar semana + copiar (v159)
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

## Herramientas de calculo, parte 2: las cuatro completas (v130)
Cierra lo empezado en v129. Ahora **Plomadas, Corte de rieles, Corte de buffers y Belting** comparten:
resultados persistentes, dibujo tecnico, PDF (`tool_pdf`) y guardado contra el proyecto
(`tool_save_ui` → hoja `Calculos` + Drive).
- **Fix del bug v110 en las tres restantes.** En Plomadas colgaban **80 lineas** del boton (los 4
  graficos CAD de v123 se borraban al tocar nada); en Rieles dos bloques y en Belting uno. Patron
  aplicado: el boton SOLO computa y guarda en `session_state`; el render vive fuera.
  Verificado por AST: ningun bloque de mas de 6 lineas cuelga ya de un `st.button`, salvo el de Rieles
  Caso 2 que es **solo computo** (arma `rows` y llama a compute_case2), sin render.
- **`rail_cut.rail_cut_svg(res, caso, n2500, n5000)`** — diagrama nuevo. Caso 1 es alzado REAL: la pila
  de rieles estandar instalados (A) contra la longitud requerida por elevador (RC/RCW); lo que
  sobresale es la diferencia. Caso 2 son barras comparativas, porque ahi no hay pila que dibujar (los
  valores vienen medidos en obra) — dibujar una geometria inventada seria mentir.
- ⚠️ **Signo de Cut\*: la app NO documenta que significa** (la UI solo mostraba el numero crudo). Con
  datos de prueba realistas los cortes salen NEGATIVOS. La leyenda del dibujo dice "diferencia contra A
  (mismo valor con signo que la tabla)" en vez de "material a cortar": describe lo que se sabe sin
  afirmar una direccion de corte que no esta definida en ninguna parte. **PENDIENTE de confirmar con el
  usuario** — es una decision de dominio, y es una operacion irreversible.

## Herramientas de calculo, parte 1: registro en el proyecto (v129)
Las cuatro herramientas (Plomadas, Corte de rieles, Corte de buffers, Belting) eran **islas**: ni PDF,
ni descarga, ni rastro en el proyecto. Calculabas, mirabas y ahi moria.
### ⚠️ Bug estructural encontrado en LAS CUATRO (mismo que v110)
Los resultados se calculaban y dibujaban **dentro de `if st.button(...)`**, asi que desaparecian con
cualquier interaccion. En Plomadas colgaban **80 lineas** del boton: los 4 graficos CAD de v123 se
borraban al tocar nada. Ademas hacia IMPOSIBLE un boton de guardar (al pulsarlo se perdia todo).
Patron correcto: el boton solo COMPUTA y guarda en `session_state`; el render vive FUERA.
### Infraestructura nueva (comun a las 4)
- **`core/toolruns.py`** — hoja **`Calculos`** (ID·ProyectoID·Grupo·Herramienta·Fecha·Usuario·Resumen·
  DatosJSON·Archivo·DriveID). `registrar()` archiva el PDF en Drive + lo registra como documento del
  proyecto + escribe la fila. Mismo patron que `prestart.submit` (Drive en best-effort: si falla, la
  fila igual se guarda). Lecturas cacheadas ttl 30 + invalidacion al escribir; `_next_id` lee FRESCO.
- **`core/tool_pdf.py`** — `tool_pdf(titulo, meta, svgs, tablas, notas)`: un solo generador para las
  cuatro, asi comparten cara entre si y con el paquete de obra del Survey.
- **`core/tool_save_ui.py`** — `render_guardar(...)`: descarga + selector de proyecto (por rol, mismo
  criterio que el Pre-Start) + guardado. Vive en un sitio para no divergir en cuatro.
### Hecho en esta version
- **🛡 Corte de buffers** completo: persistencia, **diagrama nuevo** (`buffer_cut.buffer_cut_svg`:
  alzado con el nivel HKP del plano, el HKPR real de cada buffer y el material a cortar achurado en
  rojo; escala vertical ajustada al rango y declarado en el pie), PDF y guardado en el proyecto.
- PENDIENTE en v130: Plomadas, Corte de rieles (necesita dibujo) y Belting.

## Plano unico de la sesion + paquete de obra desde el proyecto (v128)
**El hallazgo de integracion mas grande de la app:** Survey, Plomadas, Corte de rieles, Corte de buffers
y Belting tenian **cinco `file_uploader` distintos**, asi que el tecnico subia el MISMO plano hasta cinco
veces para el mismo elevador. Y `extractors/schindler.py` ya tenia todos los extractores juntos
(`extract_from_pdf`, `extract_number_of_stops`, `extract_car_guide_rail`, `extract_belting`,
`extract_hkp`): un unico PDF puede alimentarlas todas.
- **`core/plan_store.py`**: `guardar()` / `actual()` / `selector(label, key)`. El Survey registra el plano
  al cargarlo; las otras cuatro lo ofrecen con `selector`, que devuelve un `_Plano` (BytesIO **con
  `.name`**) para que sustituya al UploadedFile sin tocar la logica: los llamadores usan `.name` como
  guarda de identidad, el patron obligatorio de v112. Lo que se suba en cualquier herramienta queda
  registrado, asi que da igual por donde empieces.
  Verificado con un plano REAL: HKP=70, HQ=14045, HGP=85, NS=6 leidos del objeto compartido.
- **`core/survey_calc.py` → `recalcular(params, matriz)`**: el proyecto guarda ParamsJSON (que ya incluye
  toda la config: OMEGA_SIDE/WALL_*/CTRL_*/NS) y MatrizJSON, pero **NO la solucion**, que es derivada.
  Esto rehace SOLO la parte determinista de `_do_calculo` (sin IA, sin correo, sin cronograma, sin
  Streamlit). La logica sigue en calculations/optimizer/plumb: aqui solo se encadenan llamadas.
  **Verificado ejecutando ambos caminos sobre los mismos datos: `best` identico y `lim_map` identico.**
- **Paquete de obra desde el detalle del proyecto** (projects_ui): recalcula y arma el PDF sin pasar por
  el Survey. Antes habia que reconstruir el proyecto en el Survey y volver a calcular.
### ⚠️ Error que cometi
Inserte `from core import plan_store` usando `lineno` del ultimo import; en `plumb_ui.py` el ultimo es
un import **multilinea entre parentesis**, asi que la linea cayo DENTRO del parentesis → SyntaxError.
Correcto: usar **`end_lineno`** del nodo AST, no `lineno`.

## Survey: chequeo al asignar campo + fin de la numeracion (v127)
Revision de INTEGRACION del Survey. Se asignaban usuarios de campo **sin mirar nada de lo que la app
ya sabe de ellos**, y la app lo sabe todo (v79 contacto, v104 credenciales):
- **Credenciales**: aviso si algun asignado tiene una credencial **vencida o por vencer**
  (`credentials.list_for` + `status`). Informativo, NO bloquea (un ticket puede estar en tramite).
- **Contacto**: aviso si falta email o Telegram. Sin ellos no reciben la asignacion NI las inducciones,
  y ademas no pueden usar la app (bloqueo duro de v79).
- ⚠️ **El selector de campo se saco FUERA del `st.form`**: dentro de un form los widgets NO escriben en
  session_state hasta el submit, asi que un aviso "en vivo" ahi dentro es imposible. Ahora el aviso
  aparece al elegir, ANTES de guardar, que es cuando sirve.
- **Fallo silencioso corregido**: el resultado de la notificacion se mostraba con `if _nn:` → si no se
  notificaba a NADIE no se decia nada y parecia que habia salido. Ahora informa siempre: todos / parcial
  / ninguno, y avisa aparte si no hay canales configurados.
- **Numeracion 1-7 eliminada** (herencia del scroll unico anterior a v114): en Datos se veia 1,2,3 y en
  Resultados 4,5,6,7 sin que existieran los otros. Titulos con icono y sin numero.
### ⚠️ Error que cometi
Llame `credentials.status_label(_estado)` cuando su firma es `status_label(vencimiento)` — recibe la
FECHA, no el estado. `status_label("vencido")` devuelve **"—"** (porque `status("vencido")` no parsea y
da ""), asi que el aviso habria mostrado "White Card: —" en vez de "🔴 vencido". Lo caza **inspeccionar
la firma y probar la funcion con datos reales**, no asumir por el nombre.

## Survey lote 3: cierre de ciclo, paquete de obra y duplicados (v126)
- **`core/field_pack.py` → `field_pack_pdf(...)`**: UN PDF con lo que necesita quien va a terreno —
  cabecera del proyecto, isometrica del hueco, plantas por piso a escala y el replanteo de plomadas
  (planta + isometrica + **ficha de medidas**). Tras v119-v123 las piezas existian pero SUELTAS: habia
  que ir seccion por seccion descargandolas. NO lleva interpretaciones, log ni formulas: no es el
  informe del cliente ni el de admin. Opcion "solo pisos con incidencias" (reusa `floors_with_issues`).
  Boton en el Survey, dentro de `_render_survey_results`.
- **Cierre del ciclo al guardar**: antes terminaba en el texto muerto "Gestionalo en Mi grupo →
  Proyectos". Ahora hay boton **"Abrir proyecto ➜"** que navega de verdad: `_nav_pending` (aplicado
  antes del radio `main_nav` en app.py) + `_prjsel_pending` (aplicado antes del selectbox
  `adminproj_sel` en projects_ui) + `owner_sec` si es propietario. Patron pendiente+rerun de v111:
  jamas escribir la clave de un widget ya instanciado.
- **Aviso de duplicados**: `create_project` no comprobaba nada. Un proyecto = un elevador y el survey se
  repite por elevador, asi que era facil crear el mismo dos veces y repartir horas/gastos entre
  duplicados. Ahora compara el nombre normalizado contra los del grupo, lista los coincidentes y exige
  marcar una casilla para crear igualmente.
### ⚠️ Error que cometi (chequeo nuevo a repetir)
Inserte el bloque del paquete en la fase Resultados pero **FUERA de `_render_survey_results`**, donde NO
existen `best`/`lim_map`/`ctrl_in_frame_` (son locales de esa funcion) y ademas se dibujaba sin haber
calculado → `NameError` seguro. El chequeo global de nombres NO lo detecta: esos nombres existen en OTRA
parte del arbol. **Chequeo correcto: verificar en que funcion cae la linea insertada y que las locales
que usa esten asignadas ANTES de esa linea, dentro de esa misma funcion.**

## Survey lote 2: extraido a core/survey_ui.py (v125)
El Survey era el UNICO modulo grande dentro de `app.py`: **1243 de sus ~1650 lineas**, frente a
plumb_ui (154), prestart_ui (147), timeclock_ui (206), projects_ui (1075), que si tienen el suyo.
Esa concentracion causo v118 y v120 (indentacion en un archivo enorme con fases anidadas, compilaba
perfecto y rompia en produccion). Ahora **app.py 321 lineas / core/survey_ui.py 1353**.
- `render_survey_tab(_ROL, _GRUPO)`. Los parametros se llaman `_ROL`/`_GRUPO` A PROPOSITO: el cuerpo
  movido los usa tal cual, asi la extraccion **no tuvo que renombrar nada** dentro de 1243 lineas.
- Se mudaron con el: `SURVEY_COLS`, `USER_ONLY`, `_GRUPOS_PARAM`, `_cfg_from_state`, `_init_state`
  (renombrado `init_state`, publico: app.py lo llama al arrancar). Unico consumidor externo era él.
- Perfil de dependencias medido ANTES de mover: 48 nombres, 42 imports + 1 def + 5 asignaciones →
  extraccion limpia. Merece la pena medir esto antes de cortar.
### ⚠️ Dos errores que cometi y como se cazaron (repetir estos chequeos)
1. **Copie el RANGO del primer al ultimo import** de app.py. Como app.py tiene imports en la l.200,
   arrastro todo lo que habia en medio: **la barrera de login entera** (`if not render_login():
   st.stop()`) quedo a nivel de modulo en survey_ui, y se habria ejecutado AL IMPORTAR. Correcto:
   recoger las lineas de CADA nodo import, no el rango.
2. **Renombre la llamada `init_state()` en app.py pero no la definicion** → `ImportError` seguro en
   produccion. `py_compile` NO lo detecta. Lo caza **importar el modulo de verdad** y resolver cada
   `from X import Y` contra el modulo real.
### Chequeos que dejaron el cambio verificado
`scratchpad/verificar.py`: (1) todo nombre resuelve dentro de la funcion —contando imports locales y
`except as e`, o da falsos positivos—; (2) sin fugas entre fases; (3) el log sigue bajo `_ROL`;
(4) nada de login/sesion se colo; (5) sin `_ROL` de modulo. Ademas: importar `core.survey_ui`,
resolver todos los imports contra modulos reales (ojo: `from core import notify` da falso positivo,
un submodulo no es atributo del paquete hasta importarlo), y **diff del cuerpo movido: 0 diferencias
en 1243 lineas**.

## Survey lote 1: confidencialidad del log + leyenda de color (v124)
Revision del Survey tras v113-v123. Dos incoherencias encontradas por inspeccion:
- ⚠️ **El log del optimizador estaba a la vista de TODOS los roles**, incluido `campo` (el Survey esta en
  `_HERR`, herramientas comunes). Expone los pasos evaluados, los descartes y por que → es la logica
  propietaria que el agente IA tiene PROHIBIDO revelar (v27) y que el informe del cliente excluye a
  proposito. En el Survey solo estaban protegidos el paso 6 (informe) y el 7 (guardar). Ahora el log es
  **solo del propietario** (decision del usuario; ni el administrador del grupo cliente lo ve).
  El reindentado del bloque (45 lineas) se hizo por AST y se VERIFICO por AST que el `with` quedara
  dentro del `if _ROL` — es el mismo patron que causo v120, no se toca a mano.
- **Las tablas llevaban color sin leyenda desde v93** (se quito del sidebar y nunca se repuso): celdas en
  rojo/naranja sin nada que explicara el criterio. Nuevo `_leyenda_matriz()` bajo la matriz ajustada y
  bajo la matriz de cada solucion. Usa las MISMAS palabras que los planos ("fuera de limite") para que
  tabla y dibujo se lean como un solo lenguaje, y recuerda el criterio opuesto: WR·WL·FR·FL incumplen por
  DEBAJO del limite, OR·OL por ENCIMA.
Verificado que `cell_state` (tablas) y `_c` (dibujos) marcan EXACTAMENTE las mismas celdas, incluido el
ajuste −70 del controlador en el ultimo nivel → no habia que tocar logica, solo paleta y palabras.

## Plomado: planta a escala + 2 vistas 3D + ficha de replanteo (v123)
`plumb_svg` reescrito y 3 funciones nuevas en `core/plumb.py`. Mismo tratamiento CAD que las plantas.
⚠️ **El fallo de fondo: el dibujo NO estaba a escala.** `sx` y `sy` mapeaban X e Y a rangos distintos →
**vertical 1.7× la horizontal** (medido). El triangulo plantilla→plomos, que es JUSTO lo que se mide con
cinta en obra, salia deformado. Ahora **una sola escala** mm→px; origen X = pared real izquierda (V4=0),
eje Y = profundidad desde la pared frontal.
- Lenguaje de plano: muros achurados, paredes teoricas en eje-punto, plomos como circulo+centro, cuerdas
  d1/d2, cotas DBP/di/dd/DBPW/RW/LT, cajetin. Reusa `_hatch`/`_dim_h`/`_dim_v` de `diagrams.py`
  (importadas, NO duplicadas; no hay ciclo porque diagrams no importa plumb).
- **`plumb_iso_svg`** — isometrica con los DOS HILOS cayendo desde arriba hasta la solera, con su peso.
  Es lo que la planta no puede dar: el replanteo es una operacion VERTICAL. Solo dibuja los planos que el
  plomado conoce de verdad (paredes reales izq/der + frontal); **el fondo se deja abierto** porque el
  plomado no recibe TS. Altura esquematica (no recibe la altura del hueco) y se declara en el pie.
- **`plumb_detail_svg`** — detalle 3D de ejecucion. ⚠️ La 1a version era un plano inclinado con el mismo
  triangulo que la planta, deformado por la proyeccion: **anadia ruido, no informacion**. Se reoriento
  dandole CAIDA de hilo real (`Hh = dbp*0.72`) para que ensene la vertical. Presupuesto de lienzo
  obligatorio (alto de hilo + rombo del plano) o C2 se sale por abajo.
- **`plumb_card_svg`** — ficha de replanteo: DBP, d1, d2, di, dd en tipografia grande + la comprobacion.
  En el andamio no hace falta un plano bonito, hacen falta 5 numeros legibles desde el movil.
- **Cierre `di + DBP + dd = BSR`** — es una IDENTIDAD del modelo (verificado en los 3 modos), asi que su
  valor NO es como chequeo interno sino **como verificacion de obra**: el instalador mide di y dd con
  cinta y comprueba que cierran contra BSR.
- **`bs_check`** — BS del plano vs `SF1+BKS+2·RAIL+SF2`. Si no cuadran, el encaje usa (BSR−BS)/2 y **los
  plomos quedan mal ubicados EN SILENCIO**. Se avisa en la app (st.error) y en el dibujo. Lo descubri
  tropezando yo mismo con un dato de prueba incoherente.
- **Sacrificio Z/Omega** dibujado (lado, cuanto, y "NO CABE" si `fuera_rango`) en modo independiente.
- `_n()` pasa a formato adaptativo: `DBPW = TKSW−150+fb` arrastra el fb del survey (pasos de 0.5 mm).
- Integrado en app.py (survey), plumb_ui.py (pestana), report.py e user_report.py.
- Verificado: PDF real en los 4 modos (survey / BSR<BS / BSR>BS / BS incoherente), cierre exacto en los
  3 validos y aviso en el 4o; SVG sin `<defs>/<marker>/<pattern>`, svglib convierte los 4 graficos.

## El optimizador trabaja en pasos de 0.5 mm — NO redondear al mostrar (v122)
Pregunta del usuario: "la solucion activa redondea los valores?". Respuesta: **el dato NO se redondea
en ningun punto del calculo**; el selectbox guarda el dict completo (`r["optimizer_result"]["best"] =
_nueva`). Pero **varias PANTALLAS si redondeaban a entero**, y una de ellas causaba un problema real:
- `optimizer.optimize` barre `np.arange(-max_rl, max_rl+0.5, 0.5)` → **RL y FB pueden ser x.5**.
- La etiqueta del selector de solucion activa usaba `:+.0f` → **RL −6.0 y RL −6.5 daban la MISMA
  etiqueta** y las soluciones no se podian distinguir en el desplegable. Ahora `:+.1f`.
- Esos medios milimetros se PROPAGAN a la matriz (`WL += rl`, `FR += fb`...), asi que las cotas del
  plano con `.0f` rotulaban 71.5 como "72": la cota afirmaba un valor que no era el medido.
- Nuevo helper **`diagrams._mm(v)`**: entero si el valor lo es, 1 decimal si no. Aplicado a
  WL/WR/FL/FR/OL/OR/TK/BC, a la cota EJES y al Detalle. Asi las cotas siguen limpias donde el valor es
  entero y revelan el medio milimetro donde existe.
- Ya estaban bien (`.1f`): la metrica RL/FB del resumen, el informe cliente y el informe admin.
⚠️ REGLA: cualquier display de RL/FB o de la matriz va con **al menos 1 decimal**. Con `.0f` no solo se
pierde precision: se pueden volver INDISTINGUIBLES dos soluciones distintas.

## Fix CRITICO de geometria en los dibujos (v121)
Los planos de v119 salian con **la cabina fuera del hueco** (se escapaba por arriba del muro de fondo).
Dos suposiciones mias, mal:
**1. FL/FR NO llegan al frente de la cabina, llegan al EJE DE RIELES.** Identidad exacta de
`calculations.py` l.98: `BC_CALC = TS − TKSW − TK/2 − 25` ⇒ `TS = TKSW + TK/2 + 25 + BC_CALC`. O sea,
desde la pared frontal: TKSW (en obra = FL/FR) llega al eje de rieles, y **ese eje esta a MEDIA
profundidad del cuerpo de cabina (TK/2)**. Yo situaba el frente de la cabina a (FL+FR)/2 del muro y
ademas usaba TL como profundidad → con FL≈1176 y TL=2365 la cabina se iba 1176 mm hacia atras y no
cabia en TS. Ahora: cuerpo **TK centrado en el eje de rieles**, rieles dibujados sobre los laterales a
su profundidad real (FL izq / FR der, que es justo lo que se mide en obra), y cota **BC** atras.
⚠️ TL (= CS+TKS+TSW) NO es la profundidad util para la planta; la profundidad del cuerpo es **TK**.
**2. La apertura se centraba en un eje calculado pero se rotulaba con OL/OR medidos** → el numero no
correspondia al tramo dibujado (en el caso real, OL 277 y OR 62 salian sobre tramos casi iguales).
OL/OR se miden **desde el borde de la cabina** (ver `LIMIT_OL/OR = BKS/2 + RAIL/2 − BT/2 − FRAME`), asi
que ahora la apertura se POSICIONA con ellos: `dx0 = cx0 + OL`, `dx1 = cx0 + (cab_w − OR)`, y el
sobrante a cada lado es el FRAME, que se dibuja. La cota entre ejes pasa a rotular la distancia
**medida** (`EJES n→R/L`) en vez del OFFSET de diseno, para no afirmar un numero que no se dibuja.
- El "DETALLE" ampliado ya solo considera **WL/WR**: son las unicas holguras que se desvanecen a escala
  real. FL/FR son distancias largas (pared→eje de rieles), no holguras.
- `shaft_iso_svg` arrastraba el mismo error de profundidad: corregido igual.
Verificado midiendo el SVG en el DOM con los datos reales del usuario: WL=72, WR=294, cabina 1288×2328,
`cabina_dentro=true`, y OL 277 + marco 24,5 + BT 900 + marco 24,5 + OR 62 = **1288 = ancho de cabina**.
⚠️ Leccion de proceso: en dos revisiones a ojo crei ver fallos que NO existian (nivel rojo, cabina
atravesando el foso) y no vi este, que si era real. **Medir el SVG, no mirarlo.**

## Fix CRITICO: indentacion rompio las 2 fases del Survey (v120)
Regresion de **v118** que se detecto en produccion: `NameError: sc2` al entrar a Resultados, los 7 pasos
saliendo en la fase Datos y **la matriz del survey invisible**. Un solo error de indentacion los causaba
los tres. En el paso 3, el bloque del checkbox del Excel (lineas 1186-1194) quedo a **4 espacios en vez
de 8**, o sea FUERA de `if _fase == _FASE_DATOS:`. Consecuencias en cadena:
1. Ese bloque pasaba a ejecutarse en AMBAS fases → en Resultados `sc2` no existe → NameError.
2. El `if` de la fase Datos **terminaba** en la linea 1185, asi que todo lo posterior (pasos 4-7) dejo de
   estar dentro de la fase.
3. Peor: las lineas siguientes (a 8 espacios) quedaron absorbidas como cuerpo del `if ... sc2.button(
   "Volver a importar el Excel")`, que esta a 4 → el editor de la matriz y el import de Excel solo
   existian dentro de esa rama, **y despues de un `st.rerun()`** → codigo inalcanzable. Por eso no se veia
   la matriz y por eso cargar un Excel no hacia nada.
Fix: reindentar 1186-1194 (+4). Verificado por AST: la fase Datos cubre los pasos 1-3 (1015-1307) y el
`else` los pasos 4-7 (1312-1542).
⚠️ **Chequeo que conviene repetir tras tocar el Survey** (detecta la clase de bug de v114/v118): comparar
por AST los nombres que una fase USA y solo la otra ASIGNA. Ambas direcciones deben dar vacio. Un
`py_compile` NO detecta nada de esto: el archivo compila perfecto, el error es semantico.

## Dibujos del survey: plano tecnico a escala + isometrica (v119)
`floor_plan_svg` reescrito. Antes era un esquema con holguras FALSEADAS (`_clearance_px` comprimia el
valor a 14-92 px) y globos de color: se veia infantil y ademas **enganaba** (una holgura de 5 mm y otra
de 200 mm se dibujaban casi igual).
- **Proporcion REAL:** una sola escala mm→px para ancho y profundidad, derivada de la geometria que ya
  existia (`ancho = WL + BKS+2·RAIL + WR`, `prof = TS`, `TL`, `BC_CALC`). Lo que se ve es lo que hay.
- **Lenguaje de plano:** muros achurados, cotas con lineas de extension + marcas diagonales, jerarquia de
  grosores (muro 2.4 / cabina 1.6 / cotas 0.6), ejes eje-punto, cajetin (PISO n/N, proyecto) y leyenda.
  **El rojo se reserva** a las cotas fuera de limite (antes todo era de colores y no destacaba nada).
- **Cotas cortas:** a escala real 45 mm ≈ 12 px y el numero no cabe entre las marcas → `_dim_h/_dim_v`
  detectan el vano <36 px y sacan el valor afuera con directriz (solucion estandar de dibujo tecnico).
- **DETALLE automatico** cuando la holgura minima del piso es <25 mm: amplia esa esquina con **escala
  propia calculada** (llena el recuadro; ×3 a ×40) y marca el punto en el dibujo principal. Es la razon
  de ser de la escala real: lo critico se amplia en vez de falsear todo el plano.
- **Ambos desplazamientos:** OFFSET_CABIN como cota entre el eje de la cabina y el eje de la apertura;
  RL/FB con contorno fantasma "POS. DISENO" **solo si el desplazamiento supera 2 px** — si no, iria
  cota sobre cota ilegible, asi que los valores van a un recuadro DESPLAZAMIENTO siempre legible.
- **`shaft_iso_svg(params, limits, solution, ns, lim_map, proyecto, h_piso)`** — isometrica 30° del hueco
  completo: pisos apilados, puertas en la pared de acceso, cabina como bloque solido y **niveles con
  incidencia en rojo** (reusa `floors_with_issues`, clave `matrix`). Lienzo VERTICAL (460×700).
  ⚠️ **Planta a escala real pero ALTURA COMPRIMIDA y declarado en el subtitulo:** sin comprimir, 18 m
  contra 1,3 m dan una astilla ilegible; comprimida al maximo deja de leerse como hueco. El presupuesto
  reparte el alto entre el rombo de la base y la columna (`kz = (VH-200-diam)/H`; **no poner un piso
  minimo a kz**, pisa el presupuesto y desborda el lienzo).
  ⚠️ En isometrica con Z arriba solo se dibujan las caras que MIRAN al observador (esquina inferior =
  `x=max, y=max`); dibujar las traseras saca cunas por fuera del solido.
- Integrado en: app (expander "🧊 Vista isometrica", alto 730; plantas 500 px/piso), informe cliente
  (§5 "Diagramas del hueco", isometrica + plantas) e informe admin. `report.py`/`user_report.py` pasan
  `rl`/`fb`/`n_floors`/`proyecto`.
- Se eliminaron `_clearance_px`, `_label_box`, `_state` y `_f` (0 usos tras el cambio).
- Verificado: SVG valido, sin `<defs>/<marker>/<pattern>`, `svg2rlg` lo convierte y **los 24 textos
  (incluidas las cotas rotadas) llegan al PDF**; PDF real de 3 paginas generado.

## Fix: perdida de datos al cambiar de fase + Excel pisando el PDF (v118)
**1. CRITICO — Streamlit descarta el estado de un widget que NO se renderiza en el rerun.** Con el Survey en
2 fases (v114), al pasar a "Resultados" los `inp_*`, `ns`, `cfg_*` y proyecto/cliente/ubicacion/ingeniero
(que solo se dibujan en "Datos") se PERDIAN. Fix: al inicio de la seccion, antes de crear ningun widget, se
re-asignan a si mismas (`st.session_state[k] = st.session_state[k]`) -> las mantiene vivas entre fases.
REGLA: si un widget puede dejar de renderizarse (fases/tabs/condicionales), hay que "tocar" su clave en cada
rerun o su valor se pierde.
**2. El import de Excel pisaba los parametros leidos del PDF.** El .xlsx guarda tambien parametros y
configuracion y se restauraban siempre. Ahora hay checkbox "Restaurar tambien parametros y configuracion"
(por defecto DESMARCADO: solo se importa la matriz, el plano manda) + boton "Volver a importar el Excel"
para reimportar con otra opcion. El mensaje de exito indica que se importo.

## Fix: crash tras "Empezar un survey nuevo" (v117)
`AttributeError` en `st.session_state.last_pdf_name`. El reset de v113 BORRABA claves que luego se leen con
acceso por ATRIBUTO (`st.session_state.last_pdf_name`, `.calc_results`...). `_init_state()` no las repone
porque solo corre una vez (flag `initialized`), asi que la clave quedaba ausente y el acceso por atributo
lanza AttributeError (el acceso por `.get()` no).
Fix doble: (1) el reset ahora **reinicia a su valor por defecto** las claves criticas (pdf_extracted,
last_pdf_name, pdf_bytes, ns, survey_df, calc_results, proyecto/cliente/ubicacion/ingeniero) en vez de
borrarlas; solo se borran las auxiliares. (2) las lecturas de esas claves pasan a `.get()`.
REGLA: si borras una clave de session_state, o la reinicias, o todas sus lecturas usan `.get()`.

## Informe del CLIENTE rediseñado como presentacion (v116)
`core/user_report.py` reescrito en forma (el contenido tecnico se conserva). Concepto: documento visual,
no una lista de secciones.
- **Portada a sangre** dibujada en el canvas (`_portada`): azul COPEX, logo (`static/icon-512.png`),
  titulo grande y ficha del proyecto (cliente, proyecto, ubicacion, nº informe, fecha, paradas, preparado por).
- **Pie con paginacion "X de Y"** + barra de acento lateral en todas las paginas de contenido:
  `_NumeradoCanvas` (2 pasadas, receta estandar de ReportLab). La portada no lleva pie.
- **Nº de informe automatico**: `numero_informe()` -> `INF-AAAAMMDD-HHMM` (unico y ordenable, sin estado).
- **Separadores de seccion tipo diapositiva** (`_section`): numero grande + titulo sobre banda azul.
- **Veredicto con semaforo** (`_veredicto`) al inicio Y en conclusiones: apto / apto con observaciones /
  sin solucion, derivado de `total_off`.
- **Tarjetas KPI** (`_kpi_cards`), **callouts** (`_callout`) para lo accionable, **tablas cebra** (`_zebra`).
- **Secciones nuevas**: 10 Alcance y metodologia + limitaciones, 11 Glosario en tarjetas 2 columnas,
  12 Conclusiones + bloque de firma (preparado por / recibido por). Indice de contenidos tras el veredicto.
- **Datos ampliados**: el Survey ahora pide Proyecto / Cliente / Ubicacion / Ingeniero (antes 'Proyecto o
  Cliente' en un solo campo). Van a `all_params` (CLIENTE/UBICACION) y prellenan el guardado de proyecto.
Validado generando un PDF real: 8 paginas con portada, nº informe, glosario, alcance, conclusiones y firma.

## Survey mas pro: 8 mejoras (v115)
1. **Solucion ACTIVA elegible** (`sol_activa`): el optimizador propone varias soluciones optimas pero antes
   diagramas/plomado/informe usaban SIEMPRE `best`. Ahora un selectbox permite elegir otra por criterio de
   obra; al cambiar se escribe `calc_results["optimizer_result"]["best"]` y se RECALCULA el plomado, asi
   todo lo aguas abajo (diagramas, informes, guardar proyecto) queda consistente.
2. **Resumen ejecutivo** arriba de los resultados: RL, FB, nº fuera de limite, nº de soluciones + semaforo.
3. **Checklist listo-para-calcular** en la fase Datos (plano / parametros / matriz).
4. **Diagrama con filtro de pisos**: `diagrams.floors_with_issues` + `render_floor_plans_html(floors=...)`
   (conserva el indice real del piso, asi las etiquetas siguen bien). Modos: Con incidencias / Todos / Elegir.
5. **Validacion temprana**: `validate_inputs` tambien en la fase Datos, no solo al calcular.
6. **Duplicar para el siguiente elevador** (opcional): conserva parametros+config, limpia matriz y resultados.
7. **Comparar soluciones lado a lado** (tabla con RL/FB/OFF por columna).
8. **Exportar diagramas sueltos a PDF**: `diagrams.floor_plans_pdf` (reusa `report._svg_flowable`), se genera
   bajo demanda con un boton (no en cada rerun).
Al recalcular se descartan `sol_activa`, `_diag_pdf` y `diag_pisos` (evita indices fuera de rango/PDF viejo).

## Survey en 2 fases (v114)
Los 7 pasos en scroll unico se reorganizaron en **2 fases** con `st.radio` (NO st.tabs):
**📝 Datos del survey** (pasos 1-3: plano, parametros, matriz) y **📊 Resultados e informes** (4-7:
resultados, cronograma, informe cliente, guardar proyecto). Al pulsar "Calcular y ver resultados" se
computa y salta solo a Resultados (via `_fase_pending` + rerun, porque no se puede escribir la clave de
un widget ya instanciado). En Resultados hay boton "Recalcular con los datos actuales".
**Cambio tecnico obligado:** el computo usaba variables locales del paso 2 (`omega_side`, `wall_limiting`,
`ctrl_side`...) que NO existen cuando esa fase no se renderiza -> nuevo `_cfg_from_state()` que lee la
configuracion de session_state (fuente de verdad). Lo usan `_survey_signature()` y `_do_calculo()`.
El bloque del boton se convirtio en la funcion `_do_calculo()`, invocable desde ambas fases.
Definidos fuera de las fases (accesibles a las dos): make_highlighter, _survey_signature,
_render_survey_results, _do_calculo.

## Survey: estetica e integracion (v113)
- **Marca por campo ✅/✏️** en los parametros del plano + metrica "Leidos del plano: X/17" y aviso con los
  que faltan. Recupera la senal perdida en v93 al quitar el panel del sidebar (sin volver a ocupar el sidebar).
- **Parametros agrupados por significado** (`_GRUPOS_PARAM`): Hueco / Cabina / Puerta-umbral / Frontal /
  Laterales / Contrapeso, en vez de una grilla plana de 17 numeros. Lo no agrupado cae en "Otros".
- **Configuracion** con titulo propio; "Parametros del usuario" -> "Parametros medidos en obra".
- **Boton "Empezar un survey nuevo"** (expander con aviso): limpia inp_*/cfg_*/ns/matriz/resultados de la
  sesion. Se procesa ANTES de crear los widgets (misma regla que el import).
- **Integracion con Reconstruir proyecto:** projects_ui marca `_rebuilt_from`; el Survey muestra
  "Cargaste el proyecto X, pulsa Calcular" y el aviso se limpia al calcular.

## Fix CRITICO: el import de Excel se repetia en cada rerun (v112)
Regresion introducida por v111. El `file_uploader` CONSERVA el archivo entre reruns; el bloque de import
estaba bajo `if uploaded_excel is not None:` (sin guarda). Antes de v111 no se notaba porque el import
crasheaba de inmediato; al arreglarlo, pasaba a re-importar en CADA rerun y **pisaba los valores leidos del
PDF o escritos a mano** ("los valores se modifican solos"), ademas de re-lanzar rerun.
Fix: guarda `last_excel_id = f"{name}:{size}"` (mismo patron que la carga de PDF, que si la tenia). Se marca
tanto en exito como en error (no reintenta en bucle). Ademas NADA se muta hasta tener todo parseado: la
matriz tambien viaja en `_import_pending["df"]` y se aplica arriba con el resto.
REGLA: todo `st.file_uploader` que dispare efectos debe llevar guarda por identidad de archivo.

## Fix import de Excel (v111)
`st.session_state.ns cannot be modified after the widget with key ns is instantiated`. El import de la matriz
escribia **claves de widgets YA creados** en la misma pasada: `ns` (Paso 3), todos los `inp_*` (Paso 2) y los
`cfg_*` (Paso 2). Fallaba en el primero; los demas habrian fallado igual -> el import estaba roto entero.
Fix (patron "pendiente + rerun"): el import guarda `st.session_state["_import_pending"] = {ns, params, cfg}`
y hace rerun; al inicio de la seccion Survey, ANTES de crear cualquier widget, se aplica y se borra.
`survey_df` si se escribe directo (no es clave de widget; el editor usa key="survey_editor").
REGLA: nunca escribir st.session_state[clave_de_widget] despues de instanciar ese widget; usar pendiente+rerun
(la carga de PDF ya lo hacia bien porque ocurre en el Paso 1, antes de los widgets).

## Survey: resultados persistentes (v110)
**Bug estructural corregido.** Todo el Paso 4 (matriz ajustada, resumen, soluciones del optimizador, log,
diagramas de planta, BSR vs BS, plomado definitivo) se dibujaba DENTRO de `if st.button("Calcular")`, asi que
cualquier interaccion posterior (cambiar un dato, descargar, abrir un expander, el chat) lo borraba y obligaba
a recalcular. Refactor en `app.py`:
- `_render_survey_results(r)`: funcion nueva con TODO el render, lee de `st.session_state.calc_results`.
  Se llama FUERA del boton -> los resultados sobreviven a los reruns.
- El boton ahora solo COMPUTA y guarda. Los efectos secundarios (optimize, find_bs_step, compute_plumb,
  generate_interpretation/user, generate_report + send_usage_notification por correo) siguen DENTRO del boton
  para que NO se repitan en cada rerun (antes: re-envio de correo / re-llamadas a la IA imposibles; ahora
  garantizado por construccion).
- `_survey_signature()`: huella md5 de parametros+config+matriz. Se guarda en `_calc_sig` al calcular; si al
  redibujar la huella cambio, avisa "resultados del calculo anterior, pulsa Calcular".
Verificado: orden sig<render<boton<render-persistente<PASO5, efectos secundarios dentro del boton, y cero
nombres indefinidos en la funcion de render (chequeo AST).

## Limpieza de codigo muerto (v109)
Auditoria: se listaron todas las `def` y se conto su uso real en el repo. Eliminado (0 referencias):
- `timeclock.validate_user` + `_get_users_ws` + `USERS_SHEET`/`USERS_HEADERS` -> **flujo viejo de PIN**
  (el login por PIN se reemplazo por auth en v53). Al borrarlo, la app ya NO puede recrear la pestana
  `Usuarios` del Sheets.
- `timeclock.get_records`, `auth.can_manage_users`, `manuals.manual_names`, `alerts.open_count`,
  `projects.set_estado_manual`, `session_cookie.available`.
Verificado tras la limpieza: los 40 modulos compilan e importan; no hay imports sin usar.
Pestanas del Sheets en uso: Sheet1(fichaje), Login, Grupos, Proyectos, Actividades, Agrupaciones,
Documentos, Rieles, Alarmas, Manuales, PreStarts, Credenciales, Gastos. **`Usuarios` ya no se usa.**

## Auditoria de llamadas #2 (v108)
Auditoria completa de `get_all_records` por funcion contenedora (display vs escritura). Hallazgos y fix:
- `timeclock.open_sessions` y `timeclock.group_hours` leian la hoja ENTERA **en cada render** (pestana de
  fichaje y reporte de horas). Fix: `timeclock._cached_records()` (ttl 20 s) + `_invalidate_records()` al
  hacer clock in/out (asi el estado del reloj se ve al instante tras fichar).
- `auth.list_groups` leia la hoja Grupos en cada render de los paneles del propietario. Fix: `_group_records`
  (ttl 60 s) + `_invalidate_groups()` en add/delete.
- `expenses.group_expenses` recorria todos los proyectos (project_cost/labor_cost) en cada render -> cacheado 60 s.
REGLA: lecturas de DISPLAY siempre por lector cacheado; las rutas de ESCRITURA (clock_in/out, add/delete,
save_activities, _find_row, verify_login/session) leen FRESCO a proposito.

## Lote 2 + extras (v107)
- **Matriz de compliance:** `credentials.matrix(grupo)` -> (tipos, filas) usuarios x credenciales con
  semaforo (verde vigente / amarillo por vencer / rojo vencido / - no registrada). En admin -> Usuarios -> Credenciales.
- **Panel del propietario con tarjetas:** `render_owner_projects` usa `_portfolio_html(show_group=True)`
  (badge del grupo en el subtitulo) + la tabla queda en un expander.
- **Resumen multi-grupo del propietario:** `admin_digest.owner_digest()` (cacheado 60 s) -> nueva seccion
  Administracion -> "Resumen": por grupo activos/avance/retrasos/alarmas/vencidos/credenciales/sobre presupuesto.
- **Dashboard de agrupacion:** `projects_ui._dashboard_agrupacion` en el panel de Agrupaciones: avance
  consolidado ponderado, elevadores, horas, costo total vs presupuesto sumado, tabla por proyecto + barras.
- **Reconstruir proyecto:** en el detalle, "Cargar este proyecto en el Survey" restaura ParamsJSON+MatrizJSON
  a session_state (inp_*, ns, survey_df) para recalcular y regenerar informes.
- **Briefing por Telegram/email:** boton "Enviarmelo" en el Resumen del dia (usa notify.notify_user).
  Limitacion: Streamlit no tiene cron, se envia a demanda (no a una hora fija).
- **Login persistente con cookies:** `core/session_cookie.py` (extra-streamlit-components, import PEREZOSO
  con fallback: sin la libreria la app funciona igual). Guarda `usuario|token` 7 dias; al abrir valida con
  `auth.validate_session(usuario, token)` contra la hoja Login (token = el de la sesion unica) y restaura.
  Se limpia al cerrar sesion. Dependencia nueva en requirements.
- **Ronda de optimizacion (como v92):** `projects.gaps_by_group` (cache 60 s) evita reconstruir el cronograma
  de cada proyecto varias veces por render (KPIs + tarjetas + tabla + radar); `admin_digest.group_digest` y
  `expenses.over_budget` cacheados 60 s. Nuevos helpers `delays_of_group` / `aheads_of_group`.

## Lote de mejoras + fichaje por USUARIO (v106)
- ⚠️ **Fichaje identificado por Usuario (login), no por Nombre.** Columna `Usuario` en la hoja de fichaje
  (migra sola). `timeclock._matches(r,usuario,nombre,grupo)`: usa `Usuario`; las filas ANTIGUAS (sin
  Usuario) caen al `Nombre`. clock_in/clock_out/open_sessions/switch_project aceptan `usuario=`;
  `group_hours` agrupa por usuario (devuelve `usuario` + `nombre`). `auth.rate_map` indexa por Usuario **y**
  por Nombre (respaldo); `expenses.labor_cost` costea por Usuario. Evita mezclar horas de homónimos.
- **Adelantos:** `projects._gaps_for` → `delays_for` (gap>0.5) y **`aheads_for`** (gap<-0.5). Tarjetas del
  admin: retraso = borde rojo + ⏰ N d; **adelanto = borde verde + ⏩ N d**. Tabla del propietario: columna ⏩.
- **Presupuesto al crear** el proyecto (survey → Guardar como proyecto, `create_project(presupuesto=)`).
- **Gráficas de costos** en 💰 Gastos: barras costo por proyecto (compras vs MO) y por categoría (st.bar_chart).
- **Reenvío de inducciones**: si el admin cambia `InduccionLinks` al editar, se reenvían a los ya asignados.

## Control de costos por proyecto: gastos + mano de obra (v105)
`core/expenses.py` — hoja **`Gastos`** (ID,ProyectoID,Grupo,Fecha,Categoria,Proveedor,Descripcion,Valor,
DriveID,Archivo,CreadoPor,Creado; migra sola). Recibos por proyecto (foto/PDF a Drive, carpeta "COPEX
Recibos") + valor + categoría (`CATEGORIAS`). Los cargan **admin, campo y conductor**.
- **Costo total = compras + mano de obra.** `labor_cost(pid,grupo)` = Σ (horas de cada persona en el proyecto
  × su **tarifa/hora**). Tarifa **por usuario**: columna `Login.TarifaHora` (v105; `auth.set_rate`,
  `auth.rate_map` {Nombre:tarifa}, incluida en `list_users`). El fichaje se cruza por Nombre.
- **Presupuesto por proyecto**: columna `Proyectos.Presupuesto` (editable en el detalle). `project_cost` →
  {compras, mano_obra, total, presupuesto, pct, over}. Sobre presupuesto entra al **radar** (`sobre_presupuesto`
  en admin_digest → chip 💸 en Resumen del día + briefing).
- UI (`projects_ui`): `render_expenses(pid,grupo,can_delete)` (panel de costos + cargar recibo + lista +
  descargar/eliminar) en el detalle admin (can_delete), 📋 Mis proyectos (campo) y 📋 Proyectos (conductor,
  selector). Reporte del admin: 🛠 Mi grupo → **💰 Gastos** (`render_group_expenses`: por proyecto compras/MO/
  total/presupuesto/%, desglose por categoría, **export CSV**). Tarifa se fija en 🔧/👥 Usuarios (`set_rate`).

## Credenciales / tickets por usuario (v104)
`core/credentials.py` — hoja **`Credenciales`** (ID,Usuario,Grupo,Tipo,Numero,Clase,Emision,Vencimiento,
DriveID,Archivo,Nota,UltimoAviso,ActualizadoPor,Fecha; migra sola). Catálogo AU (`CATALOGO`: White Card,
Forklift LF, Dogging DG, Rigging RB/RI/RA, EWP/Boom WP, Working at Heights, First Aid, Driver License +
clases, Otro). `status(venc)` = vigente/por_vencer(≤30 d)/vencido/''; `expiring(grupo)`; CRUD `add/update/
delete`; `upload_file` (foto/documento a Drive, carpeta "COPEX Credenciales"); `notify_expiring(grupo)`
(avisa admin/propietario + usuario dueño, deduplicado por UltimoAviso <25 d).
- Gestión (admin en 🔧 Usuarios, propietario en 👥 Usuarios): `auth_ui.render_credenciales(usuario,grupo,
  editable=True)` — agregar (al crear el usuario o luego)/editar/eliminar + subir foto o documento. El aviso
  de vencimientos se dispara 1 vez por sesión al abrir el panel del admin.
- El usuario ve las suyas: `auth_ui.render_my_credentials` → nav **🎫 Mis credenciales** (campo y conductor).
- **Radar:** `admin_digest.group_digest` añade `cred_venc` → chip 🎫 en el Resumen del día + el briefing IA.

## Rol conductor + fichaje de 2 relojes + cronómetro (v103)
Nuevo rol **`conductor`** (auth.ROLES). Ficha con DOS relojes en paralelo (hoja fichaje gana columna
**`Tipo`** = `general`|`proyecto`, migra sola en `_cached_ws`; filas viejas = proyecto):
- **Jornada general** (total de horas del día) + **segmentos por proyecto** (para fichar a un proyecto
  DEBE haber jornada general abierta). Un usuario puede tener 1 general + 1 proyecto abiertos a la vez.
- `timeclock`: `clock_in/clock_out(..., tipo)`, `open_sessions(nombre,grupo)`, `switch_project` (cambio en
  1 toque = cierra segmento + abre nuevo), `elapsed_seconds`, `group_hours(grupo,days)` (resumen por usuario:
  general, proyecto, **sin_asignar = general − Σproyecto** = transporte/espera, y desglose por proyecto).
- UI `timeclock_ui`: `_render_normal` (todos los roles: proyecto + **cronómetro en vivo** client-side JS,
  `_chronometer`) y `_render_conductor` (2 relojes, cronómetro en ambos, cambio de proyecto, aviso de jornada
  olvidada `_aviso_olvido`). **El cronómetro es para TODOS** los roles en el fichaje.
- Nav conductor: `⏱ Fichaje` (2 relojes) + `📋 Proyectos` (`projects_ui.render_conductor_projects`: lista
  solo lectura, datos básicos + Maps, SIN avances ni actividades).
- Reporte **solo admin**: 🛠 Mi grupo → **⏱ Horas** (`projects_ui.render_group_hours`) = horas de TODOS los
  usuarios del grupo (Hoy/Semana/Mes/Todo) con general, proyectos, sin asignar y desglose. Sesiones abiertas
  cuentan con el tiempo transcurrido. Creación de conductores: admin en 🔧 Usuarios (rol campo|conductor;
  conductor no exige email/Telegram).

## Fix NS desde el plano (v102)
NS (número de paradas) volvía a quedar pegado en un default de 6 y **no se leía del PDF**. Fix:
`extractors.schindler.extract_number_of_stops(pdf)` (regex `NUMBER OF STOPS\s+(\d{1,2})` sobre texto
posicional + plano) → app.py, al cargar el PDF, setea `st.session_state["ns"]` (2–50) y muestra caption
`ns_msg`. El default de init pasó de **6 → 2** (mínimo neutro; el NS real sale del plano). La lógica de
resize de la matriz (survey_df) ya ajusta las filas al cambiar NS. Validado: NORTH SYD y AGECARE → NS=6
(coincide con travel/floor-height HQ/HE).

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

## Versiones desplegadas (v322 = actual)
⚠️ La tabla NO está completa: v241-v288 se desplegaron sin registrarse aquí (el documento se quedó
atrás). Lo que sí está descrito arriba, en sus secciones propias, es lo que se construyó en ese
tramo (Contactos/CRM, Finanzas, Inventario, geocoder, ruta del día, sistema de diseño). Para el
detalle exacto de una versión no listada: `git log`.

| Ver | Cambio principal |
|---|---|
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
