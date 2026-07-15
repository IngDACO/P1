"""
Banco de manuales para el agente de IA.

Los fragmentos (chunks) de cada manual se guardan en `survey_app/manuals/*.json.gz`
(`{"nombre":..., "chunks":[{"manual","seccion","page","text"}, ...]}`). Al arrancar
se cargan e indexan con **BM25 en Python puro** (sin dependencias ni APIs extra).
El agente busca los fragmentos relevantes a la pregunta y responde citando el manual.
"""
import glob
import gzip
import json
import math
import os
import re

import streamlit as st

_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "manuals")


def _tok(s) -> list:
    return re.findall(r"[a-z0-9]+", str(s).lower())


@st.cache_resource(show_spinner=False)
def _index():
    chunks = []
    for fp in sorted(glob.glob(os.path.join(_DIR, "*.json.gz"))):
        try:
            with gzip.open(fp, "rt", encoding="utf-8") as f:
                data = json.load(f)
            chunks.extend(data.get("chunks", []))
        except Exception:
            pass
    docs = [_tok(c.get("text", "")) for c in chunks]
    n = len(docs)
    df, tf_list = {}, []
    for d in docs:
        tf = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        tf_list.append(tf)
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    avgdl = (sum(len(d) for d in docs) / n) if n else 1.0
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
    return {"chunks": chunks, "tf": tf_list, "idf": idf,
            "avgdl": avgdl, "dl": [len(d) for d in docs], "n": n}


def is_available() -> bool:
    return _index()["n"] > 0


def manual_names() -> list:
    seen = []
    for c in _index()["chunks"]:
        m = c.get("manual", "")
        if m and m not in seen:
            seen.append(m)
    return seen


def search(query, k=6) -> list:
    """Top-k fragmentos por BM25 para la consulta."""
    idx = _index()
    if idx["n"] == 0:
        return []
    q = _tok(query)
    k1, b = 1.5, 0.75
    scored = []
    for i, tf in enumerate(idx["tf"]):
        s, dl = 0.0, idx["dl"][i]
        for t in q:
            f = tf.get(t, 0)
            if not f:
                continue
            s += idx["idf"].get(t, 0.0) * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / idx["avgdl"]))
        if s > 0:
            scored.append((s, i))
    scored.sort(reverse=True)
    out = []
    for s, i in scored[:k]:
        c = idx["chunks"][i]
        out.append({"manual": c.get("manual", ""), "seccion": c.get("seccion", ""),
                    "page": c.get("page", ""), "text": c.get("text", ""), "score": round(s, 2)})
    return out


def context_for(query, k=6, max_chars=4500) -> str:
    """Bloque de contexto con los fragmentos relevantes (para el prompt del agente)."""
    hits = search(query, k)
    if not hits:
        return ""
    parts, total = [], 0
    for h in hits:
        ref = "[" + str(h["manual"])
        if h["seccion"]:
            ref += f" · {h['seccion']}"
        if h["page"]:
            ref += f" · pág {h['page']}"
        ref += "]"
        block = f"{ref}\n{h['text']}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
