# -*- coding: utf-8 -*-
import json, sys, tomllib, gspread
from google.oauth2.service_account import Credentials
sec = tomllib.load(open("C:/Users/diego/P1/survey_app/.streamlit/secrets.toml", "rb"))
cr = Credentials.from_service_account_info(dict(sec["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
gc = gspread.authorize(cr)
M = gc.open_by_key(sec["TIMECLOCK_SHEET_ID"]); D = gc.open_by_key("1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y")
out = {}
rg = M.values_batch_get(["Groups", "Login"])["valueRanges"]
g, lg = rg[0]["values"], rg[1]["values"]
gh = g[0]; row = next(r for r in g[1:] if r and r[0] == "cliente1")
row += [""] * (len(gh) - len(row))
out["accounting_json"] = row[gh.index("AccountingJSON")]
lh = lg[0]
out["users"] = [{k: (r + [""]*len(lh))[lh.index(k)] for k in ("User", "Name", "Role", "Active", "Group", "Email")} for r in lg[1:] if r]
names = [w.title for w in D.worksheets()]
rd = D.values_batch_get([n for n in ("Sheet1", "Absences", "Roster") if n in names])["valueRanges"]
for vr in rd:
    t = vr["range"].split("!")[0].strip("'"); v = vr.get("values", [])
    out[t + "_n"] = len(v) - 1
    if t == "Sheet1":
        h = v[0]; ui = h.index("User"); ni = h.index("Name")
        out["sheet1_helper2"] = [r for r in v[1:] if len(r) > ui and (r[ui] == "helper-2" or r[ni] == "helper 2")]
        out["sheet1_last"] = v[-3:]
    if t == "Absences":
        out["absences"] = v
    if t == "Roster":
        out["roster_helper2"] = [r for r in v[1:] if "helper-2" in r]
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 15 else f"{len(v)} items") for k, v in out.items()}, ensure_ascii=False, indent=1)[:4000])
