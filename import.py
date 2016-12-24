#!/usr/bin/env python
# coding=utf-8
import json
import math
import pprint
import re
import time
from collections import OrderedDict
from copy import deepcopy

import argparse
import requests
from influxdb import InfluxDBClient
from prettytable import PrettyTable

from constants import CONFIG_NAME, get_log_handler, ORG_EMPTY_DATA_DICT, MIN, MAX, FENZHONG_1, \
    INFLUX_DB_NAME, fill_order_org_empty_dict, \
    fill_order_org_list_dict, \
    reset_dict, is_trade_time, is_trade_end_time, BASIC_INTERVAL


class DataHandler(object):
    def __init__(self, name=None, border=False):
        self.trade_period = 'day'
        self.log_logger = get_log_handler()
        self.border = border
        self.datadict = OrderedDict()
        self.static_first_record_timestamp = 0
        self.first_record_timestamp = 0
        self.last_record_timestamp = 0
        self.endpoint_url = 'http://localhost:8086/query'
        self.config_name = name
        self.cfg_file = self.read_config_file()
        self.config_data = self.cfg_file[name]
        self.date_list = list()
        self.time_list = list()
        self.all_data_dict = deepcopy(ORG_EMPTY_DATA_DICT)
        self.each_interval_data = deepcopy(fill_order_org_empty_dict(OrderedDict()))
        self.interval_sum_data_dict = deepcopy(fill_order_org_list_dict(OrderedDict()))
        self.interval_data_dict = OrderedDict()

    @staticmethod
    def pack_data_into_dict(each, data_dict, filter_range=None):
        min_range, max_range = filter_range if filter_range else (MIN, MAX)
        for key in ORG_EMPTY_DATA_DICT.keys():
            if key == 'ZUIG' or key == 'ZUID' or key == 'KPAN' or key == 'SPAN':
                data_dict[key].append(each['JIAG'])
            else:
                if min_range <= each[key] < max_range:
                    data_dict[key] += each[key]
        return data_dict

    def read_config_file(self):
        with open(CONFIG_NAME) as cfg_file:
            file_data = json.load(cfg_file, encoding='utf-8')
        cfg_print_tbl = PrettyTable(['变量名', '数值'])
        for (k, v) in file_data[self.config_name].iteritems():
            cfg_print_tbl.add_row([k, v])
        self.log_logger.debug(u'配置文件内容为：\n%s', cfg_print_tbl)
        print(u'配置文件内容为：\n%s' % cfg_print_tbl)
        return file_data

    def read_file(self):
        start_time = time.time()
        index = 0
        with open('%s' % self.cfg_file[self.config_name]['filename'], 'r') as data_file:
            while True:
                line = data_file.readline()
                if line:
                    data_elements = re.split(' |\t', line)
                    record_time = (str(data_elements[1]) + ',' + str(data_elements[0]))
                    pattern = '%Y%m%d,%H:%M'
                    time_format = time.strptime(record_time, pattern)
                    epech_time = time.mktime(time_format)
                    self.datadict[index] = {
                        'SHIJ': epech_time,  # 时间
                        'JIAG': int(data_elements[2]) if data_elements[2] else 0,  # 价格
                        'CJL': int(data_elements[3]) if data_elements[3] else 0,  # 成交量
                        'CJE': int(data_elements[4]) if data_elements[4] else 0,  # 成交额
                        'CANGL': int(data_elements[5]) if data_elements[5] else 0,  # 仓量
                        'KAIC': int(data_elements[9]) if data_elements[9] else 0,  # 开仓
                        'PINGC': int(data_elements[10] if data_elements[10] else 0),  # 平仓
                        # 'FANGX': data_elements[11].strip() if data_elements[11] else 0,  # 方向
                        'FANGX': 'fangxiang',  # 方向
                        'WEIZ': 0,  # 交易位置
                        'KDKD': 0,  # 开多开多
                        'KDKK': 0,  # 开多开空
                        'KDPD': 0,  # 开多平多
                        'PKPK': 0,  # 平空平空
                        'PKKK': 0,  # 平空开空
                        'PKPD': 0,  # 平空平多
                        'PDPD': 0,  # 平多平多
                        'PDKD': 0,  # 平多开多
                        'PDPK': 0,  # 平多平空
                        'KKKK': 0,  # 开空开空
                        'KKKD': 0,  # 开空开多
                        'KKPK': 0,  # 开空平空
                        'SHSP': 0,  # 上换手平
                        'SHSK': 0,  # 上换手开
                        'XHSP': 0,  # 下换手平
                        'XHSK': 0,  # 下换手开
                        'KPAN': 0,  # 开盘价
                        'SPAN': 0,  # 收盘价
                        'ZUIG': 0,  # 最高价
                        'ZUID': 0.  # 最低价
                    }
                else:
                    break
                index += 1
            self.log_logger.info(u'读取文件花费时间为：%s', time.time() - start_time)

    def generate_dynamic_data(self):  # 根据价格计算方向
        start_time = time.time()

        reversed_keys = deepcopy(self.datadict.keys())
        reversed_keys.reverse()
        earliest_record_index_number = len(reversed_keys) - 1  # 最早的那条记录的索引值
        # 设置最早和最晚的时间戳
        self.static_first_record_timestamp = deepcopy(self.datadict[earliest_record_index_number]['SHIJ'])
        self.first_record_timestamp = deepcopy(self.datadict[earliest_record_index_number]['SHIJ'])
        self.last_record_timestamp = deepcopy(self.datadict[0]['SHIJ'])
        self.trade_period = 'night' if time.strftime('%Y-%m-%d,%H:%M:%S', time.localtime(self.first_record_timestamp)).split(',')[
                                           1] == '19:00:00' else 'day'

        # 确定第一个交易位置值
        for each in reversed_keys:
            if each < earliest_record_index_number:
                if self.datadict[each]['JIAG'] > self.datadict[earliest_record_index_number]['JIAG']:
                    # 如果下一条记录的价格比最开始的那条记录的价格大的话. 最开始的那条记录赋值为-1
                    self.datadict[earliest_record_index_number]['WEIZ'] = -1
                    self.generate_each_dynamic_data(self.datadict[earliest_record_index_number]['WEIZ'],
                                                    earliest_record_index_number)
                    break
                elif self.datadict[each]['JIAG'] < self.datadict[earliest_record_index_number]['JIAG']:
                    # 如果下一条记录的价格比最开始的那条记录的价格小的话. 最开始的那条记录赋值为1
                    self.datadict[earliest_record_index_number]['WEIZ'] = 1
                    self.generate_each_dynamic_data(self.datadict[earliest_record_index_number]['WEIZ'],
                                                    earliest_record_index_number)
                    break
                else:
                    # 如果下一条记录的价格跟最开始的那条记录的价格一样的话. 忽略，进行下一条记录的比较
                    pass
        # print(u'确定第一个交易位置值花费时间为：%s' % (time.time() - start_time))
        self.log_logger.debug(u'确定第一个交易位置值花费时间为：%s', time.time() - start_time)

        for each in reversed_keys:
            if self.datadict[each]['WEIZ'] == 0:
                current_price = self.datadict[each]['JIAG']
                previous_price = self.datadict[each + 1]['JIAG']
                if int(current_price) - int(previous_price) > 0:
                    WEIZ = 1
                elif int(current_price) - int(previous_price) < 0:
                    WEIZ = -1
                else:
                    WEIZ = self.datadict[each + 1]['WEIZ']
                self.datadict[each]['WEIZ'] = WEIZ
                self.generate_each_dynamic_data(WEIZ, each)

        self.log_logger.debug(u'计算其他动态值所花费时间为：%s', time.time() - start_time)
        # print(u'计算其他动态值所花费时间为：%s' % (time.time() - start_time))

    def generate_each_dynamic_data(self, weizhi, each):
        if weizhi == 1:
            if self.datadict[each]['KAIC'] < self.datadict[each]['PINGC']:
                # 开仓小于平仓
                self.datadict[each]['PKPK'] = self.datadict[each]['CJL'] / 2
                self.datadict[each]['PKKK'] = self.datadict[each]['KAIC']
                self.datadict[each]['PKPD'] = self.datadict[each]['CJL'] / 2 - self.datadict[each]['KAIC']
            elif self.datadict[each]['KAIC'] > self.datadict[each]['PINGC']:
                # 开仓大于平仓
                self.datadict[each]['KDKD'] = self.datadict[each]['CJL'] / 2
                self.datadict[each]['KDKK'] = self.datadict[each]['CJL'] / 2 - self.datadict[each]['PINGC']
                self.datadict[each]['KDPD'] = self.datadict[each]['PINGC']
            else:
                # 开仓等于平仓
                self.datadict[each]['SHSP'] = self.datadict[each]['KAIC']
                self.datadict[each]['SHSK'] = self.datadict[each]['PINGC']
        elif weizhi == -1:
            if self.datadict[each]['KAIC'] < self.datadict[each]['PINGC']:
                # 开仓小于平仓
                self.datadict[each]['PDPD'] = self.datadict[each]['CJL'] / 2
                self.datadict[each]['PDKD'] = self.datadict[each]['KAIC']
                self.datadict[each]['PDPK'] = self.datadict[each]['CJL'] / 2 - self.datadict[each]['KAIC']
            elif self.datadict[each]['KAIC'] > self.datadict[each]['PINGC']:
                # 开仓大于平仓
                self.datadict[each]['KKKK'] = self.datadict[each]['CJL'] / 2
                self.datadict[each]['KKKD'] = self.datadict[each]['CJL'] / 2 - self.datadict[each]['PINGC']
                self.datadict[each]['KKPK'] = self.datadict[each]['PINGC']
            else:
                # 开仓等于平仓
                self.datadict[each]['XHSP'] = self.datadict[each]['PINGC']
                self.datadict[each]['XHSK'] = self.datadict[each]['KAIC']
        else:
            self.log_logger.error(u'有问题， 交易位置非1 或 -1')

    def generate_basic_interval_data(self):
        number_of_interval = int(math.ceil((self.last_record_timestamp - self.first_record_timestamp) / 60 / BASIC_INTERVAL))
        self.log_logger.debug(u'对\"%s\"的所有数据(数据源:%s)进行按照%s分钟的间隔，共被分割为%s段的数据',
                              self.cfg_file[self.config_name]['chinese'],
                              self.cfg_file[self.config_name]['filename'],
                              BASIC_INTERVAL, number_of_interval)
        print(u'对\"%s\"的所有数据(数据源:%s)进行按照%s分钟的间隔，共被分割为%s段的数据'
              % (self.cfg_file[self.config_name]['chinese'],
                 self.cfg_file[self.config_name]['filename'],
                 BASIC_INTERVAL, number_of_interval))

        start_time = time.time()
        for each_loop in range(0, number_of_interval):
            reset_dict(self.each_interval_data)

            start_time_diff = FENZHONG_1 * int(BASIC_INTERVAL) * each_loop
            end_time_diff = FENZHONG_1 * int(BASIC_INTERVAL) * (each_loop + 1)
            loop_dict_values = deepcopy(self.datadict.values())
            loop_dict_values.reverse()
            for each_value in loop_dict_values:
                loop_time_diff = each_value['SHIJ'] - self.static_first_record_timestamp
                if (start_time_diff <= loop_time_diff <= end_time_diff if is_trade_end_time(
                        each_value['SHIJ']) else start_time_diff <= loop_time_diff < end_time_diff) \
                        and is_trade_time(self.trade_period, epoch_time=each_value['SHIJ']):
                    self.pack_data_into_dict(each_value, self.each_interval_data, filter_range=(MIN, MAX))
                elif loop_time_diff > end_time_diff:
                    # 如果当前时间超出最大时间范围则直接跳出。因为每条的时间戳都线性递增的。所以没有必要继续后面的
                    break

            self.each_interval_data['ZUIG'] = max(self.each_interval_data['ZUIG']) if self.each_interval_data['ZUIG'] else 0
            self.each_interval_data['ZUID'] = min(self.each_interval_data['ZUID']) if self.each_interval_data['ZUID'] else 0
            self.each_interval_data['KPAN'] = self.each_interval_data['KPAN'][0] if self.each_interval_data['KPAN'] else 0
            self.each_interval_data['SPAN'] = self.each_interval_data['SPAN'][len(self.each_interval_data['SPAN']) - 1] if self.each_interval_data[
                'SPAN'] else 0

            self.interval_data_dict[each_value['SHIJ']] = self.each_interval_data

        self.log_logger.info(u'所有数据循环读取完毕，耗时: %s' % (time.time() - start_time))
        # self.log_logger.info(pprint.pformat(dict(self.interval_data_dict)))

    def converter_data_into_interval_format(self, interval, basic_interval_data_dict, org_data_dict):
        updated_record_timestamp = self.first_record_timestamp + FENZHONG_1 * int(interval)
        date_string = time.strftime('%Y-%m-%d', time.localtime(self.first_record_timestamp))
        end_time = time.strftime('%H:%M', time.localtime(updated_record_timestamp))
        if is_trade_time(self.trade_period, string_time=time.strftime('%Y-%m-%d,%H:%M:%S', time.localtime(self.first_record_timestamp))):
            self.date_list.append(u'%s' % date_string)
            self.time_list.append(u'%s' % end_time)
            for key in ORG_EMPTY_DATA_DICT.keys():
                basic_interval_data_dict[key].append(org_data_dict[key])
        self.first_record_timestamp = updated_record_timestamp

    @staticmethod
    def get_point_str_data(name, time, data):
        return {
            "measurement": name,
            "time": time,
            "fields": data
        }

    def load_dynamic_data_into_influxdb(self):
        self.create_database()
        self.write_data_into_db()
        self.query_data_from_db()

    def query_data_from_db(self):
        start_time = time.time()
        query_cmd = 'select * from %s' % self.config_name
        query_params = {
            'q': query_cmd,
            'db': INFLUX_DB_NAME,
            'epoch': 'ms'
        }
        self.log_logger.debug(u'InfluxDB查询信息: URL=>%s 查询参数=>%s', self.endpoint_url, query_params)
        r = requests.get(self.endpoint_url, params=query_params, timeout=5)
        self.log_logger.debug(u'InfluxDB查询结果为%s, 所用时间为:%s，', u'成功' if r.status_code == 200 else u'失败', time.time() - start_time)
        self.log_logger.debug(u"InfluxDB查询返回数据为:\n%s",
                              pprint.pformat(r.json()['results'][0]['series'][0]['values']))

    def write_data_into_db(self):
        start_time = time.time()
        json_body = list()
        for (k, v) in self.interval_data_dict.iteritems():
            # print k
            # pprint.pprint(dict(v))
            point_string_data = self.get_point_str_data(self.config_name, int(k) * 1000, dict(v))
            json_body.append(point_string_data)
        client = InfluxDBClient('localhost', 8086, 'root', 'root', INFLUX_DB_NAME)
        return_value = client.write_points(json_body, time_precision='ms')
        self.log_logger.debug(u'写入InfluxDB数据库结果为%s， 花费时间为:%s', u'成功' if return_value else u'失败', time.time() - start_time)

    def create_database(self):
        create_db_cmd = 'CREATE DATABASE %s' % INFLUX_DB_NAME
        create_db_params = {
            'q': create_db_cmd
        }
        r = requests.get(self.endpoint_url, params=create_db_params, timeout=5)
        self.log_logger.debug(u'创建InfluxDB数据库:%s, 结果为%s', INFLUX_DB_NAME, u'成功' if r.status_code == 200 else u'失败')


def main(name=None, border=False):
    data_handler = DataHandler(name=name, border=border)
    data_handler.read_file()
    data_handler.generate_dynamic_data()
    data_handler.generate_basic_interval_data()
    data_handler.load_dynamic_data_into_influxdb()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interval', default=30, help=u'间隔时间，时间单位为分钟。')
    parser.add_argument('-n', '--name', help=u'配置信息名称', required=True)
    parser.add_argument('--border', default=False, action='store_true', help=u'是否显示表格边框，默认为不显示。')
    args = parser.parse_args()

    main(name=args.name, border=True)
