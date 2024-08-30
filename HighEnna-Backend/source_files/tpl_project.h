#ifndef TPL_PROJECT_HEADER
#define TPL_PROJECT_HEADER

struct TplProject{
    TplProject(const std::string& directory_path_){
        python_executor = new PythonExecutor();
        task_counter = new TaskCounter();
        set_directory(directory_path_);
    }
    ~TplProject(){
        for (auto file_handler : file_handlers){
            {std::scoped_lock<std::mutex> lock(file_handler->loading_mutex);}
            delete file_handler;
        }
        delete python_executor;
        delete task_counter;
    }
public:

    std::string directory_path;
    std::filesystem::path filesystem_directory_path;
    std::filesystem::path filesystem_output_directory_path;
    
    std::unordered_set<TplFileHandler*> file_handlers;
    std::set<std::string> file_paths;

    std::unordered_map<uint64_t,TplFileHandler*> id_to_handler;
    std::unordered_map<std::string,TplFileHandler*> path_to_handler;

    std::string globals;
    PythonExecutor* python_executor;
    TaskCounter* task_counter;

public:

    void set_directory(const std::string& new_directory_path){
        directory_path = new_directory_path;
        filesystem_directory_path = new_directory_path;
        if (filesystem_output_directory_path.empty())
            filesystem_output_directory_path = filesystem_directory_path/"Scripts";
        update();
    }

    void set_output_directory(const std::string& new_directory_path){
        filesystem_output_directory_path = new_directory_path;
        for (auto file_handler : file_handlers){
            std::scoped_lock<std::mutex,std::mutex> lock(file_handler->loading_mutex,file_handler->rendering_mutex);
            file_handler->file_output_dir = new_directory_path;
            file_handler->split_name();
        }
    }

    void update(){
        std::set<std::string> cur_file_paths;
        TplFileHandler* file_handler;

        for (const auto& entry : std::filesystem::directory_iterator(filesystem_directory_path)) {
            if (entry.is_regular_file() && entry.path().extension() == ".tpl") {
                std::string file_name = entry.path().filename().string();
                std::string file_path = entry.path().string();

                if (file_paths.contains(file_path))
                    file_handler = path_to_handler[file_path];
                else
                    file_handler = new TplFileHandler(filesystem_output_directory_path.string()+"\\",file_path,file_name,python_executor,task_counter);

                file_handlers.insert(file_handler);
                cur_file_paths.insert(file_path);
                file_paths.insert(file_path);
                path_to_handler.emplace(file_path,file_handler);
            }
        }

        std::thread t([=](){
            for (auto file_handler : file_handlers)
                file_handler->update();

            std::unordered_set<uint64_t> hashes;
            for (auto file_handler : file_handlers){
                for (auto& module_name : file_handler->import_modules){
                    uint64_t hash = std::hash<std::string>()(module_name);
                    if (!hashes.contains(hash))
                        python_executor->module(module_name);
                    hashes.insert(hash);
                }
                for (auto& [module_name,attribute] : file_handler->import_from_modules){
                    uint64_t hash = std::hash<std::string>()(module_name) * std::hash<std::string>()(attribute);
                    if (!hashes.contains(hash))
                        python_executor->from_module(attribute,module_name);
                    hashes.insert(hash);
                }
                for (auto& [file_name,file_content] : file_handler->import_file_modules){
                    uint64_t hash = std::hash<std::string>()(file_content);
                    if (!hashes.contains(hash))
                        python_executor->execute(file_content);
                    hashes.insert(hash);
                }
            }
            
            for (auto file_handler : file_handlers)
                file_handler->precompute();
        });
        t.detach();

        uint64_t id=0;
        id_to_handler.clear();
        for (const std::string& file_path : file_paths){   
            file_handler = path_to_handler[file_path];
            if (cur_file_paths.contains(file_path)){
                id_to_handler.emplace(id++,file_handler);
            } else {
                path_to_handler.erase(file_path);
                file_handlers.erase(file_handler);
                file_paths.erase(file_path);
                delete file_handler;
            }
        }
    }

public:

