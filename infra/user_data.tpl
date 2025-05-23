#!/bin/bash
# Actualizar el sistema
apt-get update -y
apt-get upgrade -y

# Instalar git y python3
apt-get install -y git python3 python3-pip

# Crear el directorio para la aplicación
cd /home/ubuntu

# Clonar el repositorio de GitHub
wget -q https://github.com/andresmarinabad/quiniela_quinigol_bot/archive/refs/tags/v"${code_release}".zip
unzip -q v"${code_release}".zip

# Cambiar al directorio de la aplicación y eliminar el directorio 'infra'
cd quiniela_quinigol_bot-"${code_release}"/
rm -rf infra

# Instalar dependencias de Python desde requirements.txt
cd src
pip3 install -r requirements.txt || true

# Configurar las variables de entorno
export TELEGRAM_BOT_TOKEN="${telegram_bot_token}"
export USERS="${users}"
export ADMIN="${admin}"
export GITHUB_TOKEN="${github_token}"
export TERMINATE_ACTION="${terminate_action}"
export RENDER_ACTION="${render_action}"

# Ejecutar el bot
python3 bot.py
