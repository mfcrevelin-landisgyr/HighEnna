#ifndef INCLUDES_HEADER
#define INCLUDES_HEADER

// #include <initializer_list>
// #include <algorithm>
// #include "json.hpp"
// using json = nlohmann::ordered_json;

// #include <filesystem>
// #include <iostream>
// #include <fstream>
// #include <sstream>
// #include <iomanip>

// #include <string_view>
// #include <string>

// #include <algorithm>
// #include <limits.h>
// #include <cstdint>

// #include <stdexcept>
// #include <cerrno>

// #include <chrono>
// #include <memory>
// #include <thread>
// #include <atomic>
// #include <mutex>
// #include <numeric>

// #include <unordered_set>
// #include <unordered_map>
// #include <forward_list>
// #include <functional>
// #include <vector>
// #include <queue>
// #include <tuple>
// #include <array>
// #include <stack>
// #include <set>
// #include <regex>

// using namespace std::chrono_literals;

#include <pybind11/embed.h>
#include <pybind11/eval.h>
#include <pybind11/stl.h>

template<std::size_t R, typename Func, typename... Args>
void applyDFA(const uint8_t (&dfa)[R][256], const std::string_view& buffer, Func&& func, Args&&... args) {
    uint64_t ptr = 0;
    uint16_t transition = 0;
    uint8_t& state  = *(reinterpret_cast<uint8_t*>(&transition) + 0); // Least significant byte on LE systems, Most  in BE ones. 
    uint8_t& pstate = *(reinterpret_cast<uint8_t*>(&transition) + 1); // Most  significant byte on LE systems, Least in BE ones. 

    while (ptr < buffer.size()) {
        pstate = state;
        state = dfa[state][static_cast<uint8_t>(buffer[ptr])];
        func(transition, ptr, std::forward<Args>(args)...);
        ++ptr;
    }
}

#include "dataframe.h"
#include "file_handler.h"

#endif