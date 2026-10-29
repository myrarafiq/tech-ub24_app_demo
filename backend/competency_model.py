"""Average each competency score across the class."""

import os

from backend.csv_store import read_table
from backend.db import query

COMPETENCIES = (
    ("skill_programming", "Programming"),
    ("skill_data_stats", "Data and stats"),
    ("skill_frontend_design", "Frontend design"),
    ("skill_business_pitch", "Business pitch"),
)


def _averages_from_rows(rows):
    count = len(rows)
    averages = []
    for key, label in COMPETENCIES:
        if count == 0:
            average = None
        else:
            total = sum(int(row[key]) for row in rows)
            average = round(total / count, 2)
        averages.append({"skill": key, "label": label, "average": average})
    return averages


def average_competencies():
    if not os.environ.get("DATABASE_URL"):
        return _averages_from_rows(read_table("students"))

    columns = ", ".join(
        f"ROUND(AVG({key})::numeric, 2) AS {key}" for key, _label in COMPETENCIES
    )
    row = query(f"SELECT {columns} FROM students")[0]
    averages = []
    for (key, label), value in zip(COMPETENCIES, row):
        averages.append({
            "skill": key,
            "label": label,
            "average": None if value is None else float(value),
        })
    return averages
