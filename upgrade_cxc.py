import os, py_compile

p = os.path.expanduser("~/centro_cotizaciones.py")
t = open(p, "r", encoding="utf-8").read()

viejo_sql = 'cur.execute("CREATE TABLE IF NOT EXISTS Clientes_Ciudad (Id TEXT PRIMARY KEY, Ciudad TEXT, Nombre_Hoja_Cliente TEXT, Rut TEXT, Telefono TEXT, Email TEXT, Datos_Resumen TEXT, Fecha_Mod TEXT)")'
nuevo_sql = viejo_sql + '\n    cur.execute("CREATE TABLE IF NOT EXISTS Cuentas_Por_Cobrar (Id TEXT PRIMARY KEY, Origen_Hoja TEXT, Cliente_O_Rut TEXT, Detalle_Fila TEXT, Monto_Detectado REAL, Fecha_Archivo TEXT)")'

fn_cxc = '''
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
'''

if "Cuentas_Por_Cobrar" not in t:
    t = t.replace(viejo_sql, nuevo_sql)
    t = t.replace("def indexar_libros_clientes_ciudades():", fn_cxc + "\ndef indexar_libros_clientes_ciudades():")
    t = t.replace(
        '    df_cli = pd.read_sql_query("SELECT Ciudad, Nombre_Hoja_Cliente, Rut, Telefono, Email, Fecha_Mod, Datos_Resumen FROM Clientes_Ciudad ORDER BY Ciudad, Nombre_Hoja_Cliente", con)\n    f_out = os.path.expanduser("~/CRM_MAESTRO_NACIONAL_INSUMAES.xlsx")\n    df_cli.to_excel(f_out, index=False)',
        '    print("\\n💰 Leyendo en MODO SOLO LECTURA \'Cuentas por Cobrar.xlsx\' y \'Base-datos-clientes.xlsx\'...", flush=True)\n    indexar_cuentas_por_cobrar(dbx, con)\n    df_cli = pd.read_sql_query("SELECT Ciudad, Nombre_Hoja_Cliente, Rut, Telefono, Email, Fecha_Mod, Datos_Resumen FROM Clientes_Ciudad ORDER BY Ciudad, Nombre_Hoja_Cliente", con)\n    df_cxc = pd.read_sql_query("SELECT Origen_Hoja, Cliente_O_Rut, Monto_Detectado, Fecha_Archivo, Detalle_Fila FROM Cuentas_Por_Cobrar", con)\n    f_out = os.path.expanduser("~/CRM_MAESTRO_NACIONAL_INSUMAES.xlsx")\n    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:\n        df_cli.to_excel(wr, sheet_name="Clientes_204_Ciudades", index=False)\n        df_cxc.to_excel(wr, sheet_name="Cuentas_Por_Cobrar_y_Base", index=False)'
    )
    viejo_busc = '                con.close()\n            input("\\nPresiona Enter para continuar...")'
    nuevo_busc = '''                df3 = pd.read_sql_query("SELECT Origen_Hoja, Cliente_O_Rut, Monto_Detectado, Detalle_Fila FROM Cuentas_Por_Cobrar", con)
                m3 = df3[df3.apply(lambda r: q in " ".join(str(v).upper() for v in r), axis=1)]
                print(f"\\n💰 CUENTAS POR COBRAR Y BASE CLIENTES ({len(m3)} coincidencias):")
                for _, r in m3.head(15).iterrows():
                    print(f"  • [{r['Origen_Hoja']}] ${r['Monto_Detectado']:,.0f} | {str(r['Detalle_Fila'])[:70]}".replace(",", "."))
                con.close()
            input("\\nPresiona Enter para continuar...")'''
    t = t.replace(viejo_busc, nuevo_busc)
    open(p, "w", encoding="utf-8").write(t)
    py_compile.compile(p, doraise=True)
    print("✅ Modo 100% SOLO LECTURA garantizado + Integración de 'Cuentas por Cobrar.xlsx' activada.")
else:
    print("✅ Ya estaba integrado 'Cuentas por Cobrar.xlsx'.")
