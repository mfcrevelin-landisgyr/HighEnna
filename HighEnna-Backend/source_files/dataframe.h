/*

Add to struct Action:
	std::list<uint16_t> indices;
	std::list<uint16_t> names;
	It may have only that and no more members.

Obs:
	1. I liked your Idea of hiding what is settled.
	2. Diferentiate ActionType::AddColMultiple between the indexed and not indexed.
	3. Do not touch undo and redo yet.
*/

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

    struct StringHasher {
        using is_transparent = void;
        size_t operator()(std::string_view sv) const {
            return std::hash<std::string_view>()(sv);
        }
    };

    struct StringEqual {
        using is_transparent = void;
        bool operator()(const string_ptr& a, const string_ptr& b) const {
            return *a == *b;
        }
        bool operator()(const string_ptr& a, std::string_view b) const {
            return *a == b;
        }
        bool operator()(std::string_view a, const string_ptr& b) const {
            return a == *b;
        }
    };

    enum class ActionType {
        SetCell,
        AddRowAtEnd,
        AddRowAtIndex,
        AddRowAtMultiple,
        AddColByName,
        AddColAtIndex,
        AddColMultipleByName,
        AddColMultipleByIndex,
        DuplicateRow,
        DuplicateRowMultiple,
        MoveCol,
        DeleteRowSingle,
        DeleteRowMultiple,
        DeleteColByName,
        DeleteColByIndex,
        DeleteColMultipleByName,
        DeleteColMultipleByIndex
    };

    struct Action {
        ActionType type;
        std::list<uint16_t> indices;
        std::list<uint16_t> names;
    };

    std::unordered_set<string_ptr, StringHasher, StringEqual> string_pool;
    std::vector<row_ptr> table;
    std::vector<uint16_t> logical_to_physical_row;
    std::vector<std::string> logical_to_physical_col;

    std::stack<Action> undo_stack;
    std::stack<Action> redo_stack;

