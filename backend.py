from main import workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
load_dotenv()


app = Flask(__name__)
CORS(app)  # allow frontend to call API

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    instructions = data.get("instructions", "Summarize this text")
    notes = data.get("notes", "")
    
    result = workflow.invoke({"instructions": instructions, "notes": notes})
    return jsonify({"summary": result["summary"]})


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
            plain_text_content="\n".join(summary)
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)

        if response.status_code in [200, 202]:
            print("Yes")
            return jsonify({"success": True, "message": "Email sent successfully!"})
        else:
            return jsonify({"error": f"SendGrid failed with status {response.status_code}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)