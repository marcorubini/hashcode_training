cmake_minimum_required(VERSION 3.15)
project("HashcodeTraining")

add_subdirectory(src/checkers)

add_custom_target(book_scanning_files ALL
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/contest/book_scanning ${CMAKE_BINARY_DIR}/contest/book_scanning)
add_custom_target(book_scanning_checker ALL
  COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/src/checkers/book_scanning.out ${CMAKE_BINARY_DIR}/contest/book_scanning/check/checker
  DEPENDS book_scanning.out)

add_custom_target(more_pizza_files ALL
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/contest/more_pizza ${CMAKE_BINARY_DIR}/contest/more_pizza )
add_custom_target(more_pizza_checker ALL
  COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/src/checkers/more_pizza.out ${CMAKE_BINARY_DIR}/contest/more_pizza/check/checker
  DEPENDS more_pizza.out)

add_custom_target(even_more_pizza_files ALL
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/contest/even_more_pizza ${CMAKE_BINARY_DIR}/contest/even_more_pizza )
add_custom_target(even_more_pizza_checker ALL
  COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/src/checkers/even_more_pizza.out ${CMAKE_BINARY_DIR}/contest/even_more_pizza/check/checker
  DEPENDS even_more_pizza.out)

add_custom_target(contest_conf ALL
  COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_SOURCE_DIR}/contest/contest.yaml ${CMAKE_BINARY_DIR}/contest/contest.yaml)

