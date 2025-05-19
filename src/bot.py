
from api import genera_mensaje_nueva_jornada, render_apuestas_html
from utils import carga_apuestas_jugador

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from config import config
from utils import verificar_usuario_permitido


@verificar_usuario_permitido
async def nueva_jornada(update: Update, context: ContextTypes.DEFAULT_TYPE):

    config.apuestas = {}
    config.responsabe_id = update.effective_user.id
    user_name = update.effective_user.full_name
    config.logger.info(f"Se inicia jornada por {user_name}")
    await update.message.reply_text(f"Hola {user_name}, eres el responsable esta jornada")
    await update.message.reply_text(f"A continuación te adjunto la plantilla con la información que necesito que cada uno me envie por privado")
    quiniela, quinigol = genera_mensaje_nueva_jornada()
    await update.message.reply_text(f"/nueva_apuesta\n\n{quiniela}\n\n{quinigol}")

@verificar_usuario_permitido
async def nueva_apuesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.responsabe_id is None:
        config.logger.warning(f"Intento de apuesta sin jornada iniciada")
        await update.message.reply_text(f"Atención: La jornada no está iniciada")
        await update.message.reply_text(f"El respondable la debe iniciar con el comando /nueva_jornada")
        return

    user_name = update.effective_user.full_name
    user_id = update.effective_user.id
    config.logger.info(f"Apuesta recibida de {user_name}")
    config.logger.info(f"Apuesta recibida de {user_name}")
    texto_enviado = ' '.join(context.args)
    if texto_enviado == "":
        config.logger.warning(f"La apuesta no tiene texto")
        await update.message.reply_text(f"Necesito que adjuntes la plantilla con los partidos")
        return

    if user_id in config.apuestas:
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

    config.apuestas[user_id] = {
        'quiniela': quiniela,
        'quinigol': quinigol
    }

    config.logger.info(f"Apuesta guardada")

    await update.message.reply_text(f"Recibido y guardado. Mucha suerte!")
    await context.bot.send_message(chat_id=config.responsabe_id, text=f"El pronóstico de {user_name}:\n\n{mensaje}")

    if len(config.apuestas) == 6:
        await context.bot.send_message(chat_id=config.responsabe_id, text=f"Ya he recibido todas las apuestas")
        status = render_apuestas_html()
        if status:
            await context.bot.send_message(chat_id=config.responsabe_id, text=f"Renderizando los resultados en html...")
            await context.bot.send_message(chat_id=config.responsabe_id, text=f"Página: https://andresmarinabad.github.io/quiniela_quinigol_bot")


@verificar_usuario_permitido
async def puntuaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.logger.info(f"Obtener resultados")
    #result = obtener_resultados_puntuaciones()
    await update.message.reply_text("")


async def hola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.full_name
    user_id = update.effective_user.id
    config.logger.info(f"Se presenta el usuario {user_name}")
    await context.bot.send_message(chat_id=config.admin, text=f"Solicita acceso el usuario {user_name} con id {user_id}")
    render_apuestas_html()



def main():

    if not config.TOKEN:
        config.logger.error(f"No hay token")
        return

    app = ApplicationBuilder().token(config.TOKEN).build()
    app.add_handler(CommandHandler("hola", hola))
    app.add_handler(CommandHandler("nueva_jornada", nueva_jornada))
    app.add_handler(CommandHandler("nueva_apuesta", nueva_apuesta))
    app.add_handler(CommandHandler("puntuaciones", puntuaciones))

    config.logger.info(f"Bot en marcha")
    app.run_polling()

if __name__ == "__main__":
    main()
