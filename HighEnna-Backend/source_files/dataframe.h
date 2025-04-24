#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H


struct DataFrame {

private:

    enum class ActionType {
        SetVal,
        AddRow,
        DelRow,
        MovRow,
        AddCol,
        DelCol,
        MovCol,
    };

    struct Action {
        ActionType typ;
        std::list<uint64_t>     row_log;
        std::list<uint64_t>     row_phy;
        std::list<uint64_t>     col_log;
        std::list<uint64_t>     col_phy;
        std::list<std::string>  col_nme;
        std::list<std::string>  new_val;
        std::list<std::string>  old_val;
        Action(ActionType action_type) : typ(action_type) {}
    };

private:


    std::unordered_set<std::string> col_name_pool;

    std::vector<uint64_t> row_idx_logical_to_physical;
    std::vector<uint64_t> col_idx_logical_to_physical;

    std::vector<std::unordered_map<std::string,std::string>> rows;
    std::vector<std::string> cols;

    std::stack<std::shared_ptr<Action>> undo_stack;
    std::stack<std::shared_ptr<Action>> redo_stack;

public:

    size_t rowCount() const { return row_idx_logical_to_physical.size(); }
    size_t colCount() const { return col_idx_logical_to_physical.size(); }

public:

    std::string getCol(int64_t col_idx) {
        uint64_t col_logical_idx = abs_index(col_idx, col_idx_logical_to_physical.size());
        uint64_t col_physical_idx = col_idx_logical_to_physical[col_logical_idx];
        return cols[col_physical_idx];
    }

    std::unordered_map<std::string,std::string> getRow(int64_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, row_idx_logical_to_physical.size());
        uint64_t row_physical_idx = row_idx_logical_to_physical[row_logical_idx];
        return rows[row_physical_idx];
    }

    std::string getVal(int64_t row_idx, int64_t col_idx) {

        uint64_t row_logical_idx = abs_index(row_idx, row_idx_logical_to_physical.size());
        uint64_t col_logical_idx = abs_index(col_idx, col_idx_logical_to_physical.size());

        uint64_t row_physical_idx = row_idx_logical_to_physical[row_logical_idx];
        uint64_t col_physical_idx = col_idx_logical_to_physical[col_logical_idx];

        auto& row = rows[row_physical_idx];
        auto& col = cols[col_physical_idx];

        return row[col];
    }

    void set(const std::list<std::tuple<int64_t, int64_t, std::string>>& items) {
        auto& action = pushUndo(ActionType::SetVal);

        for (const auto& [row_idx, col_idx, val] : items) {

            uint64_t row_logical_idx = abs_index(row_idx, row_idx_logical_to_physical.size());
            uint64_t col_logical_idx = abs_index(col_idx, col_idx_logical_to_physical.size());

            uint64_t row_physical_idx = row_idx_logical_to_physical[row_logical_idx];
            uint64_t col_physical_idx = col_idx_logical_to_physical[col_logical_idx];

            auto& row = rows[row_physical_idx];
            auto& col = cols[col_physical_idx];

            std::string old = row[col];

            action.row_phy.push_back(row_physical_idx);
            action.col_phy.push_back(col_physical_idx);
            action.col_nme.push_back(col);
            action.new_val.push_back(val);
            action.old_val.push_back(old);

            row[col] = val;
        }
    }

public:

    void addRow(int64_t n_rows) {
        auto& action = pushUndo(ActionType::AddRow);

        for (int64_t i=0; i<n_rows; ++i) {
            uint64_t row_logical_idx = row_idx_logical_to_physical.size();
            rows.emplace_back();
            row_idx_logical_to_physical.insert(row_idx_logical_to_physical.begin() + row_logical_idx, rows.size() - 1);
            action.row_log.push_back(row_logical_idx);
            action.row_phy.push_back(rows.size() - 1);
        }
    }

    void addRow(const std::list<int64_t>& row_indexes) {
        auto& action = pushUndo(ActionType::AddRow);

        std::list<uint64_t> row_logicals = abs_index(row_indexes, row_idx_logical_to_physical.size()+1);
        for (uint64_t row_logical_idx : row_logicals) {
            rows.emplace_back();
            row_idx_logical_to_physical.insert(row_idx_logical_to_physical.begin() + row_logical_idx, rows.size() - 1);
            action.row_log.push_back(row_logical_idx);
            action.row_phy.push_back(rows.size() - 1);
        }
    }

    void duplicateRow(const std::list<int64_t>& row_indexes) {
        pushUndo(ActionType::AddRow);
        auto& action = *(undo_stack.top());

        std::list<uint64_t> row_logicals = abs_index(row_indexes, row_idx_logical_to_physical.size());
        for (uint64_t row_logical_idx : row_logicals) {
            uint64_t row_physical_idx = row_idx_logical_to_physical[row_logical_idx];
            rows.emplace_back(rows[row_physical_idx]);
            row_idx_logical_to_physical.insert(row_idx_logical_to_physical.begin() + row_logical_idx+1, rows.size() - 1);
            action.row_log.push_back(row_logical_idx+1);
            action.row_phy.push_back(rows.size() - 1);
        }
    }

    void delRow(const std::list<int64_t>& row_indexes) {
        auto& action = pushUndo(ActionType::DelRow);

        std::list<uint64_t> row_logicals = abs_index(row_indexes, row_idx_logical_to_physical.size());
        for (uint64_t row_logical_idx : row_logicals) {
            uint64_t row_physical_idx = row_idx_logical_to_physical[row_logical_idx];
            action.row_log.push_back(row_logical_idx);
            action.row_phy.push_back(row_physical_idx);
            row_idx_logical_to_physical.erase(row_idx_logical_to_physical.begin() + row_logical_idx);
        }
    }

