import pandas as pd
from difflib import SequenceMatcher
import os
import re
import dropbox
import io
import math
import gc

# ========================================================
# 1. CREDENCIALES Y CONFIGURACIÓN NUBE
# ========================================================
APP_KEY = "r3rxs0nwvcbuier"
APP_SECRET = "fpr892yv2ul129n"
REFRESH_TOKEN = "8yIGUthdXU0AAAAAAAAAAeo80CkDhbhuDFpa0yS20iu9YB9XceQNQput8_i6QyGt"
RUTA_NUBE_EXCEL = "/Compras L-Angel/Catalogo PortasHerramientas e Insertos.xlsx"

# ========================================================
# OPTIMIZACIÓN EXTREMA: PRE-COMPILAR REGEX PARA SALVAR RAM
# ========================================================
P_HRC = re.compile(r'HRC\s*[-]?\s*(\d+)')
P_MT = re.compile(r'MT(\d+)[-\s]*(\d*)')
P_MM = re.compile(r'(\d+(?:[.,]\d+)?)\s*MM')
P_TECNICO = re.compile(r'[A-Za-z]')
P_NUM = re.compile(r'\d')

def limpiar_web(tw):
    if not tw: return ""
    tw = str(tw).replace("KLINGSPOR - ", "").replace("LAMA TRONZAR", "").replace(",", ".").strip()
    etiquetas_basura = ["(3 UNIDADES)", "(5 UNIDADES)", "(10 UNIDADES)", "(10UN)", "(TRAPEZOIDAL)", "HSSE 5%COBALTO"]
    for basura in etiquetas_basura: tw = tw.replace(basura, "")

    tw = re.sub(r'\(\d+MM\)', '', tw) 
    tw = re.sub(r'\(\d+mm\)', '', tw)
    tw = tw.replace("COLA DE MILANO ", "").replace("FRESA CON INSERTO/ARAÑA ", "").replace("FRESA INSERTO ", "")
    tw = tw.replace("PERNO ALLEN SCREW", "ALLEN SCREW").replace("PERNO PLUM SCREW", "PLUM SCREW").replace("PERNO CLAMP SCREW", "CLAMP SCREW")
    tw = tw.replace("BRIDA ACCESORIO PORTAHERRAMIENTA", "ACCESORIO").replace("PASADOR ML PARA PORTAHERRAMIENTA", "ACCESORIO").replace("LOCK PIN CTM (PASADOR PARA PORTAHERRAMIENTA)", "ACCESORIO LOCK PIN CTM")
    tw = re.sub(r'\s+', ' ', tw).strip() 
   
    if "PLACA BASE" in tw and " PARA INSERTO" in tw:
        tw = tw.split(" PARA INSERTO")[0].strip()

    if "GJMATIC" in tw or "GJ2" in tw:
        tw = tw.replace("FLUIDO DE CORTE", "FLUIDO CORTE").replace("(TAPMATIC)", "").replace("(NUMERO 2)", "").replace("0.5L-1L", "")
        tw = tw.replace("GJMATIC", "GJ1 MATIC").replace("GJ2-MATIC", "GJ2 MATIC")
        tw = tw.replace("0,5 L", "1/2LT").replace("0.5 L", "1/2LT").replace("0,5L", "1/2LT").replace("0.5L", "1/2LT")
        tw = tw.replace("1 L", "1LT").replace("1L", "1LT")
        tw = re.sub(r'\s+', ' ', tw).strip() 

    if "FRESA" in tw:
        tw = re.sub(r'(\d+(?:[.,]\d+)?)\s*MM\s*-\s*T(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*MM', lambda m: f"D{m.group(1)}XT{m.group(2)}X{m.group(3)}MM", tw)
        tw = re.sub(r'(\d+(?:[.,]\d+)?)\s*MM\s*-\s*(\d+(?:[.,]\d+)?)\s*MM', lambda m: f"{m.group(1)} {m.group(2)}MM", tw)
        if "GRABADO" in tw:
            tw = re.sub(r'CONICO\s+(\d+)\s+GRADOS\s+PUNTA\s+(\d+(?:\.\d+)?)\s*MM\s+VASTAGO\s+(3\.175)', lambda m: f"V 1/8 {m.group(3)}*{m.group(1)}°*{m.group(2)}", tw)
            tw = re.sub(r'CONICO\s+(\d+)\s+GRADOS\s+PUNTA\s+(\d+(?:\.\d+)?)\s*MM\s+VASTAGO\s+(6(?:\.0)?)', lambda m: f"{m.group(3)}X{m.group(1)}°X{m.group(2)}", tw)
            tw = tw.replace(" ACERO", "").replace(" USO GENERAL", "").replace("FRESA GRABADO 6X", "6X").strip()
    
    tw = re.sub(r'BROCAS?\s+CON\s+INSERTO\s+N\s*°?\s*', 'ZD ', tw)
    tw = tw.replace('BROCA ZD', 'ZD').replace('BROCAS ZD', 'ZD')
    tw = re.sub(r'\s+', ' ', tw).strip()
    if tw.startswith("0 "): tw = tw[2:]
    return tw

