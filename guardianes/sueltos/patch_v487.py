# -*- coding: utf-8 -*-
"""v487: (1) las KPIs de inventario en 0, (2) los desplegables que SOBRESCRIBEN en
silencio, (3) los valores que se siguen escribiendo en español tras v469.

Todo o nada: se comprueban TODAS las anclas (exactamente una vez cada una) y se compila
antes de escribir un solo fichero. Copia previa de cada fichero en el scratchpad.
"""
import io
import os
import shutil
import warnings

RAIZ = "C:/Users/diego/P1/survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
NL = chr(10)
os.chdir(RAIZ)

HELPER = NL.join([
    "",
    "",
    "def opciones_con_actual(opciones, actual):",
    '    """(opciones, indice) para un desplegable que EDITA un valor ya guardado (v487).',
    "",
    "    ⚠️ El patron `L.index(v) if v in L else 0` SOBRESCRIBE EN SILENCIO: si el valor",
    "    guardado no esta entre las opciones —una categoria que se borro, un rol mal",
    "    tecleado en la hoja, un color que no es de la paleta— el desplegable muestra la",
    "    PRIMERA opcion y al pulsar «Guardar» esa primera opcion se escribe encima del dato",
    "    de verdad, sin que nadie lo haya elegido. En Usuarios era peor: un usuario sin rol",
    "    salia con **owner** preseleccionado.",
    "",
    "    Aqui el valor actual se ANTEPONE a las opciones y queda seleccionado, asi que",
    "    guardar sin tocar ese campo conserva lo que habia. Un valor vacio no se antepone:",
    "    no hay dato que proteger y la primera opcion es un defecto legitimo.",
    '    """',
    "    ops = list(opciones)",
    '    act = "" if actual is None else str(actual)',
    "    if act in ops:",
    "        return ops, ops.index(act)",
    "    if act.strip():",
    "        return [act] + ops, 0",
    "    return ops, 0",
    "",
])

