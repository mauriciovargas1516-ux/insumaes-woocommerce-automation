import os, re, math, json, pandas as pd
import lee_config

def leer_movs():
    p_log, p_dlog = os.path.expanduser("~/historial_erp.log"), os.path.expanduser("~/delta.log")
    act, ago, movs, va, vg, vm = [], [], [], set(), set(), set()
    if os.path.exists(p_log):
        for l in reversed(open(p_log, "r", encoding="utf-8", errors="ignore").readlines()):
            if "RESTORE" in l: continue
            m = re.match(r"^\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$", l.strip())
            if not m: continue
            f, t, cod, nom, det = m.groups()
            dc = re.sub(r"\s*\[\d+\.\d+s\]", "", det).replace("->", "➔").strip()
            ns = re.findall(r"(\d+)\s*uds", dc)
            can = "🛒 Web insumaes.cl" if "WOO" in t else ("🔫 Pistola POS" if "POS" in t else "💛 Mercado Libre")
            if len(ns) >= 2:
                a, b = int(ns[0]), int(ns[1])
                if a == b and "PAUSA" not in t and "paused" not in dc: continue
                if ("paused" in dc.split("➔")[-1] or b == 0) and a > 0 and (cod, nom) not in vg:
                    vg.add((cod, nom)); ago.append((f, can, cod, nom, f"Tenía {a} u ➔ Quedó en 0 u (Pausado)"))
                elif a == 0 and b > 0 and (cod, nom) not in va:
                    va.add((cod, nom)); act.append((f, can, cod, nom, f"Estaba en 0 ➔ Subió a {b} u (Activado)"))
                elif a > 0 and b > 0 and a != b and (f[:16], cod, nom) not in vm:
                    vm.add((f[:16], cod, nom)); d = b - a
                    movs.append((f, can, cod, nom, f"🟢 Subió +{d} u ({a} ➔ {b} u)" if d > 0 else f"🔴 Bajó {d} u ({a} ➔ {b} u)"))
    if os.path.exists(p_dlog):
        hr = "Reciente"
        for l in open(p_dlog, "r", encoding="utf-8", errors="ignore").readlines():
            mh = re.search(r"\[(\d{2}:\d{2}:\d{2}) Chile\]", l)
            if mh: hr = f"Hora {mh.group(1)}"
            mw = re.search(r"\[WOO STOCK .*?\]\s*(.*?)\s*\((ID:[\d\-]+)\):\s*(\d+)\s*➔\s*(\d+)\s*uds", l)
            if mw:
                nom, wid, a, b = mw.group(1).strip(), mw.group(2), int(mw.group(3)), int(mw.group(4))
                if a == 0 and b > 0 and (wid, nom) not in va:
                    va.add((wid, nom)); act.append((hr, "🛒 Web insumaes.cl", wid, nom, f"Estaba en 0 ➔ Subió a {b} u (Activado)"))
                elif a > 0 and b == 0 and (wid, nom) not in vg:
                    vg.add((wid, nom)); ago.append((hr, "🛒 Web insumaes.cl", wid, nom, f"Tenía {a} u ➔ Quedó en 0 u (Agotado)"))
    return act, ago, movs

