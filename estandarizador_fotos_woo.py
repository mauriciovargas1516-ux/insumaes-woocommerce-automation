import os, io, re, sys, time, json, requests, dropbox
from PIL import Image, ImageChops
from woocommerce import API

RUTA_BAK_FOTOS = os.path.expanduser("~/respaldo_fotos_originales_woo.json")

def jload(r):
    t = (r.text or "").replace("\ufeff", "").strip()
    return json.loads(t) if t else {}

def conectar():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    wc = API(url="https://www.insumaes.cl/", consumer_key=env["WOO_KEY"], consumer_secret=env["WOO_SECRET"], version="wc/v3", timeout=60)
    dbx = dropbox.Dropbox(app_key=env["DROPBOX_APP_KEY"], app_secret=env["DROPBOX_APP_SECRET"], oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"])
    return wc, dbx

def guardar_bak_foto(pid, nom, imgs_orig):
    bak = json.load(open(RUTA_BAK_FOTOS, "r", encoding="utf-8")) if os.path.exists(RUTA_BAK_FOTOS) else {}
    if str(pid) not in bak:
        bak[str(pid)] = {"name": nom, "images": [{"id": i.get("id"), "src": i.get("src")} for i in imgs_orig]}
        json.dump(bak, open(RUTA_BAK_FOTOS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def procesar_bytes_cuadrado(raw_bytes, ancho_meta=800, alto_meta=720, forzar=False):
    im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    w, h = im.size
    if not forzar and (0.85 <= (w / max(h, 1)) <= 1.25) and w <= 1000 and h <= 1000:
        return None, (w, h), (w, h)

    if h > w * 1.08:
        l_s = im.crop((0, 0, 1, h)).resize((w, h))
        r_s = im.crop((w - 1, 0, w, h)).resize((w, h))
        bg_ref = Image.blend(l_s, r_s, 0.5)
        diff = ImageChops.difference(im, bg_ref).convert("L")
        bbox = diff.point(lambda p: 255 if p > 24 else 0).getbbox()
        if bbox:
            pad = int(h * 0.05)
            y0, y1 = max(0, bbox[1] - pad), min(h, bbox[3] + pad)
            if (y1 - y0) < h * 0.92:
                im = im.crop((0, y0, w, y1))
                w, h = im.size

    sc = min(ancho_meta / w, alto_meta / h)
    nw, nh = max(1, int(round(w * sc))), max(1, int(round(h * sc)))
    im_r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (ancho_meta, alto_meta), (255, 255, 255))
    ox, oy = (ancho_meta - nw) // 2, (alto_meta - nh) // 2

    if ox > 0:
        canvas.paste(im_r.crop((0, 0, 2, nh)).resize((ox, nh), Image.Resampling.BILINEAR), (0, oy))
        canvas.paste(im_r.crop((nw - 2, 0, nw, nh)).resize((ancho_meta - nw - ox, nh), Image.Resampling.BILINEAR), (ox + nw, oy))
    if oy > 0:
        canvas.paste(im_r.crop((0, 0, nw, 2)).resize((nw, oy), Image.Resampling.BILINEAR), (ox, 0))
        canvas.paste(im_r.crop((0, nh - 2, nw, nh)).resize((nw, alto_meta - nh - oy), Image.Resampling.BILINEAR), (ox, oy + nh))

    if ox > 0 and oy > 0:
        tl, tr = im_r.getpixel((0, 0)), im_r.getpixel((nw - 1, 0))
        bl, br = im_r.getpixel((0, nh - 1)), im_r.getpixel((nw - 1, nh - 1))
        canvas.paste(Image.new("RGB", (ox, oy), tl), (0, 0))
        canvas.paste(Image.new("RGB", (ancho_meta - nw - ox, oy), tr), (ox + nw, 0))
        canvas.paste(Image.new("RGB", (ox, alto_meta - nh - oy), bl), (0, oy + nh))
        canvas.paste(Image.new("RGB", (ancho_meta - nw - ox, alto_meta - nh - oy), br), (ox + nw, oy + nh))

    canvas.paste(im_r, (ox, oy))
    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=90, optimize=True)
    return out.getvalue(), (w, h), (ancho_meta, alto_meta)

def estandarizar_lote_ids(ids_lista, forzar=False):
    wc, dbx = conectar()
    print(f"\n📸 Estandarizando {len(ids_lista)} productos a formato compacto 800x720 px...", flush=True)
    for idx, pid in enumerate(ids_lista, 1):
        t0 = time.time()
        pr = jload(wc.get(f"products/{pid}"))
        nom = pr.get("name", f"ID {pid}")
        imgs = pr.get("images") or []
        if not imgs:
            print(f"  ⚪ [{idx:03d}/{len(ids_lista)}] ID:{pid} ({nom[:38]}) -> Sin foto.")
            continue
        url_orig = imgs[0].get("src", "")
        r_img = requests.get(url_orig, timeout=25)
        if r_img.status_code != 200: continue
        nuevo_jpg, sz_a, sz_n = procesar_bytes_cuadrado(r_img.content, 800, 720, forzar=forzar)
        if nuevo_jpg is None:
            print(f"  ✅ [{idx:03d}/{len(ids_lista)}] ID:{pid} ({nom[:38]}) -> Ya está estandarizada ({sz_a[0]}x{sz_a[1]}).")
            continue
        guardar_bak_foto(pid, nom, imgs)
        fn_jpg = f"std_{pid}_{int(time.time())}.jpg"
        up = None
        # Intento 1: Puente directo terminado en .jpg
        try:
            rc = requests.post("https://litterbox.catbox.moe/resources/internals/api.php", data={"reqtype": "fileupload", "time": "1h"}, files={"fileToUpload": (fn_jpg, nuevo_jpg, "image/jpeg")}, timeout=20)
            if rc.status_code == 200 and rc.text.strip().endswith(".jpg"):
                nuevas_imgs = [{"src": rc.text.strip(), "name": nom}] + [{"id": im["id"]} for im in imgs[1:] if im.get("id")]
                up = wc.put(f"products/{pid}", {"images": nuevas_imgs})
        except Exception:
            pass
        # Intento 2 (Infalible): Puente GitHub Raw terminado en .jpg
        if up is None or up.status_code not in (200, 201):
            d_git = os.path.expanduser("~/tmp_woo_img")
            os.makedirs(d_git, exist_ok=True)
            open(os.path.join(d_git, fn_jpg), "wb").write(nuevo_jpg)
            os.system(f"cd ~ && git add -f tmp_woo_img/{fn_jpg} && git commit -m 'img {pid}' >/dev/null 2>&1 && git push origin main >/dev/null 2>&1")
            time.sleep(1.5)
            link_gh = f"https://raw.githubusercontent.com/mauriciovargas1516-ux/insumaes-woocommerce-automation/main/tmp_woo_img/{fn_jpg}"
            nuevas_imgs = [{"src": link_gh, "name": nom}] + [{"id": im["id"]} for im in imgs[1:] if im.get("id")]
            up = wc.put(f"products/{pid}", {"images": nuevas_imgs})
            os.system(f"cd ~ && git rm -f tmp_woo_img/{fn_jpg} >/dev/null 2>&1 && git commit -m 'clean img {pid}' >/dev/null 2>&1 && git push origin main >/dev/null 2>&1")
        if up.status_code in (200, 201):
            print(f"  🎨 [{idx:03d}/{len(ids_lista)}] ID:{pid} | {nom[:38]:<38} | {sz_a[0]}x{sz_a[1]} ➔ {sz_n[0]}x{sz_n[1]} px ({time.time()-t0:.1f}s)\n     🔗 {pr.get('permalink', '')}", flush=True)
        else:
            print(f"  ❌ [{idx:03d}/{len(ids_lista)}] ID:{pid} Error HTTP {up.status_code}: {up.text[:140]}", flush=True)

def restaurar_fotos(ids_lista=None):
    if not os.path.exists(RUTA_BAK_FOTOS):
        print("\n⚠️ No hay respaldos de fotos aún.")
        return
    wc, _ = conectar()
    bak = json.load(open(RUTA_BAK_FOTOS, "r", encoding="utf-8"))
    objetivos = [str(x) for x in ids_lista] if ids_lista else list(bak.keys())
    for pid in objetivos:
        if pid in bak:
            orig = [{"id": i["id"]} if i.get("id") else {"src": i["src"]} for i in bak[pid]["images"]]
            wc.put(f"products/{pid}", {"images": orig})
            print(f"  ⏪ ID:{pid} ({bak[pid]['name']}) restaurado a su foto original.")

def menu_fotos():
    f_cat = os.path.expanduser("~/respaldo_html_completo_woo.json")
    while True:
        os.system("clear")
        print("=" * 96)
        print("📸 ESTANDARIZADOR INTELIGENTE DE IMÁGENES (FORMATO COMPACTO 800x720 SIN ESPACIO MUERTO)")
        print("=" * 96)
        print(" [1] ⚡ Estandarizar los 3 Portas B45° Verticales de Foncho (IDs: 14499, 14500 y 14501)")
        print(" [2] 🎯 Estandarizar por ID_WOO específicos (ej: 14499, 14500)")
        print(" [3] 📁 Escoger UNA o VARIAS Categorías de insumaes.cl (ej: FRESA PARA BISELADO Y CHAFLANADO)")
        print(" [4] 🌐 Estandarizar TODA la Web (Solo corrige fotos verticales/gigantes, salta las sanas)")
        print(" [5] ⏪ Botón Ctrl+Z de Fotos (Restaurar foto original de 1 ID o de todas)")
        print(" [0] 🔙 Volver")
        print("=" * 96)
        op = input("\n👉 Opción (0-5): ").strip()
        if op == "0": break
        elif op == "1":
            estandarizar_lote_ids([14499, 14500, 14501], forzar=True); input("\nEnter para continuar...")
        elif op == "2":
            s = input("🔎 IDs separados por coma: ").strip()
            ids = [int(x.strip()) for x in s.split(",") if x.strip().isdigit()]
            if ids: estandarizar_lote_ids(ids, forzar=True)
            input("\nEnter para continuar...")
        elif op == "3":
            wc, _ = conectar()
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
            c_in = input("\n👉 Escribe uno o varios ID_CAT separados por coma (ej: 88, 90): ").strip()
            c_ids = [x.strip() for x in c_in.split(",") if x.strip().isdigit()]
            pids = []
            for cid in c_ids:
                p_lt = jload(wc.get("products", params={"category": cid, "per_page": 100}))
                if isinstance(p_lt, list): pids.extend(p["id"] for p in p_lt)
            if pids: estandarizar_lote_ids(list(dict.fromkeys(pids)), forzar=True)
            input("\nEnter para continuar...")
        elif op == "4":
            datos = json.load(open(f_cat, "r", encoding="utf-8")) if os.path.exists(f_cat) else {}
            estandarizar_lote_ids([int(k) for k in datos.keys()], forzar=False); input("\nEnter para continuar...")
        elif op == "5":
            s = input("🔎 ID_WOO a restaurar (o escribe TODOS): ").strip().upper()
            restaurar_fotos(None if s == "TODOS" else [s]); input("\nEnter para continuar...")

if __name__ == "__main__":
    if "--b45" in sys.argv: estandarizar_lote_ids([14499, 14500, 14501], forzar=True)
    else: menu_fotos()
