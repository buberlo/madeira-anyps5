cmake_minimum_required(VERSION 3.20)
project(AnyPS5NativeHostTools LANGUAGES CXX)

# This harness only includes portable conversion-tool source and regressions.
# Supply ANYPS5_SOURCE explicitly; no private paths or game data are embedded.
if(NOT ANYPS5_SOURCE OR NOT EXISTS "${ANYPS5_SOURCE}/CMakeLists.txt")
    message(FATAL_ERROR "ANYPS5_SOURCE must name an existing AnyPS5 source tree")
endif()
if(NOT APPLE)
    message(FATAL_ERROR "This experimental harness is scoped to native macOS tools")
endif()

set(BUILD_TESTING ON CACHE BOOL "Build all portable regression tests" FORCE)
set(ANYPS5_RELINKER_ONLY ON CACHE BOOL "Exclude runtime and vendor builds" FORCE)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_testing()
find_package(Python3 REQUIRED COMPONENTS Interpreter)

# Full upstream supplies this helper through core/libs. Native Mach-O host
# fixtures have no Windows .eh_frame section and require no transformation.
function(configure_windows_unwind target)
endfunction()

add_subdirectory("${ANYPS5_SOURCE}" anyps5)

add_executable(nid_patcher
    "${ANYPS5_SOURCE}/core/libs/nid/src/Sha1.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/NidCompute.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/NidResolver.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/ExportExclusions.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/ElfNidPatcher.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/PeNidPatcher.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/MachONidPatcher.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/BinaryPatcherFactory.cpp"
    "${ANYPS5_SOURCE}/core/libs/nid/src/main.cpp")
target_include_directories(nid_patcher PRIVATE "${ANYPS5_SOURCE}/core/libs/nid/include")
target_compile_features(nid_patcher PRIVATE cxx_std_20)
add_test(NAME nid_patcher_macho COMMAND "${Python3_EXECUTABLE}"
    "${ANYPS5_SOURCE}/core/libs/nid/tests/test_macho_nids.py" "$<TARGET_FILE:nid_patcher>")
add_test(NAME nid_patcher_symbol_versions COMMAND "${Python3_EXECUTABLE}"
    "${ANYPS5_SOURCE}/core/libs/nid/tests/test_symbol_versions.py" "$<TARGET_FILE:nid_patcher>")
