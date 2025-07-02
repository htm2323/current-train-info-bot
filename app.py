import threading
import time
import logging
from flask import Flask, request, render_template, make_response
from TrainCurrentInfoCrawler import TrainCurrentInfoCrawler
from TargetCompanyEnum import TargetCompany

app = Flask(__name__, template_folder='.')

# ログ設定
logger = logging.getLogger("train_logger")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('train_info.log', 'w', 'utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# JR西日本の列車情報を非同期に取得
def crawl_loop():
    # グローバル変数でキャッシュする
    global line_name_str, status_str, upward_train, downward_train
    crawler = TrainCurrentInfoCrawler()
    while True:
        try:
            line_name_str, status_str, upward_train, downward_train = crawler.train_currentinfo_crawl(TargetCompany.JRwest)
            # 運行情報をログファイルに出力
            logger.info(
                f"{line_name_str} の状態 : {status_str}"
            )
            logger.info(
                f"取得した上り: {upward_train}"
            )
            logger.info(
                f"取得した下り: {downward_train}"
            )
        except Exception as e:
            logger.error(f"クロール中にエラー: {e}")
        time.sleep(30)

@app.route('/')
def index():
    # 結果をHTMLに渡す
    response = make_response(render_template(
                                'index.html',
                                line_name=line_name_str, 
                                status=status_str, 
                                upward_train=upward_train, 
                                downward_train=downward_train))
    logger.info(f"{request.remote_addr} からアクセス: {request.method} {request.path} | 応答: {response.status_code}")
    return response

if __name__ == '__main__':
    # バックグラウンドでクロール開始
    threading.Thread(target=crawl_loop, daemon=True).start()
    app.run(debug=True)