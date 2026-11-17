import argparse
import os

import pandas as pd
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

        plot_hourly(df, "static/hourly.png")
        print("Chart saved to static/hourly.png")
