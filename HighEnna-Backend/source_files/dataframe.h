#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H

struct DataFrame {
    DataFrame() = default;

private:
    using string_ptr = std::shared_ptr<std::string>;

    struct StringPtrHash {
        using is_transparent = void;
        size_t operator()(const std::string_view& str_view) const { return std::hash<std::string_view>{}(str_view); }
        size_t operator()(const string_ptr& str_ptr) const { return str_ptr ? std::hash<std::string_view>{}(std::string_view(*str_ptr)) : 0; }
        size_t operator()(const std::string& str) const { return std::hash<std::string_view>{}(std::string_view(str)); }
    };

    struct StringPtrEqual {
        using is_transparent = void;
        bool operator()(const string_ptr& lhs, const string_ptr& rhs) const { return *lhs == *rhs; }
        bool operator()(const string_ptr& lhs, const std::string& rhs) const { return *lhs == rhs; }
        bool operator()(const string_ptr& lhs, const std::string_view& rhs) const { return *lhs == rhs; }
        
        bool operator()(const std::string& lhs, const string_ptr& rhs) const { return lhs == *rhs; }
        bool operator()(const std::string& lhs, const std::string& rhs) const { return lhs == rhs; }
        bool operator()(const std::string& lhs, const std::string_view& rhs) const { return lhs == rhs; }
        
        bool operator()(const std::string_view& lhs, const string_ptr& rhs) const { return lhs == *rhs; }
        bool operator()(const std::string_view& lhs, const std::string& rhs) const { return lhs == rhs; }
        bool operator()(const std::string_view& lhs, const std::string_view& rhs) const { return lhs == rhs; }
    };

    using row_t = std::unordered_map<std::string_view, string_ptr, StringPtrHash, StringPtrEqual>;
    using row_ptr = std::shared_ptr<row_t>;

    enum class ActionType {
        SetCell,
        AddRow,
        DuplicateRow,
        DeleteRow,
        AddCol,
        DeleteCol,
        MoveCol,
        MoveRow
    };

    struct Action {
        ActionType type;
        std::list<uint64_t> indices;
        std::list<std::string> names;
        std::list<std::string> values;
    };

    std::unordered_set<string_ptr, StringPtrHash, StringPtrEqual> value_pool;
    std::unordered_set<string_ptr, StringPtrHash, StringPtrEqual> col_name_pool;

    std::vector<uint64_t> logical_to_physical_idx_row;
    std::vector<string_ptr> logical_to_physical_idx_col;

    std::vector<row_ptr> table;

    std::stack<Action> undo_stack;
    std::stack<Action> redo_stack;

public:

