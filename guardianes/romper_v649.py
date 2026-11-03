# -*- coding: utf-8 -*-
"""Batería de roturas de v649. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v649"
TOPE_S = 180
PA = "core/parte_agente.py"
DU = "core/daily_log_ui.py"
RD = "core/resumen_dia.py"
REN = "core/resumen_envio.py"
HJ = "core/hojas.py"

ROTURAS = [
    # ── El agente ──
    ("⚠️ sin la regla de las varias partes", PA, [("""- An activity whose NAME joins two or more parts ("buffers (car + CW)", "LH and RH") is done \\\n""",
                                                  """- An activity is done \\\n""")]),
    ("la regla sin ceñir (pregunta de más)", PA, [("""("Is the car buffer done too?"). This is only about the parts the \\\nname lists: "finished the rails" still finishes a rails activity.""",
                                                  """("Is the car buffer done too?").""")]),
    ("⚠️ PROMPT_V sin subir (los partes sin revisar no se releen)", PA, [("""PROMPT_V = 3\n""", """PROMPT_V = 2\n""")]),
    ("la clase «question» no lo incluye", PA, [("""not decide, or that covers only part of one activity (see below). `codes` = the candidates; \\\n""",
                                               """not decide. `codes` = the candidates; \\\n""")]),
    # ── La tarjeta ──
    ("⚠️ una opción, como si fueran varias", DU, [("""x=q["termino"]) if len(q["opciones"]) == 1\n""", """x=q["termino"]) if False\n""")]),
    ("⚠️ la oficina, con «Activities your log mentions»", DU, [("""st.markdown(t("**Activities this log mentions**") if oficina else""",
                                                               """st.markdown(t("**Activities your log mentions**") if oficina else""")]),
    ("la oficina, con «Pending in your log»", DU, [("""t(":material/pending: Pending in this log — not credited ({n})", n=len(p["pendientes"]))""",
                                                    """t(":material/pending: Pending in your log — not credited ({n})", n=len(p["pendientes"]))""")]),
    ("la oficina, con «Your log names»", DU, [("""t(":material/checklist: This log names «{e}» — which of these were finished?", e=e["termino"])""",
                                               """t(":material/checklist: Your log names «{e}» — which of these were finished?", e=e["termino"])""")]),
    ("el aviso de «Issues/Pending», con «your log» para la oficina", DU, [("""_extra.append(t(((oficina and _AVISO_OFICINA.get(item["aviso"])) or _AVISO[item["aviso"]])))""",
                                                                         """_extra.append(t(_AVISO[item["aviso"]]))""")]),
    ("⚠️ la tarjeta no pasa `oficina` a lo que pinta", DU, [("""todo=(lid, str(d)), oficina=oficina)""", """todo=(lid, str(d)))""")]),
    ("sin nada que acreditar, no pasa `oficina`", DU, [("""_nada_que_confirmar(_prev, oficina)""", """_nada_que_confirmar(_prev)""")]),
    ("sin nada que acreditar, la oficina lee «your log»", DU, [("""t(":material/pending: What this log lists as still to do is not credited ({n}).", n=len(p["pendientes"]))""",
                                                               """t(":material/pending: What your log lists as still to do is not credited ({n}).", n=len(p["pendientes"]))""")]),
    ("⚠️ vuelve «1 activities»", DU, [("""    return t("Credited 1 activity from your log.") if n == 1 else""",
                                       """    return t("Credited {n} activities from your log.", n=n) if n == 1 else""")]),
    ("la oficina no dice de quién era", DU, [("""    if de:\n        return (t("Credited 1 activity from {who}'s log""", """    if False:\n        return (t("Credited 1 activity from {who}'s log""")]),
    ("⚠️ al confirmar, sin el autor", DU, [("""_acreditadas(n, _nombre(_autor) if oficina else "")""", """_acreditadas(n)""")]),
    ("el estado de la revisión, con «1 activities»", DU, [("""q=_q2) if n == 1\n""", """q=_q2) if n == 0\n""")]),
    # ── Un resumen al día, también entre procesos ──
    ("⚠️ fuera del lote de lectura", HJ, [("""    "DailyBriefs",\n""", "")]),
    ("⚠️ el lector crea la hoja", RD, [("""for r in (hojas.registros(SHEET) or [])""", """for r in (hojas.registros(SHEET, HEADERS) or [])""")]),
    ("⚠️ no mira la hoja (se paga dos veces)", RD, [("""    if not rehacer:\n        _h = _de_la_hoja(grupo, idioma)\n""", """    if False:\n        _h = _de_la_hoja(grupo, idioma)\n""")]),
    ("⚠️ no la deja en la hoja", RD, [("""            _a_la_hoja(grupo, idioma, res)\n""", "")]),
    ("⚠️ «Refresh» devuelve el de la hoja", RD, [("""    if not rehacer:\n        _h = _de_la_hoja""", """    if True:\n        _h = _de_la_hoja""")]),
    ("⚠️ vale el de otra empresa", RD, [("""                 if str(r.get("Group", "")).strip().lower() == str(grupo).strip().lower()\n                 and str(r.get("Date", ""))""",
                                         """                 if str(r.get("Date", ""))""")]),
    ("⚠️ vale el de ayer", RD, [("""and str(r.get("Date", "")).strip() == _hoy and """, """and """)]),
    ("vale el de otro idioma", RD, [(""" and str(r.get("Language", "")).strip() == str(idioma)]""", """]""")]),
    ("⚠️ manda el PRIMERO del día (no el de «Refresh»)", RD, [("""d = json.loads(filas[-1].get("Brief") or "")""", """d = json.loads(filas[0].get("Brief") or "")""")]),
    ("un destino inventado pasa", RD, [(""""ir": p.get("ir") if p.get("ir") in DESTINOS else "none",""", """"ir": p.get("ir"),""")]),
    ("la obra se cuela en otro destino", RD, [(""""obra": str(p.get("obra", "")) if p.get("ir") == "project" else ""}""", """"obra": str(p.get("obra", ""))}""")]),
    ("sin tope de puntos", RD, [(""""puntos": puntos[:MAX_PUNTOS], "hora\"""", """"puntos": puntos, "hora\"""")]),
    ("puntos vacíos", RD, [(""" and str(p.get("texto", "")).strip()]""", """]""")]),
    ("un JSON roto tumba Home", RD, [("""    except Exception as e:\n        logger.warning("resumen_dia._de_la_hoja""", """    except ZeroDivisionError as e:\n        logger.warning("resumen_dia._de_la_hoja""")]),
    ("si la hoja falla, no hay resumen", RD, [("""    except Exception as e:\n        logger.warning("resumen_dia._a_la_hoja""", """    except ZeroDivisionError as e:\n        logger.warning("resumen_dia._a_la_hoja""")]),
    ("⚠️ el envío vuelve a pagar el suyo", REN, [("""        res, _mot = RD.del_dia(grupo, gente[0][1].get("User", ""), idi)""",
                                                 """        res, _mot = RD.generar(grupo, gente[0][1].get("User", ""), idi)""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RD,
           [("# v649 · El de cada día, en el libro de la empresa", "# (control) v649 · El de cada día, en el libro de la empresa")])


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
