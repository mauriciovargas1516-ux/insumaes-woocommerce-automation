import os, re, time, json, dropbox, pandas as pd
from collections import defaultdict
from woocommerce import API

def jload(r):
    t = (r.text or "").replace("\ufeff", "").strip()
    return json.loads(t) if t else {}

def conectar_woo():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    return API(url="https://www.insumaes.cl/", consumer_key=env["WOO_KEY"], consumer_secret=env["WOO_SECRET"], version="wc/v3", timeout=45), env

def mapa_y_constructor_categorias(crear=True):
    wc, _ = conectar_woo()
    print("\n📡 Descargando mapa multinivel de categorías desde insumaes.cl...", flush=True)
    cats, pag = {}, 1
    while True:
        res = jload(wc.get("products/categories", params={"per_page": 100, "page": pag}))
        if not res or not isinstance(res, list) or "code" in res: break
        for c in res: cats[c["id"]] = c
        if len(res) < 100: break
        pag += 1
    arbol = defaultdict(list)
    for c in cats.values(): arbol[c["parent"]].append(c)
    def dibujar(pid, niv=0):
        for c in sorted(arbol[pid], key=lambda x: x["name"]):
            pref = "📁 " if niv == 0 else ("   " * niv + "└── 📄 ")
            print(f"{pref}{c['name']} (ID: {c['id']} | {c.get('count', 0)} prods)")
            dibujar(c["id"], niv + 1)
    print("\n" + "=" * 80 + "\n 🌲 MAPA COMPLETO Y MULTINIVEL DE CATEGORÍAS EN INSUMAES.CL\n" + "=" * 80)
    dibujar(0)
    print("=" * 80)
    if crear:
        while True:
            nom = input("\n📝 Nombre de NUEVA categoría a crear (o Enter para salir): ").strip()
            if not nom: break
            pad = input("👉 ID de la Categoría Padre (escribe 0 si es Principal): ").strip()
            pid = int(pad) if pad.isdigit() else 0
            r = jload(wc.post("products/categories", {"name": nom, "parent": pid}))
            print(f"✅ ¡Creada con éxito! ID: {r.get('id')} ({r.get('name')})" if "id" in r else f"❌ Error: {r}")
    return cats

def reasignador_omni_buscador():
    wc, _ = conectar_woo()
    mapa_y_constructor_categorias(crear=False)
    print("\n💡 Tip: Ingresa IDs_WOO, SKUs o Nombres separados por barra vertical (|). Ej: SKU1 | SKU2")
    items_str = input("📦 Productos a mover de categoría (Enter para cancelar): ").strip()
    if not items_str: return
    cat_dest = input("👉 ID de la NUEVA categoría (Destino) para todo el lote: ").strip()
    if not cat_dest.isdigit(): return
    cid, lista = int(cat_dest), [x.strip() for x in items_str.split("|") if x.strip()]
    for i, it in enumerate(lista, 1):
        pid, nom_ok = (int(it), it) if it.isdigit() else (None, "")
        if not pid:
            rs = jload(wc.get("products", params={"sku": it}))
            if isinstance(rs, list) and rs: pid, nom_ok = rs[0]["id"], rs[0]["name"]
            else:
                for p in (jload(wc.get("products", params={"search": it})) or []):
                    if isinstance(p, dict) and p.get("name", "").strip().upper() == it.upper():
                        pid, nom_ok = p["id"], p["name"]; break
        if pid:
            u = jload(wc.put(f"products/{pid}", {"categories": [{"id": cid}]}))
            print(f"  ✅ [{i}/{len(lista)}] Movido a Categoría {cid}: [{pid}] {u.get('name', nom_ok)}")
        else: print(f"  ❌ [{i}/{len(lista)}] No se encontró '{it}'.")

def editor_textos_html_lote():
    wc, _ = conectar_woo()
    print("\n" + "=" * 80 + "\n ✏️ EDITOR DE TEXTOS Y FICHAS HTML POR LOTE (SIN PERDER FOTOS NI DISEÑO)\n" + "=" * 80)
    ids_str = input("🔎 Ingresa los ID_WOO separados por coma (ej: 14501, 14499, 14500): ").strip()
    if not ids_str: return
    modo = input("👉 [1] Buscar y Reemplazar una frase | [2] Agregar una nota al final de la ficha: ").strip()
    ids = [x.strip() for x in ids_str.split(",") if x.strip().isdigit()]
    if modo == "1":
        buscar = input("📝 Frase exacta que quieres BUSCAR: ").strip()
        reemplazar = input("✨ Frase NUEVA por la que quieres REEMPLAZARLA: ").strip()
        if not buscar: return
        for pid in ids:
            p = jload(wc.get(f"products/{pid}"))
            dl = p.get("description", "") or ""
            if buscar in dl:
                wc.put(f"products/{pid}", {"description": dl.replace(buscar, reemplazar)})
                print(f"  ✅ [ID:{pid}] {p.get('name')} -> ¡Texto reemplazado con éxito!")
            else: print(f"  ⚠️ [ID:{pid}] No contenía la frase '{buscar}'.")
    elif modo == "2":
        nota = input("📝 Escribe la nota o compatibilidad que quieres agregar al final: ").strip()
        if not nota: return
        for pid in ids:
            p = jload(wc.get(f"products/{pid}"))
            dl = p.get("description", "") or ""
            wc.put(f"products/{pid}", {"description": dl + f"\n<p><strong>• Nota Técnica:</strong> {nota}</p>"})
            print(f"  ✅ [ID:{pid}] {p.get('name')} -> ¡Nota agregada!")

