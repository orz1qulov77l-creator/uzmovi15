import os
from flask import Flask, abort, request, render_template_string
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.formatters import HtmlFormatter

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.getcwd())

def safe_join(base, user_path):
    # foydalanuvchi kiritgan path xavfsizligini tekshirish
    base = os.path.abspath(base)
    target = os.path.abspath(os.path.join(base, user_path))
    if os.path.commonpath([base, target]) != base:
        raise ValueError("Invalid path")
    return target

def list_dir(path):
    items = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        rel = os.path.relpath(full, BASE_DIR)
        is_dir = os.path.isdir(full)
        items.append({
            "name": name,
            "rel": rel.replace("\\", "/"),
            "is_dir": is_dir,
        })
    return items

def get_file_html(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    try:
        lexer = get_lexer_for_filename(file_path)
    except Exception:
        lexer = guess_lexer(content)

    formatter = HtmlFormatter(full=True, linenos=True, cssclass="code")
    return highlight(content, lexer, formatter)

@app.route("/")
def index():
    return render_template_string("""
    <!doctype html>
    <html>
    <head>
        <title>Code Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 30px; background: #f5f7fb; color: #1f2937; }
            a { color: #2563eb; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .container { max-width: 1100px; margin: 0 auto; }
            .box { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
            .nav { margin-bottom: 20px; }
            .files { line-height: 1.8; }
            pre { background: #111827; color: #e5e7eb; padding: 20px; border-radius: 8px; overflow: auto; }
            .code { background: #111827 !important; }
            .code .linenos { background: #0f172a; color: #93c5fd; padding-right: 12px; }
        </style>
    </head>
    <body>
      <div class="container">
        <div class="box">
          <div class="nav">
            <a href="/">Home</a>
          </div>
          <h2>Repository files</h2>
          <div class="files">
            {% for item in items %}
              {% if item.is_dir %}
                <div><a href="/view?path={{ item.rel }}">📁 {{ item.name }}</a></div>
              {% else %}
                <div><a href="/view?path={{ item.rel }}">📄 {{ item.name }}</a></div>
              {% endif %}
            {% endfor %}
          </div>
        </div>
      </div>
    </body>
    </html>
    """, items=list_dir(BASE_DIR))

@app.route("/view")
def view_file():
    from flask import redirect
    rel_path = request.args.get("path", "")
    if not rel_path:
        return redirect_to_root()

    try:
        target_path = safe_join(BASE_DIR, rel_path)
    except ValueError:
        abort(403)

    if not os.path.exists(target_path):
        abort(404)

    if os.path.isdir(target_path):
        parent = os.path.relpath(os.path.dirname(target_path), BASE_DIR) if os.path.dirname(target_path) != BASE_DIR else ""
        item_list = list_dir(target_path)

        return render_template_string("""
        <!doctype html>
        <html>
        <head>
            <title>Folder</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 30px; background: #f5f7fb; color: #1f2937; }
                a { color: #2563eb; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .container { max-width: 1100px; margin: 0 auto; }
                .box { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
                .nav { margin-bottom: 15px; }
                .files { line-height: 1.8; }
            </style>
        </head>
        <body>
          <div class="container">
            <div class="box">
              <div class="nav">
                <a href="/">Home</a>
                {% if parent %}
                  / <a href="/view?path={{ parent }}">{{ parent }}</a>
                {% endif %}
              </div>
              <h2>Folder: {{ current }}</h2>
              <div class="files">
                {% for item in items %}
                  {% if item.is_dir %}
                    <div><a href="/view?path={{ item.rel }}">📁 {{ item.name }}</a></div>
                  {% else %}
                    <div><a href="/view?path={{ item.rel }}">📄 {{ item.name }}</a></div>
                  {% endif %}
                {% endfor %}
              </div>
            </div>
          </div>
        </body>
        </html>
        """, items=item_list, current=rel_path, parent=parent)

    if os.path.isfile(target_path):
        html = get_file_html(target_path)
        rel_dir = os.path.relpath(os.path.dirname(target_path), BASE_DIR)
        filename = os.path.basename(target_path)
        parent = rel_dir if rel_dir != "." else ""

        return render_template_string("""
        <!doctype html>
        <html>
        <head>
            <title>{{ filename }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f7fb; color: #1f2937; }
                a { color: #2563eb; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .container { max-width: 1200px; margin: 0 auto; }
                .box { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
                .nav { margin-bottom: 15px; }
                pre { overflow: auto; }
                .code { border-radius: 8px; }
            </style>
        </head>
        <body>
          <div class="container">
            <div class="box">
              <div class="nav">
                <a href="/">Home</a>
                {% if parent %}
                  / <a href="/view?path={{ parent }}">{{ parent }}</a>
                {% endif %}
              </div>
              <h2>{{ filename }}</h2>
              {{ code | safe }}
            </div>
          </div>
        </body>
        </html>
        """, filename=filename, parent=parent, code=html)

    abort(404)

def redirect_to_root():
    from flask import redirect
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
