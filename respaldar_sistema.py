import os, glob, zipfile, subprocess
from datetime import datetime
import dropbox

APP_KEY = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY']
APP_SECRET = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET']
REFRESH_TOKEN = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN']
MAX_DIAS_HISTORIAL = 7

def empaquetar_y_subir():
    home = os.path.expanduser("~")
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_zip = f"BACKUP_ERP_INSUMAES_{fecha_hoy}.zip"
    ruta_zip = os.path.join(home, "BACKUP_SISTEMA_ERP_INSUMAES.zip")
    raiz_interna = f"ERP_INSUMAES_{fecha_hoy}"

    print(f"\n📦 Empaquetando sistema ordenado ({nombre_zip})...")

    with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Motores y Scripts (.py y .sh)
        for pat in ("*.py", "*.sh"):
            for fp in sorted(glob.glob(os.path.join(home, pat))):
                if os.path.isfile(fp):
                    zf.write(fp, arcname=f"{raiz_interna}/1_MOTORES_Y_SCRIPTS/{os.path.basename(fp)}")

        # 2. Configuración, Llaves (.json) y Crontab
        for fp in sorted(glob.glob(os.path.join(home, "*.json"))):
            if os.path.isfile(fp):
                zf.write(fp, arcname=f"{raiz_interna}/2_CONFIGURACION_Y_LLAVES/{os.path.basename(fp)}")
        try:
            cron = subprocess.check_output(["crontab", "-l"], text=True, stderr=subprocess.DEVNULL)
            zf.writestr(f"{raiz_interna}/2_CONFIGURACION_Y_LLAVES/CRONTAB_SERVIDOR.txt", cron)
        except Exception:
            pass

        # 3. Bitácoras y Logs (.log)
        for fp in sorted(glob.glob(os.path.join(home, "*.log")) + glob.glob(os.path.join(home, "BITACORA_CAMBIOS_*.txt"))):
            if os.path.isfile(fp) and os.path.getsize(fp) < 15_000_000:
                zf.write(fp, arcname=f"{raiz_interna}/3_BITACORAS_Y_LOGS/{os.path.basename(fp)}")

        # 4. Últimas Auditorías Excel (.xlsx)
        for nombre_aud in ("AUDITORIA_MELI_INSUMAES.xlsx", "AUDITORIA_PRE_SYNC.xlsx"):
            fp_aud = os.path.join(home, nombre_aud)
            if os.path.exists(fp_aud):
                zf.write(fp_aud, arcname=f"{raiz_interna}/4_AUDITORIAS_EXCEL/{nombre_aud}")

    peso_kb = round(os.path.getsize(ruta_zip) / 1024, 1)
    print(f"✅ ZIP estructurado listo en servidor ({peso_kb} KB).")

    try:
        dbx = dropbox.Dropbox(app_key=APP_KEY, app_secret=APP_SECRET, oauth2_refresh_token=REFRESH_TOKEN, timeout=60)
        dest_hoy = f"/{nombre_zip}"
        with open(ruta_zip, "rb") as f:
            dbx.files_upload(f.read(), dest_hoy, mode=dropbox.files.WriteMode.overwrite)
        print(f"☁️ Subido a la raíz de tu Dropbox: {dest_hoy}")

        # Rotación automática: conservar solo los últimos 7 días en la raíz
        res_list = dbx.files_list_folder("")
        archivos_zip = sorted(
            [e for e in res_list.entries if isinstance(e, dropbox.files.FileMetadata) and e.name.startswith("BACKUP_ERP_INSUMAES_") and e.name.endswith(".zip")],
            key=lambda x: x.name,
            reverse=True
        )
        for viejo in archivos_zip[MAX_DIAS_HISTORIAL:]:
            dbx.files_delete_v2(f"/{viejo.name}")
            print(f"🧹 Respaldo antiguo (>7 días) eliminado de la raíz: {viejo.name}")

        print(f"📂 Raíz de Dropbox al día ({min(len(archivos_zip), MAX_DIAS_HISTORIAL)} respaldos guardados).")
    except Exception as e:
        print(f"⚠️ Aviso subida Dropbox: {e}")

if __name__ == "__main__":
    empaquetar_y_subir()
