import json
import urllib.request
import datetime
import yaml
import logging
from TargetCompanyEnum import TargetCompany
import os

PARAMS_FILE = 'params.yaml'
SCHEDULE_DIR = 'schedule_json/'
STATION_INFO_DIR = 'station_json/'

logger = logging.getLogger("train_logger")

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
            logger.warning('hankyu is under constructing')

            with open(PARAMS_FILE, encoding='utf8') as params_file:
                params = yaml.safe_load(params_file)
        
        else:
            logger.warning('not support')

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

        try:
            responce = urllib.request.urlopen(url)
            data = json.loads(responce.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"JR西日本の列車走行位置へHTTPアクセス中にエラー: {e}")
            return None, None, [], []

        line_str, status_str = self.crawl_current_trafficinfo_jr_west()
        upward_train, downward_train = self.crawl_current_next_traininfo_jr_west(data, list_station)

        return line_str, status_str, upward_train, downward_train

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

        def get_train_type(train_id, schedule):
            for hour_data in schedule:
                for train_data in hour_data['trains']:
                    if train_data['id'] == train_id:
                        return str(train_data['type'])
            return '不明'
        
        def remain_time_until_deperture(train, hour, minute):
            if int(hour) < datetime.datetime.now().hour:
                departure_time = datetime.datetime.now().replace(day=int(datetime.datetime.now().day + 1), hour=int(hour), minute=int(minute), second=0, microsecond=0)
            else:
                departure_time = datetime.datetime.now().replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            return round((departure_time - datetime.datetime.now()).total_seconds() / 60) + int(train['delayMinutes'])

        upward_train = []
        downward_train = []

        for train in data['trains']:
            debug_between = train['pos'].split('_')
            if debug_between[1] == '####':
                debug_pos = self.search_station_name(list_station, debug_between[0])
            else:
                debug_from_st = self.search_station_name(list_station, debug_between[1])
                debug_to_st = self.search_station_name(list_station, debug_between[0])
                debug_pos = debug_from_st + ' ~ ' + debug_to_st

            # logger.debug(f"Train ID: {train['no']}, Type:{train['displayType']}, Dist:{train['dest']['text']}, Delay:{train['delayMinutes']} min, Pos: {debug_pos}, Is_In_Line: {is_in_line(train)}, Is_Exist_In_Schedule: {is_exist_in_schedule(train)}")
            
            if is_in_line(train) and is_exist_in_schedule(train):
                if is_up_direction(train):
                    debug_deperture_time = get_train_deperture_time(train['no'], self.schedule[0])
                else:
                    debug_deperture_time = get_train_deperture_time(train['no'], self.schedule[1])

                debug_remain_time = remain_time_until_deperture(train, debug_deperture_time['hour'], debug_deperture_time['minute'])
                logger.debug(f"Deperture: {debug_deperture_time['hour']}:{('0' + debug_deperture_time['minute']) if len(debug_deperture_time['minute']) == 1 else debug_deperture_time['minute']}, Type:{train['displayType']}, Dist:{train['dest']['text']}, Delay:{train['delayMinutes']} min, Pos: {debug_pos}, remain_time: {debug_remain_time} min")

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
            else:
                if is_exist_in_schedule(train):
                    if is_up_direction(train):
                        debug_deperture_time = get_train_deperture_time(train['no'], self.schedule[0])
                    else:
                        debug_deperture_time = get_train_deperture_time(train['no'], self.schedule[1])
                    logger.debug(f"Deperture: {debug_deperture_time['hour']}:{('0' + debug_deperture_time['minute']) if len(debug_deperture_time['minute']) == 1 else debug_deperture_time['minute']}, Train ID: {train['no']}, Type:{train['displayType']}, Dist:{train['dest']['text']}, Pos: {debug_pos}, Is_In_Line: {' 〇 ' if is_in_line(train) else ' × '}")
                logger.debug(f"Train ID: {train['no']}, Type:{train['displayType']}, Dist:{train['dest']['text']}, Pos: {debug_pos}, Is_In_Line: {' 〇 ' if is_in_line(train) else ' × '}, Is_Exist_In_Schedule: {' 〇 ' if is_exist_in_schedule(train) else ' × '}")

        result_upward_train = []
        result_downward_train = []

        for train in upward_train:
            train_dest = train['dest']['text']
            train_id = train['no']
            between = train['pos'].split('_')
            train_type = get_train_type(train_id, self.schedule[0])

            deperture_time = get_train_deperture_time(train_id, self.schedule[0])
            hour = ('0' + deperture_time['hour']) if len(deperture_time['hour']) == 1 else deperture_time['hour']
            minute = ('0' + deperture_time['minute']) if len(deperture_time['minute']) == 1 else deperture_time['minute']
            st_deperture_time = hour + ':' + minute
            
            if between[1] == '####':
                pos = self.search_station_name(list_station, between[0]) + ' に停車中'
            else:
                from_st = self.search_station_name(list_station, between[1])
                to_st = self.search_station_name(list_station, between[0])
                pos = from_st + ' から ' + to_st + ' に向かって走行中'
            train_delay = str(train['delayMinutes']) + '分' if train['delayMinutes'] != 0 else 'なし'

            result_upward_train.append({'time': st_deperture_time, 'type': train_type, 'dest': train_dest, 'pos': pos, 'delay': train_delay, 'remain_time': str(remain_time_until_deperture(train, hour, minute))})

        for train in downward_train:
            train_dest = train['dest']['text']
            train_id = train['no']
            between = train['pos'].split('_')
            train_type = get_train_type(train_id, self.schedule[1])

            deperture_time = get_train_deperture_time(train_id, self.schedule[1])
            hour = ('0' + deperture_time['hour']) if len(deperture_time['hour']) == 1 else deperture_time['hour']
            minute = ('0' + deperture_time['minute']) if len(deperture_time['minute']) == 1 else deperture_time['minute']
            st_deperture_time = hour + ':' + minute
            
            if between[1] == '####':
                pos = self.search_station_name(list_station, between[0]) + ' に停車中'
            else:
                from_st = self.search_station_name(list_station, between[0])
                to_st = self.search_station_name(list_station, between[1])
                pos = from_st + ' から ' + to_st + ' に向かって走行中'

            train_delay = str(train['delayMinutes']) + '分' if train['delayMinutes'] != 0 else 'なし'

            result_downward_train.append({'time': st_deperture_time, 'type': train_type, 'dest': train_dest, 'pos': pos, 'delay': train_delay, 'remain_time': remain_time_until_deperture(train, hour, minute)})

        for train_list in [result_upward_train, result_downward_train]:
            train_list.sort(key=lambda x: int(x['remain_time']))
        return result_upward_train, result_downward_train

    def crawl_current_trafficinfo_jr_west(self):
        traffic_info_url = self.jr_api_url + 'area_kinki_trafficinfo.json'

        try:
            res_traffic_info = urllib.request.urlopen(traffic_info_url)
            traffic_data = json.loads(res_traffic_info.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"JR西日本の運行情報へHTTPアクセス中にエラー: {e}")
            return 'JR ' + self.request_line + '線 ', '運行情報の取得に失敗しました'

        try:
            for line in traffic_data['lines']:
                if line == self.request_line_en:
                    if traffic_data['lines'][line]['section']['from'] is None or traffic_data['lines'][line]['section']['to'] is None:
                        return 'JR ' + self.request_line + '線 ', traffic_data['lines'][line]['cause'] + ' のため ' + traffic_data['lines'][line]['status']
                    else:
                        return 'JR ' + self.request_line + '線 ', traffic_data['lines'][line]['section']['from'] + ' から ' + traffic_data['lines'][line]['section']['to'] + ' まで ' + traffic_data['lines'][line]['cause'] + ' のため ' + traffic_data['lines'][line]['status']
        except Exception as e:
            logger.error(f"クロールしたJR西日本の運行情報の処理中にエラー: {e}")
            return 'JR ' + self.request_line + '線 ', '運行情報の取得に失敗しました'

        return 'JR ' + self.request_line + '線 ', '遅延はありません'

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

        try:
            responce_stationinfo = urllib.request.urlopen(url_stationinfo)
            data_station = json.loads(responce_stationinfo.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"JR西日本の駅情報へHTTPアクセス中にエラー: {e}")
            return []

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