import os, json, time
from concurrent.futures import ThreadPoolExecutor
from woocommerce import API

RUTA_BAK_PRECIOS = os.path.expanduser("~/respaldo_precios_woo.json")

def jload(r):
    t = (r.text or "").replace("\ufeff", "").strip()
    return json.loads(t) if t else []

def conectar_woo():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    return API(url="https://www.insumaes.cl/", consumer_key=env["WOO_KEY"], consumer_secret=env["WOO_SECRET"], version="wc/v3", timeout=45), env

def redondear_clp(valor, multiplo=100):
    if multiplo <= 1: return int(round(valor))
    return int(round(valor / float(multiplo)) * multiplo)

def guardar_bak_precio(pid, nom, reg_p, sale_p):
    bak = json.load(open(RUTA_BAK_PRECIOS, "r", encoding="utf-8")) if os.path.exists(RUTA_BAK_PRECIOS) else {}
    if str(pid) not in bak:
        bak[str(pid)] = {"name": nom, "regular_price": str(reg_p or ""), "sale_price": str(sale_p or "")}
        json.dump(bak, open(RUTA_BAK_PRECIOS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def aplicar_ajuste_lote(productos, pct, modo_oferta=False, redond=100):
    _, env = conectar_woo()
    CK, CS = env["WOO_KEY"], env["WOO_SECRET"]
    cambios = []
    for p in productos:
        pid, nom = p["id"], p.get("name", "")
        reg_str = str(p.get("regular_price") or p.get("price") or "0").strip()
        sale_str = str(p.get("sale_price") or "").strip()
        try: p_base = float(reg_str)
        except Exception: continue
        if p_base <= 0: continue
        p_nuevo = max(100, redondear_clp(p_base * (1.0 + (pct / 100.0)), redond))
        cambios.append((pid, nom, int(p_base), p_nuevo, reg_str, sale_str))

    if not cambios:
        print("\n⚠️ No se encontraron productos con precio válido en la selección.")
        return

    print("\n" + "=" * 92)
    print(f"🔎 VISTA PREVIA DE SIMULACIÓN ({len(cambios)} productos | Ajuste: {pct:+.1f}% | Redondeo: ${redond})")
    print("=" * 92)
    for pid, nom, p_ant, p_nue, _, _ in cambios[:12]:
        etq = f"Tachado ${p_ant:,} -> OFERTA ${p_nue:,}" if modo_oferta else f"${p_ant:,} -> ${p_nue:,}"
        print(f"  • ID:{pid:<6} | {nom[:42]:<42} | {etq}".replace(",", "."))
    if len(cambios) > 12:
        print(f"  ... y {len(cambios) - 12} productos más.")
    print("=" * 92)
    conf = input("\n👉 ¿Confirmas aplicar este cambio en insumaes.cl? (SI/NO): ").strip().upper()
    if conf != "SI":
        print("🛑 Operación cancelada. Ningún precio fue modificado.")
        return

    for pid, nom, _, _, r_s, s_s in cambios:
        guardar_bak_precio(pid, nom, r_s, s_s)

    def _subir(item):
        i, (pid, nom, p_ant, p_nue, _, _) = item
        w = API(url="https://www.insumaes.cl/", consumer_key=CK, consumer_secret=CS, version="wc/v3", timeout=45)
        payload = {"sale_price": str(p_nue)} if modo_oferta else {"regular_price": str(p_nue), "sale_price": ""}
        r = w.put(f"products/{pid}", payload)
        return f"  ✅ [{i:03d}/{len(cambios)}] ID:{pid:<6} | {nom[:36]:<36} | ${p_ant:,} -> ${p_nue:,}".replace(",", ".") if r.status_code in (200, 201) else f"  ⚠️ ID:{pid} HTTP {r.status_code}"

    with ThreadPoolExecutor(max_workers=3) as ex:
        for m in ex.map(_subir, enumerate(cambios, 1)): print(m, flush=True)
    print(f"\n🏁 ¡Ajuste completado en {len(cambios)} productos! (Respaldo Ctrl+Z guardado).")

def menu_precios():
    while True:
        os.system("clear")
        n_bak = len(json.load(open(RUTA_BAK_PRECIOS, "r", encoding="utf-8"))) if os.path.exists(RUTA_BAK_PRECIOS) else 0
        print("=" * 96)
        print("💹  BOTÓN [25]: AJUSTADOR MASIVO DE PRECIOS POR % (CATEGORÍAS, OFERTAS TACHADAS Y CTRL+Z)")
        print(f"🛡️  Bóveda Precios Originales : ✅ {n_bak} productos con respaldo en ~/respaldo_precios_woo.json")
        print("=" * 96)
        print("  [1] 📁 Subir o Bajar % de Precios en UNA o VARIAS Categorías (Precio normal o Precio Oferta)")
        print("  [2] 🎯 Subir o Bajar % de Precios en un Lote de ID_WOO específicos (ej: 14499, 14500)")
        print("  [3] 🏷️  Quitar Ofertas Tachadas (Borrar sale_price y volver al precio normal en una Categoría)")
        print("  [4] ⏪ Botón Ctrl+Z de Precios (Restaurar los precios originales antes del ajuste)")
        print("  [0] 🔙 Volver al Panel Principal")
        print("=" * 96)
        op = input("\n👉 Selecciona una opción (0-4): ").strip()
        if op == "0": break
        elif op in ("1", "3"):
            wc, _ = conectar_woo()
            cats, pag = [], 1
            while True:
                lt = jload(wc.get("products/categories", params={"per_page": 100, "page": pag}))
                if not lt or not isinstance(lt, list): break
                cats.extend(lt)
                if len(lt) < 100: break
                pag += 1
            cats.sort(key=lambda x: x.get("name", ""))
            filtro = input("\n🔎 Escribe parte del nombre de la categoría (o Enter para ver todas): ").strip().upper()
            for c in cats:
                if not filtro or filtro in c.get("name", "").upper():
                    print(f"  ID_CAT: {c['id']:<5} | {c['name']:<45} ({c.get('count',0)} prods)")
            c_in = input("\n👉 Escribe uno o varios ID_CAT separados por coma (ej: 33, 45): ").strip()
            c_ids = [x.strip() for x in c_in.split(",") if x.strip().isdigit()]
            if not c_ids: continue
            prods = []
            for cid in c_ids:
                p_pag = 1
                while True:
                    p_lt = jload(wc.get("products", params={"category": cid, "per_page": 100, "page": p_pag}))
                    if not p_lt or not isinstance(p_lt, list): break
                    prods.extend(p_lt)
                    if len(p_lt) < 100: break
                    p_pag += 1
            unicos = list({p["id"]: p for p in prods}.values())
            if op == "3":
                for p in unicos:
                    wc.put(f"products/{p['id']}", {"sale_price": ""})
                    print(f"  ✅ ID:{p['id']} ({p.get('name','')[:40]}) -> Oferta eliminada.")
                input("\nPresiona Enter para continuar..."); continue
            pct = float(input("📈 Porcentaje a aplicar (ej: 10 para +10%, o -15 para -15%): ").strip().replace(",", ".") or "0")
            modo_of = (input("🏷️  [1] Cambiar Precio Regular | [2] Crear Precio Oferta Tachado: ").strip() == "2")
            if pct != 0: aplicar_ajuste_lote(unicos, pct, modo_oferta=modo_of, redond=100)
            input("\nPresiona Enter para continuar...")
        elif op == "2":
            wc, _ = conectar_woo()
            s = input("🔎 IDs_WOO separados por coma: ").strip()
            ids = [x.strip() for x in s.split(",") if x.strip().isdigit()]
            prods = [jload(wc.get(f"products/{i}")) for i in ids]
            prods = [p for p in prods if isinstance(p, dict) and "id" in p]
            pct = float(input("📈 Porcentaje (ej: 10 o -15): ").strip().replace(",", ".") or "0")
            modo_of = (input("🏷️  [1] Precio Regular | [2] Oferta Tachada: ").strip() == "2")
            if prods and pct != 0: aplicar_ajuste_lote(prods, pct, modo_oferta=modo_of, redond=100)
            input("\nPresiona Enter para continuar...")
        elif op == "4":
            if not os.path.exists(RUTA_BAK_PRECIOS): print("\n⚠️ Aún no hay respaldos."); input("\nEnter..."); continue
            wc, _ = conectar_woo()
            bak = json.load(open(RUTA_BAK_PRECIOS, "r", encoding="utf-8"))
            for pid, d in bak.items():
                wc.put(f"products/{pid}", {"regular_price": d["regular_price"], "sale_price": d["sale_price"]})
                print(f"  ⏪ ID:{pid} ({d['name'][:40]}) restaurado a ${d['regular_price']}.")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    menu_precios()
