#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H

struct DataFrame {
	DataFrame(){
		cell_values.insert("");
		empty_string = cell_values.get("");
	}

    std::unordered_map<std::tuple<uint64_t, std::string>, std::shared_ptr<std::string>> table;
    std::shared_ptr_set<std::string> cell_values;
    std::shared_ptr<std::string> empty_string;
    
    std::unordered_map<uint64_t,std::string> col_idx_to_name;
    std::set<std::string> columns;
    
    uint64_t width = 0, height = 0;

    struct Action {
        enum Type { Set, InsertColumn, InsertRow, InsertRowAt, RemoveColumn, RemoveRow } type;
        int64_t row; std::string col;
        std::string value, prev_value;
        bool add_value;
    };

    std::stack<Action> undo_stack;
    std::stack<Action> redo_stack;

public:

	void undo() {
	    if (undo_stack.empty()) return;
	    Action action = undo_stack.top();
	    undo_stack.pop();
	    redo_stack.push(action);

	    switch (action.type) {
	        case Action::Set: {
	            if (action.add_value)
	                cell_values.erase(action.value);
	            table[std::make_tuple(action.row, action.col)] = cell_values.get(action.prev_value);
	            break;
	        }
	        case Action::InsertColumn: {
	            columns.erase(action.col);
	            col_idx_to_name.clear();
	            uint64_t i = 0;
	            for (auto& col : columns)
	                col_idx_to_name[i++] = col;
	            for (uint64_t row = 0; row < height; ++row)
	                table.erase(std::make_tuple(row, action.col));
	            --width;
	            break;
	        }
	        case Action::InsertRow:
	        case Action::InsertRowAt: {
	            for (auto& col : columns) {
	                for (uint64_t row = action.row + 1; row < height; ++row)
	                    table[std::make_tuple(row - 1, col)] = table[std::make_tuple(row, col)];
	                table.erase(std::make_tuple(height - 1, col));
	            }
	            --height;
	            break;
	        }
	        case Action::RemoveColumn: {
	            columns.insert(action.col);
	            col_idx_to_name.clear();
	            uint64_t i = 0;
	            for (auto& col : columns)
	                col_idx_to_name[i++] = col;
	            for (uint64_t row = 0; row < height; ++row)
	                table[std::make_tuple(row, action.col)] = empty_string;
	            ++width;
	            break;
	        }
	        case Action::RemoveRow: {
	            for (auto& col : columns) {
	                for (uint64_t row = height; row > action.row; --row)
	                    table[std::make_tuple(row, col)] = table[std::make_tuple(row - 1, col)];
	                table[std::make_tuple(action.row, col)] = empty_string;
	            }
	            ++height;
	            break;
	        }
	    }
	}

	void redo() {
	    if (redo_stack.empty()) return;
	    Action action = redo_stack.top();
	    redo_stack.pop();
	    undo_stack.push(action);

	    switch (action.type) {
	        case Action::Set: {
	            if (action.add_value)
	                cell_values.insert(action.value);
	            table[std::make_tuple(action.row, action.col)] = cell_values.get(action.value);
	            break;
	        }
	        case Action::InsertColumn: {
	            columns.insert(action.col);
	            uint64_t i = 0;
	            col_idx_to_name.clear();
	            for (auto& col : columns)
	                col_idx_to_name[i++] = col;
	            for (uint64_t row = 0; row < height; ++row)
	                table[std::make_tuple(row, action.col)] = empty_string;
	            ++width;
	            break;
	        }
	        case Action::InsertRow:
	        case Action::InsertRowAt: {
	            for (auto& col : columns) {
	                for (uint64_t row = height; row > action.row; --row)
	                    table[std::make_tuple(row, col)] = table[std::make_tuple(row - 1, col)];
	                table[std::make_tuple(action.row, col)] = empty_string;
	            }
	            ++height;
	            break;
	        }
	        case Action::RemoveColumn: {
	            columns.erase(action.col);
	            col_idx_to_name.clear();
	            uint64_t i = 0;
	            for (auto& col : columns)
	                col_idx_to_name[i++] = col;
	            for (uint64_t row = 0; row < height; ++row)
	                table.erase(std::make_tuple(row, action.col));
	            --width;
	            break;
	        }
	        case Action::RemoveRow: {
	            for (auto& col : columns) {
	                for (uint64_t row = action.row + 1; row < height; ++row)
	                    table[std::make_tuple(row - 1, col)] = table[std::make_tuple(row, col)];
	                table.erase(std::make_tuple(height - 1, col));
	            }
	            --height;
	            break;
	        }
	    }
	}

public:

