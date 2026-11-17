# Library Occupancy Counter

DSA final project (IT 112 - Data Science and Algorithms, 3B). A camera watches
the library seats, Python marks each seat as taken or vacant, and a Flask
dashboard shows staff the live seat map.

No camera images are ever saved. Only time, seat name, and taken/vacant (1/0)
are stored in SQLite.

## Members

| Member                     | Role / files                                                                                         |
| -------------------------- | ---------------------------------------------------------------------------------------------------- |
| Conrey Dee Manguiran (Con) | Team leader — `occupancy.py`, `database.py`, `monitor.py`, `calibrate.py`, `tests/test_occupancy.py` |
| Gerald                     | Dashboard — `app.py`, `templates/`, `static/style.css`                                               |
| Carla                      | Analysis — `analysis.py`                                                                             |
| Angelica (Angel)           | Accuracy log and how-to notes, README members section — `docs/accuracy-log.csv`                      |
| John Lloyd                 | Permission documents — `docs/permission-letter.docx`, `docs/privacy-and-permission.docx`             |
| Jerald                     | Staff guide — `docs/staff-guide.md`                                                                  |
| Myla                       | Library survey — `docs/library-survey.md`                                                            |
| Jay                        | Phone camera setup — `docs/phone-camera-setup.md`, `test_camera.py`, `images/`                       |

## Status

Core code done, 18 unit tests pass. Live detector works with the webcam.
Dashboard works with fake data. Sample seat boxes (4 seats, T1-S1 to T1-S4)
are in `seats.json` — not the final library calibration.

Still to do before the final: test live detector + dashboard together,
mount the camera high at the library, calibrate the real seats, run the
real test and fill the accuracy log, update slides and proposal.

## Quick start

```bash
python -m unittest discover -s tests -v
python monitor.py --fake --count 5
python monitor.py --fake --busy --count 5   # show LIBRARY FULL on demand
python monitor.py --show                    # live webcam preview
```

Dashboard (in a second terminal):

```bash
python monitor.py --fake
python app.py
# open http://localhost:5000, login staff / demo-pass-123 (demo account)
```

## How it works

Camera frame -> detector finds people -> `occupancy.py` decides each seat
(a person must cover at least 30% of the seat box, each person takes only
one seat, a seat is taken if 3 of the last 5 checks say taken) ->
`database.py` saves time, seat, 1 or 0 to SQLite -> `app.py` shows it to
staff after login -> `analysis.py` finds busy hours. `seats.json` holds
the seat boxes as [x1, y1, x2, y2] numbers in the 640x480 frame.