def mostrar_ayuda_suite():
    os.system("clear")
    print("=" * 92 + "\n 📖 GUÍA RÁPIDA DE LA SUITE INSUMAES CLOUD (¿QUÉ HACE CADA HERRAMIENTA?)\n" + "=" * 92)
    guia = [
        ("1. 📸 Estandarizador Inteligente de Fotos", "Achica y encuadra las fotos que se ven gigantes o alargadas en la web (a 800x720 px) sin deformarlas. Puedes elegir aplicarlo a 1 ID, a una Categoría entera o a toda la Web."),
        ("2. 🔗 Auto-Linker de Venta Cruzada", "Lee la Caja Amarilla de tus productos y agrega botones azules clicables hacia el inserto o portaherramientas compatible para que el cliente lo sume al carrito."),
        ("3. ✏️  Editor de Textos HTML por Lote", "Permite buscar y reemplazar una palabra o agregar una nota técnica en varios productos al mismo tiempo sin tocar sus fotos ni sus tablas."),
        ("4. 🏗️  Constructor Interactivo de Categorías", "Dibuja el árbol completo de categorías y subcategorías de insumaes.cl con sus IDs y te permite crear categorías nuevas sin entrar a WordPress."),
        ("5. 🚚 Reasignador Definitivo de Categorías", "Mueve rápidamente un grupo de productos (ingresando SKU1 | SKU2 | ID) hacia una nueva categoría destino."),
        ("6. 💾 Extracción Maestra a Dropbox (.TXT)", "Clona las 1.727 fichas HTML, CSS, precios, stocks y links de fotos de tu tienda hacia la raíz de tu Dropbox (/RADIOGRAFIA_CATALOGO_HTML_WOO.txt)."),
        ("7. ⏪ Restaurador de Seguridad (Ctrl+Z)", "Tu seguro de vida: devuelve el texto HTML o la foto de 1 producto (o de todos) exactamente a como estaba antes.")
    ]
    for tit, desc in guia: print(f"\n {tit}\n    👉 {desc}")
    print("\n" + "=" * 92)
    input("\nPresiona Enter para volver al menú...")

def abrir_suite():
    import estandarizador_fotos_woo
    while True:
        os.system("clear")
        f_bak = os.path.expanduser("~/respaldo_html_completo_woo.json")
        n_bak = len(json.load(open(f_bak, "r", encoding="utf-8"))) if os.path.exists(f_bak) else 0
        print("=" * 96)
        print("🛠️  SUITE MAESTRA INSUMAES CLOUD — MENÚ DE HERRAMIENTAS DE CATÁLOGO (BOTÓN [22])")
        print(f"🛡️  Respaldo Activo : ✅ {n_bak} productos blindados en Bóveda Local y en tu Dropbox")
        print("=" * 96)
        print("  1. 📸 Estandarizador Inteligente de Fotos   | Ajusta tamaño de fotos por ID, Categoría o Web")
        print("  2. 🔗 Auto-Linker de Venta Cruzada (Botones)| Conecta Portas <-> Insertos en Cajas Amarillas")
        print("  3. ✏️  Editor de Textos HTML por Lote        | Busca/reemplaza textos técnicos en varios IDs")
        print("  4. 🏗️  Constructor Interactivo de Categorías | Ver mapa de categorías de la web o crear nuevas")
        print("  5. 🚚 Reasignador Definitivo (Categorías)   | Mover lote de productos (SKU1 | SKU2) de categoría")
        print("  6. 💾 Extracción Maestra Web a Dropbox      | Guarda todo el HTML y Fotos en Dropbox (.TXT)")
        print("  7. ⏪ Restaurador de Seguridad (Ctrl+Z)     | Devuelve HTML o Fotos al estado original")
        print("  8. ℹ️  Ayuda (¿Qué hace cada herramienta?)   | Guía explicada en simple de cada opción (1-7)")
        print("  0. 🔙 Volver al Panel Principal")
        print("=" * 96)
        op = input("\n👉 Selecciona la herramienta que deseas usar (0-8): ").strip()
        if op == "0": break
        elif op == "1": estandarizador_fotos_woo.menu_fotos()
        elif op == "2": os.system("python3 -u ~/autolinker_web.py"); input("\nEnter para volver...")
        elif op == "3": editor_textos_html_lote(); input("\nEnter para volver...")
        elif op == "4": mapa_y_constructor_categorias(crear=True); input("\nEnter para volver...")
        elif op == "5": reasignador_omni_buscador(); input("\nEnter para volver...")
        elif op == "6": os.system("python3 -u ~/exportar_html_woo.py"); input("\nEnter para volver...")
        elif op == "7":
            sub = input("\n👉 ¿Qué deseas restaurar? [1] HTML de 1 producto | [2] Fotos originales: ").strip()
            if sub == "1":
                pid_in = input("🔎 Escribe el ID_WOO del producto a restaurar (ej. 2979): ").strip()
                datos = json.load(open(f_bak, "r", encoding="utf-8")) if os.path.exists(f_bak) else {}
                if pid_in in datos:
                    wc, _ = conectar_woo()
                    wc.put(f"products/{pid_in}", {"description": datos[pid_in]["description"]})
                    print(f"  ✅ ID:{pid_in} ({datos[pid_in]['name']}) volvió a su HTML original.")
                input("\nEnter para volver...")
            elif sub == "2": estandarizador_fotos_woo.menu_fotos()
        elif op == "8": mostrar_ayuda_suite()

if __name__ == "__main__":
    abrir_suite()
