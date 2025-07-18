import pandas as pd
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# Load 2nd sheet and use row 1 as headers
df = pd.read_excel("./test_files/Annexe_7_Règles_de_gestion_ V1.5.xlsx", sheet_name="Règles de gestion PPF", header=1)

applicable_cols = [col for col in df.columns if col.startswith('Applicable')]
df[applicable_cols] = df[applicable_cols].applymap(lambda x: "oui" if x == "X" else "non")

# Texts and metadatas
texts = [
    f"Règle {row['ID Règle de gestion']} — {row['Titre']}\n\n{row['Libellé']}"
    for _, row in df.iterrows()
    if pd.notna(row["Libellé"])
]

metadatas = [
    {
        "id_regle": row["ID Règle de gestion"],
        "titre": row["Titre"],
        "applicable_e_invoicing": row["Applicable au e-invoicing"],
        "applicable_e_reporting_facture": row["Applicable au e-reporting de facture"],
        "applicable_e_reporting_paiement": row["Applicable au e-reporting de paiement"],
        "applicable_cycle_vie": row["Applicable au Cycle de vie"]
    }
    for _, row in df.iterrows()
    if pd.notna(row["Libellé"])
]

# Chroma
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create Chroma vector store from texts + metadata + embeddings
vectorstore = Chroma.from_texts(
    texts=texts,
    embedding=embedder,
    metadatas=metadatas,
    persist_directory="./chroma_store"  # directory to save persistent index
)

# Persist to disk
vectorstore.persist()
