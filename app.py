from flask import Flask, render_template
from TrainCurrentInfoCrawler import TrainCurrentInfoCrawler
from TargetCompanyEnum import TargetCompany

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    crawler = TrainCurrentInfoCrawler()
    # JR西日本の列車情報を取得
    result_string = crawler.train_currentinfo_crawl(TargetCompany.JRwest)
    # 結果をHTMLに渡す
    return render_template('index.html', result=result_string)

if __name__ == '__main__':
    app.run(debug=True)