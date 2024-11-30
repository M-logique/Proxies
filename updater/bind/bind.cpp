#include <pybind11/pybind11.h>
#include <string>
using namespace std;

namespace py = pybind11;

/*
This Python module interfaces with Go functions via C bindings.
It allows Python programs to call Go code that performs resource-fetching and other operations.
*/


extern "C" {
    char* FetchResources();
    char* FetchTGChannels(const char* data);
}

string fetch_resources() {
    char* result = FetchResources();
    string resources(result);
    free(result); 
    return resources;
}

string fetch_tg_channels(const string& data) {
    char* result = FetchTGChannels(data.c_str());
    string channels(result);
    free(result); 
    return channels;
}

PYBIND11_MODULE(resources, m) {
    m.doc() = "Python bindings for resource-fetching operations";
    

    m.def("fetch_resources", &fetch_resources, "Fetches resources and returns them as a JSON string.");
    m.def("fetch_tg_channels", &fetch_tg_channels, py::arg("data"), "Fetches Telegram channels using input data.");
}
