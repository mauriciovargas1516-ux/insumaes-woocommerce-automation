import lee_config, conectar_meli
import os, sys, io, re, time, math, json, fcntl, zipfile, unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import requests, dropbox

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

RUTA_DBX = "/Compras L-Angel/Catalogo PortasHerramientas e Insertos.xlsx"
RUTA_LOCAL, RUTA_MELI_XLSX, RUTA_WOO_XLSX, RUTA_MEM_JSON, RUTA_MAP_CACHE, RUTA_DELTA_LOG = [os.path.expanduser(f"~/{x}") for x in ("Catalogo PortasHerramientas e Insertos.xlsx", "AUDITORIA_MELI_INSUMAES.xlsx", "AUDITORIA_PRE_SYNC.xlsx", "estado_stocks_delta.json", "mapas_rapidos_cache.json", "delta.log")]
RUTA_REV = "/tmp/catalogo_rev.txt"
dbx = dropbox.Dropbox(app_key=dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY'], app_secret=dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET'], oauth2_refresh_token=dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN'])
SES_WOO, SES_MELI = requests.Session(), requests.Session()

def log_print(msg):
    print(msg, flush=True)
    try: open(RUTA_DELTA_LOG, "a", encoding="utf-8").write(str(msg) + "\n")
    except Exception: pass

def norm_key(s):
    if not s or str(s).upper() == "NAN": return ""
    t = ''.join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', t)).strip()

def obtener_credenciales_woo():
    for fn in ("~/.env", "~/sincronizador_silencioso.py", "~/motor_insumaes.py", "~/descargador_web.py"):
        p = os.path.expanduser(fn)
        if os.path.exists(p):
            txt = open(p, "r", encoding="utf-8", errors="ignore").read()
            ck, cs = re.search(r'(ck_[a-fA-F0-9]{30,45})', txt), re.search(r'(cs_[a-fA-F0-9]{30,45})', txt)
            if ck and cs: return ck.group(1), cs.group(1)
    return None, None

def guardar_mapas_ram(mm, mw):
    try:
        mt_m = os.path.getmtime(RUTA_MELI_XLSX) if os.path.exists(RUTA_MELI_XLSX) else 0
        mt_w = os.path.getmtime(RUTA_WOO_XLSX) if os.path.exists(RUTA_WOO_XLSX) else 0
        json.dump({"v": 8, "mt_m": mt_m, "mt_w": mt_w, "meli": mm, "woo": mw}, open(f"{RUTA_MAP_CACHE}.tmp", "w", encoding="utf-8"))
        os.replace(f"{RUTA_MAP_CACHE}.tmp", RUTA_MAP_CACHE)
    except Exception: pass

