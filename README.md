# 現在の運行情報お知らせbot
最寄り駅まで行って **電車が出んしゃ！** となることを防ぐためのbot(開発中)

## 現状
`params.yaml`に各種情報と情報取得先のurlを書き込む必要があります  
JR京都線での動作を確認
- JRの時刻表を取得して保存できる
- JR(東海道線)の運行情報を取得して，最寄り駅に接近中の電車についてコンソールでお知らせできる

## 実装予定
- 最寄り駅に次に来る電車3本程度について現在位置をお知らせできる機能
- 最寄り駅までの移動時間を加味して間に合うかどうかをお知らせできる機能
- slackのbotとしてリクエストを受けたらお知らせする機能
- web UI
- 阪急の運行情報を取得してお知らせできるようにする
- JR他路線についても情報を取得できるようにする
