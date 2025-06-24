from langchain_core.messages import HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from utils import encode_image, get_api_key

# Change image here
image_path = "test3.jpg"
encoded_image = encode_image(image_path)
mime_type = 'image/jpeg' if image_path.lower().endswith(('jpg', 'jpeg')) else 'image/png'

# TVA rules (in context, CAG system)
contexte_tva = """
Voici les règles applicables à la TVA en France :

- Le taux normal de TVA est de 20 %.
- Le taux réduit de 10 % s’applique à la restauration, aux transports publics, et aux travaux de rénovation dans les logements.
- Le taux super réduit de 5,5 % s’applique aux produits alimentaires, aux livres, aux équipements pour personnes handicapées et à certains produits culturels.
- Un taux de 0 % s’applique aux exportations et à certains produits médicaux.
"""

# One single prompt (instead of 2)
messages = [
    HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"""
Tu es un expert en analyse de factures.

Analyse l'image suivante :
1. Extrait tous les articles avec leur description, prix unitaire, quantité, taux de TVA appliqué et montant total.
2. Vérifie pour chaque article si le taux de TVA appliqué est correct, en utilisant les règles suivantes :

{contexte_tva}

Indique clairement les erreurs éventuelles, et propose les taux attendus le cas échéant.
Présente le tout sous forme de tableau clair ou de JSON structuré.
"""
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
            },
        ]
    )
]

# Instantiate the model
llm = ChatNVIDIA(
    base_url="https://integrate.api.nvidia.com/v1",
    model="mistralai/mistral-medium-3-instruct",
    api_key=get_api_key(),
    temperature=0
)

response = llm.invoke(messages)
print("\n📄 Résultat :")
print(response.content)
