# -*- coding: utf-8 -*-
"""Qué baterías hay que repetir tras un cambio (01/11/2026). Módulo auxiliar: lo usa `tanda.py`.

Hasta aquí la lista salía de buscar a mano «qué baterías anclan en lo que toqué». Ahora la dice el
código: una batería está afectada si una de sus ANCLAS cae a `MARGEN` líneas o menos de una línea
cambiada, si se cambió la propia batería, o si se cambió un guardián que ella corre. Las anclas las
lee `anclas_lectura.py`, el mismo lector que `check_anclas_roturas`.

⚠️ NO decide si se despliega: la suite entera sigue siendo obligatoria (v385). Esto solo elige qué
baterías VIEJAS se repiten; las nuevas se corren siempre.

    py -3.12 baterias_afectadas.py            # lo que hay sin commit, contra HEAD
    py -3.12 baterias_afectadas.py a123..b456 # lo que cambió entre dos commits
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
sys.path.insert(0, str(AQUI))
import anclas_lectura as A                                         # noqa: E402

MARGEN = 3
_HUNK = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _git(*args):
    return subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def lineas_de_diff(texto):
    """{ruta desde el repo: {líneas tocadas del fichero NUEVO}} de un `git diff -U0`."""
    out, actual = {}, None
    for l in texto.splitlines():
        if l.startswith("+++ "):
            ruta = l[4:].strip()
            actual = None if ruta == "/dev/null" else ruta[2:]
            if actual:
                out.setdefault(actual, set())
            continue
        m = _HUNK.match(l)
        if m and actual:
            ini, n = int(m[1]), int(m[2] or 1)
            # ⚠️ Un borrado (n=0) no tiene línea nueva: se marca el hueco entre `ini` e `ini + 1`
            out[actual].update(range(ini, ini + max(n, 1)) if n else (ini, ini + 1))
    return out


def cambios(base="HEAD"):
    return lineas_de_diff(_git("diff", "-U0", "--no-color", base, "--", "survey_app", "guardianes"))


def nuevas(base="HEAD"):
    """Las baterías que no existían en `base`: sin seguimiento, o añadidas en ese rango."""
    fuera = _git("ls-files", "--others", "--exclude-standard", "--", "guardianes")
    alta = _git("diff", "--name-only", "--diff-filter=A", base, "--", "guardianes")
    return sorted({Path(l.strip()).stem for l in (fuera + "\n" + alta).splitlines()
                   if Path(l.strip()).name.startswith("romper_") and l.strip().endswith(".py")})


def _resuelve(rel):
    for c in (Path(rel), A.APP / rel, A.APP / "core" / rel, A.GUAR / rel):
        if c.is_file():
            return c.resolve()
    return None


def cruzar(tocadas, margen=MARGEN):
    """{batería: [motivos]} con `tocadas` = {ruta desde el repo: {líneas}}."""
    por_ruta = {(REPO / k).resolve(): v for k, v in tocadas.items()}
    textos = {}
    out = {}

    def _texto(c):
        if c not in textos:
            textos[c] = c.read_text(encoding="utf-8").replace("\r\n", "\n")
        return textos[c]

    cambiados = {Path(k).stem for k in tocadas if k.startswith("guardianes/")}
    for p in sorted(A.GUAR.glob("romper_*.py")):
        motivos = []
        if p.stem in cambiados:
            motivos.append("se cambió la batería")
        fuente = p.read_text(encoding="utf-8")
        motivos += ["se cambió %s, que ella corre" % g for g in sorted(cambiados)
                    if g.startswith(("verif_", "check_")) and g in fuente]
        for rel, ancla in A.analiza(p)["sitios"]:
            c = _resuelve(rel)
            if c not in por_ruta:
                continue
            src, a = _texto(c), ancla.replace("\r\n", "\n")
            i = src.find(a)
            while i >= 0:
                l0 = src.count("\n", 0, i) + 1
                l1 = l0 + a.rstrip("\n").count("\n")      # el salto final del ancla no es otra línea
                if any(l in por_ruta[c] for l in range(l0 - margen, l1 + margen + 1)):
                    motivos.append("ancla en %s:%d" % (c.name, l0))
                    break
                i = src.find(a, i + 1)
        if motivos:
            out[p.stem] = motivos
    return out


def afectadas(base="HEAD"):
    return cruzar(cambios(base))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _base = (sys.argv[1:] or ["HEAD"])[0]
    _t = cambios(_base)
    print("%d ficheros cambiados, %d líneas" % (len(_t), sum(len(v) for v in _t.values())))
    _n = nuevas(_base)
    print("nuevas: %s" % (", ".join(_n) or "ninguna"))
    _af = cruzar(_t)
    for b, ms in _af.items():
        print("  %-16s %s%s" % (b, "; ".join(ms[:3]), " (+%d)" % (len(ms) - 3) if len(ms) > 3 else ""))
    print("%d baterías afectadas" % len(_af))
