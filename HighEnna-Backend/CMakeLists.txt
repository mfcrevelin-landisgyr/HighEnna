cmake_minimum_required(VERSION 3.29)

# Project name
project(HighEnna)

# Set the C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# MSVC runtime: /MD or /MDd depending on config
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

# Source files
file(GLOB SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/source_files/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/source_files/*.h"
)

# Python settings
set(DPYTHON_INCLUDE_DIR "C:/Program Files/Python39/include")
set(DPYTHON_LIBRARY_RELEASE "C:/Program Files/Python39/libs/python39.lib")
set(DPYTHON_LIBRARY_DEBUG "C:/Program Files/Python39/libs/python39_d.lib")

# pybind11
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/pybind11)

# Build the Python module
pybind11_add_module(tplbackend ${SOURCES})

# Include Python directories
target_include_directories(tplbackend PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/source_files
    ${DPYTHON_INCLUDE_DIR}
)

# Compile definitions
target_compile_definitions(tplbackend PRIVATE 
    $<$<CONFIG:Debug>:_DEBUG>
)

# Link Python libraries
target_link_libraries(tplbackend PRIVATE 
    $<$<CONFIG:Release>:${DPYTHON_LIBRARY_RELEASE}>
    $<$<CONFIG:Debug>:${DPYTHON_LIBRARY_DEBUG}>
)

# Link pybind11 libraries
target_link_libraries(tplbackend PRIVATE 
    pybind11::pybind11 
    pybind11::embed 
    pybind11::module
)

# Remove the Python version suffix from the generated .pyd file
set_target_properties(tplbackend PROPERTIES SUFFIX ".pyd")

