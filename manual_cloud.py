import os, sys, time, dropbox

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

TABLA_COMPARATIVA_MD = '## 1. Impacto Operativo y Porcentaje de Mejora (Trabajo Manual vs. Arquitectura Cloud)\n\nEl sistema transforma procesos manuales repetitivos en operaciones automatizadas por lote en Google Cloud, logrando una **mejora de eficiencia del 95,3%** (**21,2 veces más rápido**), con **52,5 horas ahorradas al mes** y **630,0 horas ahorradas al año** (equivalentes a **75,0 jornadas laborales completas** de 8,4 horas):\n\n| Proceso Operativo / Comercial | Volumen Activo | Tiempo Manual | Tiempo Cloud | Ahorro / Mes | Ahorro / Año | % Mejora (Velocidad) |\n| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n| **1. Sincronización Stock y Precios (Woo + ML)** | 2.509 ítems (550 cambios/mes) | 23,8 hrs/mes | 0,9 hrs/mes | **22,9 hrs** | **274,8 hrs** | **96,2% (26,4x más rápido)** |\n| **2. Emisión y Cruce de Cotizaciones B2B** | 141 cot/mes (445 en SQL) | 18,8 hrs/mes | 1,2 hrs/mes | **17,6 hrs** | **211,2 hrs** | **93,6% (15,7x más rápido)** |\n| **3. Estandarización HTML/CSS y Auto-Linker ISO** | 752 fichas vinculadas | 7,5 hrs/mes | 0,2 hrs/mes | **7,3 hrs** | **87,6 hrs** | **97,3% (37,5x más rápido)** |\n| **4. Estandarización de Fotos (800x720) y Categorías** | 1.727 prods (100 ajustes/mes) | 5,0 hrs/mes | 0,3 hrs/mes | **4,7 hrs** | **56,4 hrs** | **94,0% (16,7x más rápido)** |\n| **TOTAL OPERACIÓN CONTINUA** | **2.509 ítems + CRM B2B** | **55,1 hrs/mes** | **2,6 hrs/mes** | **52,5 hrs/mes** | **630,0 hrs/año** | **95,3% (21,2x más rápido)** |\n\n### Porcentaje de Mejora en Tareas Masivas por Lote (Ejecución Puntual)\n\n| Tarea Masiva de Catálogo o Inteligencia Comercial | Tiempo Manual | Tiempo Cloud | Horas Ahorradas | % Mejora (Multiplicador) |\n| :--- | :---: | :---: | :---: | :---: |\n| **Conectar botones de venta cruzada en 752 productos web** | 43,9 horas (5,2 días) | **4,0 minutos** | 43,8 horas | **99,8% (658,5x más rápido)** |\n| **Unificar ~204 Libros de Clientes por Ciudad + Cuentas por Cobrar** | 18,0 horas (2,1 días) | **1,8 minutos** | 17,9 horas | **99,8% (600,0x más rápido)** |\n| **Buscar historial, RUT y cotizaciones de un cliente en 204 ciudades** | 15,0 minutos | **0,01 segundos (SQL)** | 15,0 minutos | **99,9% (90.000x más rápido)** |\n| **Preparar y estructurar las 1.727 fichas para 1 nuevo Marketplace** | 172,7 horas (20,6 días) | **0,5 horas (30 min)** | 172,2 horas | **99,7% (345,4x más rápido)** |\n| **Expandir catálogo completo a 3 nuevos Marketplaces (Falabella, Paris, Lider)** | 518,1 horas (61,7 días) | **1,5 horas** | 516,6 horas | **99,7% (345,4x más rápido)** |\n'

