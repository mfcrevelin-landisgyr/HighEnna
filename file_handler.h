#ifndef FILE_HANDLER_HEADER
#define FILE_HANDLER_HEADER

using OutFilesMap = std::unordered_map<uint64_t, std::unique_ptr<std::ofstream>>;
using OutFilesErrMsgMap = std::unordered_map<uint64_t, std::ostringstream>;
struct TplFileHandler {
    TplFileHandler(const std::string& file_output_dir_, const std::string& file_path_, const std::string& file_name_, PythonExecutor* python_executor_):
        file_output_dir(file_output_dir_), file_path(file_path_), file_name(file_name_), python_executor(python_executor_) {}
    
public:

    std::string file_path;
    std::string file_name;
    std::string file_output_dir;

    std::string file_sub_name_0;
    std::string file_sub_name_1; 

    std::filesystem::file_time_type last_read_time;

    std::mutex my_mutex;
    bool failed = false;

    std::list<std::string> log_list;
    size_t log_width=0;

    struct Generator;
    std::vector<Generator*> file_template;
    DataFrame file_dataframe;

    size_t file_content_size;
    std::string_view file_content;
    std::unique_ptr<char[]> file_content_buffer;
    std::vector<uint64_t> file_line_indexes = {0};

    std::unordered_set<std::string_view> file_variables;

    OutFilesMap out_files;
    OutFilesErrMsgMap out_files_err_msgs;
    std::unordered_map<int64_t,std::string> file_sub_names;

    PythonExecutor* python_executor;

public:

    void update(){
        std::scoped_lock<std::mutex> lock(my_mutex);

        last_read_time = std::filesystem::last_write_time(file_path);
        out_files.clear();

        failed = false;

        log_list.clear();
        log_width=0;

        file_template.clear();
        file_dataframe.clear();

        file_line_indexes.clear();
        file_line_indexes.push_back(0);

        file_variables.clear();
        file_dataframe.clear();

        split_name();
        load(); 
        // if (!failed) parse();
        if (!failed) test_parse();
    }

