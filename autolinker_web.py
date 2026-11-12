import os, re, sys, time, json
from concurrent.futures import ThreadPoolExecutor
from woocommerce import API

MAPA_BROCAS_N = {
    "8": ("4D-8,0C20-SP03-02", "20 mm", "SPMG030104"), "8,5": ("4D-8,5C20-SP03-02", "20 mm", "SPMG030104"),
    "9": ("4D-9,0C20-SP03-02", "20 mm", "SPMG030104"), "9,5": ("4D-9,5C20-SP03-02", "20 mm", "SPMG030104"),
    "10": ("4D-10-C20-SP04-02", "20 mm", "SPMG040204"), "10,5": ("4D-10,5-C20-SP04-02", "20 mm", "SPMG040204"),
    "11": ("4D-11-C20-SP04-02", "20 mm", "SPMG040204"), "11,5": ("4D-11,5-C20-SP04-02", "20 mm", "SPMG040204"),
    "12": ("ZD04-12-XP20-SP04-02", "20 mm", "SPMG040204"), "13": ("ZD04-13-XP20-SP05-02", "20 mm", "SPGT050204-MG"),
    "15": ("ZD04-15-XP20-SP05-02", "20 mm", "SPGT050204-MG"), "20": ("ZD04-20-XP25-SP06-02", "25 mm", "SPGT060204-MG"),
    "22": ("ZD04-22-XP25-SP07-02", "25 mm", "SPGT07T308-MG"), "50": ("ZD04-50-XP40-SP14-02", "40 mm", "SPGT140512-MG"),
    "55": ("ZD04-55-XP40-SP07-04", "40 mm", "SPGT07T308-MG"), "60": ("ZD04-60-XP40-SP09-04", "40 mm", "SPGT090408-MG"),
    "65": ("ZD04-65-XP40-WC06-04", "40 mm", "WCMT06T308-MG"), "70": ("ZD04-70-XP40-WC06-04", "40 mm", "WCMT06T308-MG"),
}

def url_g(q):
    return f"https://www.insumaes.cl/?s={q}&post_type=product&dgwt_wcas=1"

def btn(etq, url):
    return f'<a href="{url}" target="_blank" style="display:inline-block;background-color:#0b3c5d;color:#ffffff !important;padding:5px 12px;margin:6px 6px 2px 0;border-radius:4px;font-weight:bold;text-decoration:underline !important;font-size:0.92em;">🔗 {etq} ➔</a>'

