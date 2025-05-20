import json
import requests
from bs4 import BeautifulSoup

from config import config

apuestas_headers = {
    "User-Agent": "Mozilla/5.0"
}

github_headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {config.GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}


def obtener_resultados_reales():

    response_quiniela = requests.get(config.url_quiniela, headers=apuestas_headers)
    response_quinigol = requests.get(config.url_quinigol, headers=apuestas_headers)
    response_quiniela.raise_for_status()
    response_quinigol.raise_for_status()

    resultados = {
        'quiniela': [],
        'quinigol': []
    }

    # QUINIELA
    soup = BeautifulSoup(response_quiniela.content, "html.parser")

    trs = soup.select("table.matchTable tr")
    for i, tr in enumerate(trs, start=1):
        td_fecha = tr.find('td', attrs={'data-matchdate': True})
        if not td_fecha:
            continue

        filas_internas = td_fecha.select('div.row.collapse')
        if len(filas_internas) > 1:
            resultados_activados = []
            for fila in filas_internas:
                activo = fila.select_one('.bQuiniela.is-active')
                if activo:
                    resultados_activados.append(activo.text.strip())
            result = '-'.join(resultados_activados) if resultados_activados else 'NOJUGADO'

        else:
            activo = td_fecha.select_one('.bQuiniela.is-active')
            result = activo.text.strip() if activo else 'NOJUGADO'

        resultados['quiniela'].append(result)


    # QUINIGOL
    soup = BeautifulSoup(response_quinigol.content, "html.parser")

    for i, tr in enumerate(soup.select("table.matchTable tr.brdcQuinigol"), start=1):
        td_resultado = tr.find("td", {"data-matchdate": True})
        if not td_resultado:
            continue

        rows = td_resultado.select("div.row.collapse")
        if len(rows) != 2:
            continue

        # Extraer el span con clase is-active en cada fila
        local_span = rows[0].select_one("span.is-active")
        visitante_span = rows[1].select_one("span.is-active")

        if local_span and visitante_span:
            resultado = f"{local_span.text.strip()}-{visitante_span.text.strip()}"
            resultados['quinigol'].append(resultado)
        else:
            resultados['quinigol'].append('NOJUGADO')

    return resultados


def genera_mensaje_nueva_jornada():

    response_quiniela = requests.get(config.url_quiniela, headers=apuestas_headers)
    response_quinigol = requests.get(config.url_quinigol, headers=apuestas_headers)
    response_quiniela.raise_for_status()
    response_quinigol.raise_for_status()

    quiniela = '## QUINIELA ##'
    quinigol = '## QUINIGOL ##'

    soup = BeautifulSoup(response_quiniela.content, "html.parser")
    rows = soup.select("table.matchTable tr")
    for row in rows:
        match_td = row.find("td", {"data-matches": True})
        if match_td:
            local = match_td.find("span", {"data-m1": True})
            visitante = match_td.find("span", {"data-m2": True})

            quiniela = f"{quiniela}\n{local.text.strip()} - {visitante.text.strip()}:"
            config.info_tabla['quiniela'].append(f'{local.text.strip()} - {visitante.text.strip()}')


    soup = BeautifulSoup(response_quinigol.content, "html.parser")
    rows = soup.select("table.matchTable tr")
    for row in rows:
        match_td = row.find("td", {"data-matches": True})
        if match_td:
            local = match_td.find("span", {"data-m1": True})
            visitante = match_td.find("span", {"data-m2": True})

            quinigol = f"{quinigol}\n{local.text.strip()} - {visitante.text.strip()}:"
            config.info_tabla['quinigol'].append(f'{local.text.strip()} - {visitante.text.strip()}')

    return quiniela, quinigol


def render_apuestas_html():

    data = {
        "ref": 'main',
        "inputs": {
            "apuestas_json": json.dumps(config.apuestas),
            "partidos_json": json.dumps(config.info_tabla)
        }
    }

    response = requests.post(config.render_action, headers=github_headers, json=data)

    if response.status_code == 204:
        return True
    else:
        return False

def reiniciar_instancia():

    response = requests.post(config.terminate_action, headers=github_headers)

    if response.status_code == 204:
        return True
    else:
        return False