# -*- coding: utf-8 -*-
"""Batería de roturas de v690. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v690"
TOPE_S = 400
CL = "core/clientes.py"
CU = "core/clientes_ui.py"
QM = "core/quotes.py"
IU = "core/invoices_ui.py"
PU = "core/projects_ui.py"

ROTURAS = [
    ("⚠️ el teléfono admite letras otra vez", CL,
     [("    return not s or (bool(re.fullmatch(", "    return True or (bool(re.fullmatch(")]),
    ("crear un cliente no mira el teléfono", CL,
     [("    if not telefono_valido(telefono):                       # v690 · H1\n        return False, _aviso_telefono()\n",
       "")]),
    ("editar la ficha no mira el teléfono", CL,
     [('    if "Phone" in fields and not telefono_valido(fields.get("Phone")):       # v690 · H1\n'
       "        return False, _aviso_telefono()\n", "")]),
    ("⚠️ renombrar a un nombre que ya tiene otro cliente", CL,
     [('                and _norm(r.get("Name")) == _norm(nuevo)):', "                and False):")]),
    ("renombrar un cliente de OTRA empresa", CL,
     [('    if not f or str(f.get("Group", "")) != str(grupo):', "    if not f:")]),
    ("⚠️ renombrar no toca sus obras", CL,
     [('                _ok_p, _ = P.update_project(str(p.get("ID", "")), {"Client": nuevo, "ClientID": cid})',
       "                _ok_p = False")]),
    ("la obra que casaba por el nombre viejo no se enlaza por ID", CL,
     [('{"Client": nuevo, "ClientID": cid})', '{"Client": nuevo})')]),
    ("renombrar no toca sus borradores", CL,
     [("        n_borr = Q.renombrar_cliente_borradores(grupo, cid, nuevo)", "        n_borr = 0")]),
    ("⚠️ los borradores renombran también las ENVIADAS", QM,
     [('            and estado_de(r) == BORRADOR and str(r.get("ClientName", "")) != str(nombre)]',
       '            and str(r.get("ClientName", "")) != str(nombre)]')]),
    ("lo abierto cuenta versiones viejas como esperando respuesta", CL,
     [("        _esp = [x for x in Q.vistas(_qs).values() if x in (Q.ENVIADA, Q.VENCIDA)]",
       "        _esp = [x for x in _qs if Q.estado_de(x) in (Q.ENVIADA, Q.VENCIDA)]")]),
    ("lo abierto cuenta facturas anuladas", CL,
     [('                    if str(f.get("Status", "")).lower() != "anulada")', "                    )")]),
    ("⚠️ la ficha no deja corregir el nombre", CU,
     [("                      if cid else disp)", "                      if False else disp)")]),
    ("«Save record» no renombra", CU,
     [('                if ok and " ".join(str(_nom_f or "").split()) != str(f.get("Name", "") or ""):',
       "                if False:")]),
    ("tras renombrar la ficha no queda abierta por su ID", CU,
     [('                    st.session_state["_cli_open"] = cid       # v690', "                    pass       # v690")]),
    ("⚠️ archivar con cosas abiertas sin confirmar", CU,
     [("                             if _ab else True)", "                             if False else True)")]),
    ("archivar no dice lo que tiene abierto", CU,
     [("                    if _ab:\n", "                    if False:\n")]),
    ("el aviso del archivado vuelve a mentir", CU,
     [('"quotes and invoices. A client with jobs still shows in the list through them, marked "',
       '"quotes and invoices."')]),
    ("⚠️ la ficha no enseña sus cotizaciones", CU,
     [("        _cotizaciones_del_cliente(grupo, f, cid)", "        pass")]),
    ("las cotizaciones de la ficha van por versión, no por trato", CU,
     [("        _tratos = sorted(Q._por_trato(_qs).values(),", "        _tratos = sorted([[x] for x in _qs],")]),
    ("«New quote for this client» para un cliente archivado", CU,
     [('    if str(f.get("Active", "SI")).upper() not in ("NO", "FALSE", "0"):\n        if st.button(',
       "    if True:\n        if st.button(")]),
    ("«New quote for this client» sin el cliente elegido", CU,
     [('            st.session_state["cot_new_cli"] = str(f.get("Name", ""))', "            pass")]),
    ("⚠️ la factura de una obra cotizada no ofrece sus líneas ni un depósito", IU,
     [('        if _cot1 and I.por_certificar(_pid1, grupo, _p1)["pendiente"] > 0:', "        if False:")]),
    ("se ofrecen las líneas con la obra ya facturada en parte", IU,
     # v702 · re-anclada: la condición es ahora «nada facturado, o solo un depósito» (`_solo_dep`, D3 del ciclo 7)
     [("            if I.es_cotizada(_pid1) and _solo_dep:",
       "            if I.es_cotizada(_pid1):")]),
    ("las líneas de la cotización con su COSTE, no su precio", IU,
     [('                             "Importe": round(_num(_l.get("precio_total")), 2),',
       '                             "Importe": round(_num(_l.get("costo_total")), 2),')]),
    ("el depósito es el total, no el %", IU,
     [('                         "Importe": round(pend * _dep / 100.0, 2),', '                         "Importe": round(pend, 2),')]),
    ("⚠️ «My projects» no enseña el contacto del cliente", PU,
     [("    _contacto_cliente_campo(prj)                     # v690", "    pass                     # v690")]),
    ("el nombre del contacto sin escapar (HTML)", PU,
     [("        _partes.append(_h.escape(_nom))", "        _partes.append(_nom)")]),
    ("sin ficha enlazada se adivina", PU,
     [("    if not _cid:\n        return\n    try:\n        from core import clientes as _CL",
       "    if False:\n        return\n    try:\n        from core import clientes as _CL")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CL,
           [('    """Lo que un cliente tiene ABIERTO, en frases (v690, ciclo 5 H18):',
             '    """Lo que un cliente tiene ABIERTO, en frases (v690, ciclo 5 H18 · control):')])


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
