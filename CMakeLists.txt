cmake_minimum_required(VERSION 3.15)
project("HashcodeTraining")

add_subdirectory(src/checkers)

add_custom_target(book_scanning_files ALL
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/problems/book_scanning ${CMAKE_BINARY_DIR}/problems/book_scanning)
add_custom_target(book_scanning_checker ALL
  COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/src/checkers/book_scanning.out ${CMAKE_BINARY_DIR}/problems/book_scanning/book_scanning/check/checker
  DEPENDS book_scanning.out)

