cmake_minimum_required(VERSION 2.6)

project (test)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS "-Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

find_package(OpenCV REQUIRED)
find_package(cppzmq REQUIRED)

add_executable(opencv_test opencv_test.cpp)
target_link_libraries(opencv_test ${OpenCV_LIBS})
target_link_libraries(opencv_test cppzmq)
