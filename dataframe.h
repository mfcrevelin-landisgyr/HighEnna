#ifndef CUSTOM_DATAFRAME_H
#define CUSTOM_DATAFRAME_H

struct DataFrame {
	DataFrame(){}

	struct tuple_hash {
		template <class T1, class T2>
		size_t operator ()(const std::tuple<T1, T2>& t) const {
			size_t h1 = std::hash<T1>{}(std::get<0>(t));
			size_t h2 = std::hash<T2>{}(std::get<1>(t));
			return std::hash<size_t>{}(h1 - h2);
		}
	};

	std::unordered_map<std::tuple<uint64_t, std::string>, std::string, tuple_hash> table;
	
	std::unordered_map<uint64_t,std::string> col_idx_to_name;
	std::set<std::string> col_names;
	
	uint64_t width = 0, height = 0;

public:

	void clear(){
		col_idx_to_name.clear();
		col_names.clear();
		table.clear();
	} 

public:

	void insert_column(const std::string& col) {
		if (col_names.contains(col))
			throw pybind11::value_error("Column already exists: "+col);

		++width;

		col_names.insert(col);
		for (uint64_t row=0; row<height; ++row)
			table[std::make_tuple(row,col)] = "";

		populate_indexes();
		std::cout << "Inserted Column: " << col << std::endl;

	}

	void insert_row() {
		uint64_t row = height++;
		for (const std::string& col : col_names)
			table[std::make_tuple(row,col)] = "";
		std::cout << "Inserted Row: " << std::to_string(row) << std::endl;
	}

	void insert_row(int64_t row) {
		uint64_t new_row = height++;
		uint64_t abs_row = abs_index(row,height);

		for (const std::string& col : col_names){
			for (uint64_t row_=new_row; row_>abs_row; --row_)
				table[std::make_tuple(row_,col)] = table[std::make_tuple(row_-1,col)];	
			table[std::make_tuple(abs_row,col)] = "";
		}

		std::cout << "Inserted Row: " << std::to_string(abs_row) << std::endl;
	}

public:

	void remove_column(const std::string& col) {
		if (!col_names.contains(col))
			throw pybind11::value_error("Column does not exist: "+col);

		--width;

		col_names.erase(col);

		for (uint64_t row=0; row<height; ++row){
			auto pos = std::make_tuple(row,col);
			table.erase(pos);
		}

		populate_indexes();
		std::cout << "Removed Column: " << col << std::endl;
	}

	void remove_column(int64_t col) {
		uint64_t abs_col = abs_index(col,width);
		std::string col_name = col_idx_to_name[abs_col];
		remove_column(col_name);
	}

	void remove_row(int64_t row) {
		uint64_t abs_row = abs_index(row,height);
		uint64_t new_row = --height;

		for (const std::string& col : col_names){
			for (uint64_t row_=abs_row; row_<new_row; ++row_)
				table[std::make_tuple(row_,col)] = table[std::make_tuple(row_+1,col)];

			auto pos = std::make_tuple(new_row,col);
			table.erase(pos);
		}

		std::cout << "Removed Row: " << std::to_string(abs_row) << std::endl;
	}

public:

	void set(std::tuple<int64_t, std::string> pos, const std::string& val) {
		auto& [row,col] = pos;
		uint64_t abs_row = abs_index(row,height);

		table[std::make_tuple(abs_row,col)] = val;
		std::cout << "Set: " << std::to_string(abs_row) << ", " << table[std::make_tuple(abs_row,col)] << std::endl;
		
	}

	void set(std::tuple<int64_t, int64_t> pos, const std::string& val) {
		auto& [row,col] = pos;

		uint64_t abs_row = abs_index(row,height);
		uint64_t abs_col = abs_index(col,width);
		std::string col_name = col_idx_to_name[abs_col];

		table[std::make_tuple(abs_row,col_name)] = val;

		std::cout << "Set: " << std::to_string(abs_row) << ", " << table[std::make_tuple(abs_row,col_name)] << std::endl;
		
	}

	std::string get(const std::tuple<int64_t, std::string>& pos) const {
		auto& [row,col] = pos;
		uint64_t abs_row = abs_index(row,height);
		if (!col_names.contains(col))
			throw pybind11::value_error("Column does not exist: "+col);
		return table.at(std::make_tuple(abs_row,col));
	}

	std::string get(const std::tuple<int64_t, int64_t>& pos) const{
		auto& [row,col] = pos;
		uint64_t abs_row = abs_index(row,height);
		uint64_t abs_col = abs_index(col,width);
		std::string col_name = col_idx_to_name.at(abs_col);
		return table.at(std::make_tuple(abs_row,col_name));
	}

public:

	void populate_indexes(){
		col_idx_to_name.clear();
		uint64_t i=0;
		for (const std::string& col : col_names)
			col_idx_to_name[i++] = col;
	}

	uint64_t abs_index(int64_t index, uint64_t size) const{
		if (index<0) index += size;
		if ( (index<0) || (static_cast<uint64_t>(index)>size))
			throw pybind11::index_error("Index out of range.");
		return index;
	}

public:

	uint64_t row_count() const{
		return height;
	}

	uint64_t col_count() const{
		return width;
	}

public:

	std::unordered_map<std::string,std::string> senario(int64_t row) const{
		uint64_t abs_row = abs_index(row,height);
		std::unordered_map<std::string,std::string> senario_map;
		for (auto& col : col_names)
			senario_map[col] = table.at(std::make_tuple(abs_row,col));
		return senario_map;
	}

public:

	void print() const {
		uint64_t max_width = 0;

		for (uint64_t row = 0; row < height; ++row)
			for (const auto& col_name : col_names)
				max_width = std::max(max_width, table.at(std::make_tuple(row, col_name)).length());

		for (const auto& col_name : col_names)
			max_width = std::max(max_width, col_name.length());

		std::cout << "Table (" << std::to_string(height) << " x " << std::to_string(width) << "):\n";
		std::cout << "|";
		for (const auto& col_name : col_names)
			std::cout << std::setw(max_width) << col_name << " |";
		std::cout << "\n";

		std::cout << "+";
		for (const auto& col_name : col_names)
			std::cout << std::string(max_width + 1, '-') << "+";
		std::cout << "\n";

		for (uint64_t row = 0; row < height; ++row) {
			std::cout << "|";
			for (const auto& col_name : col_names)
				std::cout << std::setw(max_width) << table.at(std::make_tuple(row, col_name)) << " |";
			std::cout << "\n";
		}

		std::cout << "\n";
	}

};


#endif