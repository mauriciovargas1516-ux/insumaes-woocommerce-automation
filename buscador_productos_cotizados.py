import os, re, sqlite3, dropbox
import pandas as pd
import formateador_excel_cloud

FAMILIAS = {
    "1": ("ACEITES_Y_LUBRICANTES", "ACEITE|SOLUBLE|LUBRAX|MATIC|FLUIDO|GRASA"),
    "2": ("INSERTOS_MECANIZADO", "INSERTO|TNMG|DCMT|WNMG|SEKT|APMT|CCMT|CNMG|MGMN|ERAG|IRN"),
    "3": ("PORTAHERRAMIENTAS", "PORTA|WTJNR|SCLCR|MGEHR|SER2|SEL2|SDJCR|MWLNR|barra"),
    "4": ("MEDICION_DASQUA_INSIZE", "PIE DE METRO|MICROMETRO|DASQUA|INSIZE|RELOJ|ALEXOMETRO|CALIBRE"),
    "5": ("BROCAS_IZAR_COBALTO", "BROCA|IZAR|HSSE|COBALTO|ABOCARDADOR|AVELLANADOR"),
    "6": ("FRESAS_Y_LIMAS", "FRESA|TUNGSTENO|LIMA|ARANA|CABEZAL"),
    "7": ("PLATOS_Y_PUNTOS_TORNO", "PLATO|PUNTO GIRATORIO|MANDRIL|MORDAZA|CONTRAPUNTA"),
    "8": ("MACHOS_Y_TERRAJAS", "MACHO|TERRAJA|ROSCA|HELICOIL|PORTAMACHO"),
    "9": ("CONOS_ESPIGAS_BOQUILLAS", "ESPIGA|BOQUILLA|CONO|REDUCTOR|NT40|BT40|ER32|ER25|PORTAPINZA")
}

def conectar_dbx():
    env = dict(
        l.strip().replace('"', '').split('=', 1)
        for l in open(os.path.expanduser('~/.env'))
        if '=' in l and not l.strip().startswith('#')
    )
    return dropbox.Dropbox(
        app_key=env["DROPBOX_APP_KEY"],
        app_secret=env["DROPBOX_APP_SECRET"],
        oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"]
    )