public:

    void addCol(const std::list<std::string>& col_names) {
        auto& action = pushUndo(ActionType::AddCol);

        for (const std::string& col_name : col_names) {
            if (!col_name_pool.contains(col_name)){
                
                col_name_pool.insert(col_name);
                cols.emplace_back(col_name);
                
                uint64_t col_logical_idx = col_idx_logical_to_physical.size();
                uint64_t col_physical_idx = cols.size() - 1;
                
                col_idx_logical_to_physical.insert(col_idx_logical_to_physical.begin() + col_logical_idx, col_physical_idx);
                
                action.col_log.push_back(col_logical_idx);
                action.col_phy.push_back(col_physical_idx);
                action.col_nme.push_back(col_name);
            
            }
        }
    }

    void delCol(const std::list<int64_t>& col_indexes) {
        auto& action = pushUndo(ActionType::DelCol);

        std::list<uint64_t> col_logicals = abs_index(col_indexes, col_idx_logical_to_physical.size());
        for (uint64_t col_logical_idx : col_logicals) {
            uint64_t col_physical_idx = col_idx_logical_to_physical[col_logical_idx];

            col_name_pool.erase(cols[col_physical_idx]);
            col_idx_logical_to_physical.erase(col_idx_logical_to_physical.begin() + col_logical_idx);
            
            action.col_log.push_back(col_logical_idx);
            action.col_phy.push_back(col_physical_idx);
            action.col_nme.push_back(cols[col_physical_idx]);
        }
    }


public:

    void undo() {
        if (undo_stack.empty()) return;

        redo_stack.emplace(undo_stack.top());
        auto& action = *(undo_stack.top());
        undo_stack.pop();

        switch (action.typ) {
            case ActionType::SetVal: {
                auto it_row_phy = action.row_phy.rbegin();
                auto it_col_phy = action.col_phy.rbegin();
                auto it_old_val = action.old_val.rbegin();

                for (; it_row_phy != action.row_phy.rend(); ++it_row_phy, ++it_col_phy, ++it_old_val) {
                    auto& row = rows[*it_row_phy];
                    auto& col = cols[*it_col_phy];
                    row[col] = *it_old_val;
                }

                break;
            }

            case ActionType::AddRow: {
                auto it_row_log = action.row_log.rbegin();

                for (; it_row_log != action.row_log.rend(); ++it_row_log)
                    row_idx_logical_to_physical.erase(row_idx_logical_to_physical.begin() + *it_row_log);

                break;
            }

            case ActionType::AddCol: {
                auto it_col_log = action.col_log.rbegin();
                auto it_col_nme = action.col_nme.rbegin();

                for (; it_col_log != action.col_log.rend(); ++it_col_log, ++it_col_nme) {
                    col_name_pool.erase(*it_col_nme);
                    col_idx_logical_to_physical.erase(col_idx_logical_to_physical.begin() + *it_col_log);
                }

                break;
            }

            case ActionType::DelRow: {
                auto it_row_log = action.row_log.rbegin();
                auto it_row_phy = action.row_phy.rbegin();

                for (; it_row_log != action.row_log.rend(); ++it_row_log, ++it_row_phy)
                    row_idx_logical_to_physical.insert(row_idx_logical_to_physical.begin() + *it_row_log, *it_row_phy);

                break;
            }

            case ActionType::DelCol: {
                auto it_col_log = action.col_log.rbegin();
                auto it_col_phy = action.col_phy.rbegin();
                auto it_col_nme = action.col_nme.rbegin();

                for (; it_col_log != action.col_log.rend(); ++it_col_log, ++it_col_phy, ++it_col_nme) {
                    col_name_pool.insert(*it_col_nme);
                    col_idx_logical_to_physical.insert(col_idx_logical_to_physical.begin() + *it_col_log, *it_col_phy);
                }
                break;
            }


            default:
                break;
        }
    }

    void redo() {
        if (redo_stack.empty()) return;

        undo_stack.emplace(redo_stack.top());
        auto& action = *(redo_stack.top());
        redo_stack.pop();

        switch (action.typ) {
            case ActionType::SetVal: {
                auto it_row_phy = action.row_phy.begin();
                auto it_col_phy = action.col_phy.begin();
                auto it_new_val = action.new_val.begin();

                for (; it_row_phy != action.row_phy.end(); ++it_row_phy, ++it_col_phy, ++it_new_val) {
                    auto& row = rows[*it_row_phy];
                    auto& col = cols[*it_col_phy];
                    row[col] = *it_new_val;
                }

                break;
            }

            case ActionType::AddRow: {
                auto it_row_log = action.row_log.begin();
                auto it_row_phy = action.row_phy.begin();

                for (; it_row_log != action.row_log.end(); ++it_row_log, ++it_row_phy)
                    row_idx_logical_to_physical.insert(row_idx_logical_to_physical.begin() + *it_row_log, *it_row_phy);

                break;
            }

            case ActionType::AddCol: {
                auto it_col_log = action.col_log.begin();
                auto it_col_phy = action.col_phy.begin();
                auto it_col_nme = action.col_nme.begin();

                for (; it_col_log != action.col_log.end(); ++it_col_log, ++it_col_phy, ++it_col_nme) {
                    col_name_pool.insert(*it_col_nme);
                    col_idx_logical_to_physical.insert(col_idx_logical_to_physical.begin() + *it_col_log,*it_col_phy);
                }

                break;
            }

            case ActionType::DelRow: {
                auto it_row_log = action.row_log.begin();

                for (; it_row_log != action.row_log.end(); ++it_row_log)
                    row_idx_logical_to_physical.erase(row_idx_logical_to_physical.begin() + *it_row_log);

                break;
            }

            case ActionType::DelCol: {
                auto it_col_log = action.col_log.begin();
                auto it_col_nme = action.col_nme.begin();

                for (; it_col_log != action.col_log.end(); ++it_col_log, ++it_col_nme) {
                    col_name_pool.erase(*it_col_nme);
                    col_idx_logical_to_physical.erase(col_idx_logical_to_physical.begin() + *it_col_log);
                }
                break;
            }


            default:
                break;
        }

    }

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

    Action& pushUndo(ActionType action_type) {
        undo_stack.emplace(std::make_shared<Action>(action_type));
        while (!redo_stack.empty()) redo_stack.pop();
        return *(undo_stack.top());
    }

