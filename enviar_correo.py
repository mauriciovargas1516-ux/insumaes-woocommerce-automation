import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE CREDENCIALES
# ==========================================
CORREO_ORIGEN = "mauriciovargas1516@gmail.com"
PASSWORD_APP = "os.getenv("GMAIL_PASS")" # Tu llave maestra original
CORREO_DESTINO = "mauriciovargas1516@gmail.com"

# ==========================================
# 2. CAPTURAR EL TIEMPO DESDE BASH
# ==========================================
try:
    minutos = sys.argv[1]
    segundos = sys.argv[2]
    texto_tiempo = f"⏱️ El protocolo se completó en: {minutos} minutos y {segundos} segundos."
except:
    texto_tiempo = "⏱️ El protocolo ha finalizado (tiempo no especificado)."

# ==========================================
# 3. LECTURA Y FILTRADO DEL LOG (SOLO RESUMEN)
# ==========================================
ruta_log = "/home/mauriciovargas1516/cron_registro.log"
resumen_cambios = "No se encontraron registros recientes."

if os.path.exists(ruta_log):
    try:
        with open(ruta_log, 'r', encoding='utf-8') as archivo_log:
            lineas = archivo_log.readlines()

            texto_auditoria = ""
            # Buscamos el último resumen leyendo de abajo hacia arriba
            for i in range(len(lineas) - 1, -1, -1):
                if "RESUMEN EJECUTIVO DE LA AUDITOR" in lineas[i].upper():
                    # Calculamos el rango del bloque (aprox. 12 líneas de la tabla)
                    inicio = max(0, i - 1)
                    fin = min(len(lineas), i + 12)
                    
                    bloque = lineas[inicio:fin]
                    
                    # Filtramos la "basura" visual por si se cuela
                    bloque_limpio = [
                        linea for linea in bloque 
                        if "Progreso:" not in linea 
                        and "BRAZO EJECUTOR" not in linea
                        and "CICLO FINALIZADO" not in linea
                        and "RESUMEN DE CAMBIOS" not in linea
                    ]
                    texto_auditoria = "".join(bloque_limpio)
                    break
            
            if texto_auditoria:
                resumen_cambios = texto_auditoria
            else:
                resumen_cambios = "No se encontró el Resumen Ejecutivo en esta ejecución."
                
    except Exception as e:
        resumen_cambios = f"No se pudo leer el log: {e}"

# ==========================================
# 4. CREACIÓN DEL MENSAJE
# ==========================================
fecha_actual = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
asunto = f"✅ INSUMAES CLOUD: Reporte Finalizado ({fecha_actual})"

cuerpo_mensaje = f"""Hola Mauricio,

El ciclo automático de Insumaes Cloud ha finalizado con éxito.

{texto_tiempo}

Aquí tienes el resumen de la auditoría:

{resumen_cambios}
"""

# ==========================================
# 5. ENVÍO DEL CORREO
# ==========================================
msg = MIMEMultipart()
msg['From'] = CORREO_ORIGEN
msg['To'] = CORREO_DESTINO
msg['Subject'] = asunto

msg.attach(MIMEText(cuerpo_mensaje, 'plain', 'utf-8'))

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(CORREO_ORIGEN, PASSWORD_APP)
    server.send_message(msg)
    server.quit()
    print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")
