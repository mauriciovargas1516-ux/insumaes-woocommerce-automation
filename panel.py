import os, json

RUTA_CFG = os.path.expanduser("~/config_bot.json")
RUTA_BAK = os.path.expanduser("~/respaldo_meli_original.json")
DEF_CFG = {
    "SINCRONIZAR_WOOCOMMERCE": "SI", "SINCRONIZAR_WOO_STOCK": "SI", "SINCRONIZAR_WOO_PRECIOS": "SI",
    "MODO_TURBO_DELTA": "SI", "AUDITOR_MELI": "SI", "SINCRONIZAR_MELI_STOCK": "NO",
    "SINCRONIZAR_MELI_PRECIOS": "NO", "PORCENTAJE_COLCHON": 50, "LIMITE_CORTAFUEGOS": 40,
    "MLC_PILOTO_PRUEBA": "NINGUNO", "CORREO_ANTISPAM": "SI"
}

def cargar():
    c = dict(DEF_CFG)
    if os.path.exists(RUTA_CFG):
        try: c.update(json.load(open(RUTA_CFG, "r", encoding="utf-8")))
        except Exception: pass
    return c

def guardar(c):
    c["SINCRONIZAR_WOOCOMMERCE"] = "NO" if (c.get("SINCRONIZAR_WOO_STOCK")=="NO" and c.get("SINCRONIZAR_WOO_PRECIOS")=="NO") else "SI"
    json.dump(c, open(RUTA_CFG, "w", encoding="utf-8"), indent=4)

def info_bak():
    if os.path.exists(RUTA_BAK):
        try:
            d = json.load(open(RUTA_BAK, "r", encoding="utf-8"))
            return f"✅ {d.get('total', len(d.get('items', {})))} ítems ({d.get('fecha', '')})"
        except Exception: pass
    return "⚠️ Sin foto aún"

def ico(v): return "🟢  SI" if str(v).upper() == "SI" else "🔴  NO"

def mostrar_radar_hud():
    import os, shutil, subprocess, time, re
    os.environ["TZ"] = "America/Santiago"
    try: time.tzset()
    except Exception: pass
    W = max(118, min(148, shutil.get_terminal_size((126, 30)).columns - 1))
    pids = subprocess.getoutput("pgrep -f 'marcha_rapida_delta.py'").splitlines()
    est_v = f"🟢 ACTIVO EN RAM (PID {pids[0]})" if pids else "🔴 DETENIDO"
    r_cat = os.path.expanduser("~/Catalogo PortasHerramientas e Insertos.xlsx")
    sync_t = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(r_cat))) if os.path.exists(r_cat) else "--:--:--"
    r_log = os.path.expanduser("~/historial_erp.log")
    todas = [l.strip() for l in open(r_log, "r", encoding="utf-8", errors="ignore").readlines() if l.strip()] if os.path.exists(r_log) else []
    hoy_ls = [l for l in todas if l.startswith(f"[{time.strftime('%d-%m-%Y')}")]
    c_w = sum(1 for l in hoy_ls if "[WOO" in l and "CORTAFUEGOS" not in l)
    c_m = sum(1 for l in hoy_ls if "[MELI" in l and "PAUSA" not in l)
    c_p = sum(1 for l in hoy_ls if "PAUSA" in l or "paused" in l)
    c_b = sum(1 for l in hoy_ls if "CORTAFUEGOS" in l or "BLOQUEADO" in l)
    tw = [float(m.group(1)) for l in hoy_ls if "[WOO" in l for m in [re.search(r"\[(\d+\.\d+)s\]", l)] if m]
    tm = [float(m.group(1)) for l in hoy_ls if "[MELI" in l for m in [re.search(r"\[(\d+\.\d+)s\]", l)] if m]
    aw, am = (f"{sum(tw)/len(tw):.2f}s" if tw else "0.38s"), (f"{sum(tm)/len(tm):.2f}s" if tm else "0.29s")
    print("=" * W)
    print("🎛️  PANEL DE CONTROL OMNICANAL — ERP INSUMAES CLOUD (AUTOGUARDADO & TELEMETRÍA EN VIVO)")
    print(f"💓 VIGILANTE 24/7 : {est_v} — Ciclo 3s | ☁️ Últ. Sync Dropbox: {sync_t} | ⚡ VELOCIDAD API: 🛒 Woo {aw} vs 💛 Meli {am}")
    print(f"📊 TELEMETRÍA HOY : 🛒 [WOO]: {c_w} cambios | 💛 [MELI]: {c_m} cambios | 🛑 [PAUSADOS]: {c_p} | 🛡️ [CORTAFUEGOS]: {c_b}")
    print("-" * W)
    print("📡 RADAR DE INYECCIÓN EN VIVO (Últimos 5 impactos con cronómetro de respuesta en segundos ⚡):")
    vivos = [l for l in todas if "RESTORE" not in l]
    n_top = max(5, min(28, shutil.get_terminal_size((126, 30)).lines - 34))
    for l in list(reversed(vivos if vivos else todas))[:n_top]:
        m = re.match(r"^\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$", l)
        if m:
            f, t, cod, nom, det = m.groups()
            hr = f[11:19] if len(f) >= 19 else f
            tm_m = re.search(r"\[(\d+\.\d+s)\]", det)
            ts = f"⏱️ {tm_m.group(1)}" if tm_m else "⏱️ ~0.4s"
            dc = re.sub(r"Stock\s+(\d+)\s*➔\s*(\d+)\s*uds", r"\1 uds ➔ \2 uds", re.sub(r"\s*\|\s*Precio\s*\$(\d+)\s*➔\s*\$\1\b", "", re.sub(r"\s*\[\d+\.\d+s\]", "", det).replace("->", "➔"))).strip()
            tag = "🛡️ [CORTAFUEGOS]" if "CORTAFUEGOS" in t else ("💰 [WOO-PRECIO] " if "PRECIO" in t else ("🛒 [WOOCOMMERCE]" if "WOO" in t else "💛 [MERCADOLIBRE]"))
            ico = "🛡️🚨 BLOQ" if "BLOQUEADO" in dc.upper() else ("💰 PRECIO" if ("$" in dc and "uds" not in dc) else "🔵🔄")
            ns = re.findall(r"(\d+)\s*uds", dc)
            if len(ns) >= 2 and ico == "🔵🔄":
                a, b = int(ns[0]), int(ns[1])
                ico = "🛑⚠️AGOTADO" if ("paused" in dc or b == 0) else ("🚀✨ACTIVADO" if (a == 0 and b > 0) else (f"🟢⬆️(+{b-a})" if b > a else f"🔴⬇️({b-a})"))
            print(f"   ⚡ {hr} | {tag:<16} | {ico:<9} | {dc:<22} | {ts:<8} | {nom[:max(28, W-78)]} ({cod})")
    print("=" * W)

