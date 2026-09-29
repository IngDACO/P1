# -*- coding: utf-8 -*-
"""Un libro de MENTIRA para ejercitar el guardado de etapas (v528). No es un guardián.

Desde v528 `stage_progress.acreditar` lee `StageProgress`, `Activities` y `Projects` en UNA
llamada (`values_batch_get` del libro) y escribe en OTRA (`values_batch_update`); solo las
filas nuevas van aparte (`append_rows`). Este libro imita exactamente eso y nada más:

- ⚠️ Las hojas **revientan** si alguien las lee o escribe una a una (`get_all_records`,
  `batch_update`): así un guardián que use esto prueba el camino de producción, y si el
  código volviera a leer hoja por hoja se vería aquí en vez de pasar en silencio por el
  camino de respaldo.
- ⚠️ Sustituye `auditoria.registrar`: sin eso, cada prueba escribiría una línea en el
  `AuditTrail` REAL (el guardado anota el cambio de avance de la obra).
- Cuenta las llamadas, que es lo que v528 vino a bajar.

Uso:
    m = fixture_guardado.montar(SP, P, prj, creditos=[...], actividades={orden: {...}})
    ... SP.acreditar(...) ...
    m.restaurar()
"""
import re

from core import auditoria
from core.num import col_letter


def _a1(a1):
    m = re.match(r"^([A-Z]+)(\d+)$", a1)
    c = 0
    for ch in m.group(1):
        c = c * 26 + ord(ch) - 64
    return int(m.group(2)), c


class Libro:
    id = "LIBRO-DE-MENTIRA"

    def __init__(self):
        self.hojas = {}
        self.llamadas = []            # ("leer", n_hojas) · ("escribir", data) · ("append", hoja, n)
        self.falla_escritura = False  # la escritura combinada revienta
        self.falla_lectura = False

    def values_batch_get(self, rangos, params=None):
        self.llamadas.append(("leer", len(rangos)))
        if self.falla_lectura:
            raise RuntimeError("la hoja no responde (lectura)")
        out = []
        for r in rangos:
            h = self.hojas[r.strip("'").replace("''", "'")]
            out.append({"range": r + "!A1:Z999", "values": [list(f) for f in h.grid]})
        return {"valueRanges": out}

    def values_batch_update(self, body):
        if self.falla_escritura:
            self.llamadas.append(("escribir-fallida", []))
            raise RuntimeError("la hoja no responde")
        assert body.get("valueInputOption") == "RAW", "toda escritura de la app es RAW"
        datos = []
        for d in body["data"]:
            tit, a1 = d["range"].split("!")
            h = self.hojas[tit.strip("'").replace("''", "'")]
            h.poner(a1, d["values"][0][0])
            datos.append((h.title, a1, d["values"][0][0]))
        self.llamadas.append(("escribir", datos))


class Hoja:
    def __init__(self, libro, titulo, cabecera, filas):
        self.spreadsheet, self.title = libro, titulo
        self.cab = list(cabecera)
        self.grid = [list(cabecera)] + [[str(f.get(h, "")) for h in cabecera] for f in filas]
        self.nuevas = []
        libro.hojas[titulo] = self

    def poner(self, a1, v):
        f, c = _a1(a1)
        while len(self.grid) < f:
            self.grid.append([])
        fila = self.grid[f - 1]
        while len(fila) < c:
            fila.append("")
        fila[c - 1] = v

    def append_rows(self, filas, value_input_option=None):
        self.spreadsheet.llamadas.append(("append", self.title, len(filas)))
        self.nuevas += [list(x) for x in filas]
        self.grid += [list(x) for x in filas]

    def registros(self):
        return [dict(zip(self.cab, list(f) + [""] * (len(self.cab) - len(f))))
                for f in self.grid[1:]]

    def get_all_records(self, *a, **k):
        raise AssertionError("%s se leyó hoja a hoja: el guardado debe leer en lote" % self.title)

    def batch_update(self, *a, **k):
        raise AssertionError("%s se escribió hoja a hoja: el guardado debe escribir en lote"
                             % self.title)


