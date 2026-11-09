import dropbox

# Tus credenciales maestras
APP_KEY = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY']
APP_SECRET = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET']
REFRESH_TOKEN = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN']

# El sistema de Dropbox se encarga de renovar el acceso automáticamente
dbx = dropbox.Dropbox(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    oauth2_refresh_token=REFRESH_TOKEN
)

print("🚀 Subiendo auditoría a Dropbox usando acceso autónomo...")
with open('AUDITORIA_PRE_SYNC.xlsx', 'rb') as f:
    dbx.files_upload(f.read(), '/AUDITORIA_PRE_SYNC.xlsx', mode=dropbox.files.WriteMode.overwrite)

print("✅ ¡Archivo subido con éxito! El sistema es 100% autónomo.")
