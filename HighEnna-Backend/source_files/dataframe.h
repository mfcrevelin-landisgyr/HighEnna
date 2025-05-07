#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H


struct DataFrame {

private:

    enum class ActionType {
        SetVal,
        AddRow,
        AddCol,
        DelRow,
        DelCol,
        MovRow,
        MovCol,
    };

    struct Action {
        ActionType typ;
        std::list<uint64_t>     row_lgc;
        std::list<uint64_t>     row_phy;
        std::list<uint64_t>     col_lgc;
        std::list<uint64_t>     col_phy;
        std::list<std::string>  col_nme;
        std::list<std::string>  new_val;
        std::list<std::string>  old_val;
        Action(ActionType action_type) : typ(action_type) {}
    };

private:

    std::unordered_set<std::string> col_name_pool;

    std::vector<std::unordered_map<std::string,std::string>> rows;
    std::vector<pybind11::dict> globals;
    std::vector<std::string> cols;

    std::unordered_set<uint64_t> changed_globals_physical_idx;

    std::vector<uint64_t> row_map_logical_to_physical;
    std::vector<uint64_t> col_map_logical_to_physical;

    std::stack<std::shared_ptr<Action>> undo_stack;
    std::stack<std::shared_ptr<Action>> redo_stack;

public:

    size_t rowCount() const { return row_map_logical_to_physical.size(); }
    size_t colCount() const { return col_map_logical_to_physical.size(); }

public:

    std::string getCol(int64_t col_idx) {
        uint64_t col_logical_idx = abs_index(col_idx, col_map_logical_to_physical.size());
        uint64_t col_physical_idx = col_map_logical_to_physical[col_logical_idx];
        return cols[col_physical_idx];
    }

    std::unordered_map<std::string,std::string> getRow(int64_t row_idx) {
        uint64_t row_logical_idx = abs_index(row_idx, row_map_logical_to_physical.size());
        uint64_t row_physical_idx = row_map_logical_to_physical[row_logical_idx];
        return rows[row_physical_idx];
    }

    std::string getCell(int64_t row_idx, int64_t col_idx) {

        uint64_t row_logical_idx = abs_index(row_idx, row_map_logical_to_physical.size());
        uint64_t col_logical_idx = abs_index(col_idx, col_map_logical_to_physical.size());

        uint64_t row_physical_idx = row_map_logical_to_physical[row_logical_idx];
        uint64_t col_physical_idx = col_map_logical_to_physical[col_logical_idx];

        auto& row = rows[row_physical_idx];
        auto& col = cols[col_physical_idx];

        return row[col];
    }

    void setCell(const std::list<std::tuple<int64_t, int64_t, std::string>>& items) {
        auto& action = pushUndo(ActionType::SetVal);

        if (!items.empty()) {
            pybind11::gil_scoped_acquire gil;
            for (const auto& [row_idx, col_idx, val] : items) {

                uint64_t row_logical_idx = abs_index(row_idx, row_map_logical_to_physical.size());
                uint64_t col_logical_idx = abs_index(col_idx, col_map_logical_to_physical.size());

                uint64_t row_physical_idx = row_map_logical_to_physical[row_logical_idx];
                uint64_t col_physical_idx = col_map_logical_to_physical[col_logical_idx];

                auto& global = globals[row_physical_idx];
                auto& row = rows[row_physical_idx];
                auto& col = cols[col_physical_idx];

                std::string old = row[col];

                action.row_phy.push_back(row_physical_idx);
                action.col_phy.push_back(col_physical_idx);
                action.col_nme.push_back(col);
                action.new_val.push_back(val);
                action.old_val.push_back(old);

                row[col] = val;

                // try {
                    if (val.empty())
                        global.attr("pop")("var_" + col, pybind11::none());
                    else
                        pybind11::exec("var_"+col+" = "+val, global);

                    std::cout << row_logical_idx << ", " << col_logical_idx << ", \"" << val << "\" -> {";
                    uint64_t i=0;
                    for (auto item : global) {
                        std::string key = pybind11::str(item.first);
                        if (key == "__builtins__")
                            continue;
                        std::cout << key << ": \"" << pybind11::str(item.second) << "\"";
                        auto xx = global.attr("__len__")();
                        if (i+1<pybind11::int_(global.attr("__len__")()))
                            std::cout << ", ";
                        ++i;
                    }
                    std::cout << "}" << std::endl;
                // }
                // catch (pybind11::error_already_set& e) {
                    // std::cerr << e.what() << std::endl;
                    // e.restore();
                    // throw e;
                // }
            }
        }
    }

public:

