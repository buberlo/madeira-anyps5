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

# The upstream Windows alias regression reads/writes synthetic ELF/PE only.
# Keep its production reader/writer and exact assertions available on this host.
if(NOT TARGET windows_guest_export_alias_tests)
    set(nativeAliasSources
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/guest/GuestImageReader.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/parsing/ElfReader.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsGuestModuleWriter.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsLoadImage.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsTlsBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsPeWriter.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsRelocationBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsTrampolineBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsGuestLifecycleBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsStubEmitter.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsPeFormat.cpp"
        "${ANYPS5_SOURCE}/core/relinker/io/src/BufferUtils.cpp"
        "${ANYPS5_SOURCE}/core/relinker/codegen/src/x86/StubBodyBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/CodeInstructionCollector.cpp"
        "${ANYPS5_SOURCE}/core/relinker/codegen/src/x86/X64InstructionDecoder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/UnusedNidFilter/EhFrameReader.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/UnusedNidFilter/EntryPointCollector.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/UnusedNidFilter/StrictReachability.cpp"
        "${ANYPS5_SOURCE}/core/relinker/codegen/src/x86/DecodedInstruction.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/UnusedNidFilter/ControlFlowGraph.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsImportBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/elfpatcher/src/windows/WindowsTlsTemplateBuilder.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/CallSiteResolver.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/UnusedNidFilter/GotAccessIndex.cpp"
        "${ANYPS5_SOURCE}/core/relinker/relinker/src/analysis/UnusedNidFilter/RelativeRelocationIndex.cpp"
        "${ANYPS5_SOURCE}/core/relinker/codegen/src/InstructionScanner.cpp"
    )
    add_executable(windows_guest_export_alias_tests
        "${ANYPS5_SOURCE}/core/relinker/relinker/tests/WindowsExportAliasTests.cpp"
        ${nativeAliasSources})
    get_target_property(nativeAliasIncludes relinker INCLUDE_DIRECTORIES)
    target_include_directories(windows_guest_export_alias_tests PRIVATE ${nativeAliasIncludes})
    add_test(NAME windows_guest_export_aliases COMMAND windows_guest_export_alias_tests)
    set_tests_properties(windows_guest_export_aliases PROPERTIES TIMEOUT 30)
endif()
