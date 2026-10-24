# How to Measure System Accuracy

This is how we will measure if the system is correct: we compare what we see with what the system says.

## 1. How to fill the log

File: `docs/accuracy-log.csv`

Write **one row per seat per check**. Columns:

| Column | Meaning | Example |
|---|---|---|
| `time` | Time of the check | `15:30` |
| `seat` | Seat ID | `T1-S1` |
| `real_status` | What you really see at the seat | `taken` or `vacant` |
| `system_status` | What the system shows for that seat | `taken` or `vacant` |

Steps:
1. Run the system and the camera.
2. Look at each seat in real life and write `real_status`.
3. Look at the system's answer for the same seat, at the same time, and write `system_status`.
4. Use only `taken` or `vacant` (lowercase, no extra spaces) so the counting is correct.
5. Add a new row for every seat in every check.

## 2. The formula

```
Accuracy = (rows where real_status equals system_status) / (total rows) x 100
```

A row is **correct** when `real_status` and `system_status` are the same.

## 3. Worked example (10 rows)

| # | time | seat | real_status | system_status | Match? |
|---|---|---|---|---|---|
| 1 | 15:30 | T1-S1 | taken | taken | Yes |
| 2 | 15:30 | T1-S2 | vacant | vacant | Yes |
| 3 | 15:30 | T1-S3 | taken | vacant | No |
| 4 | 15:30 | T1-S4 | vacant | vacant | Yes |
| 5 | 15:30 | T1-S5 | taken | taken | Yes |
| 6 | 15:30 | T1-S6 | vacant | vacant | Yes |
| 7 | 15:30 | T1-S7 | taken | taken | Yes |
| 8 | 15:30 | T1-S8 | vacant | taken | No |
| 9 | 15:30 | T1-S9 | taken | taken | Yes |
| 10 | 15:30 | T1-S10 | vacant | vacant | Yes |

- Total rows = 10
- Matching rows = 8
- Accuracy = 8 / 10 x 100 = **80%**
