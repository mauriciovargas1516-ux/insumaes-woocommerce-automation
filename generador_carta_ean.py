import os, re, io, json, requests, pandas as pd
import conectar_meli

P_EAN = os.path.expanduser("~/diccionario_ean_insumaes.json")

CODE128 = [
    "212222","222122","222221","121223","121322","131222","122213","122312","132212","221213",
    "221312","231212","112232","122132","122231","113222","123122","123221","223211","221132",
    "221231","213212","223112","312131","311222","321122","321221","312212","322112","322211",
    "212123","212321","232121","111323","131123","131321","112313","132113","132311","211313",
    "231113","231311","112133","112331","132131","113123","113321","133121","313121","211331",
    "231131","213113","213311","213131","311123","311321","331121","312113","312311","332111",
    "314111","221411","431111","111224","111422","121124","121421","141122","141221","112214",
    "112412","122114","122411","142112","142211","241211","221114","413111","241112","134111",
    "111242","121142","121241","114212","124112","124211","411212","421112","421211","212141",
    "214121","412121","111143","111341","131141","114113","114311","411113","411311","113141",
    "114131","311141","411131","211412","211214","211232","2331112"
]

def bits_code128(txt):
    cs = [104]; chk = 104
    for i, ch in enumerate(txt, 1):
        v = ord(ch) - 32; cs.append(v); chk += v * i
    cs.extend([chk % 103, 106])
    b = []
    for c in cs:
        bar = True
        for d in CODE128[c]:
            b.extend([1 if bar else 0] * int(d)); bar = not bar
    return b

def sincronizar_gtin_meli():
    tk = conectar_meli.obtener_token_valido()
    hdr = {"Authorization": f"Bearer {tk}"}
    p_ml = os.path.expanduser("~/meli_api_items_full.json")
    info = json.load(open(p_ml, "r", encoding="utf-8")) if os.path.exists(p_ml) else {}
    dic = json.load(open(P_EAN, "r", encoding="utf-8")) if os.path.exists(P_EAN) else {}
    ids = list(info.keys())
    nuevos = 0
    for i in range(0, len(ids), 20):
        try:
            r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(ids[i:i+20])}", headers=hdr, timeout=12).json()
            for ob in r:
                b = ob.get("body", {})
                mid = b.get("id", "")
                sku = info.get(mid, {}).get("sku", "") or mid
                for a in (b.get("attributes") or []):
                    if a.get("id") in ("GTIN", "EAN", "UPC") and a.get("value_name"):
                        for g in re.findall(r"\d{8,14}", str(a.get("value_name"))):
                            if g not in dic:
                                dic[g] = sku; nuevos += 1
        except Exception: pass
    json.dump(dic, open(P_EAN, "w", encoding="utf-8"), indent=2)
    return nuevos, len(dic)

def buscar_ean_internet(ean):
    tk = conectar_meli.obtener_token_valido()
    hdr = {"Authorization": f"Bearer {tk}"}
    p_aw = os.path.expanduser("~/AUDITORIA_PRE_SYNC.xlsx")
    skus_conocidos = set()
    if os.path.exists(p_aw):
        dfw = pd.read_excel(p_aw)
        skus_conocidos = {str(x).strip().upper().replace(".0", "") for x in dfw["SKU LOCAL"].dropna() if len(str(x).strip()) >= 4}

    for sk in skus_conocidos:
        sk_num = sk.replace("-", "")
        if len(sk_num) >= 7 and sk_num.isdigit() and sk_num in ean:
            return sk, f"Patrón numérico Dasqua/Insize dentro del EAN ({sk})"

    textos = []
    for url in (
        f"https://api.mercadolibre.com/products/search?status=active&site_id=MLC&product_identifier={ean}",
        f"https://api.mercadolibre.com/products/search?status=active&site_id=MLC&q={ean}"
    ):
        try:
            rj = requests.get(url, headers=hdr, timeout=6).json()
            for res in (rj.get("results") or []):
                textos.append(str(res.get("name", "")))
                for at in (res.get("attributes") or []):
                    textos.append(str(at.get("value_name", "")))
        except Exception: pass

    try:
        ru = requests.get(f"https://api.upcitemdb.com/prod/trial/lookup?upc={ean}", timeout=5).json()
        for it in (ru.get("items") or []):
            textos.extend([str(it.get("title", "")), str(it.get("model", "")), str(it.get("description", ""))])
    except Exception: pass

    blob = " ".join(textos).upper()
    for sk in skus_conocidos:
        if sk in blob or sk.replace("-", "") in blob:
            return sk, f"Encontrado en Internet / Catálogo Global ({sk})"
    m_d = re.search(r"\b(\d{4}-\d{4}(?:-[A-Z0-9]+)?)\b", blob)
    if m_d:
        return m_d.group(1), f"Modelo Dasqua detectado en red ({m_d.group(1)})"
    return None, (textos[0][:60] if textos else "")

