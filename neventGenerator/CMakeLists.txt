cmake_minimum_required (VERSION 2.8)
set(PROJECT_NAME_STR neventGenerator)
project(${PROJECT_NAME_STR} CXX)

set(CMAKE_CXX_STANDARD 11)

set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${PROJECT_SOURCE_DIR}/cmake")

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU")
  if (CMAKE_CXX_COMPILER_VERSION VERSION_LESS "4.9.0")
    message(FATAL_ERROR "GCC below 4.9.0 does not fully support c++11.")
  endif()
endif()

if (CMAKE_CXX_COMPILER_VERSION VERSION_LESS "4.9.3")
else ()
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fdiagnostics-color=auto")
endif()

SET(CONAN_PROFILE "default" CACHE STRING "Name of conan profile to use, uses default by default")
SET(CONAN "AUTO" CACHE STRING "conan options AUTO (conan must be in path), MANUAL (expects conanbuildinfo.cmake in build directory) or DISABLE")

if(${CONAN} MATCHES "AUTO")
  include(${CMAKE_MODULE_PATH}/conan.cmake)
  conan_cmake_run(CONANFILE conan/conanfile.txt
          PROFILE ${CONAN_PROFILE}
          BASIC_SETUP ${OUTPUT_DIRS} SKIP_RPATH
          BUILD_TYPE "None"
          BUILD outdated)
elseif(${CONAN} MATCHES "MANUAL")
  if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
    include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
    conan_basic_setup(${OUTPUT_DIRS} SKIP_RPATH
            )
  else()
    MESSAGE(FATAL_ERROR "CONAN set to MANUAL but no file named conanbuildinfo.cmake found in build directory")
  endif()
elseif(NOT ${CONAN} MATCHES "DISABLE")
  MESSAGE(FATAL_ERROR "Unrecognised option for CONAN, use AUTO, MANUAL or DISABLE")
endif()

set (CMAKE_CXX_FLAGS "-std=c++11 -D_GLIBCXX_USE_NANOSLEEP ${CMAKE_CXX_FLAGS}")
set (CMAKE_CXX_FLAGS_DEBUG "-Wall -O0 -ggdb ${CMAKE_CXX_FLAGS}")
set (CMAKE_CXX_FLAGS_RELEASE "-O3 -g0 ${CMAKE_CXX_FLAGS}")

add_custom_target(
  extern_lib
  COMMAND make
)

find_package(RdKafka REQUIRED)
find_package(Flatbuffers REQUIRED)
find_package(HDF5 REQUIRED)
find_package(StreamingDataTypes COMPONENTS 2246f84b16423b7ac18e901bf4c43a006fe635dc REQUIRED)
find_package(Googletest)

option(HAVE_ZMQ "Enable 0MQ" FALSE)
if(${HAVE_ZMQ})
find_package(ZMQ REQUIRED)
else()
  message(STATUS "Build without 0MQ support")
endif()

include_directories(
  ${RDKAFKA_INCLUDE_DIR}
  ${FLATBUFFERS_INCLUDE_DIR}
  ${RAPIDJSON_INCLUDE_DIR}
  ${HDF5_INCLUDE_DIR}
  ${ZMQ_INCLUDE_DIR}
  ${CMAKE_CURRENT_BINARY_DIR}
  )

set(libraries_common
${RDKAFKA_LIBRARIES}
${HDF5_LIBRARIES}
${ZMQ_LIBRARIES}
${CURL_LIBRARIES}
pthread
z
)

set(tgt "nevent-generator__objects")
add_library(${tgt} OBJECT
Configuration.cxx
Errors.cxx
)

foreach(tgt AMORgenerator AMORreceiver FOCUSgenerator FOCUSreceiver)
  set(sources
    ${tgt}.cxx
    $<TARGET_OBJECTS:nevent-generator__objects>
    )
  add_executable(${tgt} ${sources})
  target_link_libraries(${tgt} ${libraries_common})
  add_dependencies(${tgt} flatbuffers_generate)
endforeach()


if(NOT ${CMAKE_INSTALL_PREFIX} EQUAL "")
  message(STATUS "Files will be installed in : " ${CMAKE_INSTALL_PREFIX})
  install(TARGETS AMORgenerator RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX})
  install(FILES config.json DESTINATION ${CMAKE_INSTALL_PREFIX})
  install(FILES files/amor2015n001774.hdf DESTINATION ${CMAKE_INSTALL_PREFIX}/files)
else()
  install(TARGETS AMORgenerator RUNTIME DESTINATION /opt/amor/simfiles)
  install(FILES config.json DESTINATION ${CMAKE_INSTALL_PREFIX})
  install(FILES files/amor2015n001774.hdf DESTINATION ${CMAKE_INSTALL_PREFIX}/files)
endif()

if (have_gtest)
add_subdirectory(tests)
endif()
