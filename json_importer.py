import json
from datetime import datetime

from database import get_db_connection, normalize_player_name


class JsonImportError(Exception):
    pass


def _validate_datetime(value):
    if not isinstance(value, str) or not value.strip():
        raise JsonImportError("match_datetime が未入力です。")

    text = value.strip()

    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise JsonImportError(
            f"match_datetime の形式が不正です: {text}"
        ) from exc

    return text


def _validate_team_number(value):
    if value is None or value == "":
        return None

    try:
        team_number = int(value)
    except (TypeError, ValueError) as exc:
        raise JsonImportError(
            f"team は整数で指定してください: {value}"
        ) from exc

    if team_number not in {1, 2}:
        raise JsonImportError(
            f"team は1または2で指定してください: {team_number}"
        )

    return team_number


def _validate_result(value):
    if value is None or value == "":
        return None

    result = str(value).strip().lower()

    if result not in {"win", "lose", "draw", "unknown"}:
        raise JsonImportError(
            "result は win / lose / draw / unknown のいずれかです。"
        )

    return result


def _normalize_match(raw_match):
    if not isinstance(raw_match, dict):
        raise JsonImportError("各試合データはJSONオブジェクトで指定してください。")

    match_key = str(raw_match.get("match_key", "")).strip()

    if not match_key:
        raise JsonImportError("match_key が未入力です。")

    match_datetime = _validate_datetime(
        raw_match.get("match_datetime")
    )

    game_mode = str(raw_match.get("game_mode", "")).strip() or None
    source_player = (
        str(raw_match.get("source_player", "")).strip() or None
    )
    source_type = (
        str(raw_match.get("source_type", "json")).strip() or "json"
    )
    source_url = (
        str(raw_match.get("source_url", "")).strip() or None
    )

    raw_players = raw_match.get("players")

    if not isinstance(raw_players, list) or not raw_players:
        raise JsonImportError(
            f"{match_key}: players は1件以上必要です。"
        )

    players = []
    seen_names = set()

    for raw_player in raw_players:
        if not isinstance(raw_player, dict):
            raise JsonImportError(
                f"{match_key}: players 内の形式が不正です。"
            )

        player_name = str(raw_player.get("name", "")).strip()

        if not player_name:
            raise JsonImportError(
                f"{match_key}: プレイヤー名が未入力です。"
            )

        normalized_name = normalize_player_name(player_name)

        if normalized_name in seen_names:
            raise JsonImportError(
                f"{match_key}: 同じプレイヤーが重複しています: "
                f"{player_name}"
            )

        seen_names.add(normalized_name)

        pokemon_name = (
            str(raw_player.get("pokemon", "")).strip() or None
        )

        players.append(
            {
                "player_name": player_name,
                "normalized_name": normalized_name,
                "team_number": _validate_team_number(
                    raw_player.get("team")
                ),
                "pokemon_name": pokemon_name,
                "result": _validate_result(
                    raw_player.get("result")
                ),
            }
        )

    return {
        "match_key": match_key,
        "match_datetime": match_datetime,
        "game_mode": game_mode,
        "source_player": source_player,
        "source_type": source_type,
        "source_url": source_url,
        "players": players,
    }


def _load_matches(file_storage):
    if file_storage is None or not file_storage.filename:
        raise JsonImportError("JSONファイルを選択してください。")

    try:
        raw_data = json.load(file_storage.stream)
    except UnicodeDecodeError as exc:
        raise JsonImportError(
            "JSONファイルはUTF-8で保存してください。"
        ) from exc
    except json.JSONDecodeError as exc:
        raise JsonImportError(
            f"JSONの形式が不正です。{exc.msg}"
        ) from exc

    if isinstance(raw_data, dict):
        raw_matches = raw_data.get("matches")

        if raw_matches is None:
            raw_matches = [raw_data]
    elif isinstance(raw_data, list):
        raw_matches = raw_data
    else:
        raise JsonImportError(
            "JSONの最上位は配列、またはmatchesを含むオブジェクトにしてください。"
        )

    if not raw_matches:
        raise JsonImportError("JSON内に試合データがありません。")

    return [_normalize_match(item) for item in raw_matches]


def import_json_file(file_storage):
    matches = _load_matches(file_storage)

    connection = get_db_connection()
    inserted_matches = 0
    skipped_matches = 0
    inserted_players = 0

    try:
        for match in matches:
            existing = connection.execute(
                """
                SELECT id
                FROM matches
                WHERE match_key = ?
                """,
                (match["match_key"],),
            ).fetchone()

            if existing:
                skipped_matches += 1
                continue

            cursor = connection.execute(
                """
                INSERT INTO matches (
                    match_key,
                    match_datetime,
                    game_mode,
                    source_player,
                    source_type,
                    source_url
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    match["match_key"],
                    match["match_datetime"],
                    match["game_mode"],
                    match["source_player"],
                    match["source_type"],
                    match["source_url"],
                ),
            )

            match_id = cursor.lastrowid

            for player in match["players"]:
                connection.execute(
                    """
                    INSERT INTO match_players (
                        match_id,
                        player_name,
                        normalized_name,
                        team_number,
                        pokemon_name,
                        result
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        match_id,
                        player["player_name"],
                        player["normalized_name"],
                        player["team_number"],
                        player["pokemon_name"],
                        player["result"],
                    ),
                )
                inserted_players += 1

            inserted_matches += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return {
        "inserted_matches": inserted_matches,
        "skipped_matches": skipped_matches,
        "inserted_players": inserted_players,
    }
