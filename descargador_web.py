import os
import pandas as pd
from woocommerce import API
import json
import re

def descargar_catalogo_web():
    print("=" * 70)
    print(" 🌐 INICIANDO DESCARGA DESDE WOOCOMMERCE (CLOUD MODE)")
    print("=" * 70)
    
    wcapi = API(
        url="https://www.insumaes.cl/",
        consumer_key="os.getenv("WOO_KEY")",
        consumer_secret="os.getenv("WOO_SECRET")",
        version="wc/v3",
        timeout=60
    )
    
    productos_extraidos = []
    pagina = 1
    print("📡 Conectando con la tienda online...")
    
    while True:
        try:
            respuesta = wcapi.get("products", params={"per_page": 100, "page": pagina})
            texto_limpio = respuesta.text.strip('\ufeff')
            lote = json.loads(texto_limpio)
            
            if not isinstance(lote, list) or len(lote) == 0 or "code" in lote:
                break
                
            for prod in lote:
                nombre_padre = str(prod.get('name', '')).strip().upper()
                sku_padre = str(prod.get('sku', '')).strip().upper()
                desc_html = str(prod.get('description', '')) + " " + str(prod.get('short_description', ''))
                desc_limpia = re.sub(r'<[^>]+>', ' ', desc_html).strip().upper()
                
                # Saca las variaciones (Ej: Brocas de distintas medidas)
                if prod.get('type') == 'variable':
                    try:
                        resp_var = wcapi.get(f"products/{prod['id']}/variations", params={"per_page": 100})
                        vars_data = json.loads(resp_var.text.strip('\ufeff'))
                        for var in vars_data:
                            atributos = " ".join([str(a.get('option', '')) for a in var.get('attributes', [])])
                            if atributos.strip() == "" and var.get('sku'):
                                num_sku = re.findall(r'(\d+(?:[.,]\d+)?)', str(var.get('sku')))
                                if num_sku: atributos = num_sku[-1]
                                    
                            nombre_var = f"{nombre_padre} {atributos}".strip().upper()
                            precio_var = int(float(var.get('price'))) if var.get('price') else 0
                            stock_var = int(float(var.get('stock_quantity'))) if var.get('stock_quantity') is not None and str(var.get('stock_quantity')).strip() != "" else 0
                            
                            productos_extraidos.append({
                                'NOMBRE': nombre_var, 'SKU': str(var.get('sku', '')).strip().upper(),
                                'DESCRIPCION_WEB': desc_limpia, 'STOCK_WEB': stock_var,
                                'PRECIO_WEB': precio_var, 
                                'ID_WOO': f"{prod.get('id')}-{var.get('id')}" # <--- TRUCO: ID PADRE + GUION + ID HIJO
                            })
                    except Exception: pass
                
                # Saca los productos simples (Ej: Insertos)
                else:
                    precio = int(float(prod.get('price'))) if prod.get('price') else 0
                    stock = int(float(prod.get('stock_quantity'))) if prod.get('stock_quantity') is not None and str(prod.get('stock_quantity')).strip() != "" else 0
                    
                    productos_extraidos.append({
                        'NOMBRE': nombre_padre, 'SKU': sku_padre,
                        'DESCRIPCION_WEB': desc_limpia, 'STOCK_WEB': stock,
                        'PRECIO_WEB': precio, 
                        'ID_WOO': str(prod.get('id')) # <--- Producto simple (solo 1 ID)
                    })
                
            print(f"   -> Página {pagina} descargada...")
            if len(lote) < 100: break 
            pagina += 1
            
        except Exception as e:
            print(f"\n❌ [ERROR] Problema en página {pagina}: {e}")
            break

    df_web = pd.DataFrame(productos_extraidos)
    archivo_destino = "WEB_INSUMAES.xlsx"
    
    if len(df_web) > 0:
        df_web.to_excel(archivo_destino, index=False)
        print("\n" + "=" * 70)
        print(f" ✅ ¡DESCARGA COMPLETA! {len(df_web)} productos listos en la nube.")
        print("=" * 70)
    else:
        print("\n❌ [ERROR] No se encontraron productos.")

if __name__ == "__main__":
    descargar_catalogo_web()