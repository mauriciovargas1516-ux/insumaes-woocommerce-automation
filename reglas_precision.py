import os
import re, math, openpyxl, pandas as pd

def cargar_catalogo_completo(ruta_cat="/tmp/catalogo_cache.xlsx"):
    items = {}
    if not os.path.exists(ruta_cat):
        cands = [os.path.expanduser(f"~/{f}") for f in os.listdir(os.path.expanduser("~")) if f.endswith(".xlsx") and "AUDITORIA" not in f.upper()]
        if cands: ruta_cat = cands[0]
    try:
        wf = openpyxl.load_workbook(ruta_cat, data_only=False, read_only=True)
        wv = openpyxl.load_workbook(ruta_cat, data_only=True, read_only=True)
        hr = set(wf.sheetnames)
        if "INVENTARIO_WOO" in hr:
            for ri, (rf, rv) in enumerate(zip(wf["INVENTARIO_WOO"].iter_rows(min_row=2, max_col=4, values_only=True),
                                              wv["INVENTARIO_WOO"].iter_rows(min_row=2, max_col=4, values_only=True)), start=2):
                nom = str(rv[1] or "").strip() if rv and len(rv) > 1 else ""
                if not nom or nom == "0": continue
                fb = str(rf[1] or "").strip() if rf and len(rf) > 1 else ""
                hl, cd = "INVENTARIO_WOO", f"'INVENTARIO_WOO'!B{ri}"
                if fb.startswith("=") and "!" in fb:
                    p = fb[1:].split("!", 1)
                    h0, c0 = p[0].strip("'"), re.sub(r"[^A-Z0-9]", "", p[1].upper()) or "A1"
                    if h0 in hr: hl, cd = h0.strip(), f"'{h0}'!{c0}"
                try: stk = float(rv[2] or 0) if rv and len(rv) > 2 and rv[2] is not None else 0.0
                except Exception: continue
                try: prc = float(rv[3] or 0) if rv and len(rv) > 3 and rv[3] is not None else 0.0
                except Exception: prc = 0.0
                items[re.sub(r"\s+", " ", nom.upper()).strip()] = {
                    "nombre": nom, "stock": stk, "precio": prc, "pestana": hl, "celda": cd
                }
        wf.close(); wv.close()
    except Exception:
        pass
    # Respaldo desde AUDITORIA_PRE_SYNC.xlsx si algún item no estaba en cache
    rw = os.path.expanduser("~/AUDITORIA_PRE_SYNC.xlsx")
    if os.path.exists(rw):
        try:
            dfw = pd.read_excel(rw)
            for _, r in dfw.iterrows():
                nom = str(r.get("PRODUCTO LOCAL", "") or "").strip()
                k = re.sub(r"\s+", " ", nom.upper()).strip()
                if nom and nom != "nan" and k not in items:
                    items[k] = {
                        "nombre": nom,
                        "stock": float(r.get("STOCK FÍSICO (Real)", 0) or 0),
                        "precio": float(r.get("PRECIO LOCAL (Nuevo)", 0) or 0),
                        "pestana": str(r.get("Pestaña del Excel", "INVENTARIO_WOO") or "INVENTARIO_WOO"),
                        "celda": "'INVENTARIO_WOO'!B2"
                    }
        except Exception:
            pass
    return items

def buscar_item(items, patron):
    for k, v in items.items():
        if re.search(patron, k, re.I):
            return v
    return None

