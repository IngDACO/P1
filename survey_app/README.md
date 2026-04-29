# Survey Analyzer — Elevator Rail Survey Tool

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar

```bash
streamlit run app.py
```

## Estructura

```
survey_app/
├── app.py                  # Aplicación principal
├── requirements.txt
├── extractors/
│   ├── schindler.py        # Extractor PDF Schindler
│   ├── otis.py             # (futuro)
│   └── kone.py             # (futuro)
├── core/
│   ├── calculations.py     # Límites, offsets, CS, TL, TLBC
│   ├── optimizer.py        # Loop de optimización RL/FB
│   └── bs_logic.py         # Lógica BSR vs BS
└── ui/                     # (componentes futuros)
```

## Flujo de uso

1. Seleccionar marca y cargar PDF de planos
2. Revisar/completar parámetros extraídos
3. Ingresar parámetros de campo (BSR, BC, FS, FRAME, RAIL)
4. Configurar lado del Omega y pared limitante
5. Ingresar número de paradas y matriz SURVEY
6. Presionar **Calcular**
7. Ver matriz ajustada, resumen y matriz solución óptima