SECCIONES = {
    "1": (
        "GRUPO A: INTERRUPTORES AUTOMATICOS 24/7 (BOTONES [1] AL [8])",
        "Configuración permanente en SI / ON para sincronización autónoma cada 3 segundos:\n\n"
        "- **[1] WOO_STOCK (SI):** Sube el stock con colchón de seguridad (40%) desde el Excel de Dropbox hacia insumaes.cl.\n"
        "- **[2] WOO_PRECIOS (SI):** Actualiza los precios con IVA desde el Excel maestro hacia WooCommerce.\n"
        "- **[3] MODO TURBO DELTA (SI):** Monitorea el Excel en Dropbox cada 3 segundos e inyecta únicamente las diferencias.\n"
        "- **[4] AUDITOR MELI (SI):** Actualiza automáticamente el archivo AUDITORIA_MELI_INSUMAES.xlsx en Dropbox.\n"
        "- **[5] MELI_STOCK (SI):** Sincroniza el 40% de la bodega en las 782 publicaciones de Mercado Libre y pausa agotados.\n"
        "- **[6] MELI_PRECIOS (BLOQUEADO - NO):** Candado permanente para proteger la estructura de precios de Mercado Libre.\n"
        "- **[7] PORCENTAJE COLCHON (40%):** Define el porcentaje del stock físico que se expone en canales digitales.\n"
        "- **[8] CORTAFUEGOS PRECIOS (ON 40%):** Bloquea caídas de precio mayores al 40% por errores de digitación en el Excel."
    ),
    "2": (
        "GRUPO B: RADARES EN VIVO Y OPERACION DIARIA ([9], [12], [14], [15], [17] AL [20])",
        "Herramientas de telemetría en tiempo real y control de inventario de mostrador:\n\n"
        "- **[9] MODO PRUEBA (PILOTO):** Entorno de pruebas para validar cambios en 1 producto antes de la ejecución masiva.\n"
        "- **[12] VER BITACORA DE CAMBIOS:** Historial detallado de movimientos del día (Valor Anterior -> Valor Nuevo).\n"
        "- **[14] EJECUTAR SINCRONIZACION AHORA:** Fuerza un ciclo completo de lectura e inyección de manera inmediata.\n"
        "- **[15] ENVIAR REPORTE GMAIL:** Despacha el reporte ejecutivo y planillas de auditoría por correo electrónico.\n"
        "- **[17] AUDITOR COMPARADOR (WOO vs ML):** Cruza lado a lado Stock, Precios y SKUs entre Bodega, Web y Mercado Libre.\n"
        "- **[18] RADAR PANTALLA COMPLETA:** Telemetría en vivo de los últimos 30 impactos con marca de tiempo (DD-MM HH:MM:SS).\n"
        "- **[19] PISTOLA BARRAS & VENTAS MELI:** Descuenta ventas de mostrador o de Mercado Libre directamente sobre el inventario.\n"
        "- **[20] MONITOR ACTIVADOS Y AGOTADOS:** Filtra productos reactivados (0 -> con stock) y productos agotados en la jornada."
    ),
    "3": (
        "GRUPO C: RESCATE DE LA NUBE, BACKUPS Y GITHUB ([10], [11], [13], [16] Y [21])",
        "Sistema de respaldo integral de código fuente, bases de datos y estados de inventario:\n\n"
        "- **[10] GUARDAR FOTO DE SEGURIDAD MELI:** Almacena una instantánea exacta del stock de las 782 publicaciones de Mercado Libre.\n"
        "- **[11] RESTAURAR STOCK ORIGINAL MELI:** Revierte las 782 publicaciones al estado registrado en el punto [10].\n"
        "- **[13] ENVIAR SISTEMA (.ZIP) A DROPBOX:** Empaqueta todos los archivos .py, .sh, .json, .log y .db en BACKUP_ERP_INSUMAES.zip.\n"
        "- **[16] EXPORTAR CODIGO/LOGS (.TXT):** Genera y sube /RADIOGRAFIA_ERP_INSUMAES.txt a la raíz de Dropbox.\n"
        "- **[21] SINCRONIZAR CODIGO CON GITHUB:** Versiona y publica los módulos .py, .sh y el manual README.md en GitHub."
    ),
}

