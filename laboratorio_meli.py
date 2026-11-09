import os, json, requests, pandas as pd
import conectar_meli, lee_config

RX, RB = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx"), os.path.expanduser("~/respaldo_meli_original.json")

def abrir(cfg, guardar_fn):
    tok = conectar_meli.obtener_token_valido()
    hdr = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    df = pd.read_excel(RX) if os.path.exists(RX) else pd.DataFrame()
    bak = json.load(open(RB, "r", encoding="utf-8")).get("items", {}) if os.path.exists(RB) else {}
    sugs = []
    if not df.empty:
        cm = [c for c in df.columns if "Meta ML" in c or "50%" in c or "Colch" in c][0]
        cp = [c for c in df.columns if "Publicado Hoy" in c][0]
        cb = [c for c in df.columns if "Stock Real" in c or "Bodega" in c][0]
        for _, r in df.iterrows():
            m = str(r.get("Código ML (Ver Web)", "")).strip().upper()
            n = str(r.get("Nombre en Mercado Libre", "")).strip()
            if not m.startswith("MLC") or "Sin Pareja" in str(r.get("Estado", "")): continue
            pm, mm, bx = int(float(r.get(cp,0) or 0)), int(float(r.get(cm,0) or 0)), int(float(r.get(cb,0) or 0))
            if mm > 1 and pm != mm: sugs.append((m, n, bx, pm, mm))
            pass
        import random; random.shuffle(sugs); sugs = sugs[:6]

    while True:
        os.system("clear")
        print("="*90+"\n🧪 LABORATORIO DE PRUEBAS EN VIVO (OPCION [9] - TESTEO INSTANTÁNEO)\n"+"="*90)
        print("📋 SUGERENCIAS DE TU CATÁLOGO LISTAS PARA PROBAR CON 1 TECLA:")
        for i, (m, n, bx, pm, mm) in enumerate(sugs, 1):
            print(f" [{i}] {m:<14} | {n[:36]:<36} | Bodega:{bx:>3} | Hoy ML:{pm:>2} ➔ Meta 50%:{mm:>2}")
        print("-"*90)
        print(" [R] 🎲 Sacar 6 sugerencias nuevas al azar | O escribe directo una palabra para buscar (ej. refractometro, portabroca, fresa, taladro)")
        print(" [0] 🔙 Volver al Panel Principal\n"+"="*90)
        op = input("\n👉 Elige una sugerencia (1-6), escribe [B] para buscar, o pega un MLC (0 salir): ").strip().upper()
        if op in ("0", ""):
            cfg["MLC_PILOTO_PRUEBA"] = "NINGUNO"; guardar_fn(cfg); break
        msel, msug, bsug = None, None, None
        if op.isdigit() and 1 <= int(op) <= len(sugs):
            msel, _, bsug, _, msug = sugs[int(op)-1]
        elif op == "R":
            import laboratorio_meli; return laboratorio_meli.abrir(cfg, guardar_fn)
        elif not df.empty and not op.startswith("MLC"):
            pal = input("🔎 Palabra a buscar: ").strip() if op == "B" else op
            if pal:
                sub = df[df["Nombre en Mercado Libre"].str.contains(pal, case=False, na=False)].head(8)
                for _, r in sub.iterrows():
                    print(f"  👉 {r['Código ML (Ver Web)']} | {str(r['Nombre en Mercado Libre'])[:42]} | Hoy ML:{int(float(r[cp] or 0))} ➔ Meta:{int(float(r[cm] or 0))}")
                mi = input("\nEscribe el código MLC a abrir: ").strip().upper()
                if mi.startswith("MLC"): msel = mi
        elif op.startswith("MLC"): msel = op
        if not msel: continue
        if msug is None and not df.empty:
            fl = df[df["Código ML (Ver Web)"].astype(str).str.upper() == msel]
            msug = int(float(fl.iloc[0].get(cm,1) or 1)) if not fl.empty else 1
            bsug = int(float(fl.iloc[0].get(cb,0) or 0)) if not fl.empty else 0

        while True:
            os.system("clear")
            res = requests.get(f"https://api.mercadolibre.com/items/{msel}", headers=hdr, timeout=10).json()
            qv, sv = int(res.get("available_quantity",0)), str(res.get("status",""))
            lnk = res.get("permalink", f"https://articulo.mercadolibre.cl/{msel[:3]}-{msel[3:]}-_JM")
            oi = bak.get(msel, {"available_quantity": qv, "status": sv})
            qo, so = int(oi.get("available_quantity", qv)), str(oi.get("status", sv))
            print("="*90+f"\n🎯 PRODUCTO EN VIVO: {msel} - {res.get('title','')}\n"+"="*90)
            print(f" 📦 Stock EN VIVO hoy en Mercado Libre : {qv} unidades (Estado: {sv})")
            print(f" 🏭 Stock en tu Bodega Excel           : {bsug} unidades  ➔  Meta Colchón 50%: {msug} unidades")
            print(f" 📸 Foto Original Guardada [10]        : {qo} unidades (Estado: {so})")
            print(f" 🔗 LINK DIRECTO REAL (Haz Ctrl+Clic aquí para abrirlo en tu navegador):\n    {lnk}")
            print("-"*90)
            print(f" [1] 🚀 SUBIR A META 50% ({msug} uds) EN VIVO AHORA")
            print(" [2] ✏️  ESCRIBIR OTRA CANTIDAD MANUAL DE PRUEBA (ej. poner 2, 3 o 4 uds)")
            print(f" [3] ⏪ RESTAURAR AL VALOR ORIGINAL DE LA FOTO ({qo} uds / {so})")
            print(" [0] 🔙 Elegir otro producto / Volver\n"+"="*90)
            ac = input("\n👉 ¿Qué hacemos en vivo? (1/2/3/0): ").strip()
            if ac in ("0", ""): break
            elif ac in ("1", "2"):
                qn = msug if ac == "1" else int(input("Cantidad a publicar ahora (ej. 2, 3): ").strip() or "0")
                if qn > 0:
                    r = requests.put(f"https://api.mercadolibre.com/items/{msel}", headers=hdr, json={"available_quantity": qn}, timeout=10)
                    if r.status_code in (200,201):
                        lee_config.registrar_evento("MELI-TEST", msel, res.get("title",""), f"{qv} uds -> {qn} uds")
                        print(f"\n✅ ¡LISTO EN 1 SEGUNDO! Pasó de {qv} a {qn} uds en ML. Abre o recarga (F5) el Link de arriba.")
                    else: print(f"\n⚠️ Aviso API ML ({r.status_code}): {r.text[:120]}")
                input("\nPresiona Enter para refrescar lectura en vivo...")
            elif ac == "3":
                pl = {"available_quantity": qo} if qo > 0 else {"status": so}
                r = requests.put(f"https://api.mercadolibre.com/items/{msel}", headers=hdr, json=pl, timeout=10)
                if r.status_code in (200,201):
                    lee_config.registrar_evento("MELI-RESTORE", msel, res.get("title",""), f"{qv} uds -> {qo} uds (Original)")
                    print(f"\n⏪ ¡RESTAURADO! Volvió a {qo} uds ({so}).")
                input("\nPresiona Enter para refrescar lectura en vivo...")
