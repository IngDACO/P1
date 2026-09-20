# -*- coding: utf-8 -*-
"""v471 (2/2) · los huerfanos de `column_config` y las cabeceras que salian crudas."""
import io
import os

RAIZ = r"C:\Users\diego\P1\survey_app"
hechos, fallos = [], []


def parche(rel, viejo, nuevo, etq):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    s = io.open(p, encoding="utf-8").read()
    n = s.count(viejo)
    if n != 1:
        fallos.append("%s · %s: ancla %s (%d)"
                      % (rel, etq, "ausente" if not n else "ambigua", n))
        return
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(viejo, nuevo))
    hechos.append("%s · %s" % (rel, etq))


# ── 1 · clientes_ui: el `column_config` apuntaba a columnas que la fila no tiene ──
parche(
    "core/clientes_ui.py",
    '''    _colcfg = {"Progress": st.column_config.ProgressColumn(
        t("Progress"), min_value=0, max_value=100, format="%d%%")}
    if _hay_costo:
        _colcfg["Cost"] = st.column_config.NumberColumn(t("Cost"), format="$%,d")''',
    '''    # ⚠️ Las claves tienen que ser las de la FILA ("Avance"/"Costo"), no la etiqueta.
    # v468 las renombro aqui y no arriba, asi que las dos quedaban HUERFANAS: la barra
    # de progreso no se aplicaba y —peor— la columna de dinero perdia su `$%,d`, o sea
    # que v468 reintrodujo ahi el fallo de v399 (el importe sin separador de miles).
    _colcfg = {"Avance": st.column_config.ProgressColumn(
        t("Progress"), min_value=0, max_value=100, format="%d%%")}
    if _hay_costo:
        _colcfg["Costo"] = st.column_config.NumberColumn(t("Cost"), format="$%,d")''',
    "clientes: progreso y costo huerfanos")

# ── 2 · las cabeceras que se pintaban con su clave CRUDA, en español ─────────────
parche(
    "core/tabla.py",
    '    "Elevador": "Lift",',
    '''    "Elevador": "Lift",
    # ⚠️ v471 · estas se pintaban con su CLAVE cruda, en español, dentro de tablas por
    # lo demas inglesas — la sexta red de v450 con lo que se le escapo. No se puede
    # renombrar la clave: `Riel` y `Actividad` las LEE el codigo de vuelta y `Riel`
    # ademas viaja a `DatosJSON` (v443), asi que reabrir un calculo dejaria de casar.
    # La etiqueta es justo lo que se cambia sin tocar el dato.
    "Riel": "Rail",
    "Actividad": "Activity",
    "Avance": "Progress",
    "Inicio real": "Actual start",
    "Fin real": "Actual finish",
    "Ganancia": "Profit",
    "Orden": "Order",
    "D\u00edas": "Days",''',
    "cabeceras que faltaban en el mapa")

print("APLICADO:")
for h in hechos:
    print("   ok  " + h)
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   !!  " + f)
    raise SystemExit(1)
