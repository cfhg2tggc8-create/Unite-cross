import os
import sqlite3


DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    "unite_cross.db",
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_db_connection()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_key TEXT NOT NULL UNIQUE,
            match_datetime TEXT NOT NULL,
            game_mode TEXT,
            source_player TEXT,
            source_type TEXT NOT NULL DEFAULT 'manual',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS match_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            team_number INTEGER,
            pokemon_name TEXT,
            FOREIGN KEY (match_id)
                REFERENCES matches (id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_match_datetime
        ON matches (match_datetime);

        CREATE INDEX IF NOT EXISTS idx_player_name
        ON match_players (player_name);

        CREATE INDEX IF NOT EXISTS idx_match_players_match_id
        ON match_players (match_id);
        """
    )

    connection.commit()
    connection.close()


def get_database_counts():
    connection = get_db_connection()

    match_count = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM matches
        """
    ).fetchone()["count"]

    player_count = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM match_players
        """
    ).fetchone()["count"]

    connection.close()

    return {
        "match_count": match_count,
        "player_count": player_count,
    }
