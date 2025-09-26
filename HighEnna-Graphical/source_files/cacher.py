from collections import deque
import json
import os

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Cacher.WrappedSet):
            return {"__set__": list(obj)}
        if isinstance(obj, tuple):
            return {"__tuple__": list(obj)}
        return super().default(obj)

def custom_decoder(obj):
    if "__set__" in obj:
        return set(obj["__set__"])
    if "__tuple__" in obj:
        return tuple(obj["__tuple__"])
    return obj

class Cacher(dict):
    def __init__(self,file_path, *, reader=None, writer=None, attributes={}):
        self.file_path = os.path.abspath(file_path)

        if reader:
            self.read = reader
        else:
            def defaultReader():
                if self.file_path and os.path.isfile(self.file_path):
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    return data
                return '{}'
            self.read = defaultReader


        if writer:
            self.write = writer
        else:
            def defaultWriter(file_path,serialization):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self, f, indent=2, cls= CustomEncoder)
            self.write = defaultWriter


        data = self.wrap_item(json.loads(self.read(), object_hook=custom_decoder))

        super().__init__(data)
        self.__dict__.update(attributes)

        self.write_enable = True
        self.modified = False

    def wrap_item(self, v):
        if isinstance(v, dict):
            return Cacher.WrappedDict(self, v)
        if isinstance(v, list):
            return Cacher.WrappedList(self, v)
        if isinstance(v, set):
            return Cacher.WrappedSet(self, v)
        else:
            return v

    def unwrap_item(self, v):
        if isinstance(v, Cacher.WrappedDict):
            return {k: self.unwrap_item(val) for k, val in v.items()}
        if isinstance(v, Cacher.WrappedList):
            return [self.unwrap_item(val) for val in v]
        if isinstance(v, Cacher.WrappedSet):
            return {self.unwrap_item(val) for val in v}
        else:
            return v

    def copy(self):
        return {sk:self.unwrap_item(sv) for sk,sv in self.items()}

    def save(self):
        if self.write_enable:
            self.write(self.file_path,json.dumps(self, indent=2, cls=CustomEncoder))
        else:
            self.modified = True

    def disable_sync(self):
        self.write_enable = False

    def enable_sync(self):
        self.write_enable = True
        if self.modified:
            self.save()
            self.modified = False

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
        if not k in self.keys():
            self[k] = default
        return self[k]

    class WrappedList(list):
        def __init__(self, parent, iterable=()):
            super().__init__([self.wrap_item(v) for v in iterable])
            self.parent = parent

        def wrap_item(self, v):
            if isinstance(v, dict):
                return Cacher.WrappedDict(self, v)
            if isinstance(v, list):
                return Cacher.WrappedList(self, v)
            if isinstance(v, set):
                return Cacher.WrappedSet(self, v)
            else:
                return v

        def unwrap_item(self, v):
            if isinstance(v, Cacher.WrappedDict):
                return {k: self.unwrap_item(val) for k, val in v.items()}
            if isinstance(v, Cacher.WrappedList):
                return [self.unwrap_item(val) for val in v]
            if isinstance(v, Cacher.WrappedSet):
                return {self.unwrap_item(val) for val in v}
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
            if isinstance(v, list):
                return Cacher.WrappedList(self, v)
            if isinstance(v, set):
                return Cacher.WrappedSet(self, v)
            else:
                return v

        def unwrap_item(self, v):
            if isinstance(v, Cacher.WrappedDict):
                return {k: self.unwrap_item(val) for k, val in v.items()}
            if isinstance(v, Cacher.WrappedList):
                return [self.unwrap_item(val) for val in v]
            if isinstance(v, Cacher.WrappedSet):
                return {self.unwrap_item(val) for val in v}
            else:
                return v

        def copy(self):
            return {sk:self.unwrap_item(sv) for sk,sv in self.items()}

        def save(self):
            self.parent.save()

        def __getitem__(self, k):
            if not k in self.keys():
                self[k] = Cacher.WrappedDict(self,{})
            return super().__getitem__(k)

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

    class WrappedSet(set):
        def __init__(self, parent, iterable=()):
            super().__init__({self.wrap_item(v) for v in iterable})
            self.parent = parent

        def wrap_item(self, v):
            if isinstance(v, dict):
                return Cacher.WrappedDict(self, v)
            if isinstance(v, list):
                return Cacher.WrappedList(self, v)
            if isinstance(v, set):
                return Cacher.WrappedSet(self, v)
            else:
                return v

        def unwrap_item(self, v):
            if isinstance(v, Cacher.WrappedDict):
                return {k: self.unwrap_item(val) for k, val in v.items()}
            if isinstance(v, Cacher.WrappedList):
                return [self.unwrap_item(val) for val in v]
            if isinstance(v, Cacher.WrappedSet):
                return {self.unwrap_item(val) for val in v}
            else:
                return v

        def copy(self):
            return {self.unwrap_item(v) for v in self}

        def save(self):
            self.parent.save()

        # Mutating methods
        def add(self, elem):
            super().add(self.wrap_item(elem))
            self.parent.save()

        def remove(self, elem):
            super().remove(elem)
            self.parent.save()

        def discard(self, elem):
            super().discard(elem)
            self.parent.save()

        def pop(self):
            val = super().pop()
            self.parent.save()
            return val

        def clear(self):
            super().clear()
            self.parent.save()

        def update(self, *others):
            wrapped = [self.wrap_item(v) for o in others for v in o]
            super().update(wrapped)
            self.parent.save()

        def intersection_update(self, *others):
            super().intersection_update(*others)
            self.parent.save()

        def difference_update(self, *others):
            super().difference_update(*others)
            self.parent.save()

        def symmetric_difference_update(self, other):
            super().symmetric_difference_update(other)
            self.parent.save()