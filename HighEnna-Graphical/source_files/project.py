from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from error_messages import get_error_message
from safeIO import saferead,safewrite
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

        self.project_cache.disable_sync()
        
        self.project_cache["modules"].setdefault('modules_set',set())
        self.modules_path = os.path.join(self.project_path,"Modules")
        self.modules_mod_time = 0
        self.uuid_to_name={}
        self.name_to_uuid={}

        self.update_modules()

        uuid_name_pattern = re.compile(r"\([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\)")
        for entry in os.listdir(project_path):
            entry_path = os.path.join(project_path,entry)
            if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                self.tpy_files[entry] = TpyFile(self.dictionary, entry_path)
                self.project_cache["modules"]['module_assignments'].setdefault(entry,self.project_cache["modules"]['modules_set'].copy())
                self.project_cache["modules"]['module_assignments'][entry].update(self.tpy_files[entry].file_cache['modules']['module_assignment'])
                for module_uuid in self.tpy_files[entry].file_cache['modules']['module_assignment']:
                    if not module_uuid in self.project_cache["modules"]['modules_set']:
                        module_name = uuid_name_pattern.sub(f"({module_uuid})",self.tpy_files[entry].file_cache['modules']['module_uuid_to_name'][module_uuid])
                        module_path = os.path.join(self.modules_path, module_name)
                        if os.path.isfile(module_path):
                            base,ext = os.path.splitext(module_name)
                            module_name = f"{base}({module_uuid}){ext}"
                            module_path = os.path.join(self.modules_path, module_name)
                        safewrite('w',module_path,self.tpy_files[entry].file_cache['modules']['module_assignment'][module_uuid])

                        timestamp = (os.path.getctime(module_path),os.path.getmtime(module_path))
                        self.modules_mod_time = max(self.modules_mod_time, timestamp[1])

                        self.uuid_to_name[module_uuid] = module_name
                        self.name_to_uuid[module_name] = module_uuid

                        self.project_cache["modules"]['modules_set'].add(module_uuid)
                        self.project_cache["modules"]['module_timestamps'][module_uuid] = timestamp
                        print(entry,'written',module_uuid)

                self.tpy_files[entry].update_modules()

        for entry in [entry for entry in self.project_cache["modules"]['module_assignments'].keys() if entry not in self.tpy_files.keys()] :
            self.project_cache["modules"]['module_assignments'].pop(entry,None)

        self.project_cache.enable_sync()

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
        self.project_cache.disable_sync()

        tpy_changed = False

        for entry in [entry for entry in self.tpy_files.keys() if not os.path.exists(os.path.join(self.project_path, entry))]:
            del self.tpy_files[entry]
            self.project_cache["modules"]['module_assignments'].pop(entry,None)
            tpy_changed = True

        module_change = self.update_modules()

        for entry in sorted(os.listdir(self.project_path)):
            entry_path = os.path.join(self.project_path,entry)
            if entry in self.tpy_files:
                if os.path.getmtime(entry_path) > self.tpy_files[entry].mod_time:
                    self.tpy_files[entry].update()
                    tpy_changed = True
            else:
                if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                    self.tpy_files[entry] = TpyFile(self.dictionary, entry_path)
                    self.project_cache["modules"]['module_assignments'].setdefault(entry,self.project_cache["modules"]['modules_set'].copy())
                    self.tpy_files[entry].update_modules()
                    tpy_changed = True

        self.project_cache.enable_sync()
        return tpy_changed, module_change

    def update_modules(self):
        module_change = False

        if os.path.isdir(self.modules_path):

            module_files = {
                file_name : file_path
                for file_name in os.listdir(self.modules_path)
                if os.path.isfile(file_path := os.path.join(self.modules_path, file_name)) and file_name.endswith('py')
            }
            modules_mod_time = max([
                    os.path.getmtime(self.modules_path),
                    *[os.path.getmtime(module_path) for module_path in module_files.values()]
                ])
            if  modules_mod_time > self.modules_mod_time:
                self.modules_mod_time = modules_mod_time

                self.uuid_to_name.clear()
                self.name_to_uuid.clear()

                uuid_name_pattern = re.compile(r"\([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\)")
                uuid_pattern = re.compile(r"# *MODULE_ID *: *([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})")

                collected_timestamps = {}
                for file_name,file_path in module_files.items():

                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()

                    file_timestamps = (
                            os.path.getctime(file_path),
                            os.path.getmtime(file_path)
                        )

                    match = uuid_pattern.search(file_content)
                    if match:
                        file_uuid = match.group(1)
                        if file_uuid in collected_timestamps:
                            other_timestamps = collected_timestamps[file_uuid]

                            new_uuid = UUID()
                            while new_uuid in self.project_cache["modules"]['modules_set']:
                                new_uuid = UUID()

                            if other_timestamps < file_timestamps:
                                file_uuid = new_uuid
                                safewrite('w',file_path,uuid_pattern.sub(f"# MODULE_ID: {file_uuid}", file_content))

                                collected_timestamps[file_uuid] = (
                                        os.path.getctime(file_path),
                                        os.path.getmtime(file_path)
                                    )
                                modules_mod_time = max(modules_mod_time, collected_timestamps[file_uuid][1])
                            else:
                                other_uuid = new_uuid
                                other_name = self.uuid_to_name[file_uuid]
                                other_path = module_files[other_name]

                                with open(other_path, 'r', encoding='utf-8') as f:
                                    other_content = f.read()
                                
                                safewrite('w',other_path,uuid_pattern.sub(f"# MODULE_ID: {other_uuid}", other_content))

                                collected_timestamps[other_uuid] = (
                                        os.path.getctime(other_path),
                                        os.path.getmtime(other_path)
                                    )
                                modules_mod_time = max(modules_mod_time, collected_timestamps[other_uuid][1])

                                self.uuid_to_name[other_uuid] = other_name
                                self.name_to_uuid[other_name] = other_uuid

                    else:
                        file_uuid = UUID()
                        while file_uuid in self.project_cache["modules"]['modules_set']:
                            file_uuid = UUID()
                        safewrite('w',file_path,f"# MODULE_ID: {file_uuid}\n\n{file_content}")

                    collected_timestamps[file_uuid] = file_timestamps

                    self.uuid_to_name[file_uuid] = file_name
                    self.name_to_uuid[file_name] = file_uuid


                collected_uuids = set(collected_timestamps.keys())
                old_uuids = self.project_cache["modules"]['modules_set']

                new_uuids = collected_uuids - old_uuids
                del_uuids = old_uuids - collected_uuids

                if new_uuids or del_uuids:
                    module_change = True

                self.project_cache["modules"]['modules_set'] = collected_uuids
                self.project_cache["modules"]['module_timestamps'] = collected_timestamps

                for tpy_file_key,tpy_file_assignment in self.project_cache["modules"]['module_assignments'].items():
                    tpy_file_assignment.difference_update(del_uuids)
                    tpy_file_assignment.update(new_uuids)

                for tpy_file in self.tpy_files.values():
                    tpy_file.update_modules()
        else:
            os.makedirs(self.modules_path, exist_ok=True)
            self.modules_mod_time = os.path.getmtime(self.modules_path)

        return module_change