def cargar_mapas_ram():
    mt_m = os.path.getmtime(RUTA_MELI_XLSX) if os.path.exists(RUTA_MELI_XLSX) else 0
    mt_w = os.path.getmtime(RUTA_WOO_XLSX) if os.path.exists(RUTA_WOO_XLSX) else 0
    if os.path.exists(RUTA_MAP_CACHE):
        try:
            c = json.load(open(RUTA_MAP_CACHE, "r", encoding="utf-8"))
            if c.get("v") == 8 and c.get("mt_m") == mt_m and c.get("mt_w") == mt_w and c.get("meli") and c.get("woo"):
                return c["meli"], c["woo"]
        except Exception: pass
    import pandas as pd
    mapa_m, mapa_w = {}, {}
    if os.path.exists(RUTA_MELI_XLSX):
        try:
            df = pd.read_excel(RUTA_MELI_XLSX)
            c_mlc = next((c for c in df.columns if "MLC" in c.upper() or "CÓDIGO ML" in c.upper() or "CODIGO ML" in c.upper()), None)
            c_nex = next((c for c in df.columns if "EXCEL" in c.upper() and ("NOMBRE" in c.upper() or "CELDA" in c.upper())), None)
            c_tit = next((c for c in df.columns if "MERCADO LIBRE" in c.upper() or "TITULO" in c.upper()), None)
            c_upk = next((c for c in df.columns if "PACK" in c.upper() and ("UNID" in c.upper() or "POR" in c.upper())), None)
            c_pub = next((c for c in df.columns if "PUBLICADO HOY" in c.upper()), None)
            for r in df.to_dict("records"):
                nex, mlc = norm_key(r.get(c_nex, "")), str(r.get(c_mlc, "")).strip()
                if nex and nex != "SIN MATCH" and mlc.startswith("MLC"):
                    upk = int(float(r.get(c_upk, 1) or 1)) if c_upk and pd.notna(r.get(c_upk)) else 1
                    pub = int(float(r.get(c_pub, -1) if pd.notna(r.get(c_pub)) else -1)) if c_pub else -1
                    mapa_m.setdefault(nex, []).append({"mlc": mlc, "titulo": str(r.get(c_tit, mlc)), "pack": max(1, upk), "pub_ml": pub})
        except Exception: pass
    if os.path.exists(RUTA_WOO_XLSX):
        try:
            df = pd.read_excel(RUTA_WOO_XLSX)
            c_id = next((c for c in df.columns if c.upper() in ("ID", "ID WEB", "ID_WEB", "ID_WOO", "WOO_ID") or "ID " in c.upper()), None)
            cols_nom = [c for c in df.columns if c.upper() in ("PRODUCTO LOCAL", "PRODUCTO WEB", "NOMBRE", "NOMBRE_EN_EXCEL")]
            c_sw = next((c for c in df.columns if "STOCK WEB" in c.upper() or "STOCK_WEB" in c.upper()), None)
            c_pw = next((c for c in df.columns if "PRECIO WEB" in c.upper() or "PRECIO_WEB" in c.upper()), None)
            for r in df.to_dict("records"):
                w = str(r.get(c_id, "")).strip() if c_id and pd.notna(r.get(c_id, None)) else ""
                if w and w.lower() != "nan":
                    try:
                        ep, wl = (f"products/{int(float(w.split('-')[0]))}/variations/{int(float(w.split('-')[1]))}", f"{int(float(w.split('-')[0]))}-{int(float(w.split('-')[1]))}") if "-" in w else (f"products/{int(float(w))}", str(int(float(w))))
                        sw = int(float(r.get(c_sw, -1) if pd.notna(r.get(c_sw)) else -1)) if c_sw else -1
                        pw = int(float(r.get(c_pw, 0) if pd.notna(r.get(c_pw)) else 0)) if c_pw else 0
                        nw = str(r.get("PRODUCTO WEB", "")).upper()
                        mp = re.search(r'(?:\(|PACK\s+)(\d+)\s*(?:UNIDADES|UN)\)?', nw)
                        mw = max(1, int(mp.group(1))) if (mp and "JUEGO" not in nw and "JGO" not in nw) else 1
                        for cn in cols_nom:
                            k = norm_key(r.get(cn, ""))
                            if k and k not in ("SIN MATCH", "---"):
                                mapa_w.setdefault(k, []).append({"endpoint": ep, "id_woo": wl, "nombre": str(r.get("PRODUCTO WEB", r.get(cn, ""))), "stock_web": sw, "precio_web": pw, "pack": mw})
                    except Exception: pass
        except Exception: pass
    guardar_mapas_ram(mapa_m, mapa_w)
    return mapa_m, mapa_w

def leer_catalogo_ultrarapido(b):
    datos = {}
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        ss = ["".join(si.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))] if "xl/sharedStrings.xml" in z.namelist() else []
        ns_v = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v"
        for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            nv, cv, pv = None, 0, 0
            for c in row:
                cl = c.attrib.get("r", " ")[0]
                if cl not in ("B", "C", "D"): continue
                v = c.find(ns_v)
                if v is None or v.text is None: continue
                val = ss[int(v.text)] if c.attrib.get("t") == "s" else v.text
                if cl == "B": nv = val
                elif cl == "C":
                    try: cv = int(float(val))
                    except Exception: cv = 0
                elif cl == "D":
                    try: pv = int(round(float(val)))
                    except Exception: pv = 0
            if nv:
                nom = norm_key(nv)
                if nom and len(nom) >= 4 and not nom.replace(".","").isdigit() and nom not in ("0","NAN","NOMBRE","MONTO USD","MONTO CLP","MONTO TOTAL","ITEM CODE","#REF!"):
                    if nom not in datos or cv > datos[nom]["s"] or (cv == datos[nom]["s"] and pv > datos[nom]["p"]):
                        datos[nom] = {"s": cv, "p": pv}
    return datos