def abrir_monitor_detenidas():
    p_ml, p_am, p_mem = [os.path.expanduser(x) for x in ("~/meli_api_items_full.json", "~/AUDITORIA_MELI_INSUMAES.xlsx", "~/estado_stocks_delta.json")]
    vista = "TODO"
    while True:
        os.system("clear")
        act, ago, movs = leer_movs()
        info_ml = json.load(open(p_ml, "r", encoding="utf-8")) if os.path.exists(p_ml) else {}
        mem_d = json.load(open(p_mem, "r", encoding="utf-8")) if os.path.exists(p_mem) else {}
        df_m = pd.read_excel(p_am) if os.path.exists(p_am) else pd.DataFrame()

        ago_ml, pel_ml = [], []
        for _, rm in df_m.iterrows():
            mlc = str(rm.get("Código ML (Ver Web)", "")).strip()
            if not mlc.startswith("MLC") or "Sin Pareja" in str(rm.get("Estado", "")): continue
            nex = str(rm.get("Nombre en tu Excel (Ir a Celda)", "") if pd.notna(rm.get("Nombre en tu Excel (Ir a Celda)")) else "").strip()
            upk = max(1, int(float(rm.get("Unid. x Pack", 1) or 1))) if pd.notna(rm.get("Unid. x Pack")) else 1
            kn = re.sub(r'\b(\d+)\s*LTS?\b', r'\1L', nex.upper()).strip()
            bod = int(mem_d[kn]["s"]) if (kn in mem_d and isinstance(mem_d[kn], dict) and "s" in mem_d[kn]) else (int(float(rm.get("Stock Bodega", 0) or 0)) if pd.notna(rm.get("Stock Bodega")) else 0)
            pks = bod // upk
            mml = 0 if pks <= 0 else (1 if pks == 1 else int(math.floor(pks * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0) + 0.5)))
            st_a, q_a = info_ml.get(mlc, {}).get("status", "active"), int(info_ml.get(mlc, {}).get("qty", 0))
            mot = f"Tienes {bod} u en bodega, pero se vende en Pack de {upk}" if (bod > 0 and pks == 0) else "Tienes 0 u en tu Excel de bodega"
            if st_a == "active" and mml <= 0: pel_ml.append((mlc, nex, bod, q_a, mot))
            elif st_a != "active" and mml <= 0: ago_ml.append((mlc, nex, bod, q_a, mot))

        print("=" * 140)
        print("📋 RESUMEN FÁCIL DE TU INVENTARIO (EN ESPAÑOL SIMPLE: QUÉ REVIVIÓ, QUÉ SE ACABÓ Y QUÉ CAMBIÓ DE CANTIDAD)")
        print(f"   🚀 Volvieron a tener stock: {len(act)} | 🛑 Se quedaron en cero (Pausados): {len(ago)} | 🔄 Cambios normales de cantidad: {len(movs)}")
        print("=" * 140)
        if vista == "TODO":
            print("\n🚀 1. ¿QUÉ REVIVIÓ? (Estaba agotado en 0 y volvió a ponerse a la venta):")
            for f, can, cod, nom, chg in act[:12]:
                print(f"   • {f:<19} | {can:<18} | {chg:<36} | {nom[:44]} ({cod})")
            print("\n🛑 2. ¿QUÉ SE ACABÓ? (Llegó a 0 unidades y se pausó solo por seguridad):")
            for f, can, cod, nom, chg in ago[:12]:
                print(f"   • {f:<19} | {can:<18} | {chg:<36} | {nom[:44]} ({cod})")
            print("\n🔄 3. ¿QUÉ CAMBIÓ DE CANTIDAD? (Últimas subidas y bajadas normales en Mercado Libre y Web):")
            for f, can, cod, nom, chg in movs[:15]:
                print(f"   • {f:<19} | {can:<18} | {chg:<36} | {nom[:44]} ({cod})")
            if pel_ml:
                print(f"\n🚨 4. ¡ATENCIÓN! TIENES {len(pel_ml)} PUBLICACIONES ACTIVAS EN ML SIN STOCK SUFICIENTE (Presiona [P] para pausarlas):")
                for mlc, nex, bod, qa, mot in pel_ml[:5]:
                    print(f"   ⚠️ {mlc:<13} | {nex[:40]:<40} | Publicado en ML: {qa} u | {mot}")
            else:
                print("\n✅ 4. PROTECCIÓN AL 100%: Ninguna publicación agotada está activa hoy en Mercado Libre.")
        else:
            print(f"\n🛑 LISTA DE LAS {len(ago_ml)} PUBLICACIONES PAUSADAS HOY EN MERCADO LIBRE POR FALTA DE STOCK:")
            for idx, (mlc, nex, bod, qa, mot) in enumerate(ago_ml[:60], 1):
                print(f"   {idx:02d}. {mlc:<13} | {nex[:46]:<46} | {mot}")
        print("\n" + "=" * 140)
        print("👉 [Enter/1] Ver las 3 Tablas Juntas | [2] Ver las 19 Pausadas de ML | [P] 🛑 Pausar alertas y encender [5] MELI_STOCK | [0] Volver")
        op = input("👉 Opción: ").strip().upper()
        if op == "0": break
        elif op in ("", "1"): vista = "TODO"
        elif op == "2": vista = "PAUSADOS"
        elif op == "P":
            pc = os.path.expanduser("~/config_bot.json")
            if os.path.exists(pc):
                c = json.load(open(pc, "r", encoding="utf-8")); c["SINCRONIZAR_MELI_STOCK"] = "SI"
                json.dump(c, open(pc, "w", encoding="utf-8"), indent=4)
            import nivelar_meli_vivo; nivelar_meli_vivo.nivelar_ahora(True)
            input("\n✅ ¡Listo! Alertas pausadas en ML y botón [5] encendido en 🟢 SI. Presiona Enter...")

if __name__ == "__main__": abrir_monitor_detenidas()
