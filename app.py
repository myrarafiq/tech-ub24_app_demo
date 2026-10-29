"""Python backend: serve the frontend and read the placeholder CSV database."""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from backend.competency_model import average_competencies
from backend.csv_store import list_students

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/api/students")
def students():
    return jsonify(list_students())


@app.get("/api/competencies")
def competencies():
    return jsonify(average_competencies())


if __name__ == "__main__":
    app.run(debug=True, port=5050)
