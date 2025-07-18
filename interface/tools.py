from langchain_google_community import GoogleSearchAPIWrapper
from langchain_google_community.search import GoogleSearchRun

from playwright.sync_api import sync_playwright

from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.tools import tool
from utils import get_google_api_keys

# Get API keys
GOOGLE_API_KEY, GOOGLE_CSE_ID = get_google_api_keys()

#********************************************************************#
# Web search tool
#********************************************************************#
web_search_api_wrapper = GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID,
        k=1)

def init_web_search_tool():
    return GoogleSearchRun(api_wrapper=web_search_api_wrapper)
    
@tool
def get_french_vat_from_bofip(url: str) -> str:
    """
    Extrait les informations principales sur les taux de TVA à partir de la page BOFiP officielle.
    Résumer et bien formuler le contenu du (des) résultat(s) trouvé(s) sur {url}.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle") # Wait for JS content to load
        content = page.inner_text("body")
        browser.close()

    if content:
        return content
    else:
        return None

#********************************************************************#
# RAG tool
#********************************************************************#

# Load persisted vectorstore + embeddings
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="./chroma_store", embedding_function=embedder)
retriever = vectorstore.as_retriever(search_type="similarity")

@tool("search_regles_de_gestion")
def rag_answer_tool(question: str) -> str:
    """
    Utilise la base de règles ChromaDB pour répondre aux questions sur les conformités du e-invoices, etc.
    Retourner une seule réponse finale et détaillée pour tous les recherches.
    """
    docs = retriever.get_relevant_documents(question)
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

