#ifndef INCLUDES_HEADER
#define INCLUDES_HEADER

// #include <initializer_list>
#include <algorithm>
#include "json.hpp"
using json = nlohmann::json;

// #include <filesystem>
// #include <iostream>
// #include <fstream>
// #include <sstream>

#include <string>
#include <string_view>

// #include <limits.h>
#include <cstdint>

// #include <stdexcept>
// #include <cerrno>

// #include <chrono>
#include <memory>
// #include <thread>
// #include <atomic>
// #include <mutex>

#include <unordered_set>
#include <unordered_map>
// #include <forward_list>
// #include <functional>
#include <vector>
// #include <queue>
#include <tuple>
// #include <array>
#include <stack>
// #include <set>

using namespace std::chrono_literals;

#include <pybind11/pybind11.h>
// #include <pybind11/eval.h>
#include <pybind11/stl.h>

#define NOMINMAX
#include <windows.h>

namespace std {
    template <typename... Args>
    struct hash<std::tuple<Args...>> {
        std::size_t operator()(const std::tuple<Args...>& t) const {
            return hash_impl(t, std::index_sequence_for<Args...>{});
        }

    private:
        template <typename Tuple, std::size_t... Index>
        std::size_t hash_impl(const Tuple& t, std::index_sequence<Index...>) const {
            std::size_t h = 0;
            (..., (h ^= std::hash<std::size_t>{}(std::hash<std::size_t>{}(h) - std::hash<std::tuple_element_t<Index, Tuple>>{}(std::get<Index>(t)))));
            return h;
        }
    };
}

// #include "task_counter.h"
// #include "encoding.h"
// #include "python_executor.h"
#include "dataframe.h"
// #include "file_handler.h"
// #include "tpl_project.h"
#include "module.h"

#endif