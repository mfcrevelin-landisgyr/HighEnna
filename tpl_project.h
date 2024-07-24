#ifndef TPL_PROJECT_HEADER
#define TPL_PROJECT_HEADER

struct TplProject{
    TplProject(const std::string& directory_path_){
        python_executor = new PythonExecutor();
        set_directory(directory_path_);
    }
    ~TplProject(){
        for (auto file_handler : file_handlers)
            delete file_handler;
        delete python_executor;
    }
public:

    std::string directory_path;
    std::filesystem::path filesystem_directory_path;
    std::filesystem::path filesystem_output_directory_path;
    
    std::unordered_set<TplFileHandler*> file_handlers;
    std::set<std::string> file_paths;

    std::unordered_map<uint64_t,TplFileHandler*> id_to_handler;
    std::unordered_map<std::string,TplFileHandler*> path_to_handler;

    PythonExecutor* python_executor;

public:
    void set_directory(const std::string& directory_path_){
        directory_path = directory_path_;
        filesystem_directory_path = directory_path_;
        filesystem_output_directory_path = filesystem_directory_path/"Scripts";
        update();
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
                    file_handler = new TplFileHandler(filesystem_output_directory_path.string()+"\\",file_path,file_name,python_executor);

                file_handlers.insert(file_handler);
                cur_file_paths.insert(file_path);
                file_paths.insert(file_path);
                path_to_handler.emplace(file_path,file_handler);

                std::thread t([=](){file_handler->update();});
                t.detach();
            }
        }

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

        std::this_thread::sleep_for(20ms);
    }

public:

    void render(const std::vector<std::tuple<int64_t,std::vector<int64_t>>>& indexes){
        std::thread t([=]() { 
            if (!std::filesystem::exists(filesystem_output_directory_path)) {
                std::filesystem::create_directories(filesystem_output_directory_path);
            }
            for (auto& [handler_index,senario_indexes] : indexes){
                uint64_t index = abs_index(handler_index);
                auto file_handler = id_to_handler[index];
                file_handler->indexed_render(senario_indexes); 
            }
        });
        t.detach();
    }

    void render(int64_t handler_index, const std::vector<int64_t>& senario_indexes){
        uint64_t index = abs_index(handler_index);
        auto file_handler = id_to_handler[index];
        std::thread t([=]() { 
            if (!std::filesystem::exists(filesystem_output_directory_path)) {
                std::filesystem::create_directories(filesystem_output_directory_path);
            }
            file_handler->indexed_render(senario_indexes);
        });
        t.detach();
    }

    void render(int64_t handler_index){
        uint64_t index = abs_index(handler_index);
        auto file_handler = id_to_handler[index];
        std::thread t([=]() {
            if (!std::filesystem::exists(filesystem_output_directory_path)) {
                std::filesystem::create_directories(filesystem_output_directory_path);
            }
            file_handler->render(); 
        });
        t.detach();
    }

    void render(){

        std::thread t([=]() {
            if (!std::filesystem::exists(filesystem_output_directory_path)) {
                std::filesystem::create_directories(filesystem_output_directory_path);
            }
            for (auto file_handler : file_handlers){
                file_handler->render();
            }
        });
        t.detach();
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

    bool failed(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->my_mutex);
        return id_to_handler[index]->failed;
    }
    
    std::string log(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->my_mutex);
        return id_to_handler[index]->get_log();
    }

    std::string path(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->my_mutex);
        return id_to_handler[index]->file_path;
    }

    std::string name(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->my_mutex);
        return id_to_handler[index]->file_name;
    }

    std::string content(int64_t index_) {
        uint64_t index = abs_index(index_);
        std::scoped_lock<std::mutex> lock(id_to_handler[index]->my_mutex);
        return std::string(id_to_handler[index]->file_content);
    }

};

#endif