import re
import json
from collections import defaultdict

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config import config


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
        r"([A-Za-zÁÉÍÓÚÑáéíóúü0-9.\- ]+ - [A-Za-zÁÉÍÓÚÑáéíóúü0-9.\- ]+):\s*([12Xx])", quiniela_part)

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


def render_apuestas_html():
    partidos_json = json.dumps(config.info_tabla)
    apuestas_json = json.dumps(config.apuestas)

    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE_NAME}/dispatches"



def asignar_puntuaciones(analisis_partidos, todas_las_personas):
    puntuaciones = defaultdict(float)

    # Asegurar que todos empiecen con 0 puntos
    for persona in todas_las_personas:
        puntuaciones[persona] = 0.0

    for partido in analisis_partidos:
        # --- Quiniela ---
        quiniela = partido['quiniela_aciertos']
        n_quiniela = len(quiniela)

        if n_quiniela == 1:
            puntos_q = 3
        elif n_quiniela == 2:
            puntos_q = 2
        elif 3 <= n_quiniela <= 4:
            puntos_q = 1.5
        elif n_quiniela >= 5:
            puntos_q = 1
        else:
            puntos_q = 0

        for persona in quiniela:
            puntuaciones[persona] += puntos_q

        # --- Quinigol ---
        quinigol = partido['quinigol_aciertos']
        n_quinigol = len(quinigol)

        if n_quinigol == 1:
            puntos_gol = 3
        elif 2 <= n_quinigol <= 3:
            puntos_gol = 2
        elif 4 <= n_quinigol <= 6:
            puntos_gol = 1
        else:
            puntos_gol = 0

        for persona in quinigol:
            puntuaciones[persona] += puntos_gol

    # --- Bonus al final: Quiniela global ---
    if puntuaciones:
        max_puntos = max(puntuaciones.values())
        min_puntos = min(puntuaciones.values())

        ganadores = [p for p, pts in puntuaciones.items() if pts == max_puntos]
        perdedores = [p for p, pts in puntuaciones.items() if pts == min_puntos]

        if len(ganadores) == 1:
            puntuaciones[ganadores[0]] += 1

        if len(perdedores) == 1:
            puntuaciones[perdedores[0]] -= 1

    return dict(puntuaciones)