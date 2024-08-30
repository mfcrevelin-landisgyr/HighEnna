PYBIND11_MODULE(tplbackend, m) {
    m.doc() = R"pbdoc(
        TplProject Module
        -----------------
        This module provides an interface for managing and processing template files to
        generate code files with hardcoded parameters.
    )pbdoc";

    pybind11::class_<TplProject>(m, "TplProject")
        .def(pybind11::init<const std::string&>(),
             pybind11::arg("directory_path"),
             R"pbdoc(
                Initializes the TplProject with the given directory path.
                The directory is expected to contain only .tpl files,
                which are templates for generating scripts with hardcoded parameters.
             )pbdoc")
        .def("set_directory", &TplProject::set_directory,
             pybind11::arg("directory_path"),
             R"pbdoc(
                Loads a new project directory. Clears any previously loaded project data.
                Args:
                    directory_path (str): Path to the new project directory.
             )pbdoc")
        .def("set_output_directory", &TplProject::set_output_directory,
             pybind11::arg("output_directory_path"),
             R"pbdoc(
                Sets a new script output directory.
                Args:
                    output_directory_path (str): Path to the new output directory.
             )pbdoc")
        .def("update_modules", &TplProject::update_modules,
             pybind11::arg("index"),pybind11::arg("add_modules"),pybind11::arg("remove_modules"),
             R"pbdoc(
                Updates the list of modules for the specified template.
                Args:
                    index (int): Index of the template whose modules list is to be updated.
                    add_modules Set[str]: A set of module_name strings stating modules to be added.
                    rmv_modules Set[str]: A set of module_name strings stating modules to be removed.
             )pbdoc")
        .def("update_from_modules", &TplProject::update_from_modules,
             pybind11::arg("index"),pybind11::arg("add_from_modules"),pybind11::arg("remove_from_modules"),
             R"pbdoc(
                Updates the list of from modules for the specified template.
                Args:
                    index (int): Index of the template whose from modules list is to be updated.
                    add_from_modules Set[Tuple[str,str]]: A set of (module_name,attribute) pairs stating from modules to be added.
                    rmv_from_modules Set[Tuple[str,str]]: A set of (module_name,attribute) pairs stating from modules to be removed.
             )pbdoc")
        .def("update_file_modules", &TplProject::update_file_modules,
             pybind11::arg("index"),pybind11::arg("add_file_modules"),pybind11::arg("remove_file_modules"),
             R"pbdoc(
                Updates the list of file modules for the specified template.
                Args:
                    index (int): Index of the template whose file modules list is to be updated.
                    add_file_modules Set[Tuple[str,str]]: A set of(file_name,file_content) pairs stating file modules to be added.
                    rmv_file_modules Set[Tuple[str,str]]: A set of(file_name,file_content) pairs stating file modules to be removed.
             )pbdoc")
        .def("get_modules", &TplProject::get_modules,
             pybind11::arg("index"),
             R"pbdoc(
                Gets a list of imported modules needed to render the specified template.
                Args:
                    index (int): Index of the template to fetch module list from.
             )pbdoc")
        .def("get_from_modules", &TplProject::get_from_modules,
             pybind11::arg("index"),
             R"pbdoc(
                Gets a list of imported attributes from modules needed to render the specified template.
                Args:
                    index (int): Index of the template to fetch module list from.
             )pbdoc")
        .def("get_file_modules", &TplProject::get_file_modules,
             pybind11::arg("index"),
             R"pbdoc(
                Imports a python file. Accessible in context blocks.
                Gets a list of imported python files needed to render the specified template.
                Args:
                    index (int): Index of the template to fetch module list from.
             )pbdoc")
        .def("update", &TplProject::update,
             R"pbdoc(
                Scans the project directory for any changes (file creation, deletion, or modification).
                Reloads and reprocesses data as needed.
             )pbdoc")
        .def("render", pybind11::overload_cast<const std::vector<std::tuple<int64_t, std::vector<int64_t>>>&>(&TplProject::render),
             pybind11::arg("indices"),
             R"pbdoc(
                Renders scripts from specified templates based on a list of tuples.
                Each tuple contains a template index and a list of script indices for rendering.
                Args:
                    indices (List[Tuple[int, List[int]]]): List of tuples specifying the templates and scripts to render.
             )pbdoc")
        .def("render", pybind11::overload_cast<int64_t, const std::vector<int64_t>&>(&TplProject::render),
             pybind11::arg("index"), pybind11::arg("row_indices"),
             R"pbdoc(
                Renders specified scripts from the specified template.
                Args:
                    index (int): Index of the template to render.
                    row_indices (List[int]): List of script indices to render.
             )pbdoc")
        .def("render", pybind11::overload_cast<int64_t>(&TplProject::render),
             pybind11::arg("index"),
             R"pbdoc(
                Renders all scripts from the specified template.
                Args:
                    index (int): Index of the template to render.
             )pbdoc")
        .def("render", pybind11::overload_cast<>(&TplProject::render),
             R"pbdoc(
                Renders all scripts from all templates in the project.
             )pbdoc")
        .def("__str__", &TplProject::as_string)
        .def("__repr__", &TplProject::as_string)
        .def("__len__", &TplProject::size)
        .def("load_failed", &TplProject::load_failed,
             pybind11::arg("index"),
             R"pbdoc(
                Checks whether loading or parsing the specified template failed.
                Args:
                    index (int): The index of the template to check.
                Returns:
                    bool: True if the operation failed, False otherwise.
             )pbdoc")
        .def("render_failed", pybind11::overload_cast<int64_t>(&TplProject::render_failed),
             pybind11::arg("index"),
             R"pbdoc(
                Checks whether rendering any script from the specified template failed.
                Args:
                    index (int): The index of the template to check.
                Returns:
                    bool: True if the operation failed, False otherwise.
             )pbdoc")
        .def("render_failed", pybind11::overload_cast<int64_t,int64_t>(&TplProject::render_failed),
             pybind11::arg("index"), pybind11::arg("row"),
             R"pbdoc(
                Checks whether rendering any script from the specified template failed.
                Args:
                    index (int): The index of the template whose script to check.
                    row (int): The index of the script from the specified template to check.
                Returns:
                    bool: True if the operation failed, False otherwise.
             )pbdoc")
        .def("log", &TplProject::log,
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the log for the specified template, containing a summary of actions taken and any error messages.
                Args:
                    index (int): The index of the template to retrieve the log from.
                Returns:
                    str: The log of the template.
             )pbdoc")
        .def("vars", &TplProject::vars,
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the set of tagged variables in the specified template.
                Args:
                    index (int): The index of the template to retrieve tagged variables from.
                Returns:
                    list[str]: The set of tagged variables in the template.
             )pbdoc")
        .def("path", &TplProject::path,
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the absolute path of the specified template.
                Args:
                    index (int): The index of the template to retrieve the path from.
                Returns:
                    str: The absolute path of the template.
             )pbdoc")
        .def("name", &TplProject::name,
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the file's base name (including extension) of the specified template.
                Args:
                    index (int): The index of the template to retrieve the file base name from.
                Returns:
                    str: The base name of the template.
             )pbdoc")
        .def("code", &TplProject::text,
             pybind11::arg("index"),
             R"pbdoc(
                Retrieves the raw code of the specified template as a string.
                Args:
                    index (int): The index of the template to retrieve the raw code from.
                Returns:
                    str: The raw code of the template.
             )pbdoc")
        .def("save_data", &TplProject::save_data,
             pybind11::arg("index"),
             R"pbdoc(
                Saves the dataframe for the specified template into itself.
                Args:
                    index (int): The index of the template.
             )pbdoc")
        .def("save_modules", &TplProject::save_modules,
             R"pbdoc(
                Saves module import data.
             )pbdoc")
        .def("clear_dataframe", &TplProject::clear_dataframe,
             pybind11::arg("index"),
             R"pbdoc(
                Clears the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
             )pbdoc")
        .def("clear_dataframe_indices", pybind11::overload_cast<int64_t,const std::list<std::tuple<int64_t,std::string>>&>(&TplProject::clear_dataframe_indices),
             pybind11::arg("index"),pybind11::arg("cell_indices"),
             R"pbdoc(
                Clears the specified cells from the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
                    cell_indices List[tuple(int,str)]: The (row,col) cell indices to clead within the dataframe.
             )pbdoc")
        .def("clear_dataframe_indices", pybind11::overload_cast<int64_t,const std::list<std::tuple<int64_t,int64_t>>&>(&TplProject::clear_dataframe_indices),
             pybind11::arg("index"),pybind11::arg("cell_indices"),
             R"pbdoc(
                Clears the specified cells from the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
                    cell_indices List[tuple(int,int)]: The (row,col) cell indices to clead within the dataframe.
             )pbdoc")
        .def("insert_column", &TplProject::insert_column,
             pybind11::arg("index"), pybind11::arg("col"),
             R"pbdoc(
                Inserts a new column into the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
                    col (str): The name of the new column.
             )pbdoc")
        .def("insert_rows", pybind11::overload_cast<int64_t, int64_t>(&TplProject::insert_rows),
             pybind11::arg("index"),pybind11::arg("num_rows"),
             R"pbdoc(
                Inserts num_rows rows at the end of the dataframe from the specidfied template.
                Args:
                    index (int): The index of the template.
                    num_rows (int): Number of rows to add.
             )pbdoc")
        .def("insert_rows", pybind11::overload_cast<int64_t, const std::list<int64_t>&>(&TplProject::insert_rows),
             pybind11::arg("index"), pybind11::arg("row_indices"),
             R"pbdoc(
                Inserts a new row between the specified row indices and the previous row in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                    row_indices (int): The indices of the rows to have a row inserted before it.
             )pbdoc")
        .def("remove_rows", pybind11::overload_cast<int64_t, const std::list<int64_t>&>(&TplProject::remove_rows),
             pybind11::arg("index"), pybind11::arg("row_indices"),
             R"pbdoc(
                Removes a row from the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
                    row_indices (int): The position of the row to remove.
             )pbdoc")
        .def("duplicate_rows", pybind11::overload_cast<int64_t, const std::list<int64_t>&>(&TplProject::duplicate_rows),
             pybind11::arg("index"), pybind11::arg("row_indices"),
             R"pbdoc(
                Inserts a new row between the specified row indices and the next row in the dataframe from the specified template and copies the data in the specified row indices into the new rows.
                Args:
                    index (int): The index of the template.
                    row_indices (int): The indices of the rows to be duplicated.
             )pbdoc")
        .def("set_cell", pybind11::overload_cast<int64_t, int64_t, const std::string&, const std::string&>(&TplProject::set),
             pybind11::arg("index"), pybind11::arg("row"), pybind11::arg("col"), pybind11::arg("val"),
             R"pbdoc(
                Sets the value for the (row,col) cell position in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                    row (int): The script index.
                    col (str): The column name.
                    val (str): The value to set the cell to.
             )pbdoc")
        .def("set_cell", pybind11::overload_cast<int64_t, int64_t, int64_t, const std::string&>(&TplProject::set),
             pybind11::arg("index"), pybind11::arg("row"), pybind11::arg("col"), pybind11::arg("val"),
             R"pbdoc(
                Sets the value for the (row,col) cell position in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                    row (int): The script index.
                    col (int): The column index.
                    val (str): The value to set the cell to.
             )pbdoc")
        .def("set_cells", pybind11::overload_cast<int64_t, const std::list<std::tuple<int64_t, std::string, std::string>>&>(&TplProject::set),
             pybind11::arg("index"), pybind11::arg("cell_values"),
             R"pbdoc(
                Sets multiple cell values in the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
                    cell_values List[Tuple[int,str,str]]: Each tuple contains (row, col, val) representing the script index, column name, and value to set the cell to.
             )pbdoc")
        .def("set_cells", pybind11::overload_cast<int64_t, const std::list<std::tuple<int64_t, int64_t, std::string>>&>(&TplProject::set),
             pybind11::arg("index"), pybind11::arg("cell_values"),
             R"pbdoc(
                Sets multiple cell values in the dataframe for the specified template.
                Args:
                    index (int): The index of the template.
                    cell_values List[Tuple[int,int,str]]: Each tuple contains (row, col, val) representing the script index, column index, and value to set the cell to.
             )pbdoc")
        .def("get_cell", pybind11::overload_cast<int64_t, int64_t, const std::string&>(&TplProject::get),
             pybind11::arg("index"), pybind11::arg("row"), pybind11::arg("col"),
             R"pbdoc(
                Gets the value at the (row,col) cell position in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                    row (int): The script index.
                    col (str): The column name.
                Returns:
                    str: The value at the specified position.
             )pbdoc")
        .def("get_cell", pybind11::overload_cast<int64_t, int64_t, int64_t>(&TplProject::get),
             pybind11::arg("index"), pybind11::arg("row"), pybind11::arg("col"),
             R"pbdoc(
                Gets the value at the (row,col) cell position in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                    row (int): The script index.
                    col (int): The column index.
                Returns:
                    str: The value at the specified position.
             )pbdoc")
        .def("undo", &TplProject::undo, pybind11::arg("index"),
             R"pbdoc(
                Undoes the last edit operation done in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
             )pbdoc")
        .def("redo", &TplProject::redo, pybind11::arg("index"),
             R"pbdoc(
                Redoes the last edit operation undone by undo. 
                Args:
                    index (int): The index of the template.
             )pbdoc")
        .def("row_count", &TplProject::row_count, pybind11::arg("index"),
             R"pbdoc(
                Gets the number of rows in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                Returns:
                    int: The number of rows in the dataframe.
             )pbdoc")
        .def("col_count", &TplProject::col_count, pybind11::arg("index"),
             R"pbdoc(
                Gets the number of columns in the dataframe from the specified template.
                Args:
                    index (int): The index of the template.
                Returns:
                    int: The number of columns in the dataframe.
             )pbdoc")
        .def("total", &TplProject::total,
             R"pbdoc(
                Gets the number of scripts currently being rendered (since last render call).
                Returns:
                    int: the number of scripts currently being rendered.
             )pbdoc")
        .def("current", &TplProject::current,
             R"pbdoc(
                Gets the number of scripts that have already been rendered (since last render call).
                Returns:
                    int: the number of scripts that have already been rendered.
             )pbdoc")
        .def("is_finished", &TplProject::is_finished,
             R"pbdoc(
                Checks whether all scripts sent off to be rendered since the last render call already finished.
                Returns:
                    bool: whether all renders already finished.
             )pbdoc");
}