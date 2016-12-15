#!/usr/bin/env python
# coding=utf-8

import xlsxwriter as xlsxwriter

from constants import ORG_KEY_CHN_TITLE_DICT, ORG_ALL_SUM_EXCEL, ORG_ALL_DETAIL_EXCEL, ALL_KEY_CHN_TITLE_DICT


class ExcelTableWriter(object):
    def __init__(self, excel_file_name, sheet_name, title_names, data_values):
        self.excel_file_handler = xlsxwriter.Workbook(excel_file_name)
        self.table_handler = self.excel_file_handler.add_worksheet(sheet_name)
        self.title_bold = self.excel_file_handler.add_format({
            'bold': True,
            'border': 2,
            'bg_color': 'green'
        })
        self.border = self.excel_file_handler.add_format({'border': 1})
        self.title_names = title_names
        self.data_values = data_values


class AllDetailExcelTableWriter(ExcelTableWriter):
    def __init__(self, title_names, data_values):
        ExcelTableWriter.__init__(self, ORG_ALL_DETAIL_EXCEL, ORG_ALL_DETAIL_EXCEL.split('.')[0], title_names, data_values)
        self.create_all_detail_excel_file()

    def create_all_detail_excel_file(self):
        for i, j in enumerate(self.title_names):
            self.table_handler.set_column(i, i, 8)
            self.table_handler.write_string(0, i, ORG_KEY_CHN_TITLE_DICT[j], self.title_bold)
        for (row_idx, value) in self.data_values.iteritems():
            column_idx = 0
            for (k, v) in value.iteritems():
                if is_digit_number(v):
                    self.table_handler.write_number(row_idx + 1, column_idx, int(v))
                else:
                    self.table_handler.write_string(row_idx + 1, column_idx, str(v))
                column_idx += 1
        self.excel_file_handler.close()


class AllSumExceTableWriter(ExcelTableWriter):
    def __init__(self, title_names, data_values):
        ExcelTableWriter.__init__(self, ORG_ALL_SUM_EXCEL, ORG_ALL_SUM_EXCEL.split('.')[0], title_names, data_values)
        self.create_all_sum_excel_file()

    def create_all_sum_excel_file(self):
        for i, j in enumerate(self.title_names):
            self.table_handler.set_column(i, i, 8)
            self.table_handler.write_string(0, i, ORG_KEY_CHN_TITLE_DICT[j], self.title_bold)
        column_idx = 0
        for (key, value) in self.data_values.iteritems():
            row_idx = 0
            if is_digit_number(value):
                self.table_handler.write_number(row_idx + 1, column_idx, int(value))
            else:
                self.table_handler.write_string(row_idx + 1, column_idx, str(value))
            column_idx += 1
        self.excel_file_handler.close()


class IntervalSumExceTableWriter(ExcelTableWriter):
    def __init__(self, table_name, nonfilter_data_values, big_data_values, small_data_values, other_data_values, date_str_list, time_str_list):
        self.non_filter_data_values = nonfilter_data_values
        self.big_data_values = big_data_values
        self.small_data_values = small_data_values
        self.other_data_values = other_data_values

        self.excel_file_handler = xlsxwriter.Workbook(table_name)
        self.non_filter_table_handler = self.excel_file_handler.add_worksheet(u'无过滤分段数据')
        self.big_table_handler = self.excel_file_handler.add_worksheet(u'大单分段数据')
        self.small_table_handler = self.excel_file_handler.add_worksheet(u'小单分段数据')
        self.other_table_handler = self.excel_file_handler.add_worksheet(u'其他分段数据')
        self.title_bold = self.excel_file_handler.add_format({'bold': True, 'border': 2, 'bg_color': 'green'})
        self.border = self.excel_file_handler.add_format({'border': 1})
        self.title_names = self.non_filter_data_values.keys()
        self.create_interval_sum_excel_file(date_str_list, time_str_list)

    def create_interval_sum_excel_file(self, date_str_list, time_str_list):
        self.create_interval_sum_excel_sheet(self.non_filter_table_handler, self.non_filter_data_values, date_str_list, time_str_list)
        self.create_interval_sum_excel_sheet(self.big_table_handler, self.big_data_values, date_str_list, time_str_list)
        self.create_interval_sum_excel_sheet(self.small_table_handler, self.small_data_values, date_str_list, time_str_list)
        self.create_interval_sum_excel_sheet(self.other_table_handler, self.other_data_values, date_str_list, time_str_list)
        self.excel_file_handler.close()

    def create_interval_sum_excel_sheet(self, sheet_handler, data_values, date_str_list, time_str_list):
        sheet_handler.write_string(0, 0, u'日期', self.title_bold)
        sheet_handler.write_string(0, 1, u'时间', self.title_bold)
        sheet_handler.set_column(0, 0, 10)
        sheet_handler.set_column(1, len(data_values.keys()), 8)
        for i, j in enumerate(self.title_names):
            sheet_handler.write_string(0, i + 2, ALL_KEY_CHN_TITLE_DICT[j], self.title_bold)
        column_idx = 0
        for (key, value) in data_values.iteritems():
            row_idx = 0
            for each in value:
                sheet_handler.write_string(row_idx + 1, 0, date_str_list[row_idx])  # 日期
                sheet_handler.write_string(row_idx + 1, 1, time_str_list[row_idx])  # 时间
                if is_digit_number(each):
                    sheet_handler.write_number(row_idx + 1, column_idx + 2, int(each))
                else:
                    sheet_handler.write_string(row_idx + 1, column_idx + 2, str(each))
                row_idx += 1
            column_idx += 1


def is_digit_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
