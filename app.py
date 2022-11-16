from flask import Flask, redirect, render_template, request, session
import sqlite3
from datetime import date
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.static_folder = 'static'

if __name__ == "__main__":
  app.run()

def get_db_connection():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


db = get_db_connection()


@app.route("/")
def index():
    name = session.get("name")
    person = db.execute(
            "SELECT name FROM users WHERE name = ?", [name]).fetchall()
    if len(person) != 1:
        return redirect("/login")
    today = date.today()
    date_display = today.strftime("%b-%d-%Y")
    day = date.today().strftime("%A")
    name = session.get("name")
    tasks = db.execute("SELECT * FROM tasks WHERE name = ?", [name]).fetchall()
    return render_template("index.html", date_display=date_display, day=day, tasks=tasks)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["name"] = request.form.get("name")
        name = request.form.get("name")
        password = request.form.get("password")
        if not name:
            return render_template("error.html", message="Missing name")
        if not password:
            return render_template("error.html", message="Missing password")
        names = db.execute(
            "SELECT name FROM users WHERE name = ?", [name]).fetchall()
        if len(names) != 1:
            return render_template("error.html", message="Invalid name")
        correct_password = db.execute(
            "SELECT password FROM users WHERE name = ?", [name]).fetchall()[0]["password"]
        if password != correct_password:
            return render_template("error.html", message="Wrong password")
        return redirect("/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/login")


@app.route("/complete", methods=["GET", "POST"])
def complete():
    name = session.get("name")
    person = db.execute(
            "SELECT name FROM users WHERE name = ?", [name]).fetchall()
    if len(person) != 1:
        return redirect("/login")
    if request.method == "POST":
        name = session.get("name")
        db.execute("DELETE FROM completed WHERE name = ?", [name])
        db.commit()
        return render_template("completed.html")
    else:
        name = session.get("name")
        completed = db.execute(
            "SELECT * FROM completed WHERE name = ?", [name]).fetchall()
        return render_template("completed.html", completed=completed)


@app.route("/tag", methods=["POST"])
def tag():
    name = session.get("name")
    tag = request.form.get("tag")
    tags = db.execute(
        "SELECT * FROM tasks WHERE tag = ? AND name = ?", [tag, name]).fetchall()
    return render_template("tag.html", tags=tags, tag=tag)


@app.route("/profile")
def profile():
    name = session.get("name")
    person = db.execute(
            "SELECT name FROM users WHERE name = ?", [name]).fetchall()
    if len(person) != 1:
        return redirect("/login")
    email = db.execute("SELECT email FROM users WHERE name = ?", [name]).fetchall()[
    0]["email"]
    return render_template("profile.html", name=name, email=email)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        if not name:
            return render_template("error.html", message="Missing name")
        if not password:
            return render_template("error.html", message="Missing password")
        if not email:
            return render_template("error.html", message="Missing email")
        else:
            db.execute("INSERT INTO users (name, email, password) VALUES(?, ?, ?)",
                       (name, email, password))
            db.commit()
            return redirect("/")
    return render_template("register.html")


@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        email = request.form.get("email")
        emails = db.execute(
            "SELECT * FROM users WHERE email = ?", (email)).fetchall()

        password = request.form.get("password")

        if not email:
            return render_template("error.html", message="Missing email")

        if not password:
            return render_template("error.html", message="Missing password")

        if len(emails) < 1:
            return render_template("error.html", message="Invalid email")

        db.execute("UPDATE users SET password = ? WHERE email = ?",
                   (password, email))
        db.commit()

        return redirect("/")
    return render_template("reset.html")


@app.route("/addtask", methods=["POST"])
def add():
    task = request.form.get("task")
    name = session.get("name")
    if not task:
        return render_template("error.html", message="Missing task")
    tag = request.form.get("tag")
    if not tag:
        return render_template("error.html", message="Missing tag")

    db.execute("INSERT INTO tasks (name, task, tag) VALUES(?, ?, ?)",
               (name, task, tag))
    db.commit()

    return redirect("/")


@app.route("/completed", methods=["POST"])
def completed():
    id = request.form.get("id")
    name = session.get("name")
    task = db.execute("SELECT task FROM tasks WHERE id = ?",
                      [id]).fetchall()[0]["task"]

    tag = db.execute("SELECT tag FROM tasks WHERE id = ?",
                     [id]).fetchall()[0]["tag"]

    db.execute("INSERT INTO completed (name, task, tag) VALUES(?, ?, ?)",
               (name, task, tag))
    db.execute("DELETE FROM tasks WHERE id = ?", [id])
    db.commit()

    return redirect("/")
