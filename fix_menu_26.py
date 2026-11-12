import os, py_compile

p = os.path.expanduser("~/esqueleto_integrador.py")
t = open(p, "r", encoding="utf-8").read()

if "def abrir_esqueleto():" in t:
    t = t[:t.find("def abrir_esqueleto():")]

fn_3 = '''
def exportar_diferencia_precios_ml_dropbox():
    _, dbx, _ = conectar_todo()
    f_aud = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    if not os.path.exists(f_aud):
        _, r = dbx.files_download("/AUDITORIA_MELI_INSUMAES.xlsx")
        open(f_aud, "wb").write(r.content)
    df = pd.read_excel(f_aud, sheet_name="AUDITORIA_MELI")
    filas_todas, filas_alerta, filas_sin_par = [], [], []
    for _, r in df.iterrows():
        est, mlc = str(r.get("Estado", "")).strip(), str(r.get("Código ML (Ver Web)", "")).strip()
        nom_ml, nom_ex = str(r.get("Nombre en Mercado Libre", "")).strip(), str(r.get("Nombre en tu Excel (Ir a Celda)", "")).strip()
        pest, pack, st_bod, pub_ml = str(r.get("Pestaña del Excel", "")).strip(), r.get("Unid. x Pack", 1), r.get("Stock Bodega", 0), r.get("Publicado Hoy en ML", 0)
        try: p_ex_val = float(r.get("Precio Excel")) if pd.notna(r.get("Precio Excel")) else 0.0
        except Exception: p_ex_val = 0.0
        try: p_ml_val = float(r.get("Precio ML")) if pd.notna(r.get("Precio ML")) else 0.0
        except Exception: p_ml_val = 0.0
        if p_ex_val <= 0 or "Sin Pareja" in est:
            filas_sin_par.append({"Codigo_ML": mlc, "Estado_ML": est, "Nombre_Mercado_Libre": nom_ml, "Publicado_Hoy_ML": pub_ml, "Precio_Actual_ML": int(p_ml_val)})
            continue
        dif_clp, dif_pct = int(round(p_ml_val - p_ex_val)), round(((p_ml_val - p_ex_val) / p_ex_val) * 100.0, 1)
        liq_ml = int(round((p_ml_val * 0.86) - (3800 if p_ml_val >= 19990 else 1000)))
        gan_web = int(round(liq_ml - p_ex_val))
        sem = "🚨 ALERTA MARGEN BAJO (<20% o Pierde vs Web)" if (dif_pct < 20.0 or gan_web < 0) else ("✅ MARGEN SANO (+20% a +45%)" if dif_pct <= 45.0 else "🔥 SOBREPRECIO ALTO (> +45%)")
        reg = {"Semaforo_Rentabilidad": sem, "Codigo_ML": mlc, "Pestana_Excel": pest, "Producto_Excel": nom_ex, "Titulo_Mercado_Libre": nom_ml, "Unid_x_Pack": pack, "Stock_Bodega": st_bod, "Publicado_ML": pub_ml, "Precio_Excel_Web": int(round(p_ex_val)), "Precio_Actual_ML": int(round(p_ml_val)), "Diferencia_Pesos": dif_clp, "Recargo_ML_Pct": f"{dif_pct:+.1f}%", "Liquido_Estimado_ML": liq_ml, "Diferencia_Liquida_vs_Web": gan_web}
        filas_todas.append((dif_pct, reg))
        if "ALERTA" in sem: filas_alerta.append((dif_pct, reg))
    filas_todas.sort(key=lambda x: x[0]); filas_alerta.sort(key=lambda x: x[0])
    f_out = os.path.expanduser("~/DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        pd.DataFrame([x[1] for x in filas_alerta]).to_excel(wr, sheet_name="1_Alerta_Margen_Bajo_ML", index=False)
        pd.DataFrame([x[1] for x in filas_todas]).to_excel(wr, sheet_name="2_Comparativa_782_Items", index=False)
        pd.DataFrame(filas_sin_par).to_excel(wr, sheet_name="3_Sin_Pareja_En_Excel", index=False)
    formateador_excel_cloud.estilizar_excel_pro(f_out)
    dbx.files_upload(open(f_out, "rb").read(), "/DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx", mode=dropbox.files.WriteMode.overwrite)
    print(f"\\n✅ [3] Auditoría Precios ML vs Web subida a Dropbox ({len(filas_todas)} cruzados | {len(filas_alerta)} en Alerta <20% | {len(filas_sin_par)} sin pareja).")
'''
if "def exportar_diferencia_precios_ml_dropbox" not in t:
    t += fn_3

