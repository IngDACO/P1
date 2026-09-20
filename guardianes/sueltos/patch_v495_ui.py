# -*- coding: utf-8 -*-
"""v495 · el botón «traer cobros de Xero» y su resumen."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")
P = "core/xero_ui.py"
s = io.open(P, encoding="utf-8").read()

# 1 · el resumen de la traída, junto al del envío
ANCLA_F = '''def procesar_retorno(rol: str, grupo: str) -> None:'''
assert s.count(ANCLA_F) == 1
NUEVO_F = '''def _flash_cobros(res: dict):
    """Lo que trajo Xero, contado por separado (v495).

    ⚠️ Cada caso se dice: un «se actualizaron 2» que calle que otras tres siguen en
    borrador —y que por eso nunca traerán un cobro— deja la pantalla tranquila y el
    «por cobrar» mal (v325).
    """
    from core import theme as T          # ⚠️ local: en este módulo theme se importa así
    for _fid, numero, antes, ahora in res["actualizadas"]:
        flash.exito(t("Invoice {n}: collected {a} in Xero (it was {b} here).",
                      n=numero or "—", a=T.dinero(ahora), b=T.dinero(antes)))
    if res["iguales"]:
        flash.info(t("{n} invoice(s) already matched Xero.", n=len(res["iguales"])))
    if res["en_borrador"]:
        flash.aviso(t("Still a draft in Xero, so no payment can arrive: {l}. Your accountant "
                      "approves them in Xero.",
                      l=", ".join(_md(x[1] or x[0]) for x in res["en_borrador"])))
    for _fid, numero, credito in res["con_credito"]:
        flash.aviso(t("Invoice {n} has {c} of credit notes or prepayments applied in Xero. "
                      "That is not money received, so it is not counted as collected here.",
                      n=numero or "—", c=T.dinero(credito)))
    for _fid, numero, est in res["muertas"]:
        flash.aviso(t("Invoice {n} is {e} in Xero: nothing was changed here.",
                      n=numero or "—", e=est.lower()))
    if res["no_encontradas"]:
        flash.aviso(t("Not found in Xero (deleted there?): {l}",
                      l=", ".join(_md(x[1] or x[0]) for x in res["no_encontradas"])))
    for e in res["errores"]:
        flash.error(_md(str(e)))
    for a in res["avisos"]:
        flash.aviso(a)


'''
s = s.replace(ANCLA_F, NUEVO_F + ANCLA_F)

# 2 · el botón, después del bloque de envío y antes de desconectar
ANCLA_B = '''    # ⚠️ v489: era un desplegable TITULADO «Disconnect Xero» con una casilla y el botón
'''
assert s.count(ANCLA_B) == 1
NUEVO_B = '''    # ── v495 · dirección Xero → COPEX: el cobro lo registra el contable allí ──
    # ⚠️ Con un BOTÓN (decisión del usuario): leerlo al abrir la pantalla gastaría
    # llamadas a Xero en cada visita, y así se ve en cada pasada qué se movió.
    st.markdown(t("**Payments**"))
    st.caption(t("Your accountant reconciles the bank in Xero; this brings what is "
                 "collected there into COPEX, so «to collect» here is not left stale."))
    if st.button(t(":material/download: Bring payments from Xero"), key="xero_traer_cobros"):
        with st.spinner(t("Reading Xero…")):
            res = X.traer_cobros(grupo)
        if not any(res[k] for k in res):
            flash.info(t("No invoice of this company has been sent to Xero yet."))
        _flash_cobros(res)
        st.rerun()

''' + ANCLA_B
s = s.replace(ANCLA_B, NUEVO_B)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("xero_ui: botón y resumen de cobros")
