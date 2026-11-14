cmake_minimum_required(VERSION 3.20)
project(ArithmeticLoadPressure LANGUAGES CXX C)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
get_filename_component(VULSIM_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
add_subdirectory("${VULSIM_ROOT}/rtlzz" rtlzz)
add_executable(arithmetic-load-pressure-test
    "${VULSIM_ROOT}/rtlzz/testv2/arithmetic_load_pressure_test.cpp")
target_link_libraries(arithmetic-load-pressure-test PRIVATE predicate-expand-objects)
