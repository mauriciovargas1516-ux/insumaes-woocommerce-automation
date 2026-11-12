import os, re, requests

env = dict(l.strip().replace('"', '').split('=', 1) for l in open(os.path.expanduser('~/.env')) if '=' in l and not l.strip().startswith('#'))
CK, CS = env['WOO_KEY'], env['WOO_SECRET']
URL = "https://www.insumaes.cl/wp-json/wc/v3/products"

PORTAS = [
    {"id": 14501, "nom": "PORTAHERR CHAFLANADO B45°SC09 C20-1T-120-AP9-22",
     "texto": "Diseñado para utilizar placas formato <strong>SCMT09T308 (ej. SCMT09T308-ATM LAM9315)</strong> y compatible con código <strong>SPGT</strong> (No Incluidas)."},
    {"id": 14499, "nom": "PORTAHERR BISELADO B45°SC09 C20-2T-120-AP19-32",
     "texto": "Diseñado para utilizar placas formato <strong>SCMT09T308 (ej. SCMT09T308-ATM LAM9315)</strong> y compatible con código <strong>SPGT</strong> (No Incluidas)."},
    {"id": 14500, "nom": "PORTAHERR BISELADO B45°SC12 C25-2T-150-AP25-40",
     "texto": "Diseñado para utilizar placas formato <strong>SCMT12</strong> y compatible con <strong>SCMT09T308 (SCMT09T308-ATM LAM9315) / SPGT</strong> (No Incluidas)."},
    {"id": 14525, "nom": "PORTAHERR CHAFLANADO SPK SP06 1TC12-120L (8-16) 45°",
     "texto": "Diseñado para utilizar placas formato <strong>SPMT0602</strong> y 100% compatible con código <strong>SPGT (ej. SPGT060204-MG BTG1)</strong> (No Incluidas)."},
    {"id": 14526, "nom": "PORTAHERR CHAFLANADO SPK SP09 20 1TC16-120L (12-23) 45°",
     "texto": "Diseñado para utilizar placas formato <strong>SPMT09T3</strong> y 100% compatible con código <strong>SPGT (ej. SPGT090408-MG BTG1)</strong> (No Incluidas)."},
    {"id": 14527, "nom": "PORTAHERR CHAFLANADO SPK SP09 22 1TC20-120L (9-22) 45°",
     "texto": "Diseñado para utilizar placas formato <strong>SPMT09T3</strong> y 100% compatible con código <strong>SPGT (ej. SPGT090408-MG BTG1)</strong> (No Incluidas)."},
    {"id": 14528, "nom": "PORTAHERR CHAFLANADO SPK SP09 28 2TC20-120L (16-28) 45°",
     "texto": "Diseñado para utilizar placas formato <strong>SPMT09T3</strong> y 100% compatible con código <strong>SPGT (ej. SPGT090408-MG BTG1)</strong> (No Incluidas)."},
    {"id": 14529, "nom": "PORTAHERR CHAFLANADO SPK SP09 32 2TC20-120L (19-32) 45°",
     "texto": "Diseñado para utilizar placas formato <strong>SPMT09T3</strong> y 100% compatible con código <strong>SPGT (ej. SPGT090408-MG BTG1)</strong> (No Incluidas)."},
    {"id": 14530, "nom": "PORTAHERR CHAFLANADO SPK SP11 40 2TC25-150L (25-40) 45°",
     "texto": "Diseñado para utilizar placas formato <strong>SPMT11</strong> y 100% compatible con código <strong>SPGT (ej. SPGT110408-MG BTG1)</strong> (No Incluidas)."}
]

print("\n🚀 Actualizando fichas técnicas de los 9 Portaherramientas en insumaes.cl...")
s = requests.Session()
for p in PORTAS:
    pid = p["id"]
    r = s.get(f"{URL}/{pid}", auth=(CK, CS), timeout=15)
    if r.status_code != 200:
        print(f"  ⚠️ No se pudo leer ID {pid}: {r.status_code}")
        continue
    prod = r.json()
    desc = prod.get("description", "") or ""
    nueva_linea = f"INSERTO COMPATIBLE (RECOMENDADO):</strong> {p['texto']}"
    if "INSERTO COMPATIBLE" in desc.upper():
        desc_nueva = re.sub(r"INSERTO COMPATIBLE[^<]*?(?:</[^>]+>)?[^<]*?\(No Incluidas\)\.?", nueva_linea, desc, flags=re.I)
        if desc_nueva == desc:
            desc_nueva = re.sub(r"(<li>[^<]*INSERTO COMPATIBLE.*?</li>)", f"<li><strong>{nueva_linea}</li>", desc, flags=re.I | re.S)
    else:
        desc_nueva = desc + f"\n<ul><li><strong>{nueva_linea}</li></ul>"

    up = s.put(f"{URL}/{pid}", auth=(CK, CS), json={"name": p["nom"], "description": desc_nueva}, timeout=15)
    if up.status_code == 200:
        print(f"  ✅ [ID:{pid}] {p['nom']} -> ¡Inserto compatible actualizado en web!")
    else:
        print(f"  ❌ [ID:{pid}] Error HTTP {up.status_code}")
