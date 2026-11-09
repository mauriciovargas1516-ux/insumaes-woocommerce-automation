import os, re, time, math, json, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
import conectar_meli, lee_config
os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass
SW, SM = requests.Session(), requests.Session()

def limpiar(r):
    s = str(r or "").strip().upper().strip("*").strip()
    return re.sub(r"['\?]+", "-", re.sub(r"(\d)['\?/_]+(\d)", r"\1-\2", s))

def cred_woo():
    for fn in ("~/.env", "~/descargador_web.py", "~/sincronizador_silencioso.py", "~/motor_insumaes.py"):
        p = os.path.expanduser(fn)
        if os.path.exists(p):
            t = open(p, "r", encoding="utf-8", errors="ignore").read()
            ck, cs = re.search(r'(ck_[a-fA-F0-9]{30,45})', t), re.search(r'(cs_[a-fA-F0-9]{30,45})', t)
            if ck and cs: return ck.group(1), cs.group(1)
    return None, None

def revisar_ventas_meli(ck, cs, p_ml, p_am, p_aw):
    tk = conectar_meli.obtener_token_valido()
    hdr = {"Authorization": f"Bearer {tk}"}
    uid = str(tk).strip().split("-")[-1]
    if not uid.isdigit():
        uid = str(requests.get("https://api.mercadolibre.com/users/me", headers=hdr, timeout=10).json().get("id", ""))
    pv = os.path.expanduser("~/ordenes_meli_vistas.json")
    vistas = set(json.load(open(pv))) if os.path.exists(pv) else set()
    rj = requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&sort=date_desc&limit=15", headers=hdr, timeout=12).json()
    ords = [o for o in rj.get("results", []) if o.get("status") != "cancelled"]
    ult_5 = []
    for o in ords[:5]:
        oid = o.get("id")
        fec = str(o.get("date_closed") or o.get("date_created") or "")[:16].replace("T", " ")
        comp = o.get("buyer", {}).get("nickname", "Cliente")
        for oi in (o.get("order_items") or []):
            it = oi.get("item", {})
            ult_5.append(f"   🧾 Orden #{oid} ({fec}) | {comp:<14} | x{oi.get('quantity',1)} ud | ${int(oi.get('unit_price',0)):>7,} | {it.get('title','')[:42]} ({it.get('id','')})".replace(",", "."))
    if not vistas:
        vistas = {str(o.get("id")) for o in ords}
        if vistas: json.dump(list(vistas), open(pv, "w"))
        return [f"🛍️ Vigía de Ventas ML conectado a tu Seller ID {uid} ({len(vistas)} órdenes recientes en memoria).",
                "📋 Últimas 5 ventas reales detectadas en tu cuenta de Mercado Libre:"] + ult_5 + [
                "✅ A partir de ahora, toda nueva venta que entre después del SDNCN1212H07 descontará sola en insumaes.cl."]
    nuevas = [o for o in reversed(ords) if str(o.get("id")) not in vistas]
    if not nuevas:
        return ["✅ Sin ventas nuevas en Mercado Libre después de tu última orden (SDNCN1212H07).",
                "📋 Tus últimas 5 ventas reales registradas en Mercado Libre:"] + ult_5
    msgs = [f"🚨 ¡{len(nuevas)} VENTA(S) NUEVA(S) DETECTADA(S) EN MERCADO LIBRE! Descontando en insumaes.cl:"]
    for o in nuevas:
        vistas.add(str(o.get("id")))
        for oi in (o.get("order_items") or []):
            msgs.extend(mover(str(oi.get("item", {}).get("id", "")).strip(), -int(oi.get("quantity", 1) or 1), ck, cs, p_ml, p_am, p_aw, "VENTA-ML"))
    json.dump(list(vistas)[-200:], open(pv, "w"))
    return msgs


def leer_bodega_planilla(nl):
    pm = os.path.expanduser("~/estado_stocks_delta.json")
    if os.path.exists(pm):
        try:
            d = json.load(open(pm, "r", encoding="utf-8"))
            k = re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', nl.upper()).strip()
            for cand in (k, nl.upper().strip()):
                if cand in d and isinstance(d[cand], dict) and "s" in d[cand]:
                    return int(d[cand]["s"]), os.path.getmtime(pm)
        except Exception: pass
    return None, 0

