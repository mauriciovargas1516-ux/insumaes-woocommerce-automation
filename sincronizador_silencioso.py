import lee_config
import pandas as pd
from woocommerce import API
import os
import sys
import time

def sincronizar_woocommerce():
    print("\n" + "=" * 80)
    print(" 🤖 BRAZO EJECUTOR: SINCRONIZADOR INSUMAES (MODO AUTÓNOMO)")
    print("=" * 80)

    woo_st_on = str(lee_config.obtener_valor("SINCRONIZAR_WOO_STOCK", "SI")).upper() == "SI"
    woo_pr_on = str(lee_config.obtener_valor("SINCRONIZAR_WOO_PRECIOS", "SI")).upper() == "SI"
    if not woo_st_on and not woo_pr_on:
        print("🛑 WOO_STOCK y WOO_PRECIOS están en NO en el Panel. Omitiendo inyección en Web.")
        return
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
        consumer_key=os.getenv("WOO_KEY", dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['WOO_KEY']),
        consumer_secret=os.getenv("WOO_SECRET", dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['WOO_SECRET']),
        version="wc/v3",
        timeout=60
    )

    exitos = 0
    errores = 0

    for idx, row in df_actualizar.iterrows():
        id_woo = str(row['ID_WOO']).strip()
        nuevo_precio = int(row['PRECIO LOCAL (Nuevo)'])
        nuevo_stock = int(row['STOCK LOCAL (Nuevo)'])
        precio_antiguo = int(row['PRECIO WEB']) if pd.notna(row['PRECIO WEB']) else 0
        stock_antiguo = int(row['STOCK WEB']) if pd.notna(row['STOCK WEB']) else 0
        nombre = str(row['PRODUCTO LOCAL'])

        if id_woo == "" or id_woo.lower() == "nan":
            continue

                # --- 🛡️CORTAFUEGOS DE SEGURIDAD COMERCIAL INTELIGENTE ---
        if nuevo_precio <= 0:
            if nuevo_stock == stock_antiguo:
                print(f"   🛡️[PROTEGIDO] {nombre[:30]:<30} -> Precio $0 en Excel y Stock sin cambios ({nuevo_stock}). Manteniendo precio web (${precio_antiguo}).")
                continue
            else:
                print(f"   ⚠️[SOLO STOCK] {nombre[:30]:<30} -> Precio $0 bloqueado (se mantiene ${precio_antiguo}), pero se actualiza Stock ({stock_antiguo} -> {nuevo_stock}).")
                datos_actualizados = {
                    "manage_stock": True,
                    "stock_quantity": nuevo_stock,
                    "stock_status": "instock" if nuevo_stock > 0 else "outofstock"
                }
        else:
            datos_actualizados = {
                "regular_price": str(nuevo_precio),
                "manage_stock": True,
                "stock_quantity": nuevo_stock,
                "stock_status": "instock" if nuevo_stock > 0 else "outofstock"
            }

        try:
            # --- LÓGICA DE DETECCIÓN DE VARIACIONES ---
            if "-" in id_woo:
                id_padre, id_variacion = id_woo.split("-")
                endpoint = f"products/{int(id_padre)}/variations/{int(id_variacion)}"
            else:
                endpoint = f"products/{int(float(id_woo))}"

            respuesta = wcapi.put(endpoint, datos_actualizados)
            
            if respuesta.status_code in [200, 201]:
                print(f"   ✅ [OK] {nombre[:30]:<30} -> Stock ({stock_antiguo} ➔ {nuevo_stock}) | Precio (${precio_antiguo} ➔ ${nuevo_precio})")
                exitos += 1; lee_config.registrar_evento("WOO-WEB", f"ID:{id_woo}", nombre, f"Stock {stock_antiguo} ➔ {nuevo_stock} uds | Precio ${precio_antiguo} ➔ ${nuevo_precio}")
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
