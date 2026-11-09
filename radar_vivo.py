import os, re, sys, time, shutil, select, subprocess
os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

def limpiar_detalle(det):
    dc = re.sub(r"\s*\[\d+\.\d+s\]", "", det).replace("->", "➔").strip()
    dc = re.sub(r"\s*\|\s*Precio\s*\$(\d+)\s*➔\s*\$\1\b", "", dc)
    dc = re.sub(r"Stock\s+(\d+)\s*➔\s*(\d+)\s*uds", r"\1 uds ➔ \2 uds", dc)
    return dc

def clasificar(l):
    m = re.match(r"^\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$", l)
    if not m: return None
    f, t, cod, nom, det = m.groups()
    dc = limpiar_detalle(det)
    ns = re.findall(r"(\d+)\s*uds", dc)
    if len(ns) >= 2:
        a, b = int(ns[0]), int(ns[1])
        if a == b and "PAUSA" not in t and "paused" not in dc and "$" not in dc: return None
        est = "AGOTADO" if ("paused" in dc.split("➔")[-1] or b == 0) else ("ACTIVADO" if (a == 0 and b > 0) else ("SUBIO" if b > a else "BAJO"))
    else:
        a, b, est = 0, 0, ("PRECIO" if "$" in dc else "OTRO")
    return f, t, cod, nom, det, dc, a, b, est

def abrir_radar_completo():
    ft, off = "TODOS", 0
    while True:
        os.system("clear")
        cols, lines = shutil.get_terminal_size((134, 75))
        W = max(118, min(156, cols - 1))
        mf = max(20, lines - 7)
        pids = subprocess.getoutput("pgrep -f 'marcha_rapida_delta.py'").splitlines()
        ev = f"🟢 ACTIVO (PID {pids[0]})" if pids else "🔴 DETENIDO"
        rl = os.path.expanduser("~/historial_erp.log")
        todas = [l.strip() for l in open(rl, "r", encoding="utf-8", errors="ignore").readlines() if l.strip() and "RESTORE" not in l] if os.path.exists(rl) else []
        hoy = time.strftime("%d-%m-%Y"); hls = [l for l in todas if l.startswith(f"[{hoy}")]
        cw = sum(1 for l in hls if "WOO" in l)
        cm = sum(1 for l in hls if "MELI" in l and "PAUSA" not in l)
        cp = sum(1 for l in hls if "PAUSA" in l or "paused" in l)
        cpos = sum(1 for l in hls if "POS-" in l or "VENTA" in l)

        parsed = [x for l in reversed(todas) for x in [clasificar(l)] if x is not None]
        vs = parsed
        if ft == "WOO": vs = [x for x in parsed if "WOO" in x[1]]
        elif ft == "MELI": vs = [x for x in parsed if "MELI" in x[1]]
        elif ft == "POS": vs = [x for x in parsed if "POS-" in x[1] or "VENTA" in x[1]]
        elif ft == "ACTIVADOS": vs = [x for x in parsed if x[8] == "ACTIVADO"]
        elif ft == "AGOTADOS": vs = [x for x in parsed if x[8] == "AGOTADO"]

        tv = len(vs); off = max(0, min(off, max(0, tv - mf)))
        print("=" * W)
        print(f"📡 RADAR VERTICAL A PANTALLA COMPLETA [{ft}] ({mf} filas) | 💓 {ev} | HOY: 🛒Woo:{cw} | 💛Meli:{cm} | 🛑Pausas:{cp} | 🔫POS:{cpos}")
        print("=" * W)
        for idx, (f, t, cod, nom, det, dc, a, b, est) in enumerate(vs[off:off + mf], start=off + 1):
            hr = f[11:19] if len(f) >= 19 else f
            tm_m = re.search(r"\[(\d+\.\d+s)\]", det); ts = f"⏱️ {tm_m.group(1)}" if tm_m else "⏱️ ~0.35s"
            tag = "🛍️💛 [VENTA-ML] " if "VENTA" in t else ("🔫🛒 [POS-WOO]  " if "POS-WOO" in t else ("🔫💛 [POS-MELI] " if "POS-MELI" in t else ("🛒 [WOOCOMMERCE]" if "WOO" in t else "💛 [MERCADOLIBRE]")))
            ico = "🛑⚠️(0)" if est=="AGOTADO" else ("🚀✨ACT" if est=="ACTIVADO" else (f"🟢⬆️(+{b-a})" if est=="SUBIO" else (f"🔴⬇️({b-a})" if est=="BAJO" else "💰PRECIO")))
            print(f"{idx:03d} | ⚡{hr} | {tag:<16} | {ico:<9} | {dc:<22} | {ts:<9} | {nom[:max(24, W-88)]} ({cod})")
        print("=" * W)
        print(f"📄 {off+1}-{min(off+mf, tv)} de {tv} | [Enter/S] Bajar {mf} | [A] Subir {mf} | [V] 📜Desplegar 500 (Rueda Mouse) | [T] Todos | [W] Woo | [M] Meli | [X] 🚀Act | [Z] 🛑Ago | [0] Volver")
        sys.stdout.write("👉 Opción: "); sys.stdout.flush()
        r, _, _ = select.select([sys.stdin], [], [], 2.0)
        if r:
            op = sys.stdin.readline().strip().upper()
            if op == "0": break
            elif op in ("", "S"): off += mf
            elif op == "A": off = max(0, off - mf)
            elif op in ("T","W","M","P","X","Z"): ft, off = {"T":"TODOS","W":"WOO","M":"MELI","P":"POS","X":"ACTIVADOS","Z":"AGOTADOS"}[op], 0
            elif op == "G": import pistola_pos; pistola_pos.abrir_pistola(); break
            elif op == "V":
                os.system("clear")
                print("=" * W)
                print(f"📜 MODO CASCADA VERTICAL [{ft}] — Usa la rueda del mouse para subir y bajar libremente (Últimos 500 impactos):")
                print("=" * W)
                for idx, (f, t, cod, nom, det, dc, a, b, est) in enumerate(vs[:500], start=1):
                    hr = f[11:19] if len(f) >= 19 else f
                    tm_m = re.search(r"\[(\d+\.\d+s)\]", det); ts = f"⏱️ {tm_m.group(1)}" if tm_m else "⏱️ ~0.35s"
                    tag = "🛒 [WOOCOMMERCE]" if "WOO" in t else "💛 [MERCADOLIBRE]"
                    ico = "🛑⚠️(0)" if est=="AGOTADO" else ("🚀✨ACT" if est=="ACTIVADO" else (f"🟢⬆️(+{b-a})" if est=="SUBIO" else (f"🔴⬇️({b-a})" if est=="BAJO" else "💰PRECIO")))
                    print(f"{idx:03d} | ⚡{hr} | {tag:<16} | {ico:<9} | {dc:<22} | {ts:<9} | {nom[:max(24, W-88)]} ({cod})")
                print("=" * W)
                input("👉 Sube y baja con la rueda del mouse. Presiona [Enter] para volver al Radar en vivo...")
if __name__ == "__main__": abrir_radar_completo()
