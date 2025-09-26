from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import json
import re
import os

from error_messages import get_error_message
from safeIO import saferead,safewrite
from cacher import Cacher
from table import Table

import highennabackend

class TpyFile:
    def __init__(self,dictionary,tpy_file_path):
        self.dictionary = {'tpy_file':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.tpy_file_path = tpy_file_path
        self.tpy_file_name = os.path.basename(tpy_file_path)

        p = r'((?:\d+\.)+\d+)'
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

        self.mod_time = 0

        self.start_up()

    def load_file(self, is_update):

        with open(self.tpy_file_path,'rb') as f:
            self.file_content = f.read().replace(b'\r',b'')

        self.mod_time = os.path.getmtime(self.tpy_file_path)

        self.result_parse = highennabackend.parse(self.file_content)

        if not is_update:
            def reader():
                stream = b''.join([self.file_content[start:end] for _,start,end in self.result_parse['cache']['lines']])
                if stream:
                    # return highennabackend.decode(stream).decode(encoding="utf-8")
                    return stream.decode(encoding="utf-8")
                return '{}'

            def writer(file_path,serialization):
                start,end = self.result_parse['cache']['location']
                length = len(self.file_content)
                # stream = highennabackend.encode(serialization.encode(encoding="utf-8"))
                stream = serialization.encode(encoding="utf-8")
                rewrite = self.file_content[:start]+\
                    "R'''\n$$$\n".encode()+\
                    b'\n'.join(stream[i:i+126] for i in range(0, len(stream), 126))+\
                    "\n$$$\n'''\n".encode()+\
                    self.file_content[end:]
                safewrite('wb',file_path,rewrite)
                self.mod_time = os.path.getmtime(self.tpy_file_path)


            self.file_cache = Cacher(self.tpy_file_path,
                    reader=reader,
                    writer=writer
                )

            if self.result_parse['cache']['found']:
                if 'highenna_version' in self.file_cache:
                    if self.file_cache['highenna_version']=='2.0.0':
                        if 'table_data' in self.file_cache:
                            self.scripts_table.column_names = self.file_cache['table_data']['scripts_table']['column_names']
                            self.scripts_table.data = self.file_cache['table_data']['scripts_table']['data']
                            self.vars_table.column_names = self.file_cache['table_data']['vars_table']['column_names']
                            self.vars_table.data = self.file_cache['table_data']['vars_table']['data']
                            self.vals_table.column_names = self.file_cache['table_data']['vals_table']['column_names']
                            self.vals_table.data = self.file_cache['table_data']['vals_table']['data']

                else:
                    pass
            else:
                self.file_content += b'\n\n'
                start,end = self.result_parse['cache']['location']
                self.result_parse['cache']['location'] = (start+2,end+2)
                self.file_cache['highenna_version'] = '2.0.0'


        self.tree = self.result_parse['tree']

        self.errors_table.clear()

        rows_to_insert = []
        cells_to_set = []
        for index,error in enumerate(self.result_parse['errors']):

            line,s,e = error['location'];
            ls = self.result_parse['line_start_indexes'][line-1]
            le = self.result_parse['line_start_indexes'][line]-1
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
                (index, 1, 'Syntax'),
                (index, 2, str(line)),
                (index, 3, str(col)),
                (index, 4, str(line_message)),
                (index, 5, str(get_error_message(error['code']))),
            ])

        self.errors_table.insert_row(rows_to_insert)
        self.errors_table.set_cell(cells_to_set)

        if not self.scripts_table.column_names:
            self.scripts_table.column_names = ['Script Names']
            self.scripts_table.data = [[self.default_script_name]]

        if self.result_parse['names']['vars']:
            new_vars = [var for var in self.result_parse['names']['vars'] if not var in self.vars_table.column_names]
            length = len(self.vars_table.column_names)
            self.vars_table.insert_column([(length+i,var_name) for i,var_name in enumerate(sorted(new_vars))])
            self.vars_table.delta_to_saved_version -= 1 if not is_update else 0
            self.vars_table.undo_stack.clear()

        if self.result_parse['names']['vals']:
            new_vals = [val for val in self.result_parse['names']['vals'] if not val in self.vals_table.column_names]
            length = len(self.vals_table.column_names)
            self.vals_table.insert_column([(length+i,val_name) for i,val_name in enumerate(sorted(new_vals))])
            self.vals_table.delta_to_saved_version -= 1 if not is_update else 0
            self.vals_table.undo_stack.clear()

    def save(self):
        self.file_cache.disable_sync()

        self.file_cache['table_data']['scripts_table']['column_names'] = self.scripts_table.column_names
        self.file_cache['table_data']['scripts_table']['data'] = self.scripts_table.data
        self.scripts_table.delta_to_saved_version = 0

        self.file_cache['table_data']['vars_table']['column_names'] = self.vars_table.column_names
        self.file_cache['table_data']['vars_table']['data'] = self.vars_table.data
        self.vars_table.delta_to_saved_version = 0

        self.file_cache['table_data']['vals_table']['column_names'] = self.vals_table.column_names
        self.file_cache['table_data']['vals_table']['data'] = self.vals_table.data
        self.vals_table.delta_to_saved_version = 0
        
        self.file_cache.enable_sync()

    def has_unsaved_changes(self):
        return any([
                self.scripts_table.delta_to_saved_version != 0,
                self.vars_table.delta_to_saved_version != 0,
                self.vals_table.delta_to_saved_version != 0,
            ])

    def update_modules(self):
        self.file_cache.disable_sync()
        
        project_modules_path = self.project.modules_path
        uuid_to_name = self.project.uuid_to_name

        project_module_timestamps = self.project.project_cache['modules']['module_timestamps']
        project_module_assignment = self.project.project_cache['modules']['module_assignments'][self.tpy_file_name]
        
        self_module_timestamps   = self.file_cache['modules']['module_timestamps']
        self_module_assignment   = self.file_cache['modules']['module_assignment']
        self_module_uuid_to_name = self.file_cache['modules']['module_uuid_to_name']
        
        for module_uuid in list(self_module_assignment.keys()):
            if module_uuid not in project_module_assignment:
                print(self.tpy_file_name,'deleted',module_uuid)
                self_module_assignment.pop(module_uuid,None)
                self_module_timestamps.pop(module_uuid,None)
                self_module_uuid_to_name.pop(module_uuid,None)

        for module_uuid in project_module_assignment:
            project_module_timestamp = project_module_timestamps[module_uuid]
            module_name = uuid_to_name[module_uuid]

            if not module_name == self_module_uuid_to_name.get(module_uuid,None):
                self_module_uuid_to_name[module_uuid] = module_name

            read = (module_uuid not in self_module_assignment or
                    project_module_timestamp[1] > self_module_timestamps[module_uuid][1])

            if read:
                print(self.tpy_file_name,'read',module_uuid)
                self_module_timestamps[module_uuid] = project_module_timestamp
                with open(os.path.join(project_modules_path, module_name), 'r', encoding='utf-8') as m:
                    self_module_assignment[module_uuid] = m.read()

        self.file_cache.enable_sync()

    def remove_obsolete(self):

        obsolete_vars = [(i,) for i,var in enumerate(self.vars_table.column_names)
                         if var not in self.result_parse['names']['vars']]
        obsolete_vals = [(i,) for i,val in enumerate(self.vals_table.column_names)
                         if val not in self.result_parse['names']['vals']]

        if obsolete_vars:
            self.vars_table.remove_column(obsolete_vars)
        if obsolete_vals:
            self.vals_table.remove_column(obsolete_vals)

    def start_up(self):
        self.load_file(is_update=False)

    def update(self):
        self.load_file(is_update=True)
