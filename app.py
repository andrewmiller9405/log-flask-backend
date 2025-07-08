import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename

# Config
UPLOAD_FOLDER = "logs"
PASSWORD = "disha456"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Template (Terminal Theme)
HTML = '''
<!DOCTYPE html>
<html>
<head>
  <title>Log Terminal</title>
  <style>
    body { background-color: black; color: lime; font-family: monospace; padding: 20px; }
    a { color: cyan; text-decoration: none; }
    input { background: black; color: lime; border: 1px solid lime; }
  </style>
</head>
<body>
  {% if not authed %}
    <h2>🔐 Enter Password</h2>
    <form method="POST">
      <input name="password" type="password"/>
      <button type="submit">Login</button>
    </form>
  {% else %}
    <h2>📂 Logs in Server</h2>
    <ul>
      {% for file in files %}
        <li><a href="{{ url_for('download', filename=file) }}">{{ file }}</a></li>
      {% endfor %}
    </ul>
  {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    authed = False
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            authed = True
    return render_template_string(HTML, files=os.listdir(UPLOAD_FOLDER), authed=authed)

@app.route('/api/receive', methods=['POST'])
def receive():
    for file_key in request.files:
        file = request.files[file_key]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return "OK"

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/logs')
def redirect_logs():
    return redirect(url_for("index"))