    void set(int64_t row_idx, int64_t col_idx, const std::string& value) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size());

        uint64_t                row_physical_idx = logical_to_physical_idx_row[row_logical_idx];
        const string_ptr& col_physical_idx = logical_to_physical_idx_col[col_logical_idx];

        row_ptr& row = table[row_physical_idx];
        (*row)[*col_physical_idx] = internString(value);

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(int64_t row_idx, const std::string& col_name, const std::string& value) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t row_physical_idx = logical_to_physical_idx_row[row_logical_idx];

        row_ptr& row = table[row_physical_idx];
        (*row)[col_name] = internString(value);

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(const std::list<std::tuple<int64_t, int64_t, std::string>>& positions) {
        for (const auto& [row_idx, col_idx, value] : positions) {
            uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
            uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size());

            uint64_t                row_physical_idx = logical_to_physical_idx_row[row_logical_idx];
            const string_ptr& col_physical_idx = logical_to_physical_idx_col[col_logical_idx];

            row_ptr& row = table[row_physical_idx];
            (*row)[*col_physical_idx] = internString(value);
        }

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(const std::list<std::tuple<int64_t, std::string, std::string>>& positions) {
        for (const auto& [row_idx, col_physical_idx, value] : positions) {
            uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
            uint64_t row_physical_idx = logical_to_physical_idx_row[row_logical_idx];

            row_ptr& row = table[row_physical_idx];
            (*row)[col_physical_idx] = internString(value);
        }

        pushUndo(Action{ ActionType::SetCell });
    }

    //--------------------------------------------------------------------------------------------------------

    std::string get(int64_t row_idx, int64_t col_idx) const {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size());

        uint64_t                row_physical_idx = logical_to_physical_idx_row[row_logical_idx];
        const string_ptr& col_physical_idx = logical_to_physical_idx_col[col_logical_idx];

        const row_ptr& row = table[row_physical_idx];
        return *(*row)[*col_physical_idx];
    }

    std::string get(int64_t row_idx, const std::string& col_name) const {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t row_physical_idx = logical_to_physical_idx_row[row_logical_idx];

        if (!col_name_pool.contains(col_name))
            throw std::out_of_range("Key not found in column names.");
        // throw pybind11::key_error("Key not found in column names.");

        const row_ptr& row = table[row_physical_idx];
        return *(*row)[col_name];
    }

    //*--------------------------------------------------------------------------------------------------------

    uint64_t width() { return logical_to_physical_idx_col.size(); }

    uint64_t height() { return logical_to_physical_idx_row.size(); }

    //*--------------------------------------------------------------------------------------------------------

    void addRow() {
        table.emplace_back(std::make_shared<row_t>());
        logical_to_physical_idx_row.push_back(table.size() - 1);
        pushUndo(Action{ ActionType::AddRow });
    }

    void addRow(int64_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size() + 1);
        table.emplace_back(std::make_shared<row_t>());
        logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx, table.size() - 1);
        pushUndo(Action{ ActionType::AddRow });
    }

    void addRow(const std::list<int64_t>& row_indexes) {
        std::list<uint64_t> row_logicals = abs_index(row_indexes, logical_to_physical_idx_row.size());
        for (uint64_t row_logical_idx : row_logicals) {
            table.emplace_back(std::make_shared<row_t>());
            logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx, table.size() - 1);
        }
        pushUndo(Action{ ActionType::AddRow });
    }

    //*--------------------------------------------------------------------------------------------------------

    void duplicateRow(int64_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        table.emplace_back(std::make_shared<row_t>(*table[logical_to_physical_idx_row[row_logical_idx]]));
        logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx + 1, table.size() - 1);
        pushUndo(Action{ ActionType::DuplicateRow });
    }

    void duplicateRow(const std::list<int64_t>& row_indexes) {
        std::list<uint64_t> row_logicals = abs_index(row_indexes, logical_to_physical_idx_row.size());
        for (uint64_t row_logical_idx : row_logicals) {
            table.emplace_back(std::make_shared<row_t>(*table[logical_to_physical_idx_row[row_logical_idx]]));
            logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx + 1, table.size() - 1);
        }
        pushUndo(Action{ ActionType::DuplicateRow });
    }

    //*--------------------------------------------------------------------------------------------------------

    void delRow(int64_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        logical_to_physical_idx_row.erase(logical_to_physical_idx_row.begin() + row_logical_idx);
        pushUndo(Action{ ActionType::DeleteRow });
    }

    void delRow(const std::list<int64_t>& row_indexes) {
        std::list<uint64_t> row_logicals = abs_index(row_indexes, logical_to_physical_idx_row.size());
        for (uint64_t row_logical_idx : row_logicals)
            logical_to_physical_idx_row.erase(logical_to_physical_idx_row.begin() + row_logical_idx);
        pushUndo(Action{ ActionType::DeleteRow });
    }

    //--------------------------------------------------------------------------------------------------------

    void addCol(const std::string& col_name) {
        auto [it, inserted] = col_name_pool.insert(std::make_shared<std::string>(col_name));
        if (inserted) {
            fillCol(col_name);
            logical_to_physical_idx_col.emplace_back(*it);
            pushUndo(Action{ ActionType::AddCol });
        }
    }

    void addCol(const std::list<std::string>& col_names) {
        bool modified = false;
        for (const auto& col_name : col_names) {
            auto [it, inserted] = col_name_pool.insert(std::make_shared<std::string>(col_name));
            if (inserted) {
                fillCol(col_name);
                logical_to_physical_idx_col.emplace_back(*it);
                modified = true;
            }
        }
        if (modified)
            pushUndo(Action{ ActionType::AddCol });
    }

    void addCol(const std::tuple<int64_t, std::string>& indexed_col_name) {
        auto [col_idx, col_name] = indexed_col_name;
        uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size() + 1);

        auto [it, inserted] = col_name_pool.insert(std::make_shared<std::string>(col_name));
        if (inserted) {
            fillCol(col_name);
            logical_to_physical_idx_col.insert(logical_to_physical_idx_col.begin() + col_logical_idx, *it);
            pushUndo(Action{ ActionType::AddCol });
        }
    }

    void addCol(const std::list<std::tuple<int64_t, std::string>>& indexed_col_names) {
        auto logical_indexed_col_names = abs_index(indexed_col_names, logical_to_physical_idx_row.size());
        bool modified = false;
        for (auto [col_logical_idx, col_name] : logical_indexed_col_names) {
            auto [it, inserted] = col_name_pool.insert(std::make_shared<std::string>(col_name));
            if (inserted) {
                fillCol(col_name);
                logical_to_physical_idx_col.insert(logical_to_physical_idx_col.begin() + col_logical_idx, *it);
                modified = true;
            }
        }
        if (modified)
            pushUndo(Action{ ActionType::AddCol });
    }


    //--------------------------------------------------------------------------------------------------------

    void delCol(const std::string& col_name) {
        auto it = std::find(logical_to_physical_idx_col.begin(), logical_to_physical_idx_col.end(), col_name);
        if (it != logical_to_physical_idx_col.end()) {
            logical_to_physical_idx_col.erase(it);
            pushUndo(Action{ ActionType::DeleteCol });
        }
    }

    void delCol(int64_t col_index) {
        uint64_t logical_idx = abs_index(col_index, logical_to_physical_idx_col.size());
        logical_to_physical_idx_col.erase(logical_to_physical_idx_col.begin() + logical_idx);
        pushUndo(Action{ ActionType::DeleteCol });
    }

    void delCol(const std::list<std::string>& col_names) {
        bool modified = false;
        for (const auto& col_name : col_names) {
            auto it = std::find(logical_to_physical_idx_col.begin(), logical_to_physical_idx_col.end(), col_name);
            if (it != logical_to_physical_idx_col.end()) {
                logical_to_physical_idx_col.erase(it);
                modified = true;
            }
        }
        if (modified)
            pushUndo(Action{ ActionType::DeleteCol });
    }

    void delCol(const std::list<int64_t>& col_indexes) {
        std::list<uint64_t> col_logicals = abs_index(col_indexes, logical_to_physical_idx_col.size());
        for (uint64_t col_logical_idx : col_logicals)
            logical_to_physical_idx_col.erase(logical_to_physical_idx_col.begin() + col_logical_idx);
        pushUndo(Action{ ActionType::DeleteCol });
    }

    //--------------------------------------------------------------------------------------------------------

    void moveCol(int64_t from_idx, int64_t to_idx) {
        uint64_t from_logical_idx = abs_index(from_idx, logical_to_physical_idx_col.size());
        uint64_t to_logical_idx = abs_index(to_idx, logical_to_physical_idx_col.size());
        if (from_logical_idx == to_logical_idx) return;

        if (from_logical_idx < to_logical_idx) {
            std::rotate(
                logical_to_physical_idx_col.begin() + from_logical_idx,
                logical_to_physical_idx_col.begin() + from_logical_idx + 1,
                logical_to_physical_idx_col.begin() + to_logical_idx + 1
            );
        }
        else {
            std::rotate(
                logical_to_physical_idx_col.begin() + to_logical_idx,
                logical_to_physical_idx_col.begin() + from_logical_idx,
                logical_to_physical_idx_col.begin() + from_logical_idx + 1
            );
        }

        pushUndo(Action{ ActionType::MoveCol });
    }

    void moveRow(int64_t from_idx, int64_t to_idx) {
        uint64_t from_logical_idx = abs_index(from_idx, logical_to_physical_idx_row.size());
        uint64_t to_logical_idx = abs_index(to_idx, logical_to_physical_idx_row.size());
        if (from_logical_idx == to_logical_idx) return;

        if (from_logical_idx < to_logical_idx) {
            std::rotate(
                logical_to_physical_idx_row.begin() + from_logical_idx,
                logical_to_physical_idx_row.begin() + from_logical_idx + 1,
                logical_to_physical_idx_row.begin() + to_logical_idx + 1
            );
        }
        else {
            std::rotate(
                logical_to_physical_idx_row.begin() + to_logical_idx,
                logical_to_physical_idx_row.begin() + from_logical_idx,
                logical_to_physical_idx_row.begin() + from_logical_idx + 1
            );
        }

        pushUndo(Action{ ActionType::MoveRow });
    }


    //--------------------------------------------------------------------------------------------------------

    void undo() {}
    void redo() {}