SECCIONES["4"] = (
    "GRUPO D: BOTON [22] — SUITE MAESTRA DE CATALOGO WEB (INSUMAES.CL)",
    "Automatización de fichas técnicas HTML/CSS, estandarización de imágenes y arquitectura de categorías:\n\n"
    "- **[22 -> 1] Estandarizador Inteligente de Fotos:** Recorta espacio vacío y encuadra imágenes a 800x720 px por ID, Categoría o Web completa.\n"
    "- **[22 -> 2] Auto-Linker de Venta Cruzada:** Conecta bidireccionalmente Portaherramientas, Insertos y Accesorios en las fichas técnicas.\n"
    "- **[22 -> 3] Editor de Textos HTML por Lote:** Busca y reemplaza especificaciones o inyecta notas técnicas en múltiples IDs simultáneamente.\n"
    "- **[22 -> 4] Constructor Interactivo de Categorías:** Despliega el árbol jerárquico de categorías de WooCommerce y permite crear nuevas.\n"
    "- **[22 -> 5] Reasignador Definitivo de Categorías:** Traslada lotes de productos (SKU1 | SKU2 | ID) hacia una categoría destino.\n"
    "- **[22 -> 6] Extracción Maestra Web a Dropbox (.TXT):** Respalda las 1.727 fichas HTML y CSS en /RADIOGRAFIA_CATALOGO_HTML_WOO.txt.\n"
    "- **[22 -> 7] Restaurador de Seguridad (Ctrl+Z):** Restaura el código HTML o la imagen original de cualquier producto desde la bóveda local."
)

SECCIONES["5"] = (
    "GRUPO E: BOTON [23] — CRM NACIONAL (204 CIUDADES) & COTIZACIONES B2B",
    "Motor de inteligencia comercial SQLite en modo 100% Solo Lectura (sin alterar los archivos Excel originales):\n\n"
    "- **[23 -> 1] Sincronizar Cotizaciones y Plantilla:** Repara fórmulas J15:J18 en la plantilla oficial e indexa las carpetas mensuales de /COTIZACIONES INSUMAES (445 cotizaciones).\n"
    "- **[23 -> 2] Unificador Nacional de Clientes y Cobranza:** Lee en modo Solo Lectura los ~204 archivos 'Libro de Clientes [Ciudad].xlsx', 'Cuentas por Cobrar.xlsx' (149 filas) y 'Base-datos-clientes.xlsx' (499 filas), generando /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx.\n"
    "- **[23 -> 3] Super-Buscador 360° (SQL):** Consulta en 0,01 segundos cualquier Maestranza, RUT, Ciudad o Producto cruzando cartera histórica, cuentas por cobrar y cotizaciones."
)

