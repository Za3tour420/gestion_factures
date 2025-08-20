# backend/routes.py
import uuid
from flask import (
    Blueprint, render_template, request, session, jsonify,
    current_app, send_from_directory
)
from langchain_core.messages import SystemMessage, HumanMessage

from agent.agentic import user_agent_multiturn
from core.utils import encode_pdf_from_stream, encode_image_bytes
from config import SAVE_INVOICES_DIR


# ============================================================
# Blueprint & Config
# ============================================================
main_routes = Blueprint("main_routes", __name__)

MAX_FILES_PER_REQUEST = 5
MAX_IMAGES_PER_REQUEST = 3
MAX_TOTAL_FILE_SIZE_MB = 50


# ============================================================
# Helper Functions
# ============================================================
def allowed_file(filename, allowed_extensions):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def get_file_size(file_bytes):
    """Return size in MB."""
    return len(file_bytes) / (1024 * 1024)


def is_image_file(filename):
    image_extensions = {'jpg', 'jpeg', 'png', 'webp', 'bmp'}
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in image_extensions
    )


def build_system_prompt():
    """Return the system message for the assistant."""
    return SystemMessage(content=(
        "Vous êtes un assistant financier expert spécialisé en droit fiscal français, "
        "notamment en facturation électronique et TVA. Fournissez des réponses précises "
        "et concises basées sur les documents et outils fournis ou vos connaissances. "
        "Si vous utiliser les outils externes, formulez une réponse claire et concise.\n\n"
        "**NE RÉPONDEZ QU'AUX QUESTION RELATIVES À LA FISCALITÉ, EN PARTICULIER "
        "LA FISCALITÉ FRANÇAISE ET LA FACTURE ÉLECTRONIQUE!**\n\n"
        "Si vous traitez une facture et qu'on vous demande d'extraire ses informations, "
        "vérifiez si l'utilisateur souhaite sauvegarder les détails dans un fichier Excel. "
        "Puis, ne retournez que le lien du téléchargement après confirmation de l'utilisateur.\n\n"
        "Si vous cherchez une information dans une base des connaissances, retournez un résumé "
        "des informations pertinentes.\n\n"
        "Si l'utilisateur envoie 'bonjour' ou 'test', répondez poliment et indiquez votre mission.\n\n"
        "Répondez toujours en français. Ne divulguez aucune information sensible."
    ))


# ============================================================
# Routes
# ============================================================
@main_routes.route("/")
def index():
    """Landing page with chat history in session."""
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
        session["system_prompt_sent"] = False
        session.permanent = True

    return render_template("index.html", history=session.get("chat_history", []))


@main_routes.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint: handles queries + file uploads."""
    # Ensure session
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
        session["system_prompt_sent"] = False
        session.permanent = True

    query = request.form.get("query", "").strip()
    uploaded_files = request.files.getlist("fileUpload")
    allowed_extensions = current_app.config["ALLOWED_EXTENSIONS"]

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------
    if len(uploaded_files) > MAX_FILES_PER_REQUEST:
        return jsonify({"error": f"Trop de fichiers. Maximum: {MAX_FILES_PER_REQUEST}"}), 400

    image_count = sum(1 for f in uploaded_files if f.filename and is_image_file(f.filename))
    if image_count > MAX_IMAGES_PER_REQUEST:
        return jsonify({"error": f"Trop d'images. Maximum: {MAX_IMAGES_PER_REQUEST}"}), 400

    # --------------------------------------------------------
    # Process Files
    # --------------------------------------------------------
    processed_files = []
    total_size = 0

    for uploaded_file in uploaded_files:
        if not (uploaded_file and uploaded_file.filename):
            continue
        if not allowed_file(uploaded_file.filename, allowed_extensions):
            continue

        file_bytes = uploaded_file.read()
        total_size += get_file_size(file_bytes)

        if total_size > MAX_TOTAL_FILE_SIZE_MB:
            return jsonify({
                "error": f"Taille totale trop importante. Max: {MAX_TOTAL_FILE_SIZE_MB}MB"
            }), 400

        if is_image_file(uploaded_file.filename):
            base64_content = encode_image_bytes(file_bytes)
            processed_files.append({
                "type": "image",
                "filename": uploaded_file.filename,
                "base64": base64_content
            })
        else:
            base64_content = encode_pdf_from_stream(file_bytes)
            processed_files.append({
                "type": "document",
                "filename": uploaded_file.filename,
                "base64": base64_content
            })

    # --------------------------------------------------------
    # Construct Messages
    # --------------------------------------------------------
    messages = []

    if not session.get("system_prompt_sent", False):
        messages.append(build_system_prompt())
        session["system_prompt_sent"] = True

    if processed_files:
        content_parts = [{"type": "text", "text": query}]
        for file_info in processed_files:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{file_info['base64']}"
                }
            })
        human_message = HumanMessage(content=content_parts)
    else:
        human_message = HumanMessage(content=query)

    messages.append(human_message)

    # --------------------------------------------------------
    # Invoke Agent
    # --------------------------------------------------------
    try:
        response = user_agent_multiturn(
            query,
            processed_files if processed_files else None,
            session["thread_id"],
            messages_to_invoke=messages
        )

        # Update history
        user_content = query
        if processed_files:
            file_list = [f["filename"] for f in processed_files]
            user_content += f" [Fichiers joints: {', '.join(file_list)}]"

        session["chat_history"].append({"role": "user", "content": user_content})
        session["chat_history"].append({"role": "assistant", "content": response})
        session.modified = True

        return jsonify({"history": session["chat_history"]})

    except Exception as e:
        current_app.logger.error(f"Error in chat processing: {str(e)}", exc_info=True)
        return jsonify({"error": "Une erreur est survenue. Veuillez réessayer."}), 500


@main_routes.route("/factures/<path:filename>")
def download_excel(filename):
    """Download saved invoice Excel file."""
    return send_from_directory(SAVE_INVOICES_DIR, filename, as_attachment=True)

