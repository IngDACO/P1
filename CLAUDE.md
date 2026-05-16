# Survey App — IngDACO/P1

## Descripción
Aplicación Streamlit para análisis de surveys de elevadores (Schindler).
Extrae parámetros de PDFs de planos, corre un optimizador de posición,
y genera un reporte PDF con los resultados.

## Estructura del proyecto
```
survey_app/
├── app.py                      # UI principal Streamlit
├── requirements.txt
├── core/
│   ├── calculations.py         # calculate_limits() y apply_offsets()
│   ├── optimizer.py            # optimize() — búsqueda por RL/FB
│   ├── report.py               # Generación del reporte PDF (ReportLab)
│   ├── bs_logic.py             # Lógica de selección BS
│   └── excel_io.py             # Lectura/escritura Excel
└── extractors/
    └── schindler.py            # Extracción de parámetros del PDF Schindler
```

## Deploy
- **Streamlit Cloud:** https://dwl6s39d7u3yfwfkbpcpah.streamlit.app/
- **GitHub:** https://github.com/IngDACO/P1 (rama: main)
- Push a main → redeploy automático en Streamlit

## Fórmulas clave (versión actual)

### Límites geométricos
```python
LIMIT_WR = SF2 + RAIL/2
LIMIT_WL = SF1 + RAIL/2
LIMIT_FR = TKSW - 150
LIMIT_FL = TKSW - 150
LIMIT_OR = WALL_RIGHT - SF2 - RAIL/2   # muro derecho de la apertura
LIMIT_OL = WALL_LEFT  - SF1 - RAIL/2   # muro izquierdo de la apertura
```

### Offsets aplicados al survey (apply_offsets)
```python
OR = row["OR"] - Offset_OR   # resta (no suma)
OL = row["OL"] - Offset_OL   # resta (no suma)
```

### Selección óptima
1. Criterio 1: minimizar total de valores fuera de límite (OFF)
2. Criterio 2 (desempate): minimizar desplazamiento total `|RL| + |FB|`

### OR/OL en el optimizador
- Si `WALL_LIMITING = False`: cols activas = `[WR, FR, WL, FL]` (OR/OL excluidos)
- Si `WALL_LIMITING = True`:  cols activas = `[WR, FR, OR, WL, FL, OL]`

## Convenciones de código
- Python 3.11+, tipado con type hints
- Funciones puras (sin side-effects) en `core/`
- UI exclusivamente en `app.py`
- El reporte debe reflejar SIEMPRE las fórmulas reales que se usan en el cálculo
- Cuando cambies una fórmula en `calculations.py` → actualiza también `report.py`

## Inputs del usuario (app.py)
- Marca: Schindler (único por ahora)
- PDF de planos → extractor lee parámetros automáticamente
- Parámetros editables del PDF (TKSW, BKF1, BKF2, BKS, TKA, TKS, TSW, BGS, etc.)
- Muro izquierdo de la apertura (WALL_LEFT) y derecho (WALL_RIGHT)
- Configuración de pared limitante (WALL_LIMITING, WALL_STOP, WALL_SIDE)

## Backup
- Google Drive: https://drive.google.com/drive/folders/1PK7znRaCGWcycDJ6neUJPy72TqwgSxQW
- Cada versión en subcarpeta `vN — YYYY-MM-DD` con ZIP de todos los .py

## Comandos útiles
```bash
# Correr localmente
cd survey_app
pip install -r requirements.txt
streamlit run app.py

# Push a producción
git add -A
git commit -m "descripción del cambio"
git push origin main
```