    std::unordered_set<std::string> get_modules(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->import_modules;
    }

    bool update_modules(int64_t index_, const std::unordered_set<std::string>& add_modules, const std::unordered_set<std::string>& rmv_modules) {
        uint64_t index = abs_index(index_);
        auto file_handler = id_to_handler[index];
        std::scoped_lock<std::mutex,std::mutex,std::mutex> lock(
            file_handler->loading_mutex,file_handler->rendering_mutex,file_handler->precomputing_mutex);
        bool failed = false;
        for (auto& module_name : add_modules){
            python_executor->module(module_name);
            failed |= python_executor->failed();
            file_handler->import_modules.insert(module_name);
            file_handler->full_precompute();
        }
        for (auto& module_name : rmv_modules)
            file_handler->import_modules.erase(module_name);
        return failed;
    }

    std::unordered_set<std::tuple<std::string,std::string>> get_from_modules(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->import_from_modules;
    }

    bool update_from_modules(int64_t index_, const std::unordered_set<std::tuple<std::string,std::string>>& add_from_modules, const std::unordered_set<std::tuple<std::string,std::string>>& rmv_from_modules) {
        uint64_t index = abs_index(index_);
        auto file_handler = id_to_handler[index];
        std::scoped_lock<std::mutex,std::mutex,std::mutex> lock(
            file_handler->loading_mutex,file_handler->rendering_mutex,file_handler->precomputing_mutex);
        bool failed = false;
        for (auto& from_module : add_from_modules){
            auto& [module_name,attribute] = from_module;
            python_executor->from_module(attribute,module_name);
            failed |= python_executor->failed();
            file_handler->import_from_modules.insert(from_module);
            file_handler->full_precompute();
        }
        for (auto& from_module : rmv_from_modules)
            file_handler->import_from_modules.erase(from_module);
        return failed;
    }

    std::unordered_set<std::tuple<std::string,std::string>>  get_file_modules(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->import_file_modules;
    }

    bool update_file_modules(int64_t index_, const std::unordered_set<std::tuple<std::string,std::string>>& add_file_modules, const std::unordered_set<std::tuple<std::string,std::string>>& rmv_file_modules) {
        uint64_t index = abs_index(index_);
        auto file_handler = id_to_handler[index];
        std::scoped_lock<std::mutex,std::mutex,std::mutex> lock(
            file_handler->loading_mutex,file_handler->rendering_mutex,file_handler->precomputing_mutex);
        bool failed = false;
        for (auto& file_module : add_file_modules){
            auto& [file_name,file_content] = file_module;
            python_executor->execute(file_content);
            failed |= python_executor->failed();
            file_handler->import_file_modules.insert(file_module);
            file_handler->full_precompute();
        }
        for (auto& file_module : rmv_file_modules) {
            auto& [file_name,file_content] = file_module;
            for (auto it = file_handler->import_file_modules.begin(); it != file_handler->import_file_modules.end(); ) {
                if (std::get<1>(*it) == file_content) {
                    it = file_handler->import_file_modules.erase(it); // Remove and get the next iterator
                } else {
                    ++it; // Move to the next element
                }
            }
        }
        return failed;
    }

public:

    void render(const std::vector<std::tuple<int64_t,std::vector<int64_t>>>& indices){
        if (!std::filesystem::exists(filesystem_output_directory_path))
            std::filesystem::create_directories(filesystem_output_directory_path);
        task_counter->reset_total();
        for (auto& [handler_index,script_indices] : indices){
            std::thread t([=]() {id_to_handler[abs_index(handler_index)]->indexed_render(script_indices);});
            t.detach();
        }
    }

    void render(int64_t handler_index, const std::vector<int64_t>& script_indices){
        if (!std::filesystem::exists(filesystem_output_directory_path))
            std::filesystem::create_directories(filesystem_output_directory_path);
        task_counter->reset_total();
        std::thread t([=]() {id_to_handler[abs_index(handler_index)]->indexed_render(script_indices);});
        t.detach();
    }

