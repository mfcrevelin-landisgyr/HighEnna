import tempfile
import errno
import time
import os

tempfiledir = tempfile.gettempdir()

def safewrite(mode,file_path,content,tries=10,encoding='utf-8'):
    for _ in range(tries):

        if "b" in mode:
            tmp = tempfile.NamedTemporaryFile(mode, delete=False, dir=tempfiledir)
        else:
            tmp = tempfile.NamedTemporaryFile(mode, delete=False, dir=tempfiledir)

        tmp_path = tmp.name
        with tmp:
            tmp.write(content)

        try:
            os.replace(tmp_path, file_path)
        except FileNotFoundError as e:
            time.sleep(0.1)
            continue

        break

    else:
        raise

def saferead(mode,file_path,tries=10):
    for _ in range(tries):
        try:
            with open(file_path, mode) as f:
                return f.read()
        except (OSError, IOError) as e:
            if e.errno in (errno.ENOENT, errno.EACCES, errno.EIO):
                time.sleep(0.1)
                continue
            raise
    else:
        raise