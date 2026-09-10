import dropbox

# Tus credenciales maestras
APP_KEY = "r3rxs0nwvcbuier"
APP_SECRET = "fpr892yv2ul129n"
REFRESH_TOKEN = "8yIGUthdXU0AAAAAAAAAAeo80CkDhbhuDFpa0yS20iu9YB9XceQNQput8_i6QyGt"

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
