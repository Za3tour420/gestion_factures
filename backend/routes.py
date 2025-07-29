# backend/routes.py

from flask import Blueprint, render_template, request, session, jsonify
from agent.agentic import user_agent_multiturn
from core.utils import encode_pdf_from_stream
import uuid

main_routes = Blueprint("main_routes", __name__)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@main_routes.route("/")
def index():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
    return render_template("index.html", history=session.get("chat_history", []))

@main_routes.route("/chat", methods=["POST"])
def chat():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
    
    query = request.form.get("query", "").strip()
    uploaded_file = request.files.get("pdf")
    
    allowed_extensions = {"pdf", "jpg", "jpeg", "png", "webp"}

    if uploaded_file and allowed_file(uploaded_file.filename, allowed_extensions):
        file_bytes = uploaded_file.read()
        base64_page = encode_pdf_from_stream(file_bytes)
        response = user_agent_multiturn(query, base64_page, session["thread_id"])
    else:
        response = user_agent_multiturn(query, None, session["thread_id"])
    
    session["chat_history"].append({"role": "user", "content": query})
    session["chat_history"].append({"role": "assistant", "content": response})
    
    return jsonify({"history": session["chat_history"]})
