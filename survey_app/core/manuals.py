"""
Banco de manuales para el agente de IA.

Los fragmentos (chunks) de cada manual se guardan como
`{"nombre":..., "chunks":[{"manual","seccion","page","text"}, ...]}`, comprimidos
(.json.gz). Hay dos orígenes que se fusionan en un mismo índice:

  1. Pre-cargados en el repo: `survey_app/manuals/*.json.gz` (KONE, S5500).
  2. Subidos por el propietario desde la app (self-service): se guardan en Google
     Drive (carpeta 'COPEX Manuales') y se registran en la hoja `Manuales`. Al
     subir un PDF/ZIP, la app extrae el texto, lo trocea y sube el .json.gz a Drive.

Todo se indexa con **BM25 en Python puro** (sin dependencias ni APIs extra). El
agente busca los fragmentos relevantes a la pregunta y responde citando el manual.
"""
import glob
import gzip
import io
import json
import math
import os
import re
import zipfile
from datetime import datetime

import streamlit as st
from core import clock

_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "manuals")

_SHEET   = "Manuales"
_HEADERS = ["ID", "Nombre", "DriveID", "NumFrags", "Fecha", "SubidoPor"]
_FOLDER_NAME = "COPEX Manuales"
_WORDS_PER_CHUNK = 180


def _tok(s) -> list:
    return re.findall(r"[a-z0-9]+", str(s).lower())


# ── Manuales alojados en Drive (registro en la hoja `Manuales`) ───────────
def storage_available() -> bool:
    """El almacén de subidas (Drive + hoja) está configurado."""
    try:
        from core import drive_store, timeclock
        return drive_store.is_configured() and timeclock._secrets_present()
    except Exception:
        return False


def _index_ws():
    from core import timeclock
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(_SHEET, tuple(_HEADERS))
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _drive_records() -> list:
    """Filas de la hoja `Manuales` (cacheadas)."""
    w = _index_ws()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _drive_chunks() -> list:
    """Descarga y junta los chunks de todos los manuales alojados en Drive."""
    if not storage_available():
        return []
    from core import drive_store
    out = []
    for rec in _drive_records():
        did = rec.get("DriveID", "")
        if not did:
            continue
        try:
            raw = drive_store.download(did)
            data = json.loads(gzip.decompress(raw).decode("utf-8"))
            out.extend(data.get("chunks", []))
        except Exception:
            pass
    return out


@st.cache_resource(show_spinner=False)
def _index():
    chunks = []
    # 1) Pre-cargados en el repo
    for fp in sorted(glob.glob(os.path.join(_DIR, "*.json.gz"))):
        try:
            with gzip.open(fp, "rt", encoding="utf-8") as f:
                data = json.load(f)
            chunks.extend(data.get("chunks", []))
        except Exception:
            pass
    # 2) Subidos por el propietario (Drive)
    try:
        chunks.extend(_drive_chunks())
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


# ══════════════════════════════════════════════════════════════════════
# EXTRACCIÓN / TROCEO (para subidas self-service)
# ══════════════════════════════════════════════════════════════════════
def _extract_chunks(pdf_bytes, nombre, seccion_fija=""):
    """Trocea un PDF en fragmentos ~`_WORDS_PER_CHUNK` palabras, con página y sección."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    chunks, seccion = [], seccion_fija
    for pno, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if not txt.strip():
            continue
        # Heurística de sección: primera línea "título" (corta y en mayúsculas)
        if not seccion_fija:
            for line in txt.splitlines():
                s = line.strip()
                if 3 <= len(s) <= 60 and s == s.upper() and any(ch.isalpha() for ch in s):
                    seccion = s.title()
                    break
        words = txt.split()
        for i in range(0, len(words), _WORDS_PER_CHUNK):
            frag = " ".join(words[i:i + _WORDS_PER_CHUNK]).strip()
            if len(frag) < 40:
                continue
            chunks.append({"manual": nombre, "seccion": seccion, "page": pno, "text": frag})
    return chunks


def _chunks_from_upload(file_bytes, filename, nombre):
    """Extrae chunks de un PDF o de un ZIP con varios PDFs."""
    if filename.lower().endswith(".zip"):
        chunks = []
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            for n in z.namelist():
                if n.lower().endswith(".pdf") and "__MACOSX" not in n:
                    sub = os.path.splitext(os.path.basename(n))[0]
                    try:
                        chunks.extend(_extract_chunks(z.read(n), nombre, seccion_fija=sub))
                    except Exception:
                        pass
        return chunks
    return _extract_chunks(file_bytes, nombre)


# ══════════════════════════════════════════════════════════════════════
# GESTIÓN (panel del propietario)
# ══════════════════════════════════════════════════════════════════════
def list_uploaded() -> list:
    """Manuales subidos por el propietario (los de Drive), para el panel de gestión."""
    return _drive_records()


def repo_manual_names() -> list:
    """Nombres de los manuales pre-cargados en el repo (solo lectura)."""
    seen = []
    for fp in sorted(glob.glob(os.path.join(_DIR, "*.json.gz"))):
        try:
            with gzip.open(fp, "rt", encoding="utf-8") as f:
                nm = json.load(f).get("nombre", "")
            if nm and nm not in seen:
                seen.append(nm)
        except Exception:
            pass
    return seen


def _refresh():
    """Invalida los cachés para que el índice se reconstruya con el cambio."""
    for fn in (_drive_records, _index):
        try:
            fn.clear()
        except Exception:
            pass


def add_manual(file_bytes, filename, nombre, subido_por=""):
    """Extrae, trocea y aloja un manual en Drive; lo registra en la hoja.
    Devuelve (num_fragmentos, None) si va bien, o (0, mensaje_error)."""
    if not storage_available():
        return 0, "El almacenamiento (Drive + hoja) no está configurado."
    nombre = (nombre or os.path.splitext(filename)[0]).strip()
    try:
        chunks = _chunks_from_upload(file_bytes, filename, nombre)
    except Exception as e:
        return 0, f"No se pudo leer el archivo: {e}"
    if not chunks:
        return 0, "No se extrajo texto (¿PDF escaneado/imagen?). Súbelo con OCR aplicado."
    try:
        from core import drive_store
        payload = gzip.compress(json.dumps(
            {"nombre": nombre, "chunks": chunks}, ensure_ascii=False).encode("utf-8"))
        mid = clock.now().strftime("MAN-%Y%m%d%H%M%S")
        drive_id = drive_store.upload_to(
            drive_store.folder(_FOLDER_NAME), f"{mid}.json.gz", payload, "application/gzip")
        w = _index_ws()
        if w is None:
            return 0, "No se pudo abrir la hoja de manuales."
        w.append_row([mid, nombre, drive_id, str(len(chunks)),
                      clock.now().strftime("%Y-%m-%d %H:%M"), subido_por],
                     value_input_option="RAW")
    except Exception as e:
        return 0, f"No se pudo guardar el manual: {e}"
    _refresh()
    return len(chunks), None


def delete_manual(manual_id) -> bool:
    """Elimina un manual subido (archivo en Drive + fila en la hoja)."""
    w = _index_ws()
    if w is None:
        return False
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return False
    for i, rec in enumerate(recs):
        if str(rec.get("ID", "")) == str(manual_id):
            did = rec.get("DriveID", "")
            if did:
                try:
                    from core import drive_store
                    drive_store.delete(did)
                except Exception:
                    pass
            try:
                w.delete_rows(i + 2)  # +1 encabezado, +1 base-1
            except Exception:
                return False
            _refresh()
            return True
    return False
