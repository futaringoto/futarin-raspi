from flask import Flask, render_template
from src.log.logger import get_logger

logger = get_logger("SettingServer")

app = Flask(__name__, template_folder="./template/")


@app.route("/")
def setting():
    return render_template("setting.html")


def run():
    app.run(port=8000, debug=True)


if __name__ == "__main__":
    run()
