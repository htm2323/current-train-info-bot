import json
import urllib.request
import datetime
import yaml
from TargetCompanyEnum import TargetCompany
import os

PARAMS_FILE = 'params.yaml'
SCHEDULE_DIR = 'schedule_json/'
STATION_INFO_DIR = 'station_json/'

class TrainCurrentInfoCrawler():
    def train_currentinfo_crawl(self, target):
        if target == TargetCompany.JRwest:
            with open(PARAMS_FILE, encoding='utf8') as params_file:
                params = yaml.safe_load(params_file)
                self.request_line = params['traininfo']['jr-west']['request_line']
                self.request_line_en = params['traininfo']['jr-west']['request_line_en']
                self.request_station = params['traininfo']['jr-west']['request_station']
                self.request_station_en = params['traininfo']['jr-west']['request_station_en']
                self.jr_api_url = params['traininfo']['jr-west']['api_url']
            
            self.crawl_currentinfo_jr_west()

        elif target == TargetCompany.Hankyu:
            print('hankyu is under constructing')

            with open(PARAMS_FILE, encoding='utf8') as params_file:
                params = yaml.safe_load(params_file)
        
        else:
            print('not support')

    def crawl_currentinfo_jr_west(self):
        url = self.jr_api_url + self.request_line_en + '.json'
        station_info_path = STATION_INFO_DIR + 'jrwest_' + self.request_line_en + '.json'
        traffic_info_url = self.jr_api_url + 'area_kinki_trafficinfo.json'

        if os.path.isfile(station_info_path) is False:
            list_station = self.crawl_jrwest_station_info(station_info_path)
        else:
            with open(station_info_path) as f:
                list_station = json.load(f)['table']

        request_station_id = [item['id'] for item in list_station if item['name'] == self.request_station][0]

        responce = urllib.request.urlopen(url)
        data = json.loads(responce.read().decode('utf-8'))

        res_traffic_info = urllib.request.urlopen(traffic_info_url)
        traffic_data = json.loads(res_traffic_info.read().decode('utf-8'))

        traffic_result = None
        for line in traffic_data['lines']:
            if line == self.request_line_en:
                traffic_result = self.request_line + ' ' + traffic_data['lines'][line]['section']['from'] + ' から ' + traffic_data['lines'][line]['section']['to'] + ' まで ' + traffic_data['lines'][line]['cause'] + ' のため ' + traffic_data['lines'][line]['status']
        
        if traffic_result == None:
            traffic_result = self.request_line + '線 ' + '遅延はありません'
        print(traffic_result)

        list_near_train = []

        for train in data['trains']:
            between = train['pos'].split('_')
            for st in between:
                if st == request_station_id and (train['type'] == '10' or train['type'] == '08'):
                    list_near_train.append(train)

        result = None

        for train in list_near_train:
            train_type = train['displayType']
            train_dist = train['dest']['text']
            train_id = train['no']
            between = train['pos'].split('_')
            st_deperture_time = ''

            if train['direction'] == '0':
                schedule_path = SCHEDULE_DIR + 'jrwest_' + self.request_line_en + '_' + self.request_station_en + '_upward.json'
                with open(schedule_path) as f:
                    schedule = json.load(f)
                    for hour_data in schedule['table']:
                        if hour_data['hour'] == str(datetime.datetime.now().hour):
                            for train_data in hour_data['trains']:
                                # print('matching %s with %s' % (train_data['id'], train_id))
                                if train_data['id'] == train_id:
                                    # print('found')
                                    st_deperture_time = str(hour_data['hour']) + ':' + str(train_data['minute']) + '発 '
                                    break
                            break

                if between[1] == '####':
                    pos = self.request_station + 'に停車中'
                else:
                    from_st = self.search_station_name(list_station, between[0])
                    to_st = self.search_station_name(list_station, between[1])
                    pos = from_st + 'から' + to_st + 'に向かって走行中'
            else:
                schedule_path = SCHEDULE_DIR + 'jrwest_' + self.request_line_en + '_' + self.request_station_en + '_downward.json'
                with open(schedule_path) as f:
                    schedule = json.load(f)
                    for hour_data in schedule['table']:
                        if hour_data['hour'] == str(datetime.datetime.now().hour):
                            for train_data in hour_data['trains']:
                                # print('matching %s with %s' % (train_data['id'], train_id))
                                if train_data['id'] == train_id:
                                    # print('found')
                                    st_deperture_time = str(hour_data['hour']) + ':' + str(train_data['minute']) + '発 '
                                    break
                            break

                if between[1] == '####':
                    pos = self.request_station + 'に停車中'
                else:
                    from_st = self.search_station_name(list_station, between[0])
                    to_st = self.search_station_name(list_station, between[1])
                    pos = from_st + 'から' + to_st + 'に向かって走行中'

            if train['delayMinutes'] != 0:
                train_delay = train['delayMinutes']
                result = st_deperture_time + train_type + ' ' + train_dist + '行きが' + str(train_delay) + '分遅れで' + pos
            else:
                result = st_deperture_time + train_type + ' ' + train_dist + '行きが' + pos


            print(result)

        if result is None:
            print('☆ 本日の営業は終了しました☆')


    def crawl_jrwest_station_info(self, output_path):
        url_stationinfo = self.jr_api_url + self.request_line_en + '_st.json'
        responce_stationinfo = urllib.request.urlopen(url_stationinfo)
        data_station = json.loads(responce_stationinfo.read().decode('utf-8'))

        list_station = []

        for st in data_station['stations']:
            station = {'id': st['info']['code'], 'name': st['info']['name']}
            list_station.append(station)

        table = {'update': datetime.datetime.now().isoformat(), 'table': list_station}

        with open(output_path, 'w') as f:
            json.dump(table, f)

        return list_station
    
    def search_station_name(self, list_station, id):
        return [item['name'] for item in list_station if item['id'] == id][0]