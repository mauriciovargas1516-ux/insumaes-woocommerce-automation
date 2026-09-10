#!/bin/bash

echo "Empezó a las: $(date)"

echo "=================================================="
echo " 🚀INICIANDO PROTOCOLO AUTOMÁTICO INSUMAES CLOUD"
echo "=================================================="

echo -e "\n---> [PASO 1/4]: Despertando al Ojo Vigilante..."
python3 descargador_web.py

echo -e "\n---> [PASO 2/4]: Despertando al Cerebro Auditor..."
python3 motor_insumaes.py

echo -e "\n---> [PASO 3/4]: Despertando al Brazo Ejecutor..."
python3 sincronizador_silencioso.py

echo -e "\n---> [PASO 4/4]: Despertando al Camión de Reparto (Dropbox)..."
python3 subir_dropbox.py

echo -e "\n---> [PASO FINAL]: Avisando al jefe por correo..."
python3 enviar_correo.py

echo -e "\n=================================================="
echo " 🏁CICLO FINALIZADO CON ÉXITO"
echo "=================================================="

echo "Terminó a las: $(date)"
