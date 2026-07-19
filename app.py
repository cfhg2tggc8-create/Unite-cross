from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return """
    <h1>UNITE Match Cross Finder</h1>
    <p>アプリの初期化に成功しました。</p>
    <p>ここから検索画面を作成していきます。</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
