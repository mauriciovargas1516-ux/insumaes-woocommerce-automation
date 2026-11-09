import os, re, json, math, unicodedata, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
import conectar_meli, lee_config

def norm_k(s):
    if not s or str(s).upper() == "NAN": return ""
    t = ''.join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', t)).strip()

def nivelar_ahora(mostrar=True):
    hdr = {"Authorization": f"Bearer {conectar_meli.obtener_token_valido()}", "Content-Type": "application/json"}
    p_am, p_aw, p_ml, p_mem, p_rm = [os.path.expanduser(x) for x in ("~/AUDITORIA_MELI_INSUMAES.xlsx", "~/AUDITORIA_PRE_SYNC.xlsx", "~/meli_api_items_full.json", "~/estado_stocks_delta.json", "~/mapas_rapidos_cache.json")]
    info_ml = json.load(open(p_ml, "r", encoding="utf-8")) if os.path.exists(p_ml) else {}
    mem_delta = json.load(open(p_mem, "r", encoding="utf-8")) if os.path.exists(p_mem) else {}
    df_m = pd.read_excel(p_am) if os.path.exists(p_am) else pd.DataFrame()
    df_w = pd.read_excel(p_aw) if os.path.exists(p_aw) else pd.DataFrame()
    if df_m.empty: return 0

    col_pct = float(lee_config.obtener_valor("PORCENTAJE_COLCHON", 50) or 50) / 100.0
    if not df_w.empty and mem_delta:
        for iw, rw in df_w.iterrows():
            kl = norm_k(rw.get("PRODUCTO LOCAL", ""))
            if kl in mem_delta and isinstance(mem_delta[kl], dict) and "s" in mem_delta[kl]:
                st_v = int(mem_delta[kl]["s"])
                nw = str(rw.get("PRODUCTO WEB", "")).upper()
                mp = re.search(r'(?:\(|PACK\s+)(\d+)\s*(?:UNIDADES|UN)\)?', nw)
                pk_w = max(1, int(mp.group(1))) if (mp and "JUEGO" not in nw and "JGO" not in nw) else 1
                mw = math.ceil((st_v // pk_w) * col_pct) if (st_v // pk_w) > 0 else 0
                df_w.at[iw, "STOCK FÍSICO (Real)"] = st_v
        df_w.to_excel(p_aw, index=False)

    mlcs = [str(x).strip() for x in df_m["Código ML (Ver Web)"].dropna().unique() if str(x).strip().startswith("MLC")]
    if mostrar: print(f"\n📡 1. Leyendo stock EN VIVO de tus {len(mlcs)} publicaciones en Mercado Libre...")
    for i in range(0, len(mlcs), 20):
        try:
            for ob in requests.get(f"https://api.mercadolibre.com/items?ids={','.join(mlcs[i:i+20])}", headers=hdr, timeout=15).json():
                b = ob.get("body", {}); mid = b.get("id")
                if mid:
                    info_ml.setdefault(mid, {})["status"] = b.get("status", ""); info_ml[mid]["qty"] = int(b.get("available_quantity") or 0)
                    info_ml[mid]["price"] = int(b.get("price") or 0); info_ml[mid]["title"] = b.get("title", "")
        except Exception: pass

    w_by_sku, w_by_nom = {}, {}
    for _, rw in df_w.iterrows():
        wid = str(rw.get("ID_WOO", "")).strip()
        if not wid or wid.lower() in ("nan", "none", "---"): continue
        es_p = "PACK" in str(rw.get("PRODUCTO WEB", "")).upper()
        sl, nl = str(rw.get("SKU LOCAL", "")).strip().upper().replace(".0", ""), str(rw.get("PRODUCTO LOCAL", "")).strip().upper()
        if sl and sl not in ("NAN", "---", "") and (sl not in w_by_sku or not es_p): w_by_sku[sl] = rw
        if nl and nl not in ("NAN", "---", "") and (nl not in w_by_nom or not es_p): w_by_nom[nl] = rw

    meli_on = str(lee_config.obtener_valor("SINCRONIZAR_MELI_STOCK", "NO")).upper() == "SI"
    tareas_sync = []
    for idx, rm in df_m.iterrows():
        mlc = str(rm.get("Código ML (Ver Web)", "")).strip()
        if not mlc.startswith("MLC") or "Sin Pareja" in str(rm.get("Estado", "")): continue
        sku_ml = str(info_ml.get(mlc, {}).get("sku", "") or "").strip().upper()
        nom_ex = str(rm.get("Nombre en tu Excel (Ir a Celda)", "") if pd.notna(rm.get("Nombre en tu Excel (Ir a Celda)")) else "").strip()
        rw = w_by_sku.get(sku_ml) if (sku_ml and sku_ml in w_by_sku) else w_by_nom.get(nom_ex.upper())
        upk = int(float(rm.get("Unid. x Pack", 1) or 1)) if pd.notna(rm.get("Unid. x Pack")) else 1
        kv = norm_k(rw.get("PRODUCTO LOCAL", nom_ex) if rw is not None else nom_ex)
        if kv in mem_delta and isinstance(mem_delta[kv], dict) and "s" in mem_delta[kv]: bod = int(mem_delta[kv]["s"])
        elif rw is not None and pd.notna(rw.get("STOCK FÍSICO (Real)")): bod = int(round(float(rw.get("STOCK FÍSICO (Real)") or 0)))
        else: bod = int(round(float(rm.get("Stock Bodega") or 0))) if pd.notna(rm.get("Stock Bodega")) else 0

        pks = bod // max(1, upk)
        meta_ml = 0 if pks <= 0 else (1 if pks == 1 else int(math.floor(pks * col_pct + 0.5)))
        st_act = info_ml.get(mlc, {}).get("status", "active")
        qty_act = int(info_ml.get(mlc, {}).get("qty", 0)) if st_act == "active" else 0
        tit = info_ml.get(mlc, {}).get("title", str(rm.get("Nombre en Mercado Libre", "")))
        df_m.at[idx, "Stock Bodega"] = bod; df_m.at[idx, "Packs en Bodega"] = pks; df_m.at[idx, "Meta ML (Colchón 50%)"] = meta_ml

        if meli_on and meta_ml > 0 and st_act == "active" and qty_act != meta_ml:
            tareas_sync.append((idx, mlc, tit, qty_act, meta_ml, {"available_quantity": meta_ml}))
        elif meli_on and meta_ml <= 0 and st_act == "active":
            tareas_sync.append((idx, mlc, tit, qty_act, 0, {"status": "paused"}))
        else: df_m.at[idx, "Publicado Hoy en ML"] = qty_act

    if mostrar: print(f"⚡ 2. Nivelando en paralelo {len(tareas_sync)} publicaciones con la memoria viva de Dropbox...")
    def _go(t):
        idx, mlc, tit, qa, qn, pl = t
        return (idx, mlc, tit, qa, qn, requests.put(f"https://api.mercadolibre.com/items/{mlc}", headers=hdr, json=pl, timeout=12).status_code in (200, 201))

    ok_s = 0
    if tareas_sync:
        with ThreadPoolExecutor(max_workers=10) as ex:
            for idx, mlc, tit, qa, qn, ok in ex.map(_go, tareas_sync):
                if ok:
                    ok_s += 1; df_m.at[idx, "Publicado Hoy en ML"] = qn; info_ml.setdefault(mlc, {})["qty"] = qn
                    if qn == 0:
                        info_ml[mlc]["status"] = "paused"; df_m.at[idx, "Estado"] = "⏸️ Ya Pausado en ML"
                        lee_config.registrar_evento("MELI-PAUSA", mlc, tit, f"active ({qa} uds) -> paused (0 uds)")
                    else:
                        df_m.at[idx, "Estado"] = "✅ Activo"; lee_config.registrar_evento("MELI-STOCK", mlc, tit, f"{qa} uds -> {qn} uds")

    json.dump(info_ml, open(p_ml, "w", encoding="utf-8")); df_m.to_excel(p_am, index=False)
    if os.path.exists(p_rm): os.remove(p_rm)
    if mostrar: print(f"✅ ¡Listo! {ok_s} publicaciones actualizadas (Aceite Soluble 2L MLC1330603276 -> {info_ml.get('MLC1330603276', {}).get('qty')} uds).")
    return ok_s

if __name__ == "__main__": nivelar_ahora(True)
