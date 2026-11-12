import os, json, time, py_compile, dropbox
from concurrent.futures import ThreadPoolExecutor
from woocommerce import API

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

pa = os.path.expanduser("~/autolinker_web.py")
if os.path.exists(pa):
    ta = open(pa, "r", encoding="utf-8").read()
    ta = ta.replace('up = jload(guardar_bak_html(pid, nom, dl); wc.put(f"products/{pid}", {"description": nuevo_dl}))', 'guardar_bak_html(pid, nom, dl); up = jload(wc.put(f"products/{pid}", {"description": nuevo_dl}))')
    open(pa, "w", encoding="utf-8").write(ta)
    py_compile.compile(pa, doraise=True)
    print("✅ autolinker_web.py reparado.")

def jload(r):
    t = (r.text or "").replace("\ufeff", "").strip()
    return json.loads(t) if t else []

def exportar_catalogo_html():
    t0 = time.time()
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    CK, CS = env["WOO_KEY"], env["WOO_SECRET"]
    print("\n📦 Descargando HTML y CSS de todos los productos de insumaes.cl (5 hilos)...", flush=True)

    def bajar_pag(pag):
        wc = API(url="https://www.insumaes.cl/", consumer_key=CK, consumer_secret=CS, version="wc/v3", timeout=60)
        for _ in range(3):
            try:
                r = wc.get("products", params={"per_page": 100, "page": pag})
                if r.status_code == 200:
                    d = jload(r)
                    return d if isinstance(d, list) else []
            except Exception: time.sleep(1)
        return []

    todos, pag = [], 1
    while True:
        lotes = list(ThreadPoolExecutor(max_workers=5).map(bajar_pag, range(pag, pag + 5)))
        fin = False
        for i, lt in enumerate(lotes):
            if not lt: fin = True; break
            todos.extend(lt)
            print(f"   -> Página {pag + i} descargada ({len(todos)} productos)...", flush=True)
            if len(lt) < 100: fin = True; break
        if fin: break
        pag += 5

    todos.sort(key=lambda x: int(x.get("id", 0)))
    partes = ["="*80, f"RADIOGRAFIA COMPLETA HTML + CSS WOOCOMMERCE (INSUMAES.CL) - {time.strftime('%Y-%m-%d %H:%M:%S')}", f"Total Productos Respaldados: {len(todos)}", "="*80 + "\n"]
    dic = {}
    for p in todos:
        pid, sku, nom = p.get("id"), p.get("sku", "") or "---", p.get("name", "") or "---"
        pr, st, url = p.get("regular_price", "") or p.get("price", "0"), p.get("stock_quantity", 0), p.get("permalink", "")
        cats = " | ".join(c.get("name", "") for c in (p.get("categories") or []))
        fotos = " | ".join(im.get("src", "") for im in (p.get("images") or []))
        dc, dl = (p.get("short_description") or "").strip(), (p.get("description") or "").strip()
        dic[str(pid)] = {"id": pid, "sku": sku, "name": nom, "price": pr, "stock": st, "url": url, "short_description": dc, "description": dl}
        partes.append(f"\n{'#'*80}\n### ID_WOO: {pid} | SKU: {sku} | NOMBRE: {nom}\n### PRECIO: ${pr} | STOCK: {st} | CATEGORIAS: {cats}\n### URL: {url}\n### FOTOS: {fotos}\n{'#'*80}\n--- [HTML_DESCRIPCION_CORTA] ---\n{dc}\n\n--- [HTML_Y_CSS_DESCRIPCION_LARGA] ---\n{dl}\n")

    txt_out = "\n".join(partes)
    open(os.path.expanduser("~/RADIOGRAFIA_CATALOGO_HTML_WOO.txt"), "w", encoding="utf-8").write(txt_out)
    json.dump(dic, open(os.path.expanduser("~/respaldo_html_completo_woo.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    dbx = dropbox.Dropbox(app_key=env["DROPBOX_APP_KEY"], app_secret=env["DROPBOX_APP_SECRET"], oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"])
    dbx.files_upload(txt_out.encode("utf-8"), "/RADIOGRAFIA_CATALOGO_HTML_WOO.txt", mode=dropbox.files.WriteMode.overwrite)
    print(f"\n✅ ¡LISTO EN {time.time()-t0:.1f}s! {len(todos)} productos con su HTML y CSS respaldados en:")
    print("   1) ☁️ Raíz de tu Dropbox: /RADIOGRAFIA_CATALOGO_HTML_WOO.txt")
    print("   2) 🛡️ Bóveda Local JSON : ~/respaldo_html_completo_woo.json\n", flush=True)

if __name__ == "__main__":
    exportar_catalogo_html()
