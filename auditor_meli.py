import json
import io as _io
class _B(_io.BytesIO):
 def __init__(s,b=b''):
  super().__init__(b)
  if len(b)>50000: open('/tmp/catalogo_cache.xlsx','wb').write(b)
_io.BytesIO=_B
import lee_config
import os
import io
import sys
import time
import glob
import re
import math
import unicodedata
import dropbox
import pandas as pd
import numpy as np

APP_KEY = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_KEY']
APP_SECRET = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_APP_SECRET']
REFRESH_TOKEN = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['DROPBOX_REFRESH_TOKEN']

dbx = dropbox.Dropbox(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    oauth2_refresh_token=REFRESH_TOKEN
)
RUTA_EXCEL = "/Compras L-Angel/Catalogo PortasHerramientas e Insertos.xlsx"

def quitar_acentos(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')

def norm_text(s):
    t = quitar_acentos(str(s).upper())
    t = t.replace("FLUIDO DE CORTE TAPMATIC N°1", "FLUIDO CORTE GJ1 MATIC 1LT").replace("GJMATIC", "GJ1 MATIC")
    t = re.sub(r'(\d+),(\d+)', r'\1.\2', t)
    t = re.sub(r'\b(\d+)\.0\b', r'\1', t)
    t = re.sub(r'\b(\d+)\.0MM\b', r'\1MM', t)
    t = re.sub(r'\b(QFFD|QFGD)(\d{4}[RL]\d{2}-\d{2,3})H*(?=[A-Z]|\b)', r'\1\2H ', t)
    t = re.sub(r'\b(HSSE\s*[58]%\s*COBALTO|HSS\s*[58]%\s*COBALTO|HSS-CO|HSS\s+CO(?:\s+[58]%)?|HSS\s+COBALTO|[58]%\s*COBALTO|COBALTO\s*[58]%|CO[58]|[58]%\s*CO)\b', 'HSSE', t)
    t = re.sub(r'\bHSSE\s+HSSE\b', 'HSSE', t)
    t = re.sub(r'\b(ROTATIVOS?|ROTATIVA|ROT)\b', 'ROTATIVO', t)
    t = re.sub(r'\b(AJUSTE\s+FINO|AJUS\s+FINO?|AJUST\s+FINO?)\b', 'AJUSFINO', t)
    t = re.sub(r'\b(AJUSTE\s+PERNO|AJUST\s+PERNO?)\b', 'AJUSPERNO', t)
    t = re.sub(r'\b(RECUB\s+ESTANO)\b', 'RECUBESTANO', t)
    t = re.sub(r'\b8\s*[¨"\'´]\s*GRANO\b', '8X1 GRANO', t)
    t = re.sub(r'\bGRANO\s*(\d+)\b', r'GC\1 38A\1 A\1 G\1', t)
    t = re.sub(r'\bS50X-MTUNR22\b', 'S50X-MTURN22', t)
    t = re.sub(r'\bBOQUILLAS\b', 'BOQUILLA', t)
    t = re.sub(r'\bWITHWORTH\b', 'WHITWORTH', t)
    t = re.sub(r'\bJ\d{4}/(\d+-\d+MM)\b', r'\1', t)
    if 'MACHO' in t and 'GIRA' not in t and 'PORTA' not in t and 'ALARGADOR' not in t:
        t = re.sub(r'\bM(\d+(?:\.\d+)?X\d+(?:\.\d+)?)\b', r'M\1 \1', t)
    t = re.sub(r'\b(JUEGOS?|JGOS?|KITS?|SETS?|MALETAS?)\b', 'JGO', t)
    t = re.sub(r'\b(BROCAS?\s+CILINDRICAS?|BROCA\s+CIL)\b', 'BROCA CIL', t)
    t = re.sub(r'\b(BROCAS?\s+DE\s+CENTRO|BROCA\s+CENTRO)\b', 'BROCA CENTRO', t)
    t = re.sub(r'\b(FRESAS?\s+FRONTAL(?:ES)?)\b', 'FRESA FRONTAL', t)
    t = re.sub(r'\b(PORTABROCAS?|PORTA\s+BROCAS?)\b(?:\s+(?:M|LL))?\b', 'PORTABROCA', t)
    t = re.sub(r'\b(REFLACTOMETRO)\b', 'REFRACTOMETRO', t)
    t = re.sub(r'\b(PERNOS?\s+TORX)\b', 'PLUM SCREW', t)
    t = re.sub(r'\b(CONTRA\s+PUNTOS?|CONTRAPUNTOS?|CONTRA\s+PUNTAS?|C/P)\b', 'CONTRAPUNTO', t)
    t = re.sub(r'\b(PIE\s+DE\s+MET(?:RO)?|PIE\s+MET(?:RO)?|CALIBRADOR)\b', 'PIE METRO', t)
    t = re.sub(r'\b(MICROMETROS?|MICROMETO|MIC)\b', 'MICROMETRO', t)
    t = re.sub(r'\b(MAGNETICAS?|MAGNETICOS?|MAGENTICA|MAG)\b', 'MAGNETICA', t)
    t = re.sub(r'\b(ARTICULADAS?|ARTICULADOS?|ARTIC|ARTI)\b', 'ARTICULADA', t)
    t = re.sub(r'\b(DIGITALES|DIGITAL|DIG)\b', 'DIGITAL', t)
    t = re.sub(r'\b(COMPARADORES|COMPARADOR|COMP)\b', 'COMPARADOR', t)
    t = re.sub(r'\b(EXTERIORES|EXTERIOR|EXTERNOS?|EXTERNA|EXT)\b', 'EXTERIOR', t)
    t = re.sub(r'\b(INTERIORES|INTERIOR|INTERNOS?|INTERNA|INT)\b', 'INTERIOR', t)
    t = re.sub(r'\b(ANALOGICOS?|ANALOGO|ANALO)\b', 'ANALOGO', t)
    t = re.sub(r'\b(ESCALONADA\s+METAL|BROCA\s+ESCALONADA)\b', 'ESCALONADA', t)
    t = re.sub(r'\b(PLACAS?\s+BASE)\b', 'PLACA BASE', t)
    t = re.sub(r'\b(CUENTA\s+HILOS?)\b', 'CUENTA HILO', t)
    t = re.sub(r'\b(BOQUILLAS?)\b', 'BOQUILLA', t)
    t = re.sub(r'\b(BARRENADORES?|BARRENADOR)\b', 'BARRENADOR', t)
    if 'BOQUILLA' in t:
        t = re.sub(r'\b3\s*-\s*2[15]\s*(?:MM)?\b', 'OZ25', t)
    t = re.sub(r'(?:MM)?\s*(?:WITHWORTH|WHITWORTH)\b', ' WHITWORTH', t)
    t = re.sub(r'\b(METRICOS?|METRIC)\b', 'METRICO', t)
    t = re.sub(r'\b(LUBRAX|UTILE|PE)\b', 'BALDE', t)
    t = re.sub(r'\bS50X[\-\s]*MTUNR22', 'S50X-MTURN22 ', t)
    t = re.sub(r'\b(PIEDRA\s+PARA\s+ESMERIL)\b', 'PIEDRA T1', t)
    t = re.sub(r'\bGRANO\s*(\d+)\b', r'GC\1 A\1 G\1', t)
    t = re.sub(r'\bGJ2[\-\s]*MATIC\b', 'GJ2 MATIC', t)
    t = re.sub(r'\bAJUS(?:T|TE)?\s+FIN(?:O)?\b', 'AJUSTE FINO', t)
    t = re.sub(r'\bAJUS(?:T|TE)?\s+PERN(?:O)?\b', 'AJUSTE PERNO', t)
    t = re.sub(r'\b3203[\-\s]*25A\b', '0-25', t)
    t = re.sub(r'\bSERIE\s+3203\s+5\s*CM\b', '25-50', t)
    t = re.sub(r'\b2046S\b', '0.01 10', t)
    t = re.sub(r'\bSCKT1204AFTN\b', 'SEKT1204AFTN', t)
    t = re.sub(r'\bS50X[\-\s]*MTUNR22\b', 'S50X-MTURN22', t)
    t = re.sub(r'\b52\s*PC(?:S)?\b', '52', t)
    t = re.sub(r'\bCONO\s*5\b', 'MT5 MS5 D415', t)
    t = re.sub(r'\bGRANO\s*(\d+)\b', r'GC\1 A\1 38A\1 G\1', t)
    t = re.sub(r'\bMWLN2020K08\b', 'MWLNR2020K08', t)
    t = re.sub(r'\bWUTNR22\b', 'WTUNR22', t)
    t = re.sub(r'\bS32S[\-\s]*WTUNR22\b', 'S32U-WTUNR22', t)
    t = re.sub(r'\bSDAC([RL])(\d{4})F07\b', r'SDAC\1\2H07', t)
    t = re.sub(r'\bSNR0008M11\b', 'SNR0008K11', t)
    t = re.sub(r'\b27ERQ(\d{2})\-M\b', r'27ERQ\1', t)
    t = re.sub(r'\bWNMG080408\-MA\b', 'WNMG080408-AMM', t)
    t = re.sub(r'\bCCMT09T308\-MSF\b', 'CCMT09T308-ATM', t)
    t = re.sub(r'\b(QFFD|QFGD)(\d{4}[RL]\d{2}-\d{2,3})HH?\b', r'\1\2H', t)
    t = re.sub(r'\b(QFFD|QFGD)(\d{4}[RL]\d{2}-\d{2,3})\b', r'\1\2H', t)
    t = re.sub(r'\bISO\s*40\b', 'NT40', t)
    t = re.sub(r'\bISO\s*30\b', 'NT30', t)
    if 'CONTRAPUNTO' in t and not re.search(r'\bD41\d', t):
        t = re.sub(r'\bCONO\s*2\b', 'MT2 MS2 D412', t)
        t = re.sub(r'\bCONO\s*3\b', 'MT3 MS3 D413', t)
        t = re.sub(r'\bCONO\s*4\b', 'MT4 MS4 D414', t)
        t = re.sub(r'\bCONO\s*5\b', 'MT5 MS5 D415', t)
    else:
        t = re.sub(r'\bCONO\s*2\b', 'MT2 MS2', t)
        t = re.sub(r'\bCONO\s*3\b', 'MT3 MS3', t)
        t = re.sub(r'\bCONO\s*4\b', 'MT4 MS4', t)
        t = re.sub(r'\bCONO\s*5\b', 'MT5 MS5', t)
    t = re.sub(r'\bCONO\s*5\b', 'MT5 MS5', t)
    t = re.sub(r'\bKM\s*(\d{2})\b', r'KM\1', t)
    t = re.sub(r'\bSTM\s*(\d{2})\s*([RL](?:/[RL])?)\b', r'STM\1\2', t)
    t = re.sub(r'\bFS\s*764\b', 'FS764', t)
    t = re.sub(r'\(\s*PATA\s+LARGA\s+(\d+)\s*(?:MM)?\s*\)', r' P\1 ', t)
    t = re.sub(r'\bPATA\s+LARGA\s+(\d+)\s*(?:MM)?\b', r' P\1 ', t)
    t = re.sub(r'(\d+),(\d+)', r'\1.\2', t)
    t = re.sub(r'(\d+(?:\.\d+)?)\s*(?:MM)?\s*[X\*]\s*(\d+(?:\.\d+)?)', r'\1 MM X \2', t)
    t = re.sub(r'(\d+(?:\.\d+)?)\s*(?:MM)?\s*[X\*]\s*(\d+(?:\.\d+)?)', r'\1 MM X \2', t)
    t = re.sub(r'\b(\d+)\s+A\s+(\d+)\s*(?:MM)?\b', r'\1-\2', t)
    t = re.sub(r'[\(\)\[\],;:\'\"¨´/]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def get_tokens_and_nums(s):
    s_clean = re.sub(r'(\d+(?:\.\d+)?)\s*(?:MM|KG|CM|LT|L|UN|PCS|PC|PZA|PZAS)\b', r'\1', s)
    nums = re.findall(r'\d+(?:\.\d+)?', s_clean)
    words = set(re.findall(r'[A-Z0-9\.]+', s_clean))
    return words, nums

def ejecutar_ciclo():
    t_inicio = time.time()
    print("\n=================================================================")
    import lee_config
    for _k in ("SINCRONIZAR_WOOCOMMERCE","SINCRONIZAR_WOO_STOCK","SINCRONIZAR_WOO_PRECIOS","AUDITOR_MELI","SINCRONIZAR_MELI_STOCK","SINCRONIZAR_MELI_PRECIOS","PORCENTAJE_COLCHON","LIMITE_CORTAFUEGOS","MODO_TURBO_DELTA"): globals()[_k] = lee_config.obtener_valor(_k, globals().get(_k))
    print("⚡ MOTOR OMNICANAL TURBO — LECTURA INSTANTÁNEA EN RAM")
    print("=================================================================")

    _, res = dbx.files_download(RUTA_EXCEL)
    xl = pd.ExcelFile(io.BytesIO(res.content))

    config = {
        "SINCRONIZAR_WOOCOMMERCE": "SI",
        "AUDITOR_MELI": "SI",
        "SINCRONIZAR_MELI_STOCK": "NO",
        "SINCRONIZAR_MELI_PRECIOS": "NO",
        "PORCENTAJE_COLCHON": "50",
        "LIMITE_CORTAFUEGOS": "40",
        "MODO_TURBO_DELTA": "SI"
    }

    for s in xl.sheet_names:
        if s.strip().upper() == "CONTROL_BOT":
            df_ctrl = pd.read_excel(xl, sheet_name=s)
            if len(df_ctrl.columns) >= 2:
                for _, row in df_ctrl.iterrows():
                    k = str(row.iloc[0]).strip().upper()
                    v = str(row.iloc[1]).strip().upper()
                    if k in config and v not in ["NAN", "NONE", ""]:
                        config[k] = v
            break

    for k in list(config.keys()) + ["SINCRONIZAR_WOO_STOCK", "SINCRONIZAR_WOO_PRECIOS"]:
        val_p = lee_config.obtener_valor(k, None)
        if val_p is not None and str(val_p).strip() != "":
            config[k] = str(val_p).strip().upper()

    botones_panel = [
        ("[1] WOO_STOCK (Cantidades)", config.get("SINCRONIZAR_WOO_STOCK", config.get("SINCRONIZAR_WOOCOMMERCE", "SI")), "B"),
        ("[2] WOO_PRECIOS (Valores)", config.get("SINCRONIZAR_WOO_PRECIOS", config.get("SINCRONIZAR_WOOCOMMERCE", "SI")), "B"),
        ("[3] MODO_TURBO_DELTA (15s)", config.get("MODO_TURBO_DELTA", "SI"), "B"),
        ("[4] AUDITOR_MELI (Excel)", config.get("AUDITOR_MELI", "SI"), "B"),
        ("[5] MELI_STOCK (Cantidades)", config.get("SINCRONIZAR_MELI_STOCK", "NO"), "B"),
        ("[6] MELI_PRECIOS (Valores)", "🔒  BLOQUEADO (NO)", "L"),
        ("[7] PORCENTAJE_COLCHON", f"{config.get('PORCENTAJE_COLCHON', '50')}%", "C"),
        ("[8] LIMITE_CORTAFUEGOS", f"{config.get('LIMITE_CORTAFUEGOS', '40')}%", "F"),
    ]
    for etq, val, tb in botones_panel:
        ic = ("🟢  SI" if val == "SI" else "🔴  NO") if tb == "B" else (val if tb == "L" else (f"🔵  {val}" if tb == "C" else f"🛡️   {val}"))
        print(f"   {etq:28s} : {ic}")

    if config["AUDITOR_MELI"] != "SI":
        print(f"\n🛑 PAUSADO EN VIVO DESDE EXCEL (AUDITOR_MELI = NO) en {time.time()-t_inicio:.2f} seg.")
        return

    colchon_pct = float(re.sub(r'[^0-9.]', '', config["PORCENTAJE_COLCHON"]) or 50.0) / 100.0
    t_cruce = time.time()

    archivos_csv = sorted(glob.glob(os.path.expanduser("~/*.csv")), key=os.path.getmtime, reverse=True)
    archivo_meli = archivos_csv[0]
    df_woo = pd.read_excel(xl, sheet_name="INVENTARIO_WOO")

    df_cat = df_woo[df_woo['NOMBRE'].notna()].copy()
    df_cat['NOMBRE_STR'] = df_cat['NOMBRE'].astype(str).str.strip().str.upper()
    palabras_basura = ['', '0', '0.0', 'NAN', 'NONE', 'NOMBRE', 'ITEM CODE', 'DESCRIPCION', 'DESCRIPTION', 'ITEMS', 'MONTO USD', 'MONTO CLP', 'MONTO TOTAL']
    df_cat = df_cat[~df_cat['NOMBRE_STR'].isin(palabras_basura)].copy()
    df_cat['STOCK_FISICO'] = pd.to_numeric(df_cat['CANTIDAD'], errors='coerce').fillna(0).astype(int)
    df_cat['PRECIO_EXCEL'] = pd.to_numeric(df_cat['PRECIO'], errors='coerce').fillna(0).round().astype(int)
    df_cat['SKU_STR'] = df_cat['SKU'].fillna('').astype(str).str.strip().str.upper()
    df_cat.loc[df_cat['SKU_STR'].isin(['0', '0.0', 'NAN']), 'SKU_STR'] = ''
    df_cat = df_cat.sort_values(by=['STOCK_FISICO', 'PRECIO_EXCEL'], ascending=[False, False]).reset_index(drop=True)
    df_cat['NORM'] = df_cat['NOMBRE_STR'].apply(norm_text)
    df_cat = df_cat.drop_duplicates(subset=['NORM'], keep='first').reset_index(drop=True)

    # PRE-INDEXACIÓN EN RAM (Velocidad ERP: elimina iterrows lento)
    cat_records = []
    sku_map = {}
    brocas_cil = []
    for r in df_cat.to_dict('records'):
        enorm = r['NORM']
        ewords, enums = get_tokens_and_nums(enorm)
        r['WORDS'] = ewords
        r['NUMS'] = enums
        r['NORM_NOSPACE'] = re.sub(r'[\s\-]+', '', enorm)
        cat_records.append(r)
        if len(r['SKU_STR']) >= 4 and r['SKU_STR'] not in sku_map:
            sku_map[r['SKU_STR']] = r
        if 'BROCA CIL' in enorm:
            r['MAT'] = 'HSSE' if 'HSSE' in enorm else ('HSS' if 'HSS' in enorm else '')
            r['MEAS'] = float(enums[0]) if enums else -1.0
            brocas_cil.append(r)

    try:
        df_raw = pd.read_csv(archivo_meli, sep=";", dtype=str)
        if 'poly-component__title' not in df_raw.columns:
            df_raw = pd.read_csv(archivo_meli, sep=",", dtype=str)
    except Exception:
        df_raw = pd.read_csv(archivo_meli, dtype=str)

    def extract_item_id(url):
        if pd.isna(url): return None
        url = str(url)
        m_wid = re.search(r'wid=(MLC\d+)', url)
        m_p = re.search(r'/(?:p|up)/(MLC[U]?\d+)', url)
        m_item = re.search(r'(MLC-\d+)', url)
        return m_wid.group(1) if m_wid else (m_item.group(1).replace("-", "") if m_item else (m_p.group(1) if m_p else url))

    df_raw['ITEM_ID'] = df_raw['poly-component__title href'].apply(extract_item_id)
    df_meli = df_raw.drop_duplicates(subset=['ITEM_ID', 'poly-component__title']).copy().reset_index(drop=True)
    df_meli['PRECIO_MELI'] = pd.to_numeric(df_meli['andes-money-amount__fraction'].fillna('0').str.replace('.', '', regex=False).str.strip(), errors='coerce').fillna(0).astype(int)

    resultados = []
    for mrow in df_meli.to_dict('records'):
        title = str(mrow['poly-component__title'])
        t_upper = quitar_acentos(title.upper())
        t_norm = norm_text(title)
        matched_row = None
        match_type = "SIN MATCH"

        _ml_info = globals().get('_ML_API_SKUS')
        if _ml_info is None:
            _p_ml = os.path.expanduser('~/meli_api_items_full.json')
            _ml_info = json.load(open(_p_ml, 'r', encoding='utf-8')) if os.path.exists(_p_ml) else {}
            globals()['_ML_API_SKUS'] = _ml_info
        _sku_api = str(_ml_info.get(mrow['ITEM_ID'], {}).get('sku', '')).strip().upper()
        if _sku_api and _sku_api in sku_map:
            matched_row = sku_map[_sku_api]
            match_type = "1. Match SKU Exacto"
        if matched_row is None:
            for sku, erow in sku_map.items():
                if len(sku) >= 6 and sku in t_upper:
                    matched_row = erow
                    match_type = "1. Match SKU Exacto"
                    break

        if matched_row is None and 'BROCA CIL' in t_norm and 'IZAR' in t_norm and 'EXTRA LARGA' not in t_norm:
            mat = 'HSSE' if 'HSSE' in t_norm else ('HSS' if 'HSS' in t_norm else '')
            m_meas = re.search(r'(\d+(?:\.\d+)?)\s*MM', t_norm)
            if m_meas and mat:
                meas = float(m_meas.group(1))
                for erow in brocas_cil:
                    if erow['MAT'] == mat and erow['MEAS'] == meas and 'EXTRA LARGA' not in erow['NORM']:
                        matched_row = erow
                        match_type = "2. Código / Medida Exacta"
                        break

        if matched_row is None:
            cand_codes = re.findall(r'\b(?:[A-Z]{4}\d{2}[A-Z0-9]{2}\d{2}[A-Z0-9\-]*|[A-Z]{4}\d{4}[A-Z]{4}|[A-Z]{5}\d{4}[A-Z]\d{2}|[A-Z]{4}\d{4}[RL]\d{2}(?:-\d{2,3}H?)?|[A-Z]{2,5}\d{4}[A-Z]?\-\d+|[SWM][A-Z]{2,4}\d{4}[A-Z]\d{2}|S\d{2}[A-Z]-[A-Z]{4,5}\d{2}|C\d{2}[A-Z]-[A-Z]{5}-\d{2}|SBHA\d+\-\d+|AKT\d+[A-Z]?-\d+-\d+[A-Z]?|BAP\s*\d+R|SPB\d+|SP\s*\d{3}|MGMN\d+[A-Z\-]*|STM\d{2}[RL](?:/[RL])?|MT\d{4}|\d{2}[EI][RL][A-Z0-9\-]*|\d{2}NR[A-Z0-9\-]*|MS\d-[A-Z0-9]+|MT\d-[A-Z0-9]+|NT\d{2}-FMB\d{2}|KM\d{2}|FS764|D41\d[A-Z]?|295\d{3}|296\d{3}|334\d{3}|S50X-MTURN22|J\d{4}/\d+-\d+MM)\b', t_norm)
            for c in cand_codes:
                c_nospace = re.sub(r'[\s\-]+', '', c)
                for erow in cat_records:
                    if c.startswith('D41') and (not re.search(r'(?<![A-Z0-9])' + re.escape(c) + r'(?![A-Z0-9])', erow['NORM']) or ('JGO' in t_norm) != ('JGO' in erow['NORM'])):
                        continue
                    if c_nospace in erow['NORM_NOSPACE']:
                        matched_row = erow
                        match_type = "2. Código / Medida Exacta"
                        break
                if matched_row is not None:
                    break

        if matched_row is None:
            MARCAS = {"INSIZE", "DASQUA", "MITUTOYO", "IZAR", "ALPEN", "KLINGSPOR", "ISESA", "TOTEM", "ACCUD", "VERTEX", "KYOCERA", "SANDVIK", "BAHCO", "ROHM", "URANGA", "DORMER"}
            t_clean = re.sub(r'\b(TORNO|HERRAMIENTAS|HERRAMIENTA|MEDICION|INSERTO|PLACA|WIDIA|WIDEAS|TALADRO|MANDRIL|ACERO|INOXIDABLE|CARBONO|PROFESIONAL|INDUSTRIAL|PARA|DE|CON|EL|LA|LOS|LAS|EN|UNIDADES|UN|UNI|PIEZAS|MECANICO|SERIE|GRIS|CHINO|MAS|X|METAL|TOMA|CO5|PACK|MEDIDAS|CORTE)\b', ' ', t_norm)
            m_words, m_nums = get_tokens_and_nums(t_clean)
            m_brands = m_words & MARCAS
            equiv_map = {"75": "3", "100": "4", "150": "6", "200": "8", "300": "12", "500": "20", "600": "24", "1000": "40", "1500": "60", "2000": "80"}
            m_nums_first = {m_nums[0]} if m_nums else set()
            if ("PIE" in m_words and "METRO" in m_words) or "PLATO" in m_words:
                for n in list(m_nums[:2]):
                    m_nums_first.add(n)
                    if n in equiv_map: m_nums_first.add(equiv_map[n])
            best_score, best_erow = 0, None
            precio_meli = mrow['PRECIO_MELI']
            for erow in cat_records:
                e_words, e_nums = erow['WORDS'], erow['NUMS']
                if not e_words: continue
                e_brands = e_words & MARCAS
                if m_brands and m_brands != e_brands:
                    continue
                if "CENTRO" in m_words and not m_brands and e_brands:
                    continue
                if m_nums and e_nums:
                    if not any(mn in e_nums for mn in m_nums_first):
                        continue
                    if len(m_nums) >= 2 and re.search(r'\b' + re.escape(m_nums[0]) + r'\s*(?:MM)?\s*-\s*' + re.escape(m_nums[1]) + r'(?:MM|\b)', t_clean):
                        n1, n2 = m_nums[0], m_nums[1]
                        n2_eq = equiv_map.get(n2, n2)
                        if n1 != "0":
                            if not (n1 in e_nums and n2 in e_nums):
                                continue
                        else:
                            if not (n2 in e_nums or n2_eq in e_nums):
                                continue
                m_p = [w for w in m_words if re.match(r'^P\d{2,3}$', w)]
                if m_p and not any(pw in e_words for pw in m_p):
                    continue
                if ('JGO' in e_words) != ('JGO' in m_words) and 'PIE' not in m_words:
                    continue
                if ('RELOJ' in e_words) != ('RELOJ' in m_words):
                    continue
                if ('DIGITAL' in e_words) != ('DIGITAL' in m_words):
                    continue
                if any((fam in e_words) != (fam in m_words) for fam in ('BOQUILLA', 'BARRENADOR', 'CONTRAPUNTO', 'PORTABROCA')):
                    continue
                common = len(m_words & e_words)
                if (("PIE" in m_words and "METRO" in m_words) or "PLATO" in m_words) and any(equiv_map.get(mn) in e_nums for mn in m_nums[:2] if mn in equiv_map):
                    common += 1
                score = common / max(len(m_words), 1)
                diff_precio = abs(precio_meli - erow['PRECIO_EXCEL']) / max(precio_meli, 1) if precio_meli > 0 else 1.0
                bono_stock = 0.03 if (not m_brands and erow['STOCK_FISICO'] > 0) else 0.0
                score_ajustado = score + bono_stock - (0.15 * min(diff_precio, 1.0))
                if score >= 0.45 and common >= 2 and score_ajustado > best_score:
                    best_score, best_erow = score_ajustado, erow
            if best_erow is not None:
                matched_row = best_erow
                match_type = "3. Match Detective IA"

        es_juego = any(p in t_upper for p in ["JUEGO", "JGO", "KIT", "SET", "MALETA", "HOJAS", "PIEZAS"])
        mult = 1
        if not es_juego:
            m_pack = re.search(r'(?:\(\s*(?:PACK\s*)?(\d+)\s*(?:UNIDADES?|UN|UNI)\s*\)|\b(\d+)\s+UNIDADES\b)', t_upper)
            if m_pack:
                mult = int(m_pack.group(1) or m_pack.group(2))
            elif t_upper.startswith("PLACAS "):
                mult = 10

        if matched_row is not None:
            nombre_excel = str(matched_row['NOMBRE'])
            ya_es_pack_en_excel = bool(re.search(r'\(\s*\d+\s*(?:UNIDADES|UN|PIEZAS|PCS|PZA|PZAS)\s*\)', nombre_excel.upper()))
            if ya_es_pack_en_excel:
                mult = 1
            st_fisico = int(matched_row['STOCK_FISICO'])
            pr_excel = int(matched_row['PRECIO_EXCEL'])
            packs_disp = st_fisico // mult
            st_meli_colchon = math.ceil(packs_disp * colchon_pct) if packs_disp > 0 else 0
            pr_base_pack = pr_excel * mult
            estado = "🚨 PAUSAR EN MELI (SIN STOCK)" if packs_disp <= 0 else "✅ ACTIVO (STOCK SANO)"
            resultados.append({
                'ESTADO_MELI': estado, 'CODIGO_MLC': mrow['ITEM_ID'], 'TITULO_MELI': title,
                'PRECIO_MELI_ACTUAL': mrow['PRECIO_MELI'], 'TIPO_MATCH': match_type,
                'NOMBRE_EN_EXCEL': nombre_excel, 'STOCK_FISICO_BODEGA': st_fisico,
                'UNIDADES_POR_PACK': mult, 'PACKS_REALES_COMPLETOS': packs_disp,
                'STOCK_A_INYECTAR_MELI': st_meli_colchon, 'PRECIO_BASE_EXCEL_PACK': pr_base_pack
            })
        else:
            resultados.append({
                'ESTADO_MELI': "🔴 SIN PAREJA EN EXCEL", 'CODIGO_MLC': mrow['ITEM_ID'], 'TITULO_MELI': title,
                'PRECIO_MELI_ACTUAL': mrow['PRECIO_MELI'], 'TIPO_MATCH': "SIN MATCH",
                'NOMBRE_EN_EXCEL': "", 'STOCK_FISICO_BODEGA': np.nan, 'UNIDADES_POR_PACK': mult,
                'PACKS_REALES_COMPLETOS': np.nan, 'STOCK_A_INYECTAR_MELI': np.nan, 'PRECIO_BASE_EXCEL_PACK': np.nan
            })

    df_out = pd.DataFrame(resultados)
    archivo_salida = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
    df_out.to_excel(archivo_salida, index=False)
    import post_meli; post_meli.procesar(); _df_v = pd.read_excel(os.path.expanduser('~/AUDITORIA_MELI_INSUMAES.xlsx')); pausar = int(_df_v['Estado'].astype(str).str.contains('Pausar', na=False).sum()) if 'Estado' in _df_v.columns else pausar
    conectados = df_out[df_out['TIPO_MATCH'] != 'SIN MATCH']
    pausar = conectados[conectados['PACKS_REALES_COMPLETOS'] <= 0]
    activos = conectados[conectados['PACKS_REALES_COMPLETOS'] > 0]

    print(f"⚡ Cruce de 782 productos completado en: {time.time()-t_cruce:.2f} segundos!")
    print(f"📊 Conectados: {len(conectados)}/{len(df_out)} ({len(conectados)/len(df_out)*100:.1f}%) | ✅ Activos: {len(activos)} | 🚨 Pausar: {len(pausar)}")

    with open(archivo_salida, 'rb') as f:
        dbx.files_upload(f.read(), '/AUDITORIA_MELI_INSUMAES.xlsx', mode=dropbox.files.WriteMode.overwrite)
    print(f"✅ Subido a Dropbox. Tiempo total del ciclo: {time.time()-t_inicio:.2f} seg.")

if "--vigia" in sys.argv:
    print("👀 MODO VIGÍA EN VIVO ACTIVADO: Escuchando cambios en tu Excel de Dropbox cada 15 seg (Ctrl+C para salir)...")
    ultimo_rev = None
    while True:
        try:
            meta = dbx.files_get_metadata(RUTA_EXCEL)
            if meta.rev != ultimo_rev:
                ultimo_rev = meta.rev
                print(f"\n🔔 ¡Cambio detectado en tu Excel de Dropbox! (Rev: {ultimo_rev})")
                ejecutar_ciclo()
        except KeyboardInterrupt:
            print("\n👋 Modo Vigía detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ {e}")
        time.sleep(15)
else:
    ejecutar_ciclo()
