import lee_config
import os, sys, re, time, pandas as pd, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

os.environ["TZ"] = "America/Santiago"
try: time.tzset()
except Exception: pass

CORREO_ORIGEN = "mauriciovargas1516@gmail.com"
PASSWORD_APP = dict(l.strip().replace('"', '').split('=', 1) for l in open('/home/mauriciovargas1516/.env') if '=' in l)['GMAIL_PASS']
CORREO_DESTINO = "mauriciovargas1516@gmail.com"

if len(sys.argv) >= 3:
    texto_tiempo = f"⏱️ El protocolo se completó en: {sys.argv[1]} minutos y {sys.argv[2]} segundos."
else:
    texto_tiempo = "⏱️ El protocolo ha finalizado."

ruta_log = os.path.expanduser("~/cron_registro.log")
ruta_excel = os.path.expanduser("~/AUDITORIA_PRE_SYNC.xlsx")
ruta_meli = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")
ruta_hist = os.path.expanduser("~/historial_erp.log")
linea_inyeccion = "🏁 INYECCIÓN FINALIZADA: Revisar archivos adjuntos"

if os.path.exists(ruta_log):
    with open(ruta_log, "r", encoding="utf-8", errors="replace") as f:
        for l in reversed(f.readlines()):
            if "INYECCIÓN FINALIZADA:" in l.upper():
                linea_inyeccion = l.strip()
                break

df = None
if os.path.exists(ruta_excel):
    try: df = pd.read_excel(ruta_excel)
    except Exception: df = None

if df is not None:
    total_auditados = len(df)
    nuevos = len(df[df["TIPO DE CRUCE"] == "NUEVO INGRESO"])
    total_web = total_auditados - nuevos
    m_sku = len(df[df["TIPO DE CRUCE"].astype(str).str.contains("MATCH SKU", na=False)])
    m_nom = len(df[df["TIPO DE CRUCE"].astype(str).str.contains("MATCH NOMBRE", na=False)])
    m_det = len(df[df["TIPO DE CRUCE"].astype(str).str.contains("MATCH DETECTIVE", na=False)])
    sin_m = len(df[df["TIPO DE CRUCE"].astype(str).str.contains("SIN MATCH", na=False)])
    matches = m_sku + m_nom + m_det
    total_local = matches + nuevos
    p_match = (matches / total_web * 100) if total_web else 0
    p_sku = (m_sku / total_web * 100) if total_web else 0
    p_nom = (m_nom / total_web * 100) if total_web else 0
    p_det = (m_det / total_web * 100) if total_web else 0
    p_sin = (sin_m / total_web * 100) if total_web else 0
    p_cob = (matches / total_local * 100) if total_local else 0
    al_dia = len(df[df["ESTADO"].astype(str).str.contains("AL DIA|AL DÍA", na=False)])
    bloq = len(df[df["ESTADO"].astype(str).str.contains("ALERTA|SIN PRECIO|🛡️|🚨", na=False)])
    inyectar = len(df[df["ESTADO"].astype(str).str.contains("ACTUALIZAR", na=False)])

    resumen_cambios = "\n".join([
        "📊 1. RESUMEN EJECUTIVO WOOCOMMERCE (INSUMAES.CL)",
        "-"*60,
        f"📦 Total Catálogo Excel (Dropbox) : {total_local} productos",
        f"🌐 Total Publicados en Web        : {total_web} productos",
        f"🔍 Total Registros Auditados      : {total_auditados} registros",
        "",
        f"🎯 TASA DE MATCH EN LA WEB        : {p_match:.1f}% ({matches} de {total_web} conectados)",
        f"   ├── 🟢 Match Exacto por SKU    : {m_sku} ({p_sku:.1f}%)",
        f"   ├── 🟡 Match Exacto por Nombre : {m_nom} ({p_nom:.1f}%)",
        f"   └── 🔵 Match Detective IA      : {m_det} ({p_det:.1f}%)",
        f"🔴 En Web Sin Pareja en Excel     : {p_sin:.1f}% ({sin_m} sin match)",
        f"📈 Cobertura de tu Excel en Web   : {p_cob:.1f}% ({nuevos} nuevos por subir)",
        "-"*60,
        f"✅ Productos Al Día (Sin cambios) : {al_dia}",
        f"🛡️ Bloqueados (Varianza / $0)     : {bloq} (Ignorados por seguridad)",
        f"⚠️ Listos para Inyectar en Web    : {inyectar}",
        "-"*60,
        linea_inyeccion
    ])
else:
    resumen_cambios = "ℹ️ AUDITORIA_PRE_SYNC.xlsx en proceso de generación."

resumen_meli = ""
lista_pausar_completa = ""
df_m = None
if os.path.exists(ruta_meli):
    try: df_m = pd.read_excel(ruta_meli)
    except Exception: df_m = None