def pedir_opcion_vivo(prompt):
    import sys, os, select
    r_log = os.path.expanduser("~/historial_erp.log")
    r_cat = os.path.expanduser("~/Catalogo PortasHerramientas e Insertos.xlsx")
    mt_l = os.path.getmtime(r_log) if os.path.exists(r_log) else 0
    mt_c = os.path.getmtime(r_cat) if os.path.exists(r_cat) else 0
    sys.stdout.write(prompt)
    sys.stdout.flush()
    while True:
        r, _, _ = select.select([sys.stdin], [], [], 2.0)
        if r:
            return sys.stdin.readline().strip()
        nl = os.path.getmtime(r_log) if os.path.exists(r_log) else 0
        nc = os.path.getmtime(r_cat) if os.path.exists(r_cat) else 0
        if nl != mt_l or nc != mt_c:
            return ""

def menu():
    os.system("pgrep -f 'marcha_rapida_delta.py$' > /dev/null 2>&1 || (nohup python3 ~/marcha_rapida_delta.py >/dev/null 2>&1 &)")
    c, msg = cargar(), ""
    while True:
        os.system("clear")
        pil = str(c.get("MLC_PILOTO_PRUEBA", "NINGUNO")).strip().upper()
        es_p = pil not in ("", "NINGUNO", "NO", "NONE")
        mostrar_radar_hud()
        print("🛒 TIENDA WEB (WOOCOMMERCE - insumaes.cl)")
        print(f" [1] WOO_STOCK (Cantidades)   : {ico(c['SINCRONIZAR_WOO_STOCK'])}  | Sube el stock con colchón a tu web")
        print(f" [2] WOO_PRECIOS (Valores)    : {ico(c['SINCRONIZAR_WOO_PRECIOS'])}  | Sube los precios con IVA a tu web")
        print(f" [3] MODO_TURBO_DELTA (3s)    : {ico(c['MODO_TURBO_DELTA'])}  | Vigila tu Excel en vivo cada 3 seg")
        print("------------------------------------------------------------------------------------------")
        print("💛 MERCADO LIBRE (782 Publicaciones)")
        print(f" [4] AUDITOR_MELI (Excel)     : {ico(c['AUDITOR_MELI'])}  | Actualiza el Excel AUDITORIA_MELI en Dropbox")
        print(f" [5] MELI_STOCK (Cantidades)  : {ico(c['SINCRONIZAR_MELI_STOCK'])}  | Sube el {c['PORCENTAJE_COLCHON']}% de tu bodega y pausa agotados en ML")
        print(" [6] MELI_PRECIOS (Valores)   : 🔒  BLOQUEADO (NO) | Protegido: Nunca toca tus precios en ML")
        print("------------------------------------------------------------------------------------------")
        print("🛡️  REGLAS Y PRUEBAS")
        print(f" [7] PORCENTAJE_COLCHON       : 🔵 {c['PORCENTAJE_COLCHON']}%   | % de bodega que se publica en ML y Web")
        cf_v = int(c.get("LIMITE_CORTAFUEGOS", 40) or 0)
        cf_txt = f"🛡️  ON ({cf_v}%)  | Bloquea cambios bruscos > {cf_v}% (8+Enter = Apagar)" if cf_v > 0 else "🔓 OFF (LIBRE) | Pase libre de precios activo (Solo bloquea $0)"
        print(f" [8] CORTAFUEGOS PRECIOS      : {cf_txt}")
        print(f" [9] MODO PRUEBA (PILOTO)     : {'🎯 '+pil+' (Presiona 9 para APAGAR)' if es_p else '🧪 ABRIR LABORATORIO EN VIVO (Sugerencias + Test 1 clic)'}")
        print("------------------------------------------------------------------------------------------")
        print(f" [10] 📸 GUARDAR FOTO DE SEGURIDAD MELI  | Foto actual: {info_bak()}")
        print(" [11] ⏪ RESTAURAR STOCK ORIGINAL MELI   | Devuelve tus 782 ítems a la foto [10]")
        print(" [12] 📜 VER BITÁCORA DE CAMBIOS         | Muestra qué cambió (Antes -> Ahora)")
        print(" [13] 📦 ENVIAR SISTEMA (.ZIP) A DROPBOX | Guarda respaldo completo en la raíz de tu Dropbox")
        print(" [14] ⚡ EJECUTAR SINCRONIZACIÓN AHORA   | Corre el motor ahora mismo sin salir del panel")
        print(" [15] 📧 ENVIAR REPORTE AL CORREO AHORA  | Envía el correo con bitácora y Excels a tu Gmail")
        print(" [16] 📄 EXPORTAR CÓDIGO/LOGS (.TXT)     | Sube RADIOGRAFIA_ERP_INSUMAES.txt a tu Dropbox")
        print(" [17] 🔍 AUDITOR COMPARADOR (WOO vs ML)  | Compara lado a lado Stock, Precios y SKUs en vivo")
        print(" [18] 📡 RADAR EN VIVO PANTALLA COMPLETA | Muestra hasta 30 impactos en tiempo real + Filtros")
        print(" [19] 🔫 PISTOLA BARRAS & VENTAS MELI    | Descuenta ventas por interno (Pistola) o desde ML")
        print(" [20] 🚀🛑 MONITOR ACTIVADOS Y AGOTADOS   | Muestra qué se activó (0->Stock) y qué se agotó (0 uds)")
        print("==========================================================================================")
        print(" [0] Salir (Todo se guarda solo al presionar cada número)")
        if msg: print(f"\n💡 {msg}"); msg = ""
        op = pedir_opcion_vivo("\n👉 Opción (0-20): ")
        if op == "0": guardar(c); break
        elif op == "6": msg = "🔒 MELI_PRECIOS está BLOQUEADO por seguridad."
        elif op in ("1", "2", "3", "4"):
            k = {"1":"SINCRONIZAR_WOO_STOCK","2":"SINCRONIZAR_WOO_PRECIOS","3":"MODO_TURBO_DELTA","4":"AUDITOR_MELI","6":"SINCRONIZAR_MELI_PRECIOS"}[op]
            c[k] = "NO" if str(c.get(k,"SI")).upper()=="SI" else "SI"; guardar(c); msg = f"{k} -> {c[k]} (⚡ Aplicado en vivo)"
        elif op == "5":
            nv = "NO" if str(c.get("SINCRONIZAR_MELI_STOCK","NO")).upper()=="SI" else "SI"
            c["SINCRONIZAR_MELI_STOCK"] = nv
            if nv == "SI": c["MLC_PILOTO_PRUEBA"] = "NINGUNO"
            guardar(c); os.system("nohup python3 ~/nivelar_meli_vivo.py >/dev/null 2>&1 &") if nv=="SI" else None; msg = f"MELI_STOCK -> {nv} (⚡ Nivelando las 782 publicaciones en 2do plano...)" if nv=="SI" else "MELI_STOCK -> NO (Autoguardado)"
        elif op == "7":
            v = input("Nuevo % de Colchón (ej. 50): ").strip()
            if v.isdigit():
                c["PORCENTAJE_COLCHON"] = int(v); guardar(c)
                if str(c.get("SINCRONIZAR_MELI_STOCK","NO")).upper()=="SI": os.system("nohup python3 ~/nivelar_meli_vivo.py >/dev/null 2>&1 &")
                msg = f"PORCENTAJE_COLCHON -> {v}% (⚡ Nivelando todo el catálogo al {v}% en 2do plano...)"
        elif op == "8":
            cf_act = int(c.get("LIMITE_CORTAFUEGOS", 40) or 0)
            v = input(f"👉 Presiona [Enter] para {'🔓 APAGAR (Pase Libre)' if cf_act > 0 else '🛡️ ENCENDER (40%)'} | O escribe % (ej. 40): ").strip().upper()
            if v == "" or v in ("NO", "OFF", "SI", "ON"):
                nuevo_cf = 0 if (cf_act > 0 and v not in ("SI", "ON")) else 40
                c["LIMITE_CORTAFUEGOS"] = nuevo_cf; guardar(c)
                msg = f"CORTAFUEGOS -> {'🔓 OFF (Pase Libre de precios)' if nuevo_cf == 0 else f'🛡️ ON ({nuevo_cf}%)'} (⚡ Aplicado en vivo)"
            elif v.isdigit():
                c["LIMITE_CORTAFUEGOS"] = int(v); guardar(c)
                msg = f"CORTAFUEGOS -> {'🔓 OFF (Pase Libre)' if int(v)==0 else f'🛡️ ON ({v}%)'} (⚡ Aplicado en vivo)"
        elif op == "9":
            import laboratorio_meli; laboratorio_meli.abrir(c, guardar); c = cargar()
        elif op == "10":
            if input("¿Tomar NUEVA foto? (SI/NO): ").strip().upper()=="SI":
                import respaldo_meli; respaldo_meli.crear_respaldo(); input("\nEnter para volver...")
        elif op == "11":
            if input("¿APAGAR MELI_STOCK y restaurar foto original? (SI/NO): ").strip().upper()=="SI":
                import respaldo_meli; respaldo_meli.restaurar_respaldo(); c = cargar(); input("\nEnter para volver...")
        elif op == "12":
            import lee_config
            rlog = os.path.expanduser("~/historial_erp.log")
            lineas = [l.strip() for l in open(rlog, "r", encoding="utf-8", errors="ignore").readlines() if l.strip()] if os.path.exists(rlog) else []
            lineas.reverse()
            import shutil; por_pag = max(20, shutil.get_terminal_size((126, 70)).lines - 7)
            tot_pag = max(1, (len(lineas) + por_pag - 1) // por_pag)
            pag = 1
            while True:
                os.system("clear")
                print("="*92)
                print(f"📜  BITÁCORA DE CAMBIOS — PÁGINA {pag} DE {tot_pag} (Total registrados: {len(lineas)})")
                print("="*92)
                ini = (pag - 1) * por_pag
                for _idx, _l in enumerate(lineas[ini:ini + por_pag], ini + 1):
                    print(lee_config.fmt_bitacora(_l, _idx))
                print("="*92)
                nav = input(f"👉 [Enter/S] Siguiente hoja | [A] Hoja anterior | [0] Volver al panel: ").strip().upper()
                if nav == "0": break
                elif nav == "A": pag = max(1, pag - 1)
                else:
                    if pag < tot_pag: pag += 1
                    else: break
        elif op == "13":
            import respaldar_sistema; respaldar_sistema.empaquetar_y_subir(); input("\nEnter para volver...")
        elif op == "16":
            import exportar_radiografia; exportar_radiografia.generar_y_subir(); input("\nEnter para volver...")
        elif op == "17":
            import comparador_omnicanal; comparador_omnicanal.abrir_comparador()
        elif op == "18":
            import radar_vivo; radar_vivo.abrir_radar_completo()
        elif op == "19":
            import pistola_pos; pistola_pos.abrir_pistola()
        elif op == "20":
            import monitor_detenidas; monitor_detenidas.abrir_monitor_detenidas()
        elif op == "15":
            print("\n📧 Enviando reporte completo a tu Gmail..."); os.system("python3 ~/enviar_correo.py --forzar"); input("\nEnter para volver...")
        elif op == "14":
            guardar(c); os.system("python3 ~/marcha_rapida_delta.py --una-vez && python3 ~/auditor_meli.py"); input("\nEnter para volver...")

if __name__ == "__main__": menu()
