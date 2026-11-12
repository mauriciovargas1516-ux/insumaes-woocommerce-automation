import os, re, json, time, dropbox
import pandas as pd
import html
from woocommerce import API

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
    f_woo = os.path.expanduser("~/respaldo_html_completo_woo.json")
    f_map = os.path.expanduser("~/mapas_rapidos_cache.json")
    if not os.path.exists(f_woo):
        print("\n⚠️ Primero ejecuta el respaldo HTML en el Botón [22 -> 6]."); return

    datos_woo = json.load(open(f_woo, "r", encoding="utf-8"))
    mapas = json.load(open(f_map, "r", encoding="utf-8")) if os.path.exists(f_map) else {}
    meli_vinculados = set()
    for k_sub in ("meli_por_sku", "meli_por_nombre", "meli"):
        if isinstance(mapas.get(k_sub), dict):
            meli_vinculados.update(str(x).strip().upper() for x in mapas[k_sub].keys())

    listos_para_ml, sin_foto_web = [], []
    for pid, p in datos_woo.items():
        nom = (p.get("name") or "").strip()
        sku = (p.get("sku") or "").strip()
        try: pr = float(p.get("regular_price") or p.get("price") or 0)
        except Exception: pr = 0.0
        try: st = int(float(p.get("stock_quantity") or 0))
        except Exception: st = 0
        imgs = p.get("images") or []
        cats = " | ".join(c.get("name", "") for c in (p.get("categories") or []))
        url_foto = imgs[0].get("src", "") if imgs else ""

        if pr > 0 and st > 0:
            if not url_foto:
                sin_foto_web.append({"ID_WOO": int(pid), "SKU": sku, "Nombre": nom, "Precio_Web_IVA": int(pr), "Stock_Web_40pct": st, "Categorias": cats})
            elif nom.upper() not in meli_vinculados and (not sku or sku.upper() not in meli_vinculados):
                listos_para_ml.append({
                    "ID_WOO": int(pid), "SKU": sku, "Titulo_Sugerido_ML": nom[:60],
                    "Categoria_Web": cats, "Stock_Disponible_40pct": st,
                    "Precio_Web_IVA": int(pr), "Precio_Sugerido_ML_Mas_18pct": int(round((pr * 1.18) / 100.0) * 100),
                    "URL_Foto_Principal": url_foto,
                    "Descripcion_Texto_Plano_ML": limpiar_html_plano(p.get("description", ""))[:1500]
                })

    f_out = os.path.expanduser("~/BRECHA_EXPANSION_WOO_A_MELI.xlsx")
    with pd.ExcelWriter(f_out, engine="openpyxl") as wr:
        pd.DataFrame(listos_para_ml).to_excel(wr, sheet_name="Listos_Para_Subir_a_ML", index=False)
        pd.DataFrame(sin_foto_web).to_excel(wr, sheet_name="Con_Stock_Pero_Sin_Foto", index=False)

    dbx.files_upload(open(f_out, "rb").read(), "/BRECHA_EXPANSION_WOO_A_MELI.xlsx", mode=dropbox.files.WriteMode.overwrite)
    print("\n" + "=" * 92)
    print("📊 RESULTADO DEL ESCÁNER DE BRECHAS OMNICANAL (WOO -> MERCADO LIBRE)")
    print("=" * 92)
    print(f" 🚀 Productos con Stock, Precio y Foto listos para subir a ML : {len(listos_para_ml)} productos")
    print(f" 📸 Productos con Stock y Precio en Web pero SIN fotografía   : {len(sin_foto_web)} productos")
    print(" ☁️ Excel subido a la raíz de tu Dropbox: /BRECHA_EXPANSION_WOO_A_MELI.xlsx")
    print("=" * 92)

def generar_kit_cliente_nuevo():
    _, dbx, _ = conectar_todo()
    env_example = "\n".join([
        "# ==============================================================================",
        "# PLANTILLA DE CREDENCIALES (.env.example) - ESQUELETO OMNICANAL CLOUD",
        "# Copia este archivo como ~/.env en el servidor del cliente y rellena sus llaves",
        "# ==============================================================================",
        'WOO_URL="https://www.tienda-cliente.cl/"',
        'WOO_KEY="ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"',
        'WOO_SECRET="cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"',
        'DROPBOX_APP_KEY="xxxxxxxxxxxxxxx"',
        'DROPBOX_APP_SECRET="xxxxxxxxxxxxxxx"',
        'DROPBOX_REFRESH_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"',
        'MELI_APP_ID="xxxxxxxxxxxxxxxx"',
        'MELI_CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"',
        'MELI_REFRESH_TOKEN="TG-xxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxx"',
        'GMAIL_USER="reportes@tienda-cliente.cl"',
        'GMAIL_PASS="xxxx xxxx xxxx xxxx"',
        ""
    ])
    open(os.path.expanduser("~/.env.example"), "w", encoding="utf-8").write(env_example)

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
    dbx.files_upload(open(f_molde, "rb").read(), "/PLANTILLA_ONBOARDING_CLIENTE_NUEVO.xlsx", mode=dropbox.files.WriteMode.overwrite)
    print("\n✅ Kit de Comercialización creado con éxito:")
    print("   1) Molde '~/.env.example' listo para tu repositorio GitHub (0% claves reales expuestas).")
    print("   2) Planilla '/PLANTILLA_ONBOARDING_CLIENTE_NUEVO.xlsx' subida a la raíz de tu Dropbox.")

def abrir_esqueleto():
    while True:
        os.system("clear")
        print("=" * 96)
        print("🚀  BOTÓN [26]: ESQUELETO INTEGRADOR OMNICANAL (BRECHAS WOO->ML & KIT CLIENTES NUEVOS)")
        print("=" * 96)
        print("  [1] 🔍 Detectar Brechas en Insumaes (Productos listos en Web que faltan en ML + Web sin foto)")
        print("  [2] 📦 Generar Kit 'Llave en Mano' para Clientes Nuevos (.env.example + Plantilla Excel)")
        print("  [0] 🔙 Volver al Panel Principal")
        print("=" * 96)
        op = input("\n👉 Selecciona una opción (0-2): ").strip()
        if op == "0": break
        elif op == "1": detectar_brechas_omnicanal(); input("\nPresiona Enter para continuar...")
        elif op == "2": generar_kit_cliente_nuevo(); input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    import sys
    if "--init" in sys.argv:
        generar_kit_cliente_nuevo()
    else:
        abrir_esqueleto()
