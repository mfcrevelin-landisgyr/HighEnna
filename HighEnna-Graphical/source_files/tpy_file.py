from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os

from error_messages import get_error_message
from table import Table

import highennabackend

class TpyFile:
    def __init__(self,dictionary,tpy_file_path):
        self.dictionary = {'tpy_file':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.tpy_file_path = tpy_file_path
        self.tpy_file_name = os.path.basename(tpy_file_path)

        self.parse()


    def parse(self):
        try:
            with open(self.tpy_file_path,'rb') as f:
                self.bytes = f.read().replace(b'\r',b'')
        except Exception as e:
            print(e)
            return

        self.create_time = os.path.getctime(self.tpy_file_path)
        self.mod_time = os.path.getmtime(self.tpy_file_path)

        self.parse_result = highennabackend.parse(self.bytes)

        if 'errors' in self.parse_result:
            self.errors_table = Table()
            self.errors_table.insert_column([(0,'Error Code'),(1,'Row'),(2,'Col'),(3,'Line'),(4,'What')])
            for index,error in enumerate(self.parse_result["errors"]):

                line,s,e = error['location'];
                ls = self.parse_result['line_start_indexes'][line-1]
                le = self.parse_result['line_start_indexes'][line]-1
                col = s - ls + 1

                line_prefix = ' '*len(self.bytes[ls:s].decode())
                line_middle = '^'*len(self.bytes[s:e].decode())
                line_postfix = ' '*len(self.bytes[e:le].decode())
                line_message = self.bytes[ls:le].decode()+'\n'+line_prefix+line_middle+line_postfix

                self.errors_table.insert_row([(index,)])
                self.errors_table.set_cell([(index,0,error['code'])])
                self.errors_table.set_cell([(index,1,line)])
                self.errors_table.set_cell([(index,2,col)])
                self.errors_table.set_cell([(index,3,line_message)])
                self.errors_table.set_cell([(index,4,get_error_message(error['code']))])
        else:

            if self.parse_result['names']['vars']:
                self.vars_table = Table()
                self.vars_table.insert_column([(i,var_name) for i,var_name in enumerate(sorted(self.parse_result['names']['vars']))])

            if self.parse_result['names']['vals']:
                self.vals_table = Table()
                self.vals_table.insert_column([(i,val_name) for i,val_name in enumerate(sorted(self.parse_result['names']['vals']))])


    def update(self):
        try:
            with open(self.tpy_file_path,'rb') as f:
                self.bytes = f.read().replace(b'\r',b'')
        except Exception as e:
            print(e)
            return

        self.create_time = os.path.getctime(self.tpy_file_path)
        self.mod_time = os.path.getmtime(self.tpy_file_path)

        self.parse_result = highennabackend.parse(self.bytes)

        if 'errors' in self.parse_result:
            self.errors_table = Table()
            self.errors_table.insert_column([(0,'Error Code'),(1,'Row'),(2,'Col'),(3,'Line'),(4,'What')])
            for index,error in enumerate(self.parse_result["errors"]):

                line,s,e = error['location'];
                ls = self.parse_result['line_start_indexes'][line-1]
                le = self.parse_result['line_start_indexes'][line]-1
                col = s - ls

                line_prefix = ' '+' '*len(self.bytes[ls:s].decode())
                line_middle = '^'*len(self.bytes[s:e].decode())
                line_postfix = ' '+' '*len(self.bytes[e:le].decode())
                line_message = '"'+self.bytes[ls:le].decode()+'"\n'+line_prefix+line_middle+line_postfix

                self.errors_table.insert_row([(index,)])
                self.errors_table.set_cell([(index,0,error['code'])])
                self.errors_table.set_cell([(index,1,line)])
                self.errors_table.set_cell([(index,2,col)])
                self.errors_table.set_cell([(index,3,line_message)])
                self.errors_table.set_cell([(index,4,get_error_message(error['code']))])
        else:
            try:
                del self.errors_table
            except:
                pass

            if self.parse_result['names']['vars']:
                self.vars_table = Table()
                self.vars_table.insert_column([(i,var_name) for i,var_name in enumerate(sorted(self.parse_result['names']['vars']))])
            else:
                try:
                    del self.vars_table
                except:
                    pass

            if self.parse_result['names']['vals']:
                self.vals_table = Table()
                self.vals_table.insert_column([(i,val_name) for i,val_name in enumerate(sorted(self.parse_result['names']['vals']))])
            else:
                try:
                    del self.vals_table
                except:
                    pass

        self.mod_time = os.path.getmtime(self.tpy_file_path)

    def get_line(self, index):
        arr = self.parse_result['line_start_indexes']
        low, high = 0, len(arr) - 1
        result = None

        while low <= high:
            mid = (low + high) // 2
            if arr[mid] >= index:
                result = mid
                high = mid - 1
            else:
                low = mid + 1

        return result