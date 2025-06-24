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
            
            return self.crawl_currentinfo_jr_west()

        elif target == TargetCompany.Hankyu:
            print('hankyu is under constructing')

            with open(PARAMS_FILE, encoding='utf8') as params_file:
                params = yaml.safe_load(params_file)
        
        else:
            print('not support')

    def crawl_currentinfo_jr_west(self):
        self.schedule = self.load_jrwest_schedule()

        url = self.jr_api_url + self.request_line_en + '.json'
        station_info_path = STATION_INFO_DIR + 'jrwest_' + self.request_line_en + '.json'
        
        if os.path.isfile(station_info_path) is False:
            list_station = self.crawl_jrwest_station_info(station_info_path)
        else:
            with open(station_info_path) as f:
                list_station = json.load(f)['table']

        self.request_station_id = [item['id'] for item in list_station if item['name'] == self.request_station][0]

        responce = urllib.request.urlopen(url)
        data = json.loads(responce.read().decode('utf-8'))

        return self.crawl_current_trafficinfo_jr_west() + self.crawl_current_next_traininfo_jr_west(data, list_station)

    def crawl_current_next_traininfo_jr_west(self, data, list_station):
        def is_up_direction(train):
            if train['direction'] == 0:
                return True
            else:
                return False
            
        def is_exist_in_schedule(train):
            for schedule in self.schedule:
                for hour_data in schedule:
                    for train_data in hour_data['trains']:
                        if train_data['id'] == train['no']:
                            return True
            return False
            
        def is_past_train(train, schedule):
            for hour_data in schedule:
                for train_data in hour_data['trains']:
                    if train_data['id'] == train['no']:
                        if int(hour_data['hour']) < datetime.datetime.now().hour or \
                           (int(hour_data['hour']) == datetime.datetime.now().hour and int(train_data['minute']) < datetime.datetime.now().minute):
                            return True
            return False
        
        def is_in_line(train):
            try:
                get_station_list_idx(train['pos'].split('_')[0])
                return True
            except IndexError:
                return False
            
        def is_behind_train(base_pos, compared_pos, is_upward):
            if is_upward:
                return True if get_station_list_idx(base_pos) < get_station_list_idx(compared_pos) else False
            else:
                return True if get_station_list_idx(base_pos) > get_station_list_idx(compared_pos) else False
        
        def get_station_list_idx(station_id):
            return [i for i in range(len(list_station)) if list_station[i]['id'] == station_id][0]

        def get_train_deperture_time(train_id, schedule):
            result = {'hour': None, 'minute': None}
            for hour_data in schedule:
                for train_data in hour_data['trains']:
                    if train_data['id'] == train_id:
                        result['hour'] = str(hour_data['hour'])
                        result['minute'] = str(train_data['minute'])
                        break
            return result
        
        def remain_time_until_deperture(train, hour, minute):
            if int(hour) < datetime.datetime.now().hour:
                departure_time = datetime.datetime.now().replace(day=int(datetime.datetime.now().day + 1), hour=int(hour), minute=int(minute), second=0, microsecond=0)
            else:
                departure_time = datetime.datetime.now().replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            return round((departure_time - datetime.datetime.now()).total_seconds() / 60) + int(train['delayMinutes'])

        upward_train = []
        downward_train = []

        for train in data['trains']:
            if is_in_line(train) and is_exist_in_schedule(train):
                if is_behind_train(self.request_station_id, train['pos'].split('_')[0], is_up_direction(train)):
                    if is_up_direction(train):
                        if len(upward_train) < 3:
                            upward_train.append(train)
                        else:
                            for i in range(len(upward_train)):
                                if not is_behind_train(upward_train[i]['pos'].split('_')[0], train['pos'].split('_')[0], True):
                                    upward_train[i] = train
                                    break
                    else:
                        if len(downward_train) < 3:
                            downward_train.append(train)
                        else:
                            for i in range(len(downward_train)):
                                if not is_behind_train(downward_train[i]['pos'].split('_')[0], train['pos'].split('_')[0], False):
                                    downward_train[i] = train
                                    break

        # print(upward_train)
        # print(downward_train)

        if len(upward_train) == 0 and len(downward_train) == 0:
            print('☆ 本日の営業は終了しました☆')
            return
        
        downward_train.reverse()
        
        # result = '    上り\n'
        result = '    上り<p>'

        for train in upward_train:
            train_type = train['displayType']
            train_dist = train['dest']['text']
            train_id = train['no']
            between = train['pos'].split('_')

            # print(train_id)

            deperture_time = get_train_deperture_time(train_id, self.schedule[0])
            hour = ('0' + deperture_time['hour']) if len(deperture_time['hour']) == 1 else deperture_time['hour']
            minute = ('0' + deperture_time['minute']) if len(deperture_time['minute']) == 1 else deperture_time['minute']
            st_deperture_time = hour + ':' + minute + '発 '

            # print(st_deperture_time)
            
            if between[1] == '####':
                pos = self.search_station_name(list_station, between[0]) + ' に停車中'
            else:
                from_st = self.search_station_name(list_station, between[1])
                to_st = self.search_station_name(list_station, between[0])
                pos = from_st + ' から ' + to_st + ' に向かって走行中'

            if train['delayMinutes'] != 0:
                train_delay = train['delayMinutes']
                res_train = st_deperture_time + train_type + ' ' + train_dist + '行きが ' + str(train_delay) + ' 分遅れで ' + pos
            else:
                res_train = st_deperture_time + train_type + ' ' + train_dist + '行きが ' + pos

            # result += res_train + '  到着まであと ' + str(remain_time_until_deperture(train, hour, minute)) + ' 分\n'
            result += res_train + '  到着まであと ' + str(remain_time_until_deperture(train, hour, minute)) + ' 分<br>'

        # result += '-----\n    下り\n'
        result += '-----<br>    下り<p>'

        for train in downward_train:
            train_type = train['displayType']
            train_dist = train['dest']['text']
            train_id = train['no']
            between = train['pos'].split('_')
        
            # print(train_id)

            deperture_time = get_train_deperture_time(train_id, self.schedule[1])
            hour = ('0' + deperture_time['hour']) if len(deperture_time['hour']) == 1 else deperture_time['hour']
            minute = ('0' + deperture_time['minute']) if len(deperture_time['minute']) == 1 else deperture_time['minute']
            st_deperture_time = hour + ':' + minute + '発 '
            
            # print(st_deperture_time)
            
            if between[1] == '####':
                pos = self.search_station_name(list_station, between[0]) + ' に停車中'
            else:
                from_st = self.search_station_name(list_station, between[0])
                to_st = self.search_station_name(list_station, between[1])
                pos = from_st + ' から ' + to_st + ' に向かって走行中'

            if train['delayMinutes'] != 0:
                train_delay = train['delayMinutes']
                res_train = st_deperture_time + train_type + ' ' + train_dist + '行きが ' + str(train_delay) + ' 分遅れで ' + pos
            else:
                res_train = st_deperture_time + train_type + ' ' + train_dist + '行きが ' + pos

            # result += res_train + '  到着まであと ' + str(remain_time_until_deperture(train, hour, minute)) + ' 分\n'
            result += res_train + '  到着まであと ' + str(remain_time_until_deperture(train, hour, minute)) + ' 分<br>'
            
        # print(result)              
        return result

    def crawl_current_trafficinfo_jr_west(self):
        traffic_info_url = self.jr_api_url + 'area_kinki_trafficinfo.json'
        res_traffic_info = urllib.request.urlopen(traffic_info_url)
        traffic_data = json.loads(res_traffic_info.read().decode('utf-8'))

        traffic_result = None
        for line in traffic_data['lines']:
            if line == self.request_line_en:
                traffic_result = self.request_line + '線 ' + traffic_data['lines'][line]['section']['from'] + ' から ' + traffic_data['lines'][line]['section']['to'] + ' まで ' + traffic_data['lines'][line]['cause'] + ' のため ' + traffic_data['lines'][line]['status'] + '<br>'
        
        if traffic_result == None:
            traffic_result = self.request_line + '線 ' + '遅延はありません'
        # print(traffic_result)
        return traffic_result + '<p>'

    def load_jrwest_schedule(self):
        upward_schedule_path = SCHEDULE_DIR + 'jrwest_' + self.request_line_en + '_' + self.request_station_en + '_upward.json'
        downward_schedule_path = SCHEDULE_DIR + 'jrwest_' + self.request_line_en + '_' + self.request_station_en + '_downward.json'
        schedule = []

        for schedule_path in [upward_schedule_path, downward_schedule_path]:
            with open(schedule_path) as f:
                schedule.append(json.load(f)['table'])

        return schedule

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
        try:
            result = [item['name'] for item in list_station if item['id'] == id][0]
        except:
            result = '不明'

        return result