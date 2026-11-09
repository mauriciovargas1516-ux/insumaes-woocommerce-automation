import os, re, sys, json, time, hashlib, smtplib
os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass
RUTA_CFG, RUTA_LOG, RUTA_HASH = [os.path.expanduser(f"~/{x}") for x in ("config_bot.json", "historial_erp.log", "estado_antispam.json")]

def obtener_valor(k, d):
    try: return json.load(open(RUTA_CFG, "r", encoding="utf-8")).get(k, d) if os.path.exists(RUTA_CFG) else d
    except Exception: return d

def fmt_bitacora(l, num=None):
    m = re.match(r"^\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$", l.strip())
    pref = f"   {num:02d}. " if num is not None else "   • "
    if not m: return pref + l.strip()
    f, t, cod, nom, det = m.groups()
    hr = f[11:19] if len(f) >= 19 else f
    tm = re.search(r"\[(\d+\.\d+s)\]", det)
    ts = f" | ⏱️ {tm.group(1)}" if tm else ""
    dc = re.sub(r"Stock\s+(\d+)\s*(?:->|➔)\s*(\d+)\s*uds", r"\1 uds -> \2 uds", re.sub(r"\s*\|\s*Precio\s*\$(\d+)\s*(?:->|➔)\s*\$\1\b", "", re.sub(r"\s*\[\d+\.\d+s\]", "", det))).strip()
    ico, chg = "🔵🔄 [AJUSTE]", dc.replace("->", "➔")
    if "BLOQUEADO" in dc.upper() or "CORTAFUEGOS" in t.upper(): ico = "🛡️🚨 [CORTAFUEGOS]"
    elif "PRECIO" in t.upper() or ("$" in dc and "uds" not in dc):
        ps = re.findall(r"\$(\d+)", dc)
        if len(ps) >= 2:
            p1, p2 = int(ps[0]), int(ps[1])
            pct = int(round((p2 - p1) / max(p1, 1) * 100))
            ico, chg = (f"💰⬆️ [PRECIO +{pct}%]" if p2 >= p1 else f"💰⬇️ [PRECIO {pct}%]"), f"${p1:,} ➔ ${p2:,}".replace(",", ".")
        else: ico = "💰 [PRECIO]"
    else:
        ns = re.findall(r"(\d+)\s*uds", dc)
        if len(ns) >= 2:
            a, b = int(ns[0]), int(ns[1]); d = b - a
            ico, chg = ("🛑⚠️ [AGOTADO 0 UDS]", f"{a} ➔ 0 uds (Detenido)") if ("paused" in dc.split("->")[-1] or b == 0) else (("🚀✨ [ACTIVADO]", f"0 ➔ {b} uds (+{b})") if (a == 0 and b > 0) else ((f"🟢⬆️ [SUBIÓ +{d}]", f"{a} ➔ {b} uds (+{d})") if d > 0 else (f"🔴⬇️ [BAJÓ {d}]", f"{a} ➔ {b} uds ({d})")))
    plat = "🛒 Web insumaes.cl" if "WOO" in t else ("⏪ ML Restaurado" if "RESTORE" in t else "💛 Mercado Libre")
    lnk = (" -> https://insumaes.cl/?s=" + nom.split()[0] if nom.split() else "") if "WOO" in t else ((" -> https://articulo.mercadolibre.cl/" + cod.replace("MLC", "MLC-")) if cod.startswith("MLC") else "")
    return f"{pref}{ico:<19} | {chg:<22}{ts:<10} | [{cod}] {nom} ({plat} {hr}){lnk}"

def registrar_evento(tipo, cod, nom, det):
    linea = f"[{time.strftime('%d-%m-%Y %H:%M:%S')}] [{tipo}] {cod} | {str(nom)[:48]} | {det}\n"
    try:
        open(RUTA_LOG, "a", encoding="utf-8").write(linea)
        fp = os.path.expanduser("~/BITACORA_CAMBIOS_WOO.txt" if "WOO" in str(tipo).upper() else "~/BITACORA_CAMBIOS_MELI.txt")
        open(fp, "a", encoding="utf-8").write(fmt_bitacora(linea) + "\n")
    except Exception: pass

def _debe_enviar_correo(c_str):
    if "--forzar" in sys.argv or str(obtener_valor("CORREO_ANTISPAM", "SI")).upper() != "SI": return True
    h = hashlib.md5(re.sub(r"\d{2}-\d{2}-\d{4}\s+\d{1,2}:\d{2}(:\d{2})?|\d{1,2}:\d{2}(:\d{2})?|\d+\.\d+\s*seg", "", str(c_str)).encode("utf-8", errors="ignore")).hexdigest()
    est = json.load(open(RUTA_HASH, "r", encoding="utf-8")) if os.path.exists(RUTA_HASH) else {}
    if est.get("ultimo_hash") == h: return False
    try: json.dump({"ultimo_hash": h, "fecha": time.strftime("%d-%m-%Y %H:%M:%S")}, open(RUTA_HASH, "w", encoding="utf-8"))
    except Exception: pass
    return True

for _c in (smtplib.SMTP, smtplib.SMTP_SSL):
    if not getattr(_c, "_antispam_hooked", False):
        _o = _c.sendmail
        _c.sendmail = lambda s, f, t, m, *a, **k: ({} if not _debe_enviar_correo(m) else _o(s, f, t, m, *a, **k))
        _c._antispam_hooked = True
