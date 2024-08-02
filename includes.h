#ifndef INCLUDES_HEADER
#define INCLUDES_HEADER

#include <functional>
#include <algorithm>

#include <filesystem>
#include <iostream>
#include <fstream>
#include <sstream>

#include <string>
#include <string_view>

#include <cstdint>

#include <stdexcept>
#include <cerrno>

#include <chrono>
#include <memory>
#include <thread>
#include <mutex>

#include <unordered_set>
#include <unordered_map>
#include <vector>
#include <queue>
#include <tuple>
#include <array>
#include <stack>
#include <set>

using namespace std::chrono_literals;

// #include <Python.h>
#include <pybind11/pybind11.h>
#include <pybind11/eval.h>
#include <pybind11/stl.h>

#include "encoding.h"
#include "python_executor.h"
#include "dataframe.h"
#include "file_handler.h"
#include "tpl_project.h"
#include "module.h"


#endif