public:
    void set(int16_t row_idx, int16_t col_idx, const std::string& value) {
        uint64_t row_physical = abs_index(row_idx, logical_to_physical_row.size());
        uint64_t col_physical = abs_index(col_idx, logical_to_physical_col.size());
        const std::string& col_name = logical_to_physical_col[col_physical];

        row_ptr& row = table[logical_to_physical_row[row_physical]];
        string_ptr interned = internString(value);
        (*row)[col_name] = *interned;

        pushUndo(Action{ ActionType::SetCell });
    }

    void set(int16_t row_idx, const std::string& col_name, const std::string& value) {
        uint64_t row_physical = abs_index(row_idx, logical_to_physical_row.size());
        row_ptr& row = table[logical_to_physical_row[row_physical]];
        string_ptr interned = internString(value);
        (*row)[col_name] = *interned;

        pushUndo(Action{ ActionType::SetCell });
    }

    std::string get(int16_t row_idx, int16_t col_idx) const {
        uint64_t row_physical = abs_index(row_idx, logical_to_physical_row.size());
        uint64_t col_physical = abs_index(col_idx, logical_to_physical_col.size());
        const std::string& col_name = logical_to_physical_col[col_physical];

        const row_ptr& row = table[logical_to_physical_row[row_physical]];
        auto it = row->find(col_name);
        return (it != row->end()) ? std::string(it->second) : "";
    }

    std::string get(int16_t row_idx, const std::string& col_name) const {
        uint64_t row_physical = abs_index(row_idx, logical_to_physical_row.size());
        const row_ptr& row = table[logical_to_physical_row[row_physical]];
        auto it = row->find(col_name);
        return (it != row->end()) ? std::string(it->second) : "";
    }

    void addRow() {
        table.emplace_back(std::make_shared<row_t>());
        logical_to_physical_row.push_back(table.size() - 1);
        pushUndo(Action{ ActionType::AddRowAtEnd });
    }

    void addRow(int16_t index) {
        uint64_t idx = abs_index(index, logical_to_physical_row.size() + 1);
        table.emplace_back(std::make_shared<row_t>());
        logical_to_physical_row.insert(logical_to_physical_row.begin() + idx, table.size() - 1);
        pushUndo(Action{ ActionType::AddRowAtIndex });
    }

    void addRow(const std::list<int16_t>& indexes) {
        std::vector<uint64_t> sorted_indexes;
        for (int16_t idx : indexes) {
            sorted_indexes.push_back(abs_index(idx, logical_to_physical_row.size() + sorted_indexes.size()));
        }
        std::sort(sorted_indexes.rbegin(), sorted_indexes.rend());

        for (uint64_t idx : sorted_indexes) {
            table.emplace_back(std::make_shared<row_t>());
            logical_to_physical_row.insert(logical_to_physical_row.begin() + idx, table.size() - 1);
        }
        pushUndo(Action{ ActionType::AddRowAtMultiple });
    }

    void duplicateRow(int16_t index) {
        uint64_t idx = abs_index(index, logical_to_physical_row.size());
        row_ptr new_row = std::make_shared<row_t>(*table[logical_to_physical_row[idx]]);
        table.push_back(new_row);
        logical_to_physical_row.insert(logical_to_physical_row.begin() + idx + 1, table.size() - 1);
        pushUndo(Action{ ActionType::DuplicateRow });
    }

    void duplicateRow(const std::list<int16_t>& indexes) {
        std::vector<uint64_t> sorted_indexes;
        for (int16_t idx : indexes) {
            sorted_indexes.push_back(abs_index(idx, logical_to_physical_row.size()));
        }
        std::sort(sorted_indexes.rbegin(), sorted_indexes.rend());

        for (uint64_t idx : sorted_indexes) {
            row_ptr new_row = std::make_shared<row_t>(*table[logical_to_physical_row[idx]]);
            table.push_back(new_row);
            logical_to_physical_row.insert(logical_to_physical_row.begin() + idx + 1, table.size() - 1);
        }
        pushUndo(Action{ ActionType::DuplicateRowMultiple });
    }

    void delRow(int16_t index) {
        uint64_t idx = abs_index(index, logical_to_physical_row.size());
        logical_to_physical_row.erase(logical_to_physical_row.begin() + idx);
        pushUndo(Action{ ActionType::DeleteRowSingle });
    }

    void delRow(const std::list<int16_t>& indexes) {
        std::vector<uint64_t> sorted_indexes;
        for (int16_t idx : indexes) {
            sorted_indexes.push_back(abs_index(idx, logical_to_physical_row.size()));
        }
        std::sort(sorted_indexes.rbegin(), sorted_indexes.rend());

        for (uint64_t idx : sorted_indexes) {
            logical_to_physical_row.erase(logical_to_physical_row.begin() + idx);
        }
        pushUndo(Action{ ActionType::DeleteRowMultiple });
    }

    void addCol(const std::string& name) {
        logical_to_physical_col.push_back(name);
        pushUndo(Action{ ActionType::AddColByName });
    }

    void addCol(const std::tuple<int16_t, std::string>& indexed_name) {
        auto [index, name] = indexed_name;
        uint64_t idx = abs_index(index, logical_to_physical_col.size() + 1);
        logical_to_physical_col.insert(logical_to_physical_col.begin() + idx, name);
        pushUndo(Action{ ActionType::AddColAtIndex });
    }

    void addCol(const std::list<std::string>& names) {
        for (const auto& name : names) {
            logical_to_physical_col.push_back(name);
        }
        pushUndo(Action{ ActionType::AddColMultiple });
    }

    void addCol(const std::list<std::tuple<int16_t, std::string>>& indexed_names) {
        std::vector<std::tuple<uint64_t, std::string>> sorted_indexes;
        for (const auto& [idx, name] : indexed_names) {
            sorted_indexes.emplace_back(abs_index(idx, logical_to_physical_col.size() + sorted_indexes.size()), name);
        }
        std::sort(sorted_indexes.rbegin(), sorted_indexes.rend());

        for (const auto& [idx, name] : sorted_indexes) {
            logical_to_physical_col.insert(logical_to_physical_col.begin() + idx, name);
        }
        pushUndo(Action{ ActionType::AddColMultiple });
    }

    void delCol(const std::string& name) {
        auto it = std::find(logical_to_physical_col.begin(), logical_to_physical_col.end(), name);
        if (it != logical_to_physical_col.end()) {
            logical_to_physical_col.erase(it);
            pushUndo(Action{ ActionType::DeleteColByName });
        }
    }

    void delCol(int16_t index) {
        uint64_t idx = abs_index(index, logical_to_physical_col.size());
        logical_to_physical_col.erase(logical_to_physical_col.begin() + idx);
        pushUndo(Action{ ActionType::DeleteColByIndex });
    }

    void delCol(const std::list<std::string>& names) {
        for (auto it = names.rbegin(); it != names.rend(); ++it) {
            delCol(*it);
        }
        pushUndo(Action{ ActionType::DeleteColMultipleByName });
    }

    void delCol(const std::list<int16_t>& indexes) {
        std::vector<uint64_t> sorted_indexes;
        for (int16_t idx : indexes) {
            sorted_indexes.push_back(abs_index(idx, logical_to_physical_col.size()));
        }
        std::sort(sorted_indexes.rbegin(), sorted_indexes.rend());

        for (uint64_t idx : sorted_indexes) {
            logical_to_physical_col.erase(logical_to_physical_col.begin() + idx);
        }
        pushUndo(Action{ ActionType::DeleteColMultipleByIndex });
    }

    void moveCol(int16_t from, int16_t to) {
        uint64_t from_idx = abs_index(from, logical_to_physical_col.size());
        uint64_t to_idx = abs_index(to, logical_to_physical_col.size());
        if (from_idx == to_idx) return;

        auto col_name = logical_to_physical_col[from_idx];
        logical_to_physical_col.erase(logical_to_physical_col.begin() + from_idx);
        logical_to_physical_col.insert(logical_to_physical_col.begin() + to_idx, col_name);

        pushUndo(Action{ ActionType::MoveCol });
    }

    void undo();
    void redo();

private:
    uint64_t abs_index(int64_t index, uint64_t size) const {
        if (index < 0) index += size;
        if (index >= size)
            throw std::out_of_range("Index out of range.");
        return static_cast<uint64_t>(index);
    }

    string_ptr internString(const std::string& str) {
        auto it = string_pool.find(str);
        if (it != string_pool.end()) return *it;
        auto inserted = std::make_shared<std::string>(str);
        string_pool.insert(inserted);
        return inserted;
    }

    void pushUndo(Action action) {
        undo_stack.push(action);
        while (!redo_stack.empty()) redo_stack.pop();
    }
};

#endif
