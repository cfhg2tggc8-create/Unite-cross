import os
import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)

DATABASE_PATH = os.environ.get("DATABASE_PATH", "unite_cross.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
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
            FOREIGN KEY (match_id) REFERENCES matches (id)
        );

        CREATE INDEX IF NOT EXISTS idx_match_datetime
        ON matches (match_datetime);

        CREATE INDEX IF NOT EXISTS idx_player_name
        ON match_players (player_name);
        """
    )

    connection.commit()
    connection.close()


initialize_database()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    player = request.args.get("player", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    relation = request.args.get("relation", "all").strip()

    if relation not in {"all", "ally", "opponent"}:
        relation = "all"

    return render_template(
        "search.html",
        player=player,
        start_date=start_date,
        end_date=end_date,
        relation=relation,
        searched=bool(player),
    )


@app.route("/data")
def data():
    connection = get_db_connection()

    match_count = connection.execute(
        "SELECT COUNT(*) AS count FROM matches"
    ).fetchone()["count"]

    player_count = connection.execute(
        "SELECT COUNT(*) AS count FROM match_players"
    ).fetchone()["count"]

    connection.close()

    return f"""
    <h1>データ管理</h1>
    <p>保存済み試合数：{match_count}</p>
    <p>保存済み参加者レコード数：{player_count}</p>
    <p>CSV・JSON取込機能は次の工程で追加します。</p>
    <p><a href="/">トップへ戻る</a></p>
    """


@app.route("/sources")
def sources():
    return """
    <h1>UniteAPI取得元</h1>
    <p>この機能は準備中です。</p>
    <p><a href="/">トップへ戻る</a></p>
    """


@app.route("/statistics")
def statistics():
    return """
    <h1>統計</h1>
    <p>この機能は準備中です。</p>
    <p><a href="/">トップへ戻る</a></p>
    """


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
