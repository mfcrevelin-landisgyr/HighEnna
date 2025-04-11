#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H

#include <unordered_set>
#include <unordered_map>
#include <vector>
#include <memory>
#include <string>
#include <string_view>
#include <stack>
#include <list>
#include <tuple>
#include <stdexcept>
#include <algorithm>

struct DataFrame {
    DataFrame() = default;

private:
    using string_ptr = std::shared_ptr<std::string>;
    using row_t = std::unordered_map<std::string, std::string_view>;
    using row_ptr = std::shared_ptr<row_t>;

    struct StringPtrHash {
        using is_transparent = void;
        size_t operator()(std::string_view sv) const {return std::hash<std::string_view>()(sv);}
    };

    struct StringPtrEqual {
        using is_transparent = void;
        bool operator()(const string_ptr& a, const string_ptr& b) const { return *a == *b; }
        bool operator()(const string_ptr& a, std::string_view b) const { return *a == b; }
        bool operator()(std::string_view a, const string_ptr& b) const { return a == *b; }
        bool operator()(const string_ptr& a, const std::string& b) const { return *a == b; }
        bool operator()(const std::string& a, const string_ptr& b) const { return a == *b; }
    };

    enum class ActionType {
        SetCell,
        AddRow,
        DeleteRow,
        AddCol,
        DeleteCol,
        MoveCol,
        MoveRow
    };

    struct Action {
        ActionType type;
        std::list<uint16_t> indices;
        std::list<std::string> names;
        std::list<std::string> values;
    };

    std::unordered_set<string_ptr, StringPtrHash, StringPtrEqual> string_pool;
    std::unordered_set<string_ptr, StringPtrHash, StringPtrEqual> col_names;
    
    std::vector<uint16_t> logical_to_physical_idx_row;
    std::vector<std::string_view> logical_to_physical_idx_col;
    
    std::vector<row_ptr> table;

    std::stack<Action> undo_stack;
    std::stack<Action> redo_stack;

public:

