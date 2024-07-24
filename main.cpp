#include "includes.h"

// #include <pybind11/pybind11.h>
// #include <pybind11/eval.h>
// #include <pybind11/stl.h>
// #include <string>

// namespace py = pybind11;


// struct PythonExecutor {
//     py::dict globals;
//     py::dict locals;
//     std::string error_message;
//     bool bFailed = false;
//     std::string eval_result;

//     PythonExecutor() {
//         globals["__builtins__"] = py::module::import("builtins").attr("__dict__");
//     }

//     void exec(const std::string& code) {
//         try {
//             py::exec(code.c_str(), globals, locals);
//             error_message.clear();
//             bFailed = false;
//         } catch (const py::error_already_set& e) {
//             error_message = e.what();
//             bFailed = true;
//         }
//     }

//     void eval(const std::string& code) {
//         try {
//             py::object result = py::eval(code.c_str(), globals, locals);
//             eval_result = py::str(result).cast<std::string>();
//             error_message.clear();
//             bFailed = false;
//         } catch (const py::error_already_set& e) {
//             error_message = e.what();
//             bFailed = true;
//         }
//     }

//     bool failed() const {
//         return bFailed;
//     }

//     std::string get_error() const {
//         return error_message;
//     }

//     std::string get_eval() const {
//         return eval_result;
//     }
// };

// struct TplProject {
//     PythonExecutor* python_executor;

//     TplProject() {
//         python_executor = new PythonExecutor();
//     }

//     ~TplProject() {
//     	delete python_executor;
//     }

//     void exec(const std::string& code) {
//         python_executor->exec(code);
//     }

//     void eval(const std::string& code) {
//         python_executor->eval(code);
//     }

//     bool failed() const {
//         return python_executor->failed();
//     }

//     std::string get_error() const {
//         return python_executor->get_error();
//     }

//     std::string get_eval() const {
//         return python_executor->get_eval();
//     }
// };

// PYBIND11_MODULE(tplbackend, m) {
//     py::class_<TplProject>(m, "TplProject")
//         .def(py::init<>())
//         .def("exec", &TplProject::exec)
//         .def("eval", &TplProject::eval)
//         .def("failed", &TplProject::failed)
//         .def("get_error", &TplProject::get_error)
//         .def("get_eval", &TplProject::get_eval);
// }