fn_4 = '''
def traspasar_catalogo_multicanal(rec_pct=None):
    _, dbx, _ = conectar_todo()
    f_rad = os.path.expanduser("~/RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
    if not os.path.exists(f_rad):
        _, r_dbx = dbx.files_download("/RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
        open(f_rad, "wb").write(r_dbx.content)
    if rec_pct is None:
        rec_s = input("\\n📈 % de recargo para Marketplaces (Enter = +25% recomendado): ").strip().replace(",", ".")
        try: rec_pct = float(rec_s) if rec_s else 25.0
        except Exception: rec_pct = 25.0
    factor_mkt = 1.0 + (rec_pct / 100.0)
    txt = open(f_rad, "r", encoding="utf-8", errors="replace").read()
    bloques = re.split(r"\\n#{80}\\n### ID_WOO: ", txt)
    filas_meli, filas_mkt, filas_shop = [], [], []
    for b in bloques[1:]:
        lin = b.splitlines()
        m1 = re.match(r"(\\d+)\\s*\\|\\s*SKU:\\s*(.*?)\\s*\\|\\s*NOMBRE:\\s*(.*)", lin[0])
        if not m1: continue
        pid, sku, nom = int(m1.group(1)), m1.group(2).strip(), m1.group(3).strip()
        m2 = re.match(r"### PRECIO:\\s*\\$(.*?)\\s*\\|\\s*STOCK:\\s*(.*?)\\s*\\|\\s*CATEGORIAS:\\s*(.*)", lin[1] if len(lin)>1 else "")
        pr_s, st_s, cats = (m2.group(1).strip(), m2.group(2).strip(), m2.group(3).strip()) if m2 else ("0", "0", "")
        fotos = [x.strip() for x in (lin[3].replace("### FOTOS:", "").split("|") if len(lin)>3 else []) if x.strip()]
        desc_html = b.split("--- [HTML_Y_CSS_DESCRIPCION_LARGA] ---")[-1].strip() if "--- [HTML_Y_CSS_DESCRIPCION_LARGA] ---" in b else ""
        try: pr = float(pr_s)
        except Exception: pr = 0.0
        try: st = int(float(st_s))
        except Exception: st = 0
        if pr <= 0 or st <= 0 or not fotos: continue
        sku_ok, desc_plana = (sku if sku else f"INS-{pid}"), limpiar_html_plano(desc_html)[:1000]
        es_ins = ("INSERTO" in cats.upper())
        st_packs, p_base = ((st // 10) if es_ins else st), ((pr * 10.0) if es_ins else pr)
        p_mkt = int(round((p_base * factor_mkt) / 100.0) * 100)
        if st_packs > 0:
            filas_meli.append({"SKU_Origen": sku_ok, "Titulo_ML_60_Car": (f"Pack 10 Insertos {nom}" if es_ins else nom)[:60], "Categoria": cats, "Modalidad": "Caja x10 Uds" if es_ins else "Unidad", "Stock_Packs": st_packs, "Precio_Web_Base": int(p_base), f"Precio_ML_Mas_{int(rec_pct)}pct": p_mkt, "Foto_Principal": fotos[0], "Descripcion_Texto_Plano": desc_plana})
        filas_mkt.append({"Seller_SKU": sku_ok, "Nombre_Producto": nom[:100], "Marca": "INSUMAES", "Categoria_Familia": cats.split("|")[0].strip(), "Stock_40pct": st, "Precio_Normal_Mkt": int(round((pr * factor_mkt * 1.15) / 100.0) * 100), f"Precio_Oferta_Mkt_{int(rec_pct)}pct": int(round((pr * factor_mkt) / 100.0) * 100), "URL_Imagen_1": fotos[0], "Descripcion_Plana_Sin_HTML": desc_plana})
        filas_shop.append({"Handle": re.sub(r"[^a-z0-9]+", "-", nom.lower()).strip("-"), "Title": nom, "Vendor": "INSUMAES", "Type": cats.split("|")[0].strip(), "Variant_SKU": sku_ok, "Variant_Inventory_Qty": st, "Variant_Price": int(pr), "Image_Src": fotos[0], "Body_HTML_Conservado": desc_html[:2000]})
    f_out = os.path.expanduser("~/TRASPASO_MULTICANAL_UNIVERSAL.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        pd.DataFrame(filas_meli).to_excel(wr, sheet_name="1_Formato_MercadoLibre", index=False)
        pd.DataFrame(filas_mkt).to_excel(wr, sheet_name="2_Formato_Falabella_Paris_Lider", index=False)
        pd.DataFrame(filas_shop).to_excel(wr, sheet_name="3_Formato_Shopify_Web_B2B", index=False)
    formateador_excel_cloud.estilizar_excel_pro(f_out)
    dbx.files_upload(open(f_out, "rb").read(), "/TRASPASO_MULTICANAL_UNIVERSAL.xlsx", mode=dropbox.files.WriteMode.overwrite)
    print(f"\\n✅ [4] Traspaso Multi-Canal subido a Dropbox: {len(filas_meli)} packs ML | {len(filas_mkt)} Falabella/Paris/Lider | {len(filas_shop)} Shopify.")
'''

