
import requests

# --- LAS LLAVES MAESTRAS DEL MOTOR (Token Perpetuo) ---
TOKEN_WHATSAPP = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['WHATSAPP_TOKEN']
ID_TELEFONO = "1204555346076305"

def enviar_whatsapp_real(mensaje, numero_destino):
    url = f"https://graph.facebook.com/v17.0/{ID_TELEFONO}/messages"
    
    headers = {
        "Authorization": f"Bearer {TOKEN_WHATSAPP}", 
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": mensaje}
    }
    
    respuesta = requests.post(url, headers=headers, json=payload)
    print(f"\nRespuesta de Meta: Código {respuesta.status_code}")

if __name__ == "__main__":
    print("\n=======================================")
    print("  🤖 TERMINAL DE MENSAJES INSUMAES 🤖  ")
    print("=======================================\n")
    
    # 1. El programa te pide el número interactivo
    numero = input("📱 Ingresa el número de destino (ej: 56952115431): ")
    
    # 2. El programa te pide que redactes el mensaje
    texto = input("💬 Escribe el mensaje que quieres enviar: ")
    
    # 3. Se dispara el motor con tus respuestas
    print("\n🚀 Disparando mensaje desde Google Cloud...")
    enviar_whatsapp_real(texto, numero)
