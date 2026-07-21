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
            source_url TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS match_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            team_number INTEGER,
            pokemon_name TEXT,
            result TEXT,
            FOREIGN KEY (match_id)
                REFERENCES matches (id)
                ON DELETE CASCADE,
            UNIQUE (match_id, normalized_name)
        );

        CREATE INDEX IF NOT EXISTS idx_matches_datetime
        ON matches (match_datetime);

        CREATE INDEX IF NOT EXISTS idx_matches_source_player
        ON matches (source_player);

        CREATE INDEX IF NOT EXISTS idx_match_players_name
        ON match_players (normalized_name);

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


def normalize_player_name(player_name):
    return player_name.strip().casefold()


def search_player_matches(player_name):
    normalized_name = normalize_player_name(player_name)
    connection = get_db_connection()

    target_player = connection.execute(
        """
        SELECT player_name
        FROM match_players
        WHERE normalized_name = ?
        ORDER BY id
        LIMIT 1
        """,
        (normalized_name,),
    ).fetchone()

    if target_player is None:
        connection.close()

        return {
            "player_name": player_name,
            "match_count": 0,
            "ally_count": 0,
            "opponent_count": 0,
            "allies": [],
            "opponents": [],
            "matches": [],
        }

    match_rows = connection.execute(
        """
        SELECT
            m.id,
            m.match_datetime,
            m.match_key,
            m.game_mode,
            target.team_number AS target_team
        FROM matches m
        INNER JOIN match_players target
            ON target.match_id = m.id
        WHERE target.normalized_name = ?
        ORDER BY m.match_datetime DESC
        """,
        (normalized_name,),
    ).fetchall()

    matches = []
    ally_counts = {}
    opponent_counts = {}

    for match_row in match_rows:
        player_rows = connection.execute(
            """
            SELECT
                player_name,
                normalized_name,
                pokemon_name,
                team_number,
                result
            FROM match_players
            WHERE match_id = ?
            ORDER BY
                CASE
                    WHEN team_number IS NULL THEN 3
                    ELSE team_number
                END,
                player_name
            """,
            (match_row["id"],),
        ).fetchall()

        players = []

        for player_row in player_rows:
            is_target = (
                player_row["normalized_name"] == normalized_name
            )

            relation = "unknown"

            if is_target:
                relation = "target"
            elif (
                match_row["target_team"] is not None
                and player_row["team_number"] is not None
            ):
                if (
                    player_row["team_number"]
                    == match_row["target_team"]
                ):
                    relation = "ally"
                else:
                    relation = "opponent"

            if not is_target:
                player_key = player_row["normalized_name"]

                if relation == "ally":
                    if player_key not in ally_counts:
                        ally_counts[player_key] = {
                            "player_name": player_row["player_name"],
                            "count": 0,
                        }

                    ally_counts[player_key]["count"] += 1

                elif relation == "opponent":
                    if player_key not in opponent_counts:
                        opponent_counts[player_key] = {
                            "player_name": player_row["player_name"],
                            "count": 0,
                        }

                    opponent_counts[player_key]["count"] += 1

            players.append(
                {
                    "player_name": player_row["player_name"],
                    "pokemon_name": player_row["pokemon_name"],
                    "team_number": player_row["team_number"],
                    "result": player_row["result"],
                    "relation": relation,
                    "is_target": is_target,
                }
            )

        matches.append(
            {
                "match_key": match_row["match_key"],
                "match_datetime": match_row["match_datetime"],
                "game_mode": match_row["game_mode"],
                "target_team": match_row["target_team"],
                "players": players,
            }
        )

    allies = sorted(
        ally_counts.values(),
        key=lambda item: (-item["count"], item["player_name"].casefold()),
    )

    opponents = sorted(
        opponent_counts.values(),
        key=lambda item: (-item["count"], item["player_name"].casefold()),
    )

    ally_count = sum(item["count"] for item in allies)
    opponent_count = sum(item["count"] for item in opponents)

    connection.close()

    return {
        "player_name": target_player["player_name"],
        "match_count": len(matches),
        "ally_count": ally_count,
        "opponent_count": opponent_count,
        "allies": allies,
        "opponents": opponents,
        "matches": matches,
    }
def search_cross_matches(player1, player2):
    player1 = normalize_player_name(player1)
    player2 = normalize_player_name(player2)

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT DISTINCT
            m.id,
            m.match_key,
            m.match_datetime,
            m.game_mode
        FROM matches m
        INNER JOIN match_players p1
            ON p1.match_id = m.id
        INNER JOIN match_players p2
            ON p2.match_id = m.id
        WHERE
            p1.normalized_name = ?
        AND
            p2.normalized_name = ?
        ORDER BY
            m.match_datetime DESC
        """,
        (
            player1,
            player2,
        ),
    ).fetchall()

    matches = []

    for row in rows:

        players = connection.execute(
            """
            SELECT
                player_name,
                normalized_name,
                pokemon_name,
                result,
                team_number
            FROM match_players
            WHERE match_id = ?
            ORDER BY team_number, player_name
            """,
            (row["id"],),
        ).fetchall()

        player_list = []

        for p in players:

            role = ""

            if p["normalized_name"] == player1:
                role = "player1"

            elif p["normalized_name"] == player2:
                role = "player2"

            player_list.append(
                {
                    "player_name": p["player_name"],
                    "pokemon_name": p["pokemon_name"],
                    "team_number": p["team_number"],
                    "result": p["result"],
                    "role": role,
                }
            )

        matches.append(
            {
                "match_key": row["match_key"],
                "match_datetime": row["match_datetime"],
                "game_mode": row["game_mode"],
                "players": player_list,
            }
        )

    connection.close()

    return {
        "match_count": len(matches),
        "matches": matches,
    }
