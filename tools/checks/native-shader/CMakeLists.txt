cmake_minimum_required(VERSION 3.20)
project(AnyPS5AppleGpuCpuChecks LANGUAGES CXX)

set(ANYPS5_SOURCE "" CACHE PATH "Complete, composed AnyPS5 source tree; used read-only")
if(NOT IS_DIRECTORY "${ANYPS5_SOURCE}/core/shader/recompiler")
    message(FATAL_ERROR "Pass -DANYPS5_SOURCE=<complete composed AnyPS5 source tree>")
endif()
if(NOT APPLE OR NOT CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")
    message(FATAL_ERROR "This recipe is for native ARM64 macOS CPU checks")
endif()
get_filename_component(ANYPS5_SOURCE "${ANYPS5_SOURCE}" REALPATH)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(ANYPS5_ENABLE_SPIRV_TOOLS OFF)
set(AGC "${ANYPS5_SOURCE}/core/libs/prx/libSceAgcDriver")

# add_shader_recompiler uses this variable to locate existing third-party trees
# and its production cache source-identity inputs. No source trees are copied.
set(PROJECT_SOURCE_DIR "${ANYPS5_SOURCE}")
find_package(Threads REQUIRED)
add_library(host_runtime INTERFACE)
target_include_directories(host_runtime INTERFACE
    "${ANYPS5_SOURCE}/core/libs/prx/libc/include")
target_link_libraries(host_runtime INTERFACE Threads::Threads)

add_compile_definitions(APS5_ENABLE_TIMING_LOG=0)
add_compile_options(-Wno-return-type-c-linkage)
add_subdirectory("${ANYPS5_SOURCE}/core/shader/recompiler" recompiler)

# Preserve the production driver source guard in the native cache identity.
file(GLOB_RECURSE agc_guard_sources CONFIGURE_DEPENDS
    "${AGC}/*.cpp" "${AGC}/*.hpp" "${AGC}/*.h")
list(FILTER agc_guard_sources EXCLUDE REGEX "/(tests|tools)/")
add_shader_recompiler(shader_recompiler host_runtime
    GUARD_SOURCES ${agc_guard_sources})

function(cpu_check target)
    add_executable(${target} ${ARGN})
    target_include_directories(${target} PRIVATE
        "${ANYPS5_SOURCE}/core/libs"
        "${ANYPS5_SOURCE}/3rdparty/Vulkan-Headers/include")
    target_compile_options(${target} PRIVATE -UNDEBUG)
    target_link_libraries(${target} PRIVATE shader_recompiler)
endfunction()

cpu_check(agc_placeholder_images_tests "${AGC}/tests/PlaceholderImages.cpp")
cpu_check(agc_shader_device_profile_tests
    "${AGC}/tests/ShaderDeviceProfile.cpp"
    "${AGC}/Execution/src/ShaderDeviceProfile.cpp")
cpu_check(agc_shader_disk_cache_tests "${AGC}/tests/ShaderDiskCache.cpp")
cpu_check(agc_unused_barycentric_tests "${AGC}/tests/UnusedBarycentricProof.cpp")
cpu_check(agc_extended_public_tests "${CMAKE_CURRENT_SOURCE_DIR}/ExtendedPublicShaderCases.cpp")
target_include_directories(agc_extended_public_tests PRIVATE "${AGC}/tests")
cpu_check(agc_shader_replay "${AGC}/tools/ShaderReplay.cpp")
cpu_check(agc_lds_spill_cpu_tests "${CMAKE_CURRENT_SOURCE_DIR}/LdsSpillCpu.cpp")
target_include_directories(agc_lds_spill_cpu_tests PRIVATE "${AGC}/tests")
target_compile_definitions(agc_lds_spill_cpu_tests PRIVATE
    "APS5_LDS_EXECUTION_FIXTURE=\"${AGC}/tests/execution/LdsBeyondDeviceLimit.cpp\"")
target_compile_options(agc_lds_spill_cpu_tests PRIVATE -ffunction-sections -fdata-sections)
target_link_options(agc_lds_spill_cpu_tests PRIVATE "LINKER:-dead_strip")

enable_testing()
foreach(target IN ITEMS agc_placeholder_images_tests agc_shader_device_profile_tests
        agc_shader_disk_cache_tests agc_unused_barycentric_tests agc_lds_spill_cpu_tests agc_extended_public_tests)
    add_test(NAME ${target} COMMAND ${target})
    set_tests_properties(${target} PROPERTIES TIMEOUT 120)
endforeach()
set_tests_properties(agc_placeholder_images_tests agc_shader_device_profile_tests
    agc_unused_barycentric_tests agc_lds_spill_cpu_tests agc_extended_public_tests PROPERTIES ENVIRONMENT "ANYPS5_NO_SHADER_CACHE=1")

# ShaderReplay requires explicit private/synthetic .req paths, supplied by root;
# building it does not silently discover or run game diagnostics.
