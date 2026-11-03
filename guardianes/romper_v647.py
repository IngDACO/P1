# -*- coding: utf-8 -*-
"""Batería de roturas de v647. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v647"
TOPE_S = 180
RD = "core/resumen_dia.py"
PU = "core/projects_ui.py"
HU = "core/home_ui.py"

ROTURAS = [
    # ── Los datos ──
    ("⚠️ sin lo que espera a la oficina", RD, [("""                  ("waiting_for_the_office", CT._bandejas), """, """                  """)]),
    ("⚠️ con el rol del campo", RD, [(""""grupo": str(grupo), "rol": "administrator"}""", """"grupo": str(grupo), "rol": "field"}""")]),
    ("⚠️ el error interno llega al modelo", RD, [("""            out[k] = {"error": "could not be read"}\n""", """            out[k] = {"error": str(e)}\n""")]),
    ("⚠️ una consulta que falla lo tumba todo", RD, [("""        except Exception as e:\n            logger.warning("resumen_dia.hechos(%s): %r", k, e)\n""",
                                                      """        except ZeroDivisionError as e:\n            logger.warning("resumen_dia.hechos(%s): %r", k, e)\n""")]),
    ("⚠️ sin el día", RD, [("""    return "Today is %s %d %s (%s). Every date""", """    return "Today: %s %d %s (%s). Every date""")]),
    ("⚠️ siempre en inglés", RD, [(""""Spanish" if idioma == "es" else "English",""", """"English",""")]),
    ("⚠️ sin los datos", RD, [("""json.dumps(hechos(grupo, usuario), ensure_ascii=False, default=str))""", """"{}")""")]),
    # ── La llamada ──
    ("⚠️ vuelve la guía del Survey", RD, [("""            system=_INSTRUCCIONES, messages=""", """            system=_INSTRUCCIONES + __import__("core.chat_agent", fromlist=["x"]).SYSTEM_PROMPT, messages=""")]),
    ("⚠️ vuelve Haiku", RD, [("""MODELO = "claude-sonnet-5-5"\n""", """MODELO = "claude-haiku-4-5"\n""")]),
    ("⚠️ sin esquema", RD, [("""output_config={"effort": ESFUERZO, "format": {"type": "json_schema", "schema": _ESQUEMA}})""", """output_config={"effort": ESFUERZO})""")]),
    ("⚠️ se lee por posición (antes viene el razonamiento)", RD, [("""    _txt = next((b.text for b in r.content if getattr(b, "type", "") == "text"), "")\n""", """    _txt = r.content[0].text\n""")]),
    ("⚠️ un rechazo se da por bueno", RD, [("""    if r.stop_reason in ("refusal", "max_tokens"):\n        return None, str(r.stop_reason)\n""", "")]),
    ("⚠️ bajo AppTest, la clave de verdad", RD, [("""    _k = api_key if api_key is not None else AG.clave_api()""", """    _k = api_key if api_key is not None else "sk-real\"""")]),
    ("⚠️ con más de 7 puntos", RD, [("""MAX_PUNTOS = 7\n""", """MAX_PUNTOS = 9\n""")]),
    ("el dinero, sin el formato de la app", RD, [("""- Money as the app shows it, in either language: a $ and commas for thousands ($70,150.00).\n""", "")]),
    # ── Lo que se acepta ──
    ("⚠️ abre una obra de otra empresa", RD, [("""        if ir == "project" and obra not in obras:\n            ir = "none"\n""", "")]),
    ("⚠️ un destino inventado", RD, [("""        ir = ir if ir in DESTINOS else "none"\n""", "")]),
    ("la obra se cuela en otro destino", RD, [("""        if ir != "project":\n            obra = ""\n""", "")]),
    ("⚠️ sin tope de puntos", RD, [(""""puntos": puntos[:MAX_PUNTOS]}""", """"puntos": puntos}""")]),
    ("puntos vacíos", RD, [("""        if not tx:\n            continue\n""", "")]),
    ("⚠️ un destino apunta a un ID que no existe", RD, [(""""absences": ("planificacion", "🌴 Ausencias")""", """"absences": ("planificacion", "Absences")""")]),
    # ── Una vez al día ──
    ("⚠️ sin el día en la clave (ayer vale hoy)", RD, [("""    return (str(grupo), clock.today(grupo).isoformat(), str(idioma))\n""", """    return (str(grupo), "", str(idioma))\n""")]),
    ("⚠️ sin la empresa en la clave", RD, [("""    return (str(grupo), clock.today(grupo).isoformat(), str(idioma))\n""", """    return ("", clock.today(grupo).isoformat(), str(idioma))\n""")]),
    ("sin el idioma en la clave", RD, [("""    return (str(grupo), clock.today(grupo).isoformat(), str(idioma))\n""", """    return (str(grupo), clock.today(grupo).isoformat(), "")\n""")]),
    ("⚠️ se prepara cada vez", RD, [("""    if not rehacer and k in a["datos"]:\n        return a["datos"][k], ""\n    _f = a["fallos"].get(k)\n""", """    _f = a["fallos"].get(k)\n"""),
                                   ("""        if not rehacer and k in a["datos"]:\n            return a["datos"][k], ""\n        res, mot = generar""", """        res, mot = generar""")]),
    ("lo de otros días se acumula", RD, [("""            for _v in [x for x in a["datos"] if x[1] != k[1]]:      # lo de otros días, fuera: no crece sin fin\n                a["datos"].pop(_v, None)\n""", "")]),
    ("⚠️ un fallo se reintenta en cada recarga", RD, [("""    if not rehacer and _f and time.time() - _f[0] < ESPERA_FALLO:\n        return None, _f[1]\n""", "")]),
    ("⚠️ un fallo no se recuerda", RD, [("""            a["fallos"][k] = (time.time(), mot)\n""", """            pass\n""")]),
    ("sin espera tras un fallo", RD, [("""ESPERA_FALLO = 600 """, """ESPERA_FALLO = 0 """)]),
    ("lo que se manda, sin titular", RD, [("""    return [x for x in [res.get("titular", "")] + ["• " + p["texto"] """, """    return [x for x in ["• " + p["texto"] """)]),
    # ── La pantalla ──
    ("⚠️ «Refresh» no rehace", PU, [("""            RD.del_dia(grupo, _u, _id, rehacer=True)\n""", """            RD.del_dia(grupo, _u, _id)\n""")]),
    ("«Refresh» con los datos de antes", PU, [("""                admin_digest.group_digest.clear()     # los hechos, de ahora\n""", """                pass\n""")]),
    ("⚠️ «Open the job» no abre la obra", PU, [("""                st.session_state["_admin_open_proj"] = p["obra"]\n""", """                pass\n""")]),
    ("otro destino deja abierta una obra de antes", PU, [("""                st.session_state.pop("_admin_open_proj", None)\n            _ir_a(*RD.DESTINOS[p["ir"]])""",
                                                          """                pass\n            _ir_a(*RD.DESTINOS[p["ir"]])""")]),
    ("⚠️ los puntos, sin botón", PU, [("""        if p["ir"] in _ir and c2.button(""", """        if False and c2.button(""")]),
    ("lo urgente no se distingue", PU, [("""(":red[:material/priority_high:] " if p["urgente"] else ":material/arrow_right: ")""", """(":material/arrow_right: ")""")]),
    ("⚠️ el texto del modelo, sin escapar", PU, [("""+ maps.literal_md(p["texto"]))""", """+ p["texto"])""")]),
    ("«Send it to me» sin los puntos", PU, [("""RD.como_texto(res))""", """[res.get("titular", "")])""")]),
    ("⚠️ si falla, ni lo dice", PU, [("""        st.caption(t(":material/info: The assistant could not prepare today's read ({m}). These are the facts:", m=mot or "?"))\n""", """        pass\n""")]),
    ("⚠️ Home no lo rellena", HU, [("""    if _lectura is not None:\n        with _lectura:\n            PU.lectura_ia(grupo)\n""", "")]),
    ("⚠️ Home lo rellena ANTES de lo demás", HU, [("""    _lectura = PU.render_group_header(grupo)\n""", """    _lectura = PU.render_group_header(grupo)\n    if _lectura is not None:\n        with _lectura:\n            PU.lectura_ia(grupo)\n        _lectura = None\n""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RD,
           [("# Adónde lleva cada punto:", "# (control) Adónde lleva cada punto:")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
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
