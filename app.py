from flask import Flask, render_template
from TrainCurrentInfoCrawler import TrainCurrentInfoCrawler
from TargetCompanyEnum import TargetCompany

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    crawler = TrainCurrentInfoCrawler()
    # JR西日本の列車情報を取得
    line_name_str, status_str, upward_train, downward_train = crawler.train_currentinfo_crawl(TargetCompany.JRwest)
    print(line_name_str, status_str, upward_train, downward_train)
    # 結果をHTMLに渡す
    return render_template('index.html',
                           line_name=line_name_str, 
                           status=status_str, 
                           upward_train=upward_train, 
                           downward_train=downward_train)

if __name__ == '__main__':
    app.run(debug=True)