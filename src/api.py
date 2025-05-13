import os
import requests
import pandas as pd
from openpyxl import load_workbook
from collections import defaultdict
#from bot import #logger

FUTBALL_TOKEN = os.getenv("FUTBALL_API_TOKEN")

BASE_URL = 'https://api.football-data.org/v4'
HEADERS = {
    'X-Auth-Token': FUTBALL_TOKEN
}


def asignar_puntuaciones(analisis_partidos):
    puntuaciones = defaultdict(float)
    #logger.debug(puntuaciones)

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

        #logger.debug(quiniela)
        for persona in quiniela:
            puntuaciones[persona] += puntos_q

        #logger.debug(puntuaciones)

        max_puntos = max(puntuaciones.values())
        min_puntos = min(puntuaciones.values())

        ganadores = [persona for persona, puntos in puntuaciones.items() if puntos == max_puntos]
        #logger.debug(f"Max aciertos en quiniela: {ganadores}")
        perdedores = [persona for persona, puntos in puntuaciones.items() if puntos == min_puntos]
        #logger.debug(f"Min aciertos en quiniela: {perdedores}")

        if len(ganadores) == 1:
            #logger.debug(f"{ganadores[0]} suma 1")
            puntuaciones[ganadores[0]] += 1

        # Si hay un único perdedor, se le resta 1
        if len(perdedores) == 1:
            #logger.debug(f"{perdedores[0]} resta 1")
            puntuaciones[perdedores[0]] -= 1

        # --- Quinigol ---
        quinigol = partido['quinigol_aciertos']
        n_quinigol = len(quinigol)
        #logger.debug(n_quinigol)

        if n_quinigol == 1:
            puntos_gol = 3
        elif 2 <= n_quinigol <= 3:
            puntos_gol = 2
        elif 4 <= n_quinigol <= 6:
            puntos_gol = 1
        else:
            puntos_gol = 0

        #logger.debug(quinigol)
        for persona in quinigol:
            puntuaciones[persona] += puntos_gol

        #logger.debug(puntuaciones)

    return dict(puntuaciones)


def analizar_resultados(predicciones, resultados_reales):
    resultados = []

    #logger.debug(predicciones)
    #logger.debug(resultados_reales)

    for pred, real in zip(predicciones, resultados_reales):
        partido_info = {
            "local": pred["local"],
            "visitante": pred["visitante"],
            "resultado_real": real["resultado"],
            "quiniela_aciertos": [],
            "quinigol_aciertos": []
        }

        #logger.debug(partido_info)

        try:
            goles_local_real, goles_visitante_real = map(int, partido_info["resultado_real"].split('-'))
        except:
            #logger.debug("Resultado mal formado")
            continue

        for persona, pronostico in pred["pronosticos"].items():
            try:
                goles_local_pred, goles_visitante_pred = map(int, pronostico.split('-'))
            except:
                #logger.debug("Pronostico mal formado")
                continue

            if goles_local_pred == goles_local_real and goles_visitante_pred == goles_visitante_real:
                partido_info["quinigol_aciertos"].append(persona)

            # Comprobación de quiniela (quién ganó)
            def signo(goles1, goles2):
                return "L" if goles1 > goles2 else "V" if goles1 < goles2 else "E"

            if signo(goles_local_pred, goles_visitante_pred) == signo(goles_local_real, goles_visitante_real):
                partido_info["quiniela_aciertos"].append(persona)

        #logger.debug(partido_info)
        resultados.append(partido_info)

    #logger.debug(resultados)
    return resultados


def cargar_quinigol():

    df = pd.read_excel('quiniela_quinigol.xlsx', sheet_name='quinigol', header=1)
    df = df.dropna(subset=["Local", "Visitante"], how="all")

    columnas = df.columns.tolist()
    personas = columnas[2:]

    #logger.debug(columnas)
    #logger.debug(personas)

    quinigol = []

    for _, fila in df.iterrows():
        partido = {
            "local": fila["Local"],
            "visitante": fila["Visitante"],
            "pronosticos": {}
        }
        #logger.debug(partido)
        for persona in personas:
            pronostico = fila.get(persona)
            if pd.notna(pronostico):
                partido["pronosticos"][persona] = pronostico
        quinigol.append(partido)

    #logger.debug(quinigol)
    return quinigol


def obtener_resultado_jornada_actual_pd():
    url = f'{BASE_URL}/competitions/PD/matches?status=FINISHED'
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f'Error {response.status_code}: {response.text}')
        return

    datos = response.json()
    partidos_por_jornada = {}
    #logger.debug(datos)

    for partido in datos['matches']:
        jornada = partido['matchday']
        if jornada not in partidos_por_jornada:
            partidos_por_jornada[jornada] = []
        partidos_por_jornada[jornada].append(partido)
    #logger.debug(partidos_por_jornada)

    jornada_actual = max(partidos_por_jornada.keys())
    print(partidos_por_jornada)

    quinigol = cargar_quinigol()
    resultados = []
    #logger.debug(quinigol)

    respuesta = '*Resultados:*\n\n'

    for partido in partidos_por_jornada[jornada_actual]:
        resultado = {
            "local": partido['homeTeam']['name'],
            "visitante": partido['awayTeam']['name'],
            "resultado": f"{partido['score']['fullTime']['home']}-{partido['score']['fullTime']['away']}"
        }
        respuesta = f'{respuesta}{resultado["local"]} vs {resultado["visitante"]}: {resultado["resultado"]}\n'
        resultados.append(resultado)
        #logger.debug(resultado)

    quiniela = analizar_resultados(quinigol, resultados)
    puntos = asignar_puntuaciones(quiniela)

    respuesta = f'{respuesta}\n\n*Puntuaciones:*\n\n'
    for persona, puntuacion in puntos.items():
        respuesta = f'{respuesta}{persona}:{puntuacion}\n'

    #logger.debug(puntos)
    #logger.debug(respuesta)
    return respuesta


def generar_nueva_plantilla_jornada():
    url = f'{BASE_URL}/competitions/PD/matches?status=SCHEDULED'
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f'Error {response.status_code}: {response.text}')
        return

    datos = response.json()
    partidos_por_jornada = {}
    #logger.debug(datos)

    for partido in datos['matches']:
        jornada = partido['matchday']
        if jornada not in partidos_por_jornada:
            partidos_por_jornada[jornada] = []
        partidos_por_jornada[jornada].append(partido)
    #logger.debug(partidos_por_jornada)

    proxima_jornada = min(partidos_por_jornada.keys())

    wb = load_workbook('template.xlsx')
    ws = wb.active
    fila = 3

    ws.cell(row=1, column=1, value=f'Jornada {proxima_jornada}')

    for partido in partidos_por_jornada[proxima_jornada]:
        local = partido['homeTeam']['name']
        visitante = partido['awayTeam']['name']

        ws.cell(row=fila, column=1, value=local)
        ws.cell(row=fila, column=2, value=visitante)
        fila += 1

    #logger.debug("Se guarda el fichero output.xlsx")
    wb.save('output.xlsx')
