import pandas as pd
from woocommerce import API
import os
import sys
import time  # <-- AGREGA ESTA LÍNEA AQUÍ

def sincronizar_woocommerce():
    print("\n" + "=" * 80)
    print(" 🤖 BRAZO EJECUTOR: SINCRONIZADOR INSUMAES (MODO AUTÓNOMO)")
    print("=" * 80)

    archivo_reporte = "AUDITORIA_PRE_SYNC.xlsx"
    
    if not os.path.exists(archivo_reporte):
        print(f"❌ [ERROR] No existe '{archivo_reporte}'. El Ojo y el Cerebro deben actuar primero.")
        return

    df = pd.read_excel(archivo_reporte)

    # --- 📊 GENERACIÓN DE ESTADÍSTICAS EJECUTIVAS ---
    total_auditados = len(df)
    df_actualizar = df[df['ESTADO'] == '⚠️ ACTUALIZAR WEB']
    df_peligro = df[df['ESTADO'].astype(str).str.contains('🚨 ALERTA', na=False)]
    df_nuevos = df[df['ESTADO'].astype(str).str.contains('🔵 CREAR', na=False)]
    al_dia = total_auditados - len(df_actualizar) - len(df_peligro) - len(df_nuevos)

    print("\n" + "📊 " + "-" * 74)
    print(" RESUMEN EJECUTIVO DE LA AUDITORÍA".center(74))
    print("-" * 77)
    print(f" 🔎 Total de Productos Analizados : {total_auditados}")
    print(f" ✅ Productos Al Día (Sin cambios): {al_dia}")
    print(f" 🔵 Productos Nuevos (Sin subir)  : {len(df_nuevos)}")
    print(f" 🚨 Bloqueados (Varianza Extrema) : {len(df_peligro)} (Se ignorarán por seguridad)")
    print(f" ⚠️ LISTOS PARA INYECTAR EN WEB   : {len(df_actualizar)}")
    print("-" * 77 + "\n")

    if len(df_actualizar) == 0:
        print("✅ No hay cambios de stock o precio para inyectar hoy. Saliendo...")
        return

    # --- 🚀 INYECCIÓN DIRECTA Y AUTÓNOMA (SIN FRENOS MANUALES) ---
    print(f"🚀 Iniciando inyección segura de {len(df_actualizar)} productos en piloto automático...\n")

    wcapi = API(
        url="https://www.insumaes.cl/",
        consumer_key="os.getenv("WOO_KEY")",
        consumer_secret="os.getenv("WOO_SECRET")",
        version="wc/v3",
        timeout=60
    )

    exitos = 0
    errores = 0

    for idx, row in df_actualizar.iterrows():
        id_woo = str(row['ID_WOO']).strip()
        nuevo_precio = int(row['PRECIO LOCAL (Nuevo)'])
        nuevo_stock = int(row['STOCK LOCAL (Nuevo)'])
        nombre = row['PRODUCTO LOCAL']

        if id_woo == "" or id_woo.lower() == "nan":
            continue

        # --- 🛡️ CORTAFUEGOS DE SEGURIDAD COMERCIAL ---
        if nuevo_precio <= 0:
            print(f"   🚫 [BLOQUEADO] {nombre[:30]:<30} -> Intento de inyectar Precio $0. Ignorado.")
            errores += 1
            continue

        datos_actualizados = {"regular_price": str(nuevo_precio), "manage_stock": True, "stock_quantity": nuevo_stock}

        try:
            # --- NUEVA LÓGICA DE DETECCIÓN DE VARIACIONES ---
            if "-" in id_woo:
                id_padre, id_variacion = id_woo.split("-")
                endpoint = f"products/{int(id_padre)}/variations/{int(id_variacion)}"
            else:
                endpoint = f"products/{int(float(id_woo))}"

            respuesta = wcapi.put(endpoint, datos_actualizados)
            
            if respuesta.status_code in [200, 201]:
                print(f"   ✅ [OK] {nombre[:30]:<30} -> Precio: ${nuevo_precio} | Stock: {nuevo_stock}")
                exitos += 1
            else:
                print(f"   ❌ [ERROR API] {nombre[:30]}... : {respuesta.text}")
                errores += 1
        except Exception as e:
            print(f"   ❌ [ERROR CRÍTICO] {nombre[:30]}... : {e}")
            errores += 1
            
        time.sleep(1)

    print("\n" + "=" * 80)
    print(f" 🏁 INYECCIÓN FINALIZADA: {exitos} Actualizados | {errores} Errores")

if __name__ == "__main__":
    sincronizar_woocommerce()