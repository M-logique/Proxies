#include <pybind11/pybind11.h>
#include <string>
#include "updater.h"
using namespace std;

namespace py = pybind11;


string fetch_resources() {
    char* result = FetchResources();
    string resources(result);
    free(result); 
    return resources;
}


string fetch_tg_channels(const string& data) {
    char* result = FetchTGChannels(const_cast<char*>(data.c_str()));
    string channels(result);
    free(result); 
    return channels;
}


PYBIND11_MODULE(resources, m) {
    m.doc() = "Python bindings for resource-fetching functions";

    m.def("fetch_resources", &fetch_resources, "Fetches resources and returns them as a JSON string");
    m.def("fetch_tg_channels", &fetch_tg_channels, py::arg("data"), "Fetches Telegram channels using input data");
}