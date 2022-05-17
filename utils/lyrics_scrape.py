import requests
from bs4 import BeautifulSoup


def get_lyrics(data):
    url = data["url"]
    final = ""

    soup = BeautifulSoup(requests.get(url).content, 'lxml')

    for line in soup.find_all('div', {'data-lyrics-container': 'true'}):
        t = line.get_text(strip=True, separator='\n')
        if t:
            final += t

    return final
