import urllib.request
import json
from bs4 import BeautifulSoup
import time
import datetime
from tqdm import tqdm
import yaml
from TargetCompanyEnum import TargetCompany

PARAMS_FILE = 'params.yaml'
OUTPUT_DIR = 'schedule_json/'

class TrainScheduleCrawler():
    def trainschedule_crawl(self, target):
        if target == TargetCompany.JRwest:
            print('Crawling jr-west schedule...')

            # setup parameters
            with open(PARAMS_FILE, encoding='utf8') as params_file:
                params = yaml.safe_load(params_file)
                self.request_line_en = params['traininfo']['jr-west']['request_line_en']
                self.request_station_en = params['traininfo']['jr-west']['request_station_en']
                self.schedule_urls = params['traininfo']['jr-west']['schedule_url']

                # then start crawling
                self.crawl_schedule_jr_west()

        elif target == TargetCompany.Hankyu:
            print('hankyu is under constructing')

            # setup parameters
            with open(PARAMS_FILE, encoding='utf8') as params_file:
                params = yaml.safe_load(params_file)
                self.schedule_urls = params['traininfo']['hankyu']['schedule_url']

                # then start crawling
                self.crawl_schedule_hankyu()

        else:
            print('not support')

    # Crawling train schedule of JR west
    def crawl_schedule_jr_west(self):
        is_upward = True

        for url in self.schedule_urls:
            # prepare base url before using each train information
            base_url = url.split('/station')[0]

            # request schedule page's html
            print('GET: {}'.format(str(url)))
            res = urllib.request.urlopen(url)
            data = res.read().decode('utf-8')

            # get schedule table from html
            soup = BeautifulSoup(data, 'html.parser')
            timetable = soup.find('div', attrs={'class' : 'pc-time-tbl-wrap'}).find('table')

            # get information on each hour, then put it to list
            list_trains = []
            idx = 0
            for row in tqdm(timetable.findAll('tr')):
                # skip first row because first row is description of each column
                if idx == 0:
                    idx += 1
                    continue
                else:
                    hour_trains = []
                    cell = row.findAll(['td'])

                    # get information of each train
                    for train in cell[1].findAll('div', attrs={'class': 'minute-item'}):
                        minute = train.find('span', attrs={'class': 'minute'}).get_text()

                        # get train type, but this text is one or two charactor
                        # so assign full text of train type by myself
                        type = train.find('span', attrs={'class': 'train-type'}).get_text()
                        train_type = ''

                        if type == '':
                            train_type = '普通'
                        elif type[0] == '快':
                            train_type = '快速'
                        elif type[0] == '新':
                            train_type = '新快速'
                        elif type[0] == '特':
                            train_type = '特急'

                        detail_link = train.find('a').get('href')

                        if detail_link.find('train-timetable') != -1:
                            detail_link = base_url + detail_link.split('?')[0]

                            # print('GET: {}'.format(str(detail_link)))
                            res_traininfo = urllib.request.urlopen(detail_link)
                            data = res_traininfo.read().decode('utf-8')

                            soup_train = BeautifulSoup(data, 'html.parser')

                            infos = soup_train.findAll('tbody', attrs={'class': 'train-details'})[0]
                            # get train id, train type, destination
                            train_id = infos.findAll('tr')[0].find('td').get_text()
                            # train_type = infos.findAll('tr')[1].find('td').get_text()
                            print('%s:%s train_type: %s, dest: %s' % (cell[0].get_text(), minute, train_type, soup_train.find('div', attrs={'class': 'route-name'}).get_text()))
                            train_destination = soup_train.find('div', attrs={'class': 'route-name'}).get_text().split('　')[1].split('行')[0]

                        train_info = {'minute': minute, 'id': train_id, 'type': train_type, 'destination': train_destination, 'detail_link': detail_link}
                        hour_trains.append(train_info)
                        
                        # avoid DDoS attack
                        time.sleep(1)
                    
                    idx += 1
                    hour_info = {'hour': cell[0].get_text(), 'trains': hour_trains}
                    list_trains.append(hour_info)
            
            # create table of all train's information
            table = {'update': datetime.datetime.now().isoformat(), 'table': list_trains}
            # print(table)

            # save table as json file
            if is_upward:
                filepath  = OUTPUT_DIR + 'jrwest_' + self.request_line_en + '_' + self.request_station_en + '_upward.json'

                with open(filepath, 'w') as f:
                    json.dump(table, f)

                print('crawl upward schedule complete!')
                is_upward = False
            else:
                filepath  = OUTPUT_DIR + 'jrwest_' + self.request_line_en + '_' + self.request_station_en + '_downward.json'

                with open(filepath, 'w') as f:
                    json.dump(table, f)
                
                print('crawl downward schedule complete!')

    def crawl_schedule_hankyu(self):
        is_upward = True
        # under constructing

