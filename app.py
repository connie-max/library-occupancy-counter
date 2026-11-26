import json
import os

import pandas as pd

import matplotlib
matplotlib.use("Agg")  # no window, draw to files only (Flask runs in threads)
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, session, jsonify, Response

import analysis
import database

app = Flask(__name__)
app.secret_key = "change-me"  # temporary; Con will move the real key into the ignored secret_key file

database.init_db()

# Fake staff account (temporary)
STAFF_USERNAME = "staff"
STAFF_PASSWORD = "demo-pass-123"

# Live camera feed for the dashboard. Set this to the phone's DroidCam
# address on the day, for example "http://192.168.0.107:4747/video".
# Leave it empty and the dashboard hides the camera box. The address
# changes when the Wi-Fi changes, so check the DroidCam app each time.
CAMERA_URL = ""

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
    # People inside, from the monitor's latest check (data/people.json).
    # If the monitor is not running, there is no file and we show nothing.
    people = None
    people_time = ""
    people_path = os.path.join("data", "people.json")
    if os.path.exists(people_path):
        try:
            with open(people_path) as f:
                people_data = json.load(f)
            people = people_data.get("people")
            people_time = people_data.get("time", "")
        except (OSError, ValueError):
            people = None
    # Group seats by table (the part before "-"), so staff can see
    # at a glance which table still has a free seat.
    by_table = {}
    for name, is_taken in seats.items():
        table = name.split("-")[0]
        group = by_table.setdefault(table, {"taken": 0, "total": 0})
        group["total"] += 1
        if is_taken:
            group["taken"] += 1
    tables = [
        {"name": name, "taken": g["taken"], "total": g["total"],
         "vacant": g["total"] - g["taken"]}
        for name, g in sorted(by_table.items())
    ]
    # Seats grouped by table, in order, for the seat table.
    seat_table = []
    for table_name in sorted(by_table):
        table_seats = [
            {"name": name, "taken": bool(is_taken)}
            for name, is_taken in sorted(seats.items())
            if name.split("-")[0] == table_name
        ]
        seat_table.append({"name": table_name, "seats": table_seats})
    return render_template("live.html", seats=seats,
                           total=total, taken=taken, vacant=vacant,
                           tables=tables, seat_table=seat_table,
                           last_check=database.get_latest_time(),
                           camera_url=CAMERA_URL,
                           people=people, people_time=people_time)


@app.route("/seats")
def public_seats():
    """Public Seats page for students: no login needed.

    The background of the study says students do not know how many
    seats are free before entering the library. This page is the
    answer: anyone can open it and see which seats are free right
    now. It shows seat status only (taken or vacant), no camera
    feed and no names, so the privacy promise still holds.
    """
    seats = database.get_latest()
    total = len(seats)
    taken = sum(1 for v in seats.values() if v)
    vacant = total - taken
    people = None
    people_time = ""
    people_path = os.path.join("data", "people.json")
    if os.path.exists(people_path):
        try:
            with open(people_path) as f:
                people_data = json.load(f)
            people = people_data.get("people")
            people_time = people_data.get("time", "")
        except (OSError, ValueError):
            people = None
    by_table = {}
    for name, is_taken in seats.items():
        table = name.split("-")[0]
        group = by_table.setdefault(table, {"taken": 0, "total": 0})
        group["total"] += 1
        if is_taken:
            group["taken"] += 1
    tables = [
        {"name": name, "taken": g["taken"], "total": g["total"],
         "vacant": g["total"] - g["taken"]}
        for name, g in sorted(by_table.items())
    ]
    seat_table = []
    for table_name in sorted(by_table):
        table_seats = [
            {"name": name, "taken": bool(is_taken)}
            for name, is_taken in sorted(seats.items())
            if name.split("-")[0] == table_name
        ]
        seat_table.append({"name": table_name, "seats": table_seats})
    return render_template("seats.html", seats=seats,
                           total=total, taken=taken, vacant=vacant,
                           tables=tables, seat_table=seat_table,
                           last_check=database.get_latest_time(),
                           people=people, people_time=people_time)


