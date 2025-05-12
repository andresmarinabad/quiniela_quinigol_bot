import requests

API_KEY = '2a27d19a25d34c80b087f48149127cd5'  # Reemplaza con tu clave real
BASE_URL = 'https://api.football-data.org/v4'

HEADERS = {
    'X-Auth-Token': API_KEY
}

def obtener_jornada_actual_pd():
    url = f'{BASE_URL}/competitions/PD/matches?status=FINISHED'
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f'Error {response.status_code}: {response.text}')
        return

    datos = response.json()
    partidos_por_jornada = {}

    for partido in datos['matches']:
        jornada = partido['matchday']
        if jornada not in partidos_por_jornada:
            partidos_por_jornada[jornada] = []
        partidos_por_jornada[jornada].append(partido)

    jornada_actual = max(partidos_por_jornada.keys())
    print(f"Resultados de la jornada {jornada_actual}:\n")

    for partido in partidos_por_jornada[jornada_actual]:
        local = partido['homeTeam']['name']
        visitante = partido['awayTeam']['name']
        resultado = f"{partido['score']['fullTime']['home']} - {partido['score']['fullTime']['away']}"
        print(f"{local} {resultado} {visitante}")


def obtener_proxima_jornada_pd():
    url = f'{BASE_URL}/competitions/PD/matches?status=SCHEDULED'
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f'Error {response.status_code}: {response.text}')
        return

    datos = response.json()
    partidos_por_jornada = {}

    for partido in datos['matches']:
        jornada = partido['matchday']
        if jornada not in partidos_por_jornada:
            partidos_por_jornada[jornada] = []
        partidos_por_jornada[jornada].append(partido)

    proxima_jornada = min(partidos_por_jornada.keys())
    print(f"Partidos de la próxima jornada ({proxima_jornada}):\n")

    for partido in partidos_por_jornada[proxima_jornada]:
        local = partido['homeTeam']['name']
        visitante = partido['awayTeam']['name']
        print(f"{local} - {visitante}")


obtener_proxima_jornada_pd()
