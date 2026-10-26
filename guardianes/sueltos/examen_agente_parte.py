# -*- coding: utf-8 -*-
"""EXAMEN del agente del parte (v607). ⚠️ LLAMA A LA API DE PAGO: no es un guardián, la suite
no lo corre (solo `verif_*`/`check_*`), y cada vuelta cuesta dinero — se corre a mano y con el
permiso del usuario (26/10/2026: A+B con Sonnet 5.5, ≈ US$1,5).

  py -3.12 sueltos/examen_agente_parte.py A     → los 4 partes de prueba de PRJ-0034
  py -3.12 sueltos/examen_agente_parte.py B     → las 30 notas reservadas de Simpro (v522)

A: etiquetas en `examen_agente_etiquetas.py`, escritas ANTES de la primera vuelta.
B: las etiquetas de v522 (`D:\\CopeX\\Logs_simpro\\_texto\\analisis\\etiquetas_prueba.py`), y la
   MISMA cuenta que `verif_v522` (acierto por línea; el vocabulario dio 22 de 40, 1 error).

⚠️ Las notas de Simpro llevan NOMBRES de trabajadores: se tapan aquí, ANTES de mandarlas, con
la lista de `nombres_redactar.json` (fuera del repo), y lo que se guarda va a D:, no al repo.
⚠️ Todo en SOLO LECTURA: la hoja se lee con `spreadsheets.readonly` y nada se escribe.
"""
import concurrent.futures as cf
import importlib.util
import io
import json
import os
import re
import sys
import time

APP = r"C:\Users\diego\P1\survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP)
sys.path.insert(0, APP)
sys.path.insert(0, os.path.dirname(AQUI))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import tomllib                                                      # noqa: E402

from core import parte_agente as AG                                 # noqa: E402
from core import parte_propuestas as PP                             # noqa: E402
from core import stages as S                                        # noqa: E402

SEC = tomllib.load(open(os.path.join(APP, ".streamlit", "secrets.toml"), "rb"))
KEY = str(SEC.get("ANTHROPIC_API_KEY", "") or "")
T = r"D:\CopeX\Logs_simpro\_texto"
SALIDA = os.path.join(T, "analisis", "agente")


def _leer_todos(casos, plan_de, mapa_de, fecha_de=lambda c: ""):
    """Lee los casos EN PARALELO (como la app). `casos` = [(id, texto)].
    ⚠️ El PRIMERO solo, antes que el resto: llamadas simultáneas no comparten la caché (cada
    una la escribe y la paga), así que el primero la deja escrita para los demás."""
    out = {}
    if casos:
        c0, t0 = casos[0]
        out[c0] = AG.leer(t0, plan_de(c0), fecha_de(c0), mapa_de(c0), None, None, "en", KEY)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        fut = {ex.submit(AG.leer, txt, plan_de(cid), fecha_de(cid), mapa_de(cid), None, None,
                         "en", KEY): cid for cid, txt in casos[1:]}
        for f in cf.as_completed(fut):
            out[fut[f]] = f.result()
    return out