if df_m is not None:
    tot_m = len(df_m)
    c_m_col = "Cómo se Conectó" if "Cómo se Conectó" in df_m.columns else "TIPO_MATCH"
    c_p_col = "Packs en Bodega" if "Packs en Bodega" in df_m.columns else "PACKS_REALES_COMPLETOS"
    c_id_col = "Código ML (Ver Web)" if "Código ML (Ver Web)" in df_m.columns else "CODIGO_MLC"
    c_ti_col = "Nombre en Mercado Libre" if "Nombre en Mercado Libre" in df_m.columns else "TITULO_MELI"
    c_sb_col = "Stock Bodega" if "Stock Bodega" in df_m.columns else "STOCK_FISICO_BODEGA"
    c_up_col = "Unid. x Pack" if "Unid. x Pack" in df_m.columns else "UNIDADES_POR_PACK"
    con_m = df_m[~df_m[c_m_col].astype(str).isin(["SIN MATCH", "Sin Conexión", "nan"])]
    sin_m_meli = tot_m - len(con_m)
    act_m = con_m[pd.to_numeric(con_m[c_p_col], errors="coerce").fillna(0) > 0]
    if "Estado" in df_m.columns:
        pau_m = df_m[df_m["Estado"].astype(str).str.contains("Pausar", na=False)]
    else:
        pau_m = con_m[pd.to_numeric(con_m[c_p_col], errors="coerce").fillna(0) <= 0]
    p_m = (len(con_m) / tot_m * 100) if tot_m else 0
    lineas_pau = []
    for _idx_p, (_, r) in enumerate(pau_m.iterrows(), 1):
        link_mlc = "https://articulo.mercadolibre.cl/" + str(r[c_id_col]).replace("MLC", "MLC-")
        sb_val = int(float(r[c_sb_col] or 0)) if pd.notna(r[c_sb_col]) else 0
        up_val = int(float(r[c_up_col] or 1)) if pd.notna(r[c_up_col]) else 1
        lineas_pau.append(f"   {_idx_p:02d}. [{r[c_id_col]}] {r[c_ti_col]} (Bodega: {sb_val} uds | Pack x{up_val}) -> {link_mlc}")
    lista_pausar_completa = "\n".join(lineas_pau)

    resumen_meli = "\n\n" + "\n".join([
        "🛒 2. AUDITORÍA MERCADO LIBRE",
        "-"*60,
        f"📦 Total Publicaciones Meli       : {tot_m} publicaciones",
        f"🎯 TASA DE MATCH EN MELI          : {p_m:.1f}% ({len(con_m)} de {tot_m} conectadas)",
        f"✅ Activas con Stock Sano         : {len(act_m)} publicaciones",
        f"🔴 En Meli Sin Pareja en Excel    : {sin_m_meli} publicaciones",
        f"⏸️ Agotadas / Pausadas (0 UDS)    : {len(pau_m)} publicaciones (Ver detalle en archivo adjunto 4)",
        "-"*60
    ])

todas = [l.strip() for l in open(ruta_hist, "r", encoding="utf-8", errors="ignore").readlines() if l.strip()] if os.path.exists(ruta_hist) else []
ls_woo_all  = [l for l in reversed(todas) if "[WOO" in l]
ls_meli_all = [l for l in reversed(todas) if "[MELI" in l]

sub_w = sum(1 for l in ls_woo_all if "SUBIÓ" in lee_config.fmt_bitacora(l))
baj_w = sum(1 for l in ls_woo_all if "BAJÓ" in lee_config.fmt_bitacora(l))
sub_m = sum(1 for l in ls_meli_all if "SUBIÓ" in lee_config.fmt_bitacora(l))
baj_m = sum(1 for l in ls_meli_all if "BAJÓ" in lee_config.fmt_bitacora(l))
pau_m_cnt = sum(1 for l in ls_meli_all if "PAUSADO" in lee_config.fmt_bitacora(l))

txt_woo_top10  = "\n".join(lee_config.fmt_bitacora(l, i) for i, l in enumerate(ls_woo_all[:10], 1)) if ls_woo_all else "   ✅ Sin movimientos recientes."
txt_meli_top10 = "\n".join(lee_config.fmt_bitacora(l, i) for i, l in enumerate(ls_meli_all[:10], 1)) if ls_meli_all else "   ✅ Sin movimientos recientes."

