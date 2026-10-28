"""monitor.py - the main loop of the Library Occupancy Counter.

Flow:  camera frame -> detector finds people -> occupancy.py decides each seat
       -> database.py saves taken/vacant -> dashboard (app.py) shows it.

No camera images are ever saved. Each frame is used once and thrown away.

Examples:
    python monitor.py --fake                  (no camera needed, for testing)
    python monitor.py --source 0 --show       (laptop webcam, show a preview)
    python monitor.py --source http://192.168.1.15:8080/video   (phone, IP Webcam)
"""

import argparse
import json
import random
import time

from database import init_db, save_reading
from occupancy import SeatTracker, assign_people_to_seats, summarize


def load_seats(path):
    """Read seats.json -> {"T1-S1": (x1, y1, x2, y2), ...}"""
    with open(path) as f:
        data = json.load(f)
    return {name: tuple(box) for name, box in data.items()}


def fake_people(seats):
    """Pretend detector for testing: puts a person on about half of the seats."""
    people = []
    for x1, y1, x2, y2 in seats.values():
        if random.random() < 0.5:
            people.append((x1 - 5, y1 - 30, x2 + 5, y2))
    return people


def load_detector():
    """Load the YOLOv8 nano model (downloads the file the first time)."""
    from ultralytics import YOLO

    return YOLO("yolov8n.pt")


def detect_people(model, frame):
    """Return a list of person boxes (x1, y1, x2, y2) found in one frame."""
    results = model(frame, classes=[0], verbose=False)  # class 0 = person
    return [tuple(box) for box in results[0].boxes.xyxy.tolist()]


def draw_preview(frame, seats, people, status):
    """Draw seat boxes (red = taken, green = vacant) and people boxes (blue)."""
    import cv2

    for name, (x1, y1, x2, y2) in seats.items():
        color = (0, 0, 255) if status[name] else (0, 200, 0)
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(frame, name, (int(x1), int(y1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    for x1, y1, x2, y2 in people:
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 150, 0), 1)
    cv2.imshow("Library Occupancy Counter (press q to quit)", frame)
    return cv2.waitKey(1) & 0xFF == ord("q")


def main():
    parser = argparse.ArgumentParser(description="Library seat monitor")
    parser.add_argument("--seats", default="seats.json", help="seat boxes file")
    parser.add_argument("--source", default="0",
                        help="0 for webcam, or a phone video address")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="seconds between checks")
    parser.add_argument("--fake", action="store_true",
                        help="use a fake detector (no camera needed)")
    parser.add_argument("--show", action="store_true",
                        help="show a live preview window")
    parser.add_argument("--count", type=int, default=0,
                        help="stop after this many checks (0 = run forever)")
    args = parser.parse_args()

    seats = load_seats(args.seats)
    init_db()
    tracker = SeatTracker(seats)

    cap = None
    model = None
    if not args.fake:
        import cv2

        source = int(args.source) if args.source.isdigit() else args.source
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print("Could not open the camera:", args.source)
            return
        model = load_detector()

    print("Monitoring", len(seats), "seats. Press Ctrl+C to stop.")
    checks = 0
    try:
        while True:
            frame = None
            if args.fake:
                people = fake_people(seats)
            else:
                ok, frame = cap.read()
                if not ok:
                    print("Could not read a frame, trying again...")
                    time.sleep(1)
                    continue
                people = detect_people(model, frame)

            frame_result = assign_people_to_seats(seats, people)
            status = tracker.update(frame_result)
            save_reading(status)

            info = summarize(status)
            print(time.strftime("%H:%M:%S"),
                  "taken:", info["taken"], "vacant:", info["vacant"],
                  "FULL" if info["full"] else "")

            if args.show and frame is not None:
                if draw_preview(frame, seats, people, status):
                    break

            checks += 1
            if args.count and checks >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        if cap is not None:
            cap.release()
        if args.show:
            import cv2

            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()