menu_0_4 = '''
def abrir_esqueleto():
    while True:
        os.system("clear")
        print("=" * 96)
        print("BOTON [26]: ESQUELETO INTEGRADOR OMNICANAL (BRECHAS, PRECIOS ML & TRASPASO MULTICANAL)")
        print("=" * 96)
        print("  [1] Detectar Brechas en Insumaes (Productos listos en Web que faltan en ML + Web sin foto)")
        print("  [2] Generar Kit 'Llave en Mano' para Clientes Nuevos (.env.example + Plantilla Excel)")
        print("  [3] Exportar Diferencia de Precios ML vs Web a Dropbox (100% Solo Lectura, jamás toca ML)")
        print("  [4] Traspasador Rápido Multi-Canal (Exporta Catálogo a ML, Falabella, Paris, Lider y Shopify)")
        print("  [0] Volver al Panel Principal")
        print("=" * 96)
        op = input("\\nSelecciona una opción (0-4): ").strip()
        if op == "0": break
        elif op == "1": detectar_brechas_omnicanal(); input("\\nPresiona Enter para continuar...")
        elif op == "2": generar_kit_cliente_nuevo(); input("\\nPresiona Enter para continuar...")
        elif op == "3": exportar_diferencia_precios_ml_dropbox(); input("\\nPresiona Enter para continuar...")
        elif op == "4": traspasar_catalogo_multicanal(); input("\\nPresiona Enter para continuar...")

if __name__ == "__main__":
    abrir_esqueleto()
'''
if "def traspasar_catalogo_multicanal" in t:
    t = t[:t.find("def traspasar_catalogo_multicanal")]
t += fn_4 + menu_0_4
open(p, "w", encoding="utf-8").write(t)
py_compile.compile(p, doraise=True)
print("✅ Menú del Botón [26] actualizado con las 4 opciones (0-4).")
