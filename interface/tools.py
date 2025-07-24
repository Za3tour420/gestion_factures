from langchain_google_community import GoogleSearchAPIWrapper
from langchain_google_community.search import GoogleSearchRun

from playwright.sync_api import sync_playwright

from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.tools import tool
from utils import get_google_api_keys

from typing import Optional

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

@tool("search_regles_de_gestion")
def rag_management_rules(question: str, rule_id: Optional[str] = None) -> str:
    """
    Utilise la base de règles de gestion ChromaDB pour répondre aux questions sur les conformités et règles de gestion des e-invoices, etc.
    Déduire rule_id de la question si elle est mentionnée. Elle est de la forme GX.XX.
    Questionner la base en résumant le contenu de la requête.
    Retourner une seule réponse finale et détaillée pour tous les recherches.
    """
    print(f"🔎 RAG management rules tool called with: {question} | rule ID: {rule_id}")
    
    # Load persisted vectorstore + embeddings
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory="./knowledge_bases/regles_gestion", embedding_function=embedder)
    retriever = vectorstore.as_retriever(search_type="mmr", k=5)
    
    # Get docs
    if rule_id:
        docs = retriever.invoke(question, filter={"id_règle": rule_id})
    else:
        docs = retriever.invoke(question)
        
    print(f"✅ Retrieved {len(docs)} docs")
    
    for doc in docs:
        print("\n",doc)
    
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

@tool("search_cas_usage")
def rag_usage_cases(question: str, case_id: Optional[str] = None) -> str:
    """
    Utilise la base de cas d'usage ChromaDB pour répondre aux questions sur les cas d'usage de la facturation électronique.
    Déduire case_id de la question si elle est mentionnée. Example: "étapes cas n°4", donc case_id="4".
    Questionner la base en résumant le contenu de la requête.
    Retourner une seule réponse finale et détaillée pour tous les recherches.
    """
    print(f"🔎 RAG usage cases tool called with: {question} | case ID: {case_id}")
    
    # Load persisted vectorstore + embeddings
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory="./knowledge_bases/usage_cases", embedding_function=embedder)
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 20})
    
    # Get docs
    if case_id:
        docs = retriever.invoke(question, filter={"cas": str(case_id)})
    else:
        docs = retriever.invoke(question)
        
    print(f"✅ Retrieved {len(docs)} docs")
    
    for doc in docs:
        print("\n",doc)
    
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

