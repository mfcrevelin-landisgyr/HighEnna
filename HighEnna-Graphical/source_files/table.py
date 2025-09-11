from collections import deque

class Table:
    def __init__(self):
        self.column_names = []
        self.data = []

        self.undo_stack = deque()
        self.redo_stack = deque()

        self._last_op_data = {} # For undo/redo internal use

        self.column_names.clear()
        self.data.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def __len__(self):
        return len(self.data)
    def __bool__(self):
        return len(self.column_names)>0

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
        self._perform(action, data, record_undo=False)

    def _perform(self, action, data, record_undo=True):
        getattr(self, f"_{action}")(data, record_undo)

    def _perform_undo(self, action, data):
        getattr(self, f"_undo_{action}")(data)

    # --- Column Methods ---

    def insert_column(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._insert_column(items)

    def _insert_column(self, items, record_undo=True):
        undo_data = []

        for index, name in items:
            index = index if index <= len(self.data) else len(self.data)
            self.column_names.insert(index, name)
            for row in self.data:
                row.insert(index, "")
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

        for index, in items:
            index = index if index < len(self.data) else len(self.data)-1
            name = self.column_names.pop(index)
            removed_cells = [row.pop(index) for row in self.data]
            undo_data.append((index, name, removed_cells))

        if record_undo:
            self._record_undo("remove_column", undo_data)

    def _undo_remove_column(self, items):
        for index, name, cells in reversed(items):
            self.column_names.insert(index, name)
            for i, row in enumerate(self.data):
                row.insert(index, cells[i])

    # --- Row Methods ---

    def insert_row(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._insert_row(items)

    def _insert_row(self, items, record_undo=True):
        undo_data = []

        for index, in items:
            index = index if index <= len(self.data) else len(self.data)
            self.data.insert(index,['']*len(self.column_names))
            undo_data.append((index,))

        if record_undo:
            self._record_undo("insert_row", undo_data)

    def _undo_insert_row(self, items):
        for index, in reversed(items):
            self.data.pop(index)

    def remove_row(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._remove_row(items)

    def _remove_row(self, items, record_undo=True):
        undo_data = []

        for index, in items:
            index = index if index < len(self.data) else len(self.data)-1
            removed = self.data.pop(index)
            undo_data.append((index, removed))

        if record_undo:
            self._record_undo("remove_row", undo_data)

    def _undo_remove_row(self, items):
        for index, row in reversed(items):
            self.data.insert(index, row[:])

    def get_row(self, row):
        return {self.column_names[col]:self.data[row][col] for col in range(len(self.column_names))}

    # --- Cell Methods ---

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
            # self.column_names.insert(to_index if from_index > to_index else to_index - 1, name)

            for row in self.data:
                cell = row.pop(from_index)
                row.insert(to_index, cell)
                # row.insert(to_index if from_index > to_index else to_index - 1, cell)

            undo_data.append((to_index, from_index))  # reverse move
            # undo_data.append((to_index if from_index > to_index else to_index - 1, from_index))  # reverse move

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
            self.data.insert(to_index if from_index > to_index else to_index - 1, row)

            undo_data.append((to_index if from_index > to_index else to_index - 1, from_index))  # reverse move

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
            return content[:cell_width].ljust(cell_width)

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