def construir_botones_caja(z_u):
    botones, vistos = [], set()
    def add(k, e, u):
        if k not in vistos: vistos.add(k); botones.append(btn(e, u))

    REGLAS = [
        (r"\bTNMG\b", "TNMG", ("Ver Insertos TNMG22", url_g("TNMG22")) if "22" in z_u else ("Ver Insertos TNMG16", url_g("TNMG16"))),
        (r"\bTCMT\b", "TCMT", ("Ver Insertos TCMT16", url_g("TCMT16")) if "16" in z_u else (("Ver Insertos TCMT09", url_g("TCMT09")) if "09" in z_u else ("Ver Insertos TCMT11", url_g("TCMT11")))),
        (r"\bCNMG\b", "CNMG", ("Ver Insertos CNMG", url_g("CNMG"))),
        (r"\bCCMT\b", "CCMT", ("Ver Insertos CCMT06", url_g("CCMT06")) if "06" in z_u else (("Ver Insertos CCMT09", url_g("CCMT09")) if "09" in z_u else ("Ver Insertos CCMT", url_g("CCMT")))),
        (r"\bDNMG\b", "DNMG", ("Ver Insertos DNMG", url_g("DNMG"))),
        (r"\bDCMT\b", "DCMT", ("Ver Insertos DCMT07", url_g("DCMT07")) if "07" in z_u else ("Ver Insertos DCMT11", url_g("DCMT11"))),
        (r"\bWNMG\b", "WNMG", ("Ver Insertos WNMG0804", url_g("WNMG"))),
        (r"\bSNMG\b", "SNMG", ("Ver Insertos SNMG", url_g("SNMG"))),
        (r"\bSCMT\b", "SCMT", ("Ver Plaquita SCMT09T308 ($5.300)", "https://www.insumaes.cl/?p=3199")),
        (r"\bVNMG\b|\bVCMT\b", "VCMT", ("Ver Insertos VCMT", url_g("VCMT"))),
        (r"\bVBMT\b", "VBMT", ("Ver Insertos VBMT", url_g("VBMT"))),
        (r"\bKNUX\b", "KNUX", ("Ver Plaquita KNUX160405R11 ($6.800)", "https://www.insumaes.cl/?p=7212")),
        (r"\bRCMT\b", "RCMT", ("Ver Insertos Redondos RCMT", url_g("RCMT"))),
        (r"\bRCMX\b", "RCMX", ("Ver Insertos Redondos RCMX", url_g("RCMX"))),
        (r"\bMGMN", "MGMN", ("Ver Insertos Ranurado MGMN", url_g("MGMN"))),
        (r"\bMRMN", "MRMN", ("Ver Insertos Redondos MRMN", url_g("MRMN"))),
        (r"\bSP[2345]00\b", "SP_TR", ("Ver Insertos Tronzado SP200-SP500", url_g("LAU25"))),
        (r"\bSPGT", "SPGT", ("Ver los 6 Modelos SPGT (5mm a 14mm)", url_g("SPGT"))),
        (r"\bSPMG", "SPMG", ("Ver Insertos Broca U SPMG", url_g("SPMG"))),
        (r"\bWCMT\b|\bWCMX\b", "WCMT", ("Ver Insertos WCMT", url_g("WCMT"))),
        (r"\bSOMT\b", "SOMT", ("Ver Inserto SOMT12T308", url_g("SOMT"))),
        (r"\bAPMT", "APMT", ("Ver Inserto APMT1135 ($4.500)", url_g("APMT1135"))),
        (r"\bAPKT", "APKT", ("Ver Inserto APKT1604 ($5.500)", url_g("APKT1604"))),
        (r"\bSEHT|\bSEKT|\bSEKR|\bSEKN", "SEKT", ("Ver Insertos SEKT1204 / SEHT1204", url_g("SEKT1204"))),
        (r"\bMPHT", "MPHT", ("Ver Insertos MPHT", url_g("MPHT"))),
        (r"\b11IR\b|\b11NR\b", "11IR", ("Ver Insertos Rosca Interior 11NR", url_g("11NR"))),
        (r"\b11ER\b|\b11EL\b|\b11NL\b", "11ER", ("Ver Insertos Rosca 11NRA / 11NLA", url_g("11N"))),
        (r"\b16ER\b", "16ER", ("Ver Insertos Rosca Exterior 16ER", url_g("16ER"))),
        (r"\b16EL\b", "16EL", ("Ver Insertos Rosca Exterior 16EL", url_g("16EL"))),
        (r"\b16IR\b", "16IR", ("Ver Insertos Rosca Interior 16IR", url_g("16IR"))),
        (r"\b22ER\b", "22ER", ("Ver Insertos Rosca Exterior 22ER", url_g("22ER"))),
        (r"\b22EL\b", "22EL", ("Ver Insertos Rosca Exterior 22EL", url_g("22EL"))),
        (r"\b22IR\b", "22IR", ("Ver Insertos Rosca Interior 22IR", url_g("22IR"))),
        (r"\b27ER\b|\b27EL\b", "27ER", ("Ver Insertos Rosca 27ER", url_g("27ER"))),
        (r"\b27IR\b", "27IR", ("Ver Insertos Rosca 27IR", url_g("27IR"))),
        (r"\bMTJNR", "P_MTJ", ("Ver Portaherramientas MTJNR", url_g("MTJNR"))),
        (r"\bWTJNR", "P_WTJ", ("Ver Portaherramientas WTJNR", url_g("WTJNR"))),
        (r"\bMTENN", "P_MTE", ("Ver Portaherramientas MTENN", url_g("MTENN"))),
        (r"\bMCLNR|\bPCLNR", "P_MCL", ("Ver Portaherramientas MCLNR", url_g("MCLNR"))),
        (r"\bSCLCR", "P_SCL", ("Ver Barras Interiores SCLCR", url_g("SCLCR"))),
        (r"\bMDJNR", "P_MDJ", ("Ver Portaherramientas MDJNR", url_g("MDJNR"))),
        (r"\bSDNCN", "P_SDN", ("Ver Portaherramientas SDNCN", url_g("SDNCN"))),
        (r"\bSDJCR", "P_SDJ", ("Ver Portaherramientas SDJCR", url_g("SDJCR"))),
        (r"\bSVVCN|\bSVJCR", "P_SVJ", ("Ver Portaherramientas SVJCR / SVVCN", url_g("SVVCN"))),
        (r"\bMSSNR|\bPSSNR", "P_PSS", ("Ver Portaherramientas PSSNR / MSDNN", url_g("MSDNN"))),
        (r"\bMWLNR|\bWWLNR", "P_MWL", ("Ver Portaherramientas MWLNR / WWLNR", url_g("MWLNR"))),
        (r"\bCKJNR", "P_CKJ", ("Ver Portaherramientas CKJNR", url_g("CKJNR"))),
        (r"ROSCADO SER\b", "P_SER", ("Ver Portaherramientas Roscado SER", url_g("SER"))),
        (r"ROSCADO SEL\b", "P_SEL", ("Ver Portaherramientas Roscado SEL", url_g("SEL"))),
        (r"ROSCADO SNR\b|\bROSCADO SNL\b", "P_SNR", ("Ver Portaherramientas Roscado SNR", url_g("SNR"))),
        (r"\bMGEHR", "P_MGE", ("Ver Portaherramientas Ranurado MGEHR", url_g("MGEHR"))),
        (r"\bSPB\d*", "P_SPB", ("Ver Lamas de Tronzar SPB", url_g("SPB"))),
        (r"\bSMBB", "P_SMB", ("Ver Bloques Tronzado SMBB", url_g("SMBB"))),
        (r"BROCAS U\b", "P_ZD", ("Ver Brocas con Inserto ZD04", url_g("ZD04"))),
        (r"PLATO DE TORNO", "PLATO", ("Ver Platos de Torno", url_g("PLATO+TORNO"))),
        (r"BOQUILLAS? (?:DE PRECISIÓN )?\(?EJ\.?\s*ER\)?|BOQUILLAS ER", "BOQ_ER", ("Ver Boquillas y Portafresas ER", url_g("ER"))),
        (r"WELDON", "WELDON", ("Ver Tomas Weldon SLN", url_g("WELDON"))),
        (r"ENCASTRE B1[268]|ENCASTRE B2[24]", "MANDRIL", ("Ver Portabrocas / Mandriles", url_g("PORTA+BROCA"))),
        (r"CONO MORSE", "CM_RED", ("Ver Conos y Contrapuntas Morse", url_g("CONO+MORSE"))),
        (r"CABEZALES DE FRESADO O PLATOS PLANEADORES", "CAB_FR", ("Ver Cabezales de Fresado BAP / KM12", url_g("BAP"))),
    ]
    for pat, k, (etq, u) in REGLAS:
        if re.search(pat, z_u): add(k, etq, u)
    return botones

