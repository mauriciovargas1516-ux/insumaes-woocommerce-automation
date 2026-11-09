import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

# 1. Ponemos tus nuevas credenciales de la App
APP_KEY = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY']
APP_SECRET = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET']

# 2. Iniciamos el motor de autenticación pidiendo acceso "offline" (eterno)
auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type='offline')
authorize_url = auth_flow.start()

print("=" * 60)
print("🔑 GENERADOR DE REFRESH TOKEN PARA DROPBOX")
print("=" * 60)
print("1. Haz clic o copia esta URL en tu navegador web:")
print(f"👉 {authorize_url}\n")
print("2. Inicia sesión en tu cuenta de Dropbox de 'Compras L-Angel' y dale a 'Permitir'.")
print("3. Dropbox te mostrará un código corto en pantalla. Cópialo.")

# 3. El script se pausa esperando que le pegues el código
auth_code = input("\n📝 Pega el código de autorización aquí y presiona Enter: ").strip()

try:
    # 4. Intercambiamos el código corto por el token eterno
    oauth_result = auth_flow.finish(auth_code)
    print("\n✅ ¡ÉXITO! Tu ecosistema está autorizado.")
    print("=" * 60)
    print("ESTE ES TU NUEVO REFRESH_TOKEN. CÓPIALO Y GUÁRDALO BIEN:")
    print(oauth_result.refresh_token)
    print("=" * 60)
except Exception as e:
    print(f"\n❌ Error al generar el token: {e}")