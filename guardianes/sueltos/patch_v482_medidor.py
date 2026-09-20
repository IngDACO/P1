# -*- coding: utf-8 -*-
"""FASE 0.2 — engancha el contador y le da pantalla al propietario."""
import ast
import io

# ── 1 · el enganche, en NUESTRA subclase del cliente HTTP ────────────────────
P = "C:\\Users\\diego\\P1\\survey_app\\core\\timeclock.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''        class _ConReintento(HTTPClient):
            def request(self, *a, **kw):
                for espera in _ESPERAS:
                    try:
                        return super().request(*a, **kw)
                    except APIError as e:
'''

NUEVO = '''        class _ConReintento(HTTPClient):
            def request(self, *a, **kw):
                # ⚠️ v482 · Se apunta CADA INTENTO, no cada llamada lógica: un 429
                # reintentado son dos llamadas contra la cuota, y contar solo la
                # lógica subestimaría justo la ráfaga que se quiere medir.
                _m = a[0] if a else kw.get("method", "")
                _ep = a[1] if len(a) > 1 else kw.get("endpoint", "")
                for espera in _ESPERAS:
                    try:
                        _anotar_llamada(_m, _ep)
                        return super().request(*a, **kw)
                    except APIError as e:
'''

VIEJO2 = '''                        _dormir(espera)
                return super().request(*a, **kw)   # último intento: si falla, propaga
'''
NUEVO2 = '''                        _dormir(espera)
                _anotar_llamada(_m, _ep)
                return super().request(*a, **kw)   # último intento: si falla, propaga
'''

ANCLA_FN = "def _http_client_cls():"
HELPER = '''def _anotar_llamada(method, endpoint):
    """Apunta la llamada en el contador de cuota (v482). NUNCA puede propagar:
    un medidor que tumba una lectura es peor que no tener medidor."""
    try:
        from core import metrics
        metrics.anota(method, endpoint)
    except Exception:                       # noqa: BLE001
        pass


'''

for etq, a in (("clase", VIEJO), ("ultimo intento", VIEJO2), ("def", ANCLA_FN)):
    if s.count(a) != 1:
        raise SystemExit("timeclock: ancla %s no unica (%d)" % (etq, s.count(a)))
s = s.replace(VIEJO, NUEVO).replace(VIEJO2, NUEVO2).replace(ANCLA_FN, HELPER + ANCLA_FN)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("timeclock.py: cada intento HTTP queda apuntado")

# ── 2 · la sub-seccion del propietario ───────────────────────────────────────
P2 = "C:\\Users\\diego\\P1\\survey_app\\core\\home_ui.py"
s2 = io.open(P2, encoding="utf-8").read()
V2 = '''        ("📚 Manuales",  ":material/menu_book: Manuals")]),
'''
N2 = '''        ("📚 Manuales",  ":material/menu_book: Manuals"),
        # v482 · al FINAL, para no reordenarle el menú a quien ya lo usa (v297).
        ("📈 Cuota",     ":material/speed: API quota")]),
'''
if s2.count(V2) != 1:
    raise SystemExit("home_ui: ancla no unica (%d)" % s2.count(V2))
s2 = s2.replace(V2, N2)
ast.parse(s2)
io.open(P2, "w", encoding="utf-8", newline="").write(s2)
print("home_ui.py: sub-seccion 📈 Cuota, la ultima")

# ── 3 · el despacho y la pantalla ────────────────────────────────────────────
P3 = "C:\\Users\\diego\\P1\\survey_app\\core\\auth_ui.py"
s3 = io.open(P3, encoding="utf-8").read()
V3 = '''    elif sec == "🚆 Rieles":
        _owner_rieles()
    else:
        _owner_manuales()
'''
N3 = '''    elif sec == "🚆 Rieles":
        _owner_rieles()
    elif sec == "📈 Cuota":
        _owner_cuota()
    else:
        _owner_manuales()