def procesar_html(pid, nom, dl):
    if int(pid) in (14499, 14500, 14501, 14525, 14526, 14527, 14528, 14529, 14530):
        return dl, False
    h = re.sub(r'<div class="insumaes-auto-links"[^>]*>.*?</div>', '', dl or "", flags=re.S)
    nu = nom.upper().strip()

    if any(k in nu for k in ("MTFNR", "MTUNR", "WTUNR", "PTFNR", "MTWNR", "MTQNR")) and "TCMT/TCGT" in h.upper():
        sz = "22" if "22" in nu[-4:] else "16"
        h = re.sub(r"insertos positivos\s*<strong>\s*TCMT/TCGT tamaño \d+\s*</strong>", f"insertos negativos <strong>TNMG tamaño {sz}</strong>", h, flags=re.I)
    if "MWLNR" in nu and "WCMT" in h.upper():
        h = re.sub(r"insertos positivos\s*<strong>\s*WCMT tamaño 08\s*</strong>", "insertos trigonales <strong>WNMG tamaño 08 (WNMG0804)</strong>", h, flags=re.I)
    if "FORMA ISO R" in h.upper():
        h = re.sub(r"Forma ISO R tamaño (\d+)", r"RCMT / RCMX tamaño \1", h, flags=re.I)
    if "FORMA ISO K" in h.upper():
        h = re.sub(r"Forma ISO K tamaño 16", "KNUX tamaño 16 (KNUX160405R11 LAM9315)", h, flags=re.I)
    if "KNUX" in nu and "FORMA K" in h.upper():
        h = re.sub(r"Portaherramientas estándar para forma K", "CKJNR / CKJNL", h, flags=re.I)

    m_br = re.search(r"BROCA CON INSERTO N\s*°?\s*(\d+(?:,\d+)?)", nu)
    if m_br and m_br.group(1) in MAPA_BROCAS_N:
        cf, vast, ins_f = MAPA_BROCAS_N[m_br.group(1)]
        h = h.replace("Verificar grabado láser", cf).replace("Revisar mm", vast).replace("Verificar catálogo", ins_f)

    m_box = re.search(r'<div[^>]*style="[^"]*(?:#fff9e6|#fff8e6|#fffdf5)[^"]*"[^>]*>', h, re.I)
    if not m_box: return h, (h != dl)
    pos_close = h.find("</div>", m_box.end())
    if pos_close == -1: return h, (h != dl)

    z_u = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h[m_box.start():pos_close])).upper()
    btns = construir_botones_caja(z_u)
    if not btns: return h, (h != dl)

    bloque = f'<div class="insumaes-auto-links" style="margin-top:10px;">{"".join(btns)}</div>'
    return h[:pos_close] + bloque + h[pos_close:], True