PARCHES = [
    # ── ui_common: el helper ────────────────────────────────────────────────
    ("core/ui_common.py",
     '    return st.checkbox(texto, key=key, value=False)',
     '    return st.checkbox(texto, key=key, value=False)' + HELPER.rstrip(NL)),

    # ── inventory.py: estados con nombre + escrituras canonicas ─────────────
    ("core/inventory.py",
     'ESTADOS = ["available", "in use", "maintenance", "damaged", "written off"]',
     NL.join([
         '# ⚠️ v487: con NOMBRE, para que nadie vuelva a escribir el estado a mano. Las KPIs',
         '# de la lista buscaban "disponible"/"en_uso" y, como v469 canoniza el estado al',
         '# LEER, marcaban 0 SIEMPRE; y el alta y el mantenimiento seguian ESCRIBIENDO en',
         '# español, dejando la hoja mezclada.',
         'DISPONIBLE, EN_USO, MANTENIMIENTO, DANADO, BAJA = (',
         '    "available", "in use", "maintenance", "damaged", "written off")',
         'ESTADOS = [DISPONIBLE, EN_USO, MANTENIMIENTO, DANADO, BAJA]'])),
    ("core/inventory.py",
     '           "disponible", str(condicion or "bueno"), str(ubicacion_tipo or "bodega"),',
     '           DISPONIBLE, str(condicion or CONDICIONES[0]), str(ubicacion_tipo or UBIC_TIPOS[0]),'),
    ("core/inventory.py",
     '        campos["Status"] = "mantenimiento"',
     '        campos["Status"] = MANTENIMIENTO'),

    # ── inventory_ui.py: KPIs + los 4 desplegables del formulario ───────────
    ("core/inventory_ui.py",
     "from core import tabla",
     "from core import tabla\nfrom core import ui_common as ui"),
    ("core/inventory_ui.py",
     NL.join([
         '    c[1].metric(t("Available"), est.get("disponible", 0))',
         '    c[2].metric(t("In use"), est.get("en_uso", 0))']),
     NL.join([
         '    # ⚠️ v487: por la CONSTANTE. Con "disponible"/"en_uso" marcaban 0 SIEMPRE desde',
         '    # v469, que canoniza el estado al leer: `por_estado` trae "available"/"in use".',
         '    c[1].metric(t("Available"), est.get(INV.DISPONIBLE, 0))',
         '    c[2].metric(t("In use"), est.get(INV.EN_USO, 0))'])),
    ("core/inventory_ui.py",
     NL.join([
         '        _ci = cats.index(a.get("Category")) if a.get("Category") in cats else 0',
         '        categoria = e2.selectbox(t("Category"), cats, index=_ci)']),
     NL.join([
         '        # ⚠️ v487: los cuatro desplegables CONSERVAN el valor guardado aunque ya no',
         '        # este en la lista (una categoria borrada). Antes mostraban la primera opcion',
         '        # y «Save changes» la escribia encima, sin que nadie la eligiera.',
         '        _cats, _ci = ui.opciones_con_actual(cats, a.get("Category"))',
         '        categoria = e2.selectbox(t("Category"), _cats, index=_ci)'])),
    ("core/inventory_ui.py",
     NL.join([
         '        _ei = INV.ESTADOS.index(a.get("Status")) if a.get("Status") in INV.ESTADOS else 0',
         '        estado = e2.selectbox(t("Status"), INV.ESTADOS, index=_ei)',
         '        _cdi = INV.CONDICIONES.index(a.get("Condition")) if a.get("Condition") in INV.CONDICIONES else 0',
         '        condicion = e1.selectbox(t("Condition"), INV.CONDICIONES, index=_cdi)',
         '        _ui = INV.UBIC_TIPOS.index(a.get("LocationType")) if a.get("LocationType") in INV.UBIC_TIPOS else 0',
         '        ubic_t = e2.selectbox(t("Location (type)"), INV.UBIC_TIPOS, index=_ui)']),
     NL.join([
         '        _ests, _ei = ui.opciones_con_actual(INV.ESTADOS, a.get("Status"))',
         '        estado = e2.selectbox(t("Status"), _ests, index=_ei)',
         '        _conds, _cdi = ui.opciones_con_actual(INV.CONDICIONES, a.get("Condition"))',
         '        condicion = e1.selectbox(t("Condition"), _conds, index=_cdi)',
         '        _ubics, _ubi = ui.opciones_con_actual(INV.UBIC_TIPOS, a.get("LocationType"))',
         '        ubic_t = e2.selectbox(t("Location (type)"), _ubics, index=_ubi)'])),

    # ── catalogo_ui.py: categoria + unidad ───────────────────────────────────
    ("core/catalogo_ui.py",
     "from core import tabla",
     "from core import tabla\nfrom core import ui_common as ui"),
    ("core/catalogo_ui.py",
     NL.join([
         '        categoria = c2.selectbox(t("Category"), CAT.categorias(grupo),',
         '                                 index=max(0, CAT.categorias(grupo).index(str(it.get("Category", "")))',
         '                                           if str(it.get("Category", "")) in CAT.categorias(grupo) else 0))']),
     NL.join([
         '        # ⚠️ v487: conserva la categoria/unidad guardada aunque ya no este en la lista.',
         '        _cats, _ci = ui.opciones_con_actual(CAT.categorias(grupo), it.get("Category", ""))',
         '        categoria = c2.selectbox(t("Category"), _cats, index=_ci)'])),
    ("core/catalogo_ui.py",
     NL.join([
         '            unidad = c4.selectbox(t("Unit"), CAT.UNIDADES,',
         '                                  index=max(0, list(CAT.UNIDADES).index(str(it.get("Unit", "")))',
         '                                            if str(it.get("Unit", "")) in CAT.UNIDADES else 0))']),
     NL.join([
         '            _unis, _uni = ui.opciones_con_actual(CAT.UNIDADES, it.get("Unit", ""))',
         '            unidad = c4.selectbox(t("Unit"), _unis, index=_uni)'])),

    # ── projects_ui.py: tipo, estado manual, estado de localizacion, etiqueta ─
    ("core/projects_ui.py",
     NL.join([
         '            _tp_opts = ([_TIPO_VACIO] + P.TIPOS) if _tp_cur not in P.TIPOS else list(P.TIPOS)',
         '            tipo = e1.selectbox(t("Project type"), _tp_opts,',
         '                                index=_tp_opts.index(_tp_cur) if _tp_cur in _tp_opts else 0,']),
     NL.join([
         '            # ⚠️ v487: un tipo NO vacio que no este en la lista se conserva. Antes caia',
         '            # en «— no type —» y al guardar se BORRABA el tipo de la obra.',
         '            if _tp_cur:',
         '                _tp_opts, _tp_i = ui.opciones_con_actual(P.TIPOS, _tp_cur)',
         '            else:',
         '                _tp_opts, _tp_i = [_TIPO_VACIO] + list(P.TIPOS), 0',
         '            tipo = e1.selectbox(t("Project type"), _tp_opts,',
         '                                index=_tp_i,'])),
    ("core/projects_ui.py",
     NL.join([
         '            est_man = st.selectbox(t("Manual status (override)"), P.ESTADOS_MANUAL,',
         '                                   format_func=_etq,',
         '                                   index=P.ESTADOS_MANUAL.index(str(prj.get("ManualStatus", "")))',
         '                                   if str(prj.get("ManualStatus", "")) in P.ESTADOS_MANUAL else 0)']),
     NL.join([
         '            # ⚠️ v487: un override que no este en la lista se CONSERVA. Antes caia en «»',
         '            # y al guardar se borraba — que podia des-archivar un proyecto sin querer.',
         '            _ems, _emi = ui.opciones_con_actual(P.ESTADOS_MANUAL, prj.get("ManualStatus", ""))',
         '            est_man = st.selectbox(t("Manual status (override)"), _ems,',
         '                                   format_func=_etq, index=_emi)'])),
    ("core/projects_ui.py",
     NL.join([
         '        est = st.selectbox(t("Status"), _opts,',
         '                           index=_opts.index(_est_act) if _est_act in _opts else 0,']),
     NL.join([
         '        _opts, _est_i = ui.opciones_con_actual(_opts, _est_act)    # v487: se conserva',
         '        est = st.selectbox(t("Status"), _opts,',
         '                           index=_est_i,'])),
    ("core/projects_ui.py",
     '"tipo": tipo, "label": _TIPO_LABEL.get(tipo, tipo or "otro"),',
     '"tipo": tipo, "label": _TIPO_LABEL.get(tipo, tipo or t("other")),'),

    # ── auth_ui.py: rol y empresa ────────────────────────────────────────────
    ("core/auth_ui.py",
     NL.join([
         '            _rcur = str(u.get("Role", "") or "campo")',
         '            _nrol = _rc.selectbox(t("Role"), auth.ROLES,',
         '                                  index=auth.ROLES.index(_rcur) if _rcur in auth.ROLES else 0,']),
     NL.join([
         '            # ⚠️ v487: el defecto era "campo" —español desde v469—, que no esta en',
         '            # ROLES, asi que un usuario sin rol salia con OWNER preseleccionado y un',
         '            # «Apply role» distraido lo convertia en propietario. Ahora el defecto es',
         '            # el canonico y un rol desconocido se ENSEÑA tal cual (set_role lo rechaza).',
         '            _rcur = str(u.get("Role", "") or "field")',
         '            _rols, _ri = ui.opciones_con_actual(auth.ROLES, _rcur)',
         '            _nrol = _rc.selectbox(t("Role"), _rols,',
         '                                  index=_ri,'])),
    ("core/auth_ui.py",
     NL.join([
         '            _ngrp = _gc.selectbox(t("Company"), _gopts,',
         '                                  index=_gopts.index(_gcur) if _gcur in _gopts else 0,']),
     NL.join([
         '            _gopts, _gi = ui.opciones_con_actual(_gopts, _gcur)    # v487: se conserva',
         '            _ngrp = _gc.selectbox(t("Company"), _gopts,',
         '                                  index=_gi,'])),

    # ── roster_ui.py: color de un trabajo ────────────────────────────────────
    ("core/roster_ui.py",
     "from core import roster as R",
     "from core import roster as R\nfrom core import ui_common as ui"),
    ("core/roster_ui.py",
     NL.join([
         '                        _cur = _colinv.get(str(r.get("Color", "")).lower())',
         '                        _nombres = list(_colmap)',
         '                        _cn = e3.selectbox(t("Colour"), _nombres, key=f"tedc_{tid}",',
         '                                           index=_nombres.index(_cur) if _cur in _nombres else 0)']),
     NL.join([
         '                        # ⚠️ v487: un color que no es de la paleta se CONSERVA (antes',
         '                        # «Save changes» lo cambiaba por el primero de la paleta).',
         '                        _cur = _colinv.get(str(r.get("Color", "")).lower()) \\',
         '                            or str(r.get("Color", "")).strip()',
         '                        _nombres, _ci = ui.opciones_con_actual(list(_colmap), _cur)',
         '                        _cn = e3.selectbox(t("Colour"), _nombres, key=f"tedc_{tid}",',
         '                                           index=_ci)'])),
    ("core/roster_ui.py",
     '                                    "Color": _colmap[_cn]})',
     '                                    "Color": _colmap.get(_cn, _cn)})'),

    # ── los valores que se seguian escribiendo en español ────────────────────
    ("core/expenses.py",
     NL.join(['CATEGORIAS = ["Materials", "Tools", "Transport", "Fuel",',
              '              "Subcontractor", "Rental", "Other"]']),
     NL.join(['CATEGORIAS = ["Materials", "Tools", "Transport", "Fuel",',
              '              "Subcontractor", "Rental", "Other"]',
              '# ⚠️ v487: la categoria de una compra SIN categoria. Era "Otros" en dos sitios, y',
              '# como el canonico es "Other" la torta partia la misma categoria en DOS trozos,',
              '# los dos rotulados «Other».',
              'SIN_CATEGORIA = "Other"'])),
    ("core/expenses.py",
     '        c = str(r.get("Category", "")) or "Otros"',
     '        c = str(r.get("Category", "")) or SIN_CATEGORIA'),
    ("core/expenses.py",
     '            cat = str(r.get("Category", "")) or "Otros"',
     '            cat = str(r.get("Category", "")) or SIN_CATEGORIA'),
    ("core/orders.py",
     '                    categoria=str(r.get("Category", "")) or "Materiales",',
     '                    categoria=str(r.get("Category", "")) or E.CATEGORIAS[0],   # v487: canonico'),
    ("core/email_notify.py",
     "filename=f\"informe_admin_{(proyecto or 'proyecto').replace(' ', '_')}.pdf\")",
     "filename=f\"informe_admin_{(proyecto or 'project').replace(' ', '_')}.pdf\")"),
]


def main():
    textos = {}
    for fich, _v, _n in PARCHES:
        textos.setdefault(fich, io.open(fich, encoding="utf-8").read())
    pend = dict(textos)
    for i, (fich, viejo, nuevo) in enumerate(PARCHES, 1):
        n = pend[fich].count(viejo)
        if n != 1:
            raise SystemExit("parche %d (%s): el ancla aparece %d veces" % (i, fich, n))
        pend[fich] = pend[fich].replace(viejo, nuevo, 1)
    for fich, s in pend.items():
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(s, fich, "exec")
    copias = os.path.join(AQUI, "_bak_v487")
    os.makedirs(copias, exist_ok=True)
    for fich in pend:
        shutil.copy2(fich, os.path.join(copias, os.path.basename(fich)))
    for fich, s in pend.items():
        io.open(fich, "w", encoding="utf-8", newline="").write(s)
        print("ok", fich)


main()
