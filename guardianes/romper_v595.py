# -*- coding: utf-8 -*-
"""Bateria de roturas de v595 (Tools → Belting). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba
que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v595"
BE = "core/belting_ui.py"
BL = "core/belting.py"
TOPE_S = 600

ROTURAS = [
    ("⚠️ un ascensor SIN MEDIR vuelve a dar «DSTS -99 mm · above FFL»", BE,
     [("        _sin = [str(i + 1) for i, x in enumerate(hgpr_list) if float(x or 0) <= 0]\n",
       "        _sin = []\n")]),
    ("…o sin HQ/HGP vuelve a calcular", BE,
     [('        _faltan = [x for x, val in (("HQ", hq), ("HGP", hgp)) if float(val or 0) <= 0]\n',
       "        _faltan = []\n")]),
    ("⚠️ los resultados viejos vuelven a pasar por buenos", BE,
     [('    _vig = est.get("firma") == _ahora\n', "    _vig = True\n")]),
    ("…o se calcula sin guardar su huella (nunca vigente)", BE,
     [('                                    "hgp": hgp, "hq": hq, "firma": _ahora}\n',
       '                                    "hgp": hgp, "hq": hq}\n')]),
    ("…o el bloque de guardar deja de saberlo", BE,
     [("                   vigente=_vig)                                           # v595\n",
       "                   )\n")]),
    ("el aviso del plano vuelve a ser de UNA pasada (o desaparece)", BE,
     [('        if _plano.get("hq") or _plano.get("hgp"):\n', "        if False:\n")]),
    ("⚠️ el aviso del PDF con datos vuelve antes del `st.rerun()` (no se ve)", BE,
     [('                flash.exito(t(":material/check_circle: From the drawing: **{x} mm**. Enter the actual "\n',
       '                st.success(t(":material/check_circle: From the drawing: **{x} mm**. Enter the actual "\n')]),
    ("…y el de sin datos", BE,
     [('                flash.aviso(t("HQ/HGP were not found in the drawing. Enter them by hand."))\n',
       '                st.warning(t("HQ/HGP were not found in the drawing. Enter them by hand."))\n')]),
    ("vuelve «21 mm below from the top FFL»", BE,
     [('    return (d("{x} mm below the top FFL", x=f"{abs(v):.1f}") if v > 0\n',
       '    return (d("{x} mm below from the top FFL", x=f"{abs(v):.0f}") if v > 0\n')]),
    ("vuelve «HGPR lift 1» sin `t()`", BE,
     [('        v = cols[i % len(cols)].number_input(t("HGPR · Lift {n}", n=i + 1), step=0.5,\n',
       '        v = cols[i % len(cols)].number_input(f"HGPR lift {i+1}", step=0.5,\n')]),
    ("la leyenda vuelve al lápiz que no llevan los campos", BE,
     [('    st.markdown(t("**Data**  ·  :material/description: = from the drawing · :material/edit: = by hand"))\n',
       '    st.markdown(t("**Data**  ·  :material/description: = from the drawing · ✏️ = by hand"))\n')]),
    ("vuelve «E1: DSTS 21.0» al resumen guardado", BE,
     [('    _resumen = ", ".join(d("Lift {i}: DSTS {x}", i=r["elevador"], x=f"{float(r[\'dsts\']):.1f}")\n',
       '    _resumen = ", ".join(f"E{r[\'elevador\']}: DSTS {r[\'dsts\']}"\n')]),
    ("vuelve «belting.pdf»", BE,
     [("                   nombre_archivo=f\"Belting_{_archivo(_pr, 'shaft')}_\"\n",
       '                   nombre_archivo=f"belting_"\n')]),
    ("las cifras vuelven a no llevar a ningún sitio", BE,
     [('                st.session_state["_bajar_cpx_belt_dibujo"] = True\n', "                pass\n")]),
    ("el título del PDF vuelve sin `d()`", BE,
     [('        d("Belting — car position"),\n', '        "Belting — car position",\n')]),
    ("…o el nombre del PDF del botón", BE,
     [('    render_guardar(herramienta="belting", titulo_pdf=d("belting"),\n',
       '    render_guardar(herramienta="belting", titulo_pdf="belting",\n')]),
    ("el aviso de reabrir vuelve a su f-string", BE,
     [('        st.info(t(":material/replay: Reopened calculation **{x}**. Adjust whatever you need and "\n'
       '                  "calculate again.", x=_reab))\n',
       '        st.info(f":material/replay: Reopened calculation **{_reab}**. Adjust whatever you need and calculate again.")\n')]),
    ("⚠️ «Elevator» vuelve al diagrama", BL,
     [('{_d("Lift {n}", n=r["elevador"])}', '{_d("Elevator")} {r["elevador"]}')]),
    ("⚠️ el nombre vuelve sin medir ni escapar en el diagrama", BL,
     [("{texto_svg.cabe(proyecto, VW - 36, 9, True)}", "{proyecto}")]),
    ("una herramienta vuelve a su selector de plano sin `t()`", "core/rail_cut_ui.py",
     [('        pdf = plan_store.selector(t("Drawing PDF (for LFKK / LFGK)"), "rc_pdf")',
       '        pdf = plan_store.selector("Drawing PDF (for LFKK / LFGK)", "rc_pdf")')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", BE,
           [("def _posicion(dsts) -> str:\n", "def _posicion(dsts) -> str:   # (control)\n")])


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
