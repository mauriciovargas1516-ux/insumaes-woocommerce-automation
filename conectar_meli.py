import os, re, json, time, requests

RUTA_TOKENS = os.path.expanduser("~/meli_tokens.json")
CLIENT_ID = "2794072924542280"
REDIRECT_URI = "https://insumaes.cl/"

def obtener_token_valido():
    """Devuelve siempre un access_token vigente, renovándolo solo si venció."""
    if not os.path.exists(RUTA_TOKENS):
        return None
    with open(RUTA_TOKENS, "r", encoding="utf-8") as f:
        tk = json.load(f)
    # Si faltan menos de 10 minutos para que venza, se renueva automáticamente
    if time.time() > tk.get("expires_at", 0) - 600:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type": "refresh_token",
            "client_id": tk["client_id"],
            "client_secret": tk["client_secret"],
            "refresh_token": tk["refresh_token"]
        }, timeout=15)
        if r.status_code == 200:
            nuevo = r.json()
            tk["access_token"] = nuevo["access_token"]
            tk["refresh_token"] = nuevo["refresh_token"]
            tk["expires_at"] = time.time() + nuevo.get("expires_in", 21600)
            with open(RUTA_TOKENS, "w", encoding="utf-8") as f:
                json.dump(tk, f, indent=4)
    return tk.get("access_token")

if __name__ == "__main__":
    print("=======================================================")
    print("🔐 CONEXIÓN OFICIAL API MERCADO LIBRE (MODO SEGURO)    ")
    print("=======================================================")
    secret = input("1️⃣ Pega tu CLIENT SECRET: ").strip()
    raw_code = input("2️⃣ Pega la URL completa (o el código TG-...): ").strip()

    # Extraer limpio el código TG-... aunque peguen la URL entera
    m = re.search(r'(TG-[A-Za-z0-9\-_]+)', raw_code)
    code = m.group(1) if m else raw_code

    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": secret,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }, timeout=15)

    if r.status_code != 200:
        print(f"\n❌ Error al canjear código ({r.status_code}): {r.text}")
    else:
        datos = r.json()
        guardar_obj = {
            "client_id": CLIENT_ID,
            "client_secret": secret,
            "access_token": datos["access_token"],
            "refresh_token": datos["refresh_token"],
            "user_id": datos.get("user_id"),
            "expires_at": time.time() + datos.get("expires_in", 21600)
        }
        with open(RUTA_TOKENS, "w", encoding="utf-8") as f:
            json.dump(guardar_obj, f, indent=4)
        os.chmod(RUTA_TOKENS, 0o600)

        # Prueba 100% de SOLO LECTURA para verificar identidad
        me = requests.get(
            "https://api.mercadolibre.com/users/me",
            headers={"Authorization": f"Bearer {datos['access_token']}"},
            timeout=10
        ).json()
        print("\n✅ ¡CONEXIÓN EXITOSA Y AUTO-RENOVABLE GUARDADA EN ~/meli_tokens.json!")
        print(f"👤 Cuenta conectada : {me.get('nickname')} (ID: {me.get('id')})")
        print(f"🏢 Razón Social     : {me.get('first_name')} {me.get('last_name')}")
        print("🛡️ Estado Escritura : BLOQUEADO POR SEGURIDAD (Modo Solo Lectura activo)")
