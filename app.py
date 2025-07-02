import threading
import time
import datetime
from flask import Flask, render_template
from TrainCurrentInfoCrawler import TrainCurrentInfoCrawler
from TargetCompanyEnum import TargetCompany

app = Flask(__name__, template_folder='.')


# JR西日本の列車情報を非同期に取得
def crawl_loop():
    # グローバル変数でキャッシュする
    global line_name_str, status_str, upward_train, downward_train
    crawler = TrainCurrentInfoCrawler()
    while True:
        try:
            line_name_str, status_str, upward_train, downward_train = crawler.train_currentinfo_crawl(TargetCompany.JRwest)
            print(line_name_str, status_str, upward_train, downward_train)
            print("%s  情報を更新しました" % datetime.datetime.now())
        except Exception as e:
            print("クロール中にエラー:", e)
        time.sleep(30)

@app.route('/')
def index():
    # 結果をHTMLに渡す
    return render_template('index.html',
                           line_name=line_name_str, 
                           status=status_str, 
                           upward_train=upward_train, 
                           downward_train=downward_train)

if __name__ == '__main__':
    # バックグラウンドでクロール開始
    threading.Thread(target=crawl_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)