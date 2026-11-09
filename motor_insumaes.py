import lee_config
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
APP_KEY = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY']
APP_SECRET = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET']
REFRESH_TOKEN = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN']
RUTA_NUBE_EXCEL = "/Compras L-Angel/Catalogo PortasHerramientas e Insertos.xlsx"

# ========================================================
# 2. EXPRESIONES REGULARES PRE-COMPILADAS (AHORRO DE RAM)
# ========================================================
P_HRC = re.compile(r'HRC\s*[-]?\s*(\d+)')
P_MT = re.compile(r'MT[A]?(\d+)[-\s/]*(\d*)')
P_MS = re.compile(r'MS(\d+)[-\s/]*(\d*)')
P_NT = re.compile(r'NT(\d+)')
P_BS = re.compile(r'\bBS(\d+)\b')
P_MM = re.compile(r'(\d+(?:[.,]\d+)?)\s*MM')
P_DIM_X = re.compile(r'(\d+(?:[.,]\d+)?)\s*[X*]\s*(\d+(?:[.,]\d+)?)')
P_BROCA_CIL = re.compile(r'BROCA CIL\s+(\S+)')
P_TECNICO = re.compile(r'[A-Za-z]')
P_NUM = re.compile(r'\d')

def normalizar_decimales(texto):
    texto = texto.replace(",", ".")
    return re.sub(r'(\d+)\.0(?!\d)', r'\1', texto)

