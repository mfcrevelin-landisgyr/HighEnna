#ifndef PYTHON_EXECUTOR_HEADER
#define PYTHON_EXECUTOR_HEADER

struct PythonExecutor {
    pybind11::dict globals;
    pybind11::dict locals;
    std::string error_message;
    bool bFailed = false;
    std::string eval_result;

    PythonExecutor() {
        globals["__builtins__"] = pybind11::module::import("builtins").attr("__dict__");
    }

    void execute(const std::string& code) {
        pybind11::gil_scoped_acquire acquire;
        try {
            pybind11::exec(code.c_str(), globals, locals);
            error_message.clear();
            bFailed = false;
        } catch (const pybind11::error_already_set& e) {
            error_message = e.what();
            bFailed = true;
        }
    }

    void evaluate(const std::string& code) {
        pybind11::gil_scoped_acquire acquire;
        try {
            pybind11::object result = pybind11::eval(code.c_str(), globals, locals);
            eval_result = pybind11::str(result).cast<std::string>();
            error_message.clear();
            bFailed = false;
        } catch (const pybind11::error_already_set& e) {
            error_message = e.what();
            bFailed = true;
        }
    }

    void module(const std::string& module_name) {
        pybind11::gil_scoped_acquire acquire;
        try {
            pybind11::module mod = pybind11::module::import(module_name.c_str());

            globals[module_name.c_str()] = mod;
            error_message.clear();
            bFailed = false;
        } catch (const pybind11::error_already_set& e) {
            error_message = e.what();
            bFailed = true;
        }
    }

    void from_module(const std::string& attribute, const std::string& module_name) {
        pybind11::gil_scoped_acquire acquire;
        try {
            pybind11::module mod = pybind11::module::import(module_name.c_str());

            pybind11::object attr = mod.attr(attribute.c_str());

            globals[attribute.c_str()] = attr;
            error_message.clear();
            bFailed = false;
        } catch (const pybind11::error_already_set& e) {
            error_message = e.what();
            bFailed = true;
        }
    }

    bool failed() const {
        return bFailed;
    }

    std::string get_error() const {
        return error_message;
    }

    std::string get_eval() const {
        return eval_result;
    }
};

#endif