def corregir_fila_meli(titulo_ml, nombre_ex_actual, items):
    t = str(titulo_ml or "").upper()
    ex = str(nombre_ex_actual or "").strip()
    ex_u = re.sub(r"\s+", " ", ex.upper())

    # 1. QFGD / QFFD con sufijo pegado (90htorno -> -90H)
    m_qf = re.search(r"\b(QF[FG]D\d+[RL]\d+-\d+)H*", t)
    if m_qf:
        cod = m_qf.group(1).upper() + "H"
        cand = buscar_item(items, rf"\b{re.escape(cod)}\b")
        if cand: return cand, "Exacto por Medida/Código", None

    # 2. Portabrocas: Rango exacto (5-25mm, 3-16mm, 5-20mm, 1-16mm, 1-13mm) + Cono B (B24, B22, B18, B16)
    if "PORTABROCA" in t:
        m_rng = re.search(r"\b(\d+-\d+)\s*MM", t)
        m_con = re.search(r"\b(B(?:12|16|18|22|24))\b", t)
        if m_rng and m_con:
            rng, con = m_rng.group(1), m_con.group(1)
            cand = buscar_item(items, rf"PORTA\s*BROCA\s*LL.*{re.escape(rng)}MM\s+{con}\b")
            if cand: return cand, "Exacto por Medida/Código", None

    # 3. Adaptador Plato Cono Morse: Fijo vs Rotativo (ROT) + Cono MT3/MT4/MT5 + Diámetro exacto
    if "ADAPTADOR" in t and "PLATO" in t:
        es_rot = ("ROTATIVO" in t or re.search(r"\bROT\b", t))
        m_mt = re.search(r"\b(?:MT|CONO\s*MORSE\s*)([345])\s*-\s*(\d+)", t)
        if m_mt:
            mt_n, diam = m_mt.group(1), m_mt.group(2)
            pat = rf"^ADAPTADOR\s+ROT\s+PLATO\s+C/M\s+MT{mt_n}-{diam}\b" if es_rot else rf"^ADAPTADOR\s+PLATO\s+C/M\s+MT{mt_n}-{diam}\b"
            cand = buscar_item(items, pat)
            if cand: return cand, "Exacto por Medida/Código", None

    # 4. Fresa Frontal Izar (3mm, 5mm, 10mm, etc.)
    if t.startswith("FRESA FRONTAL") and "IZAR" in t:
        m_mm = re.search(r"FRESA\s+FRONTAL\s+IZAR\s+(\d+(?:[.,]\d+)?)\s*MM", t)
        if m_mm:
            med = m_mm.group(1).replace(".", ",")
            tipo_acero = "HSSE" if ("HSSE" in t or "COBALTO" in t) else "HSS"
            cand = buscar_item(items, rf"^FRESA\s+FRONTAL\s+{re.escape(med)}MM\s+{tipo_acero}\s+IZAR\b")
            if cand: return cand, "Exacto por Medida/Código", None

    # 5. Pies de Metro Dasqua: Análogo estándar vs Ajuste Fino vs Recub Estaño
    if ("PIE DE METRO" in t or "CALIBRE" in t) and "DIGITAL" not in t and "RELOJ" not in t and "INSIZE" not in t and "P=" not in t:
        if "FINO" not in t and "AJUS FIN" not in t and "PERNO" not in t and "ESTAÑO" not in t and "ESTANO" not in t:
            if "300MM" in t or "0-300" in t:
                cand = buscar_item(items, r'^PIE DE METRO 12"X0,05MM 1/128 \(0-300MM\) DASQUA$')
                if cand: return cand, "Exacto por Medida/Código", None
            elif "200MM" in t or "0-200" in t:
                cand = buscar_item(items, r'^PIE DE METRO 8"X0,05MM 1/128 \(0-200MM\) DASQUA$')
                if cand: return cand, "Exacto por Medida/Código", None

    # 6. Juego 3 Machos Izar Métrico (M6x1 -> 6X1MM) vs Pulgada (1/2 UNC) y Terraja NPT 1x11,5
    if "JUEGO" in t and "MACHO" in t and "IZAR" in t:
        m_met = re.search(r"\bM(\d+)\s*X\s*(\d+(?:[.,]\d+)?)\b", t)
        if m_met:
            d_m, p_m = m_met.group(1), m_met.group(2).replace(".", ",")
            cand = buscar_item(items, rf"^JGO\s+3\s+MACHO\s+{d_m}X{re.escape(p_m)}MM\s+HSS\s+CO\s+IZAR\b")
            if cand: return cand, "Exacto por Medida/Código", None

    if "TERRAJA" in t and "NPT" in t and re.search(r"\b1X11[.,]5\b", t) and "1/4" not in t and "1/2" not in t:
        cand = buscar_item(items, r"^TERRAJA\s+1X11,5\s+NPT\s+HSS\s+IZAR\b")
        if cand: return cand, "Exacto por Medida/Código", None

    # 7. Piedras de Esmeril (6x3/4, 6x1, 8x1 + Grano + Color Verde GC vs Blanca 38A)
    if "PIEDRA" in t and "ESMERIL" in t:
        m_g = re.search(r"GRANO\s*(\d+)", t)
        grano = m_g.group(1) if m_g else ""
        med_p = "6X3/4" if "6X3/4" in t else ("6X1" if "6X1" in t else ("8X1" if ("8" in t and grano) else ""))
        if med_p and grano:
            es_blanca = any(w in t for w in ("BLANCA", "OXIDO", "38A"))
            pat = rf"^PIEDRA\s+T1\s+{re.escape(med_p)}\s+38A{grano}\b" if es_blanca else rf"^PIEDRA\s+T1\s+C/S\s+VERDE\s+{re.escape(med_p)}\s+GC{grano}\b"
            cand = buscar_item(items, pat) or buscar_item(items, rf"PIEDRA.*{re.escape(med_p)}.*(?:GC|38A){grano}\b")
            if cand: return cand, "Exacto por Medida/Código", None

    # 8. Cono Reductor MS4-3, Escuadra Universal 4pcs y Alerta de Rosca en Toma FMB
    if "CONO REDUCTOR MS4-3" in t:
        cand = buscar_item(items, r"^REDUCTOR\s+C/M\s+MS4-3$")
        if cand: return cand, "Exacto por Medida/Código", None
    if "ESCUADRA UNIVERSAL 4PCS" in t and "DIGITAL" not in t:
        cand = buscar_item(items, r"^SET\s+ESCUADRA\s+UNIVERSAL\s+DASQUA\s+4PCS")
        if cand: return cand, "Exacto por Medida/Código", None
    if "FMB" in t and ex_u in items:
        m_t = re.search(r"\b(M10|M12|M14|M16|M20)\b", t)
        m_e = re.search(r"\b(M10|M12|M14|M16|M20)\b", ex_u)
        if m_t and m_e and m_t.group(1) != m_e.group(1):
            return items[ex_u], f"⚠️ Tirante ML:{m_t.group(1)} vs Excel:{m_e.group(1)}", None

    return None, None, None
