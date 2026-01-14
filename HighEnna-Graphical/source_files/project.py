from error_messages import get_error_message
from safeIO import saferead,safewrite
from scenario_file import ScenarioFile
from cacher import Cacher

import random
import re
import os

def upper_camel_case(s):
    return ''.join(word.capitalize() for word in re.split(r'[^\w]+', s))

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

        self.scenario_files = {}

        self.is_open = False

    # ---- Slots ----

    def open(self, project_path, force=False):
        if self.is_open:
            if self.project_path == os.path.abspath(project_path):
                return True
            self.close()

        for file in os.listdir(project_path):
            if file.endswith(".heproj"):
                heproj_file = file
                break
        else:
            project_cache_name = upper_camel_case(os.path.basename(project_path))
            heproj_file = f"{project_cache_name}.heproj"
        self.project_cache = Cacher(os.path.join(project_path,heproj_file))

        self.project_cache.setdefault('is_open',False)
        if self.project_cache['is_open'] and not force:
            self.project_cache = None
            return False
            
        self.project_path = project_path
        self.project_name = os.path.basename(project_path)

        self.project_cache.disable_sync()
        
        if not os.path.isdir(self.project_cache.get('render_dir','')):
            self.project_cache['render_dir'] = os.path.join(self.project_path,'scripts')
        self.project_cache["modules"].setdefault('modules_set',set())
        self.modules_path = os.path.join(self.project_path,"Modules")
        self.modules_mod_time = 0
        self.uuid_to_name={}
        self.name_to_uuid={}

        self.update_modules()

        uuid_name_pattern = re.compile(r"\([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\)")
        for entry in os.listdir(project_path):
            entry_path = os.path.join(project_path,entry)
            if os.path.isfile(entry_path) and any([entry.endswith(ext) for ext in self.application_cache['extensions']]):
                self.scenario_files[entry] = ScenarioFile(self.dictionary, entry_path)
                self.project_cache["modules"]['module_assignments'].setdefault(entry,self.project_cache["modules"]['modules_set'].copy())
                self.project_cache["modules"]['module_assignments'][entry].update(self.scenario_files[entry].file_cache['modules']['module_assignment'])
                for module_uuid in self.scenario_files[entry].file_cache['modules']['module_assignment']:
                    if not module_uuid in self.project_cache["modules"]['modules_set']:
                        module_name = uuid_name_pattern.sub(f"({module_uuid})",self.scenario_files[entry].file_cache['modules']['module_uuid_to_name'][module_uuid])
                        module_path = os.path.join(self.modules_path, module_name)
                        if os.path.isfile(module_path):
                            base,ext = os.path.splitext(module_name)
                            module_name = f"{base}({module_uuid}){ext}"
                            module_path = os.path.join(self.modules_path, module_name)
                        safewrite('w',module_path,self.scenario_files[entry].file_cache['modules']['module_assignment'][module_uuid])

                        timestamp = (os.path.getctime(module_path),os.path.getmtime(module_path))
                        self.modules_mod_time = max(self.modules_mod_time, timestamp[1])

                        self.uuid_to_name[module_uuid] = module_name
                        self.name_to_uuid[module_name] = module_uuid

                        self.project_cache["modules"]['modules_set'].add(module_uuid)
                        self.project_cache["modules"]['module_timestamps'][module_uuid] = timestamp

                self.scenario_files[entry].update_modules()

        for entry in [entry for entry in self.project_cache["modules"]['module_assignments'].keys() if entry not in self.scenario_files.keys()] :
            self.project_cache["modules"]['module_assignments'].pop(entry,None)

        self.project_cache.enable_sync()

        self.is_open = True
        self.project_cache['is_open'] = True
        return True

    def close(self):
        if not self.is_open:
            return

        self.scenario_files.clear()
        self.uuid_to_name.clear()
        self.name_to_uuid.clear()

        self.modules_mod_time = 0
        self.modules_path = None

        self.project_cache['is_open'] = False
        self.project_cache = None
        self.project_path = None
        self.project_name = None

        self.is_open = False

    def update(self):
        if not self.is_open:
            return (False,False)

        self.project_cache.disable_sync()

        scenario_changed = False

        for entry in [entry for entry in self.scenario_files.keys() if not os.path.exists(os.path.join(self.project_path, entry))]:
            del self.scenario_files[entry]
            self.project_cache["modules"]['module_assignments'].pop(entry,None)
            scenario_changed = True

        module_change = self.update_modules()

        for entry in sorted(os.listdir(self.project_path)):
            entry_path = os.path.join(self.project_path,entry)
            if entry in self.scenario_files:
                if os.path.getmtime(entry_path) > self.scenario_files[entry].mod_time:
                    self.scenario_files[entry].update()
                    scenario_changed = True
            else:
                if os.path.isfile(entry_path) and any([entry.endswith(ext) for ext in self.application_cache['extensions']]):
                    self.scenario_files[entry] = ScenarioFile(self.dictionary, entry_path)
                    self.project_cache["modules"]['module_assignments'].setdefault(entry,self.project_cache["modules"]['modules_set'].copy())
                    self.scenario_files[entry].update_modules()
                    scenario_changed = True

        self.project_cache.enable_sync()
        return scenario_changed, module_change

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

                    with open(file_path, 'r') as f:
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

                                with open(other_path, 'r') as f:
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

                # for a in self.project_cache["modules"]['module_assignments'].items():
                for scenario_file_key,scenario_file_assignment in self.project_cache["modules"]['module_assignments'].items():
                    scenario_file_assignment.difference_update(del_uuids)
                    scenario_file_assignment.update(new_uuids)

                for scenario_file in self.scenario_files.values():
                    scenario_file.update_modules()
        else:
            os.makedirs(self.modules_path, exist_ok=True)
            self.modules_mod_time = os.path.getmtime(self.modules_path)

        return module_change