resumen_bitacora = "\n\n" + "\n".join([
    "============================================================",
    "📜 3. VISTA RÁPIDA DE ÚLTIMOS 10 CAMBIOS (HISTORIAL COMPLETO EN ADJUNTOS)",
    "============================================================",
    f"🌐 3A. ÚLTIMOS 10 EN WOOCOMMERCE (Total histórico: {len(ls_woo_all)} movs | 🟢⬆️ {sub_w} Subidas | 🔴⬇️ {baj_w} Bajadas)",
    "-"*75,
    txt_woo_top10,
    "-"*75,
    "",
    f"💛 3B. ÚLTIMOS 10 EN MERCADO LIBRE (Total histórico: {len(ls_meli_all)} movs | 🟢⬆️ {sub_m} Subidas | 🔴⬇️ {baj_m} Bajadas | 🛑⏸️ {pau_m_cnt} Pausados)",
    "-"*75,
    txt_meli_top10,
    "-"*75,
    "📎 NOTA: Abajo tienes adjuntos los 4 archivos separados por plataforma (2 Excels + 2 Bitácoras completas)."
])

contenido_txt_woo = "\n".join([
    "====================================================================================",
    "🛒 BITÁCORA COMPLETA DE CAMBIOS — WOOCOMMERCE (INSUMAES.CL)",
    f"Total Movimientos: {len(ls_woo_all)} (🟢⬆️ {sub_w} Subidas | 🔴⬇️ {baj_w} Bajadas)",
    "====================================================================================",
    "",
    ("\n".join(lee_config.fmt_bitacora(l, i) for i, l in enumerate(ls_woo_all, 1)) if ls_woo_all else "Sin movimientos registrados."),
    ""
])
open(os.path.expanduser("~/BITACORA_CAMBIOS_WOO.txt"), "w", encoding="utf-8").write(contenido_txt_woo)

contenido_txt_meli = "\n".join([
    "====================================================================================",
    "💛 BITÁCORA COMPLETA DE CAMBIOS — MERCADO LIBRE CHILE",
    f"Total Movimientos: {len(ls_meli_all)} (🟢⬆️ {sub_m} Subidas | 🔴⬇️ {baj_m} Bajadas | 🛑⏸️ {pau_m_cnt} Pausados)",
    "====================================================================================",
    "",
    ("\n".join(lee_config.fmt_bitacora(l, i) for i, l in enumerate(ls_meli_all, 1)) if ls_meli_all else "Sin movimientos registrados."),
    "",
    "====================================================================================",
    "📋 LISTADO DE PUBLICACIONES AGOTADAS / EN PAUSA EN MERCADO LIBRE (0 UDS):",
    "====================================================================================",
    (lista_pausar_completa if lista_pausar_completa else "Ninguna publicación agotada."),
    ""
])
open(os.path.expanduser("~/BITACORA_CAMBIOS_MELI.txt"), "w", encoding="utf-8").write(contenido_txt_meli)

fecha_actual = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M")

cuerpo = "\n".join([
    "Hola Mauricio,",
    "",
    "El ciclo automático Omnicanal de Insumaes Cloud (WooCommerce + Mercado Libre + Motor Delta 24/7) ha finalizado con éxito.",
    "",
    texto_tiempo,
    "",
    resumen_cambios + resumen_meli + resumen_bitacora,
    ""
])

msg = MIMEMultipart()
msg["From"] = CORREO_ORIGEN
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"✅ INSUMAES OMNICANAL: Reporte Woo + Meli ({fecha_actual})"
msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

if os.path.exists(ruta_excel):
    with open(ruta_excel, "rb") as f_w:
        p1 = MIMEBase("application", "octet-stream")
        p1.set_payload(f_w.read())
    encoders.encode_base64(p1)
    p1.add_header("Content-Disposition", 'attachment; filename="1_AUDITORIA_WOO_INSUMAES.xlsx"')
    msg.attach(p1)

if os.path.exists(ruta_meli):
    with open(ruta_meli, "rb") as f_m:
        p2 = MIMEBase("application", "octet-stream")
        p2.set_payload(f_m.read())
    encoders.encode_base64(p2)
    p2.add_header("Content-Disposition", 'attachment; filename="2_AUDITORIA_MELI_INSUMAES.xlsx"')
    msg.attach(p2)

adj_w_txt = MIMEText(contenido_txt_woo, "plain", "utf-8")
adj_w_txt.add_header("Content-Disposition", f'attachment; filename="3_BITACORA_CAMBIOS_WOO_{fecha_archivo}.txt"')
msg.attach(adj_w_txt)

adj_m_txt = MIMEText(contenido_txt_meli, "plain", "utf-8")
adj_m_txt.add_header("Content-Disposition", f'attachment; filename="4_BITACORA_CAMBIOS_MELI_{fecha_archivo}.txt"')
msg.attach(adj_m_txt)

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(CORREO_ORIGEN, PASSWORD_APP)
server.send_message(msg)
server.quit()
print("✅ Correo Omnicanal enviado con 4 archivos adjuntos separados por plataforma (2 Excels + 2 Bitácoras .txt).")
