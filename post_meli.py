import os, re, requests, openpyxl, pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.utils import get_column_letter
import conectar_meli, lee_config

RW = r"C:\Users\lilo6\Dropbox\Compras L-Angel\Catalogo PortasHerramientas e Insertos.xlsx"

try:
    import dropbox as _dbx
    if not getattr(_dbx.Dropbox.files_upload, "_hk", False):
        _oup = _dbx.Dropbox.files_upload
        def _cup(self, fb, path, *a, **kw):
            r = _oup(self, fb, path, *a, **kw)
            if "MELI" in str(path).upper():
                rw = os.path.expanduser("~/AUDITORIA_PRE_SYNC.xlsx")
                if os.path.exists(rw):
                    try:
                        dw = re.sub(r"AUDITORIA_MELI[^/]*\.xlsx", "AUDITORIA_PRE_SYNC.xlsx", str(path), flags=re.I)
                        _oup(self, open(rw, "rb").read(), dw if dw != str(path) else "/AUDITORIA_PRE_SYNC.xlsx", *a, **kw)
                        print("☁️ Auditoría WordPress también subida a Dropbox.")
                    except Exception: pass
            return r
        _cup._hk = True; _dbx.Dropbox.files_upload = _cup
except Exception: pass

def leer_cat():
    omap, tp = {}, {}
    cands = ["/tmp/catalogo_cache.xlsx"] + [os.path.expanduser(f"~/{f}") for f in os.listdir(os.path.expanduser("~")) if f.endswith(".xlsx") and "AUDITORIA" not in f.upper()]
    rc = next((p for p in cands if os.path.exists(p)), None)
    if rc:
        try:
            wf = openpyxl.load_workbook(rc, data_only=False, read_only=True)
            wv = openpyxl.load_workbook(rc, data_only=True, read_only=True)
            hr = set(wf.sheetnames)
            if "INVENTARIO_WOO" in hr:
                vis = set()
                for ri, (rf, rv) in enumerate(zip(wf["INVENTARIO_WOO"].iter_rows(min_row=2, max_col=4, values_only=True), wv["INVENTARIO_WOO"].iter_rows(min_row=2, max_col=4, values_only=True)), start=2):
                    vb, fb = str(rv[1] or "").strip() if rv and len(rv)>1 else "", str(rf[1] or "").strip() if rf and len(rf)>1 else ""
                    if not vb or vb == "0" or any(b in vb.upper() for b in ("MONTO USD", "MONTO CLP", "MONTO TOTAL", "SUBTOTAL")): continue
                    hl, cd = "INVENTARIO_WOO", f"'INVENTARIO_WOO'!B{ri}"
                    if fb.startswith("=") and "!" in fb:
                        p = fb[1:].split("!", 1); h0 = p[0].strip("'"); c0 = re.sub(r"[^A-Z0-9]", "", p[1].upper()) or "A1"
                        if h0 in hr: hl, cd = h0.strip(), f"'{h0}'!{c0}"
                    omap[vb] = (hl, cd)
                    if vb.upper() not in vis: vis.add(vb.upper()); tp[hl] = tp.get(hl, 0) + 1
            wf.close(); wv.close()
        except Exception: pass
    return omap, tp

def fmt_ws(ws, wmap=None):
    hf, hfn = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid"), Font(color="FFFFFF", bold=True)
    for c in range(1, ws.max_column + 1):
        cel = ws.cell(row=1, column=c)
        if cel.value is not None: cel.fill = hf; cel.font = hfn
        ws.column_dimensions[get_column_letter(c)].width = max(len(str(cel.value or "")) + 5, (wmap or {}).get(str(cel.value), 16))
    ws.freeze_panes = "A2"

