#!/usr/bin/env python
# coding=utf-8

import logging.handlers
import math
import pprint
import re
import time
from collections import OrderedDict
from copy import deepcopy

from prettytable import PrettyTable

KEY_READ_ERROR = 'Not exist'
LOG_FILE = 'qihuo.log'
FILE_NAME = 'baicha1.txt'

FENZHONG_1 = 60
FENZHONG_5 = 5 * FENZHONG_1
FENZHONG_15 = 15 * FENZHONG_1
FENZHONG_30 = 30 * FENZHONG_1

KEY_DICT = {
    'CANGL': u'仓量', 'CJE': u'成交额', 'CJL': u'成交量', 'FANGX': u'方向', 'JIAG': u'价格', 'KAIC': u'开仓',
    'KDKD': u'开多开多', 'KDKK': u'开多开空', 'KDPD': u'开多平多', 'KKKD': u'开空开多', 'KKKK': u'开空开空',
    'KKPK': u'开空平空', 'PDKD': u'平多开多', 'PDPD': u'平多平多', 'PDPK': u'平多平空', 'PINGC': u'平仓',
    'PKKK': u'平空开空', 'PKPD': u'平空平多', 'PKPK': u'平空平空', 'SHIJ': u'时间', 'SHSP': u'上换手平',
    'SHSK': u'上换手开', 'WEIZ': u'交易位置', 'XHSP': u'下换手平', 'XHSK': u'下换手开', 'ZUIG': u'最高价',
    'ZUID': u'最低价', 'KPAN': u'开盘价', 'SPAN': u'收盘价'
}
EMPTY_TEMP_SUM_DICT = {
    'KDKD': 0, 'KDKK': 0, 'KDPD': 0, 'PKPK': 0, 'PKKK': 0, 'PKPD': 0, 'PDPD': 0, 'PDKD': 0, 'PDPK': 0,
    'KKKK': 0, 'KKKD': 0, 'KKPK': 0, 'SHSP': 0, 'SHSK': 0, 'XHSP': 0, 'XHSK': 0, 'KPAN': 0, 'SPAN': 0,
    'ZUIG': list(), 'ZUID': list()
}
ALL_SUM_DICT = {
    'KDKD': 0, 'KDKK': 0, 'KDPD': 0, 'PKPK': 0, 'PKKK': 0, 'PKPD': 0, 'PDPD': 0, 'PDKD': 0, 'PDPK': 0,
    'KKKK': 0, 'KKKD': 0, 'KKPK': 0, 'SHSP': 0, 'SHSK': 0, 'XHSP': 0, 'XHSK': 0, 'KPAN': 0, 'SPAN': 0,
    'ZUIG': list(), 'ZUID': list()
}
INTERVAL_SUM_DICT = OrderedDict()
INTERVAL_SUM_DICT['KDKD'] = list()
INTERVAL_SUM_DICT['KDKK'] = list()
INTERVAL_SUM_DICT['KDPD'] = list()
INTERVAL_SUM_DICT['PDPD'] = list()
INTERVAL_SUM_DICT['PDPK'] = list()
INTERVAL_SUM_DICT['PDKD'] = list()
INTERVAL_SUM_DICT['KKKK'] = list()
INTERVAL_SUM_DICT['KKKD'] = list()
INTERVAL_SUM_DICT['KKPK'] = list()
INTERVAL_SUM_DICT['PKPK'] = list()
INTERVAL_SUM_DICT['PKKK'] = list()
INTERVAL_SUM_DICT['PKPD'] = list()
INTERVAL_SUM_DICT['SHSK'] = list()
INTERVAL_SUM_DICT['SHSP'] = list()
INTERVAL_SUM_DICT['XHSK'] = list()
INTERVAL_SUM_DICT['XHSP'] = list()
INTERVAL_SUM_DICT['ZUIG'] = list()
INTERVAL_SUM_DICT['ZUID'] = list()
INTERVAL_SUM_DICT['KPAN'] = list()
INTERVAL_SUM_DICT['SPAN'] = list()

handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024)
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(message)s'
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def reset_dict(dict_data):
    for (k, v) in dict_data.iteritems():
        if k == 'ZUIG' or k == 'ZUID':
            dict_data[k] = list()
        else:
            dict_data[k] = 0


class DataHandler(object):
    def __init__(self):
        self.logger = logger
        self.data_dict = OrderedDict()
        self.first_record_timestamp = 0
        self.last_record_timestamp = 0

    # 根据价格计算方向
    def generate_dynamic_data(self):
        start_time = time.time()
        reversed_keys = deepcopy(self.data_dict.keys())
        reversed_keys.reverse()
        earliest_record_index_number = len(reversed_keys) - 1  # 最早的那条记录的索引值
        # 设置最早和最晚的时间戳
        self.first_record_timestamp = self.data_dict[earliest_record_index_number]['SHIJ']
        self.last_record_timestamp = self.data_dict[0]['SHIJ']
        # 确定第一个交易位置值
        for each in reversed_keys:
            if each < earliest_record_index_number:
                if self.data_dict[each]['JIAG'] > self.data_dict[earliest_record_index_number]['JIAG']:
                    # 如果下一条记录的价格比最开始的那条记录的价格大的话. 最开始的那条记录赋值为-1
                    self.data_dict[earliest_record_index_number]['WEIZ'] = -1
                    break
                elif self.data_dict[each]['JIAG'] < self.data_dict[earliest_record_index_number]['JIAG']:
                    # 如果下一条记录的价格比最开始的那条记录的价格小的话. 最开始的那条记录赋值为1
                    self.data_dict[earliest_record_index_number]['WEIZ'] = 1
                    break
                else:
                    # 如果下一条记录的价格跟最开始的那条记录的价格一样的话. 忽略，进行下一条记录的比较
                    pass
        print(u'确定第一个交易位置值花费时间为：%s' % (time.time() - start_time))

        for each in reversed_keys:
            if self.data_dict[each]['WEIZ'] == 0:
                current_price = self.data_dict[each]['JIAG']
                previous_price = self.data_dict[each + 1]['JIAG']
                if int(current_price) - int(previous_price) > 0:
                    WEIZ = 1
                elif int(current_price) - int(previous_price) < 0:
                    WEIZ = -1
                else:
                    WEIZ = self.data_dict[each + 1]['WEIZ']
                self.data_dict[each]['WEIZ'] = WEIZ

                if WEIZ == 1:
                    if self.data_dict[each]['KAIC'] < self.data_dict[each]['PINGC']:
                        # 开仓小于平仓
                        self.data_dict[each]['PKPK'] = self.data_dict[each]['CJL'] / 2
                        self.data_dict[each]['PKKK'] = self.data_dict[each]['KAIC']
                        self.data_dict[each]['PKPD'] = self.data_dict[each]['CJL'] / 2 - self.data_dict[each]['KAIC']
                    elif self.data_dict[each]['KAIC'] > self.data_dict[each]['PINGC']:
                        # 开仓大于平仓
                        self.data_dict[each]['KDKD'] = self.data_dict[each]['CJL'] / 2
                        self.data_dict[each]['KDKK'] = self.data_dict[each]['CJL'] / 2 - self.data_dict[each]['PINGC']
                        self.data_dict[each]['KDPD'] = self.data_dict[each]['PINGC']
                    else:
                        # 开仓等于平仓
                        self.data_dict[each]['SHSP'] = self.data_dict[each]['KAIC']
                        self.data_dict[each]['SHSK'] = self.data_dict[each]['PINGC']
                elif WEIZ == -1:
                    if self.data_dict[each]['KAIC'] < self.data_dict[each]['PINGC']:
                        # 开仓小于平仓
                        self.data_dict[each]['PDPD'] = self.data_dict[each]['CJL'] / 2
                        self.data_dict[each]['PDKD'] = self.data_dict[each]['KAIC']
                        self.data_dict[each]['PDPK'] = self.data_dict[each]['CJL'] / 2 - self.data_dict[each]['KAIC']
                    elif self.data_dict[each]['KAIC'] > self.data_dict[each]['PINGC']:
                        # 开仓大于平仓
                        self.data_dict[each]['KKKK'] = self.data_dict[each]['CJL'] / 2
                        self.data_dict[each]['KKKD'] = self.data_dict[each]['CJL'] / 2 - self.data_dict[each]['PINGC']
                        self.data_dict[each]['KKPK'] = self.data_dict[each]['PINGC']
                    else:
                        # 开仓等于平仓
                        self.data_dict[each]['XHSP'] = self.data_dict[each]['PINGC']
                        self.data_dict[each]['XHSK'] = self.data_dict[each]['KAIC']
                else:
                    self.logger.error(u'有问题， 交易位置非1 或 -1')

        self.logger.debug('Time Consumption for generate_price_trade_position(): %s', time.time() - start_time)
        print(u'计算其他动态值所花费时间为：%s' % (time.time() - start_time))

    def read_file(self, redis_client):
        start_time = time.time()
        index = 0
        with open('%s' % FILE_NAME, 'r') as data_file:
            while True:
                line = data_file.readline()
                if line:
                    data_elements = re.split(' |\t', line)
                    record_time = (str(data_elements[1]) + ',' + str(data_elements[0]))
                    pattern = '%Y%m%d,%H:%M'
                    time_format = time.strptime(record_time, pattern)
                    epech_time = time.mktime(time_format)
                    self.data_dict[index] = {
                        'SHIJ': epech_time,  # 时间
                        'JIAG': int(data_elements[2]) if data_elements[2] else 0,  # 价格
                        'CJL': int(data_elements[3]) if data_elements[3] else 0,  # 成交量
                        'CJE': int(data_elements[4]) if data_elements[4] else 0,  # 成交额
                        'CANGL': int(data_elements[5]) if data_elements[5] else 0,  # 仓量
                        'KAIC': int(data_elements[9]) if data_elements[9] else 0,  # 开仓
                        'PINGC': int(data_elements[10] if data_elements[10] else 0),  # 平仓
                        'FANGX': data_elements[11].strip() if data_elements[11] else 0,  # 方向
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
                    }
                    # redis_client.write_data(str(index), json.dumps(data_dict, ensure_ascii=False))
                else:
                    print(u'读取文件完毕')
                    break
                index += 1

            print(u'读取文件花费时间为：%s' % (time.time() - start_time))
            self.logger.info(u'读取文件花费时间为：%s', time.time() - start_time)

    def print_to_file(self):
        self.logger.info('All data is:\n%s', pprint.pformat(dict(self.data_dict)))

    def print_as_text(self):
        reversed_keys = deepcopy(self.data_dict.keys())
        reversed_keys.reverse()
        with open('temp.file.txt', 'w') as text_file:
            for (k, v) in KEY_DICT.iteritems():
                text_file.write(k)
                text_file.write('\t')
            text_file.write('\n')
            for each in reversed_keys:
                for (k, v) in KEY_DICT.iteritems():
                    text_file.write(str(self.data_dict[each][k]))
                    text_file.write('\t')
                text_file.write('\n')
        print(u'打印到文本文件成功')

    def read_all_sum(self):
        for each in self.data_dict.values():
            ALL_SUM_DICT['KDKD'] += each['KDKD']
            ALL_SUM_DICT['KDKK'] += each['KDKK']
            ALL_SUM_DICT['KDPD'] += each['KDPD']
            ALL_SUM_DICT['PKPK'] += each['PKPK']
            ALL_SUM_DICT['PKKK'] += each['PKKK']
            ALL_SUM_DICT['PKPD'] += each['PKPD']
            ALL_SUM_DICT['PDPD'] += each['PDPD']
            ALL_SUM_DICT['PDKD'] += each['PDKD']
            ALL_SUM_DICT['PDPK'] += each['PDPK']
            ALL_SUM_DICT['KKKK'] += each['KKKK']
            ALL_SUM_DICT['KKKD'] += each['KKKD']
            ALL_SUM_DICT['KKPK'] += each['KKPK']
            ALL_SUM_DICT['SHSP'] += each['SHSP']
            ALL_SUM_DICT['SHSK'] += each['SHSK']
            ALL_SUM_DICT['XHSP'] += each['XHSP']
            ALL_SUM_DICT['XHSK'] += each['XHSK']
            ALL_SUM_DICT['ZUIG'].append(each['JIAG'])
            ALL_SUM_DICT['ZUID'].append(each['JIAG'])

        ALL_SUM_DICT['ZUIG'] = max(ALL_SUM_DICT['ZUIG'])
        ALL_SUM_DICT['ZUID'] = min(ALL_SUM_DICT['ZUID'])
        ALL_SUM_DICT['KPAN'] = self.data_dict[len(self.data_dict.keys()) - 1]['JIAG']
        ALL_SUM_DICT['SPAN'] = self.data_dict[0]['JIAG']

        # print(u'所有汇总数据为:\n %s' % pprint.pformat(ALL_SUM_DICT))
        # self.logger.info(u'所有汇总数据为:\n %s', pprint.pformat(ALL_SUM_DICT))

        all_sum_table = PrettyTable([u'名称', u'数值'], padding_width=1, border=False)
        all_sum_table.align[u'名称'] = "l"
        all_sum_table.align[u'数值'] = "l"
        for (k, v) in ALL_SUM_DICT.iteritems():
            all_sum_table.add_row([KEY_DICT[k], v])

        self.logger.info(u'汇总数据为::\n %s', all_sum_table)
        print(u'汇总数据为:\n %s' % (all_sum_table))

    def read_interval_sum(self, interval):
        number_of_interval = int(math.ceil((self.last_record_timestamp - self.first_record_timestamp) / 60 / interval))
        self.logger.debug(u'对所有数据进行按照%s分钟的间隔，共被分割为%s段的数据', interval, number_of_interval)
        print(u'对所有数据进行按照%s分钟的间隔，共被分割为%s段的数据' % (interval, number_of_interval))

        temp_sum = EMPTY_TEMP_SUM_DICT
        timestamp_list = list()
        for each_loop in range(1, number_of_interval):
            reset_dict(temp_sum)
            for each in self.data_dict.values():
                if 0 <= each['SHIJ'] - self.first_record_timestamp < FENZHONG_1 * int(interval):
                    temp_sum['KDKD'] += each['KDKD']
                    temp_sum['KDKK'] += each['KDKK']
                    temp_sum['KDPD'] += each['KDPD']
                    temp_sum['PKPK'] += each['PKPK']
                    temp_sum['PKKK'] += each['PKKK']
                    temp_sum['PKPD'] += each['PKPD']
                    temp_sum['PDPD'] += each['PDPD']
                    temp_sum['PDKD'] += each['PDKD']
                    temp_sum['PDPK'] += each['PDPK']
                    temp_sum['KKKK'] += each['KKKK']
                    temp_sum['KKKD'] += each['KKKD']
                    temp_sum['KKPK'] += each['KKPK']
                    temp_sum['SHSP'] += each['SHSP']
                    temp_sum['SHSK'] += each['SHSK']
                    temp_sum['XHSP'] += each['XHSP']
                    temp_sum['XHSK'] += each['XHSK']
                    temp_sum['ZUIG'].append(each['JIAG'])
                    temp_sum['ZUID'].append(each['JIAG'])

            temp_sum['ZUIG'] = max(temp_sum['ZUIG']) if temp_sum['ZUIG'] else 0
            temp_sum['ZUID'] = min(temp_sum['ZUID']) if temp_sum['ZUID'] else 0
            temp_sum['KPAN'] = self.data_dict[len(self.data_dict.keys()) - 1]['JIAG']
            temp_sum['SPAN'] = self.data_dict[0]['JIAG']

            new_first_record_timestamp = self.first_record_timestamp + FENZHONG_1 * int(interval)
            validate_value_dict = deepcopy(temp_sum)
            # 删除永远不为零的4个元素
            validate_value_dict.pop('ZUIG')
            validate_value_dict.pop('ZUID')
            validate_value_dict.pop('KPAN')
            validate_value_dict.pop('SPAN')
            if any(validate_value_dict.values()):
                timestamp_list.append(u'%s-%s' %
                                      (time.strftime('%H:%M', time.localtime(self.first_record_timestamp)),
                                       time.strftime('%H:%M', time.localtime(new_first_record_timestamp))))
                INTERVAL_SUM_DICT['KDKD'].append(temp_sum['KDKD'])
                INTERVAL_SUM_DICT['KDKK'].append(temp_sum['KDKK'])
                INTERVAL_SUM_DICT['KDPD'].append(temp_sum['KDPD'])
                INTERVAL_SUM_DICT['PKPK'].append(temp_sum['PKPK'])
                INTERVAL_SUM_DICT['PKKK'].append(temp_sum['PKKK'])
                INTERVAL_SUM_DICT['PKPD'].append(temp_sum['PKPD'])
                INTERVAL_SUM_DICT['PDPD'].append(temp_sum['PDPD'])
                INTERVAL_SUM_DICT['PDKD'].append(temp_sum['PDKD'])
                INTERVAL_SUM_DICT['PDPK'].append(temp_sum['PDPK'])
                INTERVAL_SUM_DICT['KKKK'].append(temp_sum['KKKK'])
                INTERVAL_SUM_DICT['KKKD'].append(temp_sum['KKKD'])
                INTERVAL_SUM_DICT['KKPK'].append(temp_sum['KKPK'])
                INTERVAL_SUM_DICT['SHSP'].append(temp_sum['SHSP'])
                INTERVAL_SUM_DICT['SHSK'].append(temp_sum['SHSK'])
                INTERVAL_SUM_DICT['XHSP'].append(temp_sum['XHSP'])
                INTERVAL_SUM_DICT['XHSK'].append(temp_sum['XHSK'])
                INTERVAL_SUM_DICT['ZUIG'].append(temp_sum['ZUIG'])
                INTERVAL_SUM_DICT['ZUID'].append(temp_sum['ZUID'])
                INTERVAL_SUM_DICT['KPAN'].append(temp_sum['KPAN'])
                INTERVAL_SUM_DICT['SPAN'].append(temp_sum['SPAN'])
            else:
                # print(u'所有值都为0，放弃当前行更新到表。\n%s' % pprint.pformat(temp_sum))
                pass

            self.first_record_timestamp = new_first_record_timestamp
            # self.logger.debug(u'更新起始时间戳为：%s', time.strftime('%Y-%m-%d,%H:%M', time.localtime(
            # new_first_record_timestamp)))

        interval_table = PrettyTable(border=False)
        interval_table.add_column(u'名称', timestamp_list)
        for (k, v) in INTERVAL_SUM_DICT.iteritems():
            interval_table.add_column(KEY_DICT[k], v)

        self.logger.info(u'%s 分钟合计数据为::\n %s', interval, interval_table)
        print(u'%s 分钟合计数据为:\n %s' % (interval, interval_table))


def main():
    redis_client = None  # RedisConnection()
    data_handler = DataHandler()
    data_handler.read_file(redis_client)
    data_handler.generate_dynamic_data()
    # data_handler.print_to_file()
    # data_handler.print_as_text()
    data_handler.read_all_sum()
    data_handler.read_interval_sum(15)


if __name__ == '__main__':
    main()
