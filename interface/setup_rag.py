import pandas as pd
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from uuid import uuid4

# Load 2nd sheet and use row 1 as headers
df = pd.read_excel("./test_files/Annexe_7_Règles_de_gestion_ V1.5.xlsx", sheet_name="Règles de gestion PPF", header=1)

applicable_cols = [col for col in df.columns if col.startswith('Applicable')]
df[applicable_cols] = df[applicable_cols].applymap(lambda x: "oui" if x == "X" else "non")

# Create documents
documents = [Document(
        page_content=f"{row['Libellé']}",
        metadata={
        "id_règle": f"{row['ID Règle de gestion']}",
        "titre":f"{row['Titre']}"
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
    persist_directory="./chroma_store"  # directory to save persistent index
)

# Persist to disk
vectorstore.persist()
