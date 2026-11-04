"""calibrate.py - click the seats on a camera picture to make seats.json.

How to use:
  1. Run:  python calibrate.py --table T1
  2. A picture from the camera appears (it is only shown, never saved).
  3. For each seat, click TWO opposite corners (for example top-left, then bottom-right).
     The seats are named T1-S1, T1-S2, ... in the order you click.
  4. Keys:  u = undo the last seat    s = save seats.json    q = quit without saving

Run it again with a different table (--table T2 --append) to add more seats.
"""

import argparse
import json
import os
import shutil

WINDOW = "Calibrate seats (click 2 corners per seat)"


def make_box(p1, p2):
    """Turn two clicked corners into a box (x1, y1, x2, y2) = left, top, right, bottom."""
    x1, y1 = p1
    x2, y2 = p2
    return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]


def seat_name(table, number):
    return f"{table}-S{number}"


def save_seats(seats, path, append=False):
    """Write the seats to a JSON file. Keeps a backup of the old file."""
    if os.path.exists(path):
        shutil.copy(path, path + ".bak")
        if append:
            with open(path) as f:
                old = json.load(f)
            old.update(seats)
            seats = old
    with open(path, "w") as f:
        json.dump(seats, f, indent=2)
    return seats


def grab_picture(source, image_path):
    """Get one picture to draw on, from an image file or a camera."""
    import cv2

    if image_path:
        frame = cv2.imread(image_path)
        if frame is None:
            raise SystemExit(f"Could not open the image: {image_path}")
        return frame

    src = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"Could not open the camera: {source}")
    frame = None
    for _ in range(10):  # skip a few frames so the camera can adjust
        ok, frame = cap.read()
    cap.release()
    if frame is None:
        raise SystemExit("Could not read a picture from the camera.")
    return frame


def main():
    import cv2

    parser = argparse.ArgumentParser(description="Click seats to make seats.json")
    parser.add_argument("--source", default="0", help="0 for webcam, or a phone video address")
    parser.add_argument("--image", help="use a picture file instead of a camera")
    parser.add_argument("--table", default="T1", help="table name used in the seat names")
    parser.add_argument("--out", default="seats.json", help="file to write")
    parser.add_argument("--append", action="store_true", help="add to the existing file")
    args = parser.parse_args()

    base = grab_picture(args.source, args.image)
    seats = {}          # name -> box
    clicks = []         # corners clicked so far for the current seat

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((x, y))
            if len(clicks) == 2:
                name = seat_name(args.table, len(seats) + 1)
                seats[name] = make_box(clicks[0], clicks[1])
                clicks.clear()

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_mouse)
    print("Click two opposite corners of each seat. Keys: u = undo, s = save, q = quit.")

    while True:
        view = base.copy()
        for name, (x1, y1, x2, y2) in seats.items():
            cv2.rectangle(view, (x1, y1), (x2, y2), (0, 200, 0), 2)
            cv2.putText(view, name, (x1, max(15, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        for point in clicks:
            cv2.circle(view, point, 4, (0, 0, 255), -1)
        cv2.imshow(WINDOW, view)

        key = cv2.waitKey(30) & 0xFF
        if key == ord("u") and seats:
            removed = list(seats)[-1]
            del seats[removed]
            clicks.clear()
            print("Removed", removed)
        elif key == ord("s"):
            if not seats:
                print("No seats yet. Click some seats first.")
                continue
            final = save_seats(seats, args.out, args.append)
            print(f"Saved {len(final)} seats to {args.out}")
            break
        elif key == ord("q"):
            print("Quit without saving.")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()