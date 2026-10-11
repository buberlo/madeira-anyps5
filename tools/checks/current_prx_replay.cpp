#include "ControlFlow/RequestSerializer.hpp"
#include "Optimization/ResourceProgram.hpp"
#include "Optimization/RequestMemoryView.hpp"
#include "ShaderDiskCache.hpp"
#include "ShaderCacheVersion.hpp"
#include <cstring>
#include <windows.h>
#include <cstdio>
#include <fstream>
#include <filesystem>
#include <iterator>
#include <iostream>
#include <stdexcept>
using namespace ShaderRecompiler;
template<class T> void numbers(std::ostream& stream, const T& values) {
 stream << '[';
 for (std::size_t n=0; n<values.size(); ++n) { if(n) stream << ','; stream << +values[n]; }
 stream << ']';
}
void dump(const RecompileRequest& request, const RecompileResult& result, const std::filesystem::path& directory) {
 std::filesystem::create_directories(directory);
 const auto spirvPath=directory/"materialized.spv", bindingPath=directory/"binding-layout.json";
 if(std::filesystem::exists(spirvPath)||std::filesystem::exists(bindingPath))
  throw std::runtime_error("Dump destination already contains artifacts");
 const auto& words=result.spirv.Words();
 std::ofstream spirv(spirvPath,std::ios::binary);
 spirv.write(reinterpret_cast<const char*>(words.data()),static_cast<std::streamsize>(words.size()*sizeof(std::uint32_t)));
 spirv.flush(); if(!spirv) throw std::runtime_error("Writing actual materialized SPIR-V failed");
 std::ofstream output(bindingPath); output << std::boolalpha;
 output << "{\n\"schema\":2,\"scope\":\"actual_imported_prx_cpu_materialization_not_gpu_execution\","
        << "\"variantId\":" << result.variantId << ",\"specializationId\":" << result.specializationId
        << ",\"spirvWordCount\":" << words.size() << ",\"hostSubgroupSize\":" << result.hostSubgroupSize
        << ",\"targetVulkanVersion\":" << request.target.vulkanVersion << ",\"targetSpirvVersion\":" << request.target.spirvVersion
        << ",\"layout\":{\"descriptorSet\":" << request.layout.descriptorSet << ",\"firstBinding\":" << request.layout.firstBinding
        << ",\"pushConstantOffsetBytes\":" << request.layout.pushConstantOffsetBytes << ",\"pushConstantSizeBytes\":" << request.layout.pushConstantSizeBytes << "},\"bindings\":[";
 for(std::size_t n=0;n<result.bindings.size();++n) {
  const auto& b=result.bindings[n]; if(n) output << ',';
  output << "{\"kind\":" << unsigned(b.kind) << ",\"role\":" << unsigned(b.role)
         << ",\"descriptorSet\":" << b.descriptorSet << ",\"binding\":" << b.binding << ",\"count\":" << b.count
         << ",\"readOnly\":" << b.readOnly << ",\"imageShape\":";
  if(b.imageShape) output << unsigned(*b.imageShape); else output << "null";
  output << ",\"guestDescriptor\":"; numbers(output,b.guestDescriptor);
  output << ",\"samplerDepthCompare\":"; numbers(output,b.samplerDepthCompare);
  output << ",\"imageWritten\":"; numbers(output,b.imageWritten);
  output << ",\"imageDepthCompare\":"; numbers(output,b.imageDepthCompare);
  output << ",\"imageAtomic\":"; numbers(output,b.imageAtomic);
  output << ",\"imageAtomic64\":"; numbers(output,b.imageAtomic64);
  output << ",\"bufferAtomic\":"; numbers(output,b.bufferAtomic);
  output << ",\"bufferWritten\":"; numbers(output,b.bufferWritten);
  output << ",\"bufferRead\":"; numbers(output,b.bufferRead);
  output << ",\"samplerIntegerBorder\":"; numbers(output,b.samplerIntegerBorder);
  output << ",\"samplerUnnormalized\":"; numbers(output,b.samplerUnnormalized);
  output << ",\"imageUnnormalizedBaseLevel\":"; numbers(output,b.imageUnnormalizedBaseLevel);
  output << ",\"imageUnnormalized\":"; numbers(output,b.imageUnnormalized);
  output << ",\"imageSamplers\":"; numbers(output,b.imageSamplers);
  output << ",\"imageLogicalSamples\":"; numbers(output,b.imageLogicalSamples);
  output << ",\"imageNativeSamples\":"; numbers(output,b.imageNativeSamples); output << '}';
 }
 output << "],\"fragmentParameters\":[";
 for(std::size_t n=0;n<result.fragmentParameters.size();++n) {
  const auto& p=result.fragmentParameters[n];if(n)output<<',';
  output << "{\"location\":" << p.location << ",\"sourceLocation\":" << p.sourceLocation << ",\"flat\":" << p.flat
         << ",\"perVertex\":" << p.perVertex << ",\"custom\":" << p.custom << '}';
 }
 output << "],\"specialization\":[";
 for(std::size_t n=0;n<result.specialization.size();++n) {
  const auto& s=result.specialization[n];if(n)output<<',';output<<"{\"id\":"<<s.id<<",\"value\":"<<s.value<<'}';
 }
 output << "],\"pushConstantBytes\":[";
 for(std::size_t n=0;n<result.pushConstants.size();++n) {if(n)output<<',';output<<std::to_integer<unsigned>(result.pushConstants[n]);}
 output << "]}\n"; output.flush();if(!output)throw std::runtime_error("Writing binding layout failed");
 std::cout << "ACTUAL_MATERIALIZED_SPIRV_AND_BINDINGS_DUMPED 1\n";
}
int main(int argc, char** argv) {
 try {
  if (argc != 5) throw std::runtime_error("Expected PRX, frozen full request, fresh dump directory and explicit request origin required");
  const bool legacy = std::strcmp(argv[4], "--legacy-ipad-v14-v15") == 0;
  if (!legacy && std::strcmp(argv[4], "--request17") != 0) throw std::runtime_error("Explicit request17 or legacy iPad14/15 origin required");
  if (std::filesystem::exists(argv[3])) throw std::runtime_error("Fresh dump directory required");
  char path[32768]{};
  const auto module = GetModuleHandleW(L"libSceAgcDriver.prx");
  const auto count = module ? GetModuleFileNameA(module, path, sizeof(path)) : 0;
  if (!count || count >= sizeof(path) || std::strcmp(path, argv[1])) throw std::runtime_error("Actual driver identity rejected");
  if (ShaderDiskCache::FormatVersion != 28u || ShaderDiskCache::SourceVersion() != ShaderDiskCache::Generated::SourceVersion)
   throw std::runtime_error("Actual driver cache/source identity rejected");
  std::printf("ACTUAL_DRIVER_CACHE_SOURCE_VERSION %016llx\n", static_cast<unsigned long long>(ShaderDiskCache::SourceVersion()));
  std::printf("ACTUAL_DRIVER_CACHE_FORMAT %u\n", ShaderDiskCache::FormatVersion);
  std::cout << "ACTUAL_DRIVER_PATH " << path << '\n';
  std::ifstream file(argv[2], std::ios::binary);
  if (!file) throw std::runtime_error("Frozen request unavailable");
  std::string text((std::istreambuf_iterator<char>(file)), {});
  while (!text.empty() && (text.back() == '\r' || text.back() == '\n')) text.pop_back();
  auto deserialized = legacy ? RequestSerializer{}.DeserializeLegacyIpadV14V15(text) : RequestSerializer{}.Deserialize(text);
  const auto canonical = RequestSerializer{}.Serialize(deserialized.request);
  auto replayed = RequestSerializer{}.Deserialize(canonical);
  if (RequestSerializer{}.Serialize(replayed.request) != canonical)
   throw std::runtime_error("Full request canonical roundtrip differs");
  if (!legacy && canonical != text) throw std::runtime_error("Declared request17 is not canonical current serialization");
  // Migration writes only a fresh working copy; archived local14/15 stay exact.
  std::cout << "FULL_REQUEST_ORIGIN " << (legacy ? "legacy-ipad-v14-v15" : "request17") << '\n'
            << "FULL_REQUEST_CANONICAL_SERIALIZATION_VERSION 17\n";
  std::cout << "FULL_REQUEST_CANONICAL_ROUNDTRIP_MATCH 1\n"
            << "FULL_REQUEST_ORIGINAL_SERIALIZATION_MATCH " << (canonical == text) << '\n';
  const auto& request = deserialized.request;
  std::cout << "FULL_REQUEST_METADATA codeWords=" << request.shader.code.size()
            << " memoryRegions=" << request.context.memory.size()
            << " userDataWords=" << request.context.userData.size() << '\n';
  // These functions must be imported from the newly linked production PRX.
  // No shader implementation archive or inline admission proof is linked here.
  const auto prepared = PrepareShader(request);
  if (!prepared) throw std::runtime_error("No actual prepared shader handle");
  const auto& artifact = GetPreparedArtifact(*prepared);
  if (artifact.spirv.Words().empty()) throw std::runtime_error("Empty prepared artifact");
  RequestMemoryView memory(request.context.memory);
  auto runtime = memory.MakeRuntime(request.context.userData, request.shader.codeAddress);
  const auto capture = CaptureResources(request, runtime, *prepared);
  if (!capture) throw std::runtime_error("No resource capture");
  const auto materialized = MaterializeShader(request, *capture, *prepared);
  if (!materialized || materialized->spirv.Words().empty())
   throw std::runtime_error("Empty materialized shader");
  if (artifact.variantId == 0 || materialized->variantId != artifact.variantId)
   throw std::runtime_error("Prepared artifact identity changed");
  dump(request,*materialized,std::filesystem::path(argv[3]));
  std::ofstream migrated(std::filesystem::path(argv[3]) / "canonical-v17.req", std::ios::binary);
  migrated << canonical << '\n'; migrated.flush();
  if (!migrated) throw std::runtime_error("Canonical request17 working-copy write failed");
  std::cout << "ACTUAL_DRIVER_FULL_PREPARE_CAPTURE_MATERIALIZE_PASS words="
            << materialized->spirv.Words().size() << " variant=" << artifact.variantId << '\n';
  return 0;
 } catch (const std::exception& error) {
  std::cerr << "FULL_REQUEST_REPLAY_FAILURE " << error.what() << '\n';
  return 1;
 }
}
