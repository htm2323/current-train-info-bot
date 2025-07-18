import threading
import time
import datetime
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml
from flask import Flask, request, render_template, make_response
from TrainCurrentInfoCrawler import TrainCurrentInfoCrawler
from TargetCompanyEnum import TargetCompany

app = Flask(__name__, template_folder='.')

# logフォルダが存在しない場合は作成
os.makedirs('log', exist_ok=True)

# ログ設定: 毎日3時にローテーション, 最大7日分のログを保持
logger = logging.getLogger("train_logger")
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(
    'log/train_info.log',
    when='midnight',
    interval=1,
    atTime=datetime.time(3, 0),
    backupCount=7,
    encoding='utf-8'
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# params.yamlを読み込み
with open('params.yaml', 'r', encoding='utf-8') as f:
    params = yaml.safe_load(f)
DANGER_MINUTES = params['traininfo']['jr-west']['danger_minutes']
WARNING_MINUTES = params['traininfo']['jr-west']['warning_minutes']

crawler = TrainCurrentInfoCrawler()

def is_service_time():
    """運行時間内かどうかを判定（4:00-26:00）"""
    now = datetime.datetime.now()
    hour = now.hour
    return (4 <= hour <= 23) or (0 <= hour < 2)

def crawl_loop():
    """JR西日本の列車情報を非同期に取得"""
    # グローバル変数でキャッシュする
    global line_name_str, status_str, upward_train, downward_train, last_update_time
    while True:
        if is_service_time():
            line_name_str, status_str, upward_train, downward_train = crawler.train_currentinfo_crawl(TargetCompany.JRwest)

            # 最終更新時間を更新
            last_update_time = datetime.datetime.now().strftime("%H:%M:%S")

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
            if len(upward_train) == 0:
                upward_train.append({'time': '', 'type': '', 'dest': '', 'pos': '', 'delay': '', 'remain_time': "☆ 本日の運行は終了しました ☆"})
            if len(downward_train) == 0:
                downward_train.append({'time': '', 'type': '', 'dest': '', 'pos': '', 'delay': '', 'remain_time': "☆ 本日の運行は終了しました ☆"})
            time.sleep(30)
        else:
            # サービス休止時間（2:00-4:59）
            line_name_str, status_str, upward_train, downward_train = crawler.train_currentinfo_crawl(TargetCompany.JRwest)

            # 最終更新時間を更新
            last_update_time = datetime.datetime.now().strftime("%H:%M:%S")

            # 一応取得した運行情報をログファイルに出力
            logger.info(
                f"{line_name_str} の状態 : {status_str}"
            )
            logger.info(
                f"取得した上り: {upward_train}"
            )
            logger.info(
                f"取得した下り: {downward_train}"
            )

            # サービス休止中のメッセージを設定
            status_str = "☆ 本日の運行は終了しました ☆"
            logger.info("サービス休止時間中")
            time.sleep(300)

@app.route('/')
def index():
    # 結果をHTMLに渡す
    response = make_response(render_template(
                                'index.html',
                                line_name=line_name_str, 
                                status=status_str, 
                                upward_train=upward_train, 
                                downward_train=downward_train,
                                danger_minutes=DANGER_MINUTES,
                                warning_minutes=WARNING_MINUTES,
                                last_update=last_update_time))
    logger.info(f"{request.remote_addr} からアクセス: {request.method} {request.path} | 応答: {response.status_code}")
    return response

if __name__ == '__main__':
    # バックグラウンドでクロール開始
    threading.Thread(target=crawl_loop, daemon=True).start()
    app.run(debug=True)
