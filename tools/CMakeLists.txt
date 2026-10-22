cmake_minimum_required(VERSION 3.16)
project(Bo2PL CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release)
endif()

add_executable(Bo2Patcher patcher/Bo2Patcher.cpp)
if(MSVC)
  # Static runtime: the installer ships a single exe without the Visual C++ redistributable.
  set_property(TARGET Bo2Patcher PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
  target_compile_options(Bo2Patcher PRIVATE /W4)
else()
  target_compile_options(Bo2Patcher PRIVATE -Wall -Wextra)
endif()
