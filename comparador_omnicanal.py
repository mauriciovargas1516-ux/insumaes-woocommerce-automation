import lee_config
import os, math, json, pandas as pd

def num(v):
    try:
        if pd.isna(v): return 0
        s = str(v).strip()
        return 0 if (not s or s.lower() in ("nan", "none", "---")) else int(round(float(s)))
    except Exception: return 0

def abrir_comparador():
    p_ml, p_am, p_aw = [os.path.expanduser(x) for x in ("~/meli_api_items_full.json", "~/AUDITORIA_MELI_INSUMAES.xlsx", "~/AUDITORIA_PRE_SYNC.xlsx")]
    info_ml = json.load(open(p_ml, "r", encoding="utf-8")) if os.path.exists(p_ml) else {}
    df_m = pd.read_excel(p_am) if os.path.exists(p_am) else pd.DataFrame()
    df_w = pd.read_excel(p_aw) if os.path.exists(p_aw) else pd.DataFrame()

    w_by_sku, w_by_nom = {}, {}
    for _, rw in df_w.iterrows():
        wid = str(rw.get("ID_WOO", "")).strip()
        if not wid or wid.lower() in ("nan", "none", "---"): continue
        es_pack = "PACK" in str(rw.get("PRODUCTO WEB", "")).upper()
        sl, nl = str(rw.get("SKU LOCAL", "")).strip().upper().replace(".0", ""), str(rw.get("PRODUCTO LOCAL", "")).strip().upper()
        if sl and sl not in ("NAN", "---", "") and (sl not in w_by_sku or not es_pack): w_by_sku[sl] = rw
        if nl and nl not in ("NAN", "---", "") and (nl not in w_by_nom or not es_pack): w_by_nom[nl] = rw

    filas = []
    for _, rm in df_m.iterrows():
        mlc = str(rm.get("Código ML (Ver Web)", "")).strip()
        if not mlc or mlc.lower() == "nan": continue
        sku_ml = str(info_ml.get(mlc, {}).get("sku", "") or "").strip().upper()
        nom_ex = str(rm.get("Nombre en tu Excel (Ir a Celda)", "") if pd.notna(rm.get("Nombre en tu Excel (Ir a Celda)")) else "").strip()
        if not nom_ex or nom_ex.lower() == "nan": nom_ex = str(rm.get("Nombre en Mercado Libre", "") or "SIN PAREJA EN EXCEL").strip()
        pes = str(rm.get("Pestaña del Excel", "") if pd.notna(rm.get("Pestaña del Excel")) else "").strip()
        rw = w_by_sku.get(sku_ml) if (sku_ml and sku_ml in w_by_sku) else w_by_nom.get(nom_ex.upper())
        en_web = rw is not None

        bod = num(rw.get("STOCK FÍSICO (Real)") if en_web else rm.get("Stock Bodega"))
        sw = num(rw.get("STOCK WEB")) if en_web else -1
        upk = max(1, num(rm.get("Unid. x Pack", 1)) or 1)
        st_api = info_ml.get(mlc, {}).get("status", "active")
        sml = num(info_ml.get(mlc, {}).get("qty", rm.get("Publicado Hoy en ML", 0))) if st_api == "active" else 0
        pks_bod = bod // upk
        meta_ml = sw if (en_web and upk == 1) else (0 if pks_bod <= 0 else (1 if pks_bod == 1 else int(math.floor(pks_bod * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0) + 0.5))))

        pw = num(rw.get("PRECIO WEB") if en_web else rm.get("Precio Excel"))
        pml = num(info_ml.get(mlc, {}).get("price", 0) or rm.get("Precio ML", 0))
        sku_show = sku_ml or (str(rw.get("SKU LOCAL", "")).strip().replace(".0", "") if en_web and pd.notna(rw.get("SKU LOCAL")) else "---")
        if sku_show.lower() in ("nan", "none", ""): sku_show = "---"
        nom_mostrar = str(rw.get("PRODUCTO LOCAL", nom_ex)) if (en_web and pd.notna(rw.get("PRODUCTO LOCAL"))) else nom_ex
        filas.append({
            "mlc": mlc, "sku": sku_show, "nombre": nom_mostrar, "pestana": pes, "en_web": en_web,
            "bod": bod, "sw": sw, "sml": sml, "upk": upk, "meta_ml": meta_ml, "pw": pw, "pml": pml,
            "tiene_sku_ml": bool(sku_ml), "alerta_pr": (pw * upk > 0 and pml > 0 and pml < pw * upk), "alerta_st": (en_web and sml != meta_ml)
        })

    modo, filtro, pag = "SKU", "", 1
    while True:
        os.system("clear")
        if modo == "SKU": lista, tit_m = [x for x in filas if x["tiene_sku_ml"] and x["en_web"]], "🏷️  MODO [1]: ENGANCHADOS POR SKU EN AMBAS TIENDAS"
        elif modo == "ALERTAS": lista, tit_m = [x for x in filas if x["alerta_pr"] or x["alerta_st"]], "🚨 MODO [2]: DIFERENCIAS DE STOCK O PRECIO ML < NETO WEB"
        elif modo == "SOLO_ML": lista, tit_m = [x for x in filas if not x["en_web"]], "💛 MODO [3]: EN MERCADO LIBRE PERO FALTAN POR SUBIR A INSUMAES.CL"
        elif modo == "PACKS": lista, tit_m = [x for x in filas if x["upk"] > 1], "📦 MODO [5]: PUBLICACIONES EN PACK / CAJA EN MERCADO LIBRE (x2, x5, x10, x20)"
        else: lista, tit_m = list(filas), "🌐 MODO [4]: CATÁLOGO COMPLETO COMPARADO (WOO vs MELI)"

        if filtro: lista = [x for x in lista if filtro in x["nombre"].upper() or filtro in x["sku"].upper() or filtro in x["mlc"].upper() or filtro in x["pestana"].upper()]
        import shutil; por_pag = max(22, shutil.get_terminal_size((132, 70)).lines - 9); tot_pag = max(1, (len(lista) + por_pag - 1) // por_pag); pag = min(max(1, pag), tot_pag); ini = (pag - 1) * por_pag
        n_ambas = sum(1 for x in filas if x["en_web"]); n_iguales = sum(1 for x in filas if x["en_web"] and not x["alerta_st"])
        n_packs = sum(1 for x in filas if x["en_web"] and x["upk"] > 1); n_al_pr = sum(1 for x in filas if x["alerta_pr"])

        print("=" * 146)
        print(f"🔍 AUDITOR COMPARADOR OMNICANAL (insumaes.cl vs Mercado Libre) — {tit_m}")
        print(f"📊 En Ambas Tiendas: {n_ambas} ítems | ✅ Nivelados Exactos: {n_iguales}/{n_ambas} (incluye {n_packs} Packs x2/x5/x10) | ⚡ Desfase Real: {n_ambas-n_iguales} | 🚨 Precio ML < Neto: {n_al_pr}")
        if filtro: print(f"🔎 Filtro activo: '{filtro}' ({len(lista)} resultados)")
        print("=" * 146)
        print(f"{'SKU':<12} | {'PRODUCTO EN TU EXCEL / BODEGA':<42} | {'BODEGA':>6} | {'STOCK WEB':>9} | {'STOCK ML (PACK)':>15} | {'PRECIO WEB (+IVA)':>17} | {'PRECIO ML (API)':>15} | {'CÓDIGO ML':<13}")
        print("-" * 146)
        for x in lista[ini:ini + por_pag]:
            sw_s = f"{x['sw']:>9}" if x["en_web"] else "  NO WEB "
            pk_tag = f"(x{x['upk']})" if x["upk"] > 1 else "    "
            ico_s = "✅=" if (x["en_web"] and not x["alerta_st"]) else ("⚡≠" if x["en_web"] else "💛ML")
            ico_p = "🚨" if x["alerta_pr"] else "  "
            print(f"{x['sku'][:12]:<12} | {x['nombre'][:42]:<42} | {x['bod']:>6} | {sw_s} | {x['sml']:>4} {pk_tag:<5} {ico_s} | ${x['pw']:>10,} + IVA | {ico_p}${x['pml']:>12,} | {x['mlc']:<13}".replace(",", "."))
        print("=" * 146)
        print(f"📄 Pág {pag}/{tot_pag} ({len(lista)} ítems) | [Enter/S] Sig | [A] Ant | [1] SKU | [2] Alertas | [3] Solo ML | [4] Todos | [5] 📦Packs | [B] Buscar | [N] ⚡Nivelar | [0] Volver")
        op = input("👉 Opción: ").strip().upper()
        if op == "0": break
        elif op in ("", "S"):
            if pag < tot_pag: pag += 1
        elif op == "A": pag = max(1, pag - 1)
        elif op == "1": modo, filtro, pag = "SKU", "", 1
        elif op == "2": modo, filtro, pag = "ALERTAS", "", 1
        elif op == "3": modo, filtro, pag = "SOLO_ML", "", 1
        elif op == "4": modo, filtro, pag = "TODOS", "", 1
        elif op == "5": modo, filtro, pag = "PACKS", "", 1
        elif op == "N":
            import nivelar_meli_vivo; nivelar_meli_vivo.nivelar_ahora(True); input("\nEnter para recargar tabla..."); return abrir_comparador()
        elif op == "B":
            filtro = input("🔎 Escribe nombre, SKU, medida o MLC (Enter para limpiar): ").strip().upper(); pag = 1

if __name__ == "__main__": abrir_comparador()
