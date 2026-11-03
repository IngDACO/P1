# -*- coding: utf-8 -*-
"""Batería de roturas de v648. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v648"
TOPE_S = 180
RE = "core/resumen_envio.py"
PU = "core/projects_ui.py"
HJ = "core/hojas.py"
SM = "resumen_manana.py"
WF = "../.github/workflows/resumen_manana.yml"

ROTURAS = [
    # ── La hoja ──
    ("⚠️ fuera del lote de lectura", HJ, [("""    "DailySummary",\n""", "")]),
    ("⚠️ el lector de Home la crea", RE, [("""    return hojas.registros(SHEET) or []\n""", """    return hojas.registros(SHEET, HEADERS) or []\n""")]),
    # ── Pedirlo y dejarlo ──
    ("⚠️ se decide dónde escribir con la caché", RE, [("""        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))\n        ahora = clock.now(grupo).strftime""",
                                                         """        recs = list(_records())\n        ahora = clock.now(grupo).strftime""")]),
    ("⚠️ una fila nueva cada vez (se duplica)", RE, [("""        fila = next((i + 2 for i, r in enumerate(recs) if _es(r, grupo, usuario)), None)\n""", """        fila = None\n""")]),
    ("la persona, distinguiendo mayúsculas", RE, [("""            and str(r.get("User", "")).strip().lower() == str(usuario or "").strip().lower())""",
                                                   """            and str(r.get("User", "")).strip() == str(usuario or "").strip())""")]),
    ("⚠️ quitarlo no lo quita", RE, [(""""Active": SI if si else "NO",""", """"Active": SI,""")]),
    ("«desde» no se renueva al volver", RE, [("""            if si and not _activa(recs[fila - 2]):\n                _c["Since"] = ahora\n""", "")]),
    ("⚠️ sin usuario, escribe", RE, [("""    if not str(usuario or "").strip() or not str(grupo or "").strip():\n        return False, t("Sign in again to change this.")\n""", "")]),
    ("un idioma raro pasa", RE, [("""    idioma = idioma if idioma in IDIOMAS else IDIOMAS[0]\n""", "")]),
    # ── Cuándo ──
    ("⚠️ fuera de hora también manda", RE, [("""    if not ignorar_hora and not toca(ahora):\n""", """    if False:\n""")]),
    ("hasta las 12", RE, [("""HORA_DESDE, HORA_HASTA = 7, 11 """, """HORA_DESDE, HORA_HASTA = 7, 12 """)]),
    ("las 11 aún cuentan", RE, [("""    return HORA_DESDE <= ahora.hour < HORA_HASTA\n""", """    return HORA_DESDE <= ahora.hour <= HORA_HASTA\n""")]),
    ("⚠️ dos veces el mismo día", RE, [("""        if str(r.get("LastSent", "")).strip()[:10] == hoy:\n""", """        if False:\n""")]),
    # ── A quién ──
    ("⚠️ también a quien no es administrador", RE, [("""            if str(u.get("Role", "")).strip().lower() == "administrator"\n""", """            if True\n""")]),
    ("⚠️ también a un administrador dado de baja", RE, [("""\n            and str(u.get("Active", "SI")).strip().upper() in auth._ACTIVE_OK}""", """}""")]),
    ("⚠️ sin comprobar a nadie", RE, [("""        elif str(r.get("User", "")).strip().lower() not in adm:\n""", """        elif False:\n""")]),
    ("⚠️ las filas de otra empresa", RE, [("""             if str(r.get("Group", "")).strip().lower() == str(grupo).strip().lower() and _activa(r)]\n""",
                                          """             if _activa(r)]\n""")]),
    ("⚠️ también a quien lo quitó", RE, [("""             if str(r.get("Group", "")).strip().lower() == str(grupo).strip().lower() and _activa(r)]\n""",
                                         """             if str(r.get("Group", "")).strip().lower() == str(grupo).strip().lower()]\n""")]),
    # ── Qué y cómo ──
    ("⚠️ una llamada al modelo por persona", RE, [("""            por_idioma.setdefault(_i if _i in IDIOMAS else IDIOMAS[0], []).append((n, r))\n""",
                                                  """            por_idioma.setdefault(n, []).append((n, r))\n""")]),
    ("todos en inglés", RE, [("""        res, _mot = RD.del_dia(grupo, gente[0][1].get("User", ""), idi)""", """        res, _mot = RD.del_dia(grupo, gente[0][1].get("User", ""), "en")""")]),
    ("⚠️ se marca a quien no le llegó", RE, [("""            if rr.get("email") or rr.get("telegram"):\n""", """            if True:\n""")]),
    ("⚠️ se marca en otra columna", RE, [("""_col_letter(_COL["LastSent"]), n)""", """_col_letter(_COL["Since"]), n)""")]),
    ("⚠️ si el modelo falla, se manda igual", RE, [("""        if not res:\n            cuenta["fallos"] += len(gente)\n            continue\n""",
                                                   """        if not res:\n            res = {"titular": "", "puntos": [], "hora": ""}\n""")]),
    ("sin decir por qué le llega", RE, [(""": untick it there to stop.\",""", """.\",""")]),
    ("⚠️ abre (y crea) la hoja en una empresa sin nadie", RE, [("""    recs = hojas.registros(SHEET) or []\n""", """    recs = (hojas.registros(SHEET) or []) if _ws() is not None else []\n""")]),
    ("⚠️ sin el ámbito de la empresa", RE, [("""        with tenant.como_grupo(grupo):\n""", """        with tenant.como_grupo(""):\n""")]),
    ("una empresa que falla tumba las demás", RE, [("""            except Exception as e:\n                logger.warning("resumen_envio.enviar_todo""",
                                                    """            except ZeroDivisionError as e:\n                logger.warning("resumen_envio.enviar_todo""")]),
    # ── El script (registro público) ──
    ("⚠️ el error, con su mensaje", SM, [("""        print("No se pudo enviar: %s" % type(e).__name__)\n""", """        print("No se pudo enviar: %s" % e)\n""")]),
    ("⚠️ los avisos de la app, encendidos", SM, [("""logging.disable(logging.CRITICAL)\n""", "")]),
    ("con fallos sale en verde", SM, [("""    return 1 if (c.get("fallos") or c.get("errores")) else 0\n""", """    return 0\n""")]),
    # ── El trabajo de GitHub ──
    ("⚠️ el secreto, escrito en la orden", WF, [("""printf '%s\\n' "$SECRETS_TOML" > .streamlit/secrets.toml""",
                                                """printf '%s\\n' "${{ secrets.STREAMLIT_SECRETS_TOML }}" > .streamlit/secrets.toml""")]),
    ("⚠️ el secreto se imprime", WF, [("""          printf '%s\\n' "$SECRETS_TOML" > .streamlit/secrets.toml\n""",
                                      """          printf '%s\\n' "$SECRETS_TOML" > .streamlit/secrets.toml\n          cat .streamlit/secrets.toml\n""")]),
    ("⚠️ el fichero del secreto no se borra si algo falla", WF, [("""        if: always()\n""", """        if: success()\n""")]),
    ("⚠️ con pull_request", WF, [("""  workflow_dispatch:\n""", """  pull_request:\n  workflow_dispatch:\n""")]),
    ("⚠️ puede escribir en el repositorio", WF, [("""  contents: read\n""", """  contents: write\n""")]),
    ("dos a la vez", WF, [("""  cancel-in-progress: false\n""", """  cancel-in-progress: true\n""")]),
    ("solo una vez al día, a las 00:17 UTC", WF, [("""    - cron: "17 * * * *"\n""", """    - cron: "17 0 * * *"\n""")]),
    # ── En Home ──
    ("⚠️ el interruptor lo pide para otro", PU, [("""        ok, msg = RE.suscribir(grupo, usuario, idioma, _si)\n""", """        ok, msg = RE.suscribir(grupo, "Admin2x", idioma, _si)\n""")]),
    ("⚠️ si no se pudo, el interruptor se queda como si sí", PU, [("""            st.session_state[_k] = not _si\n""", """            pass\n""")]),
    ("el aviso no sale", PU, [("""        if ok:\n            flash.exito(msg)\n        else:\n            st.session_state[_k] = not _si""",
                               """        if ok:\n            pass\n        else:\n            st.session_state[_k] = not _si""")]),
    ("⚠️ sin avisar de que no le llegará", PU, [("""        if not (str(_r.get("Email", "")).strip() or str(_r.get("TelegramChatID", "")).strip()):\n""", """        if False:\n""")]),
    ("solo con email", PU, [(""" or str(_r.get("TelegramChatID", "")).strip()):\n""", """):\n""")]),
    ("⚠️ Home no lo pinta", PU, [("""    _cada_manana(grupo, _u, _id)\n""", "")]),
    ("⚠️ el interruptor sin clave", PU, [("""                    key=_k, on_change=_cambiar,\n""", """                    on_change=_cambiar,\n""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RE,
           [("# hora LOCAL de la empresa, [7, 11)", "# (control) hora LOCAL de la empresa, [7, 11)")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for a, b in cambios:
        if txt.count(a) != 1:
            return False, bak, p, "ancla x%d: %s" % (txt.count(a), a[:60])
        txt = txt.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if not ok:
            print("  ESCAPA %s (%s)" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
