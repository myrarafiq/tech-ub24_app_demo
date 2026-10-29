"""Serve the names page and read students from Postgres."""

import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from backend.competency_model import average_competencies
from backend.csv_store import list_students
from backend.db import query

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"


def load_dotenv(path):
    """Load KEY=value pairs from .env without overriding real environment variables."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")

app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


def api_error(exc):
    app.logger.error("database request failed: %s", type(exc).__name__)
    return jsonify({"error": "Could not load data"}), 500


@app.get("/api/students")
def students():
    try:
        if os.environ.get("DATABASE_URL"):
            rows = query(
                "SELECT student_id, name FROM students ORDER BY student_id"
            )
            payload = [
                {"student_id": student_id, "name": name}
                for student_id, name in rows
            ]
        else:
            payload = list_students()
    except Exception as exc:
        return api_error(exc)
    return jsonify(payload)


@app.get("/api/competencies")
def competencies():
    try:
        averages = average_competencies()
    except Exception as exc:
        return api_error(exc)
    return jsonify(averages)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
