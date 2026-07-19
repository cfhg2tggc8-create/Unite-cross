from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    return """
    <h1>クロス検索</h1>
    <p>この機能は次の工程で作成します。</p>
    <p><a href="/">トップへ戻る</a></p>
    """


@app.route("/data")
def data():
    return """
    <h1>データ管理</h1>
    <p>この機能は準備中です。</p>
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
