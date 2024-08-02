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
             )pbdoc")
        .def("clear_dataframe", &TplProject::clear_dataframe,
             pybind11::arg("index"),
             R"pbdoc(
                Clears all data in the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
             )pbdoc")
        .def("insert_column", &TplProject::insert_column,
             pybind11::arg("index"), pybind11::arg("col"),
             R"pbdoc(
                Inserts a new column into the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                    col (str): The name of the new column.
             )pbdoc")
        .def("insert_row", pybind11::overload_cast<int64_t>(&TplProject::insert_row),
             pybind11::arg("index"),
             R"pbdoc(
                Inserts a new row into the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
             )pbdoc")
        .def("insert_row", pybind11::overload_cast<int64_t, int64_t>(&TplProject::insert_row),
             pybind11::arg("index"), pybind11::arg("row"),
             R"pbdoc(
                Inserts a new row at the specified position into the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                    row (int): The position where the new row will be inserted.
             )pbdoc")
        .def("remove_column", pybind11::overload_cast<int64_t, const std::string&>(&TplProject::remove_column),
             pybind11::arg("index"), pybind11::arg("col"),
             R"pbdoc(
                Removes a column from the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                    col (str): The name of the column to remove.
             )pbdoc")
        .def("remove_column", pybind11::overload_cast<int64_t, int64_t>(&TplProject::remove_column),
             pybind11::arg("index"), pybind11::arg("col"),
             R"pbdoc(
                Removes a column at the specified position from the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                    col (int): The position of the column to remove.
             )pbdoc")
        .def("remove_row", &TplProject::remove_row,
             pybind11::arg("index"), pybind11::arg("row"),
             R"pbdoc(
                Removes a row from the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                    row (int): The position of the row to remove.
             )pbdoc")
        .def("dataframe_set", pybind11::overload_cast<int64_t, std::tuple<int64_t, std::string>, const std::string&>(&TplProject::set),
             pybind11::arg("index"), pybind11::arg("pos"), pybind11::arg("val"),
             R"pbdoc(
                Sets a value in the dataframe for the template at the given index and position.
                Args:
                    index (int): The index of the template.
                    pos (Tuple[int, str]): The position in the dataframe (row, column name).
                    val (str): The value to set.
             )pbdoc")
        .def("dataframe_set", pybind11::overload_cast<int64_t, std::tuple<int64_t, int64_t>, const std::string&>(&TplProject::set),
             pybind11::arg("index"), pybind11::arg("pos"), pybind11::arg("val"),
             R"pbdoc(
                Sets a value in the dataframe for the template at the given index and position.
                Args:
                    index (int): The index of the template.
                    pos (Tuple[int, int]): The position in the dataframe (row, column index).
                    val (str): The value to set.
             )pbdoc")
        .def("dataframe_get", pybind11::overload_cast<int64_t, const std::tuple<int64_t, std::string>&>(&TplProject::get),
             pybind11::arg("index"), pybind11::arg("pos"),
             R"pbdoc(
                Gets a value from the dataframe for the template at the given index and position.
                Args:
                    index (int): The index of the template.
                    pos (Tuple[int, str]): The position in the dataframe (row, column name).
                Returns:
                    str: The value at the specified position.
             )pbdoc")
        .def("dataframe_get", pybind11::overload_cast<int64_t, const std::tuple<int64_t, int64_t>&>(&TplProject::get),
             pybind11::arg("index"), pybind11::arg("pos"),
             R"pbdoc(
                Gets a value from the dataframe for the template at the given index and position.
                Args:
                    index (int): The index of the template.
                    pos (Tuple[int, int]): The position in the dataframe (row, column index).
                Returns:
                    str: The value at the specified position.
             )pbdoc")
        .def("dataframe_row_count", &TplProject::dataframe_row_count, pybind11::arg("index"),
             R"pbdoc(
                Gets the number of rows in the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                Returns:
                    int: The number of rows in the dataframe.
             )pbdoc")
        .def("dataframe_col_count", &TplProject::dataframe_col_count, pybind11::arg("index"),
             R"pbdoc(
                Gets the number of columns in the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                Returns:
                    int: The number of columns in the dataframe.
             )pbdoc")
        .def("dataframe_size", &TplProject::dataframe_size, pybind11::arg("index"),
             R"pbdoc(
                Gets the size (number of rows and columns) of the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template.
                Returns:
                    Tuple[int, int]: The size of the dataframe (number of rows, number of columns).
             )pbdoc")
        .def("print_dataframe", &TplProject::print_dataframe, 
             pybind11::arg("index"),
             R"pbdoc(
                Prints the dataframe for the template at the given index.
                Args:
                    index (int): The index of the template to print the dataframe for.
             )pbdoc");

}