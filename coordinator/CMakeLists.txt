cmake_minimum_required(VERSION 3.16)
project(hackathon_drift_coordinator CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Aggressively ignore warnings to fix C-ares deprecated call errors
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -Wno-deprecated-declarations" CACHE STRING "" FORCE)

include(FetchContent)
find_package(Threads REQUIRED)

# Dependencies
find_package(nlohmann_json QUIET)
if(NOT nlohmann_json_FOUND)
    FetchContent_Declare(json GIT_REPOSITORY https://github.com/nlohmann/json.git GIT_TAG v3.12.0)
    FetchContent_MakeAvailable(json)
endif()

find_package(spdlog QUIET)
if(NOT spdlog_FOUND)
    FetchContent_Declare(spdlog GIT_REPOSITORY https://github.com/gabime/spdlog.git GIT_TAG v1.12.0)
    FetchContent_MakeAvailable(spdlog)
endif()

find_package(TBB QUIET)
if(NOT TBB_FOUND)
    FetchContent_Declare(TBB GIT_REPOSITORY https://github.com/oneapi-src/oneTBB.git GIT_TAG v2021.12.0)
    set(TBB_TEST OFF CACHE BOOL "" FORCE)
    set(TBB_STRICT OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(TBB)
endif()

# Drogon/Trantor
set(BUILD_POSTGRESQL OFF CACHE BOOL "" FORCE)
set(BUILD_MYSQL OFF CACHE BOOL "" FORCE)
set(BUILD_SQLITE OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)

find_package(Drogon QUIET)
if(NOT Drogon_FOUND)
    FetchContent_Declare(drogon GIT_REPOSITORY https://github.com/drogonframework/drogon.git GIT_TAG v1.9.0)
    FetchContent_MakeAvailable(drogon)
endif()

macro(link_drogon TARGET_NAME)
    if(TARGET Drogon::Drogon)
        target_link_libraries(${TARGET_NAME} PRIVATE Drogon::Drogon)
    elseif(TARGET drogon)
        target_link_libraries(${TARGET_NAME} PRIVATE drogon)
    elseif(TARGET drogon::drogon)
        target_link_libraries(${TARGET_NAME} PRIVATE drogon::drogon)
    else()
        message(FATAL_ERROR "No Drogon target found. Install drogon or check FetchContent.")
    endif()
endmacro()

# TARGET 1
add_executable(${PROJECT_NAME} main.cpp types.hpp)
link_drogon(${PROJECT_NAME})
target_link_libraries(${PROJECT_NAME} PRIVATE spdlog::spdlog nlohmann_json::nlohmann_json Threads::Threads TBB::tbb)

# TARGET 2
add_executable(mock_agent_server mock_server.cpp)
link_drogon(mock_agent_server)
target_link_libraries(mock_agent_server PRIVATE spdlog::spdlog nlohmann_json::nlohmann_json Threads::Threads TBB::tbb)