private:

    uint64_t abs_index(int64_t index, uint64_t size) const {
        if (index < 0) index += size;
        if (index >= size)
            throw std::out_of_range("Index out of range.");
        // throw pybind11::index_error("Index out of range.");
        return static_cast<uint64_t>(index);
    }

    std::list<uint64_t> abs_index(const std::list<int64_t>& indexes, uint64_t size) const {
        std::list<uint64_t> logicals;
        for (int64_t idx : indexes)
            logicals.push_back(abs_index(idx, size));
        logicals.sort(std::greater<>());
        return logicals;
    }

    std::list<std::tuple<uint64_t, std::string>> abs_index(const std::list<std::tuple<int64_t, std::string>>& indexed_names, uint64_t size) const {
        std::list<std::tuple<uint64_t, std::string>> logicals;
        for (const auto& [idx, name] : indexed_names)
            logicals.emplace_back(abs_index(idx, size), name);
        logicals.sort([](const auto& a, const auto& b) { return std::get<0>(a) > std::get<0>(b); });
        return logicals;
    }

    void fillCol(const std::string& col_name) {
        for (row_ptr& row : table) {
            string_ptr interned_string = internString("");
            (*row)[col_name] = interned_string;
        }
    }

    string_ptr internString(const std::string& str) {
        auto [it, inserted] = value_pool.emplace(std::make_shared<std::string>(str));
        return *it;
    }

    void pushUndo(Action action) {
        undo_stack.push(action);
        while (!redo_stack.empty()) redo_stack.pop();
    }

