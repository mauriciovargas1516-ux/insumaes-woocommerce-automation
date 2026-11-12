import os, re, glob

# 1. Evitar que los JSON pesados corten tu radiografía
p_rad = os.path.expanduser("~/exportar_radiografia.py")
if os.path.exists(p_rad):
    txt_r = open(p_rad, "r", encoding="utf-8").read()
    txt_r = txt_r.replace(
        'if "token" in nom.lower(): continue',
        'if any(x in nom.lower() for x in ("token", "cache", "delta.json", "full.json")): continue'
    )
    open(p_rad, "w", encoding="utf-8").write(txt_r)
    print("✅ 1/2: exportar_radiografia.py optimizado.")

# 2. Buscar el archivo que dibuja el RADAR VERTICAL (Función 18)
objetivo = None
for ruta in sorted(glob.glob(os.path.expanduser("~/*.py"))):
    if os.path.basename(ruta) == "parche_radar_18.py":
        continue
    txt = open(ruta, "r", encoding="utf-8", errors="ignore").read()
    if "RADAR VERTICAL A PANTALLA COMPLETA" in txt:
        objetivo = ruta
        break

if not objetivo:
    print("⚠️ No se encontró el archivo del Radar Vertical.")
else:
    print(f"🎯 Archivo encontrado: {objetivo}")
    cod = open(objetivo, "r", encoding="utf-8").read()
    open(objetivo + ".bak_radar", "w", encoding="utf-8").write(cod)

    # Mostrar cómo está programada actualmente esa sección para verla clara
    lineas = cod.splitlines()
    for i, l in enumerate(lineas):
        if "RADAR VERTICAL A PANTALLA COMPLETA" in l:
            inicio = max(0, i - 25)
            fin = min(len(lineas), i + 45)
            print("\n--- CÓDIGO ACTUAL DEL RADAR (EXTRACTO) ---")
            for idx in range(inicio, fin):
                print(f"{idx+1:03d}: {lineas[idx]}")
            print("------------------------------------------\n")
            break
