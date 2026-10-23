from flask import Flask, render_template, request, redirect, session, jsonify

import database

app = Flask(__name__)
app.secret_key = "change-me"  # temporary; Con will move the real key into the ignored secret_key file

database.init_db()

# Fake staff account (temporary)
STAFF_USERNAME = "staff"
STAFF_PASSWORD = "demo-pass-123"


def logged_in():
    return "user" in session


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == STAFF_USERNAME and password == STAFF_PASSWORD:
            session["user"] = username
            return redirect("/")
        error = "Wrong username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def live():
    if not logged_in():
        return redirect("/login")
    seats = database.get_latest()
    total = len(seats)
    taken = sum(1 for v in seats.values() if v)
    vacant = total - taken
    return render_template("live.html", seats=seats,
                           total=total, taken=taken, vacant=vacant)


@app.route("/history")
def history():
    if not logged_in():
        return redirect("/login")
    rows = [
        {"time": ts, "seat": seat, "event": "Taken" if taken else "Vacant"}
        for ts, seat, taken in reversed(database.get_history())  # newest first
    ]
    return render_template("history.html", rows=rows)


@app.route("/api/status")
def api_status():
    if not logged_in():
        return jsonify(error="login required"), 401
    return jsonify(database.get_latest())


if __name__ == "__main__":
    app.run(debug=True, port=5000)