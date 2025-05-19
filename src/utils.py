import re

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from collections import defaultdict

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



def calcular_puntuaciones() -> dict:

    #apuestas = config.apuestas

    apuestas = {
      "Juanra": {
        "quiniela": ["1", "1", "1", "1", "1", "1", "X", "1", "2", "1", "2", "X", "1", "1", "-"],
        "quinigol": ["M-1", "M-1", "2-2", "2-2", "1-M", "1-2"]
      },
      "Keysals": {
        "quiniela": ["2", "X", "1", "X", "1", "1", "X", "2", "2", "1", "2", "1", "2", "1", "-"],
        "quinigol": ["2-M", "1-0", "1-M", "1-1", "1-M", "0-0"]
      },
      "Luisme": {
        "quiniela": ["2", "X", "1", "X", "1", "1", "2", "2", "2", "1", "2", "1", "X", "1", "-"],
        "quinigol": ["2-2", "M-2", "1-2", "1-2", "1-M", "0-1"]
      },
      "Serraba": {
        "quiniela": ["2", "X", "1", "X", "1", "1", "1", "X", "X", "1", "2", "1", "2", "1", "-"],
        "quinigol": ["1-1", "M-1", "1-1", "1-1", "1-1", "1-1"]
      },
      "Nacho": {
        "quiniela": ["X", "2", "1", "X", "1", "X", "1", "2", "2", "1", "X", "2", "1", "1", "-"],
        "quinigol": ["1-M", "1-1", "1-2", "1-2", "1-M", "1-2"]
      },
      "Edu": {
        "quiniela": ["2", "2", "1", "2", "1", "1", "2", "1", "2", "1", "2", "1", "2", "1", "2-M"],
        "quinigol": ["1-2", "M-0", "1-2", "2-0", "1-M", "0-2"]
      }
}

    resultados = {
      "quiniela": [
        "2",
        "2",
        "1",
        "1",
        "1",
        "1",
        "1",
        "X",
        "2",
        "1",
        "X",
        "2",
        "2",
        "2",
        "0-2"
      ],
      "quinigol": [
        "0-1",
        "2-1",
        "2-0",
        "2-2",
        "0-2",
        "0-2"
      ]
    }

    usuarios = list(apuestas.keys())
    puntuaciones_quiniela = {u: 0 for u in usuarios}
    puntuaciones_quinigol = {u: 0 for u in usuarios}

    # Calcular puntos para QUINIELA
    for i, resultado_real in enumerate(resultados['quiniela']):
        aciertos = [u for u in usuarios if apuestas[u]['quiniela'][i] == resultado_real]
        n = len(aciertos)

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
    max_q = max(puntuaciones_quiniela.values())
    min_q = min(puntuaciones_quiniela.values())

    usuarios_max = [u for u, p in puntuaciones_quiniela.items() if p == max_q]
    usuarios_min = [u for u, p in puntuaciones_quiniela.items() if p == min_q]

    if len(usuarios_max) == 1 and len(usuarios_min) == 1:
        puntuaciones_quiniela[usuarios_max[0]] += 1
        puntuaciones_quiniela[usuarios_min[0]] -= 1

    # Resultado final
    resultado_final = {}
    for u in usuarios:
        resultado_final[u] = {
            "quiniela": puntuaciones_quiniela[u],
            "quinigol": puntuaciones_quinigol[u],
            "puntos": puntuaciones_quiniela[u] + puntuaciones_quinigol[u]
        }

    return resultado_final

print(calcular_puntuaciones())