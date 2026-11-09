import os, glob, time, dropbox, pandas as pd

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

APP_KEY = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY']
APP_SECRET = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET']
REFRESH_TOKEN = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN']

def generar_y_subir():
    print("\n📄 Empaquetando todos los scripts .py, .sh, configuraciones y logs en RADIOGRAFIA_ERP_INSUMAES.txt...")
    dbx = dropbox.Dropbox(app_key=APP_KEY, app_secret=APP_SECRET, oauth2_refresh_token=REFRESH_TOKEN)
    partes = [
        "==========================================================================",
        f"RADIOGRAFIA COMPLETA ERP INSUMAES - {time.strftime('%Y-%m-%d %H:%M:%S')} (Hora Chile)",
        "==========================================================================\n"
    ]
    for fn_x in ("~/AUDITORIA_PRE_SYNC.xlsx", "~/AUDITORIA_MELI_INSUMAES.xlsx"):
        px = os.path.expanduser(fn_x)
        if os.path.exists(px):
            try:
                dfx = pd.read_excel(px)
                partes.append(f"Columnas {os.path.basename(px)}: {list(dfx.columns)}")
                fx = dfx[dfx.astype(str).apply(lambda x: x.str.contains("SOLUBLE", case=False, na=False)).any(axis=1)]
                partes.append(f"Filas SOLUBLE en {os.path.basename(px)}:\n" + fx.to_string() + "\n")
            except Exception as ex:
                partes.append(f"Error leyendo {fn_x}: {ex}\n")

    home = os.path.expanduser("~")
    for ruta in sorted(glob.glob(f"{home}/*.py") + glob.glob(f"{home}/*.sh") + glob.glob(f"{home}/*.json")):
        nom = os.path.basename(ruta)
        if "token" in nom.lower(): continue
        try:
            c = open(ruta, "r", encoding="utf-8", errors="replace").read()
            partes.append(f"\n\n{'#'*80}\n### ARCHIVO: {nom} ({len(c)} bytes)\n{'#'*80}\n{c}")
        except Exception as e:
            partes.append(f"\n### ERROR {nom}: {e}")

    for lg in ("delta.log", "historial_erp.log", "cron_registro.log"):
        pl = os.path.join(home, lg)
        if os.path.exists(pl):
            ls = open(pl, "r", encoding="utf-8", errors="replace").readlines()[-60:]
            partes.append(f"\n\n{'='*80}\n=== ÚLTIMAS 60 LÍNEAS DE {lg} ===\n{'='*80}\n" + "".join(ls))

    txt_final = "\n".join(partes)
    ruta_local = os.path.expanduser("~/RADIOGRAFIA_ERP_INSUMAES.txt")
    open(ruta_local, "w", encoding="utf-8").write(txt_final)
    dbx.files_upload(txt_final.encode("utf-8"), "/RADIOGRAFIA_ERP_INSUMAES.txt", mode=dropbox.files.WriteMode.overwrite)
    try: dbx.files_delete_v2("/Compras L-Angel/RADIOGRAFIA_ERP_INSUMAES.txt")
    except Exception: pass
    print("✅ ¡RADIOGRAFIA_ERP_INSUMAES.txt subido a la RAÍZ de tu Dropbox (junto a tus .zip)!")

if __name__ == "__main__":
    generar_y_subir()
