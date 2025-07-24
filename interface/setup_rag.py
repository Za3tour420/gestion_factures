import pandas as pd
import fitz  # PyMuPDF
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

####################################################################
# Management rules
####################################################################

# Load 2nd sheet and use row 1 as headers
df = pd.read_excel("./test_files/Annexe_7_Règles_de_gestion_ V1.5.xlsx", sheet_name="Règles de gestion PPF", header=1)

applicable_cols = [col for col in df.columns if col.startswith('Applicable')]
df[applicable_cols] = df[applicable_cols].applymap(lambda x: "oui" if x == "X" else "non")

# Create documents
documents = [Document(
        page_content=f"{row['Libellé']}",
        metadata={
        "id_règle": f"{row['ID Règle de gestion']}",
        "titre":f"{row['Titre']}",
        "source": "regles_gestion"
        },
    )
    for _, row in df.iterrows()
    if pd.notna(row["Libellé"])
]

# Embedder
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create Chroma vector store from texts + metadata + embeddings
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embedder,
    persist_directory="./knowledge_bases/regles_gestion"  # directory to save persistent index
)

####################################################################
# Use cases
####################################################################

# Extract text from page 7 onward
pdf_path = "./test_files/Dossier de spécifications externes de la facturation électronique - Cas d'usage_v2.3.pdf"
doc = fitz.open(pdf_path)

page_texts = []
for page_num in range(6, len(doc)):  # Page 7 == index 6
    text = doc[page_num].get_text().strip()
    if text:
        page_texts.append((page_num + 1, text))

# Combine all text and extract "Cas n°X" sections
full_text = "\n".join(text for _, text in page_texts)

def extract_cases(text):
    parts = re.split(r"(Cas n°\s?\d+[^:\n]*)", text)
    cases = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i+1].strip() if i+1 < len(parts) else ""
        case_number = re.search(r"Cas n°\s?(\d+)", title)
        if case_number:
            full_content = f"{title}\n{body}"
            cases.append((case_number.group(1), full_content))
    return cases

cases = extract_cases(full_text)

# Document objects
documents = []
for case_number, content in cases:
    documents.append(Document(
        page_content=content,
        metadata={"source": "cas_usage", "cas": case_number}
    ))

# Chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=2048)
chunked_docs = splitter.split_documents(documents)

# Embed and save
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = Chroma.from_documents(
    documents=chunked_docs,
    embedding=embedder,
    persist_directory="./knowledge_bases/usage_cases"
)

