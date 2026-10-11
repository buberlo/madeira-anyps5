#include "prx/libSceAgcDriver/Execution/include/Driver/Draw/DrawCache.hpp"
#include "prx/libSceAgcDriver/Execution/include/Driver/Shaders/ShaderRegistry.hpp"
#include "prx/libSceAgcDriver/Graphics/include/ShaderInputState.hpp"
#include "Optimization/ResourceProgram.hpp"
#include "CompiledVariant.hpp"
#include "ShaderDiskCache.hpp"
#include "ShaderCacheVersion.hpp"
#include "SceShaders.hpp"
#include <spirv/unified1/spirv.hpp>
#include <windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

// This deliberately uses the loaded production DLL's decoder, preparer,
// invocation, resource capture and materializer. It creates no Vulkan device.
// Shader registration is a synthetic snapshot; Driver::RegisterShader and
// PrepareNullPixelProgram(VulkanDevice) are qualified separately on a GPU.
namespace {
using namespace ShaderRecompiler;
using namespace AgcDriver::DriverDetail;
void require(bool value, const char* message) { if (!value) throw std::runtime_error(message); }
unsigned passed = 0;
void pass(const std::string& name) { std::cout << "PASS " << name << '\n'; ++passed; }
template<class Action> void rejected(Action action, const char* reason) {
    try { action(); } catch (const std::exception& error) {
        require(std::string(error.what()).find(reason) != std::string::npos, error.what()); return;
    }
    throw std::runtime_error("invalid null-pixel state was accepted");
}

struct Fixture {
    struct Header { Shader shader{}; ShaderUserData users{}; } header;
    alignas(256) std::array<std::uint32_t, 65> code{};
    std::shared_ptr<ShaderSnapshot> snapshot;
    Fixture() {
        header.shader.type = 2u; header.shader.user_data = &header.users;
        code.fill(0xffffffffu); code.back() = 0xbf810000u;
        snapshot = std::make_shared<ShaderSnapshot>();
        snapshot->type = 2u; snapshot->codeAddress = reinterpret_cast<std::uintptr_t>(code.data());
        snapshot->headerAddress = reinterpret_cast<std::uintptr_t>(&header);
        snapshot->code.assign(code.begin(), code.end());
        snapshot->header.resize(sizeof(header)); std::memcpy(snapshot->header.data(), &header, sizeof(header));
    }
    void bind(AgcDriver::QueueState& queue) const {
        const auto address = snapshot->codeAddress + 256u;
        queue.shader[0xc8u] = static_cast<std::uint32_t>(address >> 8u);
        queue.shader[0xc9u] = static_cast<std::uint32_t>(address >> 40u);
        queue.shader[0x8bu] = 0u;
    }
};

std::shared_ptr<ShaderSnapshot> builtinNull() {
    const auto address = NullPixelProgramAddress();
    require(address != 0u, "production builtin null-pixel address is absent");
    const auto* words = reinterpret_cast<const std::uint32_t*>(address);
    require(words[0] == 0xbf810000u && std::all_of(words + 1, words + 64, [](auto word) { return word == 0u; }),
            "production null-pixel code is not the registered s_endpgm program");
    Shader shader{}; shader.file_header = 0x34333231u; shader.version = 0x18u;
    shader.code = words; shader.header_size = sizeof(Shader); shader.shader_size = 64u * sizeof(std::uint32_t); shader.type = 1u;
    auto snapshot = std::make_shared<ShaderSnapshot>();
    snapshot->type = 1u; snapshot->codeAddress = address;
    snapshot->code.assign(words, words + 64); snapshot->header.resize(sizeof(Shader));
    std::memcpy(snapshot->header.data(), &shader, sizeof(shader));
    snapshot->headerAddress = reinterpret_cast<std::uintptr_t>(snapshot->header.data());
    return snapshot;
}

SpirvTarget target() {
    static const std::array<std::uint32_t, 1> capabilities{spv::CapabilityShader};
    SpirvTarget value{}; value.vulkanVersion = 0x00401000u; value.spirvVersion = 0x00010300u;
    value.subgroupSize = 64u; value.supportedCapabilities = capabilities;
    return value;
}

void materialize(const RecompileRequest& request, const SourceHandle& handle) {
    const auto& artifact = GetPreparedArtifact(handle);
    SrtRuntime runtime{}; runtime.userData = request.context.userData;
    const auto capture = CaptureResources(request, runtime, handle);
    require(capture != nullptr, "actual null-pixel capture is absent");
    const auto result = MaterializeShader(request, *capture, handle);
    require(result && result->variantId != 0u && result->variantId == artifact.variantId,
            "actual null-pixel materialization changed its prepared artifact");
    const auto& words = result->spirv.Words();
    require(words.size() >= 5u && words[0] == 0x07230203u && words[1] == request.target.spirvVersion,
            "actual materializer did not emit a SPIR-V module");
    bool fragmentEntry = false;
    for (std::size_t offset = 5u; offset < words.size();) {
        const auto count = words[offset] >> 16u; const auto opcode = words[offset] & 0xffffu;
        require(count != 0u && count <= words.size() - offset, "materialized SPIR-V is truncated");
        if (opcode == spv::OpEntryPoint && count >= 4u && words[offset + 1u] == spv::ExecutionModelFragment) fragmentEntry = true;
        require(!(opcode == spv::OpVariable && count >= 4u && words[offset + 3u] == spv::StorageClassOutput),
                "null-pixel materialization inherited a color/depth/sample output");
        offset += count;
    }
    require(fragmentEntry && result->fragmentParameters.empty(), "null pixel inherited fragment inputs or lost its stage");
    for (const auto& binding : result->bindings)
        require(binding.role != DescriptorRole::GuestImages && binding.role != DescriptorRole::GuestSamplers &&
                binding.role != DescriptorRole::GuestBuffers, "null-pixel materialization inherited guest resources");
    const auto repeated = MaterializeShader(request, *capture, handle);
    require(repeated->variantId == result->variantId && repeated->spirv.Words() == words,
            "repeated null-pixel materialization changed output");
}

AgcDriver::QueueState depthOnly(Fixture& front, unsigned addressMode) {
    AgcDriver::QueueState queue{}; front.bind(queue);
    queue.context[0x8eu] = 0u; queue.context[0x8fu] = 0xffffffffu;
    queue.context[0x200u] = 6u; queue.context[0x010u] = 3u; queue.context[0x011u] = 0u;
    // Stale pixel state must not leak into the fallback shader's static ABI.
    queue.shader[0xbu] = 0x0800003eu;
    for (unsigned n = 0; n < 32; ++n) queue.shader[0xcu + n] = 0xdeadc000u + n;
    queue.context[0x1b3u] = queue.context[0x1b4u] = 0xffffffffu;
    queue.context[0x1b6u] = 0x803fu; queue.context[0x1c5u] = 0x99999999u;
    if (addressMode == 0u) { queue.shader.erase(0x8u); queue.shader.erase(0x9u); }
    if (addressMode == 1u) { queue.shader[0x8u] = 0u; queue.shader[0x9u] = 0u; }
    if (addressMode == 2u) { queue.shader.erase(0x8u); queue.shader[0x9u] = 0u; }
    if (addressMode == 3u) { queue.shader[0x8u] = 0u; queue.shader.erase(0x9u); }
    return queue;
}

void staged(unsigned addressMode, unsigned wave) {
    Fixture front; auto null = builtinNull(); std::shared_ptr<ShaderRegistry> registry;
    PublishRegisteredShader(registry, front.snapshot); PublishRegisteredShader(registry, null);
    const auto queue = depthOnly(front, addressMode);
    require(AgcDriver::Graphics::PixelProgramSkipped(queue), "unwritten/zero PS was not selected as null");
    require(AgcDriver::Graphics::NullPixelProgramRejection(queue).empty(), "depth-only null PS was rejected");
    DrawDecode decoded{}; decoded.state.stages.path = AgcDriver::Graphics::ShaderPath::Vertex;
    decoded.state.stages.vertexWaveSize = 32u; decoded.state.stages.fragmentWaveSize = wave;
    std::array<std::uint8_t, 8> mappings{}; mappings.fill(0xe4u);
    decoded.pixel = AgcDriver::Graphics::DecodePixelStageInfo(queue.context, mappings, true);
    require(decoded.pixel.interpolatorCount == 0u && decoded.pixel.targetOutputMode == std::array<std::uint8_t, 8>{} &&
            decoded.pixel.targetExportMapping == std::array<std::uint8_t, 8>{}, "null pixel inherited old input/export ABI");
    DecodeGraphicsPrograms(decoded, queue, *registry, false, true);
    require(decoded.programs.size() == 2u && decoded.programs.back().snapshot == null && decoded.programs.back().userData.empty(),
            "draw decoder inherited old pixel SGPRs or selected another program");
    const auto stages = PrepareGraphicsStages(decoded, target());
    require(stages.size() == 2u, "actual prepared graphics stages are incomplete");
    std::vector<MemoryRegion> memory; std::vector<LinkedProgram> linked;
    for (std::size_t index = 0; index < decoded.programs.size(); ++index) {
        const auto& program = decoded.programs[index];
        memory.insert(memory.end(), program.memory.begin(), program.memory.end());
        linked.push_back({decoded.roles[index], program.binary, program.userDataBase, program.firstUserSgpr, program.userData});
    }
    const auto& fragment = decoded.programs.back();
    const auto offset = stages.front().entry.handle->artifact->bindings.pushConstantSizeBytes;
    RecompileRequest request{fragment.binary,
        {wave, fragment.firstUserSgpr, fragment.userData, {}, decoded.pixel, {}, memory, RegisteredFloatMode(*null)},
        target(), {0, 0, offset, AgcDriver::Graphics::PipelinePushConstantBytes - offset},
        GraphicsCompileContext{fragment.firstUserSgpr, linked, {}, {}, {}}};
    null->prepared->entries.push_back(stages.back().entry);
    const auto invocation = InvocationFor(*null, fragment.codeOffset, request);
    SrtRuntime runtime{}; runtime.userData = fragment.userData;
    const auto capture = invocation.Capture(runtime); const auto result = invocation.Materialize(*capture);
    require(result && result->variantId == GetPreparedArtifact(*stages.back().entry.handle).variantId,
            "actual draw invocation materialized another artifact");
    materialize(request, *stages.back().entry.handle);
    pass("depth_only_address_mode_" + std::to_string(addressMode) + "_wave" + std::to_string(wave) + "_prepare_capture_materialize");
}

void lateWave32() {
    auto null = builtinNull(); const auto pixel = AgcDriver::Graphics::DecodePixelStageInfo({}, {}, true);
    RecompileRequest request{{ShaderStage::Fragment, null->codeAddress, null->code, null->headerAddress, null->header},
        {64u, 0, {}, {}, pixel, {}, {}, {}}, target(), {0, 0, 0, 128}};
    null->prepared->entries.push_back({0, PrepareShader(request)});
    request.context.waveSize = 32u; request.layout = {0, 0, 20, 108};
    auto invocation = InvocationFor(*null, 0, request);
    const auto capture = invocation.Capture(SrtRuntime{}); const auto result = invocation.Materialize(*capture);
    require(null->prepared->entries.size() == 2u && result && result->variantId == GetPreparedArtifact(*null->prepared->entries.back().handle).variantId,
            "late wave32 fallback did not capture/materialize the newly prepared artifact");
    materialize(request, *null->prepared->entries.back().handle);
    const auto again = InvocationFor(*null, 0, request); const auto captureAgain = again.Capture(SrtRuntime{});
    require(again.Materialize(*captureAgain)->variantId == result->variantId && null->prepared->entries.size() == 2u,
            "late wave32 repeated invocation prepared another artifact");
    pass("late_wave32_actual_invocation_prepare_capture_materialize_reuse");
}

void negative(unsigned mode) {
    Fixture front; auto null = builtinNull(); std::shared_ptr<ShaderRegistry> registry;
    PublishRegisteredShader(registry, front.snapshot); PublishRegisteredShader(registry, null);
    auto queue = depthOnly(front, mode); queue.context[0x8eu] = 0xfu;
    // InitialContextRegisters disables CB0 with COLOR_INVALID; a mask alone is
    // not a writable color target. Preserve this legitimate depth-only control.
    require(AgcDriver::Graphics::ColorWriteMask(queue.context) == 0u &&
            AgcDriver::Graphics::NullPixelProgramRejection(queue).empty(),
            "COLOR_INVALID with a nonzero channel mask was treated as a color write");
    queue.context[0x31cu] = 0x28028u; // Enabled RGBA8 CB0, as in the production graphics fixture.
    require(AgcDriver::Graphics::ColorWriteMask(queue.context) == 0xfu,
            "null PS negative fixture did not enable the actual color target");
    require(AgcDriver::Graphics::NullPixelProgramRejection(queue).find("writes color") != std::string::npos,
            "actual null PS color-write guard did not reject");
    DrawDecode decoded{}; decoded.state.stages.path = AgcDriver::Graphics::ShaderPath::Vertex;
    rejected([&] { DecodeGraphicsPrograms(decoded, queue, *registry, false, true); }, "writes color");
    pass("color_write_address_mode_" + std::to_string(mode) + "_rejected_before_materialize");
}

void nonNullMissingVariant() {
    auto snapshot = builtinNull(); snapshot->codeAddress += 256u;
    const auto pixel = AgcDriver::Graphics::DecodePixelStageInfo({}, {}, true);
    RecompileRequest request{{ShaderStage::Fragment, snapshot->codeAddress, snapshot->code, snapshot->headerAddress, snapshot->header},
        {64u, 0, {}, {}, pixel, {}, {}, {}}, target(), {0, 0, 0, 128}};
    snapshot->prepared->entries.push_back({0, PrepareShader(request)}); request.context.waveSize = 32u;
    rejected([&] { static_cast<void>(InvocationFor(*snapshot, 0, request)); }, "artifact is missing");
    pass("registered_nonnull_missing_variant_still_rejected");
}
}