def correr():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    CK, CS = env["WOO_KEY"], env["WOO_SECRET"]
    f_json = os.path.expanduser("~/respaldo_html_completo_woo.json")
    datos = json.load(open(f_json, "r", encoding="utf-8"))
    tareas = []
    for pid_s, p in datos.items():
        nh, ok = procesar_html(int(pid_s), p.get("name", ""), p.get("description", ""))
        if ok: tareas.append((int(pid_s), p.get("name", ""), nh))

    if "--piloto" in sys.argv: tareas = tareas[:15]
    elif "--restantes" in sys.argv: tareas = tareas[15:]
    print(f"\n🚀 Actualizando {len(tareas)} fichas con Botones Bidireccionales ADENTRO de la Caja Amarilla...", flush=True)

    def subir(item):
        i, (pid, nom, nh) = item
        wc = API(url="https://www.insumaes.cl/", consumer_key=CK, consumer_secret=CS, version="wc/v3", timeout=45)
        for _ in range(3):
            try:
                r = wc.put(f"products/{pid}", {"description": nh})
                if r.status_code in (200, 201):
                    return f"  ✅ [{i:03d}/{len(tareas)}] ID:{pid:<6} | {nom[:44]}"
            except Exception:
                pass
            time.sleep(1.2)
        return f"  ⚠️ [{i:03d}/{len(tareas)}] ID:{pid:<6} | Reintentar luego"

    with ThreadPoolExecutor(max_workers=3) as ex:
        for msg in ex.map(subir, enumerate(tareas, 1)):
            print(msg, flush=True)
    print(f"\n🏁 ¡Listo! {len(tareas)} productos quedaron interconectados en insumaes.cl.", flush=True)

if __name__ == "__main__":
    correr()

def restaurar_original(id_unico=None):
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    wc = API(url="https://www.insumaes.cl/", consumer_key=env["WOO_KEY"], consumer_secret=env["WOO_SECRET"], version="wc/v3", timeout=45)
    datos = json.load(open(os.path.expanduser("~/respaldo_html_completo_woo.json"), "r", encoding="utf-8"))
    ids = [str(id_unico)] if id_unico else [ str(k) for k, p in datos.items() if procesar_html(int(k), p.get("name",""), p.get("description",""))[1] ]
    print(f"\n⏪ Restaurando HTML original de {len(ids)} productos desde la bóveda...", flush=True)
    for idx, pid in enumerate(ids, 1):
        if pid in datos:
            wc.put(f"products/{pid}", {"description": datos[pid]["description"]})
            print(f"  ⏪ [{idx:03d}/{len(ids)}] ID:{pid} ({datos[pid]['name']}) restaurado al original.", flush=True)