    void insert_column(std::string col) {
        if (columns.contains(col))
            throw pybind11::value_error("Column already exists: "+col);
        columns.insert(col);
        uint64_t i=0;
        col_idx_to_name.clear();
        for (auto& col_ : columns)
        	col_idx_to_name[i++] = col_;
        for (uint64_t row = 0; row < height; ++row)
            table[std::make_tuple(row, col)] = empty_string;
        undo_stack.push({ Action::InsertColumn, 0, col, "", "", false});
        while (!redo_stack.empty()) redo_stack.pop();
    }

    void insert_row() {
        uint64_t row = height++;
        for (auto& col_ : columns)
            table[std::make_tuple(row, col)] = empty_string;
        undo_stack.push({ Action::InsertRow, row, "", "", "", false});
        while (!redo_stack.empty()) redo_stack.pop();
    }

    void insert_row(int64_t row) {
    	uint64_t abs_row = abs_index(row,height+1);
        uint64_t new_row = height++;
        for (auto& col : columns) {
	        for (uint64_t row_ = new_row; row_>abs_row; --row_)
	            table[std::make_tuple(row_, col)] = table[std::make_tuple(row_-1, col)];
	        table[std::make_tuple(abs_row, col)] = empty_string;
        }
        undo_stack.push({ Action::InsertRowAt, abs_row, "", "", "", false});
        while (!redo_stack.empty()) redo_stack.pop();
    }

public:

	void remove_column(std::string col) {
	    if (!columns.contains(col))
	        throw pybind11::value_error("Column does not exist: " + col);
	    columns.erase(col);
	    uint64_t i = 0;
	    col_idx_to_name.clear();
	    for (auto& col_ : columns)
	        col_idx_to_name[i++] = col_;
	    for (uint64_t row = 0; row < height; ++row)
	        table.erase(std::make_tuple(row, col));
	    --width;
	    undo_stack.push({ Action::RemoveColumn, 0, col, "", "", false});
	    while (!redo_stack.empty()) redo_stack.pop();
	}

	void remove_column(int64_t col) {
		uint64_t abs_col = abs_index(col,width);	    
	    std::string col_ = col_idx_to_name[abs_col];
	    remove_column(col_);
	}

	void remove_row(int64_t row) {
	    uint64_t abs_row = abs_index(row, height);
        for (auto& col : columns) {
	        for (uint64_t row = abs_row+1; row<height; ++row)
	            table[std::make_tuple(row - 1, col)] = table[std::make_tuple(row, col)];
	        table.erase(std::make_tuple(height-1, col));
        }   
	    --height;
	    undo_stack.push({ Action::RemoveRow, abs_row, "", "", "", false});
	    while (!redo_stack.empty()) redo_stack.pop();
	}

public:

	void set(std::tuple<int64_t, std::string> pos, std::string val) {
	    auto [row, col] = pos;
	    uint64_t abs_row = abs_index(row, height);
	    if (!columns.contains(col))
	        throw pybind11::value_error("Column does not exist: " + col);
	    auto& cell = table[std::make_tuple(abs_row, col)];
	    std::string prev_value = *cell;
	    bool add_value = !cell_values.contains(val);
	    if (add_value) cell_values.insert(val);
	    cell = cell_values.get(val);
	    table[std::make_tuple(abs_row, col)] = cell;
	    undo_stack.push({ Action::Set, abs_row, col, val, prev_value, add_value});
	    while (!redo_stack.empty()) redo_stack.pop();
	}

	void set(std::tuple<int64_t, int64_t> pos, std::string val) {
	    auto [row, col] = pos;
	    uint64_t abs_row = abs_index(row, height);
	    uint64_t abs_col = abs_index(col, width);
	    std::string col_name = col_idx_to_name[abs_col];
	    set(std::make_tuple(abs_row, col_name), val);
	}

	std::string get(std::tuple<int64_t, std::string> pos) {
	    auto [row, col] = pos;
	    uint64_t abs_row = abs_index(row, height);
	    if (!columns.contains(col))
	        throw pybind11::value_error("Column does not exist: " + col);
	    auto it = table.find(std::make_tuple(abs_row, col));
	    if (it != table.end() && it->second)
	        return *(it->second);
	    return "";
	}

	std::string get(std::tuple<int64_t, int64_t> pos) {
	    auto [row, col] = pos;
	    uint64_t abs_row = abs_index(row, height);
	    uint64_t abs_col = abs_index(col, width);
	    std::string col_name = col_idx_to_name[abs_col];
	    return get(std::make_tuple(abs_row, col_name));
	}


public:

    uint64_t row_count() {
        return height;
    }

    uint64_t col_count() {
        return width;
    }

public:

    uint64_t abs_index(int64_t index, uint64_t size) const {
        if (index < 0) index += size;
        if (index < 0 || static_cast<uint64_t>(index) >= size) 
            throw std::out_of_range("Index out of range");
        return index;
    }
};

#endif