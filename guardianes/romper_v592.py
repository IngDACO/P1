# -*- coding: utf-8 -*-
"""Bateria de roturas de v592 (Tools → Plumb line). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba que
cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v592"
PL = "core/plumb_ui.py"
TS = "core/tool_save_ui.py"
TOPE_S = 600

ROTURAS = [
    ("⚠️ los resultados viejos vuelven a pasar por buenos", PL,
     [('    _vigente = data.get("firma") == _ahora\n', "    _vigente = True\n")]),
    ("…o el cálculo deja de apuntar sus entradas (todo saldría viejo)", PL,
     [('        st.session_state["plb_res_multi"] = {"n": n, "firma": _ahora, "results": [compute_plumb({\n',
       '        st.session_state["plb_res_multi"] = {"n": n, "results": [compute_plumb({\n')]),
    ("⚠️ el que no cabe vuelve a decir también «move the assembly»", PL,
     [('        else:\n            st.info(t("{l}: BSR < BS → **move the assembly {x} mm towards the {s}** (the Omega "\n',
       '        if True:\n            st.info(t("{l}: BSR < BS → **move the assembly {x} mm towards the {s}** (the Omega "\n')]),
    ("⚠️ vuelve `:orange[…]` a la tabla", PL,
     [('        return d("DOES NOT FIT · Omega {a} > limit {b}", a=f"{disp.get(\'omega_sacrificio\', 0):.1f}",\n',
       '        return ":orange[:material/warning:] " + d("DOES NOT FIT · Omega {a} > limit {b}", a=f"{disp.get(\'omega_sacrificio\', 0):.1f}",\n')]),
    ("la tabla vuelve a redondear a entero («6» frente a «6.5»)", PL,
     [('    return d("move {x} mm towards the {s}", x=f"{abs(disp.get(\'desp_conjunto\', 0)):.1f}",\n',
       '    return d("move {x} mm towards the {s}", x=f"{abs(disp.get(\'desp_conjunto\', 0)):.0f}",\n')]),
    ("⚠️ el encaje vuelve delante (la comprobación fuera de la vista)", PL,
     [('            d("Fit"): _encaje_txt(r.get("displacement")),\n', ""),
      ('            "BSR (mm)": round(r.get("bsr", 0), 1),\n',
       '            "BSR (mm)": round(r.get("bsr", 0), 1),\n            d("Fit"): _encaje_txt(r.get("displacement")),\n')]),
    ("⚠️ vuelve «… · Lift 3» al cajetín", PL,
     [('        suf = d("lift {i} of {n}", i=i, n=n) if n > 1 else ""\n',
       '        suf = d("Lift {i}", i=i)\n')]),
    ("vuelve «towards the L side»", PL,
     [('    return d("left") if str(s) == "L" else d("right") if str(s) == "R" else str(s or "")\n',
       '    return str(s or "")\n')]),
    ("las cifras de la plantilla dejan de llevar al dibujo", PL,
     [('                st.session_state["_bajar_cpx_plb_dibujo"] = True\n', "")]),
    ("⚠️ el aviso del plano vuelve a ser de UNA pasada (o desaparece)", PL,
     [('        if _plano.get("params"):\n', "        if False:\n")]),
    ("el aviso de leer un PDF vuelve a `st.success` (antes del `st.rerun()`)", PL,
     [('                flash.exito(t(":material/check_circle: From the drawing: **{x}**. Fill in "\n',
       '                st.success(t(":material/check_circle: From the drawing: **{x}**. Fill in "\n')]),
    ("vuelve «✏️ = by hand»", PL,
     [('                  ":material/edit: = by hand"))\n', '                  "✏️ = by hand"))\n')]),
    ("vuelve «lift(s)»", PL,
     [('                            d("Template DBP {a} · d1 {b}/d2 {c} · {n} lifts", a=f"{r0[\'dbp\']:.1f}",\n',
       '                            d("Template DBP {a} · d1 {b}/d2 {c} · {n} lift(s)", a=f"{r0[\'dbp\']:.1f}",\n')]),
    ("todos los PDF vuelven a llamarse «plumb_setout.pdf»", PL,
     [('                   nombre_archivo=f"Plumb_setout_{_archivo(_pr_base, \'shaft\')}_"\n',
       '                   nombre_archivo="plumb_setout.pdf" if True else f"Plumb_setout_{_archivo(_pr_base, \'shaft\')}_"\n')]),
    ("⚠️ el destino vuelve a ofrecer todas las obras", TS,
     [('    proys = [p for p in proys if plan_ui.es_de_herramientas(p) or str(p.get("ID", "")) == obra_id]\n', "")]),
    ("⚠️ el destino deja de venir elegido", TS,
     [("                st.session_state[_kp] = _lbl\n", "")]),
    ("⚠️ guardar dos veces vuelve a duplicar", TS,
     [('        return bool(prj) and hecho.get("firma") == firma and hecho.get("pid") == str(prj.get("ID", ""))\n',
       "        return False\n")]),
    ("⚠️ con datos viejos se vuelve a poder descargar y guardar", TS,
     [("    if not vigente:\n        st.caption(", "    if False:\n        st.caption(")]),
    ("⚠️ reabrir vuelve a perder la obra", TS,
     [('                st.session_state["pl_prj_" + _PREFIJO.get(herramienta, "").rstrip("_")] = (\n',
       "                _nada = (\n")]),
    ("una herramienta deja de pasar su obra al bloque de guardar", "core/belting_ui.py",
     [('                   obra_id=str((_prj or {}).get("ID", "")))   # v592\n', "                   )\n")]),
    ("Files vuelve a `single-row` (un toque solo enmarca)", "core/projects_ui.py",
     [('            on_select="rerun", selection_mode="single-cell",\n            key=f"arch_tbl_{pid}_',
       '            on_select="rerun", selection_mode="single-row",\n            key=f"arch_tbl_{pid}_')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PL,
           [("def _lado(s) -> str:\n", "def _lado(s) -> str:   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
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
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
