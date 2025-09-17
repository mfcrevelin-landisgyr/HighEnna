from collections import deque
import json
import os

class Cacher(dict):
    def __init__(self,file_path, *, reader=None, writer=None, attributes={}):
        self.file_path = os.path.abspath(file_path)
        self.__dict__.update(attributes)

        if reader:
            self.read = reader
        else:
            def defaultReader(cacher):
                with open(cacher.file_path, 'r') as f:
                    data = json.load(f)
                return data
            self.read = defaultReader


        if writer:
            self.write = writer
        else:
            def defaultWriter(cacher):
                os.makedirs(os.path.dirname(cacher.file_path), exist_ok=True)
                with open(cacher.file_path, 'w') as f:
                    json.dump(cacher, f, indent=2)
            self.write = defaultWriter


        data={}
        if os.path.isfile(self.file_path):
            data = self.wrap_item(self.read(self))

        super().__init__(data)


    def wrap_item(self, v):
        if isinstance(v, dict):
            return Cacher.WrappedDict(self, v)
        elif isinstance(v, list):
            return Cacher.WrappedList(self, v)
        else:
            return v

    def unwrap_item(self, v):
        if isinstance(v, Cacher.WrappedDict):
            return {sk:self.unwrap_item(sv) for sk,sv in v}
        elif isinstance(v, Cacher.WrappedList):
            return [self.unwrap_item(sv) for sv in v]
        else:
            return v

    def copy(self):
        return {sk:self.unwrap_item(sv) for sk,sv in self.items()}

    def save(self):
        self.write(self)

    def __getitem__(self, k):
        if not k in self.keys():
            self[k] = Cacher.WrappedDict(self,{})
        return super().__getitem__(k)

    def __setitem__(self, k, v):
        super().__setitem__(k, self.wrap_item(v))
        self.save()

    def __delitem__(self, k):
        super().__delitem__(k)
        self.save()

    def clear(self):
        super().clear()
        self.save()

    def pop(self, k, *args):
        val = super().pop(k, *args)
        self.save()
        return val

    def popitem(self):
        val = super().popitem()
        self.save()
        return val

    def update(self, *args, **kwargs):
        wrapped_args = []
        for mapping in args:
            wrapped_args.append({k: self.wrap_item(v) for k, v in mapping.items()})
        wrapped_kwargs = {k: self.wrap_item(v) for k, v in kwargs.items()}
        super().update(*wrapped_args, **wrapped_kwargs)
        self.save()

    def setdefault(self, k, default=None):
        val = super().setdefault(k, self.wrap_item(default))
        self.save()
        return val

    class WrappedList(list):
        def __init__(self, parent, iterable=()):
            super().__init__([self.wrap_item(v) for v in iterable])
            self.parent = parent

        def wrap_item(self, v):
            if isinstance(v, dict):
                return Cacher.WrappedDict(self, v)
            elif isinstance(v, list):
                return Cacher.WrappedList(self, v)
            else:
                return v

        def unwrap_item(self, v):
            if isinstance(v, Cacher.WrappedDict):
                return {sk:self.unwrap_item(sv) for sk,sv in v}
            elif isinstance(v, Cacher.WrappedList):
                return [self.unwrap_item(sv) for sv in v]
            else:
                return v

        def copy(self):
            return [self.unwrap_item(sv) for sv in self]

        def save(self):
            self.parent.save()

        def append(self, item):
            super().append(self.wrap_item(item))
            self.parent.save()

        def extend(self, iterable):
            super().extend(self.wrap_item(iterable))
            self.parent.save()

        def insert(self, index, item):
            super().insert(index, self.wrap_item(item))
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

        def __setitem__(self, index, v):
            super().__setitem__(index, self.wrap_item(v))
            self.parent.save()

        def __delitem__(self, index):
            super().__delitem__(index)
            self.parent.save()

    class WrappedDict(dict):
        def __init__(self, parent, mapping=(), **kwargs):
            super().__init__({k: self.wrap_item(v) for k,v in mapping.items()}, **kwargs)
            self.parent = parent

        def wrap_item(self, v):
            if isinstance(v, dict):
                return Cacher.WrappedDict(self, v)
            elif isinstance(v, list):
                return Cacher.WrappedList(self, v)
            else:
                return v

        def unwrap_item(self, v):
            if isinstance(v, Cacher.WrappedDict):
                return {sk:self.unwrap_item(sv) for sk,sv in v}
            elif isinstance(v, Cacher.WrappedList):
                return [self.unwrap_item(sv) for sv in v]
            else:
                return v

        def copy(self):
            return {sk:self.unwrap_item(sv) for sk,sv in self.items()}

        def save(self):
            self.parent.save()

        def __getitem__(self, k):
            return self.setdefault(k, Cacher.WrappedDict(self,{}))

        def __setitem__(self, k, v):
            super().__setitem__(k, self.wrap_item(v))
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
            wrapped_args = []
            for mapping in args:
                wrapped_args.append({k: self.wrap_item(v) for k, v in mapping.items()})
            wrapped_kwargs = {k: self.wrap_item(v) for k, v in kwargs.items()}
            super().update(*wrapped_args, **wrapped_kwargs)
            self.parent.save()

        def setdefault(self, k, default=None):
            val = super().setdefault(k, self.wrap_item(default))
            self.parent.save()
            return val