#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H

struct DataFrame
{

	struct Script {
		Script(){}
		Script(const std::unordered_map<std::string,std::string>& primer) : data(primer) {}
		std::unordered_map<std::string,std::string> data;
		uint64_t index = 0;
		Script* prev = nullptr;
		Script* next = nullptr;
	};

public:

	DataFrame(){}
	~DataFrame(){
		auto node = head;
		while (node){
			auto to_delete = node;
			node = node->next;
			delete to_delete;
		}
	}

public:

	std::unordered_map<std::string, std::string> empty_data;

	Script* head = nullptr; Script* tail = nullptr;
	std::unordered_map<uint64_t,Script*> index_to_script;

	std::unordered_set<uint64_t> modded_indices;

	std::set<std::string> col_names;
	std::unordered_map<uint64_t,std::string_view> index_to_column;

	uint64_t num_rows=0, num_cols=0;

public:

	void insert_rows(uint64_t num_new_rows) {
		if (num_new_rows == 0) return;
		
		std::list<Script*> nodes;

		if (!tail){
			auto new_script = new Script(empty_data);
			head = new_script;
			tail = new_script;
			--num_new_rows;
			nodes.push_front(new_script);
		}

		for (uint64_t i=0; i<num_new_rows; ++i) {
			auto prev_script = tail;
			auto new_script = new Script(empty_data);

			new_script->prev = prev_script;
			prev_script->next = new_script;
			tail = new_script;

			nodes.push_back(new_script);
		}

		update_indices();
		push_change({Change::INSERT_ROWS,nodes});

	}

	void insert_rows(const std::list<int64_t>& indices) {
		if (indices.empty()) return;
		std::list<uint64_t> abs_rows = abs_indices(indices, num_rows);

		std::list<Script*> nodes;

		for (uint64_t abs_row : abs_rows) {
			auto new_script = new Script(empty_data);

			auto next_script = index_to_script[abs_row];
			auto prev_script = next_script->prev;

			if (prev_script) prev_script->next = new_script;
			else head = new_script;

			new_script->prev = prev_script;
			next_script->prev = new_script;
			new_script->next = next_script;

			nodes.push_back(new_script);
		}

		update_indices();
		push_change({Change::INSERT_ROWS,nodes});
	}

	void remove_rows(const std::list<int64_t>& indices) {
		if (indices.empty()) return;
		std::list<uint64_t> abs_rows = abs_indices(indices, num_rows);

		std::list<Script*> nodes;

		for (uint64_t abs_row : abs_rows) {
			auto old_script = index_to_script[abs_row];

			auto prev_script = old_script->prev;
			auto next_script = old_script->next;

			if (prev_script) prev_script->next = next_script;
			else head = next_script;

			if (next_script) next_script->prev = prev_script;
			else tail = prev_script;

			nodes.push_back(old_script);
		}

		update_indices();
		push_change({Change::REMOVE_ROWS,nodes});
	}

	void duplicate_rows(const std::list<int64_t>& indices) {
		if (indices.empty()) return;
		std::list<uint64_t> abs_rows = abs_indices(indices, num_rows);

		std::list<Script*> nodes;

		for (uint64_t abs_row : abs_rows) {
			auto prev_script = index_to_script[abs_row];
			auto new_script = new Script(prev_script->data);

			auto next_script = prev_script->next;

			if (next_script) next_script->prev = new_script;
			else tail = new_script;

			new_script->prev = prev_script;
			prev_script->next = new_script;
			new_script->next = next_script;

			nodes.push_back(new_script);
		}

		update_indices();
		push_change({Change::INSERT_ROWS,nodes});
	}

public:

	void set(int64_t row, const std::string& col, const std::string& val) {
		uint64_t abs_row = abs_index(row, num_rows);
		auto script = index_to_script[abs_row];
		std::string prev_val = script->data[col];
		script->data[col] = val;
		modded_indices.insert(script->index);
		std::unordered_map<std::tuple<Script*,std::string>,std::tuple<std::string,std::string>> values;
		values.emplace( std::tuple<Script*,std::string>{script,col},std::tuple<std::string,std::string>{prev_val,val});
		push_change({Change::SET,{},values});
	}

	void set(int64_t row, int64_t col, const std::string& val) {
		uint64_t abs_col = abs_index(col, num_cols);
		std::string col_name = std::string(index_to_column[abs_col]);
		set(row,col_name,val);
	}

	void set(const std::list<std::tuple<int64_t, std::string, std::string>>& cell_values) {
	    std::unordered_map<std::tuple<Script*,std::string>,std::tuple<std::string,std::string>> values;

	    for (const auto& [row, col, val] : cell_values) {
	        uint64_t abs_row = abs_index(row, num_rows);
	        auto script = index_to_script[abs_row];
	        std::string prev_val = script->data[col];
	        script->data[col] = val;
	        modded_indices.insert(script->index);
	        values.emplace(std::tuple<Script*,std::string>{script, col},std::tuple<std::string,std::string>{prev_val, val});
	    }
	    push_change({Change::SET, {}, values});
	}

