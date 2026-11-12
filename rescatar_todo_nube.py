import os, glob, time, json, zipfile, dropbox

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

def conectar_dbx():
    env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
    return dropbox.Dropbox(app_key=env["DROPBOX_APP_KEY"], app_secret=env["DROPBOX_APP_SECRET"], oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"])

def ejecutar_rescate_total():
    t0 = time.time()
    home = os.path.expanduser("~")
    dbx = conectar_dbx()
    ahora = time.strftime("%Y-%m-%d %H:%M:%S")
    fecha_hoy = time.strftime("%Y-%m-%d")

    print("\n" + "=" * 92)
    print(f"🛡️  AUDITORÍA Y RESCATE TOTAL DE LA NUBE (.PY, .SH, .JSON, .LOG, .DB) — {ahora}")
    print("=" * 92)

    patrones = ["*.py", "*.sh", "*.log", "config_bot.json", "estado_stocks_delta.json", "mapas_rapidos_cache.json"]
    archivos_txt = []
    for pat in patrones:
        for f in sorted(glob.glob(os.path.join(home, pat))):
            nom_f = os.path.basename(f)
            if os.path.isfile(f) and not nom_f.startswith("fix_") and not nom_f.startswith("upgrade_"):
                archivos_txt.append(f)

    bloques = [
        "=" * 80,
        f"RADIOGRAFIA COMPLETA ERP INSUMAES CLOUD - GENERADO: {ahora}",
        f"Total Archivos Incluidos: {len(archivos_txt)}",
        "=" * 80 + "\n"
    ]
    for ruta in archivos_txt:
        nom = os.path.basename(ruta)
        tam = os.path.getsize(ruta)
        try:
            contenido = open(ruta, "r", encoding="utf-8", errors="replace").read()
            if nom.endswith(".log") and len(contenido) > 35000:
                contenido = "... [TRUNCADO A ÚLTIMOS 35 KB] ...\n" + contenido[-35000:]
        except Exception as e:
            contenido = f"[Error leyendo {nom}: {e}]"
        bloques.append(f"{'#' * 80}\n### ARCHIVO: {nom} ({tam} bytes)\n{'#' * 80}\n{contenido}\n\n")
        print(f"  📄 [RESCATADO EN TXT] {nom:<38} ({tam:>8,} bytes)")

    txt_final = "".join(bloques)
    ruta_rad_local = os.path.join(home, "RADIOGRAFIA_ERP_INSUMAES.txt")
    open(ruta_rad_local, "w", encoding="utf-8").write(txt_final)
    dbx.files_upload(txt_final.encode("utf-8"), "/RADIOGRAFIA_ERP_INSUMAES.txt", mode=dropbox.files.WriteMode.overwrite)
    print(f"\n  ✅ 1/2: '/RADIOGRAFIA_ERP_INSUMAES.txt' actualizado en tu Dropbox ({len(txt_final)//1024:,} KB).")

    nom_zip = f"BACKUP_ERP_INSUMAES_{fecha_hoy}.zip"
    ruta_zip_local = os.path.join(home, nom_zip)
    exts_zip = (".py", ".sh", ".json", ".log", ".db")
    cont_zip = 0
    with zipfile.ZipFile(ruta_zip_local, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(os.listdir(home)):
            r_full = os.path.join(home, item)
            if os.path.isfile(r_full) and item.endswith(exts_zip) and not item.startswith("fix_"):
                zf.write(r_full, arcname=item)
                cont_zip += 1

    tam_zip = os.path.getsize(ruta_zip_local)
    with open(ruta_zip_local, "rb") as fz:
        dbx.files_upload(fz.read(), f"/{nom_zip}", mode=dropbox.files.WriteMode.overwrite)
    print(f"  ✅ 2/2: '/{nom_zip}' subido a tu Dropbox ({cont_zip} archivos | {tam_zip//1024:,} KB) en {time.time()-t0:.1f}s.")
    print("=" * 92 + "\n")

generar_y_subir = ejecutar_rescate_total

if __name__ == "__main__":
    ejecutar_rescate_total()
