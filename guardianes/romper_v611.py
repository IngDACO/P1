# -*- coding: utf-8 -*-
"""Bateria de roturas de v611 (el índice que no ve una hoja creada fuera; recuperar lo olvidado;
sin «Select all»; el formulario de la regla vacío). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v611"
HJ = "core/hojas.py"
MEMF = "core/agente_memoria.py"
DLU = "core/daily_log_ui.py"
TOPE_S = 600


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── el índice al día ──
    ("⚠️ el lector sin cabeceras no rehace el índice (la memoria, vacía para siempre)", HJ,
     [('    if datos is None and cabeceras is None and _aparecio(sid, titulo):\n'
       '        datos = _lote(sid).get(titulo)\n', '')]),
    ("sin tope: se rehace el índice en CADA lectura que falta", HJ,
     [('    if _ult is not None and ahora - _ult < _REFRESCO_S:\n        return False\n', '')]),
    ("el tope a cero", HJ,
     [('_REFRESCO_S = 600\n', '_REFRESCO_S = 0\n')]),
    ("⚠️ se rehace el índice de TODOS los libros (los demás clientes pagan la lectura)", HJ,
     [('        timeclock._libro.clear(sheet_id)\n        return True\n',
       '        timeclock._libro.clear()\n        return True\n')]),
    ("se tira el lote de TODOS los libros", HJ,
     [('        _lote.clear(sheet_id)\n    except Exception:\n',
       '        _lote.clear()\n    except Exception:\n')]),
    ("⚠️ el respaldo de tirar el lote, sin proteger (la LECTURA revienta: lo cazó verif_v590)", HJ,
     [('lo cazó verif_v590 en la suite de v611).\n'
       '        try:\n            _lote.clear()\n        except Exception:\n            pass\n',
       'lo cazó verif_v590 en la suite de v611).\n        _lote.clear()\n')]),
    ("se tira el lote aunque la hoja siga sin existir (una lectura tirada)", HJ,
     [('    if timeclock.titulo_real(titulo, sheet_id).strip().lower() not in _existentes(sheet_id):\n'
       '        return False\n', '')]),
    ("también para hojas fuera del lote", HJ,
     [('    if titulo not in HOJAS_LECTURA or not _indice_al_dia(sheet_id):\n',
       '    if not _indice_al_dia(sheet_id):\n')]),
    ("un solo tope para todos los libros", HJ,
     [('    _ult = _refrescado.get(sheet_id)\n', '    _ult = _refrescado.get("")\n'),
      ('    _refrescado[sheet_id] = ahora\n', '    _refrescado[""] = ahora\n')]),
    ("si rehacer el índice falla, la lectura revienta", HJ,
     [('    try:\n        timeclock._libro.clear(sheet_id)\n        return True\n'
       '    except Exception as e:\n'
       '        logger.warning("hojas: no se pudo refrescar el índice de %s: %s", sheet_id, e)\n'
       '        return False\n',
       '    timeclock._libro.clear(sheet_id)\n    return True\n')]),
    ("⚠️ `ids_referenciados` con el índice viejo (un ID referenciado fuera se reutilizaría)", HJ,
     [('        _indice_al_dia(sheet_id)\n', '')]),
    # ── la memoria ──
    ("⚠️ un admin recupera lo de otro grupo", MEMF,
     [('        if not (es_propietario or str(r.get("Group", "")) == str(grupo)):\n', '        if False:\n')]),
    ("⚠️ recuperar DUPLICA una lección que se volvió a aprender", MEMF,
     [('        if k in vivas:\n            rep += 1\n            continue\n', '')]),
    ("dos olvidadas iguales vuelven las dos", MEMF,
     [('        vivas.add(k)\n', '')]),
    ("recuperar sin la hora en `Updated`", MEMF,
     [('"values": [[""]]},\n                 {"range": "%s%d" % (_col_letter(_COL["Updated"]), i + 2), '
       '"values": [[ahora]]}]\n', '"values": [[""]]}]\n')]),
    ("`olvidadas` le enseña al admin lo de otro grupo", MEMF,
     [('        if grupo is not None and str(r.get("Group", "")) != str(grupo):\n', '        if False:\n')]),
    ("`olvidadas` le enseña al admin las reglas del propietario (que no puede recuperar)", MEMF,
     [('        if grupo is not None and str(r.get("Group", "")) != str(grupo):\n',
       '        if grupo is not None and str(r.get("Group", "")) not in (str(grupo), ""):\n')]),
    ("olvidar sin anotar CUÁNDO", MEMF,
     [('        lote.append({"range": "%s%d" % (_col_letter(_COL["Updated"]), i + 2), "values": [[_ahora()]]})\n', '')]),
    ("olvidar cuenta celdas, no filas", MEMF,
     [('    return True, len(lote) // 2\n', '    return True, len(lote)\n')]),
    # ── la pantalla ──
    ("⚠️ vuelve «Select all» al olvidar", DLU,
     [('select_all=False)\n                st.button(t(":material/delete:',
       ')\n                st.button(t(":material/delete:')]),
    ("«Select all» en «Restore these»", DLU,
     [('select_all=False)\n            st.button(t(":material/undo:',
       ')\n            st.button(t(":material/undo:')]),
    ("⚠️ el panel le ofrece al admin recuperar lo de otros grupos", DLU,
     [('        _olv = MEM.olvidadas(None if _dueno else grupo)\n', '        _olv = MEM.olvidadas(None)\n')]),
    ("«Restore» sin elegir nada llama igual", DLU,
     [('            if not list(pet.get("ids") or []):\n', '            if False:\n')]),
    ("⚠️ recuperar como propietario aunque sea un admin", DLU,
     [('            ok, n, rep = MEM.restaurar(pet["ids"], grupo, _dueno)\n',
       '            ok, n, rep = MEM.restaurar(pet["ids"], grupo, True)\n')]),
    ("lo que ya volvió a aprenderse, sin decirlo («Restored: 0.» mudo)", DLU,
     [('            if ok and rep:\n', '            if False:\n')]),
    ("la frase de la regla se queda tras guardarla", DLU,
     [('                st.session_state["%s_mem_frase" % pet["kp"]] = ""\n', '')]),
    ("la actividad de la regla se queda tras guardarla", DLU,
     [('                st.session_state["%s_mem_act" % pet["kp"]] = None\n', '')]),
    ("⚠️ se vacía con `pop` en vez de ASIGNAR (no le llega al navegador: trampa 31)", DLU,
     [('                st.session_state["%s_mem_frase" % pet["kp"]] = ""\n',
       '                st.session_state.pop("%s_mem_frase" % pet["kp"], None)\n')]),
    ("se vacía también si NO se guardó (y se pierde lo tecleado)", DLU,
     [('            if ok and pet.get("kp"):\n', '            if pet.get("kp"):\n')]),
    ("todo olvidado y dice «Nothing learned yet»", DLU,
     [('        elif _olv:\n            st.caption(t("Nothing active', '        elif False:\n            st.caption(t("Nothing active')]),
    ("lo olvidado, siempre abierto (sin pedirlo)", DLU,
     [('                                key="%s_mem_ver_olv" % kp):\n',
       '                                key="%s_mem_ver_olv" % kp) or True:\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           HJ, [('_REFRESCO_S = 600\n', '_REFRESCO_S = 600   # (control)\n')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))),
                          encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g), flush=True)

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
