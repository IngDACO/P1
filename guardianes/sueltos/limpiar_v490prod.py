# -*- coding: utf-8 -*-
import json, sys, tomllib, gspread
from google.oauth2.service_account import Credentials
sec = tomllib.load(open("C:/Users/diego/P1/survey_app/.streamlit/secrets.toml", "rb"))
gc = gspread.authorize(Credentials.from_service_account_info(dict(sec["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
M = gc.open_by_key(sec["TIMECLOCK_SHEET_ID"]); D = gc.open_by_key("1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y")
SIMULAR = "--real" not in sys.argv
plan = []
# 1) fichaje de helper 2
ws = D.worksheet("Sheet1"); v = ws.get_all_values(); h = v[0]
idx = [i + 1 for i, r in enumerate(v) if i > 0
       and (r + [""] * len(h))[h.index("User")] == "helper 2"
       and r[h.index("Clock In")] == "2026-09-15 07:00:00"
       and r[h.index("Clock Out")] == "2026-09-15 15:00:00"
       and r[h.index("Type")] == "general" and r[h.index("Group")] == "cliente1"]
assert len(idx) == 1, idx
plan.append(("Sheet1", idx[0], v[idx[0] - 1]))
# 2) ausencia AUS-0001
wa = D.worksheet("Absences"); va = wa.get_all_values(); ha = va[0]
ia = [i + 1 for i, r in enumerate(va) if i > 0 and r[ha.index("ID")] == "AUS-0001"
      and r[ha.index("Reason")] == "ZZ PRUEBA v490 - borrar"]
assert len(ia) == 1, ia
plan.append(("Absences", ia[0], va[ia[0] - 1]))
# 3) emparejado en Groups.AccountingJSON (antes: vacío)
wg = M.worksheet("Groups"); vg = wg.get_all_values(); hg = vg[0]
ig = [i + 1 for i, r in enumerate(vg) if i > 0 and r[0] == "cliente1"]
assert len(ig) == 1
col = hg.index("AccountingJSON") + 1
actual = json.loads(wg.cell(ig[0], col).value or "{}")
import os; os.chdir("C:/Users/diego/P1/survey_app"); sys.path.insert(0, ".")
from core import contable as C
_fab = dict(C._DEFECTOS); _fab["cuentas"] = C._CUENTAS_DEFECTO; _fab["conceptos"] = C._CONCEPTOS_DEFECTO
_n = lambda d: json.loads(json.dumps(d, sort_keys=True))
_resto = {k: v for k, v in actual.items() if k != "xero_empleados"}
assert set(_resto) == set(_fab) and all(_n(_resto[k]) == _n(_fab[k]) for k in _resto), _resto
assert set(actual["xero_empleados"]["map"]) == {"helper 2"}, actual
plan.append(("Groups.AccountingJSON", (ig[0], col), actual))
for p in plan:
    print("PLAN", p)
if SIMULAR:
    print("simulación: nada escrito"); sys.exit(0)
ws.delete_rows(idx[0])
wa.delete_rows(ia[0])
wg.update_cell(ig[0], col, "")
print("borrado")