	void set(const std::list<std::tuple<int64_t, int64_t, std::string>>& cell_values) {
	    std::unordered_map<std::tuple<Script*,std::string>,std::tuple<std::string,std::string>> values;
	    
	    for (const auto& [row, col, val] : cell_values) {
	        uint64_t abs_row = abs_index(row, num_rows);
	        uint64_t abs_col = abs_index(col, num_cols);
	        std::string col_name = std::string(index_to_column[abs_col]);
	        auto script = index_to_script[abs_row];
	        std::string prev_val = script->data[col_name];
	        script->data[col_name] = val;
	        modded_indices.insert(script->index);
	        values.emplace(std::tuple<Script*, std::string>{script, col_name}, std::tuple<std::string, std::string>{prev_val, val});
	    }
	    
	    push_change({Change::SET, {}, values});
	}

	std::string get(int64_t row, const std::string&  col) {
		uint64_t abs_row = abs_index(row, num_rows);
		return (index_to_script[abs_row])->data[col];
	}

	std::string get(int64_t row, int64_t col) {
		uint64_t abs_row = abs_index(row, num_rows);
		uint64_t abs_col = abs_index(col, num_cols);
		std::string col_name = std::string(index_to_column[abs_col]);
		return (index_to_script[abs_row])->data[col_name];
	}

	std::unordered_map<std::string, std::string>& get_map(int64_t row){
		uint64_t abs_row = abs_index(row, num_rows);
		return (index_to_script[abs_row])->data;
	}

private:

	struct Change {
		enum Type {INSERT_ROWS,REMOVE_ROWS,SET} type;
		std::list<Script*> nodes;
		std::unordered_map<std::tuple<Script*,std::string>,std::tuple<std::string,std::string>> values;
	};

	std::stack<Change> undo_stack;
	std::stack<Change> redo_stack;

	void push_change(const Change& change) {
		undo_stack.push(change);
		while (!redo_stack.empty()) {
			auto change = redo_stack.top();
			redo_stack.pop();
			if (change.type == Change::INSERT_ROWS)
				for (auto node : change.nodes)
					delete node;
		}
	}

public:

	void undo() {
		if (undo_stack.empty()) return;
		auto change = undo_stack.top();
		redo_stack.push(change);
		undo_stack.pop();

		switch (change.type) {
			case Change::INSERT_ROWS: {
				for (auto it = change.nodes.rbegin(); it != change.nodes.rend(); ++it) {
					auto node = *it;
					auto prev_script = node->prev;
					auto next_script = node->next;

					if (prev_script) prev_script->next = next_script;
					else head = next_script;

					if (next_script) next_script->prev = prev_script;
					else tail = prev_script;
				}
				update_indices();
				break;
			}
			case Change::REMOVE_ROWS: {
				for (auto it = change.nodes.rbegin(); it != change.nodes.rend(); ++it) {
					auto node = *it;
					auto prev_script = node->prev;
					auto next_script = node->next;

					if (prev_script) prev_script->next = node;
					else head = node;

					if (next_script) next_script->prev = node;
					else tail = node;
				}
				update_indices();
				break;
			}
			case Change::SET: {
				for (auto [cell_index,values] : change.values){
					auto [node,col] = cell_index;
					auto [prev_val,val] = values;
					node->data[col] = prev_val;
					modded_indices.insert(node->index);
				}
				break;
			}
		}
	}

	void redo() {
		if (redo_stack.empty()) return;
		auto change = redo_stack.top();
		undo_stack.push(change);
		redo_stack.pop();

		switch (change.type) {
			case Change::INSERT_ROWS: {
				for (auto node : change.nodes) {
					auto prev_script = node->prev;
					auto next_script = node->next;

					if (prev_script) prev_script->next = node;
					else head = node;

					if (next_script) next_script->prev = node;
					else tail = node;
				}
				update_indices();
				break;
			}
			case Change::REMOVE_ROWS: {
				// Redo removal: delete the nodes again
				for (auto node : change.nodes) {
					auto prev_script = node->prev;
					auto next_script = node->next;

					if (prev_script) prev_script->next = next_script;
					else head = next_script;

					if (next_script) next_script->prev = prev_script;
					else tail = prev_script;
				}
				update_indices();
				break;
			}
			case Change::SET: {
				for (auto [cell_index,values] : change.values){
					auto [node,col] = cell_index;
					auto [prev_val,val] = values;
					node->data[col] = val;
					modded_indices.insert(node->index);
				}
				break;
			}
		}
	}

private:

	uint64_t abs_index(int64_t index, uint64_t size) const {
		if (index < 0) index += size;
		if (index >= size)
			throw std::out_of_range("Index out of range.");
		return static_cast<uint64_t>(index);
	}

	std::list<uint64_t> abs_indices(const std::list<int64_t>& indices, uint64_t size) const {
		std::list<uint64_t> abs_rows;
		for (auto index : indices)
			abs_rows.insert(abs_rows.end(),abs_index(index,size));
		return abs_rows;
	}