def limpiar_local(tl):
    if not tl: return ""
    tl = re.sub(r'\s*\(\d+\)', '', str(tl)).replace("LAMA ", "").replace(",", ".").strip()
    tl = re.sub(r'BROCAS?\s+CON\s+INSERTO\s+N\s*°?\s*', 'ZD ', tl)
    tl = tl.replace('BROCA ZD', 'ZD').replace('BROCAS ZD', 'ZD')
    tl = re.sub(r'ZD\d*-(\d+(?:[.,]\d+)?)-.*', r'ZD \1', tl)
    
    diccionario_local = {"TUNGS ": "TUNGSTENO ", "TUNGS.": "TUNGSTENO ", "INOX": "INOXIDABLE", "ALUM": "ALUMINIO", "CONVEXA": "RADIO INTERIOR", "ROT PLATO": "ROTATIVO PLATO"}
    for corto, largo in diccionario_local.items(): tl = tl.replace(corto, largo)
    return re.sub(r'\s+', ' ', tl).strip()

def calcular_similitud_fast(tw, tl):
    if not tw or not tl: return 0.0

    hrc_web = P_HRC.search(tw)
    hrc_local = P_HRC.search(tl)
    if hrc_web and hrc_local and hrc_web.group(1) != hrc_local.group(1): return 0.0 
            
    mt_web = P_MT.search(tw)
    mt_local = P_MT.search(tl)
    if mt_web and mt_local:
        if mt_web.group(1) != mt_local.group(1) or mt_web.group(2) != mt_local.group(2): return 0.0 

    mm_web = P_MM.search(tw)
    mm_local = P_MM.search(tl)
    if mm_web and mm_local:
        try:
            if float(mm_web.group(1).replace(',', '.')) != float(mm_local.group(1).replace(',', '.')): return 0.0
        except ValueError: pass
            
    palabras_w = tw.split()
    palabras_l = tl.split()
    if palabras_w and palabras_l:
        cw = palabras_w[0]
        cl = palabras_l[0]
        es_codigo_tecnico = lambda word: bool(P_TECNICO.search(word)) and bool(P_NUM.search(word)) and len(word) >= 4
        if es_codigo_tecnico(cw) and es_codigo_tecnico(cl):
            if cw.replace("-M", "") != cl.replace("-M", ""): return 0.0 
            
    return SequenceMatcher(None, tw, tl).ratio()

