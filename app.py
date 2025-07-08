from flask import Flask, request
import os, datetime

app = Flask(__name__)
UPLOAD_FOLDER = "logs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/api/receive", methods=["POST"])
def receive():
    for fname in request.files:
        file = request.files[fname]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file.save(os.path.join(UPLOAD_FOLDER, f"{timestamp}_{fname}"))
    return "Logs Received", 200

if __name__ == "__main__":
    app.run()
