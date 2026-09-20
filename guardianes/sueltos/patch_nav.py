# -*- coding: utf-8 -*-
"""La seccion nueva va al FINAL de cada nav, no en medio.

⚠️ No es estetica: `verif_v297` afirma que **las secciones que se añadan van DESPUES**,
para no reordenarle la nav a quien ya la tenia — y yo meti `biblioteca` en el medio de
la del CAMPO (delante de «Mis credenciales») y de la del admin (delante de «Contactos»).
Se cumple la regla en vez de relajar el guardian (criterio de v461), que es ademas como
v430 añadio «ausencias»: al final.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\home_ui.py"
s = io.open(P, encoding="utf-8").read()

BIB_ADMIN = '    ("biblioteca",    ":material/menu_book: Library"),\n'
BIB_CAMPO = '    ("biblioteca",   ":material/menu_book: Library"),\n'

# ── admin: de delante de «Contactos» al final de la lista ────────────────────
CONTACTOS = '    ("contactos",     ":material/contacts: Contacts"),\n]\n'
if s.count(BIB_ADMIN) != 1 or s.count(CONTACTOS) != 1:
    raise SystemExit("anclas admin: %d / %d" % (s.count(BIB_ADMIN), s.count(CONTACTOS)))
s = s.replace(BIB_ADMIN, "")
s = s.replace(CONTACTOS,
              '    ("contactos",     ":material/contacts: Contacts"),\n'
              '    # v472 · al FINAL a proposito: una seccion nueva no le reordena la nav\n'
              '    # a quien ya la tenia (lo que afirma `verif_v297`, y como entro\n'
              '    # «ausencias» en v430).\n'
              + BIB_ADMIN + ']\n')

# ── campo: de delante de «Mis credenciales» al final, tras «ausencias» ───────
AUSENCIAS = '    ("ausencias",    ":material/event_busy: My absences"),\n'
if s.count(BIB_CAMPO) != 1 or s.count(AUSENCIAS) != 1:
    raise SystemExit("anclas campo: %d / %d" % (s.count(BIB_CAMPO), s.count(AUSENCIAS)))
s = s.replace(BIB_CAMPO, "")
s = s.replace(AUSENCIAS, AUSENCIAS + '    # v472 · igual que arriba: al final, sin mover lo que ya usaba.\n'
              + BIB_CAMPO)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/home_ui.py: `biblioteca` al final en admin y campo (en owner ya lo estaba)")