    void split_name(){
        constexpr const uint8_t dfa[5][256] = {{ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
                                               { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
                                               { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
                                               { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
                                               { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}};
        
        bool split = false;
        uint64_t name_split_idx = 0;

        uint64_t ptr = 0;
        uint16_t transition = 0;
        uint8_t& state = *reinterpret_cast<uint8_t*>(&transition); // Least significant byte
        uint8_t& pstate = *(reinterpret_cast<uint8_t*>(&transition) + 1); // Most significant byte

        std::array<std::function<void()>,1> actions = {
            [&](){
                name_split_idx=ptr;
                split=true;
            }
        };

        std::unordered_map<uint16_t, std::vector<uint8_t>> transition_to_actions;
        for (state=0;state<5;++state){
            for (pstate=0;pstate<5;++pstate){
                transition_to_actions[transition] = {}; // Default : Null action
            }
        }

        transition = 0;

        transition_to_actions[0x0300] = {0};

        try{

            for (ptr = 0; ptr < file_name.size();++ptr) {
                const char& chr = file_name.data()[ptr];

                pstate = state;
                state = dfa[state][static_cast<uint8_t>(chr)];

                for (const uint8_t& action : transition_to_actions[transition] )
                    actions[action]();

            }

            pstate = state;
            state = dfa[state][0];

            for (const uint8_t& action : transition_to_actions[transition] )
                actions[action]();

            if (!split)
                name_split_idx = file_name.size()-4;

            file_sub_name_0 = file_output_dir + std::string(file_name.data(),name_split_idx);
            file_sub_name_1 = std::string(file_name.data()+name_split_idx,file_name.size()-name_split_idx-3); 

        } catch (const std::runtime_error& e) {
            log("Runtime Error during Parse.\n" + static_cast<std::string>(e.what()));
            failed = true;
        }

   }

    void load() {
        try{
            auto start = std::chrono::high_resolution_clock::now();

            std::ifstream file(file_path, std::ios::ate);

            if (!file.is_open()) {
                log("Failed to open file: \n\n" + std::system_category().message(errno) + "\n");
                failed = true;
                return;
            }

            std::streamsize size = file.tellg();
            file.seekg(0, std::ios::beg);
            file_content_buffer = std::make_unique<char[]>(size+1);
            
            bool read_failed = static_cast<bool>(file.read(file_content_buffer.get(), size));
            auto error_number = errno;
            file.close();

            if (error_number) {
                log("Failed to read file: " + std::to_string(error_number) + "\n\n" + std::system_category().message(error_number));
                failed = true;
                return;
            }

            /*
             Assessing the file size in the way above gives a count higher than the byte count the file
            actualy has... Probably because of filesystem blocking scheme.
             To assess what the file's actual size is, the snippet bellow performs a binary search to determine
            the first 0x00 byte in the oversized buffer.
            */
            size_t rside = size ;
            size_t lside = 0;

            while (lside < rside) {
                size_t mid = lside + ((rside - lside)>>1);
                if (file_content_buffer[mid] == 0) {
                    rside = mid;
                } else {
                    lside = mid + 1;
                }
            }

            file_content_size = lside+1; // +1 to "append" an extra 0x00 byte after the file's data in order to properly parse it in the funtion bellow.
            file_content = std::string_view(file_content_buffer.get(),file_content_size);

            auto end = std::chrono::high_resolution_clock::now();

            log_time("Successfully loaded file into memory.",start,end);

        } catch (const std::runtime_error& e) {
            log("Runtime Error during Load:\n\n" + static_cast<std::string>(e.what()));
            failed = true;
        }   
    }

public:

    struct Generator {
        virtual void write(const OutFilesMap&, OutFilesErrMsgMap&, const DataFrame&, PythonExecutor*) const = 0;
    };

    struct PlainText : Generator {
        PlainText(const char* ptr, uint64_t count):buffer(ptr,count){}
        void write(const OutFilesMap& out_files, OutFilesErrMsgMap& out_files_err_msgs, const DataFrame& dataframe,PythonExecutor* python_executor) const override {
            for (const auto& [index,out_file] : out_files){
                if (out_files_err_msgs.find(index)==out_files_err_msgs.end())
                    (*out_file) << buffer;
            }
        };
        std::string_view buffer;
    };

    struct Expression : Generator {
        Expression(const char* ptr, uint64_t count):buffer(ptr,count){}
        void write(const OutFilesMap& out_files, OutFilesErrMsgMap& out_files_err_msgs, const DataFrame& dataframe,PythonExecutor* python_executor) const override {
            std::string expression(buffer);
            for (const auto& [index,out_file] : out_files){
                if (out_files_err_msgs.find(index)!=out_files_err_msgs.end()) continue;
                for (const auto& [var,value] : dataframe.senario(index)){
                    std::cout << "Set: " << var << " = " << value << std::endl;
                    python_executor->execute("var_"+var+"="+value);
                    if (python_executor->failed()){
                        out_files_err_msgs[index] << " : Failed to set " << var << "\n";
                        out_files_err_msgs[index] << "  Expression: " << "var_"+var+"="+value << "\n";
                        out_files_err_msgs[index] << python_executor->get_error();
                        break;
                    }
                }
                if (python_executor->failed()) continue;
                python_executor->evaluate(expression);
                if (python_executor->failed()){
                    out_files_err_msgs[index] << " : Failed eval\n";
                    out_files_err_msgs[index] << "  Expression: " << expression << "\n";
                    out_files_err_msgs[index] << python_executor->get_error();
                    continue;
                }
                (*out_file) << python_executor->get_eval();
                // (*out_file) << pybind11::str(python_executor->evaluate(expression)).cast<std::string>();
            }
        };
        std::string_view buffer;
    };

    struct Line : Generator {
        Line(int64_t pre_delta_, int64_t pos_delta_):pre_delta(pre_delta_),pos_delta(pos_delta_){}
        void write(const OutFilesMap& out_files, OutFilesErrMsgMap& out_files_err_msgs, const DataFrame& dataframe,PythonExecutor* python_executor) const override {
            line += pre_delta;
            for (const auto& [index,out_file] : out_files)
                if (out_files_err_msgs.find(index)==out_files_err_msgs.end())
                    (*out_file) << std::to_string(line);
            line += pos_delta;
        };
        int64_t pre_delta,pos_delta;
        static uint64_t line;
    };

    struct LineSet : Generator {
        LineSet(uint64_t num_): num(num_) {}
        void write(const OutFilesMap& out_files, OutFilesErrMsgMap& out_files_err_msgs, const DataFrame& dataframe,PythonExecutor* python_executor) const override {
            Line::line = num;
        };
        uint64_t num;
    };

    struct For : Generator {
        For(const char* ptr, uint64_t count, int64_t beg_, int64_t end_, int64_t stp_, std::stack<std::vector<Generator*>*>& template_stk): buffer(ptr,count), beg(beg_), end(end_), stp(stp_) {template_stk.push(&inner_template);}
        void write(const OutFilesMap& out_files, OutFilesErrMsgMap& out_files_err_msgs, const DataFrame& dataframe,PythonExecutor* python_executor) const override {
            
            std::string var(buffer);
            for (int64_t var_val=beg; var_val<end; var_val+=stp){
                python_executor->execute(var+"="+std::to_string(var_val));
                for (auto generator : inner_template)
                    generator->write(out_files,out_files_err_msgs,dataframe,python_executor);
            }
        };
        std::vector<Generator*> inner_template;
        std::string_view buffer;
        int64_t beg,end,stp;        
    };

    void parse() {
        // constexpr const uint8_t dfa[24][256] = {{ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,18,22,22,22,22,22,22,22,22,22,22,22, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22, 6,22,22,22,22,22,22,22,22,22,22,22, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1,23, 1, 8,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1,23, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 9,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1,10, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,22,22,22,22,17,22,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1,23, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,12,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1,13, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,22,22,22,22,17,22,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,15, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,16, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,16, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,17,17,17,17,17,17,17,17,17,17, 1, 1, 1, 1, 1, 1, 1,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17, 1, 1, 1, 1,17, 1,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,19,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,20,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,21, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,21,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           {22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22},
        //           { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1,23, 1,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}};

        // const char* file_content_beg = file_content_buffer.get();

        uint64_t ptr = 0;
        uint16_t transition = 0;
        uint8_t& state = *reinterpret_cast<uint8_t*>(&transition); // Least significant byte
        uint8_t& pstate = *(reinterpret_cast<uint8_t*>(&transition) + 1); // Most significant byte
        
        uint64_t l_ptr = 0;
        uint64_t id_ptr = 0;
        uint64_t line_num = 0;
        uint64_t line_count = 0;

        uint64_t num = 0;
        uint64_t pre = 0;
        uint64_t post = 1;

        uint64_t var_str = 0;
        uint64_t var_end = 0;
        uint64_t count_start = 0;
        uint64_t count_end = 0;


        std::stack<std::vector<Generator*>*> template_stk;
        template_stk.push(&file_template) ;

        std::array<std::function<void()>,5> actions = {
            [&](){
                ++line_count;
                file_line_indexes.push_back(ptr + 1);
                pre=0;
                post=1;
            },
            [&](){
                l_ptr = ptr;
            },
            [&](){
                id_ptr = ptr;
            },
            [&](){
                // Deserialise
            },
            [&](){
                template_stk.top()->push(new PlainText(file_content_buffer+l_ptr,ptr-l_ptr));
            },
            [&](){
                template_stk.top()->push(new Expression(file_content_buffer+l_ptr,ptr-l_ptr));
            },
            [&](){
                template_stk.top()->push(new Line(pre,post));
            },
            [&](){
                template_stk.top()->push(new LineSet(pre,post));
            },
            [&](){
                pre = std::stoi(std::string_view(file_content_buffer+l_ptr,ptr-l_ptr));
            },
            [&](){
                post = std::stoi(std::string_view(file_content_buffer+l_ptr,ptr-l_ptr));
            },
            [&](){
                file_variables.emplace(file_content_beg + id_ptr, ptr - id_ptr);
            },
            [&](){
                log("Error: Invalid variable declaration",line_num,ptr - file_line_indexes[line_num], ptr - file_line_indexes[line_num] - 4);
                failed = true;
            },
            [&](){
                log("Error: Invalid number literal",line_num,ptr - file_line_indexes[line_num], ptr - file_line_indexes[line_num] - 4);
                failed = true;
            },
            [&](){
                log("Error: Invalid data byte",line_num,ptr - file_line_indexes[line_num], ptr - file_line_indexes[line_num] - 4);
                failed = true;
            }
        };

        // std::unordered_map<uint16_t, std::vector<uint8_t>> transition_to_actions;
        // for (state=0;state<24;++state){
        //   for (pstate=0;pstate<24;++pstate){
        //   transition_to_actions[transition] = {}; // Default : Null action
        //   }
        // }

        // transition = 0;

        // transition_to_actions[0x0005] = {};
        // transition_to_actions[0x071E] = {};
        // transition_to_actions[0x072B] = {};
        // transition_to_actions[0x0E2B] = {};
        // transition_to_actions[0x0F2B] = {};
        // transition_to_actions[0x102B] = {};
        // transition_to_actions[0x122B] = {};
        // transition_to_actions[0x112A] = {};


        // transition_to_actions[0x0102] = {};
        // transition_to_actions[0x0513] = {};
        // transition_to_actions[0x0213] = {};
        // transition_to_actions[0x191A] = {};

        // transition_to_actions[0x0201] = {};
        // transition_to_actions[0x0301] = {};
        // transition_to_actions[0x0401] = {};
        // transition_to_actions[0x0501] = {};
        // transition_to_actions[0x0601] = {};

        // transition_to_actions[0x1314] = {};
        // transition_to_actions[0x1A1B] = {};


        try{

            auto start = std::chrono::high_resolution_clock::now();

            // for (ptr = 0; ptr < file_content_size;++ptr) {
            //   const char& chr = file_content_buffer[ptr];

            //   pstate = state;
            //   state = dfa[state][static_cast<uint8_t>(chr)];

            //   for (const uint8_t& action : transition_to_actions[transition] )
            //   actions[action]();

            //   if (failed) {return;   }
            // }

            auto end = std::chrono::high_resolution_clock::now();
            log_time("Successfully parsed file.",start,end);

        } catch (const std::runtime_error& e) {
            log("Runtime Error during Parse.\n" + static_cast<std::string>(e.what()));
            failed = true;
        }
    }

    void test_parse() {

        try{
            auto start = std::chrono::high_resolution_clock::now();

            const char* file_content_beg = file_content_buffer.get();

            file_template.push_back(new PlainText(file_content_beg,21));
            file_template.push_back(new LineSet(7));
            file_template.push_back(new PlainText(file_content_beg+32,1));
            file_template.push_back(new For(file_content_beg+39,1,0,4,1));
            file_template.push_back(new PlainText(file_content_beg+172,1));

            static_cast<For*>(file_template[3])->inner_template.push_back(new PlainText(file_content_beg+44,25));
            static_cast<For*>(file_template[3])->inner_template.push_back(new Line(0,1));
            static_cast<For*>(file_template[3])->inner_template.push_back(new PlainText(file_content_beg+77,3));
            static_cast<For*>(file_template[3])->inner_template.push_back(new Expression(file_content_beg+83,18));
            static_cast<For*>(file_template[3])->inner_template.push_back(new PlainText(file_content_beg+103,27));
            static_cast<For*>(file_template[3])->inner_template.push_back(new Line(0,2));
            static_cast<For*>(file_template[3])->inner_template.push_back(new PlainText(file_content_beg+137,3));
            static_cast<For*>(file_template[3])->inner_template.push_back(new Expression(file_content_beg+143,18));
            static_cast<For*>(file_template[3])->inner_template.push_back(new PlainText(file_content_beg+163,3));
            
            // file_dataframe.insert_column("s");
            // for (uint64_t i=0; i<6; ++i){
            //   file_dataframe.insert_row();
            //   file_dataframe.set(std::make_tuple(i,"s"),"\""+std::to_string(i)+"\"");
            // }

            auto end = std::chrono::high_resolution_clock::now();
            log_time("Successfully parsed file.",start,end);

        } catch (const std::runtime_error& e) {
            log("Runtime Error during Parse.\n" + static_cast<std::string>(e.what()));
            failed = true;
        }
    }

public:

    void indexed_render(const std::vector<int64_t>& senario_indexes){
        try{

            std::ostringstream successful_stream;
            successful_stream << "Successfully rendered file(s): \n";

            std::ostringstream failed_open_stream;
            failed_open_stream << "Error : Failed to open file(s):\n";

            std::ostringstream failed_render_stream;
            failed_render_stream << "Error : Failed to render file(s):\n";

            auto start = std::chrono::high_resolution_clock::now();
            
            for (int64_t i_ : senario_indexes){
                uint64_t i = abs_index(i_);

                file_sub_names[i] = file_sub_name_0 + "." + std::to_string(i) + file_sub_name_1 + "py";
                auto out_file = std::make_unique<std::ofstream>(file_sub_names[i]);
                if (out_file->is_open()) {
                    out_files[i] = std::move(out_file);
                } else {
                    failed_open_stream << " " << file_sub_names[i] << "\n";
                    failed = true;
                    continue;
                }
            }

            for (const auto& generator : file_template){
                generator->write(out_files,out_files_err_msgs,file_dataframe,python_executor);
            }

            for (const auto& [i,out_file] : out_files){
                if (out_file && out_file->is_open())
                    out_file->close();
                if (out_files_err_msgs.find(i)==out_files_err_msgs.end())
                    successful_stream << "  " << file_sub_names[i] << "\n";
                else
                    std::remove(file_sub_names[i].c_str());
            }

            auto end = std::chrono::high_resolution_clock::now();
            log_time(successful_stream.str(),start,end);

            if(failed) {
                log(failed_open_stream.str());
            }

            if (!out_files_err_msgs.empty()){
                failed = true;
                for (const auto& [i,out_files_err_msg] : out_files_err_msgs)
                    failed_render_stream << "   " << file_sub_names[i] << out_files_err_msg.str();
                log(failed_render_stream.str());
            }

        } catch (const std::runtime_error& e) {
            log("Runtime Error during Render.\n" + static_cast<std::string>(e.what()));
            failed = true;
        }

        out_files.clear();
    }

    void render(){
        try{

            std::ostringstream successful_stream;
            successful_stream << "Successfully rendered file(s): \n";

            std::ostringstream failed_open_stream;
            failed_open_stream << "Error : Failed to open file(s):\n";

            std::ostringstream failed_render_stream;
            failed_render_stream << "Error : Failed to render file(s):\n";

            auto start = std::chrono::high_resolution_clock::now();
            
            for (uint64_t i=0; i<file_dataframe.row_count(); ++i){
                file_sub_names[i] = file_sub_name_0 + "." + std::to_string(i) + file_sub_name_1 + "py";
                auto out_file = std::make_unique<std::ofstream>(file_sub_names[i]);
                if (out_file->is_open()) {
                    out_files[i] = std::move(out_file);
                } else {
                    failed_open_stream << " " << file_sub_names[i] << "\n";
                    failed = true;
                    continue;
                }
            }

            for (const auto& generator : file_template){
                generator->write(out_files,out_files_err_msgs,file_dataframe,python_executor);
            }

            for (const auto& [i,out_file] : out_files){
                if (out_file && out_file->is_open())
                    out_file->close();
                if (out_files_err_msgs.find(i)==out_files_err_msgs.end())
                    successful_stream << "  " << file_sub_names[i] << "\n";
                else
                    std::remove(file_sub_names[i].c_str());
            }

            auto end = std::chrono::high_resolution_clock::now();
            log_time(successful_stream.str(),start,end);

            if(failed) {
                log(failed_open_stream.str());
            }

            if (!out_files_err_msgs.empty()){
                failed = true;
                for (const auto& [i,out_files_err_msg] : out_files_err_msgs)
                    failed_render_stream << "   " << file_sub_names[i] << out_files_err_msg.str();
                log(failed_render_stream.str());
            }

        } catch (const std::runtime_error& e) {
            log("Runtime Error during Render.\n" + static_cast<std::string>(e.what()));
            failed = true;
        }

        out_files.clear();
    }

public:

    uint64_t abs_index(int64_t index) const {
        if (index < 0) index += file_dataframe.row_count();
        if ((index < 0)  || (static_cast<uint64_t>(index) >= file_dataframe.row_count())) throw pybind11::index_error("Index out of range");
        return index;
    }

public:

    void log_time(const std::string& message, std::chrono::time_point<std::chrono::high_resolution_clock> start, std::chrono::time_point<std::chrono::high_resolution_clock> end){
        uint64_t time_count = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

        std::string time_unit;

        if (time_count < 1000) {
            time_unit = "ns";
        } else if (time_count < 1000000) {
            time_count /= 1000;
            time_unit = "us";
        } else if (time_count < 1000000000) {
            time_count /= 1000000;
            time_unit = "ms";
        } else {
            time_count /= 1000000000;
            time_unit = "s";
        }

        log(message+"\n\nTime taken: " + std::to_string(time_count) + " " + time_unit);
    }

    void log(const std::string& message, int64_t line_num = -1, int64_t at = -1, int64_t from = -1) {

        std::string log_block;

        if (line_num != -1) {
            uint64_t str_idx = file_line_indexes[line_num];
            uint64_t len = 0;
            while (file_content_buffer[str_idx+len] != '\n' && str_idx+len < file_content_size) ++len;
            ++len;


            if (at > -1) {

                uint64_t window_size = 32;
                uint64_t half_window = 16;
                uint64_t lower_bound = std::max(static_cast<uint64_t>(0), static_cast<uint64_t>(at) - half_window);
                uint64_t upper_bound = std::min(len, static_cast<uint64_t>(at) + half_window);

                if (upper_bound - lower_bound < window_size) {
                    if (lower_bound == 0) {
                        upper_bound = std::min(len, lower_bound + window_size);
                    }
                    if (upper_bound == len) {
                        lower_bound = std::max(static_cast<uint64_t>(0), upper_bound - window_size);
                    }
                }

                std::string line(file_content.substr(str_idx+lower_bound, upper_bound-lower_bound));

                if (from != -1) {
                    if (from > at) {
                        uint64_t limit = std::min(upper_bound,static_cast<uint64_t>(from));
                        line = line + std::string(at - lower_bound, ' ') + "^" + std::string(limit - static_cast<uint64_t>(at), '~');
                    } else {
                        uint64_t limit = std::max(lower_bound,static_cast<uint64_t>(from));
                        line = line + std::string(from - lower_bound, ' ') + std::string(static_cast<uint64_t>(at) - limit, '~') + "^";
                    }
                }
                else {
                    line = line + "\n" + std::string(at - lower_bound, ' ') + "^";
                }
            } else {
                if (len<=32){
                    log_block += "Line " + std::to_string(line_num + 1) + " :\n" + std::string(file_content.substr(str_idx, len)) + "\nmessage:\n";
                } else {
                    log_block += "Line " + std::to_string(line_num + 1) + "\nmessage:\n";
                }
            }

        }

        log_block += message;

        std::stringstream ss(logo_block);
        std::string line_log;

        while (getline(ss, line_log, '\n')) {
            log_width = std::max(log_width, line_log.size());
        }

        log_list.push_back(std::move(log_block));
    }

public:

    std::string get_log() const {
        std::string log_string;
        const std::string bar(log_width, '-');

        for (const std::string& log_block : log_list) {
            log_string += bar + "\n\n" + log_block + "\n\n";
        }

        return log_string;
    }

public:

    void print_dataframe() const {file_dataframe.print();}
    void clear_dataframe() {file_dataframe.clear();}
    void insert_column(const std::string& col) {file_dataframe.insert_column(col);}
    void insert_row() {file_dataframe.insert_row();}
    void insert_row(int64_t row) {file_dataframe.insert_row(row);}
    void remove_column(const std::string& col) {file_dataframe.remove_column(col);}
    void remove_column(int64_t col) {file_dataframe.remove_column(col);}
    void remove_row(int64_t row) {file_dataframe.remove_row(row);}
    void set(std::tuple<int64_t, std::string> pos, const std::string& val) {file_dataframe.set(pos,val);}
    void set(std::tuple<int64_t, int64_t> pos, const std::string& val) {file_dataframe.set(pos,val);}
    std::string get(const std::tuple<int64_t, std::string>& pos) const {return file_dataframe.get(pos);}
    std::string get(const std::tuple<int64_t, int64_t>& pos) const {return file_dataframe.get(pos);}
    uint64_t dataframe_row_count() const {return file_dataframe.row_count();}
    uint64_t dataframe_col_count() const {return file_dataframe.col_count();}
    std::tuple<int64_t, int64_t> dataframe_size() const {
        return std::make_tuple(file_dataframe.row_count(),file_dataframe.col_count());
    }

};

uint64_t TplFileHandler::Line::line = 0;

#endif