def generar_auditoria_cloud():
    archivo_web = "WEB_INSUMAES.xlsx"
    archivo_reporte = "AUDITORIA_PRE_SYNC.xlsx"
    
    print("=" * 80)
    print(" ☁️ CEREBRO AUDITOR INSUMAES (MODO PILOTO AUTOMÁTICO - ETERNO)")
    print("=" * 80)

    if not os.path.exists(archivo_web):
        return
        
    print("📡 Conectando a Dropbox de forma autónoma...")
    dbx = dropbox.Dropbox(app_key=APP_KEY, app_secret=APP_SECRET, oauth2_refresh_token=REFRESH_TOKEN)
    print("⬇️ Descargando Excel maestro desde Dropbox a la RAM...")
    _, respuesta = dbx.files_download(RUTA_NUBE_EXCEL)
    archivo_en_memoria = io.BytesIO(respuesta.content)
    
    print("📦 Cruzando bases de datos...")
    df_local = pd.read_excel(archivo_en_memoria, sheet_name='INVENTARIO_WOO')
    df_web = pd.read_excel(archivo_web)

    df_local = df_local.dropna(subset=['NOMBRE'])
    df_local = df_local[df_local['NOMBRE'].astype(str).str.strip() != '']
    df_local = df_local[~df_local['NOMBRE'].astype(str).str.strip().isin(['0', '0.0', '0,0'])]
    df_local = df_local[~df_local['NOMBRE'].astype(str).str.upper().str.contains('MONTO', na=False)]
    df_local.columns = df_local.columns.astype(str).str.strip().str.upper()

    col_stock = 'CANTIDAD' if 'CANTIDAD' in df_local.columns else 'STOCK'
    if col_stock in df_local.columns:
        df_local[col_stock] = pd.to_numeric(df_local[col_stock], errors='coerce').fillna(0)
        df_local = df_local.rename(columns={col_stock: 'STOCK_LOCAL'})
    elif 'STOCK_LOCAL' not in df_local.columns: df_local['STOCK_LOCAL'] = 0

    if 'PRECIO' in df_local.columns:
        df_local['PRECIO'] = pd.to_numeric(df_local['PRECIO'], errors='coerce').fillna(0).round().astype(int)
        df_local = df_local.rename(columns={'PRECIO': 'PRECIO_LOCAL'})
    elif 'PRECIO_LOCAL' not in df_local.columns: df_local['PRECIO_LOCAL'] = 0
        
    df_local['SKU'] = df_local['SKU'].fillna('').astype(str).str.strip().str.upper()
    df_local['NOMBRE'] = df_local['NOMBRE'].fillna('').astype(str).str.strip().str.upper()
    df_web['SKU'] = df_web['SKU'].fillna('').astype(str).str.strip().str.upper()
    df_web['NOMBRE'] = df_web['NOMBRE'].fillna('').astype(str).str.strip().str.upper()

    dic_local = df_local.to_dict('index')
    dic_web = df_web.to_dict('records')
    
    del df_local
    del df_web
    gc.collect()
    
    mapa_sku_local = {fila['SKU']: idx for idx, fila in dic_local.items() if fila['SKU']}
    mapa_nombre_local = {fila['NOMBRE']: idx for idx, fila in dic_local.items() if fila['NOMBRE']}

    for idx, fila in dic_local.items():
        fila['N_LOC_MAYUS'] = str(fila['NOMBRE']).upper()
        fila['TEXTO_LIMPIO'] = limpiar_local(fila['N_LOC_MAYUS'])
        fila['ES_JUEGO'] = any(w in fila['N_LOC_MAYUS'] for w in ["JGO", "JUEGO", "MALETA", "SET"])

    reporte_auditoria = []
    UMBRAL_SIMILITUD = 0.75
    local_indices_matcheados = set()
    total_web = len(dic_web)
    
    print(f"🔍 Analizando {total_web} productos (Motor Warp Fase 2 + Respirador RAM)...\n")
    
    for idx, row_web in enumerate(dic_web):
        # 💉 RESPIRADOR ARTIFICIAL DE RAM: Limpiar basura cada 50 productos
        if idx % 50 == 0:
            gc.collect()

        sku_web, nombre_web = row_web['SKU'], row_web['NOMBRE']
        precio_web = row_web.get('PRECIO_WEB', 0)
        stock_web = row_web.get('STOCK_WEB', 0)
        
        match_tipo, nombre_local_match, sku_local_match = "🔴 SIN MATCH", "---", "---"
        precio_local, stock_local, match_encontrado, idx_local_encontrado = 0, 0, False, None
        
        if sku_web != "" and sku_web in mapa_sku_local:
            idx_local_encontrado = mapa_sku_local[sku_web]
            f = dic_local[idx_local_encontrado]
            match_tipo, nombre_local_match, sku_local_match, match_encontrado = "🟢 MATCH SKU", f['NOMBRE'], f['SKU'], True
            precio_local, stock_local = f['PRECIO_LOCAL'], f['STOCK_LOCAL']
                
        if not match_encontrado and nombre_web != "" and nombre_web in mapa_nombre_local:
            idx_local_encontrado = mapa_nombre_local[nombre_web]
            f = dic_local[idx_local_encontrado]
            match_tipo, nombre_local_match, sku_local_match, match_encontrado = "🟡 MATCH NOMBRE", f['NOMBRE'], f['SKU'], True
            precio_local, stock_local = f['PRECIO_LOCAL'], f['STOCK_LOCAL']

        if not match_encontrado and nombre_web != "":
            tw_limpio = limpiar_web(nombre_web)
            mejor_similitud, mejor_idx = 0.0, None
            es_juego_web = any(w in nombre_web for w in ["JGO", "JUEGO", "MALETA", "SET"])
            
            for idx_loc, f in dic_local.items():
                if es_juego_web != f['ES_JUEGO']: continue
                sim = calcular_similitud_fast(tw_limpio, f['TEXTO_LIMPIO'])
                if sim > mejor_similitud: mejor_similitud, mejor_idx = sim, idx_loc
                
            if mejor_similitud >= UMBRAL_SIMILITUD:
                idx_local_encontrado, match_encontrado = mejor_idx, True
                f = dic_local[idx_local_encontrado]
                match_tipo, nombre_local_match, sku_local_match = "🔵 MATCH DETECTIVE", f['NOMBRE'], f['SKU']
                precio_local, stock_local = f['PRECIO_LOCAL'], f['STOCK_LOCAL']

        varianza_num, stock_a_inyectar = 0.0, 0
        if match_encontrado:
            local_indices_matcheados.add(idx_local_encontrado)
            match_unidades = re.search(r'\((\d+)\s*UNIDADES\)', nombre_web)
            if match_unidades:
                multiplicador = int(match_unidades.group(1))
                precio_local *= multiplicador
                stock_local //= multiplicador
            
            stock_a_inyectar = math.ceil(stock_local * 0.5)
            if precio_web > 0 and precio_local > 0: varianza_num = abs(precio_web - precio_local) / precio_local
                
            if precio_local <= 0 and stock_a_inyectar > 0: accion_requerida = "🚨 SIN PRECIO EN EXCEL"
            elif varianza_num >= 0.40: accion_requerida = "🚨 ALERTA DE PRECIO"
            elif stock_web != stock_a_inyectar or precio_web != precio_local: accion_requerida = "⚠️ ACTUALIZAR WEB"
            else: accion_requerida = "✅ AL DÍA"
        else: accion_requerida = "NINGUNA"
                
        reporte_auditoria.append({
            'ESTADO': accion_requerida, 'TIPO DE CRUCE': match_tipo,
            'PRODUCTO WEB': nombre_web, 'PRODUCTO LOCAL': nombre_local_match,
            'SKU WEB': sku_web, 'SKU LOCAL': sku_local_match,
            'STOCK WEB': stock_web, 'STOCK LOCAL (Nuevo)': stock_a_inyectar, 'STOCK FÍSICO (Real)': stock_local,
            'PRECIO WEB': precio_web, 'PRECIO LOCAL (Nuevo)': precio_local,
            'VARIANZA': f"{varianza_num * 100:.1f}%", 'ID_WOO': row_web.get('ID_WOO', "")
        })

        if (idx + 1) % 50 == 0 or (idx + 1) == total_web:
            porcentaje = int(((idx + 1) / total_web) * 100)
            print(f"   ⏳ Progreso: {porcentaje}% ({idx + 1} de {total_web} productos procesados...)", flush=True)

    for idx_loc, f in dic_local.items():
        if idx_loc not in local_indices_matcheados:
            stock_real = f['STOCK_LOCAL']
            reporte_auditoria.append({
                'ESTADO': '🔵 CREAR EN WEB', 'TIPO DE CRUCE': 'NUEVO INGRESO',
                'PRODUCTO WEB': '---', 'PRODUCTO LOCAL': f['NOMBRE'],
                'SKU WEB': '---', 'SKU LOCAL': f['SKU'],
                'STOCK WEB': 0, 'STOCK LOCAL (Nuevo)': math.ceil(stock_real * 0.5), 'STOCK FÍSICO (Real)': stock_real,
                'PRECIO WEB': 0, 'PRECIO LOCAL (Nuevo)': f['PRECIO_LOCAL'],
                'VARIANZA': '0.0%', 'ID_WOO': ""
            })

    pd.DataFrame(reporte_auditoria).to_excel(archivo_reporte, index=False, engine='openpyxl')

    print("\n" + "=" * 80)
    print(" 📊 REPORTE DE SALUD DEL CATÁLOGO INSUMAES")
    print(f" 📦 Local: {len(dic_local)} | 🌐 Web: {total_web} | 🔗 Matches: {len(local_indices_matcheados)}")
    print("=" * 80)

if __name__ == "__main__":
    generar_auditoria_cloud()