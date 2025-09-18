from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import json
import re
import os

from error_messages import get_error_message
from cacher import Cacher
from table import Table

import highennabackend

from time import time

class TpyFile:
    def __init__(self,dictionary,tpy_file_path):
        self.dictionary = {'tpy_file':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.tpy_file_path = tpy_file_path
        self.tpy_file_name = os.path.basename(tpy_file_path)

        p = r"((?:\d+\.)+\d+)"
        if re.search(p,self.tpy_file_name):
            self.default_script_name = re.sub(p,r'\1.{script_index}',self.tpy_file_name)
        else:
            self.default_script_name = re.sub(r'(\.\w+$)', r'.{script_index}\1', self.tpy_file_name)
        self.default_script_name = self.default_script_name.replace('.tpy','.py')

        self.scripts_table = Table(default_text=self.default_script_name)
        self.vars_table = Table()
        self.vals_table = Table()
        self.errors_table = Table(allow_empty=True)
        self.errors_table.insert_column([(0,'Error Code'),(1,'Error Type'),(2,'Lin'),(3,'Col'),(4,'Content'),(5,'What')])

        self.start_up()

    def load_file(self, is_update):
        with open(self.tpy_file_path,'rb') as f:
            self.file_content = f.read().replace(b'\r',b'')

        self.mod_time = os.path.getmtime(self.tpy_file_path)

        self.parse_result = highennabackend.parse(self.file_content)

        if not is_update:
            def reader():
                stream = b''.join([self.file_content[start:end] for _,start,end in self.parse_result['cache']['lines']])
                if stream:
                    return highennabackend.decode(stream).decode()
                return '{}'

            def writer(file_path,serialization):
                start,end = self.parse_result['cache']['location']
                length = len(self.file_content)
                stream = highennabackend.encode(serialization.encode())
                with open(file_path,'wb') as f:
                    f.write(
                            self.file_content[:start]+
                            "R'''\n$$$\n".encode()+
                            b'\n'.join(stream[i:i+126] for i in range(0, len(stream), 126))+
                            "\n$$$\n'''\n".encode()+
                            self.file_content[end:]
                        )
                self.mod_time = os.path.getmtime(self.tpy_file_path)


            self.file_cache = Cacher(self.tpy_file_path,
                    reader=reader,
                    writer=writer
                )

            if self.parse_result['cache']['found']:
                if 'highenna_version' in self.file_cache:
                    if self.file_cache['highenna_version']=='2.0.0':
                        if 'table_data' in self.file_cache:
                            self.scripts_table.column_names = self.file_cache['table_data']['scripts_table']["column_names"]
                            self.scripts_table.data = self.file_cache['table_data']['scripts_table']["data"]
                            self.vars_table.column_names = self.file_cache['table_data']['vars_table']["column_names"]
                            self.vars_table.data = self.file_cache['table_data']['vars_table']["data"]
                            self.vals_table.column_names = self.file_cache['table_data']['vals_table']["column_names"]
                            self.vals_table.data = self.file_cache['table_data']['vals_table']["data"]

                else:
                    pass
            else:
                self.file_content += b'\n\n'
                start,end = self.parse_result['cache']['location']
                self.parse_result['cache']['location'] = (start+2,end+2)
                self.file_cache['highenna_version'] = "2.0.0"


        self.tree = self.parse_result['tree']

        self.errors_table.clear()

        rows_to_insert = []
        cells_to_set = []
        for index,error in enumerate(self.parse_result["errors"]):

            line,s,e = error['location'];
            ls = self.parse_result['line_start_indexes'][line-1]
            le = self.parse_result['line_start_indexes'][line]-1
            col = s - ls + 1

            line_prefix = ' '*len(self.file_content[ls:s].decode())
            line_middle = '^'*len(self.file_content[s:e].decode())
            line_postfix = ' '*len(self.file_content[e:le].decode())
            line_message = (
                    self.file_content[ls:le].decode()
                    + '\n'
                    + line_prefix
                    + line_middle
                    + line_postfix
                )

            rows_to_insert.append((index,))
            cells_to_set.extend([
                (index, 0, str(error['code'])),
                (index, 1, "Syntax"),
                (index, 2, str(line)),
                (index, 3, str(col)),
                (index, 4, str(line_message)),
                (index, 5, str(get_error_message(error['code']))),
            ])

        self.errors_table.insert_row(rows_to_insert)
        self.errors_table.set_cell(cells_to_set)

        if not self.scripts_table.column_names:
            self.scripts_table.column_names = ["Script Names"]
            self.scripts_table.data = [[self.default_script_name]]

        if self.parse_result['names']['vars']:
            new_vars = [var for var in self.parse_result['names']['vars'] if not var in self.vars_table.column_names]
            length = len(self.vars_table.column_names)
            self.vars_table.insert_column([(length+i,var_name) for i,var_name in enumerate(sorted(new_vars))])
            self.vars_table.undo_stack.clear()

        if self.parse_result['names']['vals']:
            new_vals = [val for val in self.parse_result['names']['vals'] if not val in self.vals_table.column_names]
            length = len(self.vals_table.column_names)
            self.vals_table.insert_column([(length+i,val_name) for i,val_name in enumerate(sorted(new_vals))])
            self.vals_table.undo_stack.clear()

    def save(self):
        self.file_cache['table_data']['scripts_table']["column_names"] = self.scripts_table.column_names
        self.file_cache['table_data']['scripts_table']["data"] = self.scripts_table.data

        self.file_cache['table_data']['vars_table']["column_names"] = self.vars_table.column_names
        self.file_cache['table_data']['vars_table']["data"] = self.vars_table.data

        self.file_cache['table_data']['vals_table']["column_names"] = self.vals_table.column_names
        self.file_cache['table_data']['vals_table']["data"] = self.vals_table.data

    def remove_obsolete(self):

        obsolete_vars = [(i,) for i,var in enumerate(self.vars_table.column_names)
                         if var not in self.parse_result['names']['vars']]
        obsolete_vals = [(i,) for i,val in enumerate(self.vals_table.column_names)
                         if val not in self.parse_result['names']['vals']]

        if obsolete_vars:
            self.vars_table.remove_column(obsolete_vars)
        if obsolete_vals:
            self.vals_table.remove_column(obsolete_vals)

    def start_up(self):
        self.load_file(is_update=False)

    def update(self):
        self.load_file(is_update=True)
