# -*- coding: utf-8 -*-
"""Batería de roturas de v678. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v678"
TOPE_S = 500
RO = "core/roster.py"
RU = "core/roster_ui.py"
CT = "core/chat_tools.py"
CA = "core/chat_agent.py"
RT = "core/route_ui.py"

ROTURAS = [
    # ── H10 · el motor ──
    ("⚠️ H10 · se puede cambiar el pasado", RO,
     [("    if d0 < hoy:\n        return False, t(\"Only from today on", "    if False:\n        return False, t(\"Only from today on")]),
    ("⚠️ H10 · una ausencia del tablero se toca", RO,
     [("        if any(i[\"asig\"] in ESTADOS for i in c[\"items\"]):\n            if any(",
       "        if False:\n            if any(")]),
    ("H10 · sin tope de días", RO,
     [("    if (d1 - d0).days >= MAX_DIAS_CAMBIO:", "    if False:")]),
    ("H10 · la misma obra de origen y destino", RO,
     [("    if a_pid and a_pid == pid:\n", "    if False:\n")]),
    ("H10 · mover pierde la franja", RO,
     [("            nuevos += [{\"asig\": a_pid, \"ini\": i[\"ini\"], \"fin\": i[\"fin\"]} for i in tocar[:1]]",
       "            nuevos += [{\"asig\": a_pid, \"ini\": \"\", \"fin\": \"\"} for i in tocar[:1]]")]),
    ("H10 · mover duplica la obra que ya estaba", RO,
     [("        if a_pid and a_pid not in [_de(i[\"asig\"]) for i in resto]:", "        if a_pid:")]),
    ("H10 · el filtro por obra no filtra (quita todo)", RO,
     [("        tocar = [i for i in c[\"items\"] if (not pid or _de(i[\"asig\"]) == pid)]",
       "        tocar = list(c[\"items\"])")]),
    ("⚠️ H10 · la vista de la tarjeta ESCRIBE", RO,
     [("    if aplicar:\n        for lunes, celdas in semanas.items():", "    if True:\n        for lunes, celdas in semanas.items():")]),
    ("H10 · con `aplicar` no escribe", RO,
     [("            ok, msg = guardar_persona(grupo, lunes, usuario, celdas)\n            if not ok:\n                return False, msg\n    return True, cambios",
       "            ok, msg = True, \"\"\n            if not ok:\n                return False, msg\n    return True, cambios")]),
    # ── H10 · el asistente ──
    ("⚠️ H10 · la oficina no tiene la herramienta", CT,
     [("    # v678 · H10 del ciclo 3\n    {\"name\": \"prepare_board_change\"", "    # v678 · H10 del ciclo 3\n    {\"name\": \"prepare_board_change_x\"")]),
    ("⚠️ H10 · Confirm no hace nada (sin el tipo de tarjeta)", CT,
     [("                      \"tablero\": _confirmar_cambio_tablero}          # v678 · H10", "                      }")]),
    ("H10 · mover a una obra terminada", CT,
     [("    if dest and (P.es_completada(dest) or str(dest.get(\"Status\", \"\")) in (\"Cancelled\", \"On hold\", \"Archived\")):\n        raise _Negado(",
       "    if False:\n        raise _Negado(")]),
    ("H10 · la tarjeta no avisa de los certificados", CT,
     [("        if _req and not CR.compliance(u, _req).get(\"cumple\"):", "        if False:")]),
    ("H10 · sin nada que cambiar, deja una tarjeta vacía", CT,
     [("    if not hechos:\n        raise _Negado(f\"Nothing on {quien}'s board", "    if False:\n        raise _Negado(f\"Nothing on {quien}'s board")]),
    ("H10 · al confirmar no vuelve a mirar el tablero (escribe lo que no hay)", CT,
     [("    ok, res = R.cambiar_dias(ctx[\"grupo\"], u, d.get(\"from\"), d.get(\"to\"), pid, a_pid, aplicar=True)",
       "    ok, res = R.cambiar_dias(ctx[\"grupo\"], u, d.get(\"from\"), d.get(\"to\"), pid, a_pid, aplicar=False)")]),
    ("H10 · al moverla no la asigna a la obra nueva", CT,
     [("            P.add_field_user(a_pid, u)\n        except Exception as e:\n            logger.warning(\"chat_tools: asignar al mover",
       "            pass\n        except Exception as e:\n            logger.warning(\"chat_tools: asignar al mover")]),
    ("H10 · el asistente no sabe que puede", CA,
     [("alguien a una obra, mover o quitar días del tablero de alguien y mandar", "alguien a una obra y mandar")]),
    # ── H14 ──
    ("⚠️ H14 · el campo no tiene su plan de otro día", CT,
     [("    {\"name\": \"get_my_plan\", \"fn\": _mi_plan,", "    {\"name\": \"get_my_plan_x\", \"fn\": _mi_plan,")]),
    ("H14 · sin tope de días", CT,
     [("    d1 = min(d1, d0 + timedelta(days=MAX_DIAS_PLAN - 1))\n", "")]),
    ("⚠️ H14 · mira el tablero de OTRA persona (la que diga el modelo)", CT,
     [("    g, u = ctx[\"grupo\"], ctx[\"usuario\"]\n    d0 = _parse_date((entrada or {}).get(\"date\")) or clock.today(g)",
       "    g, u = ctx[\"grupo\"], str((entrada or {}).get(\"person\") or \"x\")\n    d0 = _parse_date((entrada or {}).get(\"date\")) or clock.today(g)")]),
    ("H14 · la ausencia no se dice", CT,
     [("                                  \"absence_or_day_off\": bool(a.get(\"es_estado\"))} for a in asig]})",
       "                                  } for a in asig]})")]),
    ("H14 · el asistente de campo no sabe que puede", CA,
     [("y solo los suyos: su día, su plan de otros días, sus obras", "y solo los suyos: su día, sus obras")]),
    # ── H16 ──
    ("⚠️ H16 · la tarjeta de aprobar no dice quién puede cubrirla", CT,
     [("            lineas += _quien_cubre(g, usuario, _chq)       # v678 · H16 del ciclo 3\n", "")]),
    ("H16 · «quién cubre» sin mirar los certificados", CT,
     [("        _ok = [x[\"nombre\"] for x in subs if x[\"cumple\"]][:4]\n        _no = [x[\"nombre\"] for x in subs if not x[\"cumple\"]][:3]\n        _q = (",
       "        _ok = [x[\"nombre\"] for x in subs][:4]\n        _no = [x[\"nombre\"] for x in subs if not x[\"cumple\"]][:3]\n        _q = (")]),
    ("H16 · si no se puede leer quién está libre, la tarjeta no sale", CT,
     [("        except Exception as e:\n            logger.warning(\"chat_tools._quien_cubre: %r\", e)\n            return out",
       "        except ZeroDivisionError as e:\n            logger.warning(\"chat_tools._quien_cubre: %r\", e)\n            return out")]),
    # ── H6 ──
    ("⚠️ H6 · Assign vuelve a un solo día", RU,
     [("        _dsel_l = (list(dias) if _toda else", "        _dsel_l = (list(dias)[:1] if _toda else")]),
    ("H6 · libre = libre solo el primer día", RU,
     [("            _dias_choque = [d for d in _dsel_l\n", "            _dias_choque = [d for d in _dsel_l[:1]\n")]),
    ("⚠️ H6 · asignar varios días pisa una ausencia", RU,
     [("        if any(it[\"asig\"] in R.ESTADOS for it in cur[\"items\"]):\n            continue\n        if str(pid) not in",
       "        if False:\n            continue\n        if str(pid) not in")]),
    ("H6 · asignar varios días pisa la otra obra del día", RU,
     [("        if str(pid) not in [it[\"asig\"] for it in cur[\"items\"]]:\n            cur[\"items\"].append({\"asig\": str(pid), \"ini\": ini, \"fin\": fin})\n        sem[dia] = {\"items\": [{\"a\": it[\"asig\"], \"i\": it[\"ini\"], \"f\": it[\"fin\"]} for it in cur[\"items\"]],\n                    \"nota\": cur[\"nota\"]}\n    return R.guardar_persona",
       "        cur[\"items\"] = [{\"asig\": str(pid), \"ini\": ini, \"fin\": fin}]\n        sem[dia] = {\"items\": [{\"a\": it[\"asig\"], \"i\": it[\"ini\"], \"f\": it[\"fin\"]} for it in cur[\"items\"]],\n                    \"nota\": cur[\"nota\"]}\n    return R.guardar_persona")]),
    ("H6 · el aviso vuelve a no decir a quién", RU,
     [("                    flash.exito(t(\"{who} → «{p}» on {d}, {a}–{b}.\", who=\", \".join(_hechos), p=_nom_prj, d=_cuando,",
       "                    flash.exito(t(\"{who} → «{p}» on {d}, {a}–{b}.\", who=str(len(_hechos)), p=_nom_prj, d=_cuando,")]),
    ("H6 · los ocupados sin su día", RU,
     [("_esc(\", \".join(f[\"nom\"] + (f\" ({f['dias']})\" if len(_dsel_l) > 1 else \"\") for f in ocupados)))",
       "_esc(\", \".join(f[\"nom\"] for f in ocupados)))")]),
    ("H6 · el día por defecto ya no es hoy", RU,
     [("default=[dias[_idx_hoy(lunes, dias)]], key=\"ai_dias\"", "default=[dias[0]], key=\"ai_dias\"")]),
    # ── H13 ──
    ("⚠️ H13 · «My route» vuelve a todas las asignadas", RT,
     [("        if _todas:\n            proys = [p for p in P.list_projects_for_field(usuario, grupo=grupo)",
       "        if True:\n            proys = [p for p in P.list_projects_for_field(usuario, grupo=grupo)")]),
    ("H13 · se cuela una obra de otra empresa", RT,
     [("        if p and str(p.get(\"Group\", \"\")) == str(grupo):", "        if p:")]),
    ("H13 · un día sin nada no lo dice", RT,
     [("            st.info(t(\":material/event_busy: Nothing is planned for you on {d}.", "            st.caption(t(\":material/event_busy: Nothing is planned for you on {d}.")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RO,
           [("MAX_DIAS_CAMBIO = 31     # v678", "MAX_DIAS_CAMBIO = 31     # (control) v678")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
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
