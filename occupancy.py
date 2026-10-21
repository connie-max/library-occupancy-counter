"""occupancy.py - decides which library seats are taken or vacant.

A box is (x1, y1, x2, y2) = left, top, right, bottom.
"""

OVERLAP_NEEDED = 0.30   # a person must cover at least 30% of a seat
HISTORY_SIZE = 5        # remember the last 5 checks of each seat
VOTES_NEEDED = 3        # seat is taken if 3 of those 5 checks say taken


def overlap_ratio(seat, person):
    """Fraction of the seat box that is covered by the person box (0 to 1)."""
    sx1, sy1, sx2, sy2 = seat
    px1, py1, px2, py2 = person

    # the rectangle where the two boxes overlap
    left = max(sx1, px1)
    top = max(sy1, py1)
    right = min(sx2, px2)
    bottom = min(sy2, py2)

    # if the boxes don't touch, width or height is negative -> use 0
    width = max(0, right - left)
    height = max(0, bottom - top)

    overlap_area = width * height
    seat_area = (sx2 - sx1) * (sy2 - sy1)
    return overlap_area / seat_area


def assign_people_to_seats(seats, people):
    """Check ONE camera frame.

    seats  = {"A1": (x1, y1, x2, y2), "A2": ...}
    people = [(x1, y1, x2, y2), ...]  boxes from the detector
    Returns {"A1": True, "A2": False, ...}  (True = taken in this frame)
    """
    taken = {name: False for name in seats}

    for person in people:
        best_seat = None
        best_ratio = 0
        # find the seat this person overlaps the most
        for name, box in seats.items():
            ratio = overlap_ratio(box, person)
            if ratio > best_ratio:
                best_ratio = ratio
                best_seat = name
        # only count it if the overlap is big enough
        if best_seat is not None and best_ratio >= OVERLAP_NEEDED:
            taken[best_seat] = True

    return taken


class SeatTracker:
    """Remembers the last few checks so one bad frame doesn't flip a seat."""

    def __init__(self, seat_names):
        self.history = {name: [] for name in seat_names}

    def update(self, frame_result):
        """Add one frame's result, then return the steady status of every seat."""
        status = {}
        for name, is_taken in frame_result.items():
            self.history[name].append(is_taken)
            # keep only the last 5 checks
            if len(self.history[name]) > HISTORY_SIZE:
                self.history[name].pop(0)
            # True counts as 1, so sum() = number of "taken" checks
            status[name] = sum(self.history[name]) >= VOTES_NEEDED
        return status


def summarize(status):
    """Count seats. FULL only when every seat is taken."""
    total = len(status)
    taken = sum(status.values())
    vacant = total - taken
    return {
        "total": total,
        "taken": taken,
        "vacant": vacant,
        "full": total > 0 and vacant == 0,
    }


if __name__ == "__main__":
    # quick self-test with made-up boxes
    print(overlap_ratio((0, 0, 10, 10), (5, 0, 15, 10)))      # 0.5
    print(overlap_ratio((0, 0, 10, 10), (0, 0, 10, 10)))      # 1.0
    print(overlap_ratio((0, 0, 10, 10), (50, 50, 60, 60)))    # 0.0

    seats = {"A1": (0, 0, 10, 10), "A2": (20, 0, 30, 10)}
    tracker = SeatTracker(seats)
    people = [(1, 1, 9, 9)]  # one person sitting at A1
    for _ in range(3):
        status = tracker.update(assign_people_to_seats(seats, people))
    print(status)             # {'A1': True, 'A2': False}
    print(summarize(status))  # taken 1, vacant 1, full False