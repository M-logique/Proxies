cmake_minimum_required(VERSION 3.12)
project(ResourceBindings)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(resources MODULE ${CMAKE_SOURCE_DIR}/bind/bind.cpp)


target_include_directories(resources PRIVATE ${Python3_INCLUDE_DIRS})
target_link_libraries(resources PRIVATE pybind11::module)
target_link_libraries(resources PRIVATE ${CMAKE_SOURCE_DIR}/updater.a)

# Finding python SOABI for the name of the output
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_config_var('SOABI'))"
    OUTPUT_VARIABLE PYTHON_SOABI
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Setting output
set_target_properties(resources PROPERTIES
    PREFIX ""                                # Remove .lib prefix
    SUFFIX ".${PYTHON_SOABI}.so"             # using python SOABI
    OUTPUT_NAME "resources"                  #filename
)

# Output dir
set_target_properties(resources PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}  
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}  
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}  
)