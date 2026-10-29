"""Connect to Postgres using DATABASE_URL from the environment."""

import os

import psycopg2


def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def query(sql):
    with psycopg2.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
