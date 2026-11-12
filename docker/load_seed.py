"""Load database/*.csv into Postgres when the students table is empty."""

import csv
import os
import time
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "database"


def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def connect():
    return psycopg2.connect(database_url())


def wait_for_students_table():
    for _ in range(30):
        try:
            with connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass('public.students')")
                    if cur.fetchone()[0] is not None:
                        return
        except psycopg2.OperationalError:
            pass
        time.sleep(1)
    raise SystemExit("Postgres did not become ready")


def blank(value):
    if value is None:
        return None
    text = value.strip()
    return text or None


def rows(name):
    with (DATABASE / f"{name}.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load(cur):
    for row in rows("students"):
        cur.execute(
            """
            INSERT INTO students (
                student_id, netid, name, school_year, intro_programming,
                skill_programming, skill_data_stats, skill_frontend_design,
                skill_business_pitch, working_style, interests, semester_goal,
                submitted_at
            )
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                int(row["student_id"]),
                row["netid"].strip(),
                row["name"].strip(),
                row["school_year"].strip(),
                row["intro_programming"].strip(),
                int(row["skill_programming"]),
                int(row["skill_data_stats"]),
                int(row["skill_frontend_design"]),
                int(row["skill_business_pitch"]),
                blank(row["working_style"]),
                blank(row["interests"]),
                blank(row["semester_goal"]),
                row["submitted_at"].strip(),
            ),
        )

    for row in rows("tools"):
        cur.execute(
            """
            INSERT INTO tools (id, name)
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s)
            """,
            (int(row["id"]), row["name"].strip()),
        )

    for row in rows("availability"):
        cur.execute(
            """
            INSERT INTO availability (id, name)
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s)
            """,
            (int(row["id"]), row["name"].strip()),
        )

    for row in rows("student_tools"):
        cur.execute(
            """
            INSERT INTO student_tools (student_id, tool_id)
            VALUES (%s, %s)
            """,
            (int(row["student_id"]), int(row["tool_id"])),
        )

    for row in rows("student_availability"):
        cur.execute(
            """
            INSERT INTO student_availability (student_id, availability_id)
            VALUES (%s, %s)
            """,
            (int(row["student_id"]), int(row["availability_id"])),
        )

    for table, column in (
        ("students", "student_id"),
        ("tools", "id"),
        ("availability", "id"),
    ):
        cur.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', '{column}'),
                COALESCE((SELECT MAX({column}) FROM {table}), 1)
            )
            """
        )


def main():
    wait_for_students_table()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM students")
            if cur.fetchone()[0]:
                print("students already loaded")
                return
            load(cur)
        conn.commit()
    print("loaded database csvs")


if __name__ == "__main__":
    main()
