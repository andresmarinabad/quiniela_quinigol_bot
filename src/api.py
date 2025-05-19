
import requests
from bs4 import BeautifulSoup

from config import config


def genera_mensaje_nueva_jornada():
    url_quiniela = "https://www.combinacionganadora.com/quiniela/"
    url_quinigol = "https://www.combinacionganadora.com/quinigol/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response_quiniela = requests.get(url_quiniela, headers=headers)
    response_quinigol = requests.get(url_quinigol, headers=headers)
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

    #logger.debug("Se guarda el fichero output.xlsx")
    return quiniela, quinigol