def limpiar_web(tw):
    if not tw: return ""
    tw = normalizar_decimales(str(tw).upper().strip())
    tw = tw.replace("KLINGSPOR - ", "").replace("LAMA TRONZAR", "").strip()
    tw = tw.replace("HSSE 5%COBALTO", "HSSE 5%CO").replace("5%COBALTO", "5%CO")
    
    etiquetas_basura = [
        "(3 UNIDADES)", "(5 UNIDADES)", "(10 UNIDADES)", "(10UNIDADES)",
        "(10UN)", "(TRAPEZOIDAL)"
    ]
    for basura in etiquetas_basura:
        tw = tw.replace(basura, "")

    tw = re.sub(r'\(\d+MM\)', '', tw)
    tw = tw.replace("COLA DE MILANO ", "").replace("FRESA CON INSERTO/ARAÑA ", "").replace("FRESA INSERTO ", "")
    tw = tw.replace("PERNO ALLEN SCREW", "ALLEN SCREW").replace("PERNO PLUM SCREW", "PLUM SCREW").replace("PERNO CLAMP SCREW", "CLAMP SCREW")
    tw = tw.replace("BRIDA ACCESORIO PORTAHERRAMIENTA", "ACCESORIO").replace("PASADOR ML PARA PORTAHERRAMIENTA", "ACCESORIO").replace("LOCK PIN CTM (PASADOR PARA PORTAHERRAMIENTA)", "ACCESORIO LOCK PIN CTM")
    tw = re.sub(r'\s+', ' ', tw).strip()

    # --- MEJORA 1: BROCAS CILÍNDRICAS VARIABLES (HSS, HSSE Y EXTRA LARGA) ---
    tw = tw.replace("BROCAS CILINDRICAS", "BROCA CIL").replace("BROCA CILINDRICA", "BROCA CIL")
    tw = tw.replace("BROCAS DE CENTRO", "BROCA CENTRO")
    if "BROCA CIL" in tw:
        es_extra = "EXTRA LARGA" in tw
        tw_base = re.sub(r'\s+', ' ', tw.replace("EXTRA LARGA", "")).strip()
        m_var = re.search(r'^BROCA CIL\s+(HSS[E]?)\s+IZAR\s+(\d+(?:\.\d+)?(?:X\d+(?:\.\d+)?)?)\s*MM$', tw_base)
        if m_var:
            mat, med = m_var.group(1), m_var.group(2)
            if med == "0.9" and mat == "HSSE": mat = "HSS"
            tw = f"BROCA CIL {med} {mat} IZAR" + (" EXTRA LARGA" if es_extra else "")

    # --- MEJORA 2: TERRAJAS, CONOS, EXTENSORES, ACEROS, MACHOS Y LLAVES ---
    tw = re.sub(r'^TOMAS?\s+CONO\s+', '', tw)
    tw = re.sub(r'^TOMAS?\s+ISO\s+', '', tw)
    tw = tw.replace("EXTENSOR DE CONO", "EXTENSION C/M")
    tw = tw.replace("REDUCTOR CONO MORSE", "REDUCTOR C/M")
    tw = re.sub(r'^ACERO RAPIDO IZAR\s+(\S+)', r'ACERO TORNEAR \1 10%CO HSSE IZAR', tw)
    tw = re.sub(r'^LLAVES?\s+ESTRELLA\s+T\s+', 'LLAVE ', tw)
    tw = re.sub(r'^LLAVES?\s+ALLEN\s+L\s+', '', tw)

    if "TERRAJA" in tw:
        tw = re.sub(r'\s*X\s*', 'X', tw)
        tw = re.sub(r'^TERRAJA\s+METRICA\s+HSSE\s+5%CO\s+IZAR\s+(M\S+?)MM$', r'TERRAJA \1 HSSE 5%CO IZAR', tw)
        tw = re.sub(r'^TERRAJA\s+(UNF|UNC)\s+IZAR\s+(\S+)\s+(\d+)H$', r'TERRAJA \2X\3 \1 HSS IZAR', tw)
        tw = re.sub(r'^TERRAJA\s+(UNF|UNC)\s+IZAR\s+(\S+)\s+HSS$', r'TERRAJA \2 \1 HSS IZAR', tw)
        tw = re.sub(r'^TERRAJA\s+NPT\s+IZAR\s+(\S+?)MM$', r'TERRAJA \1 NPT HSS IZAR', tw)

    if "JUEGO DE MACHOS IZAR" in tw:
        tw = re.sub(r'^JUEGO DE MACHOS IZAR\s+(\S+?)MM$', r'JGO 3 MACHO \1MM HSS CO IZAR', tw)

    if "LIMA REPASADORA" in tw:
        if "METRICA" in tw: tw = "LIMA REPASADORA MM"
        elif "WITHWORT" in tw: tw = "LIMA REPASADORA WITHWORT"

    if "PLACA BASE" in tw and " PARA INSERTO" in tw:
        tw = tw.split(" PARA INSERTO")[0].strip()

    if "GJMATIC" in tw or "GJ2" in tw:
        tw = tw.replace("FLUIDO DE CORTE", "FLUIDO CORTE").replace("(TAPMATIC)", "").replace("(NUMERO 2)", "").replace("0.5L-1L", "")
        tw = tw.replace("GJMATIC", "GJ1 MATIC").replace("GJ2-MATIC", "GJ2 MATIC")
        tw = tw.replace("0.5 L", "1/2LT").replace("0.5L", "1/2LT")
        tw = tw.replace("1 L", "1LT").replace("1L", "1LT")
        tw = re.sub(r'\s+', ' ', tw).strip()

    if "FRESA" in tw:
        tw = re.sub(r'(\d+(?:\.\d+)?)\s*MM\s*-\s*T(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*MM', lambda m: f"D{m.group(1)}XT{m.group(2)}X{m.group(3)}MM", tw)
        tw = re.sub(r'(\d+(?:\.\d+)?)\s*MM\s*-\s*(\d+(?:\.\d+)?)\s*MM', lambda m: f"{m.group(1)} {m.group(2)}MM", tw)
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
    tl = normalizar_decimales(str(tl).upper().strip())
    tl = re.sub(r'^[IE]R\d+-\d+(?:\.\d+)?\s*\(TRAPEZ\)\s*', '', tl)
    tl = re.sub(r'^BLOCK\s+SMBB', 'SMBB', tl)
    tl = re.sub(r'\s*\(\d+\)', '', tl).replace("LAMA ", "").strip()
    tl = re.sub(r'BROCAS?\s+CON\s+INSERTO\s+N\s*°?\s*', 'ZD ', tl)
    tl = tl.replace('BROCA ZD', 'ZD').replace('BROCAS ZD', 'ZD')
    tl = re.sub(r'ZD\d*-(\d+(?:\.\d+)?)-.*', r'ZD \1', tl)

    if "BROCA CIL" in tl and "EXTRA LARGA" in tl:
        tl = re.sub(r'(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)X\d+(?:\.\d+)?\s*MM', r'\1X\2', tl)
    if tl.startswith("AKT") and " BAP" in tl:
        tl = tl.split(" BAP")[0].strip()
    if "TERRAJA" in tl:
        tl = re.sub(r'(M\S+?)MM\b', r'\1', tl)
    if "CUCHILLA REBARBADO" in tl and " IZAR" in tl:
        tl = tl.split(" IZAR")[0].replace("(10UN)", "").strip()

    diccionario_local = {
        "TUNGS ": "TUNGSTENO ", "TUNGS.": "TUNGSTENO ", "INOX": "INOXIDABLE",
        "ALUM": "ALUMINIO", "CONVEXA": "RADIO INTERIOR", "ROT PLATO": "ROTATIVO PLATO"
    }
    for corto, largo in diccionario_local.items():
        tl = tl.replace(corto, largo)
    return re.sub(r'\s+', ' ', tl).strip()

