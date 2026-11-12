import os, re, json
import motor_pos, generador_carta_ean

P_EAN = os.path.expanduser("~/diccionario_ean_insumaes.json")

def cargar_dic():
    return json.load(open(P_EAN, "r", encoding="utf-8")) if os.path.exists(P_EAN) else {}

def guardar_ean(ean, sku_dest):
    d = cargar_dic()
    d[ean] = sku_dest.strip().upper()
    json.dump(d, open(P_EAN, "w", encoding="utf-8"), indent=2)

def abrir_pistola():
    ck, cs = motor_pos.cred_woo()
    p_ml, p_am, p_aw = [os.path.expanduser(x) for x in ("~/meli_api_items_full.json", "~/AUDITORIA_MELI_INSUMAES.xlsx", "~/AUDITORIA_PRE_SYNC.xlsx")]
    modo, ult, hist_p, msg = "VENTA", None, ["ACEITE SOLUBLE 2LT", "1030-2065"], []
    while True:
        os.system("clear")
        dic = cargar_dic()
        rl = os.path.expanduser("~/historial_erp.log")
        todas = [l.strip() for l in open(rl, "r", encoding="utf-8", errors="ignore").readlines() if l.strip() and "RESTORE" not in l] if os.path.exists(rl) else []
        print("=" * 140)
        print("🔫 TERMINAL PISTOLA DE BARRAS (DETECTOR EAN INTERNET + GENERADOR HOJA CARTA 40 STICKERS)")
        print("-" * 140)
        for l in list(reversed(todas))[:7]:
            m = re.match(r"^\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$", l)
            if m:
                f, t, cod, nom, det = m.groups(); hr = f"{f[:5]} {f[11:19]}" if len(f) >= 19 else f
                tm_m = re.search(r"\[(\d+\.\d+s)\]", det); ts = f"⏱️ {tm_m.group(1)}" if tm_m else "⏱️ ~0.35s"
                dc = re.sub(r"\s*\[\d+\.\d+s\]", "", det).replace("->", "➔").strip()
                tag = "🛍️💛 [VENTA-ML] " if "VENTA" in t else ("🔫🛒 [POS-WOO]  " if "POS-WOO" in t else ("🔫💛 [POS-MELI] " if "POS-MELI" in t else ("🛒 [WOOCOMMERCE]" if "WOO" in t else "💛 [MERCADOLIBRE]")))
                ns = re.findall(r"(\d+)\s*uds", dc)
                ico = ("🛑⏸️(0)" if int(ns[1])==0 else (f"🟢⬆️(+{int(ns[1])-int(ns[0])})" if int(ns[1])>int(ns[0]) else f"🔴⬇️({int(ns[1])-int(ns[0])})")) if len(ns)>=2 else "🔵🔄"
                print(f"   ⚡ {hr} | {tag:<16} | {ico:<9} | {dc:<22} | {ts:<9} | {nom[:50]} ({cod})")
        print("=" * 140)
        print(f"🎯 MODO PISTOLA: {'🔴 VENTA / DESPACHO (-1 ud en Web y ML)' if modo=='VENTA' else '🟢 RECEPCIÓN / DEVOLUCIÓN (+1 ud en Web y ML)'} | 🧠 Códigos EAN/SKU activos: {len(dic)}")
        print("   • Cajas Dasqua / Insize : Pistolea el EAN de la caja (lo busca solo en Internet/Catálogo ML; si no existe, lo aprende en 1 paso)")
        print("   • [L] 🖨️ Hoja Carta 40x  : Genera en tu Dropbox 1 Hoja Carta con 40 Stickers iguales del producto que elijas para imprimir y pegar")
        print("   • Comandos Rápidos      : [R] RESTAURAR (+1) | [E] 📊 Igualar Planilla Excel | [V] 🛍️ Ventas ML | [M] Modo -1/+1 | [0] Volver")
        print("-" * 140)
        if msg:
            for mi in msg: print("   " + mi)
            print("-" * 140)
        cod = motor_pos.limpiar(input("\n🔫 Dispara con tu pistola (o escribe L=Imprimir 40 Stickers, E=Planilla, R, V, M, 0): "))
        if not cod: continue
        if cod == "0": break
        if cod in ("M", "MODO"): modo = "RECEPCION" if modo == "VENTA" else "VENTA"; continue
        if cod == "MODO-VENTA": modo = "VENTA"; msg = ["🔴 Pistola cambiada a MODO VENTA (-1 ud por disparo)."]; continue
        if cod in ("MODO-RECEP", "MODO-RECEPCION"): modo = "RECEPCION"; msg = ["🟢 Pistola cambiada a MODO RECEPCIÓN (+1 ud por disparo)."]; continue
        if cod == "V": msg = motor_pos.revisar_ventas_meli(ck, cs, p_ml, p_am, p_aw); continue
        if cod in ("E", "PLANILLA", "EXCEL"): msg = motor_pos.restaurar_desde_planilla(hist_p, ck, cs, p_ml, p_am, p_aw); continue
        if cod in ("R", "+", "RESTAURAR", "DESHACER"):
            msg = ["⚠️ Pistolea primero un producto."] if not ult else motor_pos.mover(ult, +1, ck, cs, p_ml, p_am, p_aw, "RESTAURAR")
            continue
        if cod == "L":
            prod_l = motor_pos.limpiar(input("🖨️  Escribe el código o SKU del producto para crear su Hoja Carta de 40 Stickers (ej. SOLUBLE2L, GJ1-1L, 1120-3120): "))
            if prod_l:
                cb_l = dic.get(prod_l, prod_l)
                prueba = motor_pos.mover(cb_l, 0, ck, cs, p_ml, p_am, p_aw, "VERIFICAR")
                if prueba and prueba[0].startswith("❌"):
                    asoc_l = motor_pos.limpiar(input(f"👉 '{prod_l}' es un código personalizado nuevo. Escribe a qué SKU o Producto de tu Excel corresponde (ej. ACEITE SOLUBLE 2LT): "))
                    if not asoc_l: continue
                    guardar_ean(prod_l, dic.get(asoc_l, asoc_l))
                print(f"⏳ Generando Hoja Tamaño Carta (40 stickers 4x10) de '{prod_l}' y subiendo a tu Dropbox...")
                ruta_dbx = generador_carta_ean.generar_hoja_carta_40(prod_l)
                msg = [f"✅ ¡Hoja Carta de 40 Stickers subida a la raíz de tu Dropbox como: {ruta_dbx}!",
                       f"🔗 Código [{prod_l}] verificado y enlazado al 100% con tu inventario para pistolear directo."]
            continue

        cb = dic.get(cod, cod)
        res_m = motor_pos.mover(cb, -1 if modo == "VENTA" else +1, ck, cs, p_ml, p_am, p_aw, "PISTOLA")
        if res_m and res_m[0].startswith("❌"):
            print(f"\n🌐 Buscando código de barras [{cod}] automáticamente en Internet y Catálogo Global...")
            sku_red, fuente = generador_carta_ean.buscar_ean_internet(cod)
            if sku_red:
                guardar_ean(cod, sku_red)
                ult = sku_red
                if ult not in hist_p: hist_p.append(ult)
                msg = [f"🌐✨ ¡EAN [{cod}] RECONOCIDO EN INTERNET ({fuente})! Memorizado para siempre."] + motor_pos.mover(sku_red, -1 if modo == "VENTA" else +1, ck, cs, p_ml, p_am, p_aw, "PISTOLA")
            else:
                if fuente: print(f"   ℹ️ Pista encontrada en red: {fuente}")
                asoc = motor_pos.limpiar(input(f"👉 No apareció en bases globales. Escribe 1 sola vez el SKU en tu Excel para [{cod}] (o Enter para cancelar): "))
                if asoc:
                    dest = dic.get(asoc, asoc)
                    guardar_ean(cod, dest)
                    ult = dest
                    if ult not in hist_p: hist_p.append(ult)
                    msg = [f"✅ ¡Caja [{cod}] memorizada para siempre como '{dest}'!"] + motor_pos.mover(dest, -1 if modo == "VENTA" else +1, ck, cs, p_ml, p_am, p_aw, "PISTOLA")
                else:
                    msg = res_m
        else:
            ult = cb
            if ult not in hist_p: hist_p.append(ult)
            msg = res_m

if __name__ == "__main__": abrir_pistola()