    void set(int16_t row_idx, int16_t col_idx, const std::string& value) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size());

        uint64_t                row_physical = logical_to_physical_idx_row[row_logical_idx]
        const std::string_view& col_physical = logical_to_physical_idx_col[col_logical_idx];

        row_ptr& row = table[row_physical];
        string_ptr interned = internString(value);
        (*row)[col_physical] = *interned;

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(int16_t row_idx, const std::string& col_physical, const std::string& value) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t row_physical = logical_to_physical_idx_row[row_logical_idx]

        row_ptr& row = table[row_physical];
        string_ptr interned = internString(value);
        (*row)[col_physical] = *interned;

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(const std::list<std::tuple<int16_t, int16_t, std::string>>& positions) {
        for (const auto& [row_idx, col_idx, value] : positions) {
            uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
            uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size());

            uint64_t                row_physical = logical_to_physical_idx_row[row_logical_idx]
            const std::string_view& col_physical = logical_to_physical_idx_col[col_logical_idx];

            row_ptr& row = table[row_physical];
            string_ptr interned = internString(value);
            (*row)[col_physical] = *interned;
        }

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(const std::list<std::tuple<int16_t, std::string, std::string>>& positions) {
        for (const auto& [row_idx, col_physical, value] : positions) {
            uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
            uint64_t row_physical = logical_to_physical_idx_row[row_logical_idx]
            
            row_ptr& row = table[row_physical];
            string_ptr interned = internString(value);
            (*row)[col_physical] = *interned;
        }

        pushUndo(Action{ ActionType::SetCell });
    }

    //--------------------------------------------------------------------------------------------------------

    std::string get(int16_t row_idx, int16_t col_idx) const {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size());

        uint64_t                row_physical = logical_to_physical_idx_row[row_logical_idx]
        const std::string_view& col_physical = logical_to_physical_idx_col[col_logical_idx];

        const row_ptr& row = table[row_physical];
        return (*row)[col_physical];
    }

    std::string get(int16_t row_idx, const std::string& col_physical) const {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        uint64_t row_physical = logical_to_physical_idx_row[row_logical_idx]

        if (!col_names.contains(col_physical))
            throw std::out_of_range("Index out of range.");
            // throw pybind11::index_error("Index out of range.");

        const row_ptr& row = table[row_physical];
        return (*row)[col_physical];
    }

    //--------------------------------------------------------------------------------------------------------

    void addRow() {
        table.emplace_back(std::make_shared<row_t>());
        logical_to_physical_idx_row.push_back(table.size() - 1);
        pushUndo(Action{ ActionType::AddRow });
    }

    void addRow(int16_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size() + 1);
        table.emplace_back(std::make_shared<row_t>());
        logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx, table.size() - 1);
        pushUndo(Action{ ActionType::AddRow });
    }

    void addRow(const std::list<int16_t>& row_indexes) {
        std::vector<uint64_t> row_logicals = std::move(abs_index(row_indexes,logical_to_physical_idx_row.size()));
        for (uint64_t row_logical_idx : row_logicals) {
            table.emplace_back(std::make_shared<row_t>());
            logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx, table.size() - 1);
        }
        pushUndo(Action{ ActionType::AddRow });
    }

    //--------------------------------------------------------------------------------------------------------

    void duplicateRow(int16_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        table.emplace_back(std::make_shared<row_t>(*table[logical_to_physical_idx_row[row_logical_idx]]));
        logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx + 1, table.size() - 1);
        pushUndo(Action{ ActionType::DuplicateRow });
    }

    void duplicateRow(const std::list<int16_t>& row_indexes) {
        std::vector<uint64_t> row_logicals = std::move(abs_index(row_indexes,logical_to_physical_idx_row.size()));
        for (uint64_t row_logical_idx : row_logicals) {
            table.emplace_back(std::make_shared<row_t>(*table[logical_to_physical_idx_row[idx]]));
            logical_to_physical_idx_row.insert(logical_to_physical_idx_row.begin() + row_logical_idx + 1, table.size() - 1);
        }
        pushUndo(Action{ ActionType::DuplicateRow });
    }

    //--------------------------------------------------------------------------------------------------------

    void delRow(int16_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, logical_to_physical_idx_row.size());
        logical_to_physical_idx_row.erase(logical_to_physical_idx_row.begin() + row_logical_idx);
        pushUndo(Action{ ActionType::DeleteRow });
    }

    void delRow(const std::list<int16_t>& row_indexes) {
        std::vector<uint64_t> row_logicals = std::move(abs_index(row_indexes,logical_to_physical_idx_row.size()));
        for (uint64_t row_logical_idx : row_logicals)
            logical_to_physical_idx_row.erase(logical_to_physical_idx_row.begin() + row_logical_idx);
        pushUndo(Action{ ActionType::DeleteRow });
    }

    //--------------------------------------------------------------------------------------------------------

    void addCol(const std::string& col_name) {
        auto [it, inserted] = col_names.insert(col_name);
        if (inserted) {
            fillCol(col_name);
            logical_to_physical_idx_col.emplace_back(*it);
            pushUndo(Action{ ActionType::AddCol });
        }
    }

    void addCol(const std::list<std::string>& col_names) {
        bool modified = false;
        for (const auto& col_name : col_names) {
            auto [it, inserted] = col_names.insert(col_name);
            if (inserted) {
                fillCol(col_name);
                logical_to_physical_idx_col.emplace_back(*it);
                modified = true;
            }
            logical_to_physical_idx_col.push_back(col_name);
        }
        if (modified)
            pushUndo(Action{ ActionType::AddCol });
    }

    void addCol(const std::tuple<int16_t, std::string>& indexed_col_name) {
        auto [col_idx, col_name] = indexed_col_name;
        uint64_t col_logical_idx = abs_index(col_idx, logical_to_physical_idx_col.size() + 1);

        auto [it, inserted] = col_names.insert(col_name);
        if (inserted) {
            fillCol(col_name);
            logical_to_physical_idx_col.insert(logical_to_physical_idx_col.begin() + col_logical_idx, col_name_ptr);
            pushUndo(Action{ ActionType::AddCol });
        }
    }

    void addCol(const std::list<std::tuple<int16_t, std::string>>& indexed_col_names) {
        auto logical_indexed_col_names = abs_index(indexed_col_names, logical_to_physical_idx_row.size());
        bool modified = false;
        for (auto [col_logical_idx, col_name] : logical_indexed_col_names){
            auto [it, inserted] = col_names.insert(col_name);
            if (inserted) {
                fillCol(col_name);
                logical_to_physical_idx_col.insert(logical_to_physical_idx_col.begin() + col_logical_idx, col_name_ptr);
                pushUndo(Action{ ActionType::AddCol });
            }
        }
        if (modified)
            pushUndo(Action{ ActionType::AddCol });
    }

    //--------------------------------------------------------------------------------------------------------

    void delCol(const std::string& name) {
        auto it = std::find(logical_to_physical_idx_col.begin(), logical_to_physical_idx_col.end(), name);
        if (it != logical_to_physical_idx_col.end()) {
            logical_to_physical_idx_col.erase(it);
            pushUndo(Action{ ActionType::DeleteCol });
        }
    }

    void delCol(int16_t index) {
        uint64_t idx = abs_index(index, logical_to_physical_idx_col.size());
        logical_to_physical_idx_col.erase(logical_to_physical_idx_col.begin() + idx);
        pushUndo(Action{ ActionType::DeleteColIndexed });
    }

    void delCol(const std::list<std::string>& names) {
        for (auto it = names.rbegin(); it != names.rend(); ++it) {
            delCol(*it);
        }
        pushUndo(Action{ ActionType::DeleteColMultiple });
    }

    void delCol(const std::list<int16_t>& indexes) {
        std::vector<uint64_t> sorted_indexes;
        for (int16_t idx : indexes) {
            sorted_indexes.push_back(abs_index(idx, logical_to_physical_idx_col.size()));
        }
        std::sort(sorted_indexes.rbegin(), sorted_indexes.rend());

        for (uint64_t idx : sorted_indexes) {
            logical_to_physical_idx_col.erase(logical_to_physical_idx_col.begin() + idx);
        }
        pushUndo(Action{ ActionType::DeleteColMultipleIndexed });
    }

    //--------------------------------------------------------------------------------------------------------

    void moveCol(int16_t from_idx, int16_t to_idx) {
        uint64_t from_logical_idx = abs_index(from_idx, logical_to_physical_idx_col.size());
        uint64_t to_logical_idx = abs_index(to_idx, logical_to_physical_idx_col.size());
        if (from_logical_idx == to_logical_idx) return;

        if (from_logical_idx < to_logical_idx) {
            std::rotate(
                logical_to_physical_idx_col.begin() + from_logical_idx,
                logical_to_physical_idx_col.begin() + from_logical_idx + 1,
                logical_to_physical_idx_col.begin() + to_logical_idx + 1
            );
        } else {
            std::rotate(
                logical_to_physical_idx_col.begin() + to_logical_idx,
                logical_to_physical_idx_col.begin() + from_logical_idx,
                logical_to_physical_idx_col.begin() + from_logical_idx + 1
            );
        }

        pushUndo(Action{ ActionType::MoveCol });
    }

    void moveRow(int16_t from_idx, int16_t to_idx) {
        uint64_t from_logical_idx = abs_index(from_idx, logical_to_physical_idx_row.size());
        uint64_t to_logical_idx = abs_index(to_idx, logical_to_physical_idx_row.size());
        if (from_logical_idx == to_logical_idx) return;

        if (from_logical_idx < to_logical_idx) {
            std::rotate(
                logical_to_physical_idx_row.begin() + from_logical_idx,
                logical_to_physical_idx_row.begin() + from_logical_idx + 1,
                logical_to_physical_idx_row.begin() + to_logical_idx + 1
            );
        } else {
            std::rotate(
                logical_to_physical_idx_row.begin() + to_logical_idx,
                logical_to_physical_idx_row.begin() + from_logical_idx,
                logical_to_physical_idx_row.begin() + from_logical_idx + 1
            );
        }

        pushUndo(Action{ ActionType::MoveRow });
    }


    //--------------------------------------------------------------------------------------------------------

    void undo();
    void redo();

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
        for (int16_t idx : indexes) 
            logicals.push_back(abs_index(idx, size));
        logicals.sort(std::greater<>());
        return logicals;
    }

    std::list<std::tuple<uint16_t, std::string>> abs_index(const std::list<std::tuple<int16_t, std::string>>& indexed_names, uint64_t size) const {
        std::list<std::tuple<uint16_t, std::string>> logicals;
        for (const auto& [idx, name] : indexed_names)
            logicals.emplace_back(abs_index(idx, size),name);
        logicals.sort([](const auto& a, const auto& b) { return std::get<0>(a) > std::get<0>(b);});
        return logicals;
    }

    void fillCol(const std::string& col_name) {
        for (row_ptr& row : table) {
            string_ptr interned_string = internString("");
            (*row)[col_name] = *interned_string;
        }
    }

    string_ptr internString(const std::string& str) {
        auto [it, inserted] = string_pool.emplace(std::make_shared<std::string>(str));
        return *it;
    }

    void pushUndo(Action action) {
        undo_stack.push(action);
        while (!redo_stack.empty()) redo_stack.pop();
    }
};

#endif