class Montaje:
    def __init__(self, SP, P, libro, sp, acts, prjs, auditado, orig):
        self.SP, self.P, self.libro = SP, P, libro
        self.sp, self.acts, self.prjs = sp, acts, prjs
        self.auditado, self._orig = auditado, orig

    # ── lo que se escribió ──────────────────────────────────────────────────
    def _escritas(self, titulo):
        return [(a1, v) for k, *resto in self.libro.llamadas if k == "escribir"
                for (t, a1, v) in resto[0] if t == titulo]

    def nuevas_sp(self):
        return [dict(zip(self.SP.HEADERS, f)) for f in self.sp.nuevas]

    def lotes_sp(self):
        """Por cada escritura combinada, lo que llevó de `StageProgress`."""
        out = []
        for k, *resto in self.libro.llamadas:
            if k == "escribir":
                _l = [{"range": a1, "values": [[v]]} for (t, a1, v) in resto[0]
                      if t == self.sp.title]
                if _l:
                    out.append(_l)
        return out

    def _orden_de_fila(self):
        _io = self.acts.cab.index("Order")
        return {i + 1: int(float(f[_io])) for i, f in enumerate(self.acts.grid)
                if i > 0 and len(f) > _io and str(f[_io]).strip()}

    def actividades_escritas(self):
        """`{orden: {columna: valor}}` de lo escrito en `Activities`."""
        letra = {col_letter(i + 1): h for i, h in enumerate(self.acts.cab)}
        fila = self._orden_de_fila()
        out = {}
        for a1, v in self._escritas(self.acts.title):
            f, _c = _a1(a1)
            out.setdefault(fila.get(f), {})[letra[re.match(r"[A-Z]+", a1).group(0)]] = v
        return out

    def escrituras_avance(self):
        """Una lista por escritura combinada: `[{"orden", "avance"}]` de `Activities.Progress`."""
        _lp = col_letter(self.acts.cab.index("Progress") + 1)
        fila = self._orden_de_fila()
        out = []
        for k, *resto in self.libro.llamadas:
            if k != "escribir":
                continue
            _l = [{"orden": fila.get(_a1(a1)[0]), "avance": float(v)}
                  for (t, a1, v) in resto[0]
                  if t == self.acts.title and re.match(r"[A-Z]+", a1).group(0) == _lp]
            if _l:
                out.append(_l)
        return out

    def obra_escrita(self):
        letra = {col_letter(i + 1): h for i, h in enumerate(self.prjs.cab)}
        return {letra[re.match(r"[A-Z]+", a1).group(0)]: v
                for a1, v in self._escritas(self.prjs.title)}

    def cuenta(self):
        """`{"leer": n, "escribir": n, "append": n}` — las llamadas a Google del guardado."""
        out = {"leer": 0, "escribir": 0, "append": 0}
        for k, *_r in self.libro.llamadas:
            if k in ("leer", "append"):
                out[k] += 1
            elif k.startswith("escribir"):
                out["escribir"] += 1
        return out

    def restaurar(self):
        for (mod, nombre), v in self._orig.items():
            setattr(mod, nombre, v)


def montar(SP, P, prj, creditos=(), actividades=None, plan=None, otra_obra=True) -> Montaje:
    """Sustituye las tres hojas y la auditoría. Devuelve el montaje (con `restaurar()`).

    - `creditos`: filas que YA están en `StageProgress` (dicts por columna; se les pone
      `ProjectID` = el de la obra si no lo traen).
    - `actividades`: `{orden: {columna: valor}}` de `Activities`; por defecto, una fila por
      etapa del plan con su peso y avance 0.
    - `otra_obra`: una fila de OTRA obra delante en cada hoja, para que un índice de fila
      mal calculado (o un filtro por obra que falte) escriba donde no debe y se vea.
    """
    pid = str(prj.get("ID", ""))
    plan = plan if plan is not None else SP.plan_de_obra(prj)
    libro = Libro()
    _ajena = {"ProjectID": "PRJ-AJENA", "StageOrder": "1", "Order": "1", "Pct": "100",
              "Activity": "ajena", "Weight": "50", "Progress": "33", "ID": "PRJ-AJENA",
              "Status": "In progress"}
    sp = Hoja(libro, "StageProgress", SP.HEADERS,
              ([_ajena] if otra_obra else [])
              + [dict({"ProjectID": pid}, **c) for c in (creditos or ())])
    if actividades is None:
        actividades = {i: {"Name": e.get("nombre", ""), "Weight": str(e.get("peso", ""))}
                       for i, e in enumerate(plan or [], start=1)}
    acts = Hoja(libro, "Activities", P.ACTIVITIES_HEADERS,
                ([_ajena] if otra_obra else [])
                + [dict({"ProjectID": pid, "Order": str(o), "Progress": "0",
                         "DurationDays": "1"}, **v) for o, v in actividades.items()])
    prjs = Hoja(libro, "Projects", P.PROJECTS_HEADERS,
                ([_ajena] if otra_obra else []) + [dict(prj)])
    auditado = []
    orig = {(SP, "_ws"): SP._ws, (SP, "_invalidate"): SP._invalidate,
            (P, "_activities_ws"): P._activities_ws, (P, "_projects_ws"): P._projects_ws,
            (P, "_invalidate"): P._invalidate, (auditoria, "registrar"): auditoria.registrar}
    SP._ws = lambda: sp
    SP._invalidate = lambda: None
    P._activities_ws = lambda: (acts, None)
    P._projects_ws = lambda: (prjs, None)
    P._invalidate = lambda: None
    auditoria.registrar = lambda *a, **k: auditado.append((a, k)) or True
    return Montaje(SP, P, libro, sp, acts, prjs, auditado, orig)
