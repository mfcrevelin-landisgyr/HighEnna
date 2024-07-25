PYBIND11_MODULE(tplbackend, m) {
    m.doc() = R"pbdoc(
        TplProject Module
        -----------------
        This module provides an interface for managing and processing template files to
        generate code files with substituted parameters.
    )pbdoc";

    pybind11::class_<TplProject>(m, "TplProject")
        .def(pybind11::init<const std::string&>(), 
             pybind11::arg("directory_path"),
             R"pbdoc(
                Initializes the TplProject with the given directory path. 
                The directory is expected to contain only .tpl files, 
                which are templates for generating Python scripts with substituted parameters.
             )pbdoc")
        .def("set_directory", &TplProject::set_directory, 
             pybind11::arg("directory_path"),
             R"pbdoc(
                Loads a new project directory. Clears any previously loaded project data.
                Args:
                    directory_path (str): Path to the new project directory.
             )pbdoc")
        .def("update", &TplProject::update, 
             R"pbdoc(
                Scans the project directory for any changes (file creation, deletion, or modification). 
                Reloads and reprocesses data as needed.
             )pbdoc")
        .def("render", pybind11::overload_cast<const std::vector<std::tuple<int64_t, std::vector<int64_t>>>&>(&TplProject::render), 
             pybind11::arg("indexes"),
             R"pbdoc(
                Renders variations of specified templates based on a list of tuples. 
                Each tuple contains an index and a list of indexes for rendering variations.
                Args:
                    indexes (List[Tuple[int, List[int]]]): List of tuples specifying the templates and variations to render.
             )pbdoc")
        .def("render", pybind11::overload_cast<int64_t, const std::vector<int64_t>&>(&TplProject::render), 
             pybind11::arg("handler_index"), pybind11::arg("scenario_indexes"),
             R"pbdoc(
                Renders specified variations for the template at the given index.
                Args:
                    handler_index (int): Index of the template to render.
                    scenario_indexes (List[int]): List of variation indexes to render.
             )pbdoc")
        .def("render", pybind11::overload_cast<int64_t>(&TplProject::render), 
             pybind11::arg("handler_index"),
             R"pbdoc(
                Renders all variations for the template at the given index.
                Args:
                    handler_index (int): Index of the template to render.
             )pbdoc")
        .def("render", pybind11::overload_cast<>(&TplProject::render), 
             R"pbdoc(
                Renders all variations for all templates in the project.
             )pbdoc")
        .def("__str__", &TplProject::as_string)
        .def("__repr__", &TplProject::as_string)
        .def("__len__", &TplProject::size)
        .def("failed", &TplProject::failed, 
             pybind11::arg("index"),
             R"pbdoc(
                Checks if loading, parsing, or rendering the template at the given index failed.
                Args:
                    index (int): The index of the template to check.
                Returns:
                    bool: True if the operation failed, False otherwise.
             )pbdoc")
        .def("log", &TplProject::log, 
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the log for the template at the given index, containing a summary of actions taken and any error messages.
                Args:
                    index (int): The index of the template to retrieve the log for.
                Returns:
                    str: The log of the template.
             )pbdoc")
        .def("path", &TplProject::path, 
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the absolute path of the template at the given index.
                Args:
                    index (int): The index of the template to retrieve the path for.
                Returns:
                    str: The absolute path of the template.
             )pbdoc")
        .def("name", &TplProject::name, 
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the base name (including extension) of the template at the given index.
                Args:
                    index (int): The index of the template to retrieve the name for.
                Returns:
                    str: The base name of the template.
             )pbdoc")
        .def("text", &TplProject::text, 
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the raw text of the template at the given index as a string.
                Args:
                    index (int): The index of the template to retrieve the text for.
                Returns:
                    str: The raw text of the template.
             )pbdoc");
}