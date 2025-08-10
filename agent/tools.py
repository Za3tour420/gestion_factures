from langchain_google_community import GoogleSearchAPIWrapper
from langchain_google_community.search import GoogleSearchRun

from playwright.sync_api import sync_playwright

from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.tools import tool

from core.utils import get_google_api_keys
from config import KNOWLEDGE_BASE_DIR, SAVE_INVOICES_DIR

import pandas as pd
from datetime import datetime

from typing import Optional
import os

# Get API keys
GOOGLE_API_KEY, GOOGLE_CSE_ID = get_google_api_keys()

#********************************************************************#
# Web search tools
#********************************************************************#
web_search_api_wrapper = GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID,
        k=5)

def init_web_search_tool():
    return GoogleSearchRun(api_wrapper=web_search_api_wrapper)
    
@tool("summarize_url_content")
def summarize_url_content(url: str) -> str:
    """
    Extraire les informations principales sur les taux de TVA à partir de {url} fourni.
    Ne formulez aucun URL qui n'existe pas dans vos connaissances.
    Résumer et bien formuler le contenu du (des) résultat(s) trouvé(s).
    """
    
    print(f"Summarizer tool called with | URL: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle") # Wait for JS content to load
        content = page.inner_text("body")
        browser.close()

    return content.strip() if content else "Aucune information extraite de la page."

#********************************************************************#
# RAG tools
#********************************************************************#
# Load embedder once
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@tool("rag_management_rules")
def rag_management_rules(question: str, rule_id: Optional[str] = None) -> str:
    """
    Utilise la base de règles de gestion ChromaDB pour répondre aux questions sur les conformités et règles de gestion des e-invoices, etc.
    Déduis rule_id de la question si elle est mentionnée. Elle est de la forme GX.XX.
    Questionne la base en résumant le contenu de la requête.
    Retourne une seule réponse finale, détaillée et pas trop longue.
    """
    print(f"🔎 RAG management rules tool called with: {question} | rule ID: {rule_id}")
    
    # Load persisted vectorstore
    vectorstore = Chroma(persist_directory=os.path.join(KNOWLEDGE_BASE_DIR, 'regles_gestion'), embedding_function=embedder)
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

@tool("rag_usage_cases")
def rag_usage_cases(question: str, case_id: Optional[str] = None) -> str:
    """
    Utilise la base de cas d'usage ChromaDB pour répondre aux questions sur les cas d'usage de la facturation électronique.
    Déduis case_id de la question si elle est mentionnée. Example: "étapes cas n°4", donc case_id="4".
    Questionne la base en résumant le contenu de la requête.
    Retourne une seule réponse finale, détaillée et pas trop longue.
    """
    print(f"🔎 RAG usage cases tool called with: {question} | case ID: {case_id}")
    
    # Load persisted vectorstore
    vectorstore = Chroma(persist_directory=os.path.join(KNOWLEDGE_BASE_DIR, 'usage_cases'), embedding_function=embedder)
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

#********************************************************************#
# BOFIP tool
#********************************************************************#

@tool("extract_products_and_services")
def extract_products_and_services():
    """
    Extraire les produits et services des taux demandés à partir des URL du site BOFIP.
    Résumer le contenu final et retourner une réponse concise et claire.
    Toujours inclure les liens sources.
    """
    print("BOFIP checker tool called")
    
    content_list = []
    
    url_list = ["https://bofip.impots.gouv.fr/bofip/1376-PGP.html/identifiant=BOI-TVA-LIQ-20-20140919",
    "https://bofip.impots.gouv.fr/bofip/1377-PGP.html/identifiant=BOI-TVA-LIQ-30-20230823",
    "https://bofip.impots.gouv.fr/bofip/1378-PGP.html/identifiant=BOI-TVA-LIQ-40-20230628"
    ]
    
    # Init driver
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
    
        # Actual loop
        for url in url_list:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle") # Wait for JS content to load
            
            links = page.query_selector_all("a")
            matched_links = []
            
            for link in links:
                text = link.inner_text().strip()
                href = link.get_attribute("href")
                if "BOI-TVA-LIQ" in text and href:
                    full_url = href if href.startswith("http") else f"https://bofip.impots.gouv.fr{href}"
                    matched_links.append(full_url)
            
            for sub_url in matched_links[:2]:
                try:
                    page.goto(sub_url, timeout=60000)
                    page.wait_for_load_state("networkidle")
                    content = page.inner_text("body")
                    content_list.append(f"\n\n---\n\n🔗 {sub_url}\n\n{content}")
                except Exception as e:
                    content_list.append(f"\n\n---\n\n❌ Erreur pour {sub_url}: {e}")

        browser.close()

    return "\n\n".join(content_list) if content_list else "Aucune information extraite."

#********************************************************************#
# Excel save tool
#********************************************************************#

def save_invoice_to_excel(data: dict, output_dir=SAVE_INVOICES_DIR, filename_prefix="facture"):
    os.makedirs(output_dir, exist_ok=True)
    
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{filename_prefix}_{now}.xlsx"
    filepath = os.path.join(output_dir, filename)

    df = pd.DataFrame([data])  # convert single dict to one-row DataFrame
    df.to_excel(filepath, index=False)
    
@tool("save_to_excel")
def save_to_excel(data: dict) -> str:
    """
    Sauvegarde les détails extraits d'une facture en un fichier Excel.
    Créer le dictionnaire des données.
    """
    print("Saving to Excel tool called with:\n", data)
    save_invoice_to_excel(data)
    
    return "File saved successfully!"
    
