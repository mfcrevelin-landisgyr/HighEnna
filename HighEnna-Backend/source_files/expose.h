#ifndef EXPOSE_H
#define EXPOSE_H

PYBIND11_MODULE(highennabackend, m) {
    m.def("parse", &parse, pybind11::arg("code"));
}

#endif // EXPOSE_H
