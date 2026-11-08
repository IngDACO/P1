# -*- coding: utf-8 -*-
"""Batería de roturas de v652. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v652"
TOPE_S = 600
IP = "core/interpretation.py"
SU = "core/survey_ui.py"

ROTURAS = [
    # ── E · la llamada ──
    ("⚠️ vuelve Haiku", IP, [("""MODEL = "claude-sonnet-5-5"\n""", """MODEL = "claude-haiku-4-5"\n""")]),
    ("⚠️ bajo AppTest, la clave de verdad", IP, [("""    return AG.clave_api()\n""", """    return "sk-real"\n""")]),
    ("⚠️ se lee por posición (antes viene el razonamiento)", IP, [("""    txt = next((b.text for b in r.content if getattr(b, "type", "") == "text"), "")\n""",
                                                                   """    txt = r.content[0].text\n""")]),
    ("sin esquema", IP, [("""output_config={"effort": ESFUERZO, "format": {"type": "json_schema", "schema": _esquema(claves)}})""",
                          """output_config={"effort": ESFUERZO})""")]),
    ("un rechazo se da por bueno", IP, [("""    if r.stop_reason in ("refusal", "max_tokens"):\n        return None, "the AI stopped (%s)" % r.stop_reason\n""", "")]),
    # ── A · los hechos ──
    ("⚠️ RL positivo, a la DERECHA", IP, [("""    return "left" if rl > 0.05 else "right" if rl < -0.05 else "none"\n""",
                                          """    return "right" if rl > 0.05 else "left" if rl < -0.05 else "none"\n""")]),
    ("⚠️ FB positivo, hacia el FRENTE", IP, [("""    return "rear" if fb > 0.05 else "front" if fb < -0.05 else "none"\n""",
                                             """    return "front" if fb > 0.05 else "rear" if fb < -0.05 else "none"\n""")]),
    ("⚠️ «sigue fuera» lo que la solución no cuenta (OR/OL del Caso 2)", IP, [("""            if int(_num(por_col.get(c))) <= 0:\n                continue\n""",
                                                                              """            if False:\n                continue\n""")]),
    ("lo que sigue fuera, sin sus pisos", IP, [(""""floors": pisos if len(pisos) == int(_num(por_col.get(c))) else None,""", """"floors": None,""")]),
    # ── A · lo que escribe la app ──
    ("⚠️ el cliente no se entera de lo que sigue fuera", IP, [("""    for q in s.get("still_out_of_limit") or []:\n""", """    for q in []:\n""")]),
    ("⚠️ B · los desplazamientos sin la plantilla de plomadas", IP, [("""    out = ["Set out the plumb template and the plumb lines with these shifts from the drawing position:",""",
                                                                      """    out = ["Move the car block with these shifts:",""")]),
    ("⚠️ los cortes, del lado contrario", IP, [("""            partes.append("%.1f mm on the left side" % c["cut_left_side_of_opening_mm"])\n""",
                                               """            partes.append("%.1f mm on the right side" % c["cut_left_side_of_opening_mm"])\n""")]),
    # ── A · `revisar` ──
    ("⚠️ no mira las cifras", IP, [("""            if any(abs(v - a) < 0.051 for a in permitidos) or (v == int(v) and v <= tope_entero):\n""",
                                    """            if True:\n""")]),
    ("⚠️ no mira los sentidos", IP, [("""            if sentido != esperado[eje]:\n""", """            if False:\n""")]),
    ("⚠️ «todo resuelto» pasa", IP, [("""        if queda:\n            for m in _TODO_RESUELTO.finditer(txt):\n""",
                                     """        if False:\n            for m in _TODO_RESUELTO.finditer(txt):\n""")]),
    ("⚠️ B · mover una cabina instalada pasa", IP, [("""        for m in _PROCEDIMIENTO.finditer(txt):\n""", """        for m in []:\n""")]),
    ("«shift right» no se ve", IP, [("""(left|right|back|rear|front)\\b", re.I)""", """(zzleft)\\b", re.I)""")]),
    ("«to the left wall» se toma por un sentido", IP, [("""(?!\\s*(?:-\\s*)?(?:wall|side|hand|jamb|of\\b))""", "")]),
    # ── A · un intento más; si no, no se publica ──
    ("⚠️ sin segundo intento", IP, [("""    if probs:\n        data2, _m2 = _llamar(""", """    if False:\n        data2, _m2 = _llamar(""")]),
    ("⚠️ (interno) lo que no casa se publica igual", IP, [("""            out[key] = NO_INCLUIDO if (v and key in probs) else v\n""", """            out[key] = v\n""")]),
    ("⚠️ (cliente) lo que no casa se publica igual", IP, [("""            if key in probs:\n                out["_avisos"].append(""",
                                                          """            if False:\n                out["_avisos"].append(""")]),
    ("«evasion_pared» aunque no haya empuje extra", IP, [("""            if key == "evasion_pared" and not""", """            if False and key == "evasion_pared" and not""")]),
    ("⚠️ al modelo se le piden también desplazamientos y cortes", IP, [("""_DEL_MODELO_CLIENTE = ("resumen", "implementacion", "verificacion")\n""",
                                                                        """_DEL_MODELO_CLIENTE = ("resumen", "desplazamientos", "cortes", "implementacion", "verificacion")\n""")]),
    ("⚠️ sin respuesta, el informe del cliente se bloquea", IP, [("""        if data is None:\n            out["_avisos"].append(""",
                                                                 """        if data is None:\n            return _user_fallback(mot)\n            out["_avisos"].append(""")]),
    ("sin clave, el informe del cliente se bloquea", IP, [("""        if not k:\n            out["_avisos"].append(""",
                                                          """        if not k:\n            return _user_fallback("no key")\n            out["_avisos"].append(""")]),
    ("⚠️ el del cliente no sabe de qué solución es", IP, [(""""_ok": True, "_error": None, "_avisos": [], "_sol": solucion_de(calc_results), "_modelo": MODEL}""",
                                                          """"_ok": True, "_error": None, "_avisos": [], "_modelo": MODEL}""")]),
    ("B · las instrucciones vuelven a dejar mover la cabina", IP, [("""Never describe moving an installed car, releasing rail brackets or jacking anything.""",
                                                                    """Be practical.""")]),
    # ── C/D · en el Survey ──
    ("⚠️ elegir otra solución no reescribe el texto", SU, [("""                if _ia_vieja(r):\n                    with st.spinner(""",
                                                           """                if False:\n                    with st.spinner(""")]),
    ("⚠️ nunca se sabe si el texto es de otra solución", SU, [("""    return "_sol" in iu and iu.get("_sol") != solucion_de(_calc_ia(r))\n""", """    return False\n""")]),
    ("⚠️ al reescribir, las cajas son las mismas (el navegador no suelta lo viejo)", SU, [("""    r["_iu_v"] = int(r.get("_iu_v", 0) or 0) + 1\n""", """    pass\n""")]),
    ("⚠️ el PDF, sin lo que dejó la oficina", SU, [("""interpretation_user = _iu_final(r),       # v652 · D: lo que dejó la oficina""",
                                                   """interpretation_user = r.get("interpretation_user"),""")]),
    ("⚠️ sin «Rewrite the interpretation»", SU, [("""                if st.button(t(":material/refresh: Rewrite the interpretation"), key="sv_reescribir_ia",""",
                                                  """                if False and st.button(t(":material/refresh: Rewrite the interpretation"), key="sv_reescribir_ia",""")]),
    ("⚠️ guardar sin reescribir (lo del campo, de otra solución)", SU, [("""                        if _ia_vieja(r):\n""", """                        if False:\n""")]),
    ("⚠️ a la obra, el texto sin revisar", SU, [(""""user":  _iu_final(r)}))""", """"user":  r.get("interpretation_user")}))""")]),
    ("la IA, sin la matriz ajustada", SU, [("""            "survey_adj":       survey_adj_df,      # v652 · los pisos fuera de límite ANTES de desplazar\n""", "")]),
    ("los avisos del asistente, sin enseñar", SU, [("""                    for _av in interp_usr.get("_avisos") or []:\n""", """                    for _av in []:\n""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", IP,
           [("# lo que el modelo suele calcular por su cuenta", "# (control) lo que el modelo suele calcular por su cuenta")])


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
