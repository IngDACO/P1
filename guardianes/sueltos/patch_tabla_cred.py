# -*- coding: utf-8 -*-
"""La tabla de credenciales, ordenada para un movil.

Medido: son **6 columnas** en una pantalla que el campo abre desde el telefono. A
375 px eso deja ~60 px por columna, y glide **recorta sin poner puntos suspensivos**
(v408), asi que el numero que esa persona tiene que enseñar en obra se ve a medias
**sin avisar**.

⚠️ La cura es la de v408/v398: **no encoger, PRIORIZAR**. No se oculta ninguna
columna —siguen las seis— pero las que se miran primero van primero:
   Tipo · Estado · Vence · Number · Clase · Issued
Y `Tipo` va **anclado**: es la identidad, y sin anclarla se escapa por la izquierda en
cuanto alguien se desplaza a ver la fecha, que es justo cuando hace falta saber DE QUE
credencial se esta hablando.

⚠️ Se aplica a la tabla UNICA, no a una copia para el campo: dos definiciones de la
misma tabla divergen (la leccion de los cinco `_num` de v323).
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\auth_ui.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''        st.dataframe(pd.DataFrame([{
            "Tipo": r.get("Type"), "Number": r.get("Number"), "Clase": r.get("Class"),
            "Issued": r.get("IssueDate") or "—", "Vence": r.get("ExpiryDate") or "—",
            "Estado": C.status_label(r.get("ExpiryDate")),
        } for r in creds]), hide_index=True, width="stretch", column_config=tabla.cfg())
'''

NUEVO = '''        # ⚠️ v478 · ORDEN pensado para el móvil: lo que se mira primero, primero
        # (Tipo · Estado · Vence), y lo de contexto detrás. No se oculta ninguna: es
        # priorizar, no encoger — a 375 px encoger recorta el texto SIN avisar (v408).
        st.dataframe(pd.DataFrame([{
            "Tipo": r.get("Type"), "Estado": C.status_label(r.get("ExpiryDate")),
            "Vence": r.get("ExpiryDate") or "—", "Number": r.get("Number"),
            "Clase": r.get("Class"), "Issued": r.get("IssueDate") or "—",
        } for r in creds]), hide_index=True, width="stretch",
            # ⚠️ `Tipo` ANCLADA: es la identidad, y sin anclar se escapa por la
            # izquierda justo cuando alguien se desplaza a mirar la fecha.
            column_config=tabla.cfg(extra={"Tipo": st.column_config.TextColumn(
                t("Type"), pinned=True)}))
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/auth_ui.py: tabla de credenciales priorizada + Tipo anclada")
