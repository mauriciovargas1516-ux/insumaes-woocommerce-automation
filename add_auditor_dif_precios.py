import os, py_compile

p = os.path.expanduser("~/esqueleto_integrador.py")
t = open(p, "r", encoding="utf-8").read()

fn_dif = '''
def exportar_diferencia_precios_ml_dropbox():
    _, dbx, _ = conectar_todo()
    f_aud = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    if not os.path.exists(f_aud):
        try:
            _, r = dbx.files_download("/AUDITORIA_MELI_INSUMAES.xlsx")
            open(f_aud, "wb").write(r.content)
        except Exception as e:
            print(f"\\n⚠️ No se encontró AUDITORIA_MELI_INSUMAES.xlsx: {e}"); return

    df = pd.read_excel(f_aud, sheet_name="AUDITORIA_MELI")
    filas_todas, filas_alerta, filas_sin_par = [], [], []

    for _, r in df.iterrows():
        est = str(r.get("Estado", "")).strip()
        mlc = str(r.get("Código ML (Ver Web)", "")).strip()
        nom_ml = str(r.get("Nombre en Mercado Libre", "")).strip()
        nom_ex = str(r.get("Nombre en tu Excel (Ir a Celda)", "")).strip()
        pest = str(r.get("Pestaña del Excel", "")).strip()
        pack = r.get("Unid. x Pack", 1)
        st_bod = r.get("Stock Bodega", 0)
        pub_ml = r.get("Publicado Hoy en ML", 0)
        p_ex, p_ml = r.get("Precio Excel", None), r.get("Precio ML", None)

        try: p_ex_val = float(p_ex) if pd.notna(p_ex) else 0.0
        except Exception: p_ex_val = 0.0
        try: p_ml_val = float(p_ml) if pd.notna(p_ml) else 0.0
        except Exception: p_ml_val = 0.0

        if p_ex_val <= 0 or "Sin Pareja" in est:
            filas_sin_par.append({"Codigo_ML": mlc, "Estado_ML": est, "Nombre_Mercado_Libre": nom_ml, "Publicado_Hoy_ML": pub_ml, "Precio_Actual_ML": int(p_ml_val)})
            continue

        dif_clp = int(round(p_ml_val - p_ex_val))
        dif_pct = round(((p_ml_val - p_ex_val) / p_ex_val) * 100.0, 1)
        envio_est = 3800 if p_ml_val >= 19990 else 1000
        liquido_ml = int(round((p_ml_val * 0.86) - envio_est))
        gan_vs_web = int(round(liquido_ml - p_ex_val))

        if dif_pct < 20.0 or gan_vs_web < 0: sem = "🚨 ALERTA MARGEN BAJO (<20% o Pierde vs Web)"
        elif dif_pct <= 45.0: sem = "✅ MARGEN SANO (+20% a +45%)"
        else: sem = "🔥 SOBREPRECIO ALTO (> +45%)"

        reg = {
            "Semaforo_Rentabilidad": sem, "Codigo_ML": mlc, "Pestana_Excel": pest,
            "Producto_Excel": nom_ex, "Titulo_Mercado_Libre": nom_ml, "Unid_x_Pack": pack,
            "Stock_Bodega": st_bod, "Publicado_ML": pub_ml, "Precio_Excel_Web": int(round(p_ex_val)),
            "Precio_Actual_ML": int(round(p_ml_val)), "Diferencia_Pesos": dif_clp,
            "Recargo_ML_Pct": f"{dif_pct:+.1f}%", "Liquido_Estimado_ML": liquido_ml,
            "Diferencia_Liquida_vs_Web": gan_vs_web
        }
        filas_todas.append((dif_pct, reg))
        if "ALERTA" in sem: filas_alerta.append((dif_pct, reg))
'''
