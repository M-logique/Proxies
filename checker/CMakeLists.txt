cmake_minimum_required(VERSION 3.12)
project(ProxiesBindings)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(proxies MODULE ${CMAKE_SOURCE_DIR}/bind/bind.cpp)


target_include_directories(proxies PRIVATE ${Python3_INCLUDE_DIRS})
target_link_libraries(proxies PRIVATE pybind11::module)
target_link_libraries(proxies PRIVATE ${CMAKE_SOURCE_DIR}/checker.a)


# Setting output
set_target_properties(proxies PROPERTIES
    PREFIX ""                                # Remove .lib prefix
    OUTPUT_NAME "proxies"                    # output file name
)

# Output dir
set_target_properties(proxies PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}  
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}  
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}  
)