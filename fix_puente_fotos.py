import os, py_compile

p = os.path.expanduser("~/estandarizador_fotos_woo.py")
t = open(p, "r", encoding="utf-8").read()

viejo_bloque = '''        ruta_dbx = f"/tmp_woo_img/std_{pid}_{int(time.time())}.jpg"
        dbx.files_upload(nuevo_jpg, ruta_dbx, mode=dropbox.files.WriteMode.overwrite)
        link_temp = dbx.files_get_temporary_link(ruta_dbx).link
        nuevas_imgs = [{"src": link_temp, "name": nom}] + [{"id": im["id"]} for im in imgs[1:] if im.get("id")]
        up = wc.put(f"products/{pid}", {"images": nuevas_imgs})
        try: dbx.files_delete_v2(ruta_dbx)
        except Exception: pass'''

nuevo_bloque = '''        fn_jpg = f"std_{pid}_{int(time.time())}.jpg"
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
            os.system(f"cd ~ && git rm -f tmp_woo_img/{fn_jpg} >/dev/null 2>&1 && git commit -m 'clean img {pid}' >/dev/null 2>&1 && git push origin main >/dev/null 2>&1")'''

t = t.replace(viejo_bloque, nuevo_bloque)
t = t.replace('print(f"  ❌ [{idx:03d}/{len(ids_lista)}] ID:{pid} Error HTTP {up.status_code}", flush=True)', 'print(f"  ❌ [{idx:03d}/{len(ids_lista)}] ID:{pid} Error HTTP {up.status_code}: {up.text[:140]}", flush=True)')
open(p, "w", encoding="utf-8").write(t)
py_compile.compile(p, doraise=True)
print("✅ Doble Puente .JPG activado en estandarizador_fotos_woo.py")
