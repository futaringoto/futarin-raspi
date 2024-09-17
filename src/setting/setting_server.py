from flask import Flask, render_template, request
from src.log.logger import get_logger
import src.setting.wifi as wifi

logger = get_logger("SettingServer")

app = Flask(
    __name__,
    template_folder="./flask-src/template/",
    static_folder="./flask-src/static/",
)


@app.route("/")
@app.route("/setting/", methods=["GET"])
def setting_html():
    return render_template("setting.html")


@app.route("/api/setting", methods=["POST"])
def save_setting():
    wifi_ssid = request.form["wifiSsid"]
    wifi_pw = request.form["wifiPassword"]
    wifi.save(wifi_ssid, wifi_pw)
    return "", 200


def run():
    app.run(port=8000, debug=True)


if __name__ == "__main__":
    run()