def _owner_cuota():
    """Consumo real de la API de Google, medido (v482).

    ⚠️ Responde la pregunta que decide la fase 5 de la ruta: ¿aprieta la cuota de
    verdad? Hasta ahora se habría contestado por intuición. El contador vive en
    memoria del proceso (`core/metrics.py`) y **no cuesta ni una llamada**.
    """
    from core import metrics, theme as _T
    st.markdown(t("### :material/speed: Google API quota"))
    st.caption(t("Measured in this process. The ceiling is **60 reads and 60 writes per minute** for the whole app, because there is a single service account. Restarting the app resets the counter."))

    r = metrics.resumen()
    if not r["total"]:
        st.info(t("No calls recorded yet in this process. Move around the app and come back."))
        return

    _pl, _pe = r["pico"]["lectura"], r["pico"]["escritura"]
    _al, _ae = r["ahora"]["lectura"], r["ahora"]["escritura"]

    def _color(n):
        return _T.ROJO if n >= 54 else (_T.AMBAR if n >= 36 else _T.VERDE)

    _T.kpi_row([
        (t("Reads · last minute"), str(_al), t("of 60"), _color(_al)),
        (t("Writes · last minute"), str(_ae), t("of 60"), _color(_ae)),
        (t("Peak reads in one minute"), str(_pl), t("worst minute seen"), _color(_pl)),
        (t("Peak writes in one minute"), str(_pe), t("worst minute seen"), _color(_pe)),
    ])

    _mins = r["minutos_vivo"]
    st.caption(f"{r['total']} {t('calls in')} {_mins:.0f} {t('min')} "
               f"({(r['total'] / _mins if _mins else 0):.1f} {t('per minute on average')})"
               + (f" · ⚠️ {t('history truncated: only the most recent calls are kept')}"
                  if r["truncado"] else ""))

    # ⚠️ El veredicto se dice en palabras, no solo en números: el pico es lo que
    # decide, no la media — la media siempre sale tranquilizadora.
    _peor = max(_pl, _pe)
    if _peor >= 54:
        st.error(t("The worst minute seen used {n} of the 60 available. The ceiling is real: more service accounts or a different data layer.").replace("{n}", str(_peor)))
    elif _peor >= 36:
        st.warning(t("The worst minute seen used {n} of 60. There is room, but a second active client could reach the ceiling.").replace("{n}", str(_peor)))
    else:
        st.success(t("The worst minute seen used {n} of 60. The ceiling is not the constraint today.").replace("{n}", str(_peor)))

    # Reparto por libro: dice si el consumo es de un cliente o de todos.
    if r["por_libro"]:
        _nom = {}
        try:
            for g in auth.list_groups():
                _sid = str(g.get("SheetID", "") or "").strip()
                if _sid:
                    _nom[_sid] = str(g.get("Group", ""))
        except Exception:
            pass
        _filas = [{
            t("Book"): _nom.get(k, t("master") if k not in _nom else k),
            t("Reads"): v["lectura"], t("Writes"): v["escritura"],
            t("Total"): v["lectura"] + v["escritura"],
        } for k, v in sorted(r["por_libro"].items(),
                             key=lambda kv: -(kv[1]["lectura"] + kv[1]["escritura"]))]
        st.markdown(t("**By book**"))
        st.dataframe(pd.DataFrame(_filas), hide_index=True, width="stretch",
                     column_config=tabla.cfg())

    if len(r["por_minuto"]) > 1:
        st.markdown(t("**Calls per minute**"))
        _df = pd.DataFrame([{t("Reads"): l, t("Writes"): e}
                            for _c, l, e in r["por_minuto"]])
        st.line_chart(_df, height=180)

    if st.button(t(":material/restart_alt: Reset the counter"), key="cuota_reset"):
        metrics.reiniciar()
        flash.exito(t("Counter reset."))
        st.rerun()
'''
if s3.count(V3) != 1:
    raise SystemExit("auth_ui: ancla no unica (%d)" % s3.count(V3))
s3 = s3.replace(V3, N3)
ast.parse(s3)
io.open(P3, "w", encoding="utf-8", newline="").write(s3)
print("auth_ui.py: pantalla de cuota + despacho explicito")