def calcular_similitud_fast(tw, tl):
    if not tw or not tl: return 0.0

    if "BROCA CIL" in tw or "BROCA CIL" in tl:
        if ("BROCA CIL" in tw) != ("BROCA CIL" in tl): return 0.0
        if ("EXTRA LARGA" in tw) != ("EXTRA LARGA" in tl): return 0.0
        if ("HSSE" in tw) != ("HSSE" in tl): return 0.0
        mb_w, mb_l = P_BROCA_CIL.search(tw), P_BROCA_CIL.search(tl)
        if mb_w and mb_l and mb_w.group(1) != mb_l.group(1): return 0.0

    hrc_web, hrc_local = P_HRC.search(tw), P_HRC.search(tl)
    if hrc_web and hrc_local and hrc_web.group(1) != hrc_local.group(1): return 0.0

    mt_web, mt_local = P_MT.search(tw), P_MT.search(tl)
    if mt_web and mt_local:
        if mt_web.group(1) != mt_local.group(1) or mt_web.group(2) != mt_local.group(2): return 0.0

    ms_web, ms_local = P_MS.search(tw), P_MS.search(tl)
    if ms_web and ms_local:
        if ms_web.group(1) != ms_local.group(1) or ms_web.group(2) != ms_local.group(2): return 0.0

    nt_web, nt_local = P_NT.search(tw), P_NT.search(tl)
    if nt_web and nt_local and nt_web.group(1) != nt_local.group(1): return 0.0

    bs_web, bs_local = P_BS.search(tw), P_BS.search(tl)
    if bs_web and bs_local and bs_web.group(1) != bs_local.group(1): return 0.0

    dx_web, dx_local = P_DIM_X.search(tw), P_DIM_X.search(tl)
    if dx_web and dx_local:
        if dx_web.group(1) != dx_local.group(1) or dx_web.group(2) != dx_local.group(2): return 0.0

    mm_web, mm_local = P_MM.search(tw), P_MM.search(tl)
    if mm_web and mm_local:
        try:
            if float(mm_web.group(1)) != float(mm_local.group(1)): return 0.0
        except ValueError: pass

    palabras_w, palabras_l = tw.split(), tl.split()
    if palabras_w and palabras_l:
        cw, cl = palabras_w[0], palabras_l[0]
        es_codigo_tecnico = lambda word: bool(P_TECNICO.search(word)) and bool(P_NUM.search(word)) and len(word) >= 4
        if es_codigo_tecnico(cw) and es_codigo_tecnico(cl):
            if cw.replace("-M", "") != cl.replace("-M", ""): return 0.0

    ratio = SequenceMatcher(None, tw, tl).ratio()
    if "IZAR" in tw and "IZAR" in tl:
        ratio = min(1.0, ratio + 0.03)
    elif ("IZAR" in tw) != ("IZAR" in tl) and "BROCA CENTRO" in tw:
        ratio -= 0.15
    return ratio

