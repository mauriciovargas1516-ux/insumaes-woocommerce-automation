import shutil
import os, json, time, requests
from concurrent.futures import ThreadPoolExecutor
import conectar_meli, lee_config

RUTA_BAK = os.path.expanduser("~/respaldo_meli_original.json")
RUTA_CFG = os.path.expanduser("~/config_bot.json")
RUTA_XLS = os.path.expanduser("~/AUDITORIA_MELI_INSUMAES.xlsx")

def crear_respaldo():
    import pandas as pd
    tok = conectar_meli.obtener_token_valido()
    hdr = {"Authorization": f"Bearer {tok}"}
    df = pd.read_excel(RUTA_XLS)
    col = "Código ML (Ver Web)" if "Código ML (Ver Web)" in df.columns else df.columns[1]
    mlcs = [str(x).strip().upper() for x in df[col].dropna().unique() if str(x).strip().upper().startswith("MLC")]
    items = {}
    for i in range(0, len(mlcs), 20):
        r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(mlcs[i:i+20])}", headers=hdr, timeout=15)
        if r.status_code == 200:
            for o in r.json():
                if o.get("code") == 200:
                    b = o.get("body", {})
                    items[b["id"]] = {"available_quantity": int(b.get("available_quantity",0)), "price": int(b.get("price",0) or 0), "status": b.get("status",""), "title": str(b.get("title",""))[:45]}
    if os.path.exists(RUTA_BAK) and not os.path.exists(RUTA_BAK + ".2026-10-30.bak"): shutil.copy2(RUTA_BAK, RUTA_BAK + ".2026-10-30.bak")
    if os.path.exists(RUTA_BAK) and not os.path.exists(RUTA_BAK + ".2026-10-30.bak"): shutil.copy2(RUTA_BAK, RUTA_BAK + ".2026-10-30.bak")
    json.dump({"fecha": time.strftime("%Y-%m-%d %H:%M:%S"), "total": len(items), "items": items}, open(RUTA_BAK,"w",encoding="utf-8"), indent=2)
    print(f"✅ Foto guardada: {len(items)} ítems.")

def restaurar_respaldo():
    tok = conectar_meli.obtener_token_valido()
    hdr = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    data = json.load(open(RUTA_BAK, "r", encoding="utf-8"))
    items = data.get("items", {})
    mlcs = list(items.keys())
    if os.path.exists(RUTA_CFG):
        c = json.load(open(RUTA_CFG, "r", encoding="utf-8"))
        c["SINCRONIZAR_MELI_STOCK"] = "NO"; c["MLC_PILOTO_PRUEBA"] = "NINGUNO"
        json.dump(c, open(RUTA_CFG, "w", encoding="utf-8"), indent=4)
    print(f"\n⏪ Revisando {len(mlcs)} publicaciones contra tu foto ({data.get('fecha')})...")
    tareas = []
    for i in range(0, len(mlcs), 20):
        r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(mlcs[i:i+20])}", headers=hdr, timeout=15)
        if r.status_code == 200:
            for o in r.json():
                if o.get("code") == 200:
                    b = o.get("body", {}); mid = b.get("id"); orig = items.get(mid, {})
                    qn, sn = int(b.get("available_quantity",0)), str(b.get("status",""))
                    qo, so = int(orig.get("available_quantity",0)), str(orig.get("status",""))
                    pl = {}
                    if qn != qo and qo > 0: pl["available_quantity"] = qo
                    if sn != so and so in ("active","paused"): pl["status"] = so
                    if pl: tareas.append((mid, orig.get("title",""), qn, sn, qo, so, pl))
    def _put(t):
        mid, tit, qn, sn, qo, so, pl = t
        rp = requests.put(f"https://api.mercadolibre.com/items/{mid}", headers=hdr, json=pl, timeout=12)
        return (mid, tit, qn, sn, qo, so, rp.status_code in (200, 201))
    ok_cnt = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for mid, tit, qn, sn, qo, so, ok in ex.map(_put, tareas):
            if ok:
                ok_cnt += 1
                lee_config.registrar_evento("MELI-RESTORE", mid, tit, f"{qn} uds ({sn}) -> {qo} uds ({so})")
                if ok_cnt <= 20: print(f"  ↩️ Restaurado {mid}: {qn} ({sn}) ➔ {qo} ({so})")
    print(f"\n✅ Restauración lista: {ok_cnt} publicaciones devueltas a su estado original.")