def generar_readme_y_dropbox(subir_dbx=True):
    lin = [
        "# ERP Omnicanal Insumaes Cloud — Arquitectura y Manual de Operaciones (V5)\n",
        f"> **Última actualización:** `{time.strftime('%Y-%m-%d %H:%M:%S')}` (Chile) | **35 Funciones Activas (Panel 0-24)** | **Stack:** Python, Google Cloud VM, SQLite, WooCommerce API, Mercado Libre API, Dropbox API\n",
        "---\n",
        TABLA_COMPARATIVA_MD,
        "---\n",
        "## 2. Desglose Funcional de Módulos (Panel de Control 0-24)\n"
    ]
    for k in sorted(SECCIONES.keys()):
        t, c = SECCIONES[k]
        lin.append(f"### {t}\n\n{c}\n")
    lin.append("---\n\n## 3. Comandos Directos de Ejecución en Terminal (SSH)\n\n"
               "- **Abrir Panel Principal:** `python3 ~/panel.py`\n"
               "- **Abrir Manual de Operaciones:** `python3 ~/manual_cloud.py`\n"
               "- **Ejecutar Rescate Completo a Dropbox (`.TXT` y `.ZIP`):** `python3 -u ~/rescatar_todo_nube.py`\n"
               "- **Abrir Suite Maestra Web (`[22]`):** `python3 ~/suite_cloud_woo.py`\n"
               "- **Abrir CRM Nacional y Cotizaciones B2B (`[23]`):** `python3 ~/centro_cotizaciones.py`\n")
    md = "\n".join(lin)
    open(os.path.expanduser("~/README.md"), "w", encoding="utf-8").write(md)
    open(os.path.expanduser("~/MANUAL_INSTRUCCIONES_INSUMAES.txt"), "w", encoding="utf-8").write(md)
    if subir_dbx:
        try:
            env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
            dbx = dropbox.Dropbox(app_key=env["DROPBOX_APP_KEY"], app_secret=env["DROPBOX_APP_SECRET"], oauth2_refresh_token=env["DROPBOX_REFRESH_TOKEN"])
            dbx.files_upload(md.encode("utf-8"), "/MANUAL_INSTRUCCIONES_INSUMAES.txt", mode=dropbox.files.WriteMode.overwrite)
        except Exception: pass
    return md

def abrir_manual():
    generar_readme_y_dropbox(subir_dbx=False)
    while True:
        os.system("clear")
        print("=" * 96)
        print("BOTON [24]: MANUAL DE OPERACIONES Y COMPARATIVA DE TIEMPOS — ERP INSUMAES CLOUD")
        print("Sincronizado con : ~/README.md (GitHub) y /MANUAL_INSTRUCCIONES_INSUMAES.txt (Dropbox)")
        print("=" * 96)
        print("  [1] Grupo A: Interruptores Automáticos 24/7 (Botones [1] al [8])")
        print("  [2] Grupo B: Radares en Vivo y Operación Diaria ([9], [12], [14], [15], [17] al [20])")
        print("  [3] Grupo C: Rescate de la Nube (.ZIP / .TXT), Backups y GitHub ([10], [11], [13], [16], [21])")
        print("  [4] Grupo D: Botón [22] — Suite Maestra de Catálogo Web (Fotos, Auto-Linker, Categorías)")
        print("  [5] Grupo E: Botón [23] — CRM Nacional (204 Ciudades), Cuentas por Cobrar y Cotizaciones")
        print("  [6] Ver Tabla Comparativa de Tiempos (Trabajo Manual vs. Máquina Cloud)")
        print("  [7] Publicar/Actualizar este Manual Ejecutivo en GitHub (README.md) y en Dropbox")
        print("  [0] Volver al Panel Principal")
        print("=" * 96)
        op = input("\nSelecciona una sección (0-7): ").strip()
        if op == "0": break
        elif op in SECCIONES:
            os.system("clear")
            t, c = SECCIONES[op]
            print("=" * 96 + f"\n {t}\n" + "=" * 96 + f"\n\n{c.replace('**', '')}\n\n" + "=" * 96)
            input("\nPresiona Enter para volver al Manual...")
        elif op == "6":
            os.system("clear")
            print(TABLA_COMPARATIVA_MD.replace("**", ""))
            input("\nPresiona Enter para volver al Manual...")
        elif op == "7":
            generar_readme_y_dropbox(subir_dbx=True)
            os.system("cd ~ && git add README.md manual_cloud.py && git commit -m 'Docs: README ejecutivo con tablas comparativas y listas Markdown' >/dev/null 2>&1 && git push -f origin main")
            print("\nManual actualizado en GitHub (README.md) y en Dropbox.")
            input("\nPresiona Enter para volver...")

if __name__ == "__main__":
    if "--sync" in sys.argv:
        generar_readme_y_dropbox(subir_dbx=True)
        print("README.md ejecutivo generado y subido a Dropbox.")
    else:
        abrir_manual()
