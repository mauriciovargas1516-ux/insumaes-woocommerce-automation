import os
import json
import re
import requests
import mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from collections import defaultdict
import platform
import subprocess
import hashlib  
import time
import sys
import concurrent.futures
import shutil
from datetime import datetime
from difflib import SequenceMatcher

# ==============================================================================
# --- AUTO-INSTALACIÓN DE LIBRERÍAS (Blindaje de entorno) ---
# ==============================================================================
def instalar_dependencias():
    librerias = {
        "woocommerce": "WooCommerce",
        "docx": "python-docx",
        "bs4": "beautifulsoup4",
        "requests": "requests",
        "tqdm": "tqdm"
    }
    for modulo, paquete in librerias.items():
        try:
            __import__(modulo)
        except ImportError:
            print(f"Instalando librería necesaria: {paquete}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

instalar_dependencias()

from woocommerce import API
from docx import Document
from bs4 import BeautifulSoup
from tqdm import tqdm

# ==============================================================================
# 1. CREDENCIALES DE ACCESO Y CONFIGURACIÓN COMPARTIDA
# ==============================================================================
URL_TIENDA = "https://www.tu-tienda.cl/" 
CONSUMER_KEY = "TU_CONSUMER_KEY_AQUI"
CONSUMER_SECRET = "TU_CONSUMER_SECRET_AQUI"

WP_USER = "tu_correo@gmail.com"
WP_APP_PASSWORD = "TU_PASSWORD_DE_APLICACION_AQUI"
URL_API_MEDIOS = f"{URL_TIENDA}wp-json/wp/v2/media"

try:
    wcapi = API(
        url=URL_TIENDA,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        version="wc/v3",
        timeout=120
    )
except Exception as e:
    print(f"[ERROR CRÍTICO] Error al conectar con WooCommerce: {e}")
    exit()


# ==============================================================================
# HERRAMIENTA 1: SINCRONIZADOR MAESTRO DE PRODUCTOS
# ==============================================================================
REGLAS_CATEGORIAS = {
    "fresa": 45, "tungsteno": 102, "inserto": 12, "escuadra": 88,
    "pie de metro": 90, "calibre": 90, "micrometro": 92, "base magnetica": 105,
    "dasqua": 200, "portaherramienta": 33, "bloque en v": 110,
    "block v": 110, "mesa de granito": 115
}

def analizar_categoria_inteligente(texto_titulo, id_categoria_lote):
    texto_completo = texto_titulo.lower()
    categorias_assigned = []
    reglas_activadas = []
    for palabra_clave, id_cat in REGLAS_CATEGORIAS.items():
        if palabra_clave in texto_completo:
            if id_cat not in categorias_assigned:
                categorias_assigned.append(id_cat)
                reglas_activadas.append(palabra_clave)
    if not categorias_assigned and id_categoria_lote:
        categorias_assigned.append(id_categoria_lote)
        reglas_activadas.append("Categoría Manual (Respaldo)")
    return categorias_assigned, reglas_activadas

def mostrar_arbol_categorias():
    print("\n" + "=" * 70)
    print(" 🔍 MAPA COMPLETO Y MULTINIVEL DE CATEGORÍAS EN INSUMAES")
    print("=" * 70)
    todas_las_categorias = []
    pagina = 1
    try:
        while True:
            respuesta_raw = wcapi.get("products/categories", params={"per_page": 100, "page": pagina})
            texto_limpio = respuesta_raw.text.replace('\ufeff', '').strip()
            respuesta = json.loads(texto_limpio)
            if not respuesta or not isinstance(respuesta, list) or "code" in respuesta: break
            todas_las_categorias.extend(respuesta)
            if len(respuesta) < 100: break 
            pagina += 1
        arbol_logico = defaultdict(list)
        for cat in todas_las_categorias:
            arbol_logico[cat["parent"]].append(cat)
        def dibujar_rama(parent_id, nivel=0):
            categorias_ordenadas = sorted(arbol_logico[parent_id], key=lambda x: x["name"])
            for cat in categorias_ordenadas:
                id_actual = cat["id"]
                nombre_actual = cat["name"]
                if nivel == 0:
                    print(f"📁 {nombre_actual.upper()} (ID: {id_actual})")
                else:
                    print(f"{'   ' * nivel}└── 📄 {nombre_actual} (ID: {id_actual})")
                if id_actual in arbol_logico:
                    dibujar_rama(id_actual, nivel + 1)
        dibujar_rama(0)
        print("=" * 70 + "\n")
        return todas_las_categorias
    except Exception as e:
        print(f"[ALERTA] Error al procesar el mapa: {e}\n")
        return []

def gestionar_categoria_interactiva(categorias_existentes, usar_ia):
    root = tk.Tk()
    root.withdraw()
    mensaje = "ID o Nombre de categoría de RESPALDO:" if usar_ia else "ID o Nombre de la categoría OBLIGATORIA:"
    entrada = simpledialog.askstring("Asignación de Categoría", mensaje)
    if not entrada or not entrada.strip(): return None
    entrada = entrada.strip()
    if entrada.isdigit():
        id_buscado = int(entrada)
        for cat in categorias_existentes:
            if cat["id"] == id_buscado: return cat["id"]
        messagebox.showerror("Error", f"El ID '{id_buscado}' no existe.")
        return None
    for cat in categorias_existentes:
        if cat["name"].lower() == entrada.lower(): return cat["id"]
    if messagebox.askyesno("Categoría Inexistente", f"La categoría '{entrada}' no existe.\n\n¿Deseas crearla?"):
        parent_str = simpledialog.askstring("Nivel de Categoría", f"Si '{entrada}' es SUBCATEGORÍA, escribe el Padre.\n(Deja en blanco si será Principal):")
        payload_nueva_cat = {"name": entrada}
        if parent_str and parent_str.strip():
            parent_input = parent_str.strip()
            parent_id = None
            if parent_input.isdigit():
                parent_id = int(parent_input)
            else:
                for cat in categorias_existentes:
                    if cat["name"].lower() == parent_input.lower():
                        parent_id = cat["id"]
                        break
                if not parent_id:
                    if messagebox.askyesno("Padre Inexistente", f"El padre '{parent_input}' no existe.\n¿Crearlo?"):
                        try:
                            nuevo_padre = wcapi.post("products/categories", {"name": parent_input}).json()
                            parent_id = nuevo_padre["id"]
                            categorias_existentes.append(nuevo_padre)
                        except Exception as e:
                            messagebox.showerror("Error", f"Fallo al crear Padre: {e}")
                            return None
                    else: return None
            if parent_id: payload_nueva_cat["parent"] = parent_id
        try:
            nueva_cat = wcapi.post("products/categories", payload_nueva_cat).json()
            messagebox.showinfo("Éxito", f"Categoría '{entrada}' creada (ID: {nueva_cat['id']})")
            return nueva_cat["id"]
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al crear categoría: {e}")
            return None
    return None

def solicitar_prefijo_sku():
    root = tk.Tk()
    root.withdraw()
    prefijo = simpledialog.askstring("Prefijos", "¿Inyectar prefijo a los SKUs? (Deja en blanco para original):")
    return prefijo.strip() if prefijo and prefijo.strip() else ""

def subir_imagen_a_wordpress(ruta_imagen):
    nombre_archivo = os.path.basename(ruta_imagen)
    tipo_mime, _ = mimetypes.guess_type(ruta_imagen)
    if not tipo_mime: tipo_mime = 'image/jpeg' 
    headers = {'Content-Disposition': f'attachment; filename="{nombre_archivo}"', 'Content-Type': tipo_mime}
    try:
        with open(ruta_imagen, 'rb') as imagen:
            respuesta = requests.post(URL_API_MEDIOS, headers=headers, data=imagen, auth=(WP_USER, WP_APP_PASSWORD), timeout=120)
            if respuesta.status_code == 201: return respuesta.json().get('id')
            else: return None
    except Exception: return None

def ejecutor_sincronizador_maestro():
    root = tk.Tk()
    root.withdraw()
    usar_ia = messagebox.askyesno("Modo", "🤖 ¿Activar IA de Auto-asignación?")
    publicar_directo = messagebox.askyesno("Publicación", "📢 ¿PUBLICAR inmediatamente?")
    estandarizar_fotos = messagebox.askyesno("Imágenes", "📸 ¿RENOMBRAR imágenes automáticamente?")
    usar_radar = messagebox.askyesno("Radar", "♻️ ¿Enlazar fotos repetidas (MD5)?")
    categorias_web = mostrar_arbol_categorias()
    id_categoria_final = gestionar_categoria_interactiva(categorias_web, usar_ia)
    if not usar_ia and id_categoria_final is None: return
    prefijo_sku = solicitar_prefijo_sku()
    carpeta_madre = filedialog.askdirectory(title="Selecciona la Carpeta Madre")
    if not carpeta_madre: return
    subcarpetas = [n for n in os.listdir(carpeta_madre) if os.path.isdir(os.path.join(carpeta_madre, n))]
    creados, actualizados, errores = 0, 0, 0
    estado_texto = "PUBLICADOS" if publicar_directo else "BORRADORES"
    registro_txt = []
    def loguear(mensaje): print(mensaje); registro_txt.append(mensaje)
    ruta_md5 = "registro_fotos_insumaes.json"
    registro_md5 = json.load(open(ruta_md5, "r", encoding="utf-8-sig")) if os.path.exists(ruta_md5) else {}
    loguear("\n" + "=" * 70); loguear(f" 🚀 INICIANDO TRANSMISIÓN A INSUMAES"); loguear("=" * 70)
    for index, nombre_carpeta in enumerate(subcarpetas, 1):
        ruta_carpeta = os.path.join(carpeta_madre, nombre_carpeta)
        ruta_json = os.path.join(ruta_carpeta, f"{nombre_carpeta}.json")
        if os.path.exists(ruta_json):
            try: datos_locales = json.load(open(ruta_json, 'r', encoding='utf-8-sig'))
            except Exception as e: loguear(f"❌ Error JSON {nombre_carpeta}: {e}"); continue 
            titulo_web = nombre_carpeta.replace("A-R", "A/R").replace("a-r", "A/R").replace("A-C", "A/C").replace("a-c", "A/C")
            if any(p in titulo_web.lower() for p in ["acero rapido", "acero rápido", "hss", "cobalto", "pulg"]):
                titulo_web = re.sub(r'(\d)-(\d)', r'\1/\2', titulo_web)
            titulo_web = titulo_web.replace(" PULG", '"').replace("PULG", '"')
            sku = f"{prefijo_sku}{re.sub(r'-+', '-', nombre_carpeta.replace(' ', '-').replace(',', '').replace('/', '').replace('(', '').replace(')', '')).strip('-')}"
            precio = datos_locales.get("precio_regular", datos_locales.get("precio_venta", 0))
            stock = datos_locales.get("stock_cantidad", datos_locales.get("stock", 0))
            loguear(f"\n[{index}/{len(subcarpetas)}] Procesando: '{titulo_web}'...")
            ids_cat = analizar_categoria_inteligente(titulo_web, id_categoria_final)[0] if usar_ia else ([id_categoria_final] if id_categoria_final else [])
            imagenes = sorted([i for i in os.listdir(ruta_carpeta) if i.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
            if estandarizar_fotos and imagenes:
                temp_nombres = []
                for i, img in enumerate(imagenes):
                    ruta_vieja, ext = os.path.join(ruta_carpeta, img), os.path.splitext(img)[1].lower()
                    ruta_temp = os.path.join(ruta_carpeta, f"__tmp_{i}{ext}")
                    os.rename(ruta_vieja, ruta_temp); temp_nombres.append((ruta_temp, ext))
                imagenes = [] 
                for i, (ruta_temp, ext) in enumerate(temp_nombres, 1):
                    nuevo_nombre = f"{sku}-{i}{ext}"
                    os.rename(ruta_temp, os.path.join(ruta_carpeta, nuevo_nombre)); imagenes.append(nuevo_nombre)
            ids_img = []
            producto_existe = len(wcapi.get("products", params={"sku": sku, "status": "any"}).json()) > 0
            if imagenes:
                for img in imagenes:
                    ruta_img = os.path.join(ruta_carpeta, img)
                    md5_foto = None
                    if usar_radar:
                        try:
                            hash_md5 = hashlib.md5()
                            with open(ruta_img, "rb") as f:
                                for trozo in iter(lambda: f.read(4096), b""): hash_md5.update(trozo)
                            md5_foto = hash_md5.hexdigest()
                        except: pass
                    if usar_radar and md5_foto and md5_foto in registro_md5: ids_img.append(registro_md5[md5_foto])
                    else:
                        id_subida = subir_imagen_a_wordpress(ruta_img)
                        if id_subida:
                            ids_img.append(id_subida)
                            if usar_radar and md5_foto: registro_md5[md5_foto] = id_subida
            payload = {
                "name": titulo_web, "type": "simple", "status": "publish" if publicar_directo else "draft", 
                "regular_price": str(precio), "description": datos_locales.get("descripcion", ""),
                "sku": sku, "manage_stock": True, "stock_quantity": stock,
                "stock_status": "instock" if int(stock) > 0 else "outofstock"
            }
            if ids_cat: payload["categories"] = [{"id": c} for c in ids_cat]
            if ids_img: payload["images"] = [{"id": img, "position": p} for p, img in enumerate(ids_img)]
            try:
                if producto_existe:
                    id_web = wcapi.get("products", params={"sku": sku, "status": "any"}).json()[0]["id"]
                    if wcapi.put(f"products/{id_web}", payload).status_code == 200: actualizados += 1; loguear("  -> [OK] Actualizado")
                    else: errores += 1
                else:
                    if wcapi.post("products", payload).status_code == 201: creados += 1; loguear("  -> [OK] Creado")
                    else: errores += 1
            except Exception as e: loguear(f"  -> [ERROR] {e}"); errores += 1
    if usar_radar: json.dump(registro_md5, open(ruta_md5, "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    informe = f"Finalizado.\nCreados: {creados}\nActualizados: {actualizados}\nErrores: {errores}"
    loguear("\n" + "=" * 70); loguear(informe)
    try: open(os.path.join(carpeta_madre, "Reporte_Sincronizacion.txt"), "w", encoding="utf-8").write("\n".join(registro_txt))
    except: pass
    messagebox.showinfo("Reporte", informe)


# ==============================================================================
# HERRAMIENTA 2: CONSTRUCTOR INTERACTIVO DE CATEGORÍAS
# ==============================================================================
def inyector_categorias():
    print("\n" + "=" * 60)
    print(" 🏗️  CONSTRUCTOR DE CATEGORÍAS MAESTRO ")
    print("=" * 60)
    print("📡 Descargando mapa actual...\n")
    categorias_web = {}
    pagina = 1
    while True:
        try:
            res = json.loads(wcapi.get("products/categories", params={"per_page": 100, "page": pagina}).text.strip('\ufeff'))
            if not res or "code" in res: break
            for cat in res: categorias_web[cat['id']] = cat
            if len(res) < 100: break
            pagina += 1
        except: break
    arbol = defaultdict(list)
    for cat in categorias_web.values(): arbol[cat['parent']].append(cat)
    def dibujar(parent_id, nivel=0):
        for cat in sorted(arbol[parent_id], key=lambda x: x["name"]):
            print(f"{'   ' * nivel}📁 {cat['name'].upper()}" if nivel==0 else f"{'   ' * nivel}└── 📄 {cat['name']} (ID: {cat['id']})")
            dibujar(cat['id'], nivel + 1)
    dibujar(0)
    while True:
        nombre = input("\n📝 Nombre de NUEVA categoría: ").strip()
        if not nombre: continue
        padre = input("👉 ID del Padre (0 si es principal): ").strip()
        try: padre_id = int(padre) if padre else 0
        except ValueError: print("❌ Número inválido."); continue
        try:
            res = json.loads(wcapi.post("products/categories", {"name": nombre, "parent": padre_id}).text.strip('\ufeff'))
            if "id" in res: print(f"✅ ¡Creada! ID: {res['id']}")
            else: print(f"❌ Error: {res.get('message', 'Desconocido')}")
        except Exception as e: print(f"❌ Error de API: {e}")
        if input("\n🔄 ¿Crear otra? (s/n): ").strip().lower() != 's': break


# ==============================================================================
# HERRAMIENTA 3: ENSAMBLADOR INTELIGENTE DE IMÁGENES
# ==============================================================================
def extraer_clave_inteligente(nombre_carpeta):
    nombre_upper = nombre_carpeta.upper()
    materiales_conocidos = ["PLASTICO Y ALUMINIO", "ACERO", "MADERA", "WIDIA", "CARBURO DE TUNGSTENO", "USO GENERAL"]
    for material in materiales_conocidos:
        if material in nombre_upper: return material 
    match_medida = re.search(r'(\d+(?:[.,]\d+)?)\s*MM', nombre_upper)
    if match_medida: return match_medida.group(1) 
    return None

def archivo_coincide_con_clave(nombre_archivo, clave_detectada, umbral=0.60):
    fn_norm = os.path.splitext(nombre_archivo)[0].upper().replace(',', '.')
    clave_norm = clave_detectada.upper().replace(',', '.')
    if clave_norm.isalpha() or " " in clave_norm:
        if clave_norm in fn_norm: return True
    else:
        if re.search(r'(?<![\d.])' + re.escape(clave_norm) + r'(?![\d.])', fn_norm, re.IGNORECASE): return True
    return SequenceMatcher(None, clave_norm, fn_norm).ratio() >= umbral

def ejecutar_ensamblador_inteligente():
    root = tk.Tk()
    root.withdraw()
    modo_bruto = messagebox.askyesno("Modo", "¿Activar MODO INYECCIÓN EN BRUTO?\nSÍ: Copia masiva\nNO: Cerebro Dual por Material/Medida")
    reemplazar_existentes = messagebox.askyesno("Reemplazo", "¿Sobrescribir si la foto ya existe?")
    purga_total = messagebox.askyesno("Purga", "¿ELIMINAR TODAS las imágenes previas en las carpetas destino antes de inyectar?")
    
    print("\n" + "=" * 80)
    print(f" 🚀 INICIANDO ENSAMBLADO INSUMAES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    fotos_purgadas_total, ext_validas = 0, ('.png', '.jpg', '.jpeg', '.webp')

    if modo_bruto:
        carpeta_fotos = filedialog.askdirectory(title="Fotos a Inyectar")
        carpeta_madre = filedialog.askdirectory(title="Carpeta Madre")
        if not carpeta_fotos or not carpeta_madre: return
        fotos = [f for f in os.listdir(carpeta_fotos) if f.lower().endswith(ext_validas)]
        con_json, inyectadas, omitidas = 0, 0, 0
        for raiz, _, archivos in os.walk(carpeta_madre):
            if any(f.lower().endswith('.json') for f in archivos):
                con_json += 1
                if purga_total:
                    for f in archivos:
                        if f.lower().endswith(ext_validas):
                            try: os.remove(os.path.join(raiz, f)); fotos_purgadas_total += 1
                            except: pass
                for foto in fotos:
                    ruta_final = os.path.join(raiz, foto)
                    if os.path.exists(ruta_final) and not reemplazar_existentes: omitidas += 1; continue
                    shutil.copy2(os.path.join(carpeta_fotos, foto), ruta_final); inyectadas += 1
                print(f"   ✅ [PROCESADO] -> {os.path.basename(raiz)}")
        messagebox.showinfo("Reporte", f"Bruto Finalizado\nCarpetas: {con_json}\nPurgadas: {fotos_purgadas_total}\nInyectadas: {inyectadas}\nOmitidas: {omitidas}")
        return

    carpeta_repetibles = filedialog.askdirectory(title="Imágenes Repetibles")
    carpeta_personalizadas = filedialog.askdirectory(title="Imágenes Personalizadas")
    carpeta_madre = filedialog.askdirectory(title="Carpeta Madre")
    if not (carpeta_repetibles and carpeta_personalizadas and carpeta_madre): return
    f_rep = [f for f in os.listdir(carpeta_repetibles) if f.lower().endswith(ext_validas)]
    f_per = [f for f in os.listdir(carpeta_personalizadas) if f.lower().endswith(ext_validas)]
    
    t_rep, t_per, t_omi = 0, 0, 0
    for subcarpeta in [d for d in os.listdir(carpeta_madre) if os.path.isdir(os.path.join(carpeta_madre, d))]:
        ruta_destino = os.path.join(carpeta_madre, subcarpeta)
        clave = extraer_clave_inteligente(subcarpeta)
        print(f"\n📁 {subcarpeta}")
        if not clave: print("   ├─ ⚠️ Sin clave detectada."); continue 
        
        if purga_total:
            for f in os.listdir(ruta_destino):
                if f.lower().endswith(ext_validas):
                    try: os.remove(os.path.join(ruta_destino, f)); fotos_purgadas_total += 1
                    except: pass
        if f_rep:
            for foto in f_rep:
                ruta_final = os.path.join(ruta_destino, foto)
                if os.path.exists(ruta_final) and not reemplazar_existentes: t_omi += 1; continue
                shutil.copy2(os.path.join(carpeta_repetibles, foto), ruta_final); t_rep += 1
        if f_per:
            match = False
            for foto_p in f_per:
                if archivo_coincide_con_clave(foto_p, clave):
                    ruta_final = os.path.join(ruta_destino, foto_p)
                    if os.path.exists(ruta_final) and not reemplazar_existentes: t_omi += 1; match = True; continue
                    shutil.copy2(os.path.join(carpeta_personalizadas, foto_p), ruta_final); t_per += 1; match = True
            if not match: print(f"   └─ ❌ [ALERTA] Sin similitud para '{clave}'.")
    messagebox.showinfo("Reporte", f"Inteligente Completado\nPurgadas: {fotos_purgadas_total}\nGenéricas: {t_rep}\nPersonalizadas: {t_per}")


# ==============================================================================
# HERRAMIENTA 4: SANITIZADOR DE IMÁGENES
# ==============================================================================
def eliminador_masivo_fotos():
    root = tk.Tk()
    root.withdraw()
    carpeta_madre = filedialog.askdirectory(title="Carpeta Madre para Limpiar Fotos")
    if not carpeta_madre: return
    
    adv = f"⚠️ CRÍTICO ⚠️\n\nEliminará imágenes en:\n{carpeta_madre}\nSOLO si hay un archivo .json en la carpeta.\n¿Continuar?"
    if not messagebox.askyesno("Confirmación", adv, icon='warning'): return
    
    print("\n" + "=" * 70)
    print(" 🧹 INICIANDO SANITIZADOR CONDICIONADO DE FOTOS")
    print("=" * 70)
    fotos_eliminadas, errores, carpetas_procesadas, carpetas_omitidas = 0, 0, 0, 0
    exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')

    for raiz, _, archivos in os.walk(carpeta_madre):
        if any(a.lower().endswith('.json') for a in archivos):
            carpetas_procesadas += 1
            print(f"📂 [JSON DETECTADO] Revisando: {raiz}")
            for archivo in archivos:
                if archivo.lower().endswith(exts):
                    try:
                        os.remove(os.path.join(raiz, archivo))
                        fotos_eliminadas += 1
                    except Exception as e: errores += 1; print(f"  ❌ Error {archivo}: {e}")
        else: carpetas_omitidas += 1
        
    resumen = f"Sanitización Completada\nCarpetas con JSON: {carpetas_procesadas}\nOmitidas: {carpetas_omitidas}\nFotos Eliminadas: {fotos_eliminadas}\nErrores: {errores}"
    print(f"\n{resumen}")
    messagebox.showinfo("Reporte Sanitizador", resumen)


# ==============================================================================
# HERRAMIENTA 5: SANITIZADOR DE WORDS
# ==============================================================================
def eliminador_masivo_words():
    root = tk.Tk()
    root.withdraw()
    carpeta_madre = filedialog.askdirectory(title="Carpeta Madre para Limpiar Words")
    if not carpeta_madre: return
    
    adv = f"⚠️ CRÍTICO ⚠️\n\nEliminará TODOS los archivos Word (.docx) en:\n{carpeta_madre}\n¿Seguro?"
    if not messagebox.askyesno("Confirmación", adv, icon='warning'): return
    
    print("\n" + "=" * 70)
    print(" 🧹 INICIANDO SANITIZADOR QUIRÚRGICO DE WORDS")
    print("=" * 70)
    eliminados, errores = 0, 0

    for raiz, _, archivos in os.walk(carpeta_madre):
        for archivo in archivos:
            if archivo.lower().endswith('.docx'):
                try:
                    os.remove(os.path.join(raiz, archivo))
                    eliminados += 1
                    print(f"🗑️ [ELIMINADO] -> {archivo}")
                except Exception as e: errores += 1; print(f"❌ Error {archivo}: {e}")
                
    res = f"Sanitización Completada.\nWords eliminados: {eliminados}\nErrores: {errores}"
    print(f"\n{res}")
    messagebox.showinfo("Reporte", res)


# ==============================================================================
# HERRAMIENTA 6: EXTRACCIÓN MAESTRA DE INSUMAES (MODO TURBO)
# ==============================================================================
def limpiar_nombre_carpeta(nombre): return re.sub(r'[<>:"/\\|?*]', '_', nombre).strip()
def limpiar_html(texto_html): return BeautifulSoup(texto_html, "html.parser").get_text(separator='\n').strip() if texto_html else "Sin descripción."

def ejecutor_respaldo_maestro():
    root = tk.Tk()
    root.withdraw()
    ruta_destino = filedialog.askdirectory(title="Carpeta para el respaldo")
    if not ruta_destino: return
    tiempo_inicio = time.time()
    stats = {"carpetas_creadas": 0, "jsons_generados": 0, "words_generados": 0, "fotos_descargadas": 0, "errores": 0}
    print("\n" + "=" * 75); print(" 🚀 INICIANDO EXTRACCIÓN MAESTRA (TURBO)"); print("=" * 75)
    
    cat_web, pag = {}, 1
    while True:
        res = json.loads(wcapi.get("products/categories", params={"per_page": 100, "page": pag}).text.strip('\ufeff'))
        if not res or "code" in res: break
        for c in res: cat_web[c['id']] = c
        if len(res) < 100: break
        pag += 1
        
    def get_ruta(id_cat):
        partes, actual = [], id_cat
        while actual != 0 and actual in cat_web:
            partes.insert(0, limpiar_nombre_carpeta(cat_web[actual]['name']))
            actual = cat_web[actual]['parent']
        return os.path.join(*partes) if partes else "Sin Categorizar"

    prod_web, pag = [], 1
    while True:
        res = json.loads(wcapi.get("products", params={"per_page": 100, "page": pag}).text.strip('\ufeff'))
        if not res or "code" in res: break
        prod_web.extend(res)
        if len(res) < 100: break
        pag += 1

    def procesar(p):
        s = {"carpetas_creadas": 0, "jsons_generados": 0, "words_generados": 0, "fotos_descargadas": 0, "errores": 0}
        nombre = limpiar_nombre_carpeta(p.get('name', ''))
        if not nombre: return s
        id_prin, max_p = 0, -1
        if p.get('categories'):
            for c in p['categories']:
                prof, actual = 0, c['id']
                while actual != 0 and actual in cat_web: prof += 1; actual = cat_web[actual]['parent']
                if prof > max_p: max_p, id_prin = prof, c['id']
        ruta = os.path.join(ruta_destino, get_ruta(id_prin), nombre)
        if not os.path.exists(ruta): os.makedirs(ruta, exist_ok=True); s["carpetas_creadas"] += 1
        
        r_json = os.path.join(ruta, f"{nombre}.json")
        if not os.path.exists(r_json):
            d = {"sku": p.get('sku', ''), "precio": p.get('regular_price', '0'), "stock": p.get('stock_quantity', 0), "desc": p.get('description', '')}
            with open(r_json, 'w', encoding='utf-8-sig') as f: json.dump(d, f, indent=4, ensure_ascii=False)
            s["jsons_generados"] += 1
            
        r_word = os.path.join(ruta, f"Descripcion - {nombre}.docx")
        if not os.path.exists(r_word):
            doc = Document(); doc.add_heading(p.get('name', ''), 0)
            doc.add_paragraph(limpiar_html(p.get('description', ''))); doc.save(r_word)
            s["words_generados"] += 1
            
        if p.get('images'):
            for i, img in enumerate(p['images'], 1):
                r_img = os.path.join(ruta, f"{nombre} - {i}.jpg")
                if not os.path.exists(r_img):
                    try:
                        resp = requests.get(img['src'], stream=True, timeout=15)
                        if resp.status_code == 200:
                            with open(r_img, 'wb') as f:
                                for c in resp.iter_content(1024): f.write(c)
                            s["fotos_descargadas"] += 1
                    except: s["errores"] += 1
        return s

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        resultados = list(tqdm(ex.map(procesar, prod_web), total=len(prod_web), desc="⚡ Clonando", unit="prod"))
    
    for r in resultados:
        for k in stats: stats[k] += r[k]
        
    m, s = divmod(time.time() - tiempo_inicio, 60)
    rep = f"FINALIZADO en {int(m)}m {int(s)}s\nProds: {len(prod_web)}\nCarpetas: {stats['carpetas_creadas']}\nFotos: {stats['fotos_descargadas']}"
    print(f"\n{rep}"); messagebox.showinfo("Éxito", rep)


# ==============================================================================
# HERRAMIENTA 7: REASIGNADOR OMNI-BUSCADOR DE CATEGORÍAS
# ==============================================================================
def reasignador_omni_buscador():
    print("\n" + "=" * 60)
    print(" 🚚 REASIGNADOR DEFINITIVO (SKU / NOMBRE) - INSUMAES ")
    print("=" * 60)
    print("📡 Descargando mapa actual de categorías desde el servidor...\n")
    
    categorias_web = {}
    pagina_cat = 1
    while True:
        try:
            res_raw = wcapi.get("products/categories", params={"per_page": 100, "page": pagina_cat})
            res = json.loads(res_raw.text.strip('\ufeff'))
            if not res or "code" in res: break
            for cat in res: categorias_web[cat['id']] = cat
            if len(res) < 100: break
            pagina_cat += 1
        except Exception: break

    arbol_logico = {}
    for cat_id, cat_data in categorias_web.items():
        padre = cat_data['parent']
        if padre not in arbol_logico: arbol_logico[padre] = []
        arbol_logico[padre].append(cat_data)

    def dibujar_rama(parent_id, nivel=0):
        if parent_id not in arbol_logico: return
        categorias_ordenadas = sorted(arbol_logico[parent_id], key=lambda x: x["name"])
        for cat in categorias_ordenadas:
            espaciado = "   " * nivel
            if nivel == 0:
                print(f"📁 {cat['name'].upper()} (ID: {cat['id']})")
            else:
                print(f"{espaciado}└── 📄 {cat['name']} (ID: {cat['id']})")
            dibujar_rama(cat['id'], nivel + 1)

    print("🌲 MAPA DE CATEGORÍAS ACTUALES:")
    print("-" * 60)
    dibujar_rama(0)
    print("-" * 60)
    print("💡 Tip 1: Revisa los IDs de arriba para asignar el 'Destino' correcto.")
    print("💡 Tip 2: Puedes ingresar SKUs o NOMBRES EXACTOS separados por barra vertical (|).\n")

    while True:
        items_input = input("\n📦 Ingresa SKUs o Nombres (o 'salir' para terminar): ").strip()
        if items_input.lower() == 'salir':
            print("👍 ¡Reasignador cerrado! Inventario actualizado.")
            break
        if not items_input: continue

        lista_items = [s.strip() for s in items_input.split('|')]
        print(f"✅ Se detectaron {len(lista_items)} productos para procesar.")

        nueva_cat_str = input("👉 ID de la NUEVA categoría (Destino) para TODO el lote: ").strip()
        try: nueva_cat_id = int(nueva_cat_str)
        except ValueError: print("❌ El ID de la categoría debe ser un número."); continue

        print("\n🚀 Iniciando traslado masivo inteligente...\n")
        
        for i, item in enumerate(lista_items, 1):
            print(f"[{i}/{len(lista_items)}] ⏳ Procesando '{item}'...")
            try:
                prod_id, nombre_confirmado = None, ""
                
                # INTENTO 1: Buscar como SKU
                res_raw = wcapi.get("products", params={"sku": item})
                productos_sku = json.loads(res_raw.text.strip('\ufeff'))
                
                if productos_sku:
                    prod_id = productos_sku[0]['id']
                    nombre_confirmado = productos_sku[0]['name']
                else:
                    # INTENTO 2: Buscar como Nombre Exacto
                    res_raw_nom = wcapi.get("products", params={"search": item})
                    productos_nom = json.loads(res_raw_nom.text.strip('\ufeff'))
                    for p in productos_nom:
                        if p['name'].strip().upper() == item.upper():
                            prod_id = p['id']
                            nombre_confirmado = p['name']
                            break

                if not prod_id:
                    print(f"   ❌ Ojo: No se encontró '{item}' ni por SKU ni por Nombre. Saltando.")
                    continue
                
                # EJECUTAR REASIGNACIÓN
                data_update = {"categories": [{"id": nueva_cat_id}]}
                update_raw = wcapi.put(f"products/{prod_id}", data_update)
                update_res = json.loads(update_raw.text.strip('\ufeff'))
                
                if "id" in update_res: print(f"   ✅ ¡Movido con éxito! ({nombre_confirmado})")
                else: print(f"   ❌ Error al actualizar: {update_res.get('message', 'Desconocido')}")
                    
            except Exception as e: print(f"   ❌ Error de conexión con este ítem: {e}")
            time.sleep(0.5)


# ==============================================================================
# AYUDA Y DOCUMENTACIÓN 
# ==============================================================================
def mostrar_ayuda():
    limpiar_pantalla()
    print("\n" + "="*70)
    print(" 📖 GUÍA RÁPIDA DE LA SUITE INSUMAES ")
    print("="*70)
    print("""
Aquí tienes la explicación detallada y sencilla de cada herramienta:

1. 🚀 Sincronizador Maestro (Productos, Imágenes e IA)
   ¿Para qué sirve?: Es tu motor de subida de productos a WooCommerce.
   ¿Cómo funciona?: Lee una carpeta con productos (archivos JSON y fotos). Sube todo a la tienda web, renombra las imágenes para que queden perfectas y usa Inteligencia Artificial para adivinar la categoría leyendo el título de la carpeta.

2. 🏗️ Constructor Interactivo de Categorías
   ¿Para qué sirve?: Crea categorías en tu tienda sin entrar a WordPress.
   ¿Cómo funciona?: Te dibuja un mapa visual con las categorías que ya tienes. Luego, te permite escribir el nombre de una nueva, decirle si tiene una categoría "padre" y la crea automáticamente en tu web.

3. 🧠 Ensamblador de Imágenes (Inteligente/Bruto)
   ¿Para qué sirve?: Reparte fotos locales en tus carpetas de forma automática.
   ¿Cómo funciona?:
   - Modo Bruto: Agarra un grupo de fotos y las pega en TODAS las carpetas.
   - Modo Inteligente: Analiza el nombre de la carpeta (ej: "10 MM" o "ACERO") y solo le pega la foto que hace match con esa medida o material.

4. 🧹 Sanitizador de Imágenes (Requiere .json)
   ¿Para qué sirve?: Borra fotos viejas para que puedas poner nuevas.
   ¿Cómo funciona?: Revisa todas tus carpetas, y SOLO SI encuentra un archivo .json adentro, borra todas las fotos. Es un sistema de seguridad para no borrar fotos por accidente.

5. 🗑️ Sanitizador de Archivos Word (.docx)
   ¿Para qué sirve?: Elimina las descripciones en formato Word.
   ¿Cómo funciona?: Entra a la carpeta madre que elijas y borra absolutamente todos los archivos .docx. Úsalo para limpiar espacio.

6. 💾 Extracción Maestra de Insumaes (Respaldo Turbo)
   ¿Para qué sirve?: Clona toda tu tienda web hacia tu computador.
   ¿Cómo funciona?: Descarga todo tu catálogo de internet súper rápido usando múltiples hilos. Recrea tus categorías como carpetas físicas en Windows, baja las fotos, crea un Word con las descripciones y un JSON con precios y stock.

7. 🚚 Reasignador Definitivo (Categorías)
   ¿Para qué sirve?: Mueve rápidamente un grupo de productos de una categoría a otra.
   ¿Cómo funciona?: Te muestra un mapa de las categorías web. Luego, te pide que escribas los SKU o nombres exactos de los productos (separados por un "|", por ejemplo: SKU1|SKU2). Finalmente, ingresas el ID de la nueva categoría y el sistema los reubicará automáticamente.
    """)
    print("="*70)


# ==============================================================================
# MENÚ PRINCIPAL
# ==============================================================================
def limpiar_pantalla(): os.system('cls' if os.name == 'nt' else 'clear')

def menu_principal():
    while True:
        limpiar_pantalla()
        print("\n" + "="*70)
        print(" 🛠️  SUITE MAESTRA INSUMAES - MENÚ PRINCIPAL V4  🛠️")
        print("="*70)
        print("  1. 🚀 Sincronizador Maestro (Productos, Imágenes e IA)")
        print("  2. 🏗️ Constructor Interactivo de Categorías")
        print("  3. 🧠 Ensamblador de Imágenes (Inteligente/Bruto)")
        print("  4. 🧹 Sanitizador de Imágenes (Requiere .json)")
        print("  5. 🗑️ Sanitizador de Archivos Word (.docx)")
        print("  6. 💾 Extracción Maestra de Insumaes (Respaldo Turbo)")
        print("  7. 🚚 Reasignador Definitivo (Categorías)")
        print("  8. ℹ️  Ayuda (¿Qué hace cada herramienta?)")
        print("  9. ❌ Salir")
        print("="*70)
        
        opcion = input("👉 Selecciona la herramienta que deseas usar (1-9): ").strip()
        
        if opcion == '1': ejecutor_sincronizador_maestro(); input("\nPresiona Enter para volver...")
        elif opcion == '2': inyector_categorias(); input("\nPresiona Enter para volver...")
        elif opcion == '3': ejecutar_ensamblador_inteligente(); input("\nPresiona Enter para volver...")
        elif opcion == '4': eliminador_masivo_fotos(); input("\nPresiona Enter para volver...")
        elif opcion == '5': eliminador_masivo_words(); input("\nPresiona Enter para volver...")
        elif opcion == '6': ejecutor_respaldo_maestro(); input("\nPresiona Enter para volver...")
        elif opcion == '7': reasignador_omni_buscador(); input("\nPresiona Enter para volver...")
        elif opcion == '8': mostrar_ayuda(); input("\nPresiona Enter para volver...")
        elif opcion == '9': print("\n👋 ¡Cerrando la Suite Insumaes! Que tengas un excelente día.\n"); break
        else: print("\n⚠️ Opción no válida. Por favor elige un número del 1 al 9."); time.sleep(2)

if __name__ == "__main__":
    menu_principal()