public:
    void print(std::ostream& os = std::cout) const {
        constexpr size_t MAX_COL_WIDTH = 15;

        os << "Strings: ";
        for (const auto& value_ptr : value_pool)
            os << (*value_ptr) << " (" << value_ptr.use_count() << ")" << ", ";
        os << "\n";

        os << "Columns: ";
        for (const auto& col_name : col_name_pool)
            os << (*col_name) << " (" << col_name.use_count() << ")" << ", ";
        os << "\n\n";

        std::unordered_map<std::string, size_t> column_widths;

        os << "logical_to_physical_idx_row: ";
        for (const auto& row_phy : logical_to_physical_idx_row) {
            os << row_phy << ", ";
        }
        os << "\n";

        os << "logical_to_physical_idx_col: ";
        for (const auto& col_phy : logical_to_physical_idx_col) {
            os << *col_phy << ", ";
            column_widths[(*col_phy)] = std::min((*col_phy).size(), MAX_COL_WIDTH);
        }
        os << "\n\n";

        for (const auto& row : table)
            for (const auto& col_name : logical_to_physical_idx_col)
                column_widths[*col_name] = std::max(column_widths[*col_name], std::min((*(*row)[*col_name]).size(), MAX_COL_WIDTH));

        auto print_separator = [&]() {
            os << "*";
            for (const auto& col_name : logical_to_physical_idx_col)
                os << std::string(column_widths[*col_name] + 2, '-') << "*";
            os << "\n";
            };

        print_separator();

        os << "|";
        for (const auto& col_name : logical_to_physical_idx_col)
            os << " " << std::setw(column_widths[*col_name]) << std::left << *col_name << " |";
        os << "\n";

        os << "*";
        for (const auto& col_name : logical_to_physical_idx_col)
            os << std::string(column_widths[*col_name] + 2, '#') << "*";

        // Print data rows
        for (const auto& row_physical_idx : logical_to_physical_idx_row) {
            const auto& row = table[row_physical_idx];
            os << "|";
            for (const auto& col_name : logical_to_physical_idx_col) {
                std::string value(*((*row)[*col_name]));
                if (value.size() > column_widths[*col_name])
                    value = value.substr(0, column_widths[*col_name] - 3) + "...";
                os << " " << std::setw(column_widths[*col_name]) << std::left << value << " |";
            }
            os << "\n";
            print_separator();
        }

    }

};

#endif
