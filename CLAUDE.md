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

---

## Estructura de archivos
```
C:\Users\diego\P1\survey_app\
├── app.py                  # UI Streamlit — SOLO presentación, sin lógica
├── requirements.txt        # pypdf, pandas, numpy, openpyxl, reportlab, streamlit
├── core/
│   ├── calculations.py     # calculate_limits(), apply_offsets(), analyze_matrix()
│   ├── optimizer.py        # optimize() — itera RL×FB, aplica restricciones
│   ├── report.py           # generate_report() — ReportLab PDF con diagramas ASCII
│   ├── bs_logic.py         # find_bs_step() — análisis BSR vs BS
│   └── excel_io.py         # export/import survey Excel
└── extractors/
    └── schindler.py        # extract_from_pdf() — pypdf CAD PDF parser
```

---

## Parámetros de entrada

### Del PDF (schindler.py los extrae)
`TKSW, BKS, TKA, TKS, TSW, BGS, BKF1, BKF2, BS, BT, BK, TK, TS, SF1, SF2, SG, TG`

### Del usuario (app.py — USER_ONLY)
`BSR, FS, FRAME, RAIL, OFFSET_CABIN`  
⚠️ `BC` fue **eliminado** de inputs — ahora se calcula como `BC_CALC`  
⚠️ `WALL_LEFT` / `WALL_RIGHT` fueron **eliminados** — reemplazados por `OFFSET_CABIN` + `OFFSET_SIDE`

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
4. Pared limitante (si wall=True y tsw < fs):
   - Verifica OR o OL en parada específica vs límite → SKIP si falla
```

### Cómo se aplican los desplazamientos en cada paso
```python
WR += rl;  FR += fb;  OR += rl
WL -= rl;  FL += fb;  OL -= rl
```

### Criterios de selección
1. **Criterio 1:** mínimo `total_off` (valores bajo su límite)
2. **Criterio 2 (desempate):** mínimo `|RL| + |FB|`

---

## Caso 1 vs Caso 2 — diferencias clave

| Aspecto | Caso 1 (WALL_LIMITING=True) | Caso 2 (WALL_LIMITING=False) |
|---|---|---|
| OR/OL en conteo OFF | Sí | **No** |
| MAX_OFF_RL fórmula | max(DIF_WR, DIF_OR, DIF_WL, DIF_OL) | max(DIF_WR, DIF_WL) |
| Columnas optimizer | WR FR OR WL FL OL | WR FR WL FL |
| Color OR/OL en tabla | Rojo si v < lim | **Naranja si v > lim** (requiere corte) |
| Columnas extra | — | CUT OR = OR−LIMIT_OR, CUT OL = OL−LIMIT_OL |

---

## Colores en tablas (app y reporte)
- 🔴 Rojo oscuro `#c0392b`: valor mínimo fuera de límite
- 🔴 Rojo claro `#f1948a`: fuera de límite
- 🟠 Naranja `#e67e22`: OR/OL requieren corte (Caso 2, v > lim)
- 🟢 Verde `#d4efdf`: solución óptima en log

---

## report.py — secciones del PDF
```
1. Parámetros entrada (PDF + usuario)
2. Dimensiones cabina (CS, TL, BC_CALC, TLBC) + 📊 diagrama perfil lateral
3. Límites geométricos (WR/WL/OR/OL/FR/FL/OB/ZB) + 📊 diagrama sección transversal
4. Offsets (FR, FL, WR, WL, OR, OL)
5. Matriz SURVEY original
6. Matriz SURVEY ajustada + análisis DIF por columna
7. Optimización: params + 📊 diagramas RL/FB + log + resultado final por solución
8. BSR vs BS
```
Función helper `_diagram_block(title, lines, styles)` — caja ASCII monoespaciada.

### Regla importante
**Si cambias una fórmula en calculations.py → actualizar también report.py (secciones 2, 3, 4).**

---

## extractors/schindler.py — extract_from_pdf()

Usa **pypdf modo normal** (un solo paso). ~20-25s por PDF CAD.  
**NO usar:** pdfplumber (da valores erróneos), pypdf layout mode (71s).

### Pipeline de extracción
```
Paso 1: CRLF → LF, unir dígito-\n-dígito  (fix: TKS=30\r\n62 → TKS=3062)
Paso 2: separar parámetros concatenados   (fix: TKSW=965TS=1750)
Paso 3: regex PARAM=VALUE                 (fix: BS=19981272 → truncar a BS=1998)
Paso 4: línea a línea:
  A) valor DESPUÉS del label  (PARAM=valor o PARAM valor)
  D) valor ANTES del label    (170BKF2 → BKF2=170)  ← Caso especial Schindler CAD
  B/C) label solo → buscar número en línea anterior/siguiente
```

---

## Versiones desplegadas (v9 = actual)
| Ver | Cambio principal |
|---|---|
| v5 | Extractor: CRLF fix, caso D valor-antes-label, sin pdfplumber |
| v6 | BC_CALC + FB_MAX_BACK constraint en optimizer |
| v7 | BC eliminado de inputs usuario, calculado automáticamente |
| v8 | Diagramas ASCII en reporte PDF (secciones 2, 3, 7) |
| v9 | Caso 2: OR/OL naranja cuando requieren corte, sin rojo por debajo límite |