    void render(int64_t handler_index){
        if (!std::filesystem::exists(filesystem_output_directory_path))
            std::filesystem::create_directories(filesystem_output_directory_path);
        task_counter->reset_total();
        std::thread t([=]() {id_to_handler[abs_index(handler_index)]->render();});
        t.detach();
    }

    void render(){
        if (!std::filesystem::exists(filesystem_output_directory_path))
            std::filesystem::create_directories(filesystem_output_directory_path);
        task_counter->reset_total();
        for (auto file_handler : file_handlers){
            std::thread t([=]() {file_handler->render();});
            t.detach();
        }
    }

public:

    uint64_t abs_index(int64_t index) const {
        if (index < 0) index += file_handlers.size();
        if ((index < 0)  || (static_cast<uint64_t>(index) >= file_handlers.size())) throw pybind11::index_error("Index out of range");
        return index;
    }

public:

    std::string as_string() const {
        constexpr char prefix[] = "TplProject(";
        constexpr char sufix[] = ")";
        return prefix + directory_path + sufix;
    }

    uint64_t size() const {
        return file_handlers.size();
    }

public:

    bool load_failed(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->load_failed;
    }

    bool render_failed(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        return id_to_handler[index]->render_failed();
    }

    bool render_failed(int64_t index_, int64_t script) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        return id_to_handler[index]->render_failed(script);
    }
    
    std::string log(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        return id_to_handler[index]->get_log();
    }

    std::string path(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->file_path;
    }

    std::string name(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->file_name;
    }

    std::string text(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return std::string(id_to_handler[index]->file_content);
    }

    std::vector<std::string> vars(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->get_vars();
    }

public:

    void clear_dataframe(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->clear_dataframe();
    }

    void clear_dataframe_indices(int64_t index_, const std::list<std::tuple<int64_t,std::string>>& cell_indices) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->clear_dataframe_indices(cell_indices);
    }

    void clear_dataframe_indices(int64_t index_, const std::list<std::tuple<int64_t,int64_t>>& cell_indices) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->clear_dataframe_indices(cell_indices);
    }

    void insert_column(int64_t index_, const std::string& col){
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->insert_column(col);
    }

    void insert_rows(int64_t index_, int64_t num_rows) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->insert_rows(num_rows);
    }

    void insert_rows(int64_t index_, const std::list<int64_t>& rows) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->insert_rows(rows);
    }

    void remove_rows(int64_t index_, const std::list<int64_t>& rows) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->remove_rows(rows);
    }

    void duplicate_rows(int64_t index_, const std::list<int64_t>& rows) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->duplicate_rows(rows);
    }

    void set(int64_t index_, int64_t row, const std::string& col, const std::string& val) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->set(row,col, val);
    }

    void set(int64_t index_, int64_t row, int64_t col, const std::string& val) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->set(row,col, val);
    }

    void set(int64_t index_, const std::list<std::tuple<int64_t, std::string, std::string>>& cell_values) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->set(cell_values);
    }

    void set(int64_t index_, const std::list<std::tuple<int64_t, int64_t, std::string>>& cell_values) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        id_to_handler[index]->set(cell_values);
    }

    std::string get(int64_t index_, int64_t row, const std::string& col) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->get(row,col);
    }

    std::string get(int64_t index_, int64_t row, int64_t col) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->get(row,col);
    }

    void undo(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        return id_to_handler[index]->undo();
    }

    void redo(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex,std::mutex> lock(id_to_handler[index]->loading_mutex,id_to_handler[index]->rendering_mutex);
        return id_to_handler[index]->redo();
    }

    uint64_t row_count(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->row_count();
    }

    uint64_t col_count(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->col_count();
    }

public:

    int total() const { return task_counter->total(); }
    int current() const { return task_counter->current(); }
    bool is_finished() const { return task_counter->is_finished(); }

public:

    void save_data(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->loading_mutex);
        return id_to_handler[index]->save_data();
    }

    void save_modules() {
        std::thread t([=](){
            for (auto handler : file_handlers){
                std::scoped_lock<std::mutex> lock(handler->loading_mutex);
                handler->save_modules();
            }
        });
        t.detach();
    }

};

#endif