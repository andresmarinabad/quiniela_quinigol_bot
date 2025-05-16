
import os
import boto3
import logging
import watchtower
from api import genera_mensaje_nueva_jornada, carga_apuestas_jugador

from telegram import Update, Document, error
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

apuestas = {}

responsabe_id = None

# Config logger for CloudWatch
logger = logging.getLogger("quiniela_quinigol_bot")
logger.setLevel(logging.INFO)
boto3_client=boto3.client("logs", region_name="eu-west-1")
logger.addHandler(watchtower.CloudWatchLogHandler(log_group_name="QuiniBot", boto3_client=boto3_client))

async def nueva_jornada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global responsabe_id
    global apuestas
    apuestas = {}
    responsabe_id = update.effective_user.id
    user_name = update.effective_user.full_name
    logger.info(f"Se inicia jornada por {user_name}")
    await update.message.reply_text(f"Hola {user_name}, eres el responsable esta jornada")
    await update.message.reply_text(f"A continuación te adjunto la plantilla con la información que necesito que cada uno me envie por privado")
    quiniela, quinigol = genera_mensaje_nueva_jornada()
    await update.message.reply_text(f"/nueva_apuesta\n\n{quiniela}\n\n{quinigol}")

async def nueva_apuesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if responsabe_id is None:
        logger.warning(f"Intento de apuesta sin jornada iniciada")
        await update.message.reply_text(f"Atención: La jornada no está iniciada")
        await update.message.reply_text(f"El respondable la debe iniciar con el comando /nueva_jornada")
        return

    user_name = update.effective_user.full_name
    logger.info(f"Apuesta recibida de {user_name}")
    texto_enviado = ' '.join(context.args)
    if texto_enviado == "":
        logger.warning(f"La apuesta no tiene texto")
        await update.message.reply_text(f"Necesito que adjuntes la plantilla con los partidos")
        return

    quiniela, quinigol, mensaje = carga_apuestas_jugador(texto_enviado)

    if len(quiniela) < 15 or len(quinigol) < 6:
        logger.warning(f"Algunos de los resultados no está bien informado")
        await update.message.reply_text(f"Uno de los resultados está vacío. Revísalo y reenvía por favor.")
        return

    user_id = update.effective_user.id
    global apuestas

    apuestas[user_id] = {
        'quiniela': quiniela,
        'quinigol': quinigol
    }

    logger.info(f"Apuesta guardada")
    print(apuestas)

    await update.message.reply_text(f"Recibido y guardado. Mucha suerte!")
    bot = context.bot
    await bot.send_message(chat_id=responsabe_id, text=f"El pronóstico de {user_name}:\n\n{mensaje}")


async def actualiza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Obtener resultados")
    #result = obtener_resultados_puntuaciones()
    await update.message.reply_text("")



def main():

    if not TOKEN:
        print('no token')
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("nueva_jornada", nueva_jornada))
    app.add_handler(CommandHandler("nueva_apuesta", nueva_apuesta))
    app.add_handler(CommandHandler("actualiza", actualiza))

    logger.info(f"Bot en marcha")
    app.run_polling()

if __name__ == "__main__":
    main()