@app.route("/analytics")
def analytics_page():
    """Busiest hours and days, the chart, and the forecast.

    This is the report page for staff and for the higher-ups: it shows
    what the data says, not the raw readings. The numbers come from the
    sample day in data/demo_seats.db while the camera has not logged a
    real week yet, and the page says so.
    """
    if not logged_in():
        return redirect("/login")
    # Real data only, from the day the library camera started
    # (26 Nov 2026). Older rows in data/seats.db are test rows, so
    # they are left out of the report.
    df = analysis.load_from_db()
    if not df.empty:
        df = df[df["timestamp"] >= pd.to_datetime("2026-11-26")]
    is_sample = False
    if df.empty:
        return render_template("analytics.html", empty=True,
                               is_sample=is_sample)
    top_hours = [
        {"hour": int(h), "seats": round(float(s), 1)}
        for h, s in analysis.busiest_hours(df).head(3).items()
    ]
    top_days = [
        {"day": str(d), "seats": round(float(s), 1)}
        for d, s in analysis.busiest_days(df).head(3).items()
    ]
    peak_hour, peak_seats = analysis.predict_next_peak(df)
    total_checks = int(df["timestamp"].nunique())
    first_time = str(df["timestamp"].min())
    last_time = str(df["timestamp"].max())
    analysis.plot_hourly(df, os.path.join("static", "hourly.png"))
    # People inside right now, from the monitor's latest check.
    people = None
    people_path = os.path.join("data", "people.json")
    if os.path.exists(people_path):
        try:
            with open(people_path) as f:
                people = json.load(f).get("people")
        except (OSError, ValueError):
            people = None
    return render_template(
        "analytics.html",
        empty=False,
        is_sample=is_sample,
        top_hours=top_hours,
        top_days=top_days,
        peak_hour=peak_hour,
        peak_seats=peak_seats,
        total_checks=total_checks,
        first_time=first_time,
        last_time=last_time,
        chart_exists=True,
        people=people,
    )


@app.route("/analytics/report")
def analytics_report():
    """Downloadable PDF report of the analytics, with the LCC logo.

    Same real data as the analytics page, from 26 Nov 2026 onwards.
    Returns a PDF file the staff can save or print. Built with
    matplotlib, which is already installed, so no new package is
    needed.
    """
    if not logged_in():
        return redirect("/login")
    df = analysis.load_from_db()
    if not df.empty:
        df = df[df["timestamp"] >= pd.to_datetime("2026-11-26")]
    if df.empty:
        return "No readings yet.", 404
    top_hours = [
        (int(h), round(float(s), 1))
        for h, s in analysis.busiest_hours(df).head(3).items()
    ]
    top_days = [
        (str(d), round(float(s), 1))
        for d, s in analysis.busiest_days(df).head(3).items()
    ]
    peak_hour, peak_seats = analysis.predict_next_peak(df)
    total_checks = int(df["timestamp"].nunique())
    first_time = str(df["timestamp"].min())
    last_time = str(df["timestamp"].max())
    # Build the PDF: logo at the top, then the report text.
    from io import BytesIO
    logo_path = os.path.join(os.path.dirname(__file__),
                             "static", "lcc-logo.jpg")
    logo = plt.imread(logo_path)
    fig = plt.figure(figsize=(8.5, 11))
    # Logo, centered, square (figure is 8.5 by 11 inches).
    logo_ax = fig.add_axes([0.425, 0.86, 0.15, 0.116])
    logo_ax.imshow(logo)
    logo_ax.axis("off")
    fig.text(0.5, 0.83, "Legacy College of Compostela",
             fontsize=16, weight="bold", ha="center", family="Arial")
    fig.text(0.5, 0.80, "Library Occupancy Report",
             fontsize=13, weight="bold", ha="center", family="Arial")
    # People inside right now, from the monitor's latest check.
    people = None
    people_time = ""
    people_path = os.path.join("data", "people.json")
    if os.path.exists(people_path):
        try:
            with open(people_path) as f:
                people_data = json.load(f)
            people = people_data.get("people")
            people_time = people_data.get("time", "")
        except (OSError, ValueError):
            people = None
    lines = [
        "",
        "Data: real readings from the library camera, "
        f"{first_time} to {last_time}.",
        f"Total checks: {total_checks}",
    ]
    if people is not None:
        lines.append(f"People inside right now: {people} (as of {people_time}).")
    lines.append("")
    lines.append("Busiest hours (average seats taken):")

    for hour, seats in top_hours:
        lines.append(f"  {hour:02d}:00 - {seats} seats")
    lines.append("")
    lines.append("Busiest days (average seats taken):")
    for day, seats in top_days:
        lines.append(f"  {day} - {seats} seats")
    lines.append("")
    lines.append(
        f"Forecast: next peak tomorrow around {peak_hour}:00, "
        f"about {peak_seats} seats taken.")
    lines.append(
        "The forecast is the busiest hour in the data so far. "
        "It is a simple hourly average, not a machine learning model.")
    # Wrap long lines so nothing runs off the right edge.
    import textwrap
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=70) or [""])
    body = "\n".join(wrapped)
    fig.text(0.1, 0.76, body, fontsize=11, family="Arial",
             verticalalignment="top")
    buf = BytesIO()
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition":
                 "attachment; filename=library-occupancy-report.pdf"},
    )


