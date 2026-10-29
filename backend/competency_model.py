"""Average each competency score across the class."""

from backend.csv_store import read_table

COMPETENCIES = (
    ("skill_programming", "Programming"),
    ("skill_data_stats", "Data and stats"),
    ("skill_frontend_design", "Frontend design"),
    ("skill_business_pitch", "Business pitch"),
)


def average_competencies():
    rows = read_table("students")
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
