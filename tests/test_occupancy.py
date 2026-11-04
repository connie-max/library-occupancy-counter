"""Unit tests for occupancy.py

Run from the project folder:
    python -m unittest discover -s tests
"""

import os
import sys
import unittest

# let the tests find occupancy.py in the project folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from occupancy import (  # noqa: E402
    SeatTracker,
    assign_people_to_seats,
    overlap_ratio,
    summarize,
)

SEAT = (0, 0, 10, 10)


class TestOverlapRatio(unittest.TestCase):
    def test_person_exactly_on_seat(self):
        self.assertEqual(overlap_ratio(SEAT, (0, 0, 10, 10)), 1.0)

    def test_half_overlap(self):
        self.assertEqual(overlap_ratio(SEAT, (5, 0, 15, 10)), 0.5)

    def test_far_apart(self):
        self.assertEqual(overlap_ratio(SEAT, (50, 50, 60, 60)), 0.0)

    def test_boxes_only_touch_at_edge(self):
        self.assertEqual(overlap_ratio(SEAT, (10, 0, 20, 10)), 0.0)

    def test_person_bigger_than_seat(self):
        # a big person box covers the whole seat
        self.assertEqual(overlap_ratio(SEAT, (-5, -5, 20, 20)), 1.0)


class TestAssignPeopleToSeats(unittest.TestCase):
    def setUp(self):
        self.seats = {"A1": (0, 0, 10, 10), "A2": (20, 0, 30, 10)}

    def test_no_people_means_all_vacant(self):
        result = assign_people_to_seats(self.seats, [])
        self.assertEqual(result, {"A1": False, "A2": False})

    def test_person_on_a1(self):
        result = assign_people_to_seats(self.seats, [(1, 1, 9, 9)])
        self.assertEqual(result, {"A1": True, "A2": False})

    def test_small_overlap_is_ignored(self):
        # covers only 10% of A1, below the 30% rule
        result = assign_people_to_seats(self.seats, [(9, 0, 19, 10)])
        self.assertEqual(result["A1"], False)

    def test_exactly_30_percent_counts(self):
        # covers exactly 30% of A1
        result = assign_people_to_seats(self.seats, [(7, 0, 17, 10)])
        self.assertEqual(result["A1"], True)

    def test_person_takes_only_one_seat(self):
        # this person overlaps both seats, but must take only the bigger overlap
        seats = {"A1": (0, 0, 10, 10), "A2": (8, 0, 18, 10)}
        result = assign_people_to_seats(seats, [(0, 0, 9, 10)])
        self.assertEqual(result, {"A1": True, "A2": False})

    def test_two_people_two_seats(self):
        people = [(1, 1, 9, 9), (21, 1, 29, 9)]
        result = assign_people_to_seats(self.seats, people)
        self.assertEqual(result, {"A1": True, "A2": True})


class TestSeatTracker(unittest.TestCase):
    def test_needs_three_taken_checks(self):
        tracker = SeatTracker(["A1"])
        self.assertFalse(tracker.update({"A1": True})["A1"])   # 1 vote
        self.assertFalse(tracker.update({"A1": True})["A1"])   # 2 votes
        self.assertTrue(tracker.update({"A1": True})["A1"])    # 3 votes

    def test_one_bad_frame_does_not_flip_seat(self):
        tracker = SeatTracker(["A1"])
        for _ in range(5):
            tracker.update({"A1": True})
        # one frame where the detector missed the person
        self.assertTrue(tracker.update({"A1": False})["A1"])

    def test_seat_becomes_vacant_after_person_leaves(self):
        tracker = SeatTracker(["A1"])
        for _ in range(5):
            tracker.update({"A1": True})
        status = None
        for _ in range(3):
            status = tracker.update({"A1": False})
        self.assertFalse(status["A1"])

    def test_only_last_five_checks_are_kept(self):
        tracker = SeatTracker(["A1"])
        for _ in range(20):
            tracker.update({"A1": True})
        self.assertEqual(len(tracker.history["A1"]), 5)


class TestSummarize(unittest.TestCase):
    def test_counts(self):
        info = summarize({"A1": True, "A2": False, "A3": True})
        self.assertEqual(info["total"], 3)
        self.assertEqual(info["taken"], 2)
        self.assertEqual(info["vacant"], 1)
        self.assertFalse(info["full"])

    def test_full_when_all_taken(self):
        self.assertTrue(summarize({"A1": True, "A2": True})["full"])

    def test_empty_is_not_full(self):
        self.assertFalse(summarize({})["full"])


if __name__ == "__main__":
    unittest.main()