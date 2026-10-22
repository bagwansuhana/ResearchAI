
import json
import sqlite3
from pathlib import Path


# Store the database inside the project's data folder.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "researchai.db"


def get_connection():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_sessions (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT,
                session_json TEXT NOT NULL
            )
            """
        )


def save_session(session):
    if not session or not session.get("id"):
        raise ValueError(
            "A research session with an ID is required."
        )

    session_json = json.dumps(
        session,
        ensure_ascii=False,
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO research_sessions (
                id,
                question,
                created_at,
                status,
                session_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                question = excluded.question,
                created_at = excluded.created_at,
                status = excluded.status,
                session_json = excluded.session_json
            """,
            (
                session["id"],
                session.get("question", ""),
                session.get("created_at", ""),
                session.get("status", ""),
                session_json,
            ),
        )


def load_sessions():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT session_json
            FROM research_sessions
            ORDER BY created_at DESC
            """
        ).fetchall()

    sessions = []

    for row in rows:
        try:
            sessions.append(
                json.loads(row["session_json"])
            )
        except (json.JSONDecodeError, TypeError):
            continue

    return sessions


def load_session(session_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT session_json
            FROM research_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    if row is None:
        return None

    try:
        return json.loads(row["session_json"])
    except (json.JSONDecodeError, TypeError):
        return None


# Create the database and table if needed.
initialize_database()
