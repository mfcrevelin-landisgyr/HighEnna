from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os

from error_messages import get_error_message
from tpy_file import TpyFile
from cacher import Cacher

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
        
        # Open Tpy Files
        for entry in os.listdir(project_path):
            entry_path = os.path.join(project_path,entry)
            if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                self.tpy_files[entry] = TpyFile(self.dictionary, entry_path)

        self.is_open = True

    def close(self):
        if not self.is_open:
            return

        self.tpy_files.clear()

        self.project_cache = None
        self.project_path = None
        self.project_name = None

        self.is_open = False

    def update(self):
        changed = False

        for entry in [entry for entry in self.tpy_files.keys() if not os.path.exists(os.path.join(self.project_path, entry))]:
            del self.tpy_files[entry]
            changed = True

        for entry in sorted(os.listdir(self.project_path)):
            entry_path = os.path.join(self.project_path,entry)
            if entry in self.tpy_files:
                if os.path.getmtime(entry_path) > self.tpy_files[entry].mod_time:
                    self.tpy_files[entry].update()
                    changed = True
            else:
                if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                    self.tpy_files[entry] = TpyFile(self.dictionary, entry_path)
                    changed = True

        return changed