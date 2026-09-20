# -*- coding: utf-8 -*-
"""v486: los cuatro sitios que pintaban «None» pasan por `tabla.celda` + `derecha`.

Todo o nada: si un ancla no es unica o algo no compila, no se escribe NADA.
"""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")

NL = chr(10)

PARCHES = [
    # ── 1. el parte de horas (el fallo de v485) ──────────────────────────────
    ("core/contable_ui.py",
     NL.join([
        '        det = contable.partes(grupo, desde, hasta)',
        '        _filas = [dict({t("Employee"): f["nombre"], t("Payroll ID"): f["payroll_id"],',
        '                        t("Earnings rate"): f["etiqueta"]},',
        '                       # \u26a0\ufe0f NaN y no None: con la columna entera vac\u00eda pandas la deja',
        '                       # en `object` y Streamlit imprime el texto \u00abNone\u00bb \u2014 el fallo que',
        '                       # document\u00f3 v467, y se ve\u00eda en la tabla del parte. Con NaN la',
        '                       # columna es float y la celda sale vac\u00eda, igual que en el CSV.',
        '                       **{d.strftime("%a %d/%m"): f["horas"].get(d, float("nan"))',
        '                          for d in det["dias"]},',
        '                       **{t("Total"): f["total"]})',
        '                  for f in det["filas"]]',
        '        st.dataframe(pd.DataFrame(_filas), hide_index=True, width="stretch",',
        '                     column_config=tabla.cfg())']),
     NL.join([
        '        det = contable.partes(grupo, desde, hasta)',
        '        # Una sola definici\u00f3n de la etiqueta del d\u00eda: la usan las filas Y la',
        '        # configuraci\u00f3n de columnas, as\u00ed que no hay dos listas en paralelo que',
        '        # puedan desincronizarse (v433/v434).',
        '        _etq_dia = {d: d.strftime("%a %d/%m") for d in det["dias"]}',
        '        _filas = [dict({t("Employee"): f["nombre"], t("Payroll ID"): f["payroll_id"],',
        '                        t("Earnings rate"): f["etiqueta"]},',
        '                       # \u26a0\ufe0f Cadena, NO un nulo: `st.dataframe` pinta cualquier nulo',
        '                       # como el literal \u00abNone\u00bb en gris y no hay configuraci\u00f3n que lo',
        '                       # evite \u2014 el cuadro de lo medido est\u00e1 en `tabla.celda`. Con NaN',
        '                       # (v485) se segu\u00eda viendo \u00abNone\u00bb en producci\u00f3n. El d\u00eda sin',
        '                       # horas sale vac\u00edo, igual que en el CSV.',
        '                       **{_etq_dia[d]: tabla.celda(f["horas"].get(d), 2)',
        '                          for d in det["dias"]},',
        '                       **{t("Total"): tabla.celda(f["total"], 2)})',
        '                  for f in det["filas"]]',
        '        st.dataframe(pd.DataFrame(_filas), hide_index=True, width="stretch",',
        '                     column_config=tabla.cfg(None, dict(',
        '                         {c: tabla.derecha(c) for c in _etq_dia.values()},',
        '                         **{t("Total"): tabla.derecha(t("Total"))})))'])),

    # ── 2. nómina: «Rate/h» (el pie PROMETE que vacío = sin tarifa) ──────────
    ("core/payroll_ui.py",
     NL.join([
        '        "Rate/h": (round(_num(x.get("HourlyRate")), 2)',
        '                     if _num(x.get("HourlyRate")) > 0 else float("nan")),']),
     NL.join([
        '        # \u26a0\ufe0f Cadena vac\u00eda, NO NaN: un nulo se pinta \u00abNone\u00bb en gris (ver el cuadro',
        '        # en `tabla.celda`), y el pie de ESTA tabla promete que un \u00abRate/h\u00bb vac\u00edo',
        '        # significa que esa persona no tiene tarifa puesta. Dec\u00eda \u00abNone\u00bb.',
        '        "Rate/h": (tabla.celda(x.get("HourlyRate"), 2, "$")',
        '                     if _num(x.get("HourlyRate")) > 0 else ""),'])),
    ("core/payroll_ui.py",
     '                       "Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,.2f")}))',
     '                       "Rate/h": tabla.derecha(t("Rate/h"))}))'),

    # ── 3. inventario: «Costo» del historial ─────────────────────────────────
    ("core/inventory_ui.py",
     NL.join([
        '            # \u26a0\ufe0f NaN y no None: si TODA la columna es None, pandas la deja en',
        '            # `object` y Streamlit pinta el literal \u00abNone\u00bb; con NaN es float y',
        '            # sale vacia (medido, no supuesto).',
        '            "Costo":   (round(_num(m.get("Cost")), 0) if str(m.get("Cost", "")).strip()',
        '                        else float("nan")),']),
     NL.join([
        '            # \u26a0\ufe0f Cadena vac\u00eda, NO NaN: `st.dataframe` pinta cualquier nulo como el',
        '            # literal \u00abNone\u00bb en gris y ninguna `column_config` lo evita \u2014 el cuadro',
        '            # de lo medido est\u00e1 en `tabla.celda`. Lo que dec\u00eda aqu\u00ed («con NaN sale',
        '            # vacia, medido») era FALSO: esta tabla segu\u00eda diciendo \u00abNone\u00bb.',
        '            "Costo":   (tabla.celda(m.get("Cost"), 0, "$")',
        '                        if str(m.get("Cost", "")).strip() else ""),'])),
    ("core/inventory_ui.py",
     '            column_config=tabla.cfg(None, {"Costo": st.column_config.NumberColumn(t("Cost"), format="$%,d")}))',
     '            column_config=tabla.cfg(None, {"Costo": tabla.derecha(t("Cost"))}))'),

    # ── 4. catálogo: «Horas» de un producto ──────────────────────────────────
    ("core/catalogo_ui.py",
     NL.join([
        '            # \u26a0\ufe0f NaN, no None: una columna ENTERA de None la deja pandas en',
        '            # `object` y Streamlit pinta el literal \u00abNone\u00bb (pasaba con un',
        '            # catalogo de solo productos).',
        '            "Horas": (round(_num(i.get("EstHours")), 2)',
        '                      if str(i.get("Type", "")) == CAT.SERVICIO else float("nan")),']),
     NL.join([
        '            # \u26a0\ufe0f Cadena vac\u00eda, NO NaN: `st.dataframe` pinta cualquier nulo como el',
        '            # literal \u00abNone\u00bb en gris, con o sin `column_config` (cuadro de lo medido',
        '            # en `tabla.celda`). Un producto no tiene horas, y se ve\u00eda \u00abNone\u00bb.',
        '            "Horas": (tabla.celda(i.get("EstHours"), 2)',
        '                      if str(i.get("Type", "")) == CAT.SERVICIO else ""),'])),
    ("core/catalogo_ui.py",
     NL.join([
        '                           column_config=tabla.cfg(None, {"Costo": st.column_config.NumberColumn(',
        '                               t("Cost"), format="$%,.2f", help=t("Product: unit cost. Service: hours \u00d7 rate."))}))']),
     NL.join([
        '                           column_config=tabla.cfg(None, {',
        '                               "Horas": tabla.derecha(t("Hours")),',
        '                               "Costo": st.column_config.NumberColumn(',
        '                                   t("Cost"), format="$%,.2f",',
        '                                   help=t("Product: unit cost. Service: hours \u00d7 rate."))}))'])),
]


def main():
    textos = {}
    for fich, _v, _n in PARCHES:
        textos.setdefault(fich, io.open(fich, encoding="utf-8").read())

    # 1) TODAS las anclas antes de escribir una sola
    pend = dict(textos)
    for i, (fich, viejo, nuevo) in enumerate(PARCHES, 1):
        n = pend[fich].count(viejo)
        if n != 1:
            raise SystemExit("parche %d (%s): el ancla aparece %d veces" % (i, fich, n))
        pend[fich] = pend[fich].replace(viejo, nuevo, 1)

    # 2) compilar
    import warnings
    for fich, s in pend.items():
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(s, fich, "exec")

    # 3) escribir
    for fich, s in pend.items():
        io.open(fich, "w", encoding="utf-8", newline="").write(s)
        print("ok", fich)


main()
