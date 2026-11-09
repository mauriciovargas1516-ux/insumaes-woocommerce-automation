import pandas as pd

# Configuramos Pandas para fuerza bruta: nada de recortes
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 2000) # Ancho exagerado para evitar cortes
pd.set_option('display.max_colwidth', 50) # Ajuste de ancho de columna

df = pd.read_excel("AUDITORIA_PRE_SYNC.xlsx")
to_sync = df[df['ESTADO'] == '⚠️ ACTUALIZAR WEB']

# Imprimimos de forma que fuerce la visualización de todas las columnas
print(to_sync[['PRODUCTO LOCAL', 'PRECIO WEB', 'PRECIO LOCAL (Nuevo)', 'VARIANZA']].to_string(index=False))
