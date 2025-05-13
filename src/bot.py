
import os
import boto3
import logging
import watchtower
from api import generar_nueva_plantilla_jornada, obtener_resultado_jornada_actual_pd
from telegram import Update, Document
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

esperando_archivo = set()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Config logger for CloudWatch
logger = logging.getLogger("quiniela_quinigol_bot")
logger.setLevel(logging.INFO)
boto3_client=boto3.client("logs", region_name="eu-west-1")
logger.addHandler(watchtower.CloudWatchLogHandler(log_group_name="QuiniBot", boto3_client=boto3_client))

async def descargar_plantilla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    generar_nueva_plantilla_jornada()
    logger.info(f"Descargar plantilla")
    await update.message.reply_document(document=open('output.xlsx', "rb"), filename="quiniela_quinigol.xlsx")

async def nueva_jornada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    esperando_archivo.add(update.effective_user.id)
    logger.info(f"Nueva jornada")
    await update.message.reply_text("Envíame el archivo Excel (formato .xlsx o .xls).")

async def resultados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Obtener resultados")
    result = obtener_resultado_jornada_actual_pd()
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)

async def recibir_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    document: Document = update.message.document
    logger.info(f"Recibir documento")

    if user_id not in esperando_archivo:
        logger.warning(f"Falta primero /nueva_jornada")
        await update.message.reply_text("Por favor, primero usa el comando /nueva_jornada.")
        return

    if not document.file_name.endswith((".xlsx", ".xls")):
        logger.warning(f"El archivo subido no es excel")
        await update.message.reply_text("El archivo debe ser Excel (.xlsx o .xls).")
        return

    file = await context.bot.get_file(document.file_id)
    await file.download_to_drive(custom_path=document.file_name)

    esperando_archivo.remove(user_id)
    logger.info(f"Se descarga el fichero")
    await update.message.reply_text("Recibido y guardado :)")

def main():

    if not TOKEN:
        print('no token')
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("nueva_jornada", nueva_jornada))
    app.add_handler(CommandHandler("resultados", resultados))
    app.add_handler(CommandHandler("descargar_plantilla", descargar_plantilla))
    app.add_handler(MessageHandler(filters.Document.ALL, recibir_documento))

    logger.info(f"Bot en marcha")
    app.run_polling()

if __name__ == "__main__":
    main()
