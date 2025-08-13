# backend/routes.py

from flask import Blueprint, render_template, request, session, jsonify, Response, stream_with_context, current_app
from agent.agentic import user_agent_multiturn, user_agent_multiturn_stream
from core.utils import encode_pdf_from_stream
import uuid
from langchain_core.messages import SystemMessage, HumanMessage # Import SystemMessage and HumanMessage

main_routes = Blueprint("main_routes", __name__)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@main_routes.route("/")
def index():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
        session["system_prompt_sent"] = False # flag to track if the system prompt has been sent
        session.permanent = True
    return render_template("index.html", history=session.get("chat_history", []))

@main_routes.route("/chat", methods=["POST"])
def chat():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
        session["system_prompt_sent"] = False # Ensure flag is set for new sessions
        session.permanent = True

    query = request.form.get("query", "").strip()
    uploaded_file = request.files.get("pdf")
    allowed_extensions = current_app.config["ALLOWED_EXTENSIONS"]
    

    # Construct the messages list
    messages = []
    if not session.get("system_prompt_sent", False):
        system_prompt = SystemMessage(content="""Vous êtes un assistant financier expert spécialisé en droit fiscal français, notamment en facturation électronique et TVA.
Fournissez des réponses précises et concises basées sur les documents et outils fournis ou vos connaissances. Si vous utiliser les outils externes, formulez une réponse claire et concise.
**NE RÉPONDEZ QU'AUX QUESTION RELATIVES À LA FISCALITÉ, EN PARTICULIER LA FISCALITÉ FRANÇAISE ET LA FACTURE ÉLECTRONIQUE!**

Si tous traitez une facture et que vous êtes demandés d'extraire ses informations, veuillez voir si l'utilisateur souhaite sauvegarder les détails dans un fichier Excel.

Si vous cherchez une information dans une base des connaissances, retourner un résumé des informations trouvées et pertinentes à la requête de l'utilisateur.

Si l'utilisateur vous envoie un message comme 'bonjour' ou 'test', répondez poliment et indiquer votre mission en tant qu'assistant.

Répondez toujours en français. Ne divulguez aucune information sensible.
""")

        messages.append(system_prompt)
        session["system_prompt_sent"] = True # Set the flag after adding the system prompt

    # Build human message
    if uploaded_file and allowed_file(uploaded_file.filename, allowed_extensions):
        file_bytes = uploaded_file.read()
        base64_page = encode_pdf_from_stream(file_bytes)
        human_message = HumanMessage(content=[
            {"type": "text", "text": query},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_page}"}}
        ])
    else:
        human_message = HumanMessage(content=query)
    
    messages.append(human_message)

    # Invoke the agent with the constructed messages list
    # The user_agent_multiturn function expects a list of messages.
    # It will be responsible for extracting the HumanMessage from this list.
    response = user_agent_multiturn(query, base64_page if 'base64_page' in locals() else None, session["thread_id"], messages_to_invoke=messages)
    
    session["chat_history"].append({"role": "user", "content": query})
    session["chat_history"].append({"role": "assistant", "content": response})
    
    session.modified = True
    
    return jsonify({"history": session["chat_history"]})
