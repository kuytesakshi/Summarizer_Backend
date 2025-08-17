from main import workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# For file handling
import docx
from pypdf import PdfReader

load_dotenv()

app = Flask(__name__)
CORS(app)

# Allowed extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(filepath, ext):
    text = ""
    if ext == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    elif ext == "pdf":
        reader = PdfReader(filepath)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    elif ext == "docx":
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text


@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        instructions = request.form.get("instructions")
        text = ""

        # Case 1: File upload (form-data)
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "Empty filename"}), 400

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                ext = filename.rsplit(".", 1)[1].lower()
                text = extract_text_from_file(filepath, ext)

                # ✅ Delete after reading
                if os.path.exists(filepath):
                    os.remove(filepath)
            else:
                return jsonify({"error": "Invalid file type"}), 400

        # Case 2: Raw notes text (JSON)
        elif request.is_json:
            data = request.get_json(silent=True) or {}
            instructions = data.get("instructions", "Summarize this text")
            text = data.get("notes", "")

        if not text.strip():
            return jsonify({"error": "No notes or file content found"}), 400

        # 🔹 Debug print
        print("Instructions:", instructions[:100])
        print("Text length:", len(text))

        # Run summarization
        result = workflow.invoke({"instructions": instructions, "notes": text})
        return jsonify({"summary": result["summary"]})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Backend crashed: {str(e)}"}), 500


@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.json
    recipient = data.get("recipient")
    summary = data.get("summary")

    if not recipient or not summary:
        return jsonify({"error": "Missing recipient or summary"}), 400

    try:
        message = Mail(
            from_email=os.getenv("EMAIL"),
            to_emails=recipient,
            subject="Meeting Notes Summary",
            plain_text_content="\n".join(summary),
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)

        if response.status_code in [200, 202]:
            return jsonify({"success": True, "message": "Email sent successfully!"})
        else:
            return jsonify({"error": f"SendGrid failed with status {response.status_code}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