def cargar_mem_disco():
    if os.path.exists(RUTA_MEM_JSON):
        try:
            d = json.load(open(RUTA_MEM_JSON, "r", encoding="utf-8"))
            if isinstance(d, dict):
                return {k: (v if isinstance(v, dict) and "s" in v else {"s": int(v), "p": 0}) for k, v in d.items() if isinstance(v, (dict, int, float))}
        except Exception: pass
    return {}

def guardar_mem_disco(m):
    try:
        json.dump(m, open(f"{RUTA_MEM_JSON}.tmp", "w", encoding="utf-8"))
        os.replace(f"{RUTA_MEM_JSON}.tmp", RUTA_MEM_JSON)
    except Exception: pass

def disparar_woo_item(nom, st_nue, pr_nue, col_pct, lim_cf, woo_st_on, woo_pr_on, w, ck, cs):
    wid, ep, pk = w["id_woo"], w["endpoint"], w.get("pack", 1)
    mw, pw_meta = (math.ceil((st_nue // pk) * col_pct) if (st_nue // pk) > 0 else 0), int(pr_nue * pk)
    sw_ant, pw_ant = int(w.get("stock_web", -1)), int(w.get("precio_web", 0))
    payload, cambia_st, cambia_pr = {}, bool(woo_st_on), False
    if woo_pr_on and pw_meta > 0 and pw_ant != pw_meta:
        var_p = abs(pw_ant - pw_meta) / float(pw_meta) if pw_ant > 0 else 0.0
        if var_p >= lim_cf and pw_ant > 0:
            pct_v, pct_l = int(round(var_p * 100)), int(round(lim_cf * 100))
            if True:
                w["ultimo_bloq"] = pw_meta
                log_print(f"      🛡️ [CORTAFUEGOS {pct_l}%] {nom} (ID:{wid}): ${pw_ant} ➔ ${pw_meta} bloqueado (Var {pct_v}% > {pct_l}%)")
                lee_config.registrar_evento("WOO-CORTAFUEGOS", f"ID:{wid}", nom, f"Precio ${pw_ant} -> ${pw_meta} BLOQUEADO (Var {pct_v}% > {pct_l}%) [0.01s]")
        else: cambia_pr, payload["regular_price"] = True, str(pw_meta)
    if cambia_st: payload.update({"stock_quantity": mw, "manage_stock": True, "stock_status": "instock" if mw > 0 else "outofstock"})
    if not payload: return
    t_req = time.time()
    try:
        rw = SES_WOO.put(f"https://insumaes.cl/wp-json/wc/v3/{ep}", auth=(ck, cs), json=payload, timeout=10)
        dt = time.time() - t_req
        if rw.status_code in (200, 201):
            if cambia_st:
                w["stock_web"] = mw
                log_print(f"      ✅ [WOO STOCK {dt:.2f}s] {nom} (ID:{wid}): {sw_ant} ➔ {mw} uds (Bodega: {st_nue})")
                lee_config.registrar_evento("WOO-ACTIVADO" if (sw_ant==0 and mw>0) else ("WOO-AGOTADO" if mw==0 else "WOO-TURBO"), f"ID:{wid}", nom, f"{sw_ant} uds -> {mw} uds [{dt:.2f}s]") if sw_ant != mw else None
            if cambia_pr:
                w["precio_web"], w["ultimo_bloq"] = pw_meta, 0
                log_print(f"      💰 [WOO PRECIO {dt:.2f}s] {nom} (ID:{wid}): ${pw_ant} ➔ ${pw_meta}")
                lee_config.registrar_evento("WOO-PRECIO", f"ID:{wid}", nom, f"Precio ${pw_ant} -> ${pw_meta} [{dt:.2f}s]")
    except Exception as ew: log_print(f"      ⚠️ Error Woo {wid}: {ew}")

def disparar_meli_item(nom, st_nue, col_pct, m, hdr):
    mlc, pk = m["mlc"], m["pack"]
    pks = st_nue // pk
    mm = 0 if pks <= 0 else (1 if pks == 1 else int(math.floor(pks * col_pct + 0.5)))
    qr, t_req = int(m.get("pub_ml", -1)), time.time()
    try:
        if mm <= 0:
            rm = SES_MELI.put(f"https://api.mercadolibre.com/items/{mlc}", headers=hdr, json={"status": "paused"}, timeout=10)
            dt = time.time() - t_req
            if rm.status_code == 200:
                m["pub_ml"] = 0
                log_print(f"      ⏸️ [MELI PAUSA {dt:.2f}s] {mlc} ({nom}) PAUSADO (0 uds)")
                lee_config.registrar_evento("MELI-PAUSA", mlc, m["titulo"], f"active ({qr} uds) -> paused (0 uds) [{dt:.2f}s]")
        else:
            rm = SES_MELI.put(f"https://api.mercadolibre.com/items/{mlc}", headers=hdr, json={"status": "active", "available_quantity": mm}, timeout=10)
            dt = time.time() - t_req
            if rm.status_code == 200:
                m["pub_ml"] = mm
                log_print(f"      ✅ [MELI STOCK {dt:.2f}s] {mlc} ({nom}): {qr} ➔ {mm} uds (Bodega: {st_nue})")
                lee_config.registrar_evento("MELI-ACTIVADO" if (qr==0 and mm>0) else "MELI-STOCK", mlc, m["titulo"], f"{qr} uds -> {mm} uds [{dt:.2f}s]") if qr != mm else None
    except Exception as eml: log_print(f"      ⚠️ Error ML {mlc}: {eml}")

def ejecutar_pasada(ultima_rev, mem_cat, estado_ant, ck, cs, forzar=False):
    if str(lee_config.obtener_valor("MODO_TURBO_DELTA", "SI")).upper() != "SI" and not forzar:
        return ultima_rev, mem_cat, estado_ant
    woo_st_on = str(lee_config.obtener_valor("SINCRONIZAR_WOO_STOCK", "SI")).upper() == "SI"
    woo_pr_on = str(lee_config.obtener_valor("SINCRONIZAR_WOO_PRECIOS", "SI")).upper() == "SI"
    meli_on = str(lee_config.obtener_valor("SINCRONIZAR_MELI_STOCK", "NO")).upper() == "SI"
    col_pct = float(lee_config.obtener_valor("PORCENTAJE_COLCHON", 50) or 50) / 100.0
    _cf_raw = float(lee_config.obtener_valor("LIMITE_CORTAFUEGOS", 40) or 0)
    lim_cf = (_cf_raw / 100.0) if _cf_raw > 0 else 999.0
    estado_actual = (woo_st_on, woo_pr_on, meli_on, col_pct, lim_cf)
    cambio_panel, recien_meli = (estado_actual != estado_ant) or forzar, (meli_on and not estado_ant[2]) or forzar

    meta = dbx.files_get_metadata(RUTA_DBX)
    if (meta.rev != ultima_rev) or cambio_panel:
        t0, ultima_rev = time.time(), meta.rev
        rev_disco = open(RUTA_REV).read().strip() if os.path.exists(RUTA_REV) else ""
        if not os.path.exists(RUTA_LOCAL) or meta.rev != rev_disco:
            _, res = dbx.files_download(RUTA_DBX)
            raw = res.content
            open(RUTA_LOCAL, "wb").write(raw); open("/tmp/catalogo_cache.xlsx", "wb").write(raw); open(RUTA_REV, "w").write(meta.rev)
        else: raw = open(RUTA_LOCAL, "rb").read()

        nuevos = leer_catalogo_ultrarapido(raw)
        mapa_meli, mapa_woo = cargar_mapas_ram()
        if not mem_cat: mem_cat = cargar_mem_disco()
        tk_meli = conectar_meli.obtener_token_valido() if meli_on else None
        hdr_meli = {"Authorization": f"Bearer {tk_meli}"} if tk_meli else {}

        r_ult = os.path.expanduser("~/ultimos_editados.json")
        ult_ed = json.load(open(r_ult)) if os.path.exists(r_ult) else ["BALDE ACEITE SOLUBLE 19L", "ACEITE SOLUBLE 2L"]
        cambiados = []
        for n, d_nue in nuevos.items():
            s_nue, p_nue = d_nue["s"], d_nue["p"]
            d_ant = mem_cat.get(n, {"s": s_nue, "p": p_nue})
            cambio_ex = (n in mem_cat) and (s_nue != d_ant["s"] or (p_nue != d_ant["p"] and d_ant["p"] > 0))
            if cambio_ex and n not in ult_ed:
                ult_ed = ([n] + ult_ed)[:15]
            reintento_panel = cambio_panel and (n in ult_ed)
            if cambio_ex or reintento_panel:
                cambiados.append((n, s_nue, p_nue, True))
        try: json.dump(ult_ed, open(r_ult, "w"))
        except Exception: pass

        mem_cat = nuevos; guardar_mem_disco(mem_cat)
        if cambiados:
            log_print(f"\n⚡ [{time.strftime('%H:%M:%S')} Chile] ¡DISPARO PARALELO V8 ({len(cambiados)} ítems)! (XML en {time.time()-t0:.2f}s)")
            tareas = []
            with ThreadPoolExecutor(max_workers=12) as ex:
                for nom, st_nue, pr_nue, act_w in cambiados[:120]:
                    if (woo_st_on or woo_pr_on) and ck and cs and nom in mapa_woo and act_w:
                        vistos = set()
                        for w in mapa_woo[nom]:
                            if w["id_woo"] in vistos: continue
                            vistos.add(w["id_woo"])
                            tareas.append(ex.submit(disparar_woo_item, nom, st_nue, pr_nue, col_pct, lim_cf, woo_st_on, woo_pr_on, w, ck, cs))
                    if meli_on and tk_meli and nom in mapa_meli:
                        for m in mapa_meli[nom]:
                            pks = st_nue // m["pack"]
                            mm = 0 if pks <= 0 else (1 if pks == 1 else int(math.floor(pks * col_pct + 0.5)))
                            if True:
                                tareas.append(ex.submit(disparar_meli_item, nom, st_nue, col_pct, m, hdr_meli))
                for t in tareas:
                    try: t.result()
                    except Exception: pass
            guardar_mapas_ram(mapa_meli, mapa_woo)
            log_print(f"🚀 ¡Sincronización Paralela V8 completada en {time.time()-t0:.2f}s totales!")
    return ultima_rev, mem_cat, estado_actual

def vigilar_dropbox():
    ultima_rev, mem_cat = None, cargar_mem_disco()
    cargar_mapas_ram()
    ck, cs = obtener_credenciales_woo()
    est_ini = (
        str(lee_config.obtener_valor("SINCRONIZAR_WOO_STOCK", "SI")).upper() == "SI",
        str(lee_config.obtener_valor("SINCRONIZAR_WOO_PRECIOS", "SI")).upper() == "SI",
        str(lee_config.obtener_valor("SINCRONIZAR_MELI_STOCK", "NO")).upper() == "SI",
        float(lee_config.obtener_valor("PORCENTAJE_COLCHON", 50) or 50) / 100.0,
        (float(lee_config.obtener_valor("LIMITE_CORTAFUEGOS", 40) or 0) / 100.0 if float(lee_config.obtener_valor("LIMITE_CORTAFUEGOS", 40) or 0) > 0 else 999.0),
    )
    if "--una-vez" in sys.argv:
        ejecutar_pasada(ultima_rev, mem_cat, est_ini, ck, cs, forzar=True); return
    fp_lock = open("/tmp/delta_insumaes.lock", "w")
    try: fcntl.flock(fp_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError: return
    log_print(f"🚀 [{time.strftime('%H:%M:%S')} Chile] MOTOR FRANCOTIRADOR V8 ACTIVO (Stock + Precios Woo + Cronómetro)...")
    while True:
        try: ultima_rev, mem_cat, est_ini = ejecutar_pasada(ultima_rev, mem_cat, est_ini, ck, cs, forzar=False)
        except Exception as e: log_print(f"⚠️ Vigilante: {e}")
        time.sleep(3)

if __name__ == "__main__": vigilar_dropbox()
