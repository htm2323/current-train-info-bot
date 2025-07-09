# 現在の運行情報お知らせbot
最寄り駅まで行って **電車が出んしゃ！** となることを防ぐためのWebサービスです．

## 概要

- 電車の運行情報を取得し、最寄り駅に接近中の電車をWeb UIで案内します．
    - 現状はJR西日本管内に対応しています．(JR京都線で動作確認しました．)
    - 阪急は対応予定です．
- 上り・下りそれぞれ直近3本の電車について，発車時刻・種別・行先・遅延・到着までの目安時間や「間に合う/間に合わない」などを表示します．
- ページは30秒ごとに自動更新され，リアルタイムの運行情報が確認できます．

## 要件
- Ubuntu
- Python3
- flask
- beautifulsoup

## 使用方法
1. **依存パッケージのインストール**
   ```bash
   pip install flask pyyaml beautifulsoup4 tqdm
   ```
   またはuvでの設定も可能です．
   ```bash
   uv sync
   ```

3. **設定**
- params.yaml に情報を取得したい路線名，最寄り駅名，時刻表のURLなど）を記入してください。JR京都線 高槻駅の場合は以下のとおりです．
    ```
    request_line: '京都'
    request_line_en: 'kyoto'
    request_station: '高槻'
    request_station_en: 'takatsuki'
    schedule_url: ['JRおでかけネット上の駅時刻表URL(上り)', 'JRおでかけネット上の駅時刻表URL(下り)']
    danger_minutes: 5  #「間に合わない」表示に切り替わる時間(分)
    warning_minutes: 10  #「走れば間に合う」表示に切り替える時間(分)
    ```

3. **時刻表データの取得**
- `setup_app.py` を実行して，最寄り駅の時刻表データを取得して`schedule_json/`以下に格納します．
    ```
    python setup_app.py

    # uvの場合
    uv run setup_app.py
    ```

4. **Webアプリの起動**
    ```
    python app.py

    # uvの場合
    uv run app.py
    ```
- 実行後，ブラウザで `http://localhost:5000` にアクセスしてください。

## 実装予定
- slackのbotとしてリクエストを受けたらお知らせする機能
- 阪急の運行情報を取得してお知らせできるようにする