def pdf_esc(s):
    return str(s).encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def generar_hoja_carta_40(cod_input):
    import dropbox
    dic = json.load(open(P_EAN, "r", encoding="utf-8")) if os.path.exists(P_EAN) else {}
    cod_bar = cod_input.strip().upper()
    dest = dic.get(cod_bar, cod_bar)

    p_aw = os.path.expanduser("~/AUDITORIA_PRE_SYNC.xlsx")
    titulo, sub = dest[:30], "INSUMAES.CL | CONTROL DE INVENTARIO"
    if os.path.exists(p_aw):
        import pandas as pd
        dfw = pd.read_excel(p_aw)
        for _, rw in dfw.iterrows():
            sl = str(rw.get("SKU LOCAL", "")).strip().upper().replace(".0", "")
            pl = str(rw.get("PRODUCTO LOCAL", "")).strip().upper()
            if dest in (sl, pl) or cod_bar in (sl, pl):
                titulo = pl[:30]
                if sl and sl not in ("NAN", "---"):
                    cod_bar = sl if len(sl) <= 14 else cod_bar
                    sub = f"SKU: {sl} | INSUMAES.CL"
                break

    W, H = 612.0, 792.0
    ml, mr, mt, mb = 18.0, 18.0, 28.0, 16.0
    cw, rh = (W - ml - mr) / 4.0, (H - mt - mb) / 10.0
    bits = bits_code128(cod_bar)
    nb = len(bits)

    ops = [f"BT /F1 10 Tf {W/2 - len(titulo)*2.5 - 80:.1f} {H - 18:.1f} Td ({pdf_esc(f'HOJA CARTA (40 STICKERS 4x10) - {titulo} ({cod_bar})')}) Tj ET"]
    for r in range(10):
        for c in range(4):
            x0, y0 = ml + c * cw + 3.0, H - mt - (r + 1) * rh + 3.0
            bw, bh = cw - 6.0, rh - 6.0
            ops.extend(["0.5 w [2 2] 0 d 0.4 G", f"{x0:.2f} {y0:.2f} {bw:.2f} {bh:.2f} re S", "[] 0 d 0 g 0 G"])
            t1, t2, t3 = titulo[:28], sub[:34], f"* {cod_bar} *"
            ops.append(f"BT /F1 6.6 Tf {x0 + bw/2 - len(t1)*1.8:.2f} {y0 + bh - 10.5:.2f} Td ({pdf_esc(t1)}) Tj ET")
            ops.append(f"0.3 g BT /F2 5.2 Tf {x0 + bw/2 - len(t2)*1.3:.2f} {y0 + bh - 17.5:.2f} Td ({pdf_esc(t2)}) Tj ET 0 g")
            bx0, by0, b_h, mod_w = x0 + 10.0, y0 + 13.5, bh - 34.0, (bw - 20.0) / float(nb)
            i = 0
            while i < nb:
                if bits[i] == 1:
                    j = i + 1
                    while j < nb and bits[j] == 1: j += 1
                    ops.append(f"{bx0 + i * mod_w:.3f} {by0:.2f} {(j - i) * mod_w:.3f} {b_h:.2f} re f")
                    i = j
                else: i += 1
            ops.append(f"BT /F3 7.4 Tf {x0 + bw/2 - len(t3)*2.2:.2f} {y0 + 4.2:.2f} Td ({pdf_esc(t3)}) Tj ET")

    sb = "\n".join(ops).encode("latin-1")
    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> /Contents 7 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n",
        b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold /Encoding /WinAnsiEncoding >>\nendobj\n",
        f"7 0 obj\n<< /Length {len(sb)} >>\nstream\n".encode("latin-1") + sb + b"\nendstream\nendobj\n"
    ]
    out, offs = bytearray(b"%PDF-1.4\n"), [0]
    for o in objs: offs.append(len(out)); out.extend(o)
    xp = len(out)
    out.extend(f"xref\n0 {len(offs)}\n0000000000 65535 f \n".encode("latin-1"))
    for of in offs[1:]: out.extend(f"{of:010d} 00000 n \n".encode("latin-1"))
    out.extend(f"trailer\n<< /Size {len(offs)} /Root 1 0 R >>\nstartxref\n{xp}\n%%EOF\n".encode("latin-1"))

    if titulo and cod_bar not in dic:
        dic[cod_bar] = titulo; json.dump(dic, open(P_EAN, "w", encoding="utf-8"), indent=2)
    limpio = re.sub(r"[^A-Z0-9_-]", "_", cod_bar)
    f_pdf = os.path.expanduser(f"~/ETIQUETAS_CARTA_40_{limpio}.pdf")
    open(f_pdf, "wb").write(bytes(out))

    dbx = dropbox.Dropbox(app_key=dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY'], app_secret=dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET'], oauth2_refresh_token=dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN'])
    dbx.files_upload(bytes(out), f"/ETIQUETAS_CARTA_40_{limpio}.pdf", mode=dropbox.files.WriteMode.overwrite)
    return f"/ETIQUETAS_CARTA_40_{limpio}.pdf"