public:
    void print(std::ostream& os = std::cout) {
        os << "\ncol_name_pool: ";
        uint64_t i=0;
        for (const auto& col_name : col_name_pool) {
            os << "\"" << col_name << "\"";
            if (i + 1 < row_idx_logical_to_physical.size()) os << ", ";
            ++i;
        }

        os << "\nrow_idx: ";
        for (size_t i = 0; i < row_idx_logical_to_physical.size(); ++i) {
            os << row_idx_logical_to_physical[i];
            if (i + 1 < row_idx_logical_to_physical.size()) os << ", ";
        }

        os << "\ncol_idx: ";
        for (size_t i = 0; i < col_idx_logical_to_physical.size(); ++i) {
            os << col_idx_logical_to_physical[i];
            if (i + 1 < col_idx_logical_to_physical.size()) os << ", ";
        }
        os << "\n\n";

        std::unordered_map<std::string, size_t> col_widths;
        for (const auto& col : cols) {
            col_widths[col] = col.size();
            for (auto& row : rows)
                col_widths[col] = std::max(col_widths[col], (row[col]).size());
        }


        auto printBorder = [&](const auto& col_order, char corner, char fill) {
            os << corner;
            for (size_t i : col_order) {
                os << std::string(col_widths[cols[i]] + 2, fill) << corner;
            }
            os << "\n";
        };

        auto printTable = [&](const std::vector<size_t>& row_order, const std::vector<size_t>& col_order) {
            printBorder(col_order,'+', '-');
            os << "|";
            for (size_t col_i : col_order) {
                os << " " << std::setw(col_widths[cols[col_i]]) << cols[col_i] << " |";
            }
            os << "\n";
            printBorder(col_order,'+', '=');

            for (size_t row_i : row_order) {
                auto& row = rows[row_i];
                os << "|";
                for (size_t col_i : col_order) 
                    os << " " << std::setw(col_widths[cols[col_i]]) << row[cols[col_i]] << " |";
                os << "\n";
                printBorder(col_order,'+', '-');
            }
        };

        std::vector<size_t> true_row_order(rows.size());
        std::iota(true_row_order.begin(), true_row_order.end(), 0);
        std::vector<size_t> true_col_order(cols.size());
        std::iota(true_col_order.begin(), true_col_order.end(), 0);
        
        os << "\n  === TABLE (Physical Order) ===\n\n";
        printTable(true_row_order, true_col_order);

        os << "\n  === TABLE (Logical Order) ===\n\n";
        printTable(row_idx_logical_to_physical, col_idx_logical_to_physical);

        os << "\n";
    }


};

#endif