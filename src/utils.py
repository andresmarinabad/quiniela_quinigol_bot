import re

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config import config
from api import obtener_resultados_reales


def verificar_usuario_permitido(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user.id
        if user not in config.usuarios_permitidos:
            await update.message.reply_text(f"No tienes permiso para interactuar con este bot.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def carga_apuestas_jugador(texto):

    mensaje_quiniela = '## QUINIELA ##\n'
    mensaje_quinigol = '## QUINIGOL ##\n'
    quiniela = []
    quinigol = []

    texto = texto.strip()

    # Dividir en secciones
    if "## QUINIGOL ##" in texto:
        quiniela_part, quinigol_part = texto.split("## QUINIGOL ##", 1)
    else:
        quiniela_part = texto
        quinigol_part = ""

    quiniela_part = quiniela_part.replace("## QUINIELA ##", "").strip()
    quinigol_part = quinigol_part.strip()

    # QUINIELA: resultado debe ser 1, X o 2
    partidos_quiniela = re.findall(
        r"([A-Za-zÁÉÍÓÚÑáéíóúü0-9.\- ]+ - [A-Za-zÁÉÍÓÚÑáéíóúü0-9.\- ]+):\s*([12Xx\-])", quiniela_part)

    # QUINIGOL: resultado tipo n-n o M-n o n-M o M-M
    partidos_quinigol = re.findall(
        r"([A-Za-zÁÉÍÓÚÑáéíóúü0-9.\- ]+ - [A-Za-zÁÉÍÓÚÑáéíóúü0-9.\- ]+):\s*([0-9M]-[0-9M])", quinigol_part)

    for partido, result in partidos_quiniela:
        mensaje_quiniela = f'{mensaje_quiniela}\n{partido.strip()}: {result.strip().upper()}'
        quiniela.append((result.strip().upper()))

    for partido, result in partidos_quinigol:
        mensaje_quinigol = f'{mensaje_quinigol}\n{partido.strip()}: {result.strip().upper()}'
        quinigol.append((result.upper()))

    return quiniela, quinigol, f'{mensaje_quiniela}\n\n{mensaje_quinigol}'



def calcular_puntuaciones() -> str:

    apuestas = config.apuestas
    resultados = obtener_resultados_reales()

    usuarios = list(apuestas.keys())
    puntuaciones_quiniela = {u: 0 for u in usuarios}
    puntuaciones_quinigol = {u: 0 for u in usuarios}
    aciertos_quiniela = {u: 0 for u in usuarios}
    bonus_quiniela = {u: 0 for u in usuarios}

    # Calcular puntos para QUINIELA
    for i, resultado_real in enumerate(resultados['quiniela']):
        aciertos = [u for u in usuarios if apuestas[u]['quiniela'][i] == resultado_real]
        n = len(aciertos)

        for u in aciertos_quiniela:
            aciertos_quiniela[u] += aciertos.count(u)

        if n in [5, 6]:
            puntos = 1
        elif n in [3, 4]:
            puntos = 1.5
        elif n == 2:
            puntos = 2
        elif n == 1:
            puntos = 3
        else:
            puntos = 0

        for u in aciertos:
            puntuaciones_quiniela[u] += puntos

    # Calcular puntos para QUINIGOL
    for i, resultado_real in enumerate(resultados['quinigol']):
        aciertos = [u for u in usuarios if apuestas[u]['quinigol'][i] == resultado_real]
        n = len(aciertos)

        if n in [4, 5, 6]:
            puntos = 1
        elif n in [2, 3]:
            puntos = 2
        elif n == 1:
            puntos = 3
        else:
            puntos = 0

        for u in aciertos:
            puntuaciones_quinigol[u] += puntos

    # BONUS Quiniela: al que más +1, al que menos -1 (si no hay empate)
    valores = list(aciertos_quiniela.values())
    max_val = max(valores)
    min_val = min(valores)

    maximos = [usuario for usuario, puntos in aciertos_quiniela.items() if puntos == max_val]
    minimos = [usuario for usuario, puntos in aciertos_quiniela.items() if puntos == min_val]

    if len(maximos) == 1:
        bonus_quiniela[maximos[0]] = 1

    # Restar 1 al único con mínimo, si no hay empate
    if len(minimos) == 1:
        bonus_quiniela[minimos[0]] = -1

    # Resultado final
    resultado_final = {}
    for u in usuarios:
        resultado_final[u] = {
            "quiniela": puntuaciones_quiniela[u],
            "quinigol": puntuaciones_quinigol[u],
            "bonus": bonus_quiniela[u],
            "puntos": puntuaciones_quiniela[u] + puntuaciones_quinigol[u] + bonus_quiniela[u]
        }

    mensaje = 'RESUMEN JORNADA:\n'
    mensaje += '\n'.join(
        (
            f"{persona}: {resultados['puntos']}"
            if sum(val != 0 for val in [resultados['quiniela'], resultados['quinigol'], resultados['bonus']]) == 1
            else (
                f"{persona}: {' + '.join(str(val) for val in [resultados['quiniela'], resultados['quinigol'], resultados['bonus']] if val != 0)} = {resultados['puntos']}"
                if resultados['puntos'] > 0 else f"{persona}: 0"
            )
        )
        for persona, resultados in resultado_final.items()
    )
    return mensaje

