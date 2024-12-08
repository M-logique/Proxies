#include <pybind11/pybind11.h>
#include <string>
using namespace std;

namespace py = pybind11; // Alias for pybind11 namespace

/*
This C++ module provides Python bindings for interfacing with Go functions via C bindings.
It allows Python programs to call Go code for operations such as proxy processing.
*/

// Declaration of an external C function that is implemented in Go.
extern "C" {
    char* ProcessProxies(const char* jsonInput, const char* xrayCorePath);
}

// Wrapper function for `ProcessProxies` to work with C++ `std::string`.
string process_proxies(const string& json_input, const string& xray_core_file_path) {
    char* result = ProcessProxies(
        json_input.c_str(),
        xray_core_file_path.c_str()
    );

    string output(result); // Convert C-style string to C++ string.
    free(result); // Free the memory allocated by the Go function.

    return output;
}

PYBIND11_MODULE(resources, m) {
    m.doc() = "Python bindings for Go functions that perform proxy processing operations.";

    // Define the `process_proxies` function in the Python module.
    m.def(
        "process_proxies",
        &process_proxies,
        py::arg("json_input"),
        py::arg("xray_core_file_path"),
        R"pbdoc(
        Processes proxy configurations using the provided JSON input and Xray Core binary path.

        
        :param json_input: JSON string containing proxy configurations.
        :type input_json: str
        :param xray_core_file_path: Path to the Xray Core executable.
        :type xray_cre_file_path: str

        
        :return: Output string after processing the proxies.
        :rtype str:
        )pbdoc"
    );
}