    void addRow(int64_t n_rows) {
        auto& action = pushUndo(ActionType::AddRow);

        if (n_rows) {
            pybind11::gil_scoped_acquire gil;
            for (int64_t i=0; i<n_rows; ++i) {
                uint64_t row_logical_idx = row_map_logical_to_physical.size();
                rows.emplace_back();
                globals.emplace_back();
                globals[globals.size()-1]["__builtins__"] = pybind11::module::import("builtins").attr("__dict__");
                row_map_logical_to_physical.insert(row_map_logical_to_physical.begin() + row_logical_idx, rows.size() - 1);
                action.row_lgc.push_back(row_logical_idx);
                action.row_phy.push_back(rows.size() - 1);
            }
        }
    }

    void addRow(const std::list<int64_t>& row_indexes) {
        auto& action = pushUndo(ActionType::AddRow);

        std::list<uint64_t> row_logical_indexes = abs_index(row_indexes, row_map_logical_to_physical.size()+1);
        if (!row_logical_indexes.empty()){
            pybind11::gil_scoped_acquire gil;
            for (uint64_t row_logical_idx : row_logical_indexes) {
                rows.emplace_back();
                globals.emplace_back();
                globals[globals.size()-1]["__builtins__"] = pybind11::module::import("builtins").attr("__dict__");
                row_map_logical_to_physical.insert(row_map_logical_to_physical.begin() + row_logical_idx, rows.size() - 1);
                action.row_lgc.push_back(row_logical_idx);
                action.row_phy.push_back(rows.size() - 1);
            }
        }
    }

    void duplicateRow(const std::list<int64_t>& row_indexes) {
        pushUndo(ActionType::AddRow);
        auto& action = *(undo_stack.top());

        std::list<uint64_t> row_logical_indexes = abs_index(row_indexes, row_map_logical_to_physical.size());
        if (!row_logical_indexes.empty()){
            pybind11::gil_scoped_acquire gil;
            for (uint64_t row_logical_idx : row_logical_indexes) {
                uint64_t row_physical_idx = row_map_logical_to_physical[row_logical_idx];
                rows.emplace_back(rows[row_physical_idx]);
                globals.emplace_back(globals[row_physical_idx]);
                row_map_logical_to_physical.insert(row_map_logical_to_physical.begin() + row_logical_idx+1, rows.size() - 1);
                action.row_lgc.push_back(row_logical_idx+1);
                action.row_phy.push_back(rows.size() - 1);
            }
        }
    }

    void delRow(const std::list<int64_t>& row_indexes) {
        auto& action = pushUndo(ActionType::DelRow);

        std::list<uint64_t> row_logical_indexes = abs_index(row_indexes, row_map_logical_to_physical.size());
        for (uint64_t row_logical_idx : row_logical_indexes) {
            uint64_t row_physical_idx = row_map_logical_to_physical[row_logical_idx];
            action.row_lgc.push_back(row_logical_idx);
            action.row_phy.push_back(row_physical_idx);
            row_map_logical_to_physical.erase(row_map_logical_to_physical.begin() + row_logical_idx);
        }
    }

public:

