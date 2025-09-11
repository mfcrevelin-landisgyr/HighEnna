from collections import deque
import json
import os

class Cacher:
    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        self.data = {}
        if os.path.isfile(self.file_path):
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
        for k, v in list(self.data.items()):
            if isinstance(v, dict):
                self.data[k] = Cacher.WrappedDict(self, v)
            elif isinstance(v, list):
                self.data[k] = Cacher.WrappedList(self, v)

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = Cacher.WrappedDict(self, value)
        elif isinstance(value, list):
            value = Cacher.WrappedList(self, value)
        self.data[key] = value
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    class WrappedList(list):
        def __init__(self, parent, iterable=()):
            super().__init__(self._wrap_items(iterable))
            self.parent = parent

        @staticmethod
        def _wrap_items(iterable):
            wrapped = []
            for i, item in enumerate(iterable):
                if isinstance(item, dict):
                    wrapped.append(Cacher.WrappedDict(self, item))
                elif isinstance(item, list):
                    wrapped.append(Cacher.WrappedList(self, item))
                else:
                    wrapped.append(item)
            return wrapped

        def save(self):
            self.parent.save()

        def append(self, item):
            if isinstance(item, dict):
                super().append(Cacher.WrappedDict(self, item))
            elif isinstance(item, list):
                super().append(Cacher.WrappedList(self, item))
            else:
                super().append(item)
            self.parent.save()

        def extend(self, iterable):
            super().extend(self._wrap_items(iterable))
            self.parent.save()

        def insert(self, index, item):
            if isinstance(item, dict):
                super().insert(index, Cacher.WrappedDict(self, item))
            elif isinstance(item, list):
                super().insert(index, Cacher.WrappedList(self, item))
            else:
                super().insert(index, item)
            self.parent.save()

        def remove(self, item):
            super().remove(item)
            self.parent.save()

        def pop(self, index=-1):
            result = super().pop(index)
            self.parent.save()
            return result

        def clear(self):
            super().clear()
            self.parent.save()

        def sort(self, *args, **kwargs):
            super().sort(*args, **kwargs)
            self.parent.save()

        def reverse(self):
            super().reverse()
            self.parent.save()

        def __setitem__(self, index, value):
            if isinstance(value, dict):
                super().__setitem__(index, Cacher.WrappedDict(self, value))
            elif isinstance(value, list):
                super().__setitem__(index, Cacher.WrappedList(self, value))
            else:
                super().__setitem__(index, value)
            self.parent.save()

        def __delitem__(self, index):
            super().__delitem__(index)
            self.parent.save()

    class WrappedDict(dict):
        def __init__(self, parent, mapping=(), **kwargs):
            super().__init__(self._wrap_items(mapping), **kwargs)
            self.parent = parent

        @staticmethod
        def _wrap_items(mapping):
            wrapped = {}
            for k, v in mapping.items():
                if isinstance(v, dict):
                    wrapped[k] = Cacher.WrappedDict(self, v)
                elif isinstance(v, list):
                    wrapped[k] = Cacher.WrappedList(self, v)
                else:
                    wrapped[k] = v
            return wrapped

        def save(self):
            self.parent.save()

        def __setitem__(self, k, v):
            super().__setitem__(k, v)
            self.parent.save()

        def __delitem__(self, k):
            super().__delitem__(k)
            self.parent.save()

        def clear(self):
            super().clear()
            self.parent.save()

        def pop(self, k, *args):
            val = super().pop(k, *args)
            self.parent.save()
            return val

        def popitem(self):
            val = super().popitem()
            self.parent.save()
            return val

        def update(self, *args, **kwargs):
            super().update(*args, **kwargs)
            self.parent.save()

        def setdefault(self, k, default=None):
            if isinstance(default, dict):
                super().setdefault(k, Cacher.WrappedDict(self, default))
            elif isinstance(default, list):
                super().setdefault(k, Cacher.WrappedList(self, default))
            else:
                super().setdefault(k, default)
            self.parent.save()
            return val