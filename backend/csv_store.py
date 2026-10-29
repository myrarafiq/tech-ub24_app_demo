"""Read the placeholder CSV tables in database/."""

import csv
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[1] / "database"


def read_table(name):
    path = DATABASE / f"{name}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def list_students():
    return [
        {"student_id": row["student_id"], "name": row["name"]}
        for row in read_table("students")
    ]
