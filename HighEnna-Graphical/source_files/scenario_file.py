from PyQt6.QtCore import QMutex, QMutexLocker

from error_messages import get_error_message
from safeIO import saferead,safewrite
from cacher import Cacher
from table import Table

from charset_normalizer import from_bytes
from html import escape as html_escape
import importlib.util
import traceback
import sys
import re
import os

import highennabackend

class ScenarioFile:
    def __init__(self,dictionary,scenario_path):
        self.dictionary = {'scenario_file':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.scenario_path = scenario_path
        self.scenario_name = os.path.basename(scenario_path)
        self.scenario_stem,self.scenario_ext = os.path.splitext(self.scenario_name)

        p = r'((?:\d+\.)+\d+)'
        if re.search(p,self.scenario_stem):
            self.default_script_stem = re.sub(p,r'\1.{script_index:0>3}',self.scenario_stem)
        else:
            self.default_script_stem = self.scenario_stem + R".{script_index:0>3}"

        self.mutex = QMutex()

        self.scripts_table = Table(name='scripts_table')
        self.vars_table = Table(name='vars_table')
        self.vals_table = Table(name='vals_table')
        self.errors_table = Table(name='errors_table',allow_empty=True)
        self.errors_table.insert_column([(0,'Error Code'),(1,'Error Type'),(2,'Lin'),(3,'Col'),(4,'Content'),(5,'What')])

        self.mod_time = 0

        self.start_up()

        self.scripts_table.set_default_text(self.default_script_stem)

    def start_up(self):
        self.load_file(is_update=False)

    def update(self):
        self.load_file(is_update=True)

    def load_file(self, is_update):
        with QMutexLocker(self.mutex):

            with open(self.scenario_path,'rb') as f:
                self.file_content = f.read().replace(b'\r',b'')

            self.encoding = from_bytes(self.file_content).best().encoding

            self.script_ext = self.project.application_cache['extensions'][self.scenario_ext]

            self.mod_time = os.path.getmtime(self.scenario_path)

            self.result_parse = highennabackend.parse(self.file_content)

            self.tree = self.result_parse['tree']

            self.errors_table.clear()

            rows_to_insert = []
            cells_to_set = []
            self.cache_error = False
            for index,error in enumerate(self.result_parse['errors']):

                line,s,e = error['location'];
                ls = self.result_parse['line_indexes'][line-1]
                le = self.result_parse['line_indexes'][line]-1
                col = s - ls + 1

                snipet = self.file_content[ls:le].replace(b'\t',b' ')
                n = ls

                try:
                    line_prefix = ' '*len(snipet[ls-n:s-n].decode(encoding=self.encoding))
                    line_middle = '^'*len(snipet[s-n:e-n].decode(encoding=self.encoding))
                    line_postfix = ' '*len(snipet[e-n:le-n].decode(encoding=self.encoding))
                    line_message = (
                            snipet[ls-n:le-n].decode(encoding=self.encoding).replace(' ','°')
                            + '\n'
                            + line_prefix
                            + line_middle
                            + line_postfix
                        )
                except UnicodeDecodeError:
                    for e in range(e+1,le):
                        try:
                            line_prefix = ' '*len(snipet[ls-n:s-n].decode(encoding=self.encoding))
                            line_middle = '^'*len(snipet[s-n:e-n].decode(encoding=self.encoding))
                            line_postfix = ' '*len(snipet[e-n:le-n].decode(encoding=self.encoding))
                            line_message = (
                                    snipet[ls-n:le-n].decode(encoding=self.encoding).replace(' ','°')
                                    + '\n'
                                    + line_prefix
                                    + line_middle
                                    + line_postfix
                                )
                            break
                        except UnicodeDecodeError:
                            pass
                    else:
                        try:
                            line_message = snipet[ls-n:le-n].decode(encoding=self.encoding).replace(' ','°')
                        except UnicodeDecodeError:
                            line_message = ''

                error_code = str(error['code'])
                self.cache_error |= 'EOF_OPN_CACHE' in error_code or 'MULT_CACHE' in error_code

                rows_to_insert.append((index,))
                cells_to_set.extend([
                    (index, 0, error_code),
                    (index, 1, 'Syntax'),
                    (index, 2, str(line)),
                    (index, 3, str(col)),
                    (index, 4, str(line_message)),
                    (index, 5, str(get_error_message(error['code']))),
                ])




            self.errors_table.insert_row(rows_to_insert)
            self.errors_table.set_cell(cells_to_set)

            if not is_update:
                def reader():
                    if self.cache_error:
                        return '{}'
                    stream = b''.join([self.file_content[start:end] for _,start,end in self.result_parse['cache']['lines']])
                    if stream:
                        return highennabackend.decode(stream).decode(encoding='utf-8')
                        # return stream.decode(encoding=self.encoding)
                    return '{}'

                def writer(file_path,serialization):
                    if self.cache_error:
                        return
                    start,end = self.result_parse['cache']['location']
                    length = len(self.file_content)
                    stream = highennabackend.encode(serialization.encode(encoding='utf-8'))
                    # stream = serialization.encode(encoding=self.encoding)
                    rewrite = self.file_content[:start]+\
                        "R'''\n$$$\n".encode()+\
                        b'\n'.join(stream[i:i+126] for i in range(0, len(stream), 126))+\
                        "\n$$$\n'''\n".encode()+\
                        self.file_content[end:]
                    safewrite('wb',file_path,rewrite,encoding=self.encoding)
                    self.mod_time = os.path.getmtime(self.scenario_path)


                self.file_cache = Cacher(self.scenario_path,
                        reader=reader,
                        writer=writer
                    )

                if self.result_parse['cache']['found']:
                    if 'highenna_version' in self.file_cache:
                        if self.file_cache['highenna_version']=='2.0.0':
                            if 'table_data' in self.file_cache:
                                self.scripts_table.column_names = self.file_cache['table_data']['scripts_table']['column_names'].copy()
                                self.scripts_table.data = self.file_cache['table_data']['scripts_table']['data'].copy()
                                self.vars_table.column_names = self.file_cache['table_data']['vars_table']['column_names'].copy()
                                self.vars_table.data = self.file_cache['table_data']['vars_table']['data'].copy()
                                self.vals_table.column_names = self.file_cache['table_data']['vals_table']['column_names'].copy()
                                self.vals_table.data = self.file_cache['table_data']['vals_table']['data'].copy()
                    else:
                        pass
                else:
                    self.file_content += b'\n\n'
                    start,end = self.result_parse['cache']['location']
                    self.result_parse['cache']['location'] = (start+2,end+2)

                self.file_cache['highenna_version'] = '2.0.0'

            if not self.scripts_table.column_names:
                self.scripts_table.column_names = ['Script Names']
                self.scripts_table.data = [[self.default_script_stem]]

            if self.result_parse['names']['vars']:
                new_vars = [var for var in self.result_parse['names']['vars'] if not var in self.vars_table.column_names]
                if new_vars:
                    length = len(self.vars_table.column_names)
                    self.vars_table.insert_column([(length+i,var_name) for i,var_name in enumerate(sorted(new_vars))])
                    self.vars_table.delta_to_saved_version -= 1 if not is_update else 0
                    self.vars_table.undo_stack.clear()

            if self.result_parse['names']['vals']:
                new_vals = [val for val in self.result_parse['names']['vals'] if not val in self.vals_table.column_names]
                if new_vals:
                    length = len(self.vals_table.column_names)
                    self.vals_table.insert_column([(length+i,val_name) for i,val_name in enumerate(sorted(new_vals))])
                    self.vals_table.delta_to_saved_version -= 1 if not is_update else 0
                    self.vals_table.undo_stack.clear()



    def log_render_error(self,append_text_signal, exc, file_name, code='', indent='    | '):

        chain = []
        current = exc
        while current is not None:
            chain.append(current)
            current = current.__context__ or current.__cause__
        
        tracebacks = []
        for e in reversed(chain):
            tb_frames = traceback.extract_tb(e.__traceback__)
            tracebacks.append(tb_frames)

        lines = [indent]
        cumulative = []
        for i, (e, frames) in enumerate(zip(reversed(chain), reversed(tracebacks))):
            cumulative.extend(frames)
            lines.append(f'{indent}Traceback (most recent call last):')

            for filename, lineno, func, line in traceback.extract_tb(e.__traceback__):
                if 'scenario_file.py' in filename: continue
                lines.append(html_escape(f'{indent}  File "{filename}", line {lineno}, in {func}'))
                if filename == file_name:
                    if line:
                        lines.append(html_escape(f'{indent}    {line.strip()}'))
                    elif code:
                        lines.append(html_escape(f'{indent}    {(code.splitlines()[lineno-1]).strip()}'))

            lines.extend([
                    indent,
                    f'{indent}<span style="color:#f44250;">{html_escape(type(e).__name__)}</span>: {html_escape(str(e))}'
                ])

            if i < len(chain) - 1:
                lines.extend([
                        indent,
                        f'{indent}<span style="color:#fdfd96;">During handling of the above exception, another exception occurred:</span>',
                        indent,
                    ])

        lines.append(f'{indent}\n')
        append_text_signal.emit('\n'.join(lines))

    def render(self,items, append_text_signal, progress_signal):
        if not items:
            return
        with QMutexLocker(self.mutex):
            script_ext = self.project.application_cache['extensions'][self.scenario_ext]

            append_text_signal.emit(f'Scenario: <span style="color:#fff856;">{self.scenario_name}</span>\n')

            if self.has_syntax_errors():
                append_text_signal.emit('  <span style="color:#fd9d7d;">Contains Syntax errors. Quitting Scenario.</span>\n')
                progress_signal.emit(len(items))
                return False

            self.errors_table.clear()

            builtins_scope = {'__builtins__':globals()['__builtins__']}

            if self.project.modules_path not in sys.path:
                sys.path.append(self.project.modules_path)

            append_text_signal.emit(f' *Importing <span style="color:#c695c6;">Modules</span>')
            modules_scope = builtins_scope.copy()
            modules_ok = True
            if self.file_cache['modules']['module_assignment']:
                for module_uuid,module_content in self.file_cache['modules']['module_assignment'].items():
                    module_name = self.project.uuid_to_name[module_uuid]

                    module_path = os.path.join(self.project.modules_path, module_name)

                    module_base_name = os.path.splitext(module_name)[0]
                    module_scope = builtins_scope.copy()
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_path, submodule_search_locations=self.project.modules_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)

                        modules_scope.update(module.__dict__)
                    except Exception as e:
                        if modules_ok:
                            append_text_signal.emit('\n')
                            modules_ok = False

                        append_text_signal.emit(f'   *Importing <span style="color:#3d84fb;">{module_name}</span>\n')
                        self.log_render_error(append_text_signal,e,module_name,module_content)

                        index = len(self.errors_table)
                        self.errors_table.insert_row([(index,)])
                        self.errors_table.set_cell([
                            (index, 0, type(e).__name__),
                            (index, 1, 'Import'),
                            (index, 2, str(traceback.extract_tb(e.__traceback__)[-1].lineno)),
                            (index, 4, module_name),
                            (index, 5, str(e)),
                        ])

                if modules_ok:
                    append_text_signal.emit(f': <span style="color:#67ff67;">Ok</span>\n')
            else:
                append_text_signal.emit(f': <span style="color:#CCCCCC;">None</span>\n')


            append_text_signal.emit(f' *Setting <span style="color:#c695c6;">Vals</span>')
            vals_scope = builtins_scope.copy()
            vals_ok = True
            if self.vals_table:
                for name,value in self.vals_table.get_row(0).items():
                    val_name = f'val_{name}'
                    val_value = value.replace("'","\\'")
                    val_scope = builtins_scope.copy()
                    try:
                        code = compile(f"exec('{val_name} = {val_value}')", filename=val_name, mode='exec')
                        exec(code, val_scope)
                        vals_scope.update(val_scope)
                    except Exception as e:
                        if vals_ok:
                            append_text_signal.emit('\n')
                            vals_ok = False

                        append_text_signal.emit(f'   *Setting <span style="color:#3d84fb;">{val_name}</span>\n')
                        self.log_render_error(append_text_signal,e,val_name,f'{val_name} = {val_value}')

                        index = len(self.errors_table)
                        self.errors_table.insert_row([(index,)])
                        self.errors_table.set_cell([
                            (index, 0, type(e).__name__),
                            (index, 1, 'Vals'),
                            (index, 4, f'{val_name} = {value}'),
                            (index, 5, str(e)),
                        ])

                if vals_ok:
                    append_text_signal.emit(f': <span style="color:#67ff67;">Ok</span>\n')
            else:
                append_text_signal.emit(f': <span style="color:#CCCCCC;">None</span>\n')

            partial_scope = {}
            partial_scope.update(modules_scope)
            partial_scope.update(vals_scope)

            vars_ok_ok = True
            if self.vars_table:
                for script_index in items:
                    append_text_signal.emit(
                            f'  Script: <span style="color:#fff856;">#{script_index+1}</span>\n'
                            f'   *Setting <span style="color:#c695c6;">Vars</span>'
                        )
                    vars_scope = builtins_scope.copy()
                    vars_ok = True
                    for var_col,(name,value) in enumerate(self.vars_table.get_row(script_index).items()):
                        var_name = f"var_{name}"
                        var_value = value.replace("'","\\'")
                        var_scope = builtins_scope.copy()
                        try:
                            code = compile(f"exec('{var_name} = {var_value}')", filename=var_name, mode='exec')
                            exec(code, var_scope)
                            vars_scope.update(var_scope)
                        except Exception as e:
                            if vars_ok:
                                append_text_signal.emit('\n')
                                vars_ok = False
                                vars_ok_ok = False

                            append_text_signal.emit(f'     *Setting <span style="color:#3d84fb;">{var_name}</span>\n')
                            self.log_render_error(append_text_signal,e,var_name,f'{var_name} = {var_value}',indent='      | ')

                            tb = traceback.extract_tb(e.__traceback__)
                            frame = next(reversed([f for f in tb if f.filename == var_name]), None)
                            index = len(self.errors_table)
                            self.errors_table.insert_row([(index,)])
                            self.errors_table.set_cell([
                                (index, 0, type(e).__name__),
                                (index, 1, 'Vars'),
                                (index, 2, str(script_index+1)),
                                (index, 3, str(var_col+1)),
                                (index, 4, f'{var_name} = {value}'),
                                (index, 5, str(e)),
                            ])

                    vars_scope['script_index'] = script_index+1

                    script_name = self.scripts_table.data[script_index][0]
                    try:
                        code = compile(f"exec('script_name = f\"{script_name}{script_ext}\"')", filename='script_name', mode='exec')
                        exec(code, vars_scope)
                    except Exception as e:
                        if vars_ok:
                            append_text_signal.emit('\n')
                            vars_ok = False
                            vars_ok_ok = False

                        append_text_signal.emit(f'     *Setting <span style="color:#3d84fb;">script_name</span>\n')
                        self.log_render_error(append_text_signal,e,'script_name',f'script_name = f\"{script_name}{script_ext}\"',indent='      | ')

                        tb = traceback.extract_tb(e.__traceback__)
                        frame = next(reversed([f for f in tb if f.filename == 'script_name']), None)
                        index = len(self.errors_table)
                        self.errors_table.insert_row([(index,)])
                        self.errors_table.set_cell([
                            (index, 0, type(e).__name__),
                            (index, 1, 'Name'),
                            (index, 2, str(script_index+1)),
                            (index, 4, f'script_name = f\"{script_name}{script_ext}\"'),
                            (index, 5, str(e)),
                        ])

                    if vars_ok:
                        append_text_signal.emit(f': <span style="color:#67ff67;">Ok</span>\n')

                    append_text_signal.emit(f'   *Rendering')

                    if not all([modules_ok,vals_ok,vars_ok]):
                        append_text_signal.emit(f': <span style="color:#fd9d7d;">Errors occurred. Skipping <span style="color:#fff856;">#{script_index+1}</span>.</span>\n')
                        progress_signal.emit(1)
                        continue

                    total_scope = {}
                    total_scope.update(partial_scope)
                    total_scope.update(vars_scope)

                    self.render_tree(total_scope, append_text_signal)

                    progress_signal.emit(1)

            else:
                append_text_signal.emit(f'  Script: <span style="color:#fff856;">#Single</span>\n')
                append_text_signal.emit(f'   *Setting <span style="color:#c695c6;">Vars</span>')

                script_name = self.scripts_table.data[0][0]
                vars_ok = True
                var_scope = builtins_scope.copy()
                var_scope['script_index'] = 1
                try:
                    code = compile(f"exec('script_name = f\"{script_name}{script_ext}\"')", filename='script_name', mode='exec')
                    exec(code, var_scope)
                    partial_scope.update(var_scope)
                except Exception as e:
                    if vars_ok:
                        append_text_signal.emit('\n')
                        vars_ok = False
                        vars_ok_ok = False

                    append_text_signal.emit(f'     *Setting <span style="color:#3d84fb;">script_name</span>\n')
                    self.log_render_error(append_text_signal,e,'script_name',f'script_name = f\"{script_name}{script_ext}\"',indent='      | ')

                    tb = traceback.extract_tb(e.__traceback__)
                    frame = next(reversed([f for f in tb if f.filename == 'script_name']), None)
                    index = len(self.errors_table)
                    self.errors_table.insert_row([(index,)])
                    self.errors_table.set_cell([
                        (index, 0, type(e).__name__),
                        (index, 1, 'Name'),
                        (index, 2, str(1)),
                        (index, 4, f'script_name = f\"{script_name}{script_ext}\"'),
                        (index, 5, str(e)),
                    ])

                if vars_ok:
                    append_text_signal.emit(f': <span style="color:#CCCCCC;">None</span>\n')

                append_text_signal.emit(f'   *Rendering')
                
                if not all([modules_ok,vals_ok,vars_ok]):
                    append_text_signal.emit(f': <span style="color:#fd9d7d;">Errors occurred. Skipping.</span>\n')
                    progress_signal.emit(1)
                    return False

                self.render_tree(partial_scope, append_text_signal)

                progress_signal.emit(1)

        return all([modules_ok,vals_ok,vars_ok_ok])

    def render_tree(self, my_scope, append_text_signal):

        render_ok = True

        def _render_tree(f_bytes,tree,scope):

            nonlocal append_text_signal
            nonlocal render_ok

            for block in tree:

                if block['type'] == 'plain_text':
                    start,end = block['argument']
                    f_bytes.extend(self.file_content[start:end])

                elif block['type'] == 'expression':
                    line_no,start,end = block['argument']
                    expression = self.file_content[start:end].decode(encoding=self.encoding)
                    try:
                        escaped_expression = expression.replace("'","\\'")
                        code = compile(f"str(eval('{escaped_expression}'))", filename='expression', mode='eval')
                        expanded_expression = eval(code, scope)
                        f_bytes.extend(expanded_expression.encode(encoding='utf-8'))
                    except Exception as e:
                        if render_ok:
                            append_text_signal.emit(': <span style="color:#ff382f;">Failed</span>\n')
                            render_ok = False

                        append_text_signal.emit(f'     *Evaluating "<span style="color:#f9ae57;">$${expression}$$</span>" - row: {line_no+1}, col: {start}-{end}\n      |\n')
                        self.log_render_error(append_text_signal,e,expression,indent='      | ')

                        index = len(self.errors_table)
                        self.errors_table.insert_row([(index,)])
                        self.errors_table.set_cell([
                            (index, 0, type(e).__name__),
                            (index, 1, 'Expression'),
                            (index, 2, line_no+1),
                            (index, 4, expression),
                            (index, 5, str(e)),
                        ])

                elif block['type'] == 'EXEC':
                    line_no,start,end = block['argument']
                    argument = self.file_content[start:end].decode(encoding=self.encoding)
                    try:
                        escaped_argument = argument.replace("'","\\'")
                        code = compile(f"exec('{escaped_argument}')", filename='EXEC', mode='exec')
                        exec(code, scope)
                    except Exception as e:
                        if render_ok:
                            append_text_signal.emit(': <span style="color:#ff382f;">Failed</span>\n')
                            render_ok = False

                        append_text_signal.emit(f'     *Executing "<span style="color:#f9ae57;">$EXEC{{{argument}}}$</span>" - row: {line_no+1}, col: {start}-{end}\n      |\n')
                        self.log_render_error(append_text_signal,e,argument,indent='      | ')

                        index = len(self.errors_table)
                        self.errors_table.insert_row([(index,)])
                        self.errors_table.set_cell([
                            (index, 0, type(e).__name__),
                            (index, 1, 'Command'),
                            (index, 2, line_no+1),
                            (index, 4, argument),
                            (index, 5, str(e)),
                        ])

                elif block['type'] == 'FOR':
                    line_no,start,end = block['argument']
                    for_subtree = block['subtree']

                    argument = self.file_content[start:end].decode(encoding=self.encoding)

                    for_scope = scope.copy()
                    for_scope['virtual_scope'] = for_scope

                    code_str = f'''
__snapshots__ = []
for {argument}:
    __copy__ = virtual_scope.copy()
    __trash__ = __copy__.pop('virtual_scope', None)
    __trash__ = __copy__.pop('__snapshots__', None)
    __trash__ = __copy__.pop('__copy__', None)
    __trash__ = __copy__.pop('__trash__', None)
    __snapshots__.append(__copy__)
'''

                    try:
                        code = compile(code_str, filename='FOR', mode='exec')
                        exec(code, for_scope)
                        snapshots = for_scope.pop('__snapshots__')
                        for snapshot_scope in snapshots:
                            _render_tree(f_bytes,for_subtree,snapshot_scope)

                    except Exception as e:
                        if render_ok:
                            append_text_signal.emit(': <span style="color:#ff382f;">Failed</span>\n')
                            render_ok = False

                        append_text_signal.emit(f'     *Evaluating "<span style="color:#f9ae57;">$FOR{{{argument}}}$</span>" - row: {line_no+1}, col: {start}-{end}\n      |\n')
                        self.log_render_error(append_text_signal,e,'FOR',code=code_str,indent='      | ')

                        index = len(self.errors_table)
                        self.errors_table.insert_row([(index,)])
                        self.errors_table.set_cell([
                            (index, 0, type(e).__name__),
                            (index, 1, 'FOR Block'),
                            (index, 2, line_no+1),
                            (index, 4, argument),
                            (index, 5, str(e)),
                        ])

                elif block['type'] == 'IF':
                    for if_block in block['blocks']:
                        if_subtree = if_block['subtree']
                        truth = False
                        if not 'argument' in if_block:
                            truth = True
                        else:
                            line_no,start,end = if_block['argument']

                            argument = self.file_content[start:end].decode(encoding=self.encoding).strip()

                            if_scope = scope.copy()

                            code_str = f'''
__truth__ = False
if {argument}:
    __truth__ = True
'''
                            try:
                                code = compile(code_str, filename='IF', mode='exec')
                                exec(code, if_scope)
                                truth = if_scope.pop('__truth__')

                            except Exception as e:
                                if render_ok:
                                    append_text_signal.emit(': <span style="color:#ff382f;">Failed</span>\n')
                                    render_ok = False

                                append_text_signal.emit(f'     *Evaluating "<span style="color:#f9ae57;">$IF{{{argument}}}$</span>" - row: {line_no+1}, col: {start}-{end}\n      |\n')
                                self.log_render_error(append_text_signal,e,'IF',code=code_str,indent='      | ')

                                index = len(self.errors_table)
                                self.errors_table.insert_row([(index,)])
                                self.errors_table.set_cell([
                                    (index, 0, type(e).__name__),
                                    (index, 1, 'IF Block'),
                                    (index, 2, line_no+1),
                                    (index, 4, argument),
                                    (index, 5, str(e)),
                                ])

                        if truth:
                            _render_tree(f_bytes,if_subtree,scope)
                            break

        result_bytes = bytearray()
        _render_tree(result_bytes,self.tree,my_scope)
        if render_ok:
            os.makedirs(self.project.project_cache["render_dir"], exist_ok=True)
            result_bytes = re.sub(br"(?:(?<=\n)\n)?R'''\n+'''\n*",b'',result_bytes)
            append_text_signal.emit(' <span style="color:#67ff67;">Success</span>\n')
            safewrite('wb',os.path.join(self.project.project_cache["render_dir"],my_scope['script_name']),result_bytes)
        # import json
        # os.makedirs(self.project.project_cache["render_dir"], exist_ok=True)
        # safewrite('w',os.path.join(self.project.project_cache["render_dir"],"tree.txt"),json.dumps(self.tree,indent=2))

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

    def update_modules(self):
        with QMutexLocker(self.mutex):
            self.file_cache.disable_sync()
            
            project_modules_path = self.project.modules_path
            uuid_to_name = self.project.uuid_to_name

            project_module_timestamps = self.project.project_cache['modules']['module_timestamps']
            project_module_assignment = self.project.project_cache['modules']['module_assignments'][self.scenario_name]
            
            self_module_timestamps   = self.file_cache['modules']['module_timestamps']
            self_module_assignment   = self.file_cache['modules']['module_assignment']
            self_module_uuid_to_name = self.file_cache['modules']['module_uuid_to_name']
            
            for module_uuid in list(self_module_assignment.keys()):
                if module_uuid not in project_module_assignment:
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
                    self_module_timestamps[module_uuid] = project_module_timestamp
                    with open(os.path.join(project_modules_path, module_name), 'r', encoding='utf-8') as m:
                        self_module_assignment[module_uuid] = m.read()

            self.file_cache.enable_sync()

    def has_unsaved_changes(self):
        return any([
                self.scripts_table.delta_to_saved_version != 0,
                self.vars_table.delta_to_saved_version != 0,
                self.vals_table.delta_to_saved_version != 0,
            ])

    def has_syntax_errors(self):
        return any(self.errors_table.data[row][1] == 'Syntax' for row in range(len(self.errors_table)))

    def remove_obsolete(self):

        obsolete_vars = [(i,) for i,var in enumerate(self.vars_table.column_names)
                         if var not in self.result_parse['names']['vars']]
        obsolete_vals = [(i,) for i,val in enumerate(self.vals_table.column_names)
                         if val not in self.result_parse['names']['vals']]

        if obsolete_vars:
            self.vars_table.remove_column(obsolete_vars)
        if obsolete_vals:
            self.vals_table.remove_column(obsolete_vals)
