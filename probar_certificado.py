import os
from cryptography.hazmat.primitives.serialization import pkcs12

# Cargamos la clave desde la variable de entorno que configuramos
clave_sii = os.getenv("CLAVE_SII")

if not clave_sii:
    print("Error: La variable de entorno CLAVE_SII no está configurada.")
else:
    try:
        # Abrimos el archivo .pfx
        with open("certificado.pfx", "rb") as f:
            pfx_data = f.read()
            
        # Intentamos cargar el certificado
        p12 = pkcs12.load_pkcs12(pfx_data, clave_sii.encode())
        
        print("✅ ¡Éxito! El certificado se cargó correctamente en memoria.")
        print("Tu empresa está lista para firmar documentos.")
        
    except Exception as e:
        print(f"❌ Error al cargar el certificado: {e}")
