import os, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def estilizar_excel_pro(ruta_xlsx):
    if not os.path.exists(ruta_xlsx): return
    wb = openpyxl.load_workbook(ruta_xlsx)
    fill_hdr = PatternFill("solid", fgColor="1F4E78")
    fill_par = PatternFill("solid", fgColor="F9FBFD")
    font_hdr = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_cel = Font(name="Calibri", size=10, color="111111")
    borde_fino = Border(
        left=Side(style="thin", color="D9D9D9"), right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"), bottom=Side(style="thin", color="D9D9D9")
    )

    for ws in wb.worksheets:
        max_r, max_c = ws.max_row, ws.max_column
        if max_r < 1 or max_c < 1: continue
        ws.views.sheetView[0].showGridLines = True
        if max_r > 1:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = f"A1:{get_column_letter(max_c)}{max_r}"

        ws.row_dimensions[1].height = 30
        es_moneda = {}
        anchos = {}

        for c in range(1, max_c + 1):
            cel_h = ws.cell(1, c)
            txt_h = str(cel_h.value or "").strip()
            cel_h.fill = fill_hdr
            cel_h.font = font_hdr
            cel_h.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cel_h.border = borde_fino
            anchos[c] = max(len(txt_h) + 6, 14)
            es_moneda[c] = any(k in txt_h.upper() for k in ("PRECIO", "TOTAL", "SUBTOTAL", "MONTO", "VALOR"))

        for r in range(2, max_r + 1):
            max_lineas = 1
            for c in range(1, max_c + 1):
                cel = ws.cell(r, c)
                v = cel.value
                cel.font = font_cel
                cel.border = borde_fino
                if r % 2 == 0: cel.fill = fill_par
                if es_moneda[c] and isinstance(v, (int, float)):
                    cel.number_format = '"$"#,##0'
                    cel.alignment = Alignment(horizontal="right", vertical="center")
                    largo = len(f"${v:,.0f}") + 4
                elif isinstance(v, (int, float)):
                    cel.alignment = Alignment(horizontal="center", vertical="center")
                    largo = len(str(v)) + 4
                else:
                    s = str(v or "").strip()
                    largo = max((len(l) for l in s.splitlines()), default=0) + 4
                    est_lin = max(1, (len(s) // 55) + s.count("\n") + 1)
                    if est_lin > max_lineas: max_lineas = min(est_lin, 4)
                    cel.alignment = Alignment(horizontal="left", vertical="center", wrap_text=(len(s) > 50 or "\n" in s))
                if largo > anchos[c]:
                    anchos[c] = min(largo, 58)
            ws.row_dimensions[r].height = max(22, max_lineas * 16)

        for c, w in anchos.items():
            ws.column_dimensions[get_column_letter(c)].width = max(w, 14)

    wb.save(ruta_xlsx)
