from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from error_messages import get_error_message
from tpy_file import TpyFile
from cacher import Cacher

import random
import re
import os

chars = [chr(ord('A')+i) for i in range(26)]+[chr(ord('0')+i) for i in range(10)]
def UUID():
    part1 = ''.join(random.choice(chars) for _ in range(4))
    part2 = ''.join(random.choice(chars) for _ in range(4))
    part3 = ''.join(random.choice(chars) for _ in range(4))
    part4 = ''.join(random.choice(chars) for _ in range(4))
    return f"{part1}-{part2}-{part3}-{part4}"

class Project:
    def __init__(self):
        self.dictionary = {"project":self}
        self.__dict__.update(self.dictionary)

        self.project_cache = None
        self.project_path = None
        self.project_name = None
    
        self.tpy_files = {}

        self.is_open = False

    # ---- Slots ----
    
    def open(self, project_path):
        if self.is_open:
            self.close()

        self.project_path = project_path
        self.project_name = os.path.basename(project_path)
        self.project_cache = Cacher(os.path.join(project_path,".project_cache"))
        
        self.project_cache["modules"].setdefault('modules_set',set())
        self.modules_path = os.path.join(self.project_path,"Modules")
        self.modules_mod_time = 0
        self.uuid_to_name={}
        self.name_to_uuid={}
        self.update_modules_dir()

        for entry in os.listdir(project_path):
            entry_path = os.path.join(project_path,entry)
            if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                self.tpy_files[entry] = TpyFile(self.dictionary, entry_path)
                self.project_cache["modules"]['modules_assigment'].setdefault(entry,self.project_cache["modules"]['modules_set'].copy())

        for entry in [entry for entry in self.project_cache["modules"]['modules_assigment'].keys() if entry not in self.tpy_files.keys()] :
            self.project_cache["modules"]['modules_assigment'].pop(entry,None)

        self.is_open = True

    def close(self):
        if not self.is_open:
            return

        self.tpy_files.clear()
        self.uuid_to_name.clear()
        self.name_to_uuid.clear()

        self.modules_mod_time = 0
        self.modules_path = None

        self.project_cache = None
        self.project_path = None
        self.project_name = None

        self.is_open = False

    def update(self):
        changed = False

        for entry in [entry for entry in self.tpy_files.keys() if not os.path.exists(os.path.join(self.project_path, entry))]:
            del self.tpy_files[entry]
            self.project_cache["modules"]['modules_assigment'].pop(entry,None)
            changed = True

        self.update_modules_dir()

        for entry in sorted(os.listdir(self.project_path)):
            entry_path = os.path.join(self.project_path,entry)
            if entry in self.tpy_files:
                if os.path.getmtime(entry_path) > self.tpy_files[entry].mod_time:
                    self.tpy_files[entry].update()
                    changed = True
            else:
                if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                    self.tpy_files[entry] = TpyFile(self.dictionary, entry_path)
                    self.project_cache["modules"]['modules_assigment'].setdefault(entry,self.project_cache["modules"]['modules_set'])
                    changed = True

        return changed

    def update_modules_dir(self):
        if os.path.isdir(self.modules_path):

            modules_mod_time = os.path.getmtime(self.modules_path)
            if  modules_mod_time > self.modules_mod_time:
                self.modules_mod_time = modules_mod_time
                
                self.uuid_to_name.clear()
                self.name_to_uuid.clear()

                module_files = [
                    (file_name, file_path)
                    for file_name in os.listdir(self.modules_path)
                    if os.path.isfile(file_path := os.path.join(self.modules_path, file_name)) and file_name.endswith('py')
                ]
                
                collected_timestamps = {}
                for file_name,file_path in module_files:
                    with open(file_path,'r') as f:
                        file_content = f.read()

                    match = re.search(r"# *MODULE_ID *: *([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})",file_content)
                    if match:
                        file_uuid = match.group(1)
                    else:

                        file_uuid = UUID()
                        while file_uuid in self.project_cache["modules"]['modules_set']:
                            file_uuid = UUID()

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"# MODULE_ID: {file_uuid}\n\n{file_content}")

                    collected_timestamps[file_uuid] = os.path.getmtime(file_path)
                    
                    self.uuid_to_name[file_uuid] = file_name
                    self.name_to_uuid[file_name] = file_uuid
                
                collected_uuids = set(collected_timestamps.keys())
                old_uuids = self.project_cache["modules"]['modules_set']

                new_uuids = collected_uuids - old_uuids
                removed_uuids = old_uuids - collected_uuids

                # for uuid, timestamp in collected_timestamps.items():
                #     if uuid in new_uuids:
                #         self.load(uuid)
                #     else:
                #         if uuid not in self.project_cache["modules"]['module_timestamps']:
                #             self.remove(uuid)
                #         elif timestamp > self.project_cache["modules"]['module_timestamps'][uuid]:
                #             self.load(uuid)

                self.project_cache["modules"]['modules_set'] = collected_uuids
                self.project_cache["modules"]['module_timestamps'] = collected_timestamps

                for tpy_file_assignment in self.project_cache["modules"]['modules_assigment'].values():
                    tpy_file_assignment.intersection_update(collected_uuids)
                    tpy_file_assignment.update(new_uuids)

        else:
            os.makedirs(self.modules_path, exist_ok=True)
            self.modules_mod_time = os.path.getmtime(self.modules_path)