def buscar_producto_en_cotizaciones(termino_manual=None):
    db_path = os.path.expanduser("~/boveda_cotizaciones_insumaes.db")
    f_rep = os.path.expanduser("~/REPORTE_MAESTRO_COTIZACIONES_2026.xlsx")

    if termino_manual:
        etiqueta = re.sub(r"[^A-Z0-9]+", "_", termino_manual.upper()).strip("_")
        patron = re.escape(termino_manual.strip())
    else:
        os.system("clear")
        print("=" * 92)
        print("🎯 BUSCADOR DE PRODUCTOS DENTRO DE LAS 445 COTIZACIONES B2B (RAYOS-X)")
        print("=" * 92)
        print("  [1] Aceites y Fluidos de Corte (Aceite Soluble, Lubrax, Tapmatic)")
        print("  [2] Insertos de Mecanizado (TNMG, DCMT, WNMG, SEKT, APMT, CCMT, MGMN)")
        print("  [3] Portaherramientas (Exterior, Interior, Roscado, Tronzado)")
        print("  [4] Instrumentos de Medicion (Pie de Metro, Micrometro, Dasqua, Insize)")
        print("  [5] Brocas y Abocardadores (Brocas Izar, Cobalto HSSE, Centro)")
        print("  [6] Fresas y Limas Rotativas (Fresas Tungsteno, HSS, Limas)")
        print("  [7] Platos de Torno y Puntos Giratorios (3 y 4 Garras, Mandriles)")
        print("  [8] Machos, Terrajas y Roscado (Juegos de Machos, Terrajas)")
        print("  [9] Conos, Espigas y Boquillas (Espigas MS, Juegos Boquillas, Reductores)")
        print("  [10] Escribir cualquier Producto, Medida o SKU especifico")
        print("  [0] Volver")
        print("=" * 92)
        op = input("\nSelecciona una familia (1-9), [10] para escribir, o [0] salir: ").strip()
        if op == "0" or not op:
            return
        elif op in FAMILIAS:
            etiqueta, patron = FAMILIAS[op]
        else:
            q = input("\nEscribe el nombre, codigo o medida del producto (ej: ACEITE): ").strip()
            if not q:
                return
            etiqueta = re.sub(r"[^A-Z0-9]+", "_", q.upper()).strip("_")
            patron = q

    dfs_encontrados = []
    if os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        tablas = [
            r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        for tb in tablas:
            if "cliente" in tb.lower() and "cotiz" not in tb.lower():
                continue
            df_tb = pd.read_sql_query(f"SELECT * FROM {tb}", con)
            if df_tb.empty:
                continue
            m = df_tb.astype(str).apply(
                lambda c: c.str.contains(patron, case=False, na=False, regex=True)
            ).any(axis=1)
            if m.any():
                dfs_encontrados.append(df_tb[m])

    if not dfs_encontrados and os.path.exists(f_rep):
        xls = pd.ExcelFile(f_rep)
        for sh in xls.sheet_names:
            df_s = pd.read_excel(f_rep, sheet_name=sh)
            m = df_s.astype(str).apply(
                lambda c: c.str.contains(patron, case=False, na=False, regex=True)
            ).any(axis=1)
            if m.any():
                dfs_encontrados.append(df_s[m])

    if not dfs_encontrados:
        print(f"\nNo se encontraron cotizaciones con '{etiqueta}' ({patron}).")
        return

    df_res = pd.concat(dfs_encontrados, ignore_index=True).drop_duplicates()
    print("\n" + "=" * 92)
    print(f"✅ SE ENCONTRARON {len(df_res)} COTIZACIONES QUE INCLUYEN: {etiqueta}")
    print("=" * 92)
    print(df_res.head(15).to_string(index=False))
    if len(df_res) > 15:
        print(f"\n... y {len(df_res) - 15} cotizaciones adicionales.")

    col_cli = next(
        (c for c in df_res.columns if any(k in c.upper() for k in ("CLIENTE", "EMPRESA", "RAZON", "SEÑOR"))),
        None
    )
    col_tot = next(
        (c for c in df_res.columns if any(k in c.upper() for k in ("TOTAL", "MONTO", "NETO"))),
        None
    )

    f_out = os.path.expanduser(f"~/COTIZACIONES_CON_{etiqueta[:25]}.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        df_res.to_excel(wr, sheet_name="1_Cotizaciones_Con_Producto", index=False)
        if col_cli:
            df_c = df_res.copy()
            if col_tot:
                df_c["_monto_num"] = pd.to_numeric(df_c[col_tot], errors="coerce").fillna(0)
            else:
                df_c["_monto_num"] = 0
            grp = df_c.groupby(col_cli, dropna=False).agg(
                Veces_Cotizado=(col_cli, "count"),
                Monto_Total_Cotizado=("_monto_num", "sum")
            ).reset_index().sort_values(by=["Veces_Cotizado", "Monto_Total_Cotizado"], ascending=False)
            grp.to_excel(wr, sheet_name="2_Clientes_Que_Lo_Piden", index=False)

    formateador_excel_cloud.estilizar_excel_pro(f_out)
    nom_dbx = f"/COTIZACIONES_CON_{etiqueta[:25]}.xlsx"
    conectar_dbx().files_upload(
        open(f_out, "rb").read(), nom_dbx, mode=dropbox.files.WriteMode.overwrite
    )
    print("\n" + "=" * 92)
    print(f"☁️  Excel auto-ajustado subido a tu Dropbox: {nom_dbx}")
    print("   - Pestana 1: Detalle de cada cotizacion donde aparece el producto.")
    print("   - Pestana 2: Ranking de Clientes/Maestranzas que lo han pedido.")
    print("=" * 92)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        buscar_producto_en_cotizaciones(" ".join(sys.argv[1:]))
    else:
        while True:
            buscar_producto_en_cotizaciones()
            if input("\n¿Buscar otro producto? (S/N): ").strip().upper() != "S":
                break
