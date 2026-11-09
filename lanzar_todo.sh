#!/bin/bash

INICIO=$(date +%s)
echo "Empezó a las: $(date)"

echo "===================================================="
echo "🚀 INICIANDO PROTOCOLO AUTOMÁTICO INSUMAES CLOUD"
echo "===================================================="

rm -f WEB_INSUMAES.xlsx AUDITORIA_PRE_SYNC.xlsx

echo -e "\n---> [PASO 1/5]: Despertando al Ojo Vigilante (WooCommerce)..."
python3 -u descargador_web.py

echo -e "\n---> [PASO 2/5]: Despertando al Cerebro Auditor (WooCommerce)..."
python3 -u motor_insumaes.py

echo -e "\n---> [PASO 3/5]: Despertando al Brazo Ejecutor (WooCommerce)..."
python3 -u sincronizador_silencioso.py

echo -e "\n---> [PASO 4/5]: Despertando al Auditor de Mercado Libre (CONTROL_BOT)..."
python3 -u auditor_meli.py

echo -e "\n---> [PASO 5/5]: Despertando al Camión de Reparto (Dropbox)..."
python3 -u subir_dropbox.py

FIN=$(date +%s)
DURACION=$((FIN - INICIO))
MINUTOS=$((DURACION / 60))
SEGUNDOS=$((DURACION % 60))

echo -e "\n---> [PASO FINAL]: Avisando al Jefe por correo (Woo + Meli)..."
python3 -u enviar_correo.py $MINUTOS $SEGUNDOS

echo -e "\n===================================================="
echo "🏁 CICLO FINALIZADO CON ÉXITO (${MINUTOS}m ${SEGUNDOS}s)"
echo "===================================================="
echo "Terminó a las: $(date)"
