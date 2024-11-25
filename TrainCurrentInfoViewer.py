import TrainCurrentInfoCrawler
from TargetCompanyEnum import TargetCompany
import time

crawler = TrainCurrentInfoCrawler.TrainCurrentInfoCrawler()

while True:
    crawler.train_currentinfo_crawl(TargetCompany.JRwest)
    time.sleep(30)