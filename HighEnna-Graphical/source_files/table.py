from collections import deque

class Table:
    ir=0
    def __init__(self, default_text = '', allow_empty=False):
        self.column_names = []
        self.data = [] if allow_empty else [[]]

        self.undo_stack = deque()
        self.redo_stack = deque()

        self.allow_empty = allow_empty

        self.default_text = default_text



    def __len__(self):
        return len(self.data)
    def __bool__(self):
        return bool(self.column_names) and bool(self.data)


    # --- Undo/Redo ---

    def _record_undo(self, action, data):
        self.undo_stack.append((action, data))
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        action, data = self.undo_stack.pop()
        self.redo_stack.append((action, data))
        self._perform_undo(action, data)

    def redo(self):
        if not self.redo_stack:
            return
        action, data = self.redo_stack.pop()
        self.undo_stack.append((action, data))
        self._perform_redo(action, data)

    def _perform_redo(self, action, data):
        getattr(self, f"_{action}")(data, False)

    def _perform_undo(self, action, data):
        getattr(self, f"_undo_{action}")(data)

    # --- Column Methods ---

    def insert_column(self, items):
        length = len(self.column_names)
        items_ = []

        bellow_indexes = [item for item in items if item[0]<=length]
        items = items[len(bellow_indexes):]

        while bellow_indexes:
            bellow_indexes = sorted(bellow_indexes, key=lambda x: x[0], reverse=True)

            length += len(bellow_indexes)
            items_+=bellow_indexes

            bellow_indexes = [item for item in items if item[0]<=length]
            items = items[len(bellow_indexes):]

        if items:
            items = sorted(items, key=lambda x: x[0])
            raise IndexError(f"Column index {items[0][0]} out of bounds")

        self._insert_column(items_)

    def _insert_column(self, items, record_undo=True):
        undo_data = []

        for index, name in items:
            self.column_names.insert(index, name)
            for row in self.data:
                row.insert(index, self.default_text)
            undo_data.append((index, name))

        if record_undo:
            self._record_undo("insert_column", undo_data)

    def _undo_insert_column(self, items):
        for index, _ in reversed(items):
            self.column_names.pop(index)
            for row in self.data:
                row.pop(index)

    def remove_column(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._remove_column(items)

    def _remove_column(self, items, record_undo=True):
        undo_data = []

        for index, *_ in items:
            index = index if index < len(self.column_names) else len(self.column_names)-1
            name = self.column_names.pop(index)
            removed_cells = [row.pop(index) for row in self.data]
            undo_data.append((index, name, removed_cells))

        if record_undo:
            self._record_undo("remove_column", undo_data)

    def _undo_remove_column(self, items):
        for index, name, removed_cells in reversed(items):
            self.column_names.insert(index, name)
            for i, row in enumerate(self.data):
                row.insert(index, removed_cells[i])

    # --- Row Methods ---

    def insert_row(self, items):
        length = len(self.data)
        items_ = []

        bellow_indexes = [item for item in items if item[0]<=length]
        items = items[len(bellow_indexes):]

        while bellow_indexes:
            bellow_indexes = sorted(bellow_indexes, key=lambda x: x[0], reverse=True)

            length += len(bellow_indexes)
            items_+=bellow_indexes

            bellow_indexes = [item for item in items if item[0]<=length]
            items = items[len(bellow_indexes):]
        

        if items:
            Table.ir+=1
            if Table.ir>=11:
                # print(Table.ir)
                import pdb; pdb.set_trace()
            items = sorted(items, key=lambda x: x[0])
            raise IndexError(f"Row index {items[0][0]} out of bounds")

        self._insert_row(items_)

    def _insert_row(self, items, record_undo=True):

        undo_data = []

        for index, in items:
            self.data.insert(index,[self.default_text]*len(self.column_names))
            undo_data.append((index,))

        if record_undo:
            self._record_undo("insert_row", undo_data)

    def _undo_insert_row(self, items):
        for index, in reversed(items):
            self.data.pop(index)



    def duplicate_row(self, items):
        length = len(self.data)
        items_ = []

        bellow_indexes = [item for item in items if item[0] < length]
        items = items[len(bellow_indexes):]

        while bellow_indexes:
            bellow_indexes = sorted(bellow_indexes, key=lambda x: x[0], reverse=True)

            items_ += bellow_indexes
            length += len(bellow_indexes)

            bellow_indexes = [item for item in items if item[0] < length]
            items = items[len(bellow_indexes):]

        if items:
            items = sorted(items, key=lambda x: x[0])
            raise IndexError(f"Row index {items[0][0]} out of bounds")

        self._duplicate_row(items_)

    def _duplicate_row(self, items, record_undo=True):
        undo_data = []

        for index, in items:
            row_copy = self.data[index].copy()
            self.data.insert(index + 1, row_copy)
            undo_data.append((index,))

        if record_undo:
            self._record_undo("duplicate_row", undo_data)

    def _undo_duplicate_row(self, items):
        for index, in reversed(items):
            self.data.pop(index + 1)



    def remove_row(self, items):
        items = [sorted(items, key=lambda x: x[0], reverse=True)]
        self._remove_row(items)

    def _remove_row(self, items, record_undo=True):
        undo_data = [[],False]

        for index,*_ in items[0]:
            index = index if index < len(self.data) else len(self.data)-1
            removed = self.data.pop(index)
            undo_data[0].append((index, removed))

        if not self.data and not self.allow_empty:
            undo_data[1]=True
            self.data.append([self.default_text] * len(self.column_names))

        if record_undo:
            self._record_undo("remove_row", undo_data)

    def _undo_remove_row(self, items):
        if items[1]:
            self.data.pop()
        for index, row in reversed(items[0]):
            self.data.insert(index, row[:]),



    def get_row(self, row):
        return {self.column_names[col]:self.data[row][col] for col in range(len(self.column_names))}

    # --- Cell Methods ---

    def clear(self):
        old_data = [row[:] for row in self.data]
        self._clear(old_data)

    def _clear(self, old_data, record_undo=True):
        self.data = [] if self.allow_empty else [[]]

        if record_undo:
            self._record_undo("clear", old_data)

    def _undo_clear(self, old_data):
        self.data = [row[:] for row in old_data]



    def clear_cell(self, items):
        items = [(row, col, self.default_text, self.data[row][col]) for row, col in items]
        self._set_cell(items)

    def set_cell(self, items):
        items = [(row, col, new, self.data[row][col]) for row, col, new in items]
        self._set_cell(items)

    def _set_cell(self, items, record_undo=True):
        undo_data = []

        for row, col, new, old in items:
            self.data[row][col] = new
            undo_data.append((row, col, new, old))

        if record_undo:
            self._record_undo("set_cell", undo_data)

    def _undo_set_cell(self, items):
        undo_data = []

        for row, col, new, old in items:
            self.data[row][col] = old


    def get_cell(self, row, col):
        return self.data[row][col]

    # --- Reorder Methods ---

    def move_column(self, items):
        self._move_column(items)

    def _move_column(self, items, record_undo=True):
        undo_data = []

        for from_index, to_index in items:
            if from_index == to_index or not (0 <= from_index < len(self.column_names)) or not (0 <= to_index <= len(self.column_names)):
                continue

            name = self.column_names.pop(from_index)
            self.column_names.insert(to_index, name)

            for row in self.data:
                cell = row.pop(from_index)
                row.insert(to_index, cell)

            undo_data.append((to_index, from_index))  # reverse move

        if record_undo:
            self._record_undo("move_column", undo_data)

    def _undo_move_column(self, items):
        self._move_column(items, record_undo=False)

    def move_row(self, items):
        self._move_row(items)

    def _move_row(self, items, record_undo=True):
        undo_data = []

        for from_index, to_index in items:
            if from_index == to_index or not (0 <= from_index < len(self.data)) or not (0 <= to_index <= len(self.data)):
                continue

            row = self.data.pop(from_index)
            self.data.insert(to_index, row)

            undo_data.append((to_index, from_index))  # reverse move

        if record_undo:
            self._record_undo("move_row", undo_data)

    def _undo_move_row(self, items):
        self._move_row(items, record_undo=False)

    # --- Print Method ---

    def print(self, cell_width: int = 15):
        if not self.column_names:
            print("(Empty Table)")
            return

        def format_cell(content: str) -> str:
            return content.replace('\n','')[:cell_width].ljust(cell_width)

        def print_separator():
            print("*" + "*".join(["-" * cell_width for _ in self.column_names]) + "*")

        # Print header
        print_separator()
        header = "|" + "|".join([format_cell(name) for name in self.column_names]) + "|"
        print(header)
        print_separator()

        # Print rows
        for row in self.data:
            line = "|" + "|".join([format_cell(cell) for cell in row]) + "|"
            print(line)

        print_separator()