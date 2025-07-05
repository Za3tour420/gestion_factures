import uuid
from flask import Flask, render_template, request, redirect, url_for, session
import os
from agentic import user_agent_multiturn
from utils import encode_pdf

app = Flask(__name__)
app.secret_key = os.urandom(15).hex()
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/", methods=["GET", "POST"])
def index():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
        session["chat_history"] = []
    
    response = ""
    if request.method == "POST":
        query = request.form["query"]
        uploaded_file = request.files["pdf"]

        if uploaded_file and allowed_file(uploaded_file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(filepath)

            base64_pages = encode_pdf(filepath)
            if base64_pages:
                print(f"Base64 page(s): {base64_pages}")
                response = user_agent_multiturn(query, base64_pages[0])
                 #Store in session for UI display (not for model memory)
                session["chat_history"].append({"role": "user", "content": query})
                session["chat_history"].append({"role": "assistant", "content": response})

                return render_template("index.html", history=session["chat_history"])

    # On GET (refresh): clear memory and history
    session.clear()
    return render_template("index.html", history=[])

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)

