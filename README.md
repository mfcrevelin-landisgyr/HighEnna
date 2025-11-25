<img src="HighEnna-Graphical/source_files/assets/icons/icon.png" alt="Image" width="300">

# High Enna

High Enna is a template-driven text processing tool designed for code-oriented workflows. It processes a templated file containing placeholder blocks defined through a specific syntax. A graphical, spreadsheet-like interface presents a structured table where substitution values for these placeholders can be configured, including multiple sets of variations. High Enna then combines the template with these configured values to generate multiple output versions of the original file with hard-coded substitutions applied.

# How to Use

This section describes how to build, run, and debug the project.  
For a deeper explanation of the system architecture, see **[How It Works](#how-it-works)**.

## Build Chain Overview

The project is composed of four components arranged in dependency order:

1. **Documentation**
2. **Backend**
3. **Frontend**
4. **Installer**

- **Documentation** and **Backend** are independent.  
- **Frontend** depends on both **Documentation** and **Backend**.  
- **Installer** depends on the **Frontend**.

Each component contains:

- `source_files/` — the component’s relevant source code  
- `make.bat` — rebuilds the component and triggers dependent builds if needed

Running the `make.bat` of a later component automatically rebuilds earlier components when their outputs are missing or outdated.
There is no need to build each component manually, just the latest component you want to have built.

---

## 1. Documentation Component

The documentation system uses **Sphinx** to generate HTML pages included with the application.  
These pages are displayed by the frontend through an embedded web engine, allowing the user to browse the documentation directly inside the application.

### Build

```shell
cd Documentation
make.bat
```

- Gegenerates the HTML using Sphinx and the configured theme if missing or outdated  
- Injects the generated files into the frontend directory
- When ran manually, automatically opens the generated HTML in the browser.

## 2. Backend Component

The backend is implemented in **C++** and compiled into a Python extension module (`.pyd`).  
It provides three core operations required by the frontend:

- **encode** — converts a raw byte buffer into a restricted ASCII-printable representation  
- **decode** — restores the original binary data from the encoded form  
- **parse** — analyzes the template structure and identifies placeholder blocks

### Build

```shell
cd Backend
make.bat
```

- Rebuilds the module if missing or outdated 
- Injects the resulting `.pyd` into the frontend’s directory

## 3. Frontend Component

The frontend is a **Python** application built with **PyQt6**.  
It is responsible for:

- Offering a spreadsheet-like interface for defining substitution values  
- Managing multiple variation configurations  
- Interacting with the backend `.pyd` module  
- Displaying the bundled documentation through an embedded web engine  
- Producing the final generated output files

### Build

```shell
cd Frontend
make.bat
```

- Invokes the **Backend** and **Documentation** build scripts  
- Uses **PyInstaller** to generate a single-file `.exe` if missing or outdated

To run without building an executable, make sure to run the **Backend** and **Documentation** build scripts manually, then:

```shell
cd Frontend/source_files
python main.py
```

## 4. Installer Component

The Installer uses **Inno Setup** to assemble the final distributable installer package.

### Build

```shell
cd Installer
make.bat
```

- Calls the **Frontend** build scripts  
- Packages all required files into an installer executable

---

# Debugging

- **Documentation**  
  After building, the generated HTML documentation opens automatically in the default browser.  
  The `.html` files can also be opened manually.

- **Backend**  
  The generated `.pyd` module may be imported directly into a Python console for testing:
  ```shell
  cd Backend/source_files/VS/Release
  python
  ```
  ```python
  import highennabackend
  ```

- **Frontend**  
  Recommended debugging method (since you can see exceptions' details this way):
  ```shell
  cd Frontend/source_files
  python main.py
  ```
  Alternatively, build and run the executable.

---

## Acknowledgements

This software makes use of the pybind11 library from Wenzel Jakob and contributors which is licensed under a BSD-style license.  
Copyright © 2016 Wenzel Jakob and contributors  
https://github.com/pybind/pybind11/blob/master/LICENSE

This software makes use of the json class from Niels Lohmann which is licensed under the MIT License.  
Copyright © 2013-2022 Niels Lohmann  
https://json.nlohmann.me/home/license/

This software makes use of the Qt6 framework from Qt Company Ltd. and contributors which is licensed under the GNU LGPL License.  
Copyright © 2018 Qt Company Ltd.  
https://doc.qt.io/qt-6/lgpl.html

This project makes use of the Sphinx documentation generator, developed by Georg Brandl and contributors, which is licensed under a BSD license.  
Copyright © Georg Brandl and contributors  
https://github.com/sphinx-doc/sphinx/blob/master/LICENSE

This project makes use of PyInstaller from Hartmut Goebel and others, which is dual-licensed under **GPL 2.0** (with a special exception allowing commercial bundling) and **Apache 2.0** for some files.  
https://pyinstaller.org/en/stable/license.html

This project makes use of Inno Setup, by Jordan Russell and Martijn Laan, licensed under the *Inno Setup License*.  
Copyright © 1997–2025 Jordan Russell
Portions © 2000–2025 Martijn Laan  
https://github.com/jrsoftware/issrc/blob/HEAD/license.txt