int main(int argc, char** argv) {
    try {
        require(argc == 2, "exact fresh production PRX path argument required");
        char path[32768]{}; const auto module = GetModuleHandleW(L"libSceAgcDriver.prx");
        const auto count = module ? GetModuleFileNameA(module, path, sizeof(path)) : 0u;
        require(count != 0u && count < sizeof(path) && _stricmp(path, argv[1]) == 0,
                "fixture loaded a different production PRX");
        require(ShaderDiskCache::FormatVersion == 28u &&
                ShaderDiskCache::SourceVersion() == ShaderDiskCache::Generated::SourceVersion,
                "actual null-pixel driver cache/source identity differs");
        std::cout << "ACTUAL_DRIVER_PATH " << path << '\n'
                  << "ACTUAL_DRIVER_CACHE_SOURCE_VERSION " << std::hex;
        std::cout.width(16); std::cout.fill('0'); std::cout << ShaderDiskCache::SourceVersion() << std::dec << '\n'
                  << "ACTUAL_DRIVER_CACHE_FORMAT " << ShaderDiskCache::FormatVersion << '\n';
        for (unsigned mode = 0; mode < 4; ++mode) for (const auto wave : {32u, 64u}) staged(mode, wave);
        lateWave32(); negative(0); negative(1); nonNullMissingVariant();
        require(passed == 12u, "actual null-pixel fixture coverage is incomplete");
        std::cout << "TOTAL_PASS " << passed << '\n'
                  << "GPU_EXECUTION 0\nREGISTER_SHADER_DEVICE_API_EXECUTION 0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "NULL_PIXEL_MATERIALIZATION_FAILURE " << error.what() << '\n'; return 1;
    }
}
