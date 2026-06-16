cmake_minimum_required(VERSION 3.16)
project(hackathon_drift_coordinator CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)
find_package(Threads REQUIRED)

# ============================================================================
# 1. DEPENDENCY: NLOHMANN JSON (Check -> Fallback)
# ============================================================================
find_package(nlohmann_json QUIET)
if(NOT nlohmann_json_FOUND)
    message(STATUS "nlohmann_json not found locally. Fetching from GitHub...")
    FetchContent_Declare(
        json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG        v3.12.0
    )
    FetchContent_MakeAvailable(json)
endif()

# ============================================================================
# 2. DEPENDENCY: SPDLOG (Check -> Fallback)
# ============================================================================
find_package(spdlog QUIET)
if(NOT spdlog_FOUND)
    message(STATUS "spdlog not found locally. Fetching from GitHub...")
    FetchContent_Declare(
        spdlog
        GIT_REPOSITORY https://github.com/gabime/spdlog.git
        GIT_TAG        v1.12.0
    )
    FetchContent_MakeAvailable(spdlog)
endif()

# ============================================================================
# 3. DEPENDENCY: INTEL TBB (Check -> Fallback)
# ============================================================================
find_package(TBB QUIET)
if(NOT TBB_FOUND)
    message(STATUS "Intel TBB not found locally. Fetching from GitHub...")
    FetchContent_Declare(
        TBB
        GIT_REPOSITORY https://github.com/oneapi-src/oneTBB.git
        GIT_TAG        v2021.12.0
    )
    set(TBB_TEST OFF CACHE BOOL "" FORCE)
    set(TBB_STRICT OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(TBB)
endif()

# ============================================================================
# 4. DEPENDENCY: DROGON FRAMEWORK (Check -> Fallback)
# ============================================================================
find_package(Drogon QUIET)
if(NOT Drogon_FOUND)
    message(STATUS "Drogon not found locally. Fetching from GitHub...")
    FetchContent_Declare(
        drogon
        GIT_REPOSITORY https://github.com/drogonframework/drogon.git
        GIT_TAG        v1.9.0
    )
    set(BUILD_POSTGRESQL OFF CACHE BOOL "" FORCE)
    set(BUILD_MYSQL OFF CACHE BOOL "" FORCE)
    set(BUILD_SQLITE OFF CACHE BOOL "" FORCE)
    set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(drogon)
endif()

# ============================================================================
# TARGET 1: THE CORE COORDINATOR EXECUTABLE
# ============================================================================
add_executable(${PROJECT_NAME} 
    main.cpp
    types.hpp
)

# Cross-platform namespacing linkage for Target 1
if(TARGET drogon::drogon)
    target_link_libraries(${PROJECT_NAME} PRIVATE drogon::drogon)
else()
    target_link_libraries(${PROJECT_NAME} PRIVATE Drogon::Drogon)
endif()

if(TARGET TBB::tbb)
    target_link_libraries(${PROJECT_NAME} PRIVATE TBB::tbb)
else()
    target_link_libraries(${PROJECT_NAME} PRIVATE tbb)
endif()

target_link_libraries(${PROJECT_NAME} PRIVATE
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    Threads::Threads
)

# ============================================================================
# TARGET 2: MOCK TEST SERVER EXECUTABLE
# ============================================================================
add_executable(mock_agent_server 
    mock_server.cpp
)

# Cross-platform namespacing linkage for Target 2
if(TARGET drogon::drogon)
    target_link_libraries(mock_agent_server PRIVATE drogon::drogon)
else()
    target_link_libraries(mock_agent_server PRIVATE Drogon::Drogon)
endif()

target_link_libraries(mock_agent_server PRIVATE
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    Threads::Threads
)

# ============================================================================
# CROSS-PLATFORM COMPILER DEFINITIONS
# ============================================================================
if(WIN32)
    target_compile_definitions(${PROJECT_NAME} PRIVATE WIN32_LEAN_AND_MEAN)
    target_compile_definitions(mock_agent_server PRIVATE WIN32_LEAN_AND_MEAN)
endif()
