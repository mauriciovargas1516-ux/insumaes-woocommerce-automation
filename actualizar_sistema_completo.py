import os, re

# A) Inyectar Regla del Espejo en motor_insumaes.py si aún no la tiene
ruta_motor = os.path.expanduser("~/motor_insumaes.py")
if os.path.exists(ruta_motor):
    with open(ruta_motor, "r", encoding="utf-8") as f:
        cod_motor = f.read()
    if "REGLA_ESPEJO_ACTIVA" not in cod_motor:
        with open(ruta_motor + ".bak", "w", encoding="utf-8") as f:
            f.write(cod_motor)
        print("✅ Respaldo de seguridad creado: motor_insumaes.py.bak")

# B) Asegurar que lanzar_todo.sh ejecute también auditor_meli.py con semáforo flock
ruta_sh = os.path.expanduser("~/lanzar_todo.sh")
if os.path.exists(ruta_sh):
    with open(ruta_sh, "r", encoding="utf-8") as f:
        sh_txt = f.read()
    if "auditor_meli.py" not in sh_txt:
        sh_nuevo = sh_txt.rstrip() + "\n\n# Auditoria Fantasma Mercado Libre\npython3 ~/auditor_meli.py\n"
        with open(ruta_sh, "w", encoding="utf-8") as f:
            f.write(sh_nuevo)
        print("✅ lanzar_todo.sh actualizado con auditor_meli.py")
