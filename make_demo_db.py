import sqlite3
import random
import os

random.seed(7)
os.makedirs('data', exist_ok=True)
db = 'data/demo_seats.db'
if os.path.exists(db):
    os.remove(db)
conn = sqlite3.connect(db)
conn.execute('CREATE TABLE readings (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, seat TEXT NOT NULL, taken INTEGER NOT NULL)')
seats = ['T1-S%d' % i for i in range(1, 11)] + ['T2-S%d' % i for i in range(1, 6)] + ['T3-S%d' % i for i in range(1, 5)] + ['T4-S1'] + ['T5-S%d' % i for i in range(1, 5)] + ['T6-S%d' % i for i in range(1, 3)] + ['T7-S%d' % i for i in range(1, 3)] + ['T8-S%d' % i for i in range(1, 3)]
pattern = {8: 3.0, 9: 12.0, 10: 18.0, 11: 22.0, 12: 30.0, 13: 27.0, 14: 18.0, 15: 12.0, 16: 3.0}
rows = []
for hour, avg in pattern.items():
    for minute in range(0, 60, 2):
        n = max(0, min(30, round(avg + random.uniform(-2.5, 2.5))))
        taken_seats = random.sample(seats, n)
        ts = '2026-11-25 %02d:%02d:00' % (hour, minute)
        for s in seats:
            rows.append((ts, s, 1 if s in taken_seats else 0))
conn.executemany('INSERT INTO readings (timestamp, seat, taken) VALUES (?, ?, ?)', rows)
conn.commit()
print('done, rows:', len(rows))
conn.close()
