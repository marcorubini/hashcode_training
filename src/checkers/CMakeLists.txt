cmake_minimum_required(VERSION 3.15)
project("HashcodeCheckers")

add_library(compiler_options INTERFACE)
target_compile_features(compiler_options INTERFACE cxx_std_14)
target_link_libraries(compiler_options INTERFACE "-static")

add_executable(book_scanning.out "book_scanning.cpp")
target_link_libraries(book_scanning.out PRIVATE compiler_options)
