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

def abrir_esqueleto():
    while True:
        os.system("clear")
        print("=" * 96)
        print("🚀  BOTÓN [26]: ESQUELETO INTEGRADOR OMNICANAL (BRECHAS WOO->ML & KIT CLIENTES NUEVOS)")
        print("=" * 96)
        print("  [1] 🔍 Detectar Brechas en Insumaes (Productos listos en Web que faltan en ML + Web sin foto)")
        print("  [2] 📦 Generar Kit 'Llave en Mano' para Clientes Nuevos (Con Columnas y Filas Auto-Ajustadas)")
        print("  [0] 🔙 Volver al Panel Principal")
        print("=" * 96)
        op = input("\n👉 Selecciona una opción (0-2): ").strip()
        if op == "0": break
        elif op == "1": detectar_brechas_omnicanal(); input("\nPresiona Enter para continuar...")
        elif op == "2": generar_kit_cliente_nuevo(); input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    import sys
    if "--run" in sys.argv:
        detectar_brechas_omnicanal()
        generar_kit_cliente_nuevo()
        _, dbx, _ = conectar_todo()
        for nom_x in ("CRM_MAESTRO_NACIONAL_INSUMAES.xlsx", "REPORTE_MAESTRO_COTIZACIONES_2026.xlsx"):
            p_x = os.path.expanduser(f"~/{nom_x}")
            if os.path.exists(p_x):
                formateador_excel_cloud.estilizar_excel_pro(p_x)
                dbx.files_upload(open(p_x, "rb").read(), f"/{nom_x}", mode=dropbox.files.WriteMode.overwrite)
                print(f"✨ '{nom_x}' auto-ajustado en alto/ancho y actualizado en tu Dropbox.")
    else:
        abrir_esqueleto()