    void addCol(const std::list<std::string>& col_names) {
        auto& action = pushUndo(ActionType::AddCol);

        for (const std::string& col_name : col_names) {
            if (!col_name_pool.contains(col_name)){
                
                col_name_pool.insert(col_name);
                cols.emplace_back(col_name);
                
                uint64_t col_logical_idx = col_map_logical_to_physical.size();
                uint64_t col_physical_idx = cols.size() - 1;
                
                col_map_logical_to_physical.insert(col_map_logical_to_physical.begin() + col_logical_idx, col_physical_idx);
                
                action.col_lgc.push_back(col_logical_idx);
                action.col_phy.push_back(col_physical_idx);
                action.col_nme.push_back(col_name);
            
            }
        }
    }

    void delCol(const std::list<int64_t>& col_indexes) {
        auto& action = pushUndo(ActionType::DelCol);

        std::list<uint64_t> col_logicals = abs_index(col_indexes, col_map_logical_to_physical.size());
        for (uint64_t col_logical_idx : col_logicals) {
            uint64_t col_physical_idx = col_map_logical_to_physical[col_logical_idx];

            col_name_pool.erase(cols[col_physical_idx]);
            col_map_logical_to_physical.erase(col_map_logical_to_physical.begin() + col_logical_idx);
            
            action.col_lgc.push_back(col_logical_idx);
            action.col_phy.push_back(col_physical_idx);
            action.col_nme.push_back(cols[col_physical_idx]);
        }
    }

public:

    void moveCol(int64_t idx_from, int64_t idx_to) {
        auto& action = pushUndo(ActionType::MovCol);

        // uint64_t logical_idx_from = abs_index( idx_from , col_map_logical_to_physical.size());
        // uint64_t logical_idx_to   = abs_index( idx_to   , col_map_logical_to_physical.size());

        // if (logical_idx_from == logical_idx_to) return;

        // action.col_lgc.push_back(logical_idx_from);
        // action.col_lgc.push_back(logical_idx_to);

        // if (logical_idx_from < logical_idx_to) {
        //     std::rotate(
        //         col_map_logical_to_physical.begin() + logical_idx_from,
        //         col_map_logical_to_physical.begin() + logical_idx_from + 1,
        //         col_map_logical_to_physical.begin() + logical_idx_to + 1
        //     );
        // }
        // else {
        //     std::rotate(
        //         col_map_logical_to_physical.begin() + logical_idx_to,
        //         col_map_logical_to_physical.begin() + logical_idx_from,
        //         col_map_logical_to_physical.begin() + logical_idx_from + 1
        //     );
        // }
    }

    void moveRow(int64_t idx_from, int64_t idx_to) {
        auto& action = pushUndo(ActionType::MovRow);

        // uint64_t logical_idx_from = abs_index( idx_from , row_map_logical_to_physical.size());
        // uint64_t logical_idx_to   = abs_index( idx_to   , row_map_logical_to_physical.size());
        
        // if (logical_idx_from == logical_idx_to) return;

        // action.row_lgc.push_back(logical_idx_from);
        // action.row_lgc.push_back(logical_idx_to);

        // if (logical_idx_from < logical_idx_to) {
        //     std::rotate(
        //         row_map_logical_to_physical.begin() + logical_idx_from,
        //         row_map_logical_to_physical.begin() + logical_idx_from + 1,
        //         row_map_logical_to_physical.begin() + logical_idx_to + 1
        //     );
        // }
        // else {
        //     std::rotate(
        //         row_map_logical_to_physical.begin() + logical_idx_to,
        //         row_map_logical_to_physical.begin() + logical_idx_from,
        //         row_map_logical_to_physical.begin() + logical_idx_from + 1
        //     );
        // }
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
                auto it_row_lgc = action.row_lgc.rbegin();

                for (; it_row_lgc != action.row_lgc.rend(); ++it_row_lgc)
                    row_map_logical_to_physical.erase(row_map_logical_to_physical.begin() + *it_row_lgc);

                break;
            }

            case ActionType::AddCol: {
                auto it_col_lgc = action.col_lgc.rbegin();
                auto it_col_nme = action.col_nme.rbegin();

                for (; it_col_lgc != action.col_lgc.rend(); ++it_col_lgc, ++it_col_nme) {
                    col_name_pool.erase(*it_col_nme);
                    col_map_logical_to_physical.erase(col_map_logical_to_physical.begin() + *it_col_lgc);
                }

                break;
            }

