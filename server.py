import sys

from flask import Flask, render_template, request, redirect, make_response
from datetime import datetime, timedelta
import game

TEMPLATE_FOLDER = "html"
PASSWD_FILE = "data/passwd"
COOKIE_TEAM = "team"
COOKIE_PASSWORD = "password"
COOKIE_HOURS = 12
ERROR_AUTH = "Team not found or wrong password"
ERROR_CODE = "Wrong code"

BASE_URL = ""

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

def clear_cookies_and_redirect():
    resp = make_response(redirect(f"{BASE_URL}/login"))
    resp.set_cookie(COOKIE_TEAM, "", expires=0)
    resp.set_cookie(COOKIE_PASSWORD, "", expires=0)
    return resp

def check_auth(team, password):
    try:
        with open(PASSWD_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    login, passwd = line.split(":", 1)
                    if login == team and passwd == password:
                        return True
    except FileNotFoundError:
        pass
    return False

@app.route("/", methods=["GET", "POST"])
def index():
    team = request.cookies.get(COOKIE_TEAM)
    password = request.cookies.get(COOKIE_PASSWORD)
    if not team or not password or not check_auth(team, password):
        return redirect(f"{BASE_URL}/login")
    if not game.has_team_file(team):
        return clear_cookies_and_redirect()
    error = None
    if request.method == "POST":
        code = request.form.get("code", "")
        if game.check_code(team, code):
            return redirect(f"{BASE_URL}/")
        else:
            error = ERROR_CODE
    state = game.get_game_state(team)
    return render_template("index.html", state=state, error=error)

@app.route("/standings")
def standings():
    team = request.cookies.get(COOKIE_TEAM)
    password = request.cookies.get(COOKIE_PASSWORD)
    if not team or not password or not check_auth(team, password):
        return redirect(f"{BASE_URL}/login")
    if game.has_team_file(team):
        return redirect(f"{BASE_URL}/")
    standings_data = game.get_standings()
    return render_template("standings.html", standings=standings_data)

@app.route("/where")
def where():
    try:
        team = request.args.get("team", "")
        lat = request.args.get("lat", "")
        lon = request.args.get("lon", "")
        if team and lat and lon:
            lat_f = float(lat)
            lon_f = float(lon)
            if not game.save_location(team, lat_f, lon_f):
                return "forbidden", 403
            return "ok"
    except Exception as e:
        print(f"/where error: {e}")
    return "error"

@app.route("/map")
def map_page():
    markers = []
    try:
        from datetime import datetime
        locations = game.get_team_locations()
        now = datetime.now()
        for team, points in locations.items():
            for p in points:
                mins = int((now - p["ts"]).total_seconds() // 60)
                markers.append({
                    "team": team,
                    "lat": p["lat"],
                    "lon": p["lon"],
                    "mins": mins
                })
    except Exception as e:
        print(f"/map error: {e}")
    return render_template("map.html", markers=markers)

@app.route("/finish_game", methods=["POST"])
def finish_game():
    team = request.cookies.get(COOKIE_TEAM)
    password = request.cookies.get(COOKIE_PASSWORD)
    if not team or not password or not check_auth(team, password):
        return redirect(f"{BASE_URL}/login")
    if game.has_team_file(team):
        return redirect(f"{BASE_URL}/")
    game.finish_game()
    return redirect(f"{BASE_URL}/standings")

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
                resp = make_response(redirect(f"{BASE_URL}/"))
            else:
                resp = make_response(redirect(f"{BASE_URL}/standings"))
            resp.set_cookie(COOKIE_TEAM, team, expires=expires)
            resp.set_cookie(COOKIE_PASSWORD, password, expires=expires)
            return resp
        error = ERROR_AUTH
    return render_template("login.html", error=error)

if __name__ == "__main__":
    port = 8888
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        if len(sys.argv) > 2:
            port = int(sys.argv[2])
    app.run(port=port, debug=True)