@app.route("/analytics/report/custom")
def custom_report():
    """Custom PDF report: staff picks a day, a time range, and a chart.

    The chart types come from sir Tiempo's EDA lecture:
    bar (average seats by hour), histogram (shape of the counts),
    box plot (middle + outliers), scatter (hour against seats taken).
    The summary shows mean and median, because the lecture warns that
    one strange number can fool the mean.
    """
    if not logged_in():
        return redirect("/login")
    day = request.args.get("date", "")
    try:
        start_hour = int(request.args.get("start_hour", "0"))
        end_hour = int(request.args.get("end_hour", "23"))
    except ValueError:
        return "Start and end hour must be numbers 0 to 23.", 400
    chart = request.args.get("chart", "bar")
    if chart not in ("bar", "histogram", "box", "scatter"):
        return "Chart must be bar, histogram, box, or scatter.", 400
    start_hour = max(0, min(23, start_hour))
    end_hour = max(0, min(23, end_hour))
    if end_hour < start_hour:
        return "End hour must be after start hour.", 400
    df = analysis.load_from_db()
    if not df.empty:
        df = df[df["timestamp"] >= pd.to_datetime("2026-11-26")]
    if day:
        try:
            picked = pd.to_datetime(day).date()
        except ValueError:
            return "Date must be YYYY-MM-DD.", 400
        df = df[df["timestamp"].dt.date == picked]
    df = df[(df["timestamp"].dt.hour >= start_hour)
            & (df["timestamp"].dt.hour <= end_hour)]
    if df.empty:
        return "No readings for that day and time. Pick another.", 404
    counts = analysis.taken_per_check(df)
    total_checks = int(df["timestamp"].nunique())
    mean_taken = round(float(counts.mean()), 1)
    median_taken = round(float(counts.median()), 1)
    top_hours = [
        (int(h), round(float(s), 1))
        for h, s in analysis.busiest_hours(df).head(3).items()
    ]
    first_time = str(df["timestamp"].min())
    last_time = str(df["timestamp"].max())
    chart_names = {
        "bar": "Bar chart: average seats taken by hour",
        "histogram": "Histogram: how often each occupancy level happens",
        "box": "Box plot: middle and outliers of seats taken",
        "scatter": "Scatter plot: hour of day against seats taken",
    }
    # Build the chosen chart to an image in memory.
    from io import BytesIO
    chart_buf = BytesIO()
    tmp_path = os.path.join("static", "custom-chart.png")
    if chart == "bar":
        analysis.plot_hourly(df, tmp_path)
    elif chart == "histogram":
        analysis.plot_histogram(df, tmp_path)
    elif chart == "box":
        analysis.plot_box(df, tmp_path)
    else:
        analysis.plot_scatter(df, tmp_path)
    with open(tmp_path, "rb") as f:
        chart_buf.write(f.read())
    chart_buf.seek(0)
    chart_img = plt.imread(chart_buf)
    # Build the PDF: logo, title, summary, then the chart.
    logo_path = os.path.join(os.path.dirname(__file__),
                             "static", "lcc-logo.jpg")
    logo = plt.imread(logo_path)
    fig = plt.figure(figsize=(8.5, 11))
    logo_ax = fig.add_axes([0.425, 0.86, 0.15, 0.116])
    logo_ax.imshow(logo)
    logo_ax.axis("off")
    fig.text(0.5, 0.83, "Legacy College of Compostela",
             fontsize=16, weight="bold", ha="center", family="Arial")
    fig.text(0.5, 0.80, "Library Occupancy Report (Custom)",
             fontsize=13, weight="bold", ha="center", family="Arial")
    lines = [
        "",
        f"Day: {day or 'all days from 26 Nov 2026'}, "
        f"hours {start_hour:02d}:00 to {end_hour:02d}:00.",
        f"Chart: {chart_names[chart]}.",
        f"Data: real readings from the library camera, "
        f"{first_time} to {last_time}.",
        f"Total checks: {total_checks}",
        f"Mean seats taken: {mean_taken}",
        f"Median seats taken: {median_taken}",
        "",
        "Busiest hours (average seats taken):",
    ]
    for hour, seats in top_hours:
        lines.append(f"  {hour:02d}:00 - {seats} seats")
    lines.append("")
    lines.append(
        "Mean and median are both shown because one strange check "
        "can fool the mean; the median is the honest centre.")
    import textwrap
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=70) or [""])
    body = "\n".join(wrapped)
    fig.text(0.1, 0.76, body, fontsize=11, family="Arial",
             verticalalignment="top")
    chart_ax = fig.add_axes([0.08, 0.05, 0.84, 0.32])
    chart_ax.imshow(chart_img)
    chart_ax.axis("off")
    buf = BytesIO()
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition":
                 "attachment; filename=library-occupancy-report-custom.pdf"},
    )


