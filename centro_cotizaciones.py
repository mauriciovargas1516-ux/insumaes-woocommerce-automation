import os, io, re, sys, time, json, sqlite3, dropbox, openpyxl
import pandas as pd
from datetime import datetime

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

RUTA_DB = os.path.expanduser("~/boveda_cotizaciones_insumaes.db")
RUTA_PLANTILLA = os.path.expanduser("~/Plantilla_cotizaciones_INSUMAES.xlsx")

def conectar_dbx():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    return dropbox.Dropbox(app_key=env["DROPBOX_APP_KEY"], app_secret=env["DROPBOX_APP_SECRET"], oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"])

def inicializar_sqlite():
    con = sqlite3.connect(RUTA_DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Cotizaciones (Numero_Cotizacion TEXT PRIMARY KEY, Carpeta_Mes TEXT, Fecha_Emision TEXT, Rut_Cliente TEXT, Nombre_Cliente TEXT, Telefono TEXT, Email TEXT, Forma_Pago TEXT, Items_Count INTEGER, Subtotal_Neto REAL, Total_Pagar REAL, Alerta_Formula TEXT, Resumen_Items TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS Detalle_Cotizaciones (Id INTEGER PRIMARY KEY AUTOINCREMENT, Numero_Cotizacion TEXT, Carpeta_Mes TEXT, Nombre_Cliente TEXT, Fila INTEGER, Descripcion TEXT, Cantidad REAL, Precio_Unitario REAL, Descuento_Pct REAL, Subtotal_Linea REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS Clientes_Ciudad (Id TEXT PRIMARY KEY, Ciudad TEXT, Nombre_Hoja_Cliente TEXT, Rut TEXT, Telefono TEXT, Email TEXT, Datos_Resumen TEXT, Fecha_Mod TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS Cuentas_Por_Cobrar (Id TEXT PRIMARY KEY, Origen_Hoja TEXT, Cliente_O_Rut TEXT, Detalle_Fila TEXT, Monto_Detectado REAL, Fecha_Archivo TEXT)")
    con.commit()
    return con

def reparar_plantilla_dropbox(dbx=None):
    if dbx is None: dbx = conectar_dbx()
    print("\n🔧 Revisando '/Plantilla cotizaciones INSUMAES.xlsx' en Dropbox...", flush=True)
    _, res = dbx.files_download("/Plantilla cotizaciones INSUMAES.xlsx")
    open(RUTA_PLANTILLA, "wb").write(res.content)
    wb = openpyxl.load_workbook(RUTA_PLANTILLA)
    ws = wb["Hoja1"]
    rep = []
    for r in range(14, 27):
        v = ws[f"J{r}"].value
        if not v or "IF(" not in str(v).upper():
            ws[f"J{r}"].value = f'=IF(G{r}="", "", H{r}*G{r}-(G{r}*((H{r}*I{r})/100)))'
            rep.append(f"J{r}")
    if rep:
        wb.save(RUTA_PLANTILLA)
        dbx.files_upload(open(RUTA_PLANTILLA, "rb").read(), "/Plantilla cotizaciones INSUMAES.xlsx", mode=dropbox.files.WriteMode.overwrite)
        print(f"  ✅ ¡Fórmulas reparadas en {', '.join(rep)} y actualizadas en Dropbox!", flush=True)
    else:
        print("  ✅ Fórmulas J14:J26 de la plantilla 100% sanas.", flush=True)

def _num(v):
    if v is None or v == "": return 0.0
    if isinstance(v, (int, float)): return float(v)
    s = re.sub(r"[^\d.,-]", "", str(v)).replace(".", "").replace(",", ".")
    try: return float(s)
    except Exception: return 0.0

def _der(ws, fila, c1, c2):
    for c in range(c1, c2 + 1):
        v = ws.cell(fila, c).value
        if v is not None and str(v).strip() != "": return str(v).strip()
    return ""

def analizar_cot(raw_b, nom_f, mes):
    wb_f = openpyxl.load_workbook(io.BytesIO(raw_b), data_only=False)
    ws_f = wb_f["Hoja1"] if "Hoja1" in wb_f.sheetnames else wb_f.active
    wb_v = openpyxl.load_workbook(io.BytesIO(raw_b), data_only=True)
    ws_v = wb_v["Hoja1"] if "Hoja1" in wb_v.sheetnames else wb_v.active
    nc = os.path.splitext(nom_f)[0].strip()
    cli = _der(ws_v, 8, 3, 7) or "SIN NOMBRE"
    tel, em = _der(ws_v, 9, 3, 7), _der(ws_v, 10, 3, 7)
    fe, fp, rut = _der(ws_v, 8, 9, 11), _der(ws_v, 9, 9, 11), _der(ws_v, 10, 9, 11)
    for col_f in ("I8", "J8"):
        if isinstance(ws_v[col_f].value, datetime): fe = ws_v[col_f].value.strftime("%d-%m-%Y")
    items, neto, sin_f = [], 0.0, []
    for r in range(14, 27):
        d = _der(ws_v, r, 2, 6)
        c, pu, dp = _num(ws_v[f"G{r}"].value), _num(ws_v[f"H{r}"].value), _num(ws_v[f"I{r}"].value)
        if d and c > 0:
            sl = round(c * pu * (1.0 - (dp / 100.0)))
            neto += sl
            items.append((r, d, c, pu, dp, sl))
            if not ws_f[f"J{r}"].value: sin_f.append(f"F{r}")
    al = f"⚠️ Sin fórmula: {','.join(sin_f)}" if sin_f else "✅ OK"
    res = " | ".join(f"{int(c)}x {d[:25]}" for _, d, c, _, _, _ in items)
    return {"num": nc, "mes": mes, "fecha": str(fe)[:16], "rut": rut, "cli": cli, "tel": tel, "em": em, "fp": fp, "n": len(items), "neto": neto, "tot": round(neto * 1.19), "al": al, "res": res, "items": items}

def sincronizar_cotizaciones_dropbox():
    dbx = conectar_dbx()
    reparar_plantilla_dropbox(dbx)
    con = inicializar_sqlite()
    cur = con.cursor()
    ya = {r[0] for r in cur.execute("SELECT Numero_Cotizacion FROM Cotizaciones").fetchall()}
    print("\n📂 Escaneando '/COTIZACIONES INSUMAES' en Dropbox...", flush=True)
    carpetas = [e for e in dbx.files_list_folder("/COTIZACIONES INSUMAES").entries if isinstance(e, dropbox.files.FolderMetadata)]
    nuevas = 0
    for carp in sorted(carpetas, key=lambda x: x.name):
        rm = dbx.files_list_folder(carp.path_lower)
        archs = list(rm.entries)
        while rm.has_more: rm = dbx.files_list_folder_continue(rm.cursor); archs.extend(rm.entries)
        excs = [f for f in archs if isinstance(f, dropbox.files.FileMetadata) and f.name.lower().endswith(".xlsx") and not f.name.startswith("~$")]
        print(f"   📁 {carp.name:<22} : {len(excs)} cotizaciones (.xlsx)", flush=True)
        for fm in excs:
            nid = os.path.splitext(fm.name)[0].strip()
            if nid in ya: continue
            try:
                _, rp = dbx.files_download(fm.path_lower)
                d = analizar_cot(rp.content, fm.name, carp.name)
                cur.execute("INSERT OR REPLACE INTO Cotizaciones VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (d["num"], d["mes"], d["fecha"], d["rut"], d["cli"], d["tel"], d["em"], d["fp"], d["n"], d["neto"], d["tot"], d["al"], d["res"]))
                for fl, ds, ct, pu, dp, sl in d["items"]:
                    cur.execute("INSERT INTO Detalle_Cotizaciones (Numero_Cotizacion,Carpeta_Mes,Nombre_Cliente,Fila,Descripcion,Cantidad,Precio_Unitario,Descuento_Pct,Subtotal_Linea) VALUES (?,?,?,?,?,?,?,?,?)", (d["num"], d["mes"], d["cli"], fl, ds, ct, pu, dp, sl))
                nuevas += 1
            except Exception: pass
        con.commit()
    print(f"✅ ¡Bóveda de Cotizaciones actualizada! ({nuevas} nuevas agregadas hoy).", flush=True)


def indexar_cuentas_por_cobrar(dbx=None, con=None):
    cerrar = False
    if dbx is None: dbx = conectar_dbx()
    if con is None: con = inicializar_sqlite(); cerrar = True
    cur = con.cursor()
    cur.execute("DELETE FROM Cuentas_Por_Cobrar")
    archivos_obj = [
        ("/Compras L-Angel/Cuentas por Cobrar.xlsx", "CUENTAS_POR_COBRAR"),
        ("/Compras L-Angel/Base-datos-clientes.xlsx", "BASE_DATOS_CLIENTES")
    ]
    tot = 0
    for ruta_dbx, pref in archivos_obj:
        try:
            md, rp = dbx.files_download(ruta_dbx)
            f_mod = md.client_modified.strftime("%d-%m-%Y %H:%M")
            wb = openpyxl.load_workbook(io.BytesIO(rp.content), read_only=True, data_only=True)
            for h_nom in wb.sheetnames:
                ws = wb[h_nom]
                for r_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=500, max_col=15, values_only=True), 1):
                    celdas = [str(v).strip() for v in row if v is not None and str(v).strip() != ""]
                    if not celdas: continue
                    lin = " | ".join(celdas)
                    if r_idx == 1 and any(k in lin.upper() for k in ("RUT", "CLIENTE", "FACTURA", "MONTO", "SALDO")): continue
                    nums = [float(v) for v in row if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 100]
                    monto = max(nums) if nums else 0.0
                    cur.execute("INSERT OR REPLACE INTO Cuentas_Por_Cobrar VALUES (?,?,?,?,?,?)",
                                (f"{pref}::{h_nom}::F{r_idx}", f"{pref} ({h_nom})", celdas[0][:60], lin[:450], monto, f_mod))
                    tot += 1
            wb.close()
            print(f"   ✅ [SOLO LECTURA] '{os.path.basename(ruta_dbx)}' leído sin tocar el original ({tot} filas).", flush=True)
        except Exception as e:
            print(f"   ⚠️ Aviso al leer {ruta_dbx}: {e}", flush=True)
    con.commit()
    if cerrar: con.close()
    return tot

def indexar_libros_clientes_ciudades():
    dbx = conectar_dbx()
    con = inicializar_sqlite()
    cur = con.cursor()
    print("\n🌎 Escaneando todos los 'Libro de Clientes [Ciudad].xlsx' en '/Compras L-Angel'...", flush=True)
    rm = dbx.files_list_folder("/Compras L-Angel")
    archs = list(rm.entries)
    while rm.has_more: rm = dbx.files_list_folder_continue(rm.cursor); archs.extend(rm.entries)
    libros = [f for f in archs if isinstance(f, dropbox.files.FileMetadata) and "libro de clientes" in f.name.lower() and f.name.lower().endswith(".xlsx")]
    libros.sort(key=lambda x: x.size, reverse=True)
    print(f"   -> Se detectaron {len(libros)} Libros de Clientes por Ciudad/Comuna en Chile.", flush=True)

    tot_hojas = 0
    for idx, f_lib in enumerate(libros, 1):
        ciudad = re.sub(r"(?i)libro de clientes\s*", "", os.path.splitext(f_lib.name)[0]).strip(" -")
        try:
            _, rp = dbx.files_download(f_lib.path_lower)
            wb = openpyxl.load_workbook(io.BytesIO(rp.content), read_only=True, data_only=True)
            hojas = wb.sheetnames
            for h_nom in hojas:
                ws = wb[h_nom]
                textos = []
                for row in ws.iter_rows(min_row=1, max_row=25, max_col=10, values_only=True):
                    for val in row:
                        if val is not None and str(val).strip() != "":
                            textos.append(str(val).strip())
                blob = " | ".join(textos[:30])
                m_rut = re.search(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b", blob)
                m_em = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", blob)
                m_tel = re.search(r"(?:\+?56\s*9\s*\d{4}\s*\d{4}|\b9\s*\d{7,8}\b)", blob)
                cid_key = f"{ciudad}::{h_nom}"
                cur.execute("INSERT OR REPLACE INTO Clientes_Ciudad VALUES (?,?,?,?,?,?,?,?)",
                            (cid_key, ciudad, h_nom, m_rut.group(0) if m_rut else "", m_tel.group(0) if m_tel else "", m_em.group(0) if m_em else "", blob[:400], f_lib.client_modified.strftime("%d-%m-%Y")))
                tot_hojas += 1
            wb.close()
            if idx <= 15 or idx % 20 == 0:
                print(f"   ✅ [{idx:03d}/{len(libros)}] {ciudad:<28} ({f_lib.size//1024:4d} KB) ➔ {len(hojas):3d} hojas/clientes leídos", flush=True)
            con.commit()
        except Exception: pass

    print("\n💰 Leyendo en MODO SOLO LECTURA 'Cuentas por Cobrar.xlsx' y 'Base-datos-clientes.xlsx'...", flush=True)
    indexar_cuentas_por_cobrar(dbx, con)
    df_cli = pd.read_sql_query("SELECT Ciudad, Nombre_Hoja_Cliente, Rut, Telefono, Email, Fecha_Mod, Datos_Resumen FROM Clientes_Ciudad ORDER BY Ciudad, Nombre_Hoja_Cliente", con)
    df_cxc = pd.read_sql_query("SELECT Origen_Hoja, Cliente_O_Rut, Monto_Detectado, Fecha_Archivo, Detalle_Fila FROM Cuentas_Por_Cobrar", con)
    f_out = os.path.expanduser("~/CRM_MAESTRO_NACIONAL_INSUMAES.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        df_cli.to_excel(wr, sheet_name="Clientes_204_Ciudades", index=False)
        df_cxc.to_excel(wr, sheet_name="Cuentas_Por_Cobrar_y_Base", index=False)
    dbx.files_upload(open(f_out, "rb").read(), "/CRM_MAESTRO_NACIONAL_INSUMAES.xlsx", mode=dropbox.files.WriteMode.overwrite)
    con.close()
    print(f"\n🏆 ¡CRM Nacional consolidado! {tot_hojas} fichas/hojas de clientes de {len(libros)} ciudades unificadas en:")
    print("   ☁️ Raíz de tu Dropbox: /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx", flush=True)

def abrir_centro_cotizaciones():
    while True:
        os.system("clear")
        con = inicializar_sqlite()
        n_cot = con.execute("SELECT COUNT(*) FROM Cotizaciones").fetchone()[0]
        n_cli = con.execute("SELECT COUNT(*) FROM Clientes_Ciudad").fetchone()[0]
        con.close()
        print("=" * 96)
        print("🏢  BOTÓN [23]: CRM NACIONAL (204 CIUDADES), COTIZACIONES B2B & REPARADOR DE PLANTILLA")
        print(f"📊  Bóveda SQLite Activa : ✅ {n_cli} Clientes/Hojas Nacionales | ✅ {n_cot} Cotizaciones Indexadas")
        print("=" * 96)
        print("  1. 🔧 Reparar Plantilla Cotizaciones (J15:J18) + Sincronizar '/COTIZACIONES INSUMAES'")
        print("  2. 🌎 Unificar los ~204 'Libro de Clientes [Ciudad].xlsx' en 1 Excel Maestro Nacional")
        print("  3. 🔎 Super-Buscador 360° (Busca un Cliente, RUT, Ciudad o Producto en Ciudades + Cotizaciones)")
        print("  0. 🔙 Volver al Panel Principal")
        print("=" * 96)
        op = input("\n👉 Selecciona una opción (0-3): ").strip()
        if op == "0": break
        elif op == "1": sincronizar_cotizaciones_dropbox(); input("\nPresiona Enter para continuar...")
        elif op == "2": indexar_libros_clientes_ciudades(); input("\nPresiona Enter para continuar...")
        elif op == "3":
            q = input("\n🔎 Escribe Cliente, Maestranza, RUT, Ciudad o Producto a buscar: ").strip().upper()
            if q:
                con = inicializar_sqlite()
                df1 = pd.read_sql_query("SELECT Ciudad, Nombre_Hoja_Cliente, Rut, Telefono, Email, Datos_Resumen FROM Clientes_Ciudad", con)
                m1 = df1[df1.apply(lambda r: q in " ".join(str(v).upper() for v in r), axis=1)]
                print(f"\n🏢 LIBROS DE CLIENTES POR CIUDAD ({len(m1)} encontrados):")
                for _, r in m1.head(15).iterrows():
                    print(f"  • [{r['Ciudad']}] Hoja: {r['Nombre_Hoja_Cliente']} | RUT:{r['Rut']} | Tel:{r['Telefono']} | {str(r['Datos_Resumen'])[:55]}")
                df2 = pd.read_sql_query("SELECT Numero_Cotizacion, Carpeta_Mes, Nombre_Cliente, Total_Pagar, Resumen_Items FROM Cotizaciones", con)
                m2 = df2[df2.apply(lambda r: q in " ".join(str(v).upper() for v in r), axis=1)]
                print(f"\n📑 COTIZACIONES B2B ({len(m2)} encontradas):")
                for _, r in m2.head(15).iterrows():
                    print(f"  • [{r['Numero_Cotizacion']}] ({r['Carpeta_Mes']}) {str(r['Nombre_Cliente'])[:28]:<28} | ${r['Total_Pagar']:,.0f} | {str(r['Resumen_Items'])[:45]}".replace(",", "."))
                df3 = pd.read_sql_query("SELECT Origen_Hoja, Cliente_O_Rut, Monto_Detectado, Detalle_Fila FROM Cuentas_Por_Cobrar", con)
                m3 = df3[df3.apply(lambda r: q in " ".join(str(v).upper() for v in r), axis=1)]
                print(f"\n💰 CUENTAS POR COBRAR Y BASE CLIENTES ({len(m3)} coincidencias):")
                for _, r in m3.head(15).iterrows():
                    print(f"  • [{r['Origen_Hoja']}] ${r['Monto_Detectado']:,.0f} | {str(r['Detalle_Fila'])[:70]}".replace(",", "."))
                con.close()
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    reparar_plantilla_dropbox()