def _resumen(lect):
    ok = [r for r, _m in lect.values() if r]
    fallos = [m for r, m in lect.values() if not r]
    uso = {}
    for r in ok:
        uso = AG._suma(uso, r["uso"])
    seg = sorted(r["seg"] for r in ok)
    print("\nLecturas: %d bien, %d fallidas %s" % (len(ok), len(fallos), fallos or ""))
    if seg:
        print("Segundos: mediana %.1f · máx %.1f" % (seg[len(seg) // 2], seg[-1]))
    print("Tokens: entrada %d · salida %d · leídos de caché %d · escritos en caché %d"
          % (uso.get("in", 0), uso.get("out", 0), uso.get("cache_r", 0), uso.get("cache_w", 0)))
    print("Coste: US$%.4f  (US$%.4f por parte)" % (AG.coste_usd(uso),
                                                   AG.coste_usd(uso) / max(1, len(ok))))
    print("Códigos fuera del plan descartados: %d · líneas que el modelo se saltó: %d"
          % (sum(r["invalidos"] for r in ok), sum(r["anadidas"] for r in ok)))
    print("Modelos que contestaron: %s" % sorted({r["modelo"] for r in ok}))


# ═════════════════════════════════════════════════════════════════
# A · los 4 partes de PRJ-0034
# ═════════════════════════════════════════════════════════════════
def examen_a():
    import gspread
    from google.oauth2.service_account import Credentials
    from examen_agente_etiquetas import ETIQUETAS_A
    from core import stage_progress as SP
    gc = gspread.authorize(Credentials.from_service_account_info(
        dict(SEC["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))
    m = gc.open_by_key(SEC["TIMECLOCK_SHEET_ID"])
    sid = next(str(r.get("SheetID", "")).strip() for r in m.worksheet("Groups").get_all_records()
               if str(r.get("Group", "")).strip().casefold() == "cliente1")
    L = gc.open_by_key(sid)
    prj = next(r for r in L.worksheet("Projects").get_all_records(numericise_ignore=["all"])
               if r.get("ID") == "PRJ-0034")
    logs = {r["ID"]: r for r in L.worksheet("DailyLogs").get_all_records(numericise_ignore=["all"])
            if r.get("ProjectID") == "PRJ-0034"}
    mapa = {}
    for r in L.worksheet("StageProgress").get_all_records(numericise_ignore=["all"]):
        if r.get("ProjectID") == "PRJ-0034":
            try:
                mapa[(int(float(r.get("StageOrder"))), str(r.get("Activity")))] = float(r.get("Pct") or 0)
            except ValueError:
                pass
    plan = SP.plan_de_obra(prj)
    print("PRJ-0034 · %d etapas · lo acreditado: %d actividades" % (len(plan), len(mapa)))
    casos = [(lid, str(logs[lid]["Text"])) for lid in sorted(ETIQUETAS_A) if lid in logs]
    lect = _leer_todos(casos, lambda c: plan, lambda c: mapa, lambda c: str(logs[c].get("Date", "")))

    tot = {"hecho": [0, 0, 0], "pregunta": [0, 0, 0], "empezado": [0, 0, 0]}
    mal_ag = mal_vo = 0
    vo_tot = {"hecho": [0, 0], "pregunta": [0, 0]}
    for lid, txt in casos:
        reg, motivo = lect[lid]
        print("\n" + "=" * 90 + "\n%s %r" % (lid, txt))
        voc = PP.propuestas(txt, plan, {})
        vo_dir = {f["actividad"] for f in voc["actividades"]}
        vo_ops = vo_dir | {o["actividad"] for q in voc["preguntas"] for o in q["opciones"]} \
            | {o["actividad"] for e in voc["etapas"] for o in e["opciones"]}
        if not reg:
            print("   SIN LECTURA: %s" % motivo)
            continue
        for f in reg["fragmentos"]:
            print("   L%s [%s] «%s» → %s%s" % (f["linea"], f["clase"], f["texto"], f["actividades"],
                                              ("  ¿%s?" % f["pregunta"]) if f["pregunta"] else
                                              ("  (%s)" % f["motivo"] if f["motivo"] else "")))
        for tipo, k, okk, mal in ETIQUETAS_A[lid]:
            fs = [f for f in reg["fragmentos"] if k.lower() in f["texto"].lower()]
            hechas = {a for f in fs if f["clase"] == "done" for a in f["actividades"]}
            ops = {a for f in fs if f["clase"] == "question" for a in f["actividades"]}
            m_ag = len(hechas & mal)
            mal_ag += m_ag
            mal_vo += len(vo_dir & mal)
            if tipo == "hecho":
                tot[tipo][0] += 1
                tot[tipo][1] += bool(hechas & okk)
                tot[tipo][2] += bool((hechas | ops) & okk)
                vo_tot[tipo][0] += bool(vo_dir & okk)
                vo_tot[tipo][1] += bool(vo_ops & okk)
                v = "directo" if hechas & okk else ("en pregunta" if ops & okk else "FALLO")
            elif tipo == "pregunta":
                tot[tipo][0] += 1
                tot[tipo][1] += bool(ops & okk)
                tot[tipo][2] += bool((hechas | ops) & okk)
                vo_tot[tipo][0] += bool((vo_ops - vo_dir) & okk)
                vo_tot[tipo][1] += bool(vo_ops & okk)
                v = "pregunta" if ops & okk else ("directo" if hechas & okk else "FALLO")
            else:
                tot[tipo][0] += 1
                tot[tipo][1] += (not m_ag) and any(f["clase"] == "started" for f in fs)
                tot[tipo][2] += not m_ag
                v = "empezado" if any(f["clase"] == "started" for f in fs) and not m_ag else (
                    "ERROR (acreditaría)" if m_ag else "no acreditado")
            print("   · %-9s «%s»: %s%s" % (tipo, k, v, ("  ⚠️ error seguro %s" % (hechas & mal)) if m_ag else ""))
    print("\n" + "=" * 90)
    print("AGENTE   hecho: %d/%d directos (%d/%d contando preguntas) · pregunta: %d/%d · "
          "empezado sin acreditar: %d/%d · errores seguros: %d"
          % (tot["hecho"][1], tot["hecho"][0], tot["hecho"][2], tot["hecho"][0],
             tot["pregunta"][1], tot["pregunta"][0], tot["empezado"][2], tot["empezado"][0], mal_ag))
    print("VOCABUL. hecho: %d/%d directos (%d/%d contando preguntas) · pregunta: %d/%d · "
          "errores seguros: %d" % (vo_tot["hecho"][0], tot["hecho"][0], vo_tot["hecho"][1],
                                   tot["hecho"][0], vo_tot["pregunta"][0], tot["pregunta"][0], mal_vo))
    _resumen(lect)
    return lect


# ═════════════════════════════════════════════════════════════════
# B · las 30 notas reservadas (v522)
# ═════════════════════════════════════════════════════════════════
def _tapador():
    d = json.load(io.open(os.path.join(T, "analisis", "nombres_redactar.json"), encoding="utf-8"))
    # Lo ambiguo primero (frases con su reemplazo), después las palabras sueltas (con su
    # posesivo pegado: «Jesse's», «javads»).
    pats = [(re.compile(p, re.I if "i" in fl else 0), rep) for p, rep, fl in d.get("regex", [])]
    pats += [(re.compile(r"\b%s(?:'s|s)?\b" % re.escape(n), re.I), "[worker]") for n in d.get("i", [])]

    def tapar(s):
        n = 0
        for p, rep in pats:
            s, k = p.subn(rep, s)
            n += k
        return s, n
    return tapar


def examen_b():
    conds = [c["nombre"] for p in S.PISTAS for c in S.condicionales(p) if "hydraulic" not in c["nombre"]]
    plan = S.plan_de("Ripout + Installation", conds)
    _sp = importlib.util.spec_from_file_location("etq522", os.path.join(T, "analisis", "etiquetas_prueba.py"))
    E = importlib.util.module_from_spec(_sp)
    _sp.loader.exec_module(E)
    ETAPA_DE = {a["nombre"]: "S:%s:%s" % (e["pista"], e["numero"]) for e in plan for a in e["actividades"]}
    notas = json.load(io.open(os.path.join(T, "analisis", "prueba_notas.json"), encoding="utf-8"))
    tapar = _tapador()
    casos, tapados = [], 0
    for k, n in enumerate(notas):
        lin = []
        for l in n["lineas"]:
            l2, c = tapar(l)
            tapados += c
            lin.append(l2)
        casos.append((k, "\n".join(lin)))
    print("Notas: %d · líneas: %d · nombres tapados antes de enviar: %d"
          % (len(casos), sum(len(n["lineas"]) for n in notas), tapados))
    lect = _leer_todos(casos, lambda c: plan, lambda c: {})

    def _bien(acts, okk):
        return [a for a in acts if a in okk or ETAPA_DE.get(a) in okk]

    esperan = a_dir = a_len = err = en_no_avance = 0
    vo_esp = vo_ok = vo_err = 0
    detalle = []
    for k, txt in casos:
        reg, motivo = lect[k]
        n = notas[k]
        r = __import__("core.vocabulario", fromlist=["buscar"]).buscar("\n".join(n["lineas"]), plan)
        vpor = {}
        for c in r["candidatos"]:
            for i in c["lineas"]:
                vpor.setdefault(i, []).append(c["actividad"])
        for e in r["etapas"]:
            for i in e["lineas"]:
                vpor.setdefault(i, []).append("S:%s:%s" % (e["pista"], e["numero"]))
        for i, (tipo, okk, mal) in enumerate(E.ETIQUETAS[(n["carpeta"], n["archivo"])]):
            fs = [f for f in (reg or {}).get("fragmentos", []) if f["linea"] == i + 1]
            hechas = [a for f in fs if f["clase"] == "done" for a in f["actividades"]]
            ops = [a for f in fs if f["clase"] == "question" for a in f["actividades"]]
            err += sum(1 for a in hechas if a in mal)
            vv = vpor.get(i, [])
            vo_err += sum(1 for v in vv if v in mal)
            if tipo in ("trabajo", "retirada"):
                esperan += 1
                a_dir += bool(_bien(hechas, okk))
                a_len += bool(_bien(hechas + ops, okk))
                vo_esp += 1
                vo_ok += bool([v for v in vv if v in okk or ETAPA_DE.get(v) in okk
                               or any(ETAPA_DE.get(a) == v for a in okk)])
                veredicto = "directo" if _bien(hechas, okk) else (
                    "en pregunta" if _bien(ops, okk) else "FALLO")
            elif tipo in ("no_avance", "pendiente"):
                en_no_avance += bool(hechas)
                veredicto = "propone %s" % hechas if hechas else "bien (nada)"
            else:
                veredicto = "vago: %s" % (hechas or ops or "-")
            detalle.append((k, i, tipo, veredicto, [(f["clase"], f["actividades"]) for f in fs]))
    for k, i, tipo, v, fs in detalle:
        print("   %02d.%d %-9s %-14s %s" % (k, i, tipo, v[:14], fs))
    print("\n" + "=" * 90)
    print("AGENTE   aciertos: %d de %d directos (%d contando preguntas) · errores seguros: %d · "
          "propone algo en líneas no_avance/pendiente: %d" % (a_dir, esperan, a_len, err, en_no_avance))
    print("VOCABUL. aciertos: %d de %d · errores seguros: %d   (v522: 22 de 40, 1)" % (vo_ok, vo_esp, vo_err))
    _resumen(lect)
    os.makedirs(SALIDA, exist_ok=True)
    _f = os.path.join(SALIDA, "examen_B_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
    json.dump({str(k): v[0] for k, v in lect.items()}, io.open(_f, "w", encoding="utf-8"),
              ensure_ascii=False)
    print("Guardado (fuera del repo): %s" % _f)
    return lect


# ═════════════════════════════════════════════════════════════════
# C · las 1070 notas (sin etiquetas: cobertura, barandillas, coste y una muestra)
# ═════════════════════════════════════════════════════════════════
def examen_c():
    """Lo que se puede medir sin etiquetas, con las MISMAS barandillas que `verif_v522`:
    nada propuesto como hecho bajo «Issues/Pendings», ninguna oración de QUITAR que acredite
    MONTAR, líneas que el modelo se saltó, códigos fuera del plan; y una muestra de 30 notas
    al azar (semilla 607) para que el usuario la lea. ⚠️ Se guarda en D:, nunca en el repo.
    Se reanuda: lo ya leído (`examen_C.jsonl`) no se vuelve a pagar."""
    import random
    conds = [c["nombre"] for p in S.PISTAS for c in S.condicionales(p) if "hydraulic" not in c["nombre"]]
    plan = S.plan_de("Ripout + Installation", conds)
    PISTA = {a[0]: p for (p, n), v in S.ACTIVIDADES.items() for a in v}
    CAB = re.compile(r"^\W*(issues?|problems?|pendings?( lifts?)?( to do)?|pending items?|to do( list)?)\s*:?", re.I)
    QUITAR = re.compile(r"\bremov\w*|\bdismantl\w*|\brip(?:ped|ping)\s*-?\s*out\b"
                        r"|\b(?:took|take[sn]?|taking)\s+(?:\w+\s+)?(?:off|out|down|apart)\b", re.I)
    OKR = ("Remove", "Rip out", "Release", "Final clear-out", "Lighten", "Pack up",
           "Initial electrical shutdown", "Fully kill lift", "Retain/preserve")
    partes = json.load(io.open(os.path.join(T, "partes.json"), encoding="utf-8"))
    tapar = _tapador()
    casos = []
    for k, p in enumerate(partes):
        lin = [tapar(l)[0] for l in p["lineas"]]
        if any(x.strip() for x in lin):
            casos.append((k, "\n".join(lin)))
    os.makedirs(SALIDA, exist_ok=True)
    _jl = os.path.join(SALIDA, "examen_C.jsonl")
    hechos = {}
    if os.path.isfile(_jl):
        for l in io.open(_jl, encoding="utf-8"):
            d = json.loads(l)
            if d.get("reg"):
                hechos[d["k"]] = d["reg"]
    faltan = [c for c in casos if c[0] not in hechos]
    print("Notas con texto: %d · ya leídas: %d · por leer: %d" % (len(casos), len(hechos), len(faltan)))
    lock = __import__("threading").Lock()
    fallos = {}

    def _uno(c):
        k, txt = c
        reg, mot = AG.leer(txt, plan, "", {}, None, None, "en", KEY)
        if not reg and mot in ("rate_limit", "timeout", "connection", "api_529", "api_500"):
            time.sleep(5)
            reg, mot = AG.leer(txt, plan, "", {}, None, None, "en", KEY)
        with lock:
            if reg:
                hechos[k] = reg
                with io.open(_jl, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"k": k, "reg": reg}, ensure_ascii=False) + "\n")
            else:
                fallos[k] = mot
        return k

    t0 = time.time()
    if faltan:
        _uno(faltan[0])                                     # escribe la caché para los demás
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            for i, _k in enumerate(ex.map(_uno, faltan[1:]), start=2):
                if i % 100 == 0:
                    print("   %d de %d · %.0f s" % (i, len(faltan), time.time() - t0), flush=True)
    print("Fallidas: %d %s" % (len(fallos), sorted(set(fallos.values()))))

    clases, bloq, contra, preguntas_nota = {}, 0, 0, []
    for k, txt in casos:
        reg = hechos.get(k)
        if not reg:
            continue
        lin = txt.splitlines()
        en_bloque, bloq_lineas = False, set()
        for i, l in enumerate(lin, start=1):
            if CAB.match(l):
                en_bloque = True
            elif en_bloque:
                bloq_lineas.add(i)
        nq = 0
        for f in reg["fragmentos"]:
            clases[f["clase"]] = clases.get(f["clase"], 0) + 1
            nq += f["clase"] in ("question", "unclear")
            if f["clase"] == "done" and f["linea"] in bloq_lineas:
                bloq += 1
            if f["clase"] == "done" and QUITAR.search(f["texto"]):
                contra += any(PISTA.get(a) == "install" and not a.startswith(OKR)
                              for a in f["actividades"])
        preguntas_nota.append(nq)
    leidas = [hechos[k] for k, _t in casos if k in hechos]
    print("\n" + "=" * 90)
    print("Trozos por clase: %s" % dict(sorted(clases.items(), key=lambda x: -x[1])))
    print("Propuestos como HECHOS bajo «Issues/Pendings»: %d" % bloq)
    print("Trozos de QUITAR propuestos como MONTAR: %d" % contra)
    pq = sorted(preguntas_nota)
    if pq:
        print("Preguntas + no entendidos por nota: mediana %d · media %.1f · máx %d"
              % (pq[len(pq) // 2], sum(pq) / len(pq), pq[-1]))
    _resumen({k: (hechos[k], "") for k, _t in casos if k in hechos})
    # La muestra para el usuario: 30 notas al azar, con lo que leyó el agente.
    rnd = random.Random(607)
    muestra = rnd.sample([c for c in casos if c[0] in hechos], min(30, len(leidas)))
    _m = os.path.join(SALIDA, "muestra_C_30.txt")
    with io.open(_m, "w", encoding="utf-8") as f:
        for k, txt in muestra:
            f.write("=" * 80 + "\nNOTA %d (%s)\n%s\n\n" % (k, partes[k]["carpeta"], txt))
            for fr in hechos[k]["fragmentos"]:
                f.write("  L%s [%s] «%s» → %s%s\n" % (
                    fr["linea"], fr["clase"], fr["texto"], fr["actividades"] or "",
                    ("  ¿%s?" % fr["pregunta"]) if fr["pregunta"] else
                    ("  (%s)" % fr["motivo"] if fr["motivo"] else "")))
            f.write("\n")
    print("Muestra para revisar (fuera del repo): %s" % _m)


if __name__ == "__main__":
    if not KEY:
        sys.exit("Sin ANTHROPIC_API_KEY en el secrets.toml local.")
    que = (sys.argv[1:] or ["A"])[0].upper()
    {"A": examen_a, "B": examen_b, "C": examen_c}[que]()
