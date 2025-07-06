from langchain_google_community import GoogleSearchAPIWrapper
from langchain_google_community.search import GoogleSearchRun
from langchain_core.tools import tool

import requests
from bs4 import BeautifulSoup

from utils import get_google_api_keys

# Get API keys
GOOGLE_API_KEY, GOOGLE_CSE_ID = get_google_api_keys()

# Web search tool
web_search_api_wrapper = GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID,
        k=1)

def init_web_search_tool():
    return GoogleSearchRun(api_wrapper=web_search_api_wrapper)
    
@tool
def get_french_vat_from_bofip() -> str:
    """
    Extrait les informations principales sur les taux de TVA à partir de la page BOFiP officielle.
    Résumer et bien formuler le contenu du (des) résultat(s) trouvé(s).
    """
    url = "https://bofip.impots.gouv.fr/bofip/1380-PGP.html/identifiant%3DBOI-TVA-LIQ-10-20250514"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    content = soup.find('content', class_='field--name-body')
    if content:
        content_text = content.get_text() # To get just the text inside the content
        return content_text
    else:
        return "Aucune information pertinente trouvée!"

#********************************************************************#
