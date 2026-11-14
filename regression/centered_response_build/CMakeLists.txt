cmake_minimum_required(VERSION 3.20)
project(ArithmeticCenteredResponse LANGUAGES CXX C)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
get_filename_component(VULSIM_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
add_subdirectory("${VULSIM_ROOT}/rtlzz" rtlzz)
add_executable(arithmetic-centered-response-test
    "${VULSIM_ROOT}/rtlzz/testv2/arithmetic_centered_response_test.cpp")
target_link_libraries(arithmetic-centered-response-test PRIVATE predicate-expand-objects)
