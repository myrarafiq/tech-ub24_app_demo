"""Assign students to groups by dealing clusters round-robin."""

import csv
from pathlib import Path

from cluster_model import predict_cluster

SKILL_COLUMNS = (
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
)

DATA_PATH = Path(__file__).resolve().parent / "class_dataset.csv"


def assign_groups(students, n_groups=8):
    """Label each student with a cluster and a group number starting at 1.

    Clusters are dealt from largest to smallest. Within a cluster, students
    are ordered by id. The deal continues across clusters, so group numbers
    do not restart when the next cluster begins. Equal-sized clusters are
    ordered by cluster number.
    """
    labeled = []
    for student in students:
        skills = tuple(student[column] for column in SKILL_COLUMNS)
        labeled.append(
            {
                "id": student["id"],
                "cluster": predict_cluster(skills),
                "group": None,
            }
        )

    by_cluster = {}
    for student in labeled:
        by_cluster.setdefault(student["cluster"], []).append(student)

    ordered_clusters = sorted(
        by_cluster,
        key=lambda cluster: (-len(by_cluster[cluster]), cluster),
    )

    deal = []
    for cluster in ordered_clusters:
        members = sorted(by_cluster[cluster], key=lambda student: student["id"])
        deal.extend(members)

    for index, student in enumerate(deal):
        student["group"] = (index % n_groups) + 1

    return labeled


def load_students(path):
    students = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            student = {"id": row["netid"]}
            for column in SKILL_COLUMNS:
                student[column] = float(row[column])
            students.append(student)
    return students


def main():
    assigned = assign_groups(load_students(DATA_PATH))
    clusters = sorted({student["cluster"] for student in assigned})
    groups = sorted({student["group"] for student in assigned})
    missing = 0
    for group in groups:
        members = [student for student in assigned if student["group"] == group]
        counts = {cluster: 0 for cluster in clusters}
        for student in members:
            counts[student["cluster"]] += 1
        count_text = ", ".join(f"{cluster}: {counts[cluster]}" for cluster in clusters)
        print(f"group {group}: n={len(members)} clusters=({count_text})")
        if any(count == 0 for count in counts.values()):
            missing += 1
    print(f"groups missing a cluster: {missing}")


if __name__ == "__main__":
    main()