@app.route("/history")
def history():
    """One row per check, newest first, latest 100 checks.

    The old page showed one row per seat per check, which is thousands
    of rows nobody can read as a report. A check is one moment in time,
    so the report shows the time, how many seats were taken, and how
    many were vacant. The summary at the top says how many checks there
    are in total and the average seats taken.
    """
    if not logged_in():
        return redirect("/login")
    rows = database.get_history()
    by_time = {}
    for ts, seat, taken in rows:
        check = by_time.setdefault(ts, {"taken": 0, "total": 0})
        check["total"] += 1
        if taken:
            check["taken"] += 1
    checks = [
        {"time": ts, "taken": c["taken"], "vacant": c["total"] - c["taken"],
         "total": c["total"],
         "pct": round(c["taken"] / c["total"] * 100) if c["total"] else 0}
        for ts, c in sorted(by_time.items(), reverse=True)
    ]
    busiest = max(checks, key=lambda c: c["taken"]) if checks else None
    total_checks = len(checks)
    if checks:
        avg_taken = round(sum(c["taken"] for c in checks) / total_checks, 1)
        first_time = checks[-1]["time"]
        last_time = checks[0]["time"]
    else:
        avg_taken = 0
        first_time = ""
        last_time = ""
    return render_template(
        "history.html",
        checks=checks[:100],
        total_checks=total_checks,
        avg_taken=avg_taken,
        first_time=first_time,
        last_time=last_time,
        busiest=busiest,
    )


@app.route("/api/status")
def api_status():
    if not logged_in():
        return jsonify(error="login required"), 401
    return jsonify(database.get_latest())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
