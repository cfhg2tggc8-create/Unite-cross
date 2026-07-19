from flask import Flask, redirect, render_template, request, url_for

from database import get_database_counts, initialize_database
from json_importer import JsonImportError, import_json_file


app = Flask(__name__)

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
    counts = get_database_counts()

    message = request.args.get("message", "").strip()
    error = request.args.get("error", "").strip()

    return render_template(
        "data.html",
        match_count=counts["match_count"],
        player_count=counts["player_count"],
        message=message,
        error=error,
    )


@app.route("/data/import-json", methods=["POST"])
def import_json():
    json_file = request.files.get("json_file")

    try:
        result = import_json_file(json_file)

        message = (
            f'{result["inserted_matches"]}試合を登録しました。'
            f'{result["inserted_players"]}件の参加者データを保存しました。'
        )

        if result["skipped_matches"]:
            message += (
                f' 重複していた{result["skipped_matches"]}試合は'
                "登録を省略しました。"
            )

        return redirect(
            url_for(
                "data",
                message=message,
            )
        )

    except JsonImportError as exc:
        return redirect(
            url_for(
                "data",
                error=str(exc),
            )
        )

    except Exception:
        app.logger.exception("JSON import failed")

        return redirect(
            url_for(
                "data",
                error="JSON取込中に予期しないエラーが発生しました。",
            )
        )


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
