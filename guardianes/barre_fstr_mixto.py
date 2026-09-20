"""CUARTA red: la f-string ENTERA, no sus trozos sueltos.

⚠️ Las tres redes de v441/v442 miran cadenas COMPLETAS. Una f-string no es una cadena
completa: es una lista de trozos, y cada trozo por separado puede no parecer nada
(`"Guardado como **"` + `"** en "`). Así se colaron dos cosas:

  · fragmentos de UNA palabra   → `f"{n} alarmas"`      (la red corta pide 2+)
  · f-strings A MEDIO TRADUCIR  → `f"Collected {x} de {y}"`

La red buena CONCATENA los trozos literales de cada f-string y mira el resultado. Es
la misma lección de la trampa nº30: cada red nueva descubre una bolsa nueva, y un «0»
solo vale para la forma que esa red sabe ver.
"""
import ast
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

from barre_cortas import ES as _ES_FUNC, _sin                      # noqa: E402

# ⚠️ El léxico de `barre_cortas` son PALABRAS FUNCIONALES (de, la, con, sin…), y con
# él la red ve `f"Collected {x} de {y}"` pero NO ve `f"{n} alarmas"` — justo el caso
# que originó esta red. Es la trampa nº28: un detector por idioma es ciego a los
# sustantivos sin acento ni artículo. Se le suman los del DOMINIO, y aun así el
# «0» hay que leerlo como *0 de lo que esta red puede ver*.
_ES_NOMBRES = {
    "alarmas", "vencidos", "vencidas", "credenciales", "proyectos", "proyecto",
    "personas", "usuarios", "horas", "dias", "obras", "obra", "activos", "activo",
    "pendientes", "pendiente", "retraso", "retrasos", "adelanto", "adelantado",
    "adelantados", "sitios", "trabajos", "trabajo", "actividades", "facturas",
    "nominas", "cotizaciones", "clientes", "cliente", "gastos", "compras",
    "recibos", "documentos", "archivos", "fotos", "alertas", "avisos",
    "elevadores", "elevador", "asignados", "asignado", "ausencias", "colillas",
    "restantes", "creadas", "omitidas", "guardado", "guardada", "eliminado",
    "desactivado", "cartera", "semana", "semanas", "pisos", "margen", "consumido",
    "planificados", "planificado", "planificador", "libres", "ocupados",
    "cumple", "faltan", "tambien", "llevas", "mostrando", "abiertas", "cerradas",
}
ES = _ES_FUNC | _ES_NOMBRES


def _dentro_de_t(tr):
    """Nodos JoinedStr que ya viven dentro de t()/d()/_d(): no se tocan."""
    fuera = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in {"t", "d", "_d"}:
            for x in ast.walk(n):
                fuera.add(id(x))
    return fuera


def mixtas(ruta):
    """f-strings cuyo TEXTO literal concatenado contiene español."""
    try:
        src = Path(ruta).read_text(encoding="utf-8")
        tr = ast.parse(src)
    except Exception:
        return []
    fuera = _dentro_de_t(tr)
    out = []
    for n in ast.walk(tr):
        if not isinstance(n, ast.JoinedStr) or id(n) in fuera:
            continue
        txt = " ".join(p.value for p in n.values
                       if isinstance(p, ast.Constant) and isinstance(p.value, str))
        if not txt.strip():
            continue
        # ⚠️ Se quitan colores hex y etiquetas HTML: `background:#eaf3de` aporta la
        # «palabra» «de» y da un falso positivo (el mismo de v442).
        limpio = re.sub(r"#[0-9a-fA-F]{3,8}", " ", txt)
        limpio = re.sub(r"<[^>]*>", " ", limpio)
        limpio = re.sub(r":material/[a-z_]+:", " ", limpio)
        # y los identificadores con guión bajo, que son claves, no texto
        limpio = re.sub(r"\w*_\w*", " ", limpio)
        if set(re.findall(r"[a-záéíóúñü]+", _sin(limpio))) & ES:
            out.append((n.lineno, txt.strip()[:70]))
    return out


if __name__ == "__main__":
    tot = 0
    for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
        hits = sorted(set(mixtas(f)))
        if hits:
            print(f"\n── {f.name} ({len(hits)})")
            for ln, s in hits:
                print(f"   {ln}: {s!r}")
            tot += len(hits)
    print(f"\n{tot} f-strings con español")
