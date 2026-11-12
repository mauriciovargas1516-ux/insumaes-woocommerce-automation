import os, re, json, time, html, dropbox
import pandas as pd
from woocommerce import API
import formateador_excel_cloud

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

def conectar_todo():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    wc = API(url=env.get("WOO_URL", "https://www.insumaes.cl/"), consumer_key=env["WOO_KEY"], consumer_secret=env["WOO_SECRET"], version="wc/v3", timeout=45)
    dbx = dropbox.Dropbox(app_key=env["DROPBOX_APP_KEY"], app_secret=env["DROPBOX_APP_SECRET"], oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"])
    return wc, dbx, env

def limpiar_html_plano(html_txt):
    if not html_txt: return ""
    s = re.sub(r"(?i)<\s*(?:br|/p|/div|/tr|/li|/h\d)\b[^>]*>", "\n", str(html_txt))
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return "\n".join(l.strip() for l in s.splitlines() if l.strip())

def detectar_brechas_omnicanal():
    _, dbx, _ = conectar_todo()
    f_rad = os.path.expanduser("~/RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
    if not os.path.exists(f_rad):
        try:
            _, r_dbx = dbx.files_download("/RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
            open(f_rad, "wb").write(r_dbx.content)
        except Exception:
            print("\n⚠️ Primero ejecuta el respaldo en el Botón [22 -> 6]."); return

    meli_set = set()
    f_map = os.path.expanduser("~/mapas_rapidos_cache.json")
    if os.path.exists(f_map):
        mp = json.load(open(f_map, "r", encoding="utf-8"))
        for k, v in mp.items():
            if "meli" in k.lower() and isinstance(v, dict):
                meli_set.update(str(x).strip().upper() for x in v.keys())
    f_aud = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    if os.path.exists(f_aud):
        try:
            df_a = pd.read_excel(f_aud)
            for col in df_a.columns:
                if any(w in str(col).upper() for w in ("SKU", "TITULO", "NOMBRE", "EXCEL", "CATALOGO")):
                    meli_set.update(str(x).strip().upper() for x in df_a[col].dropna())
        except Exception: pass

    txt = open(f_rad, "r", encoding="utf-8", errors="replace").read()
    bloques = re.split(r"\n#{80}\n### ID_WOO: ", txt)
    listos_ml, sin_foto = [], []

    for b in bloques[1:]:
        lin = b.splitlines()
        m1 = re.match(r"(\d+)\s*\|\s*SKU:\s*(.*?)\s*\|\s*NOMBRE:\s*(.*)", lin[0])
        if not m1: continue
        pid, sku, nom = int(m1.group(1)), m1.group(2).strip(), m1.group(3).strip()
        m2 = re.match(r"### PRECIO:\s*\$(.*?)\s*\|\s*STOCK:\s*(.*?)\s*\|\s*CATEGORIAS:\s*(.*)", lin[1] if len(lin)>1 else "")
        pr_s, st_s, cats = (m2.group(1).strip(), m2.group(2).strip(), m2.group(3).strip()) if m2 else ("0", "0", "")
        fotos = [x.strip() for x in (lin[3].replace("### FOTOS:", "").split("|") if len(lin)>3 else []) if x.strip()]
        desc_html = b.split("--- [HTML_Y_CSS_DESCRIPCION_LARGA] ---")[-1].strip() if "--- [HTML_Y_CSS_DESCRIPCION_LARGA] ---" in b else ""
        try: pr = float(pr_s)
        except Exception: pr = 0.0
        try: st = int(float(st_s))
        except Exception: st = 0

        if pr > 0 and st > 0:
            if not fotos:
                sin_foto.append({"ID_WOO": pid, "SKU": sku, "Nombre_Producto": nom, "Precio_Web_IVA": int(pr), "Stock_Web_40pct": st, "Categorias_Web": cats})
            elif nom.upper() not in meli_set and (not sku or sku.upper() not in meli_set):
                listos_ml.append({
                    "ID_WOO": pid, "SKU": sku, "Titulo_Sugerido_ML": nom[:60],
                    "Categorias_Web": cats, "Stock_Web_40pct": st,
                    "Precio_Web_IVA": int(pr), "Precio_Sugerido_ML_18pct": int(round((pr * 1.18) / 100.0) * 100),
                    "URL_Foto_Principal": fotos[0],
                    "Descripcion_Limpia_ML": limpiar_html_plano(desc_html)[:500]
                })
    f_out = os.path.expanduser("~/BRECHA_EXPANSION_WOO_A_MELI.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        pd.DataFrame(listos_ml).to_excel(wr, sheet_name="Listos_Para_Subir_a_ML", index=False)
        pd.DataFrame(sin_foto).to_excel(wr, sheet_name="Con_Stock_Pero_Sin_Foto", index=False)

    formateador_excel_cloud.estilizar_excel_pro(f_out)
    dbx.files_upload(open(f_out, "rb").read(), "/BRECHA_EXPANSION_WOO_A_MELI.xlsx", mode=dropbox.files.WriteMode.overwrite)
    print("\n" + "=" * 92)
    print("📊 RESULTADO DEL ESCÁNER DE BRECHAS OMNICANAL (WOO -> MERCADO LIBRE)")
    print("=" * 92)
    print(f" 🚀 Productos con Stock, Precio y Foto listos para subir a ML : {len(listos_ml)} productos")
    print(f" 📸 Productos con Stock y Precio en Web pero SIN fotografía   : {len(sin_foto)} productos")
    print(" ✨ Columnas, altos de fila, formato moneda $ y autofiltros auto-ajustados.")
    print(" ☁️ Excel subido a la raíz de tu Dropbox: /BRECHA_EXPANSION_WOO_A_MELI.xlsx")
    print("=" * 92)

def generar_kit_cliente_nuevo():
    _, dbx, _ = conectar_todo()
    df_molde = pd.DataFrame([
        {
            "SKU": "EJEMPLO-001", "Nombre_Producto": "PORTAHERRAMIENTA EXTERIOR WTJNR2020K16",
            "Categoria": "PORTAHERRAMIENTAS", "Precio_Venta_IVA": 34000, "Stock_Fisico_Bodega": 10,
            "Descripcion_Tecnica": "Portaherramienta exterior vástago 20x20 mm para inserto TNMG160408.",
            "URL_Foto_Principal": "https://www.insumaes.cl/wp-content/uploads/ejemplo.jpg"
        }
    ])
    f_molde = os.path.expanduser("~/PLANTILLA_ONBOARDING_CLIENTE_NUEVO.xlsx")
    df_molde.to_excel(f_molde, index=False)
    formateador_excel_cloud.estilizar_excel_pro(f_molde)
    dbx.files_upload(open(f_molde, "rb").read(), "/PLANTILLA_ONBOARDING_CLIENTE_NUEVO.xlsx", mode=dropbox.files.WriteMode.overwrite)
    print("\n✅ Plantilla '/PLANTILLA_ONBOARDING_CLIENTE_NUEVO.xlsx' auto-ajustada y subida a Dropbox.")



def traspasar_catalogo_multicanal(rec_pct=None):
    _, dbx, _ = conectar_todo()
    f_rad = os.path.expanduser("~/RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
    if not os.path.exists(f_rad):
        _, r_dbx = dbx.files_download("/RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
        open(f_rad, "wb").write(r_dbx.content)
    if rec_pct is None:
        rec_s = input("\n📈 % de recargo para Marketplaces (Enter = +25% recomendado): ").strip().replace(",", ".")
        try: rec_pct = float(rec_s) if rec_s else 25.0
        except Exception: rec_pct = 25.0
    factor_mkt = 1.0 + (rec_pct / 100.0)
    txt = open(f_rad, "r", encoding="utf-8", errors="replace").read()
    bloques = re.split(r"\n#{80}\n### ID_WOO: ", txt)
    filas_meli, filas_mkt, filas_shop = [], [], []
    for b in bloques[1:]:
        lin = b.splitlines()
        m1 = re.match(r"(\d+)\s*\|\s*SKU:\s*(.*?)\s*\|\s*NOMBRE:\s*(.*)", lin[0])
        if not m1: continue
        pid, sku, nom = int(m1.group(1)), m1.group(2).strip(), m1.group(3).strip()
        m2 = re.match(r"### PRECIO:\s*\$(.*?)\s*\|\s*STOCK:\s*(.*?)\s*\|\s*CATEGORIAS:\s*(.*)", lin[1] if len(lin)>1 else "")
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
    print(f"\n✅ [4] Traspaso Multi-Canal subido a Dropbox: {len(filas_meli)} packs ML | {len(filas_mkt)} Falabella/Paris/Lider | {len(filas_shop)} Shopify.")

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
        op = input("\nSelecciona una opción (0-4): ").strip()
        if op == "0": break
        elif op == "1": detectar_brechas_omnicanal(); input("\nPresiona Enter para continuar...")
        elif op == "2": generar_kit_cliente_nuevo(); input("\nPresiona Enter para continuar...")
        elif op == "3": exportar_diferencia_precios_ml_dropbox(); input("\nPresiona Enter para continuar...")
        elif op == "4": traspasar_catalogo_multicanal(); input("\nPresiona Enter para continuar...")


def exportar_diferencia_precios_ml_dropbox():
    _, dbx, _ = conectar_todo()
    f_aud = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    if not os.path.exists(f_aud):
        _, r = dbx.files_download("/AUDITORIA_MELI_INSUMAES.xlsx")
        open(f_aud, "wb").write(r.content)
    df = pd.read_excel(f_aud, sheet_name="AUDITORIA_MELI")
    todas, alerta, sin_par = [], [], []
    for _, r in df.iterrows():
        est = str(r.get("Estado", "")).strip()
        mlc = str(r.get("Código ML (Ver Web)", "")).strip()
        nom_ml = str(r.get("Nombre en Mercado Libre", "")).strip()
        nom_ex = str(r.get("Nombre en tu Excel (Ir a Celda)", "")).strip()
        pest = str(r.get("Pestaña del Excel", "")).strip()
        pack = r.get("Unid. x Pack", 1)
        st_bod = r.get("Stock Bodega", 0)
        pub_ml = r.get("Publicado Hoy en ML", 0)
        p_ex, p_ml = r.get("Precio Excel"), r.get("Precio ML")
        try: vx = float(p_ex) if pd.notna(p_ex) else 0.0
        except Exception: vx = 0.0
        try: vm = float(p_ml) if pd.notna(p_ml) else 0.0
        except Exception: vm = 0.0
        if vx <= 0 or "Sin Pareja" in est:
            sin_par.append({
                "Codigo_ML": mlc, "Estado_ML": est,
                "Nombre_Mercado_Libre": nom_ml,
                "Publicado_Hoy_ML": pub_ml,
                "Precio_Actual_ML": int(vm)
            })
            continue
        dif_clp = int(round(vm - vx))
        dif_pct = round(((vm - vx) / vx) * 100.0, 1)
        envio = 3800 if vm >= 19990 else 1000
        liq_ml = int(round((vm * 0.86) - envio))
        gan_web = int(round(liq_ml - vx))
        if dif_pct < 20.0 or gan_web < 0:
            sem = "ALERTA MARGEN BAJO (<20% o Pierde vs Web)"
        elif dif_pct <= 45.0:
            sem = "MARGEN SANO (+20% a +45%)"
        else:
            sem = "SOBREPRECIO ALTO (> +45%)"
        reg = {
            "Semaforo_Rentabilidad": sem, "Codigo_ML": mlc,
            "Pestana_Excel": pest, "Producto_Excel": nom_ex,
            "Titulo_Mercado_Libre": nom_ml, "Unid_x_Pack": pack,
            "Stock_Bodega": st_bod, "Publicado_ML": pub_ml,
            "Precio_Excel_Web": int(round(vx)),
            "Precio_Actual_ML": int(round(vm)),
            "Diferencia_Pesos": dif_clp,
            "Recargo_ML_Pct": f"{dif_pct:+.1f}%",
            "Liquido_Estimado_ML": liq_ml,
            "Diferencia_Liquida_vs_Web": gan_web
        }
        todas.append((dif_pct, reg))
        if "ALERTA" in sem:
            alerta.append((dif_pct, reg))
    todas.sort(key=lambda x: x[0])
    alerta.sort(key=lambda x: x[0])
    f_out = os.path.expanduser("~/DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        d1 = pd.DataFrame([x[1] for x in alerta])
        d2 = pd.DataFrame([x[1] for x in todas])
        d3 = pd.DataFrame(sin_par)
        d1.to_excel(wr, sheet_name="1_Alerta_Margen_Bajo_ML", index=False)
        d2.to_excel(wr, sheet_name="2_Comparativa_782_Items", index=False)
        d3.to_excel(wr, sheet_name="3_Sin_Pareja_En_Excel", index=False)
    formateador_excel_cloud.estilizar_excel_pro(f_out)
    dbx.files_upload(
        open(f_out, "rb").read(),
        "/DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx",
        mode=dropbox.files.WriteMode.overwrite
    )
    print(f"\n[OK] [3] Auditoria lista: {len(todas)} cruzados | "
          f"{len(alerta)} en Alerta (<20%) | {len(sin_par)} sin pareja\n"
          "     -> /DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx")


def exportar_diferencia_precios_ml_dropbox():
    _, dbx, _ = conectar_todo()
    f_aud = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    if not os.path.exists(f_aud):
        _, r = dbx.files_download("/AUDITORIA_MELI_INSUMAES.xlsx")
        open(f_aud, "wb").write(r.content)
    df = pd.read_excel(f_aud, sheet_name="AUDITORIA_MELI")
    todas, alerta, sin_par = [], [], []
    for _, r in df.iterrows():
        est = str(r.get("Estado", "")).strip()
        mlc = str(r.get("Código ML (Ver Web)", "")).strip()
        nom_ml = str(r.get("Nombre en Mercado Libre", "")).strip()
        nom_ex = str(r.get("Nombre en tu Excel (Ir a Celda)", "")).strip()
        pest = str(r.get("Pestaña del Excel", "")).strip()
        pack = r.get("Unid. x Pack", 1)
        st_bod = r.get("Stock Bodega", 0)
        pub_ml = r.get("Publicado Hoy en ML", 0)
        p_ex, p_ml = r.get("Precio Excel"), r.get("Precio ML")
        try: vx = float(p_ex) if pd.notna(p_ex) else 0.0
        except Exception: vx = 0.0
        try: vm = float(p_ml) if pd.notna(p_ml) else 0.0
        except Exception: vm = 0.0
        if vx <= 0 or "Sin Pareja" in est:
            sin_par.append({
                "Codigo_ML": mlc, "Estado_ML": est,
                "Nombre_Mercado_Libre": nom_ml,
                "Publicado_Hoy_ML": pub_ml,
                "Precio_Actual_ML": int(vm)
            })
            continue
        dif_clp = int(round(vm - vx))
        dif_pct = round(((vm - vx) / vx) * 100.0, 1)
        envio = 3800 if vm >= 19990 else 1000
        liq_ml = int(round((vm * 0.86) - envio))
        gan_web = int(round(liq_ml - vx))
        if dif_pct < 20.0 or gan_web < 0:
            sem = "ALERTA MARGEN BAJO (<20% o Pierde vs Web)"
        elif dif_pct <= 45.0:
            sem = "MARGEN SANO (+20% a +45%)"
        else:
            sem = "SOBREPRECIO ALTO (> +45%)"
        reg = {
            "Semaforo_Rentabilidad": sem, "Codigo_ML": mlc,
            "Pestana_Excel": pest, "Producto_Excel": nom_ex,
            "Titulo_Mercado_Libre": nom_ml, "Unid_x_Pack": pack,
            "Stock_Bodega": st_bod, "Publicado_ML": pub_ml,
            "Precio_Excel_Web": int(round(vx)),
            "Precio_Actual_ML": int(round(vm)),
            "Diferencia_Pesos": dif_clp,
            "Recargo_ML_Pct": f"{dif_pct:+.1f}%",
            "Liquido_Estimado_ML": liq_ml,
            "Diferencia_Liquida_vs_Web": gan_web
        }
        todas.append((dif_pct, reg))
        if "ALERTA" in sem:
            alerta.append((dif_pct, reg))
    todas.sort(key=lambda x: x[0])
    alerta.sort(key=lambda x: x[0])
    f_out = os.path.expanduser("~/DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        d1 = pd.DataFrame([x[1] for x in alerta])
        d2 = pd.DataFrame([x[1] for x in todas])
        d3 = pd.DataFrame(sin_par)
        d1.to_excel(wr, sheet_name="1_Alerta_Margen_Bajo_ML", index=False)
        d2.to_excel(wr, sheet_name="2_Comparativa_782_Items", index=False)
        d3.to_excel(wr, sheet_name="3_Sin_Pareja_En_Excel", index=False)
    formateador_excel_cloud.estilizar_excel_pro(f_out)
    dbx.files_upload(
        open(f_out, "rb").read(),
        "/DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx",
        mode=dropbox.files.WriteMode.overwrite
    )
    print(f"\n[OK] [3] Auditoria lista: {len(todas)} cruzados | "
          f"{len(alerta)} en Alerta (<20%) | {len(sin_par)} sin pareja\n"
          "     -> /DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx")

if __name__ == "__main__":
    abrir_esqueleto()