            case ActionType::DelRow: {
                auto it_row_lgc = action.row_lgc.rbegin();
                auto it_row_phy = action.row_phy.rbegin();

                for (; it_row_lgc != action.row_lgc.rend(); ++it_row_lgc, ++it_row_phy)
                    row_map_logical_to_physical.insert(row_map_logical_to_physical.begin() + *it_row_lgc, *it_row_phy);

                break;
            }

            case ActionType::DelCol: {
                auto it_col_lgc = action.col_lgc.rbegin();
                auto it_col_phy = action.col_phy.rbegin();
                auto it_col_nme = action.col_nme.rbegin();

                for (; it_col_lgc != action.col_lgc.rend(); ++it_col_lgc, ++it_col_phy, ++it_col_nme) {
                    col_name_pool.insert(*it_col_nme);
                    col_map_logical_to_physical.insert(col_map_logical_to_physical.begin() + *it_col_lgc, *it_col_phy);
                }
                break;
            }

            case ActionType::MovCol: {
                // auto it_col_lgc = action.col_lgc.rbegin();

                // uint64_t logical_idx_from = *(it_col_lgc++);
                // uint64_t logical_idx_to   = *it_col_lgc;

                // if (logical_idx_from < logical_idx_to) {
                //     std::rotate(
                //         col_map_logical_to_physical.begin() + logical_idx_from,
                //         col_map_logical_to_physical.begin() + logical_idx_from + 1,
                //         col_map_logical_to_physical.begin() + logical_idx_to + 1
                //     );
                // }
                // else {
                //     std::rotate(
                //         col_map_logical_to_physical.begin() + logical_idx_to,
                //         col_map_logical_to_physical.begin() + logical_idx_from,
                //         col_map_logical_to_physical.begin() + logical_idx_from + 1
                //     );
                // }

                break;
            }

            case ActionType::MovRow: {
                // auto it_row_lgc = action.row_lgc.rbegin();

                // uint64_t logical_idx_from = *(it_row_lgc++);
                // uint64_t logical_idx_to   = *it_row_lgc;

                // if (logical_idx_from < logical_idx_to) {
                //     std::rotate(
                //         row_map_logical_to_physical.begin() + logical_idx_from,
                //         row_map_logical_to_physical.begin() + logical_idx_from + 1,
                //         row_map_logical_to_physical.begin() + logical_idx_to + 1
                //     );
                // }
                // else {
                //     std::rotate(
                //         row_map_logical_to_physical.begin() + logical_idx_to,
                //         row_map_logical_to_physical.begin() + logical_idx_from,
                //         row_map_logical_to_physical.begin() + logical_idx_from + 1
                //     );
                // }
                
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
                auto it_row_lgc = action.row_lgc.begin();
                auto it_row_phy = action.row_phy.begin();

                for (; it_row_lgc != action.row_lgc.end(); ++it_row_lgc, ++it_row_phy)
                    row_map_logical_to_physical.insert(row_map_logical_to_physical.begin() + *it_row_lgc, *it_row_phy);

                break;
            }

            case ActionType::AddCol: {
                auto it_col_lgc = action.col_lgc.begin();
                auto it_col_phy = action.col_phy.begin();
                auto it_col_nme = action.col_nme.begin();

                for (; it_col_lgc != action.col_lgc.end(); ++it_col_lgc, ++it_col_phy, ++it_col_nme) {
                    col_name_pool.insert(*it_col_nme);
                    col_map_logical_to_physical.insert(col_map_logical_to_physical.begin() + *it_col_lgc,*it_col_phy);
                }

                break;
            }

            case ActionType::DelRow: {
                auto it_row_lgc = action.row_lgc.begin();

                for (; it_row_lgc != action.row_lgc.end(); ++it_row_lgc)
                    row_map_logical_to_physical.erase(row_map_logical_to_physical.begin() + *it_row_lgc);

                break;
            }

