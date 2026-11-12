import os, sys, time, dropbox

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

SECCIONES = {
    "1": (
        "🟢 GRUPO A: INTERRUPTORES AUTOMÁTICOS 24/7 (BOTONES [1] AL [8])",
        "Los dejas en SI / ON una sola vez y el vigilante trabaja solo cada 3 segundos:\n"
        " • [1] WOO_STOCK (SI)        : Sube el stock con colchón (40%) del Excel a insumaes.cl.\n"
        " • [2] WOO_PRECIOS (SI)      : Sube los precios con IVA del Excel a tu web automáticamente.\n"
        " • [3] MODO TURBO DELTA (SI) : Vigila tu Excel en Dropbox cada 3 seg e inyecta solo cambios.\n"
        " • [4] AUDITOR MELI (SI)     : Actualiza AUDITORIA_MELI_INSUMAES.xlsx en tu Dropbox.\n"
        " • [5] MELI_STOCK (SI)       : Sube el 40% de tu bodega a las 782 publicaciones de Mercado Libre.\n"
        " • [6] MELI_PRECIOS (BLOQ)   : Candado fijo (NO) para proteger tus precios de Mercado Libre.\n"
        " • [7] PORCENTAJE COLCHÓN    : Define qué % de la bodega se publica en internet (ej: 40%).\n"
        " • [8] CORTAFUEGOS PRECIOS   : Bloquea caídas bruscas > 40% si alguien digita mal en Excel."
    ),
    "2": (
        "🔭 GRUPO B: RADARES EN VIVO Y OPERACIÓN DIARIA ([9], [12], [14], [15], [17] AL [20])",
        "Para supervisar en tiempo real o descontar ventas de mostrador:\n"
        " • [9]  MODO PRUEBA (PILOTO) : Laboratorio para probar 1 producto antes del lote completo.\n"
        " • [12] VER BITÁCORA         : Historial de qué productos cambiaron hoy (Antes -> Ahora).\n"
        " • [14] EJECUTAR AHORA       : Fuerza una sincronización completa en este mismo segundo.\n"
        " • [15] ENVIAR REPORTE GMAIL : Envía el resumen y Excels de auditoría a tu correo.\n"
        " • [17] AUDITOR COMPARADOR   : Compara lado a lado Stock y Precios (Excel vs Web vs ML).\n"
        " • [18] RADAR PANTALLA COMPL.: Últimos 30 impactos en vivo con fecha (DD-MM HH:MM:SS).\n"
        " • [19] PISTOLA BARRAS & ML  : Descuenta ventas de mesón (pistola) o de ML en el Excel.\n"
        " • [20] MONITOR ACTIVADOS    : Muestra qué revivió (0 -> Stock) y qué se agotó hoy (0 uds)."
    ),
    "3": (
        "🛡️ GRUPO C: RESCATE DE LA NUBE, BACKUPS Y GITHUB ([10], [11], [13], [16] Y [21])",
        "Tus seguros de vida para respaldar código, logs, bases de datos e inventario:\n"
        " • [10] GUARDAR FOTO MELI    : Guarda copia exacta del stock de tus 782 ítems de ML.\n"
        " • [11] RESTAURAR STOCK MELI : Devuelve tus 782 ítems de ML a la foto guardada en [10].\n"
        " • [13] ENVIAR .ZIP A DROPBOX: Guarda todos tus .py, .sh, .json, .log y .db en Dropbox (.ZIP).\n"
        " • [16] EXPORTAR CÓDIGO .TXT : Sube /RADIOGRAFIA_ERP_INSUMAES.txt a la raíz de tu Dropbox.\n"
        " • [21] SINCRONIZAR GITHUB   : Sube todos tus .py, .sh y el Manual README.md a tu GitHub."
    ),
}

SECCIONES["4"] = (
    "🛠️ GRUPO D: BOTÓN [22] — SUITE MAESTRA DE CATÁLOGO WEB (INSUMAES.CL)",
    "Taller de diseño, fotos, categorías y botones de venta cruzada en WooCommerce:\n"
    " • [22 -> 1] 📸 Estandarizador Fotos : Encuadra fotos gigantes a 800x720 px por ID, Categoría o Web.\n"
    " • [22 -> 2] 🔗 Auto-Linker Botones  : Conecta Portas <-> Insertos en las Cajas Amarillas.\n"
    " • [22 -> 3] ✏️  Editor HTML por Lote : Busca/reemplaza textos o agrega notas en varios IDs.\n"
    " • [22 -> 4] 🏗️  Constructor Categor. : Dibuja el árbol de categorías de insumaes.cl y crea nuevas.\n"
    " • [22 -> 5] 🚚 Reasignador Categor. : Mueve lotes de productos (SKU1 | SKU2) de categoría.\n"
    " • [22 -> 6] 💾 Extracción Web (.TXT): Respalda las 1.727 fichas HTML en /RADIOGRAFIA_CATALOGO_HTML_WOO.txt.\n"
    " • [22 -> 7] ⏪ Restaurador (Ctrl+Z) : Devuelve el HTML o la Foto de 1 ID (o todos) al original."
)