def restaurar_desde_planilla(cods_hist, ck, cs, p_ml, p_am, p_aw):
    if not cods_hist:
        cods_hist = ["ACEITE SOLUBLE 2LT", "1030-2065", "1331-2115", "1120-3120"]
    msgs = ["📊 RESTAURANDO CANTIDADES EXACTAS DESDE TU PLANILLA EXCEL DE DROPBOX:"]
    vistos = set()
    for c in cods_hist:
        if c in vistos: continue
        vistos.add(c)
        msgs.extend(mover(c, 0, ck, cs, p_ml, p_am, p_aw, orig="PLANILLA-EXCEL"))
    return msgs

def mover(cb, du, ck, cs, p_ml, p_am, p_aw, orig="PISTOLA"):
    iml = json.load(open(p_ml, "r", encoding="utf-8")) if os.path.exists(p_ml) else {}
    dfm, dfw = pd.read_excel(p_am), pd.read_excel(p_aw)
    p_ean_f = os.path.expanduser("~/diccionario_ean_insumaes.json")
    dic_e = json.load(open(p_ean_f, "r", encoding="utf-8")) if os.path.exists(p_ean_f) else {}
    cb = dic_e.get(cb, cb)
    cb_norm = re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', cb.upper()).replace("SOLUBLE2L", "ACEITE SOLUBLE 2L").replace("SOLUBLE5L", "ACEITE SOLUBLE 5L").strip()
    nl, se = None, ""
    for _, rw in dfw.iterrows():
        sl = str(rw.get("SKU LOCAL", "")).strip().upper().replace(".0", "")
        pl = str(rw.get("PRODUCTO LOCAL", "")).strip().upper()
        pw = str(rw.get("PRODUCTO WEB", "")).strip().upper()
        pl_n = re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', pl)
        pw_n = re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', pw)
        if cb in (sl, pl, pw) or cb_norm in (sl, pl_n, pw_n) or (len(cb) >= 4 and cb in sl):
            if pl and pl != "---": nl, se = str(rw.get("PRODUCTO LOCAL", "")).strip(), sl; break
    if not nl:
        for _, rm in dfm.iterrows():
            mi = str(rm.get("Código ML (Ver Web)", "")).strip().upper()
            si = str(iml.get(mi, {}).get("sku", "")).strip().upper()
            ni = str(rm.get("Nombre en tu Excel (Ir a Celda)", "")).strip()
            ni_n = re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', ni.upper())
            if cb in (mi, si, ni.upper()) or cb_norm in (mi, si, ni_n) or (len(cb) >= 5 and (cb in ni.upper() or cb_norm in ni_n)):
                nl, se = ni, (si or mi); break
    if not nl: return [f"❌ Código '{cb}' no encontrado. Prueba 1331-2115, 1120-3120, 1030-2065 o SOLUBLE2L."]

    fw = dfw[dfw["PRODUCTO LOCAL"].astype(str).str.strip().str.upper() == nl.upper()].copy()
    fm = dfm[dfm["Nombre en tu Excel (Ir a Celda)"].astype(str).str.strip().str.upper() == nl.upper()].copy()
    st_planilla, mt_plan = leer_bodega_planilla(nl)
    mt_aud = os.path.getmtime(p_aw) if os.path.exists(p_aw) else 0
    ba_aud = int(float(fw["STOCK FÍSICO (Real)"].max() if not fw.empty else (fm["Stock Bodega"].max() if not fm.empty else 10)))
    usar_plan = (orig == "PLANILLA-EXCEL") or (st_planilla is not None and mt_plan > mt_aud)
    ba = st_planilla if (usar_plan and st_planilla is not None) else ba_aud
    bn = (st_planilla if st_planilla is not None else ba_aud) if orig == "PLANILLA-EXCEL" else max(0, ba + (du * 2))
    hml = {"Authorization": f"Bearer {conectar_meli.obtener_token_valido()}", "Content-Type": "application/json"}
    res, ts = [f"🏷️  [{orig}] {cb} ➔ {nl} (SKU: {se or 'DIRECTO'}) | Bodega: {ba} ➔ {bn} uds"], []

    for iw, rw in fw.iterrows():
        w = str(rw.get("ID_WOO", "")).strip()
        if not w or w.lower() in ("nan", "none", "---"): continue
        ep = f"products/{int(float(w.split('-')[0]))}/variations/{int(float(w.split('-')[1]))}" if "-" in w else f"products/{int(float(w))}"
        wc = f"{int(float(w.split('-')[0]))}-{int(float(w.split('-')[1]))}" if "-" in w else str(int(float(w)))
        nt = str(rw.get("PRODUCTO WEB", nl))
        mp = re.search(r'(?:\(|PACK\s+)(\d+)\s*(?:UNIDADES|UN)\)?', nt.upper())
        pk = max(1, int(mp.group(1))) if (mp and "JUEGO" not in nt.upper() and "JGO" not in nt.upper()) else 1
        sa = int(math.ceil((ba // pk) * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0))) if usar_plan else int(float(rw.get("STOCK WEB", 0) or 0))
        sn_w = max(0, int(math.ceil((bn // pk) * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0)))) if (orig == 'PLANILLA-EXCEL' or pk > 1) else max(0, sa + du)
        ts.append(("WOO", iw, wc, ep, nt, pk, int(float(rw.get("STOCK WEB", 0) or 0)), sn_w))
    if True:
        for im, rm in fm.iterrows():
            m = str(rm.get("Código ML (Ver Web)", "")).strip()
            if not m.startswith("MLC"): continue
            tm, pk = str(rm.get("Nombre en Mercado Libre", nl)), max(1, int(float(rm.get("Unid. x Pack", 1) or 1)))
            sa = int(math.floor((ba // pk) * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0) + 0.5)) if usar_plan else int(float(iml.get(m, {}).get("qty", rm.get("Publicado Hoy en ML", 0)) or 0))
            sn_m = (0 if (bn // pk) <= 0 else (1 if (bn // pk) == 1 else int(math.floor((bn // pk) * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0) + 0.5)))) if (orig == 'PLANILLA-EXCEL' or pk > 1) else max(0, sa + du)
            ts.append(("MELI", im, m, m, tm, pk, int(float(iml.get(m, {}).get("qty", rm.get("Publicado Hoy en ML", 0)) or 0)), sn_m))

    def _go(t):
        c, idx, idn, ep, tit, pk, sa, sn = t; t0 = time.time()
        if c == "WOO":
            r = SW.put(f"https://insumaes.cl/wp-json/wc/v3/{ep}", auth=(ck, cs), json={"stock_quantity": sn, "manage_stock": True, "stock_status": "instock" if sn > 0 else "outofstock"}, timeout=10)
            dt = time.time() - t0
            if r.status_code in (200, 201): lee_config.registrar_evento("VENTA-ML-WOO" if orig=="VENTA-ML" else "POS-WOO", f"ID:{idn}", tit, f"{sa} uds -> {sn} uds [{dt:.2f}s]")
        else:
            r = SM.put(f"https://api.mercadolibre.com/items/{ep}", headers=hml, json={"available_quantity": sn} if sn > 0 else {"status": "paused"}, timeout=10)
            dt = time.time() - t0
            if r.status_code in (200, 201): lee_config.registrar_evento("POS-MELI", idn, tit, f"{sa} uds -> {sn} uds [{dt:.2f}s]")
        return (c, idx, idn, tit, pk, sa, sn, dt)

    with ThreadPoolExecutor(max_workers=8) as ex:
        for c, idx, idn, tit, pk, sa, sn, dt in ex.map(_go, ts):
            plb = f" (Pack x{pk})" if pk > 1 else ""
            if c == "WOO":
                dfw.at[idx, "STOCK WEB"] = sn; dfw.at[idx, "STOCK LOCAL (Nuevo)"] = sn; dfw.at[idx, "STOCK FÍSICO (Real)"] = bn
                res.append(f"🛒 [WOOCOMMERCE ID:{idn}]{plb:<10} : {sa} uds ➔ {sn} uds | ⏱️ {dt:.2f}s | {tit[:46]}")
            else:
                dfm.at[idx, "Publicado Hoy en ML"] = sn; dfm.at[idx, "Meta ML (Colchón 50%)"] = sn; dfm.at[idx, "Stock Bodega"] = bn
                iml.setdefault(idn, {})["qty"] = sn
                res.append(f"💛 [MERCADOLIBRE {idn}]{plb:<10} : {sa} uds ➔ {sn} uds | ⏱️ {dt:.2f}s | {tit[:46]}")
    dfw.to_excel(p_aw, index=False); dfm.to_excel(p_am, index=False); json.dump(iml, open(p_ml, "w", encoding="utf-8"))
    if os.path.exists(os.path.expanduser("~/mapas_rapidos_cache.json")): os.remove(os.path.expanduser("~/mapas_rapidos_cache.json"))
    return res