            case ActionType::DelCol: {
                auto it_col_lgc = action.col_lgc.begin();
                auto it_col_nme = action.col_nme.begin();

                for (; it_col_lgc != action.col_lgc.end(); ++it_col_lgc, ++it_col_nme) {
                    col_name_pool.erase(*it_col_nme);
                    col_map_logical_to_physical.erase(col_map_logical_to_physical.begin() + *it_col_lgc);
                }
                break;
            }

            case ActionType::MovCol: {
                // auto it_col_lgc = action.col_lgc.begin();

                // uint64_t logical_idx_from = *(it_col_lgc++);
                // uint64_t logical_idx_to   = *it_col_lgc;

                // if (logical_idx_from < logical_idx_to) {
                //     std::rotate(
                //         col_map_logical_to_physical.begin() + logical_idx_from,
                //         col_map_logical_to_physical.begin() + logical_idx_from + 1,
                //         col_map_logical_to_physical.begin() + logical_idx_to + 1
                //     );
                // }
                // else {
                //     std::rotate(
                //         col_map_logical_to_physical.begin() + logical_idx_to,
                //         col_map_logical_to_physical.begin() + logical_idx_from,
                //         col_map_logical_to_physical.begin() + logical_idx_from + 1
                //     );
                // }

                break;
            }

            case ActionType::MovRow: {
                // auto it_row_lgc = action.row_lgc.begin();

                // uint64_t logical_idx_from = *(it_row_lgc++);
                // uint64_t logical_idx_to   = *it_row_lgc;

                // if (logical_idx_from < logical_idx_to) {
                //     std::rotate(
                //         row_map_logical_to_physical.begin() + logical_idx_from,
                //         row_map_logical_to_physical.begin() + logical_idx_from + 1,
                //         row_map_logical_to_physical.begin() + logical_idx_to + 1
                //     );
                // }
                // else {
                //     std::rotate(
                //         row_map_logical_to_physical.begin() + logical_idx_to,
                //         row_map_logical_to_physical.begin() + logical_idx_from,
                //         row_map_logical_to_physical.begin() + logical_idx_from + 1
                //     );
                // }
                
                break;
            }


            default:
                break;
        }

    }

private:

    void rotate(std::vector<uint64_t>& vector, uint64_t logical_idx_from, uint64_t logical_idx_to) {
        if (logical_idx_from < logical_idx_to) {
            std::rotate(
                vector.begin() + logical_idx_from,
                vector.begin() + logical_idx_from + 1,
                vector.begin() + logical_idx_to + 1
            );
        }
        else {
            std::rotate(
                vector.begin() + logical_idx_to,
                vector.begin() + logical_idx_from,
                vector.begin() + logical_idx_from + 1
            );
        }
    }

    uint64_t abs_index(int64_t index, uint64_t size) const {
        if (index < 0) index += size;
        if (index >= size)
            throw std::out_of_range("Index out of range.");
            // throw pybind11::index_error("Index out of range.");
        return static_cast<uint64_t>(index);
    }

    std::list<uint64_t> abs_index(const std::list<int64_t>& indexes, uint64_t size) const {
        std::list<uint64_t> logical_indexes;
        for (int64_t idx : indexes)
            logical_indexes.push_back(abs_index(idx, size));
        logical_indexes.sort(std::greater<>());
        return logical_indexes;
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
            if (i + 1 < row_map_logical_to_physical.size()) os << ", ";
            ++i;
        }

        os << "\nrow_idx: ";
        for (size_t i = 0; i < row_map_logical_to_physical.size(); ++i) {
            os << row_map_logical_to_physical[i];
            if (i + 1 < row_map_logical_to_physical.size()) os << ", ";
        }

        os << "\ncol_idx: ";
        for (size_t i = 0; i < col_map_logical_to_physical.size(); ++i) {
            os << col_map_logical_to_physical[i];
            if (i + 1 < col_map_logical_to_physical.size()) os << ", ";
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
        printTable(row_map_logical_to_physical, col_map_logical_to_physical);

        os << "\n";
    }


};

#endif