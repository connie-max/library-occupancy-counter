"""analysis.py - busiest hours from the real readings in data/seats.db.

Carla's original functions are kept: taken_per_check, busiest_hours,
plot_hourly. The fix is in how data is loaded: the old __main__ tried to
read data/sample.csv, which does not exist in the repo, so
`python analysis.py` crashed with FileNotFoundError.

Now it reads from SQLite via database.get_history(), which is where
monitor.py actually saves readings. A CSV path can still be given
with --csv if you want to analyse an exported file instead.
"""

import argparse
import os

import pandas as pd

import matplotlib
matplotlib.use("Agg")  # no window, draw to files only (Flask runs in threads)
import matplotlib.pyplot as plt

import database


def load_readings(path):
    """Load a CSV export: columns timestamp, seat, taken."""
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_from_db(path=None):
    """Load all readings from SQLite as a DataFrame.

    database.get_history() returns [(timestamp, seat, taken), ...]
    oldest first. Returns an empty DataFrame (with the right columns)
    when there are no readings yet.
    """
    rows = database.get_history(path)
    df = pd.DataFrame(rows, columns=["timestamp", "seat", "taken"])
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def taken_per_check(df):
    result = df.groupby("timestamp")["taken"].sum()
    return result


def busiest_hours(df):
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour

    # Count occupied seats at each check, then find the hourly average
    check_counts = taken_per_check(df)
    check_counts = check_counts.reset_index()
    check_counts["hour"] = check_counts["timestamp"].dt.hour

    result = check_counts.groupby("hour")["taken"].mean()
    return result.sort_values(ascending=False)


def predict_next_peak(df):
    """Predict the next busy period, in plain words.

    The next peak is the hour with the highest average seats taken,
    because that hour was the busiest in the data we already have.
    Returns (hour, expected seats taken).
    """
    hourly = busiest_hours(df)
    hour = int(hourly.index[0])
    seats = round(float(hourly.iloc[0]), 1)
    return hour, seats


def busiest_days(df):
    """Average seats taken per day, busiest first.

    Same idea as busiest_hours, but grouped by calendar day, so the
    report can say which days are busiest, not just which hours.
    Returns a Series indexed by date, sorted highest first.
    """
    check_counts = taken_per_check(df)
    check_counts = check_counts.reset_index()
    check_counts["day"] = check_counts["timestamp"].dt.date

    result = check_counts.groupby("day")["taken"].mean()
    return result.sort_values(ascending=False)


def plot_hourly(df, out_path):
    hourly = busiest_hours(df).sort_index()

    plt.figure(figsize=(10, 5))
    plt.bar(hourly.index, hourly.values)

    plt.xlabel("Hour of day")
    plt.ylabel("Average seats taken")
    plt.title("Average Library Occupancy by Hour")
    plt.xticks(range(24))
    plt.tight_layout()

    # Create the output folder if needed
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def plot_histogram(df, out_path):
    """Histogram (sir's lecture, slide 7): shape of the data.

    One variable: seats taken per check. Shows how the counts are
    spread: most checks have few seats taken, a few have many.
    """
    counts = taken_per_check(df)
    plt.figure(figsize=(10, 5))
    plt.hist(counts.values, bins=range(0, int(counts.max()) + 2),
             edgecolor="black")
    plt.xlabel("Seats taken in one check")
    plt.ylabel("Number of checks")
    plt.title("How Often Each Occupancy Level Happens (Histogram)")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def plot_box(df, out_path):
    """Box plot (sir's lecture, slide 7): middle + outliers.

    One variable: seats taken per check. The box is the middle half,
    the line inside is the median, the dots are outliers. The lecture
    warns that one strange number can fool the mean, so the median
    here is the honest centre.
    """
    counts = taken_per_check(df)
    plt.figure(figsize=(10, 5))
    plt.boxplot(counts.values, vert=False)
    plt.xlabel("Seats taken in one check")
    plt.title("Seats Taken per Check (Box Plot)")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def plot_scatter(df, out_path):
    """Scatter plot (sir's lecture, slide 7): two variables together.

    Hour of day (x) against seats taken (y). One dot is one check.
    Shows whether busy times cluster at certain hours.
    """
    check_counts = taken_per_check(df).reset_index()
    check_counts["hour"] = check_counts["timestamp"].dt.hour
    plt.figure(figsize=(10, 5))
    plt.scatter(check_counts["hour"], check_counts["taken"])
    plt.xlabel("Hour of day")
    plt.ylabel("Seats taken")
    plt.title("Seats Taken by Hour (Scatter Plot)")
    plt.xticks(range(24))
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busiest hours from seat readings")
    parser.add_argument("--csv", default=None,
                        help="optional CSV export to analyse instead of data/seats.db")
    parser.add_argument("--db", default=None,
                        help="optional SQLite path (default: data/seats.db)")
    args = parser.parse_args()

    if args.csv:
        df = load_readings(args.csv)
    else:
        df = load_from_db(args.db)

    if df.empty:
        print("No readings yet. Run monitor.py first, then run analysis.py again.")
    else:
        print(f"Readings: {len(df)} rows, {df['timestamp'].nunique()} checks")
        print("Top 3 busiest hours:")
        print(busiest_hours(df).head(3))
        print("Top 3 busiest days:")
        print(busiest_days(df).head(3))

        hour, seats = predict_next_peak(df)
        print(f"Next peak: tomorrow around {hour}:00, about {seats} seats taken.")

        plot_hourly(df, "static/hourly.png")
        print("Chart saved to static/hourly.png")
