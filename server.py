import sys

from flask import (Flask, render_template, request, redirect, make_response,
                   url_for)
from datetime import datetime, timedelta
import game

TEMPLATE_FOLDER = "html"
PASSWD_FILE = "data/passwd"
COOKIE_TEAM = "team"
COOKIE_PASSWORD = "password"
COOKIE_HOURS = 12
ERROR_AUTH = "Team not found or wrong password"
ERROR_CODE = "Wrong code"

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

def check_auth(team, password):
    with open(PASSWD_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                login, passwd = line.split(":", 1)
                if login == team and passwd == password:
                    return True
    return False

@app.route("/", methods=["GET", "POST"])
def index():
    team = request.cookies.get(COOKIE_TEAM)
    password = request.cookies.get(COOKIE_PASSWORD)
    if not team or not password or not check_auth(team, password):
        return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        code = request.form.get("code", "")
        if game.check_code(team, code):
            return redirect(url_for("index"))
        else:
            error = ERROR_CODE
    state = game.get_game_state(team)
    return render_template("index.html", state=state, error=error)

@app.route("/standings")
def standings():
    team = request.cookies.get(COOKIE_TEAM)
    password = request.cookies.get(COOKIE_PASSWORD)
    if not team or not password or not check_auth(team, password):
        return redirect(url_for("login"))
    if game.has_team_file(team):
        return redirect(url_for("index"))
    standings_data = game.get_standings()
    return render_template("standings.html", standings=standings_data)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        team = request.form.get(COOKIE_TEAM, "")
        password = request.form.get(COOKIE_PASSWORD, "")
        if check_auth(team, password):
            expires = datetime.now() + timedelta(hours=COOKIE_HOURS)
            if game.has_team_file(team):
                game.init_progress(team)
                resp = make_response(redirect(url_for("index")))
            else:
                resp = make_response(redirect(url_for("standings")))
            resp.set_cookie(COOKIE_TEAM, team, expires=expires)
            resp.set_cookie(COOKIE_PASSWORD, password, expires=expires)
            return resp
        error = ERROR_AUTH
    return render_template("login.html", error=error)

if __name__ == "__main__":
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    app.run(port=port, debug=True)
