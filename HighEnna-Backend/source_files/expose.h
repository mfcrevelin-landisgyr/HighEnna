#ifndef EXPOSE_H
#define EXPOSE_H

PYBIND11_MODULE(highennabackend, m) {
    m.def("parse" , &parse , py::arg("code"));
    m.def("encode", &encode, py::arg("code"));
    m.def("decode", &decode, py::arg("code"));
}

#endif // EXPOSE_H
