# =========================================================
# MINI PROJECT - TaskTrack (small web application)
# =========================================================
#
# Platform  : Python 3 + Flask (runs on any OS with a browser)
# Features  : Register, Login, Add task, Complete task,
#             Delete task, Logout
# Storage   : In-memory dictionaries (data resets on restart)
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install flask
#   python app.py
#   open http://127.0.0.1:5000
#
# =========================================================

import re

from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "stqa-mini-project"   # ponytail: fixed key, fine for a lab app

users = {}   # username -> password
tasks = {}   # username -> list of {"title": str, "done": bool}


# =========================================================
# VALIDATION RULES  (white-box tests target these)
# =========================================================

def validate_username(username):
    if not re.fullmatch(r"[A-Za-z0-9_]{3,15}", username):
        return "Username must be 3-15 letters, digits or _"
    return ""


def validate_password(password):
    if len(password) < 6:
        return "Password must be at least 6 characters"
    if not re.search(r"\d", password):
        return "Password must contain a digit"
    return ""


def validate_task(title):
    title = title.strip()
    if not title:
        return "Task title cannot be empty"
    if len(title) > 50:
        return "Task title must be at most 50 characters"
    return ""


# =========================================================
# HTML TEMPLATE  (ids are used by the Selenium scripts)
# =========================================================

PAGE = """
<!doctype html>
<title>TaskTrack - {{ heading }}</title>
<style>
  body { font-family: sans-serif; max-width: 420px; margin: 40px auto; }
  input, button { padding: 6px; margin: 4px 0; }
  .error { color: #b00020; } .msg { color: #1b5e20; }
  .done { text-decoration: line-through; color: gray; }
</style>
<h2 id="heading">{{ heading }}</h2>
{% if error %}<p class="error" id="error">{{ error }}</p>{% endif %}
{% if msg %}<p class="msg" id="msg">{{ msg }}</p>{% endif %}

{% if page == "login" or page == "register" %}
<form method="post">
  <input id="username" name="username" placeholder="Username"><br>
  <input id="password" name="password" type="password" placeholder="Password"><br>
  {% if page == "register" %}
  <input id="confirm" name="confirm" type="password" placeholder="Confirm password"><br>
  {% endif %}
  <button id="submit" type="submit">{{ heading }}</button>
</form>
{% if page == "login" %}<a id="register-link" href="/register">Create account</a>
{% else %}<a id="login-link" href="/login">Back to login</a>{% endif %}

{% else %}
<p>Logged in as <b id="user">{{ user }}</b> | <a id="logout" href="/logout">Logout</a></p>
<form method="post" action="/tasks/add">
  <input id="task-title" name="title" placeholder="New task">
  <button id="add-task" type="submit">Add</button>
</form>
<ul id="task-list">
{% for t in items %}
  <li class="task {{ 'done' if t.done }}">
    <span class="title">{{ t.title }}</span>
    {% if not t.done %}<a class="complete" href="/tasks/{{ loop.index0 }}/done">Done</a>{% endif %}
    <a class="delete" href="/tasks/{{ loop.index0 }}/delete">Delete</a>
  </li>
{% endfor %}
</ul>
<p id="count">{{ items|length }} task(s)</p>
{% endif %}
"""


def page(**kw):
    return render_template_string(PAGE, **{"error": "", "msg": "", **kw})


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():
    return redirect(url_for("tasks_page") if "user" in session else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return page(page="register", heading="Register")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    error = validate_username(username) or validate_password(password)
    if not error and password != confirm:
        error = "Passwords do not match"
    if not error and username.lower() in (u.lower() for u in users):
        error = "Username already exists"
    if error:
        return page(page="register", heading="Register", error=error)

    users[username] = password
    tasks[username] = []
    return page(page="login", heading="Login", msg="Registration successful, please login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return page(page="login", heading="Login")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return page(page="login", heading="Login", error="Enter username and password")
    if users.get(username) != password:
        return page(page="login", heading="Login", error="Invalid username or password")

    session["user"] = username
    return redirect(url_for("tasks_page"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/tasks")
def tasks_page():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    return page(page="tasks", heading="My Tasks", user=user, items=tasks[user])


@app.route("/tasks/add", methods=["POST"])
def add_task():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    title = request.form.get("title", "")

    error = validate_task(title)
    if error:
        return page(page="tasks", heading="My Tasks", user=user, items=tasks[user], error=error)

    tasks[user].append({"title": title.strip(), "done": False})
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<int:i>/<action>")
def change_task(i, action):
    if "user" not in session:
        return redirect(url_for("login"))
    items = tasks[session["user"]]
    if 0 <= i < len(items):
        if action == "done":
            items[i]["done"] = True
        elif action == "delete":
            items.pop(i)
    return redirect(url_for("tasks_page"))


if __name__ == "__main__":
    app.run(debug=True)
