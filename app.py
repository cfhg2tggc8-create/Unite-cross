from flask import Flask, render_template, request

from database import get_database_counts, initialize_database


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

    return render_template(
        "data.html",
        match_count=counts["match_count"],
        player_count=counts["player_count"],
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
