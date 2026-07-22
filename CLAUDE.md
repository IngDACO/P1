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
│   ├── auth_ui.py          # render_login/user_bar/owner_panel(grupos/usuarios/proyectos/rieles)/group_panel
│   ├── projects.py         # gestión de proyectos: Proyectos/Actividades/Agrupaciones/Documentos (Sheets) — v65+
│   ├── projects_ui.py      # panel admin/propietario/campo + docs + alarmas + cronograma real vs plan
│   ├── drive_store.py      # documentos por proyecto en Google Drive (OAuth drive.file) — v74
│   ├── notify.py           # notificaciones email + Telegram (asignación, avisos) — v77
│   ├── alerts.py           # alarmas/avisos por proyecto (campo↔admin) — v88
│   ├── belting.py          # compute_belting/belting_svg — belting (DSTS) — v86
│   ├── belting_ui.py       # render_belting_tab()
│   └── rails.py            # catálogo de rieles (referencia→medidas) para autocompletar RAIL — v84
└── extractors/
    └── schindler.py        # extract_from_pdf() + extract_car_guide_rail() + extract_belting() — pypdf CAD PDF

C:\Users\diego\copex_mobile\   # App Android (Capacitor) — carga la URL de Streamlit; ver sección Móvil
```

**Versión (v35+):** `app.py` lee `survey_app/VERSION` con `utf-8-sig` (evita el BOM que agrega
PowerShell). `backup_survey.ps1` escribe `"vNN"` antes de cada commit → se actualiza sola.

## NAVEGACIÓN — NO usar st.tabs ⚠️ (v56)
`st.tabs` causaba **mezcla de contenido** entre pestañas (bug de Streamlit con contenido pesado
+ reruns; también con tabs anidados). Se reemplazó por un **selector `st.radio` horizontal** que
renderiza SOLO la sección activa (`if/elif _seccion == ...`). El survey completo va bajo
`if _seccion == _L_SURVEY:` (Paso 1→6). **No volver a introducir `st.tabs`** (ni anidados).

Secciones visibles según el rol (ver Login/Roles):
- Todos: 📐 Survey · 🔩 Plomadas · ✂️ Corte de rieles · ⏱ Fichaje
- Propietario: + 👑 Administración   |   Administrador: + 🛠 Mi grupo   |   Campo: sin extra y sin descargar informes

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
- **Campo** (📋 Mis proyectos): ve asignados (`list_projects_for_field`), actualiza Avance% por actividad (`update_activity_progress` recalcula proyecto). `render_field_projects`.
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

## Versiones desplegadas (v141 = actual)
| Ver | Cambio principal |
|---|---|
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
