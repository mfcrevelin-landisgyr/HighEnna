<img src="HighEnna-Graphical/source_files/assets/icons/icon.png" alt="Image" width="300">

# High Enna

High Enna is a text processor designed to work with code files. It identifies specific placeholder structures in a template file, based on a defined syntax, and generates variations of that template file substituting these blocks with hard-coded values. High Enna includes a graphical user interface (GUI) that allows users to view and edit the substitution values in a table format, similar to Excel.

## Getting Started

### Prerequisites

To build High Enna, you'll need the following software:

- Visual Studio (for building the backend)
- Inno Setup Compiler (for creating the installer)
- Python 3.9 or higher

### Build Instructions

1. **Setup Visual Studio Project**:
    - Navigate to `HighEnna-Backend`.
    - Run `make_visual_studio_project.bat` to set up the Visual Studio compilation scheme. This will create a `VS` directory inside `HighEnna-Backend`.
   		- This project, as is, links against Python 3.9 libraries. Before creating the Visual Studio project, make sure to either install Python 3.9 with debugging options on your computer and set it to be the first Python version in your `PATH` enviroment variable or, if you want to link agains libs of a different version of Python, edit the following lines in `CMakeLists.txt` under `HighEnna-Backend` to link against them:
      		```cmake
      		set(DPYTHON_LIBRARY_RELEASE "C:/Program Files/Python39/libs/python39.lib")
      		set(DPYTHON_LIBRARY_DEBUG "C:/Program Files/Python39/libs/python39_d.lib")
      		```
    - Open the `.sln` file inside the `VS` directory with Visual Studio.
    - Compile the project to generate `tplbackend.pyd` under `Release` or `Debug`.

2. **Copy Backend Output**:
    - Copy the `tplbackend.pyd` file to `HighEnna-Graphical/source_files`, replacing the existing file.

3. **Build the Graphical Executable**:
    - Navigate to `HighEnna-Graphical`.
    - Run `make_graphical_executable.bat`.

4. **Create Installer** (Optional):
    - Navigate to `HighEnna-Installer`.
    - Run `make_installer.bat` to produce an installer for the application. Note that this step requires Inno Setup Compiler to be installed on your computer.

### Development Workflow

#### Modifying Backend Code

- Make code changes in `HighEnna-Backend/source_files`.
- Follow these steps to apply your changes:
  1. Recompile `tplbackend.pyd` with Visual Studio.
  2. Copy the updated `tplbackend.pyd` to `HighEnna-Graphical/source_files`, replacing the existing file.
  3. Run `make_graphical_executable.bat` under `HighEnna-Graphical`.
  4. (Optional) Run `make_installer.bat` under `HighEnna-Installer` to update the installer.

#### Modifying GUI Code

- Make code changes in `HighEnna-Graphical/source_files`.
- Follow these steps to apply your changes:
  1. Run `make_graphical_executable.bat` under `HighEnna-Graphical`.
  2. (Optional) Run `make_installer.bat` under `HighEnna-Installer` to update the installer.

### Debugging

- Generating the installer is not required for debugging.
    - After following the steps to build `tplbackend.pyd` and copying it to `HighEnna-Graphical/source_files`, you can run it directly from `HighEnna-Graphical/source_files` by opening a terminal in that directory and using the command:
      ```shell
      python .\main.py
      ```
      or
    - After following the steps to build the executable, you can run it directly from `HighEnna-Graphical/build/HighEnna.exe`.

## Acknowledgements

This software makes use of the pybind11 library from Wenzel Jakob and contributors which is licensed under a BSD-style license.  
Copyright (c) 2016 Wenzel Jakob  
https://github.com/pybind/pybind11/blob/master/LICENSE

This software makes use of the json class from Niels Lohmann which is licensed under the MIT License.  
Copyright © 2013-2022 Niels Lohmann  
https://json.nlohmann.me/home/license/

This software makes use of the Qt6 framework from Qt Company Ltd. and contributors which is licensed under the GNU LGPL License.  
Copyright (C) 2018 Qt Company Ltd.  
https://doc.qt.io/qt-6/lgpl.html
