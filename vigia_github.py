import os, time, glob, fcntl, subprocess, py_compile

os.chdir(os.path.expanduser("~"))
fp = open("/tmp/vigia_github.lock", "w")
try: fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError: raise SystemExit()

while True:
    try:
        # Verificar que ningún .py esté a medio editar antes de sincronizar
        ok = True
        for f in glob.glob("/home/mauriciovargas1516/*.py"):
            try: py_compile.compile(f, doraise=True)
            except Exception: ok = False; break

        if ok:
            # A) Si cambió algo en Google Cloud -> Subir solo a GitHub
            st = subprocess.getoutput("git status --porcelain *.py *.sh .gitignore").strip()
            if st:
                subprocess.run("git add .gitignore *.py *.sh && git commit -m 'Auto-Sync En Vivo Cloud -> GitHub'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run("git push origin main", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # B) Si cambiaste algo en la web de GitHub -> Bajarlo solo a Google Cloud
            subprocess.run("git fetch origin main", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            loc = subprocess.getoutput("git rev-parse HEAD").strip()
            rem = subprocess.getoutput("git rev-parse origin/main").strip()
            if loc and rem and loc != rem:
                subprocess.run("git pull --rebase origin main", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run("pkill -f marcha_rapida_delta.py && (nohup python3 ~/marcha_rapida_delta.py >/dev/null 2>&1 &)", shell=True)
    except Exception:
        pass
    time.sleep(60)
