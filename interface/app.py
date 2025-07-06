import uuid
from flask import Flask, render_template, request, session, jsonify
import os
from agentic import user_agent_multiturn
from utils import encode_pdf_from_stream

app = Flask(__name__)
app.secret_key = os.urandom(15).hex()
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
def index():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
    return render_template("index.html", history=session.get("chat_history", []))

@app.route("/chat", methods=["POST"])
def chat():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
    
    query = request.form.get("query", "").strip()
    uploaded_file = request.files.get("pdf")
    
    if uploaded_file and allowed_file(uploaded_file.filename):
        file_bytes = uploaded_file.read()
        base64_page = encode_pdf_from_stream(file_bytes)
        
        response = user_agent_multiturn(query, base64_page, session["thread_id"])
    else:
        response = user_agent_multiturn(query, None, session["thread_id"])
    
    session["chat_history"].append({"role": "user", "content": query})
    session["chat_history"].append({"role": "assistant", "content": response})
    
    print("Chat history now: ", session["chat_history"])
    
    return jsonify({"history": session["chat_history"]})


if __name__ == "__main__":
    app.run(debug=True)