def procesar():
    rx = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    if not os.path.exists(rx): return
    try:
        df = pd.read_excel(rx)
    except Exception:
        return
    def gc(*ks): return next((c for c in df.columns if any(k in str(c).upper() for k in ks)), None)
    c_est, c_mlc, c_tit, c_nex, c_mat = gc("ESTADO"), gc("CODIGO_MLC", "CÓDIGO ML"), gc("TITULO", "MERCADO LIBRE"), gc("NOMBRE_EN_EXCEL", "TU EXCEL"), gc("MATCH", "CONECTÓ")
    c_sbod, c_upk, c_pks, c_col, c_pb, c_pm = gc("FISICO", "STOCK BODEGA"), gc("UNIDADES", "UNID."), gc("PACKS"), gc("STOCK_A_", "COLCHÓN"), gc("PRECIO_BASE", "PRECIO EXCEL"), gc("PRECIO_MELI", "PRECIO ML")
    tk, sinc, pil = conectar_meli.obtener_token_valido(), str(lee_config.obtener_valor("SINCRONIZAR_MELI_STOCK", "NO")).upper(), str(lee_config.obtener_valor("MLC_PILOTO_PRUEBA", "NINGUNO")).upper()
    amap, (omap, tp_ex) = {}, leer_cat()
    if tk and c_mlc:
        s = requests.Session(); s.headers.update({"Authorization": f"Bearer {tk}"})
        ids = [str(x).strip() for x in df[c_mlc].dropna().unique() if str(x).strip().startswith("MLC")]
        for i in range(0, len(ids), 20):
            try:
                for it in s.get(f"https://api.mercadolibre.com/items?ids={','.join(ids[i:i+20])}", timeout=15).json():
                    b = it.get("body", {})
                    if b.get("id"): amap[b["id"]] = (b.get("status", ""), b.get("available_quantity", 0), b.get("permalink", ""))
            except Exception: pass
    import reglas_precision, math
    cat_items = reglas_precision.cargar_catalogo_completo()
    corregidos_prec = 0
    for idx_p, row_p in df.iterrows():
        cand_p, tmat_p, _ = (None, None, None) if "SKU" in str(row_p.get(c_mat, "")).upper() else reglas_precision.corregir_fila_meli(row_p.get(c_tit, ""), row_p.get(c_nex, ""), cat_items)
        if cand_p:
            df.at[idx_p, c_nex] = cand_p["nombre"]
            if c_mat and tmat_p: df.at[idx_p, c_mat] = tmat_p
            if c_sbod: df.at[idx_p, c_sbod] = int(cand_p["stock"])
            if c_pb and cand_p["precio"] > 0: df.at[idx_p, c_pb] = int(round(cand_p["precio"]))
            upk_v = int(float(row_p.get(c_upk, 1) or 1)) if c_upk and pd.notna(row_p.get(c_upk)) else 1
            pks_v = int(cand_p["stock"] // max(upk_v, 1))
            _cp = float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0; col_v = 0 if pks_v <= 0 else (1 if pks_v == 1 else int(math.floor(pks_v * _cp + 0.5)))
            if c_pks: df.at[idx_p, c_pks] = pks_v
            if c_col: df.at[idx_p, c_col] = col_v
            df.at[idx_p, c_est] = "✅ Activo" if col_v > 0 else "🚨 Pausar (Sin Stock)"
            omap[cand_p["nombre"]] = (cand_p["pestana"], cand_p["celda"])
            corregidos_prec += 1
    print(f"🔬 Motor de Precisión Quirúrgica: {corregidos_prec} emparejamientos corregidos/verificados.")

    n = len(df)
    pcol, ccol, sml, ecol, mcol = pd.Series([""]*n, dtype="object"), pd.Series([""]*n, dtype="object"), pd.Series([None]*n, dtype="object"), df[c_est].astype("object").copy(), df[c_mat].astype("object").copy()
    cambios = 0
    for idx, row in df.iterrows():
        mlc, nex = str(row.get(c_mlc, "")).strip(), str(row.get(c_nex, "")).strip()
        if nex in omap: pcol.at[idx], ccol.at[idx] = omap[nex][0], omap[nex][1]
        elif nex and nex != "SIN MATCH": pcol.at[idx], ccol.at[idx] = "INVENTARIO_WOO", "'INVENTARIO_WOO'!B2"
        else: pcol.at[idx], ccol.at[idx] = "Sin Conexión", ""
        if mlc in amap:
            st, qr, _ = amap[mlc]; sml.at[idx] = 0 if st == "paused" else int(qr or 0)
            est, perm = str(ecol.at[idx]).upper(), (sinc == "SI") or (pil == mlc)
            if "PAUSAR" in est or "SIN STOCK" in est:
                if st == "paused": ecol.at[idx] = "⏸️ Ya Pausado en ML"
                elif st == "active" and perm and cambios < 25 and s.put(f"https://api.mercadolibre.com/items/{mlc}", json={"status": "paused"}, timeout=10).status_code == 200:
                    ecol.at[idx] = "⏸️ Ya Pausado en ML"; sml.at[idx] = 0; cambios += 1; lee_config.registrar_evento("MELI-PAUSA", mlc, row.get(c_tit, ""), f"active ({qr} uds) -> paused (0 uds)")
            elif "ACTIVO" in est and c_col and pd.notna(row.get(c_col)):
                mq = int(float(row[c_col])) if str(row[c_col]).strip() else 0
                if mq > 0:
                    if st == "paused": ecol.at[idx] = "🔵 Pausado (Con Stock)"
                    elif st == "active" and int(qr) != mq and perm and cambios < 500 and s.put(f"https://api.mercadolibre.com/items/{mlc}", json={"available_quantity": mq}, timeout=10).status_code == 200:
                        ecol.at[idx] = "✅ Stock Actualizado"; sml.at[idx] = mq; cambios += 1; lee_config.registrar_evento("MELI-STOCK", mlc, row.get(c_tit, ""), f"{qr} uds -> {mq} uds")
        es, ms = str(ecol.at[idx]).upper(), str(mcol.at[idx]).upper()
        ecol.at[idx] = "⏸️ Ya Pausado en ML" if "PAUSAD" in es and "CON STOCK" not in es else ("🚨 Pausar (Sin Stock)" if "PAUSAR" in es or "SIN STOCK" in es else ("❓ Sin Pareja en Excel" if "SIN" in es else ("🔵 Pausado (Con Stock)" if "CON STOCK" in es else "✅ Activo")))
        mcol.at[idx] = "Exacto por SKU" if "SKU" in ms else ("Exacto por Medida/Código" if "MEDIDA" in ms or "CODIGO" in ms or "CÓDIGO" in ms else (str(mcol.at[idx]) if "⚠️" in ms else ("Por Nombre Similar" if "IA" in ms or "NOMBRE" in ms else "Sin Conexión")))

    dfo = pd.DataFrame({
        "Estado": ecol, "Código ML (Ver Web)": df[c_mlc], "Nombre en Mercado Libre": df[c_tit], "Nombre en tu Excel (Ir a Celda)": df[c_nex],
        "Pestaña del Excel": pcol, "Cómo se Conectó": mcol, "Stock Bodega": df[c_sbod] if c_sbod else 0, "Unid. x Pack": df[c_upk] if c_upk else 1,
        "Packs en Bodega": df[c_pks] if c_pks else 0, "Publicado Hoy en ML": sml, "Meta ML (Colchón 50%)": df[c_col] if c_col else 0,
        "Precio Excel": df[c_pb] if c_pb else 0, "Precio ML": df[c_pm] if c_pm else 0
    })
    celdas_orig = ccol.tolist()
    ml_p = dfo[dfo["Pestaña del Excel"] != "Sin Conexión"].groupby("Pestaña del Excel")["Nombre en tu Excel (Ir a Celda)"].nunique().to_dict()
    fcob, tex_s, tml_s = [], 0, 0
    for pn in sorted(set(list(tp_ex.keys()) + list(ml_p.keys())), key=lambda k: tp_ex.get(k, 0), reverse=True):
        tx, em = max(tp_ex.get(pn, 0), ml_p.get(pn, 0)), ml_p.get(pn, 0)
        if tx == 0: continue
        fcob.append({"1. PESTAÑA DEL EXCEL": pn, "Total en tu Excel": int(tx), "Publicados en ML": int(em), "Faltan por Subir a ML": int(tx - em), "% de tu Excel en ML": f"{round((em/tx)*100,1)}%"})
        tex_s += tx; tml_s += em
    pg = round((tml_s / max(tex_s, 1)) * 100, 1)
    fcob.append({"1. PESTAÑA DEL EXCEL": "TOTAL CATÁLOGO EXCEL", "Total en tu Excel": int(tex_s), "Publicados en ML": int(tml_s), "Faltan por Subir a ML": int(tex_s - tml_s), "% de tu Excel en ML": f"{pg}%"})
    vc_e = dfo["Estado"].value_counts(); tml_i = max(len(dfo), 1)
    dfe = pd.DataFrame([{"2. ESTADO EN MERCADO LIBRE": k, "Publicaciones": int(v), "% de tu Tienda ML": f"{round((v/tml_i)*100,1)}%"} for k, v in vc_e.items()] + [{"2. ESTADO EN MERCADO LIBRE": "TOTAL PUBLICACIONES ML", "Publicaciones": int(vc_e.sum()), "% de tu Tienda ML": "100.0%"}])
    with pd.ExcelWriter(rx, engine="openpyxl") as w:
        dfo.to_excel(w, sheet_name="AUDITORIA_MELI", index=False)
        pd.DataFrame(fcob).to_excel(w, sheet_name="RESUMEN_ESTADISTICO", startrow=1, startcol=0, index=False)
        dfe.to_excel(w, sheet_name="RESUMEN_ESTADISTICO", startrow=1, startcol=6, index=False)
    wb = openpyxl.load_workbook(rx); ws = wb["AUDITORIA_MELI"]
    fmt_ws(ws, {"Nombre en Mercado Libre": 38, "Nombre en tu Excel (Ir a Celda)": 36, "Pestaña del Excel": 22, "Estado": 22, "Cómo se Conectó": 24})
    for c in range(1, wb["RESUMEN_ESTADISTICO"].max_column + 1): wb["RESUMEN_ESTADISTICO"].column_dimensions[get_column_letter(c)].width = 24
    fa, fv, lw, ll = Font(color="0563C1", underline="single"), Font(color="107C41", underline="single", bold=True), 0, 0
    for ri in range(2, ws.max_row + 1):
        cm = ws.cell(row=ri, column=2); vm = str(cm.value or "").strip()
        if vm.startswith("MLC"): cm.hyperlink = amap.get(vm, ("", 0, ""))[2] or f"https://articulo.mercadolibre.cl/MLC-{vm.replace('MLC','')}"; cm.font = fa; lw += 1
        cn = ws.cell(row=ri, column=4); vn = str(cn.value or "").strip(); rcel = celdas_orig[ri - 2] if (ri - 2) < len(celdas_orig) else ""
        if vn and vn != "SIN MATCH" and rcel: cn.hyperlink = Hyperlink(ref=cn.coordinate, target=RW, location=rcel); cn.font = fv; ll += 1
    wb.save(rx)
    n_pausar = int((dfo["Estado"] == "🚨 Pausar (Sin Stock)").sum())
    n_yapaus = int((dfo["Estado"] == "⏸️ Ya Pausado en ML").sum())
    print(f"📌 Estado Real API ML -> 🚨 Activas por Pausar: {n_pausar} | ⏸️ Ya Pausadas en ML: {n_yapaus} | ⚡ Cambios hoy: {cambios}")
    print(f"📊 Cobertura del Excel en ML: {tml_s} de {tex_s} productos de tu Excel están en ML ({pg}%).")
    print(f"✅ Meli Ordenado | 🔗 Links ML: {lw} | 📂 Links Excel Local reparados: {ll}")
    procesar_woo(omap)

def procesar_woo(omap=None):
    cands = [os.path.expanduser("~/AUDITORIA_PRE_SYNC.xlsx")] + [os.path.expanduser(f"~/{f}") for f in os.listdir(os.path.expanduser("~")) if "AUDITORIA" in f.upper() and "MELI" not in f.upper() and f.endswith(".xlsx")]
    rx = next((p for p in cands if p and os.path.exists(p)), None)
    if not rx: return
    try:
        df = pd.read_excel(rx)
    except Exception:
        return
    if df.empty: return
    if omap is None: omap, _ = leer_cat()
    n = len(df); c_nom = next((c for c in df.columns if any(k in str(c).upper() for k in ("NOMBRE", "PRODUCTO", "TITULO"))), df.columns[1] if len(df.columns)>1 else df.columns[0])
    pcol, ccol = pd.Series([""]*n, dtype="object"), pd.Series([""]*n, dtype="object")
    for idx, row in df.iterrows():
        nex = str(row.get(c_nom, "")).strip()
        if nex in omap: pcol.at[idx], ccol.at[idx] = omap[nex][0], omap[nex][1]
        elif nex: pcol.at[idx], ccol.at[idx] = "INVENTARIO_WOO", "'INVENTARIO_WOO'!B2"
    df["Pestaña del Excel"] = pcol; celdas_orig = ccol.tolist(); tw = max(len(df), 1); vc_p = df["Pestaña del Excel"].value_counts()
    dfp = pd.DataFrame([{"PESTAÑA DEL EXCEL": k, "Productos en Web": int(v), "% de tu Web": f"{round((v/tw)*100,1)}%"} for k, v in vc_p.items()] + [{"PESTAÑA DEL EXCEL": "TOTAL WEB WOOCOMMERCE", "Productos en Web": int(vc_p.sum()), "% de tu Web": "100.0%"}])
    rx_tmp = f"{rx}.tmp.{os.getpid()}.xlsx"
    with pd.ExcelWriter(rx_tmp, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="AUDITORIA_WOO", index=False)
        dfp.to_excel(w, sheet_name="RESUMEN_ESTADISTICO", startrow=1, startcol=0, index=False)
    wb = openpyxl.load_workbook(rx_tmp); ws = wb["AUDITORIA_WOO"]; fmt_ws(ws); fv = Font(color="107C41", underline="single", bold=True)
    cnom_i = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}.get(c_nom); ll = 0
    for ri in range(2, ws.max_row + 1):
        if cnom_i:
            cn = ws.cell(row=ri, column=cnom_i); vn = str(cn.value or "").strip(); rcel = celdas_orig[ri - 2] if (ri - 2) < len(celdas_orig) else ""
            if vn and rcel: cn.hyperlink = Hyperlink(ref=cn.coordinate, target=RW, location=rcel); cn.font = fv; ll += 1
    wb.save(rx_tmp); wb.close(); os.replace(rx_tmp, rx)
    print(f"✅ Auditoría WordPress ({os.path.basename(rx)}) actualizada con {ll} links a tu Excel local.")

if __name__ == "__main__": procesar()
