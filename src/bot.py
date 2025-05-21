import time

from api import genera_mensaje_nueva_jornada, render_apuestas_html, reiniciar_instancia
from utils import carga_apuestas_jugador, calcular_puntuaciones

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes, CallbackQueryHandler

from config import config
from utils import verificar_usuario_permitido


@verificar_usuario_permitido
async def nueva_jornada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.responsabe_id is not None:
        user = await context.bot.get_chat(config.responsabe_id)
        await update.message.reply_text(f"La jornada ya ha sido iniciada por {user.first_name} {user.last_name}")
        return

    config.apuestas = {}
    config.responsabe_id = update.effective_user.id
    user_name = update.effective_user.full_name
    config.logger.info(f"Se inicia jornada por {user_name}")
    await update.message.reply_text(f"Hola {user_name}, eres el responsable esta jornada")
    await update.message.reply_text(f"A continuación te adjunto la plantilla con la información que necesito que cada uno me envie por privado")
    quiniela, quinigol = genera_mensaje_nueva_jornada()
    await update.message.reply_text(f"/nueva_apuesta\n\n{quiniela}\n\n{quinigol}")
    await update.message.reply_text(f"Utiliza el comando /reiniciar al final de la jornada para resetearme")


@verificar_usuario_permitido
async def nueva_apuesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.responsabe_id is None:
        config.logger.warning(f"Intento de apuesta sin jornada iniciada")
        await update.message.reply_text(f"Atención: La jornada no está iniciada")
        await update.message.reply_text(f"El respondable la debe iniciar con el comando /nueva_jornada")
        return

    user_name = update.effective_user.full_name
    config.logger.info(f"Apuesta recibida de {user_name}")
    config.logger.info(f"Apuesta recibida de {user_name}")
    texto_enviado = ' '.join(context.args)
    if texto_enviado == "":
        config.logger.warning(f"La apuesta no tiene texto")
        await update.message.reply_text(f"Necesito que adjuntes la plantilla con los partidos")
        return

    if user_name in config.apuestas:
        await update.message.reply_text(f"Ya habías enviado una apuesta empanao!")
        user = await context.bot.get_chat(config.responsabe_id)
        await update.message.reply_text(f"Contacta por privado con {user.first_name} {user.last_name} si necesitas modificar algo.")
        await context.bot.send_message(chat_id=config.responsabe_id, text=f"Tramposo detectado: el usuario {user_name} ha tratado de enviar una segunda apuesta")
        return

    quiniela, quinigol, mensaje = carga_apuestas_jugador(texto_enviado)

    if len(quiniela) < 15 or len(quinigol) < 6:
        config.logger.warning(f"Algunos de los resultados no está bien informado")
        await update.message.reply_text(f"Uno de los resultados está vacío. Revísalo y reenvía por favor.")
        return

    config.apuestas[user_name] = {
        'quiniela': quiniela,
        'quinigol': quinigol
    }

    config.logger.info(f"Apuesta guardada")

    await update.message.reply_text(f"Recibido y guardado. Mucha suerte!")
    await context.bot.send_message(chat_id=config.responsabe_id, text=f"El pronóstico de {user_name}:\n\n{mensaje}")

    if len(config.apuestas) == 6:
        await context.bot.send_message(chat_id=config.responsabe_id, text=f"Ya he recibido todas las apuestas")
        render_apuestas_html()
        await context.bot.send_message(chat_id=config.responsabe_id, text=f"Renderizo los resultados en html...")
        time.sleep(15)
        await context.bot.send_message(chat_id=config.responsabe_id, text=f"Ya tienes las apuestas en la mini app")


@verificar_usuario_permitido
async def puntuaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.logger.info(f"Obtener resultados")
    mensaje = calcular_puntuaciones()
    await update.message.reply_text("Estas son las puntuaciones actuales según los partidos que ya han finalizado:")
    await update.message.reply_text(f"{mensaje}")


async def hola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    genera_mensaje_nueva_jornada()
    render_apuestas_html()
    user_name = update.effective_user.full_name
    user_id = update.effective_user.id
    config.logger.info(f"Se presenta el usuario {user_name}")
    await context.bot.send_message(chat_id=config.admin, text=f"Solicita acceso el usuario {user_name} con id {user_id}")


@verificar_usuario_permitido
async def reiniciar(update: Update, context: CallbackContext):
    if config.responsabe_id is None:
        await update.message.reply_text(f"Buen intento. Pero va a ser que no")
        return

    user_id = update.effective_user.id
    if config.responsabe_id != user_id:
        await update.message.reply_text(f"HAHAHA, No tienes poder aquí!")
        return

    else:
        keyboard = [
            [
                InlineKeyboardButton("Con gran pesar, Sí", callback_data='confirmar_si'),
                InlineKeyboardButton("No", callback_data='confirmar_no')
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "¿Estás seguro de que quieres reiniciar tu bot favorito?",
            reply_markup=reply_markup
        )


async def manejar_confirmacion(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'confirmar_si':
        await query.edit_message_text("Adiós mundo cruel!")
        reiniciar_instancia()
    elif query.data == 'confirmar_no':
        await query.edit_message_text("❌ Cancelado. Tu bot está a salvo.")


def main():

    if not config.TOKEN:
        config.logger.error(f"No hay token")
        return

    app = ApplicationBuilder().token(config.TOKEN).build()
    app.add_handler(CommandHandler("hola", hola))
    app.add_handler(CommandHandler("nueva_jornada", nueva_jornada))
    app.add_handler(CommandHandler("nueva_apuesta", nueva_apuesta))
    app.add_handler(CommandHandler("puntuaciones", puntuaciones))
    app.add_handler(CommandHandler("reiniciar", reiniciar))
    app.add_handler(CallbackQueryHandler(manejar_confirmacion, pattern='^confirmar_'))


    config.logger.info(f"Bot en marcha")
    app.run_polling()

if __name__ == "__main__":
    main()