SECCIONES["5"] = (
    "🏢 GRUPO E: BOTÓN [23] — CRM NACIONAL (204 CIUDADES) & COTIZACIONES B2B",
    "Inteligencia comercial en MODO 100% SOLO LECTURA (jamás modifica los Excels de tu tío):\n"
    " • [23 -> 1] 🔧 Sincronizar Cotizac. : Repara fórmulas J15:J18 en Plantilla e indexa /COTIZACIONES INSUMAES.\n"
    " • [23 -> 2] 🌎 Unificar 204 Ciudades: Lee los ~204 'Libro de Clientes [Ciudad].xlsx' + 'Cuentas por Cobrar.xlsx'\n"
    "                                       y crea en Dropbox /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx.\n"
    " • [23 -> 3] 🔎 Super-Buscador 360°  : Busca en 0,01s cualquier Maestranza, RUT, Ciudad o Producto."
)

def generar_readme_y_dropbox(subir_dbx=True):
    lin = [
        "# 🛠️ ERP Omnicanal Insumaes Cloud — Manual Oficial de Operaciones (V5)\n",
        f"> **Última actualización:** `{time.strftime('%Y-%m-%d %H:%M:%S')}` (Chile) | **35 Funciones Activas (Panel 0-24)**\n",
        "---\n"
    ]
    for k in sorted(SECCIONES.keys()):
        t, c = SECCIONES[k]
        lin.append(f"## {t}\n\n```text\n{c}\n```\n")
    lin.append("## ⚡ Comandos Directos en Terminal SSH\n- Panel Principal: `python3 ~/panel.py`\n- Manual Interactivo: `python3 ~/manual_cloud.py`\n- Rescatar Todo a Dropbox (`.TXT` y `.ZIP`): `python3 -u ~/rescatar_todo_nube.py`\n")
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
        print("📖  BOTÓN [24]: MANUAL DE INSTRUCCIONES INTERACTIVO — ERP INSUMAES CLOUD (35 FUNCIONES)")
        print("☁️  Sincronizado en : ~/README.md (Portada de tu GitHub) y /MANUAL_INSTRUCCIONES_INSUMAES.txt (Dropbox)")
        print("=" * 96)
        print("  [1] 🟢 Grupo A: Interruptores Automáticos 24/7 (Botones [1] al [8])")
        print("  [2] 🔭 Grupo B: Radares en Vivo y Operación Diaria ([9], [12], [14], [15], [17] al [20])")
        print("  [3] 🛡️  Grupo C: Rescate de la Nube (.ZIP / .TXT), Backups y GitHub ([10], [11], [13], [16], [21])")
        print("  [4] 🛠️  Grupo D: Botón [22] — Suite Maestra de Catálogo Web (Fotos, Auto-Linker, Categorías)")
        print("  [5] 🏢 Grupo E: Botón [23] — CRM Nacional (204 Ciudades), Cuentas por Cobrar y Cotizaciones")
        print("  [6] 📜 Ver TODO el Manual Completo en pantalla")
        print("  [7] 🐙 Subir/Actualizar este Manual y Código en GitHub (README.md) y en Dropbox ahora")
        print("  [0] 🔙 Volver al Panel Principal")
        print("=" * 96)
        op = input("\n👉 Elige qué sección quieres consultar (0-7): ").strip()
        if op == "0": break
        elif op in SECCIONES:
            os.system("clear")
            t, c = SECCIONES[op]
            print("=" * 96 + f"\n {t}\n" + "=" * 96 + f"\n\n{c}\n\n" + "=" * 96)
            input("\n👉 Presiona Enter para volver al Manual...")
        elif op == "6":
            os.system("clear")
            for k in sorted(SECCIONES.keys()):
                t, c = SECCIONES[k]
                print("=" * 96 + f"\n {t}\n" + "-" * 96 + f"\n{c}\n")
            input("\n👉 Presiona Enter para volver al Manual...")
        elif op == "7":
            generar_readme_y_dropbox(subir_dbx=True)
            os.system("cd ~ && git add README.md *.py *.sh 2>/dev/null && git commit -m 'Docs: Manual V5 en README.md + Modulos Cloud' >/dev/null 2>&1 && git push origin main")
            print("\n✅ ¡Manual publicado en la portada de tu GitHub (README.md) y en la raíz de tu Dropbox!")
            input("\n👉 Presiona Enter para volver...")

if __name__ == "__main__":
    if "--sync" in sys.argv:
        generar_readme_y_dropbox(subir_dbx=True)
        print("✅ README.md generado y /MANUAL_INSTRUCCIONES_INSUMAES.txt subido a Dropbox.")
    else:
        abrir_manual()