	void update_indices(){
		Script* current = head;
		num_rows = 0;
		while(current){
			if (index_to_script[num_rows]!=current)
				modded_indices.insert(num_rows);
			current->index = num_rows;
			index_to_script[num_rows++] = current;
			current = current->next;
		}
	}

public:

	void clear() {
		empty_data.clear();
		index_to_script.clear();
		col_names.clear();
		index_to_column.clear();
		num_rows=0, num_cols=0;

		auto node = head;
		while (node){
			auto to_delete = node;
			node = node->next;
			delete to_delete;
		}
		head = nullptr;
		tail = nullptr;
	}

	void clear_cells(const std::list<std::tuple<int64_t,std::string>>& cell_indices) {
		std::unordered_map<std::tuple<Script*,std::string>,std::tuple<std::string,std::string>> values;
		for (auto [row,col] : cell_indices) {
			uint64_t abs_row = abs_index(row, num_rows);
			auto script = index_to_script[abs_row];
			std::string prev_val = script->data[col];
			std::string val = "";
			script->data[col] = "";
			modded_indices.insert(script->index);
			values.emplace(std::tuple<Script*,std::string>{script,col},std::tuple<std::string,std::string>{prev_val,val});
		}
		push_change({Change::SET,{},values});
	}
	
	void clear_cells(const std::list<std::tuple<int64_t,int64_t>>& cell_indices) {
		std::unordered_map<std::tuple<Script*,std::string>,std::tuple<std::string,std::string>> values;
		for (auto [row,col] : cell_indices) {
			uint64_t abs_row = abs_index(row, num_rows);
			uint64_t abs_col = abs_index(col, num_cols);
			std::string col_name = std::string(index_to_column[abs_col]);
			auto script = index_to_script[abs_row];
			std::string prev_val = script->data[col_name];
			std::string val = "";
			script->data[col_name] = "";
			modded_indices.insert(script->index);
			values.emplace(std::tuple<Script*,std::string>{script,col_name},std::tuple<std::string,std::string>{prev_val,val});
		}
		push_change({Change::SET,{},values});
	}

	void insert_column(const std::string& name) {
		if (!col_names.contains(name)) {
			col_names.insert(name);
			num_cols = col_names.size();
			uint64_t i = 0;
			for (const auto& col_name : col_names)
				index_to_column[i++] = col_name;
			auto node = head;
			while (node){
				node->data[name];
				node = node->next;
			}
			empty_data[name];
		}
	}

public:

	void serialize(json& j) const {
		json& dataframe = j["dataframe"];

		dataframe["empty_data"] = empty_data;

		dataframe["index_to_script"] = json::object();
		auto node = head;
		uint64_t index = 0;
		while (node) {
			dataframe["index_to_script"][std::to_string(index++)] = node->data;
			node = node->next;
		}

		dataframe["col_names"] = col_names;

		dataframe["num_rows"] = num_rows;
		dataframe["num_cols"] = num_cols;
	}

	bool deserialize(const json& j) {
		// Temporary variables to hold the data
		std::unordered_map<std::string, std::string> temp_empty_data;
		std::map<uint64_t, Script*> temp_index_to_script;
		std::set<std::string> temp_col_names;
		uint64_t temp_num_rows;
		uint64_t temp_num_cols;

		try {
			const json& dataframe = j.at("dataframe");

			// Extract data into temporary variables
			for (auto [var,val] : dataframe.at("empty_data").items())
				temp_empty_data[var]=val;

			for (auto& [key, value] : dataframe.at("index_to_script").items()) {
				std::unordered_map<std::string, std::string> temp_primer;
				for (auto [var,val] : value.items())
					temp_primer[var]=val;
				auto script = new Script(temp_primer);
				temp_index_to_script[std::stoull(key)] = script;
			}

			for (auto& [_,col] : dataframe.at("col_names").items())
				temp_col_names.insert(col);

			temp_num_rows = dataframe.at("num_rows").get<uint64_t>();
			temp_num_cols = dataframe.at("num_cols").get<uint64_t>();

			// If all reads succeeded, move the temporary variables into the class members
			empty_data = std::move(temp_empty_data);
			clear();
			head = nullptr;
			tail = nullptr;
			for (auto& [index, script] : temp_index_to_script) {
				if (!head) {
					head = tail = script;
				} else {
					tail->next = script;
					script->prev = tail;
					tail = script;
				}
				index_to_script[index] = script;
				modded_indices.insert(index);
			}
			col_names = std::move(temp_col_names);
			uint64_t i = 0;
			for (const auto& col_name : col_names)
				index_to_column[i++] = col_name;
			num_rows = temp_num_rows;
			num_cols = temp_num_cols;

			update_indices();

			return false;
		} catch (const std::exception& e) {
			for (auto& [index, script] : temp_index_to_script)
				delete script;
			return true;
		}
	}

public:

	uint64_t row_count() const {return num_rows;}
	uint64_t col_count() const {return num_cols;}

};

#endif