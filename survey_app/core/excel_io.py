"""
Exportar e importar la matriz SURVEY como Excel.
"""
import io
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

SURVEY_COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]

# ── Exportar ─────────────────────────────────────────────────
def export_survey_excel(df: pd.DataFrame, project_info: dict = None) -> bytes:
    """
    Genera un Excel con:
      - Hoja 'SURVEY'  : la matriz editable
      - Hoja 'INFO'    : parámetros del proyecto (opcional)
    Retorna bytes del archivo.
    """
    wb = openpyxl.Workbook()

    # ── Hoja SURVEY ──
    ws = wb.active
    ws.title = "SURVEY"

    header_fill  = PatternFill("solid", fgColor="1A3A5C")
    header_font  = Font(color="FFFFFF", bold=True, name="Calibri", size=11)
    normal_font  = Font(name="Calibri", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border  = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    # Título
    ws.merge_cells("A1:G1")
    ws["A1"] = "SURVEY ANALYZER — Matriz de medidas en campo (mm)"
    ws["A1"].font = Font(color="FFFFFF", bold=True, name="Calibri", size=12)
    ws["A1"].fill = header_fill
    ws["A1"].alignment = center_align

    # Encabezados columnas
    headers = ["Parada"] + SURVEY_COLS
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.font  = header_font
        cell.fill  = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Datos
    for row_idx, (_, row) in enumerate(df.iterrows(), start=3):
        ws.cell(row=row_idx, column=1, value=row_idx - 2).font = Font(bold=True, name="Calibri", size=10)
        ws.cell(row=row_idx, column=1).alignment = center_align
        ws.cell(row=row_idx, column=1).border = thin_border
        for col_idx, col in enumerate(SURVEY_COLS, start=2):
            cell = ws.cell(row=row_idx, column=col_idx, value=float(row[col]))
            cell.font      = normal_font
            cell.alignment = center_align
            cell.border    = thin_border

    # Ancho de columnas
    ws.column_dimensions["A"].width = 10
    for col_letter in ["B","C","D","E","F","G"]:
        ws.column_dimensions[col_letter].width = 14

    # ── Hoja INFO (parámetros) ──
    if project_info:
        ws2 = wb.create_sheet("INFO")
        ws2.merge_cells("A1:B1")
        ws2["A1"] = "Parámetros del proyecto"
        ws2["A1"].font = Font(color="FFFFFF", bold=True, name="Calibri", size=11)
        ws2["A1"].fill = header_fill
        ws2["A1"].alignment = center_align

        ws2.cell(row=2, column=1, value="Parámetro").font = header_font
        ws2.cell(row=2, column=1).fill  = PatternFill("solid", fgColor="2E6DA4")
        ws2.cell(row=2, column=2, value="Valor").font = header_font
        ws2.cell(row=2, column=2).fill  = PatternFill("solid", fgColor="2E6DA4")

        row_idx = 3
        for k, v in project_info.items():
            if v is None:
                continue
            ws2.cell(row=row_idx, column=1, value=str(k)).font = normal_font
            ws2.cell(row=row_idx, column=2, value=str(round(v, 3) if isinstance(v, float) else v)).font = normal_font
            ws2.cell(row=row_idx, column=1).border = thin_border
            ws2.cell(row=row_idx, column=2).border = thin_border
            row_idx += 1

        ws2.column_dimensions["A"].width = 20
        ws2.column_dimensions["B"].width = 20

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ── Importar ─────────────────────────────────────────────────
def import_survey_excel(file) -> pd.DataFrame:
    """
    Lee un Excel generado por export_survey_excel y retorna el DataFrame.
    file: path string o file-like object.
    """
    df = pd.read_excel(file, sheet_name="SURVEY", header=1, usecols="A:G")
    df.columns = ["Parada"] + SURVEY_COLS
    df = df.drop(columns=["Parada"])
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return df