def generar_auditoria_cloud():
    archivo_web = "WEB_INSUMAES.xlsx"
    archivo_reporte = "AUDITORIA_PRE_SYNC.xlsx"

    print("=" * 80)
    print(" ☁️ CEREBRO AUDITOR INSUMAES (MODO PILOTO AUTOMÁTICO - V2 POTENCIADO)")
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
    elif 'STOCK_LOCAL' not in df_local.columns:
        df_local['STOCK_LOCAL'] = 0

    if 'PRECIO' in df_local.columns:
        df_local['PRECIO'] = pd.to_numeric(df_local['PRECIO'], errors='coerce').fillna(0).round().astype(int)
        df_local = df_local.rename(columns={'PRECIO': 'PRECIO_LOCAL'})
    elif 'PRECIO_LOCAL' not in df_local.columns:
        df_local['PRECIO_LOCAL'] = 0

    df_local['SKU'] = df_local['SKU'].fillna('').astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.upper()
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
    mapa_limpio_local = {}

    for idx, fila in dic_local.items():
        fila['N_LOC_MAYUS'] = str(fila['NOMBRE']).upper()
        fila['TEXTO_LIMPIO'] = limpiar_local(fila['N_LOC_MAYUS'])
        fila['ES_JUEGO'] = any(w in fila['N_LOC_MAYUS'] for w in ["JGO", "JUEGO", "MALETA", "SET"])
        if fila['TEXTO_LIMPIO'] and fila['TEXTO_LIMPIO'] not in mapa_limpio_local:
            mapa_limpio_local[fila['TEXTO_LIMPIO']] = idx

    reporte_auditoria = []
    UMBRAL_SIMILITUD = 0.75
    local_indices_matcheados = set()
    total_web = len(dic_web)

    print(f"🔍 Analizando {total_web} productos (Motor Warp Fase 2 + Mejoras Variables)...\n")

    for idx, row_web in enumerate(dic_web):
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
            es_juego_web = any(w in nombre_web for w in ["JGO", "JUEGO", "MALETA", "SET"])

            if tw_limpio in mapa_limpio_local:
                idx_local_encontrado = mapa_limpio_local[tw_limpio]
                f = dic_local[idx_local_encontrado]
                match_tipo, nombre_local_match, sku_local_match, match_encontrado = "🔵 MATCH DETECTIVE", f['NOMBRE'], f['SKU'], True
                precio_local, stock_local = f['PRECIO_LOCAL'], f['STOCK_LOCAL']
            else:
                mejor_similitud, mejor_idx = 0.0, None
                for idx_loc, f in dic_local.items():
                    if es_juego_web != f['ES_JUEGO']: continue
                    sim = calcular_similitud_fast(tw_limpio, f['TEXTO_LIMPIO'])
                    if sim > mejor_similitud:
                        mejor_similitud, mejor_idx = sim, idx_loc

                if mejor_similitud >= UMBRAL_SIMILITUD:
                    idx_local_encontrado, match_encontrado = mejor_idx, True
                    f = dic_local[idx_local_encontrado]
                    match_tipo, nombre_local_match, sku_local_match = "🔵 MATCH DETECTIVE", f['NOMBRE'], f['SKU']
                    precio_local, stock_local = f['PRECIO_LOCAL'], f['STOCK_LOCAL']

        varianza_num, stock_a_inyectar = 0.0, 0
        if match_encontrado:
            local_indices_matcheados.add(idx_local_encontrado)
            match_unidades = re.search(r'(?:\(|PACK\s+)(\d+)\s*(?:UNIDADES|UN)\)?', nombre_web)
            if match_unidades and "JUEGO" not in nombre_web and "JGO" not in nombre_web:
                multiplicador = int(match_unidades.group(1))
                precio_local *= multiplicador
                stock_local //= multiplicador

            _col_w = float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 50) or 50) / 100.0; stock_a_inyectar = math.ceil(stock_local * _col_w)
            if precio_web > 0 and precio_local > 0:
                varianza_num = abs(precio_web - precio_local) / precio_local

            if precio_local <= 0 and stock_a_inyectar > 0: accion_requerida = "🚨 SIN PRECIO EN EXCEL"
            elif varianza_num >= ((float(lee_config.obtener_valor('LIMITE_CORTAFUEGOS', 40) or 0) / 100.0) if float(lee_config.obtener_valor('LIMITE_CORTAFUEGOS', 40) or 0) > 0 else 999.0): accion_requerida = "🚨 ALERTA DE PRECIO"
            elif stock_web != stock_a_inyectar or precio_web != precio_local: accion_requerida = "⚠️ ACTUALIZAR WEB"
            else: accion_requerida = "✅ AL DÍA"
        else:
            accion_requerida = "NINGUNA"

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
                'STOCK WEB': 0, 'STOCK LOCAL (Nuevo)': math.ceil(stock_real * (float(lee_config.obtener_valor('PORCENTAJE_COLCHON', 30) or 30) / 100.0)), 'STOCK FÍSICO (Real)': stock_real,
                'PRECIO WEB': 0, 'PRECIO LOCAL (Nuevo)': f['PRECIO_LOCAL'],
                'VARIANZA': '0.0%', 'ID_WOO': ""
            })

    _tmp_rep = f'{archivo_reporte}.tmp.{os.getpid()}.xlsx'; pd.DataFrame(reporte_auditoria).to_excel(_tmp_rep, index=False, engine='openpyxl'); os.replace(_tmp_rep, archivo_reporte)

    print("\n" + "=" * 80)
    print(" 📊 REPORTE DE SALUD DEL CATÁLOGO INSUMAES")
    print(f" 📦 Local: {len(dic_local)} | 🌐 Web: {total_web} | 🔗 Matches: {len(local_indices_matcheados)}")
    print("=" * 80)

if __name__ == "__main__":
    generar_auditoria_cloud()
