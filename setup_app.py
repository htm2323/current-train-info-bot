import TrainScheduleCrawler
from TargetCompanyEnum import TargetCompany

crawler = TrainScheduleCrawler.TrainScheduleCrawler()
crawler.trainschedule_crawl(TargetCompany.JRwest)