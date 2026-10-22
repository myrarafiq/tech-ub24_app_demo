"""Apply schema.sql and load class_dataset.csv into Railway Postgres.

Reads DATABASE_URL from the environment or from a local .env file.
Use the public Railway URL locally (host like *.proxy.rlwy.net).
The private host (*.railway.internal) only works from inside Railway.
"""

import csv
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent
TABLES = (
    "students",
    "tools",
    "student_tools",
    "availability",
    "student_availability",
)


def load_dotenv(path):
    """Load KEY=value pairs from a .env file without overriding existing vars."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def dataset_path():
    """Use data/class_dataset.csv when present, otherwise the repo-root copy."""
    preferred = ROOT / "data" / "class_dataset.csv"
    if preferred.exists():
        return preferred
    fallback = ROOT / "class_dataset.csv"
    if fallback.exists():
        return fallback
    raise SystemExit(f"Could not find {preferred} or {fallback}")


def sql_statements(script):
    """Split a SQL script into individual statements."""
    lines = []
    for line in script.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def split_values(cell):
    """Split a semicolon-joined cell into stripped, non-empty values."""
    return [part.strip() for part in (cell or "").split(";") if part.strip()]


def clean_text(value):
    """Trim text. Treat blanks and the Excel error #NAME? as SQL NULL."""
    if value is None:
        return None
    text = value.strip()
    if not text or text == "#NAME?":
        return None
    return text


def main():
    load_dotenv(ROOT / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set. Add the public Railway URL to .env.")
    if "railway.internal" in database_url:
        raise SystemExit(
            "DATABASE_URL uses the private Railway host. "
            "From a laptop, use DATABASE_PUBLIC_URL instead."
        )

    schema_sql = (ROOT / "schema.sql").read_text()
    csv_path = dataset_path()

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DROP TABLE IF EXISTS
                    student_tools,
                    student_availability,
                    tools,
                    availability,
                    students
                """
            )
            for statement in sql_statements(schema_sql):
                cur.execute(statement)

            with csv_path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    cur.execute(
                        """
                        INSERT INTO students (
                            netid, name, school_year, intro_programming,
                            skill_programming, skill_data_stats,
                            skill_frontend_design, skill_business_pitch,
                            working_style, interests, semester_goal, submitted_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING student_id
                        """,
                        (
                            row["netid"].strip(),
                            row["name"].strip(),
                            row["school_year"].strip(),
                            row["intro_programming"].strip(),
                            int(row["skill_programming"]),
                            int(row["skill_data_stats"]),
                            int(row["skill_frontend_design"]),
                            int(row["skill_business_pitch"]),
                            clean_text(row["working_style"]),
                            clean_text(row["interests"]),
                            clean_text(row["semester_goal"]),
                            row["submitted_at"].strip(),
                        ),
                    )
                    student_id = cur.fetchone()[0]

                    for tool_name in split_values(row["tools"]):
                        cur.execute(
                            """
                            INSERT INTO tools (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                            """,
                            (tool_name,),
                        )
                        tool_id = cur.fetchone()[0]
                        cur.execute(
                            """
                            INSERT INTO student_tools (student_id, tool_id)
                            VALUES (%s, %s)
                            """,
                            (student_id, tool_id),
                        )

                    for slot in split_values(row["availability"]):
                        cur.execute(
                            """
                            INSERT INTO availability (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                            """,
                            (slot,),
                        )
                        availability_id = cur.fetchone()[0]
                        cur.execute(
                            """
                            INSERT INTO student_availability (student_id, availability_id)
                            VALUES (%s, %s)
                            """,
                            (student_id, availability_id),
                        )

            print(f"Loaded {csv_path}")
            for table in TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                print(f"{table}: {cur.fetchone()[0]}")


if __name__ == "__main__":
    main()
