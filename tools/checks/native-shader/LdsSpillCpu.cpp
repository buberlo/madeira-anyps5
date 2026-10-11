// CPU-only checks of actual production compilation and its emitted SPIR-V.
// Reuse the original synthetic shader and Compile/WorkgroupBytes helpers;
// the renamed GPU entrypoint is never invoked and is discarded by the linker.
#define SPV_ENABLE_UTILITY_CODE
#define main RetainedLdsGpuFixtureMain
#include APS5_LDS_EXECUTION_FIXTURE
#undef main
#include "BdaAbi.hpp"
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
#include <string_view>
#include <utility>

namespace {

using Triple = std::array<std::uint32_t, 3>;
using Words = std::span<const std::uint32_t>;

void Check(bool good, const std::string& reason) {
    if (!good) throw std::runtime_error("CPU LDS spill: " + reason);
}

// Small emitted-instruction reader, not a shader emulator. It evaluates only
// the integer SSA operations and builtin component loads forming the LDS slice.
struct Module {
    std::vector<Words> instructions;
    std::map<std::uint32_t, Words> definitions;
    std::map<std::uint32_t, std::uint32_t> builtins;
    std::uint32_t spill = 0, local = 0;

    explicit Module(Words words) {
        Check(words.size() >= 5u && words[0] == 0x07230203u, "invalid SPIR-V header");
        for (std::size_t at = 5; at < words.size();) {
            const auto count = words[at] >> 16u;
            Check(count != 0u && count <= words.size() - at, "malformed SPIR-V instruction");
            const auto i = words.subspan(at, count);
            instructions.push_back(i);
            const auto opcode = static_cast<spv::Op>(i[0] & 65535u);
            bool result = false, typed = false;
            spv::HasResultAndType(opcode, &result, &typed);
            if (result) definitions[i[typed ? 2u : 1u]] = i;
            if (opcode == spv::OpDecorate && count == 4u && i[2] == spv::DecorationBuiltIn)
                builtins[i[1]] = i[3];
            if (opcode == spv::OpName && count >= 3u) {
                const auto* text = reinterpret_cast<const char*>(i.data() + 2u);
                const auto available = (count - 2u) * sizeof(std::uint32_t);
                const auto* end = static_cast<const char*>(std::memchr(text, 0, available));
                Check(end != nullptr, "unterminated SPIR-V name");
                const std::string_view name(text, static_cast<std::size_t>(end - text));
                if (name == "workgroup_memory") spill = i[1];
                if (name == "lds_dwords") local = i[1];
            }
            at += count;
        }
    }

    static spv::Op Op(Words i) { return static_cast<spv::Op>(i[0] & 65535u); }
    std::uint32_t Constant(std::uint32_t id) const {
        const auto i = definitions.at(id);
        Check(Op(i) == spv::OpConstant && i.size() == 4u, "expected scalar u32 constant");
        return i[3];
    }
    bool Decorated(std::uint32_t id, spv::Decoration decoration,
                   std::optional<std::uint32_t> value = std::nullopt) const {
        return std::any_of(instructions.begin(), instructions.end(), [&](Words i) {
            return Op(i) == spv::OpDecorate && i[1] == id && i[2] == decoration &&
                (!value || (i.size() == 4u && i[3] == *value));
        });
    }
    bool PointerInto(std::uint32_t pointer, std::uint32_t variable) const {
        const auto found = definitions.find(pointer);
        return found != definitions.end() && Op(found->second) == spv::OpAccessChain &&
            found->second[3] == variable;
    }
    std::uint32_t Eval(std::uint32_t id, const Triple& counts, const Triple& group,
                       unsigned depth = 0u) const {
        Check(depth < 32u, "unexpected slice expression depth");
        const auto i = definitions.at(id);
        const auto op = Op(i);
        if (op == spv::OpConstant) return Constant(id);
        if (op == spv::OpIAdd || op == spv::OpIMul) {
            const auto a = Eval(i[3], counts, group, depth + 1u);
            const auto b = Eval(i[4], counts, group, depth + 1u);
            return op == spv::OpIAdd ? a + b : a * b;
        }
        Check(op == spv::OpLoad, "slice expression contains an unsupported operation");
        const auto pointer = definitions.at(i[3]);
        Check(Op(pointer) == spv::OpAccessChain && pointer.size() == 5u,
              "slice input is not a builtin component pointer");
        const auto component = Constant(pointer[4]);
        Check(component < 3u, "slice builtin component out of range");
        const auto builtin = builtins.at(pointer[3]);
        Check(builtin == spv::BuiltInNumWorkgroups || builtin == spv::BuiltInWorkgroupId,
              "slice expression reads an unrelated builtin");
        return (builtin == spv::BuiltInNumWorkgroups ? counts : group)[component];
    }
};

void Inspect(const ShaderRecompiler::RecompileResult& result, std::uint32_t ldsBytes,
             std::uint32_t limit, const std::string& label) {
    const auto expectedSpill = static_cast<std::uint64_t>(ldsBytes) + 4u > limit;
    const auto stride = ldsBytes / 4u + 1u; // guest data plus the 64-bit atomic lock
    Check(result.workgroupMemoryDwords == (expectedSpill ? stride : 0u), label + " wrong spill threshold/stride");
    const auto words = result.spirv.Words();
    Check(WorkgroupBytes(words) <= limit, label + " exceeds advertised Workgroup storage");
    const Module module(words);
    Check((module.spill != 0u) == expectedSpill, label + " wrong storage-buffer declaration");
    const auto variable = expectedSpill ? module.spill : module.local;
    Check(variable != 0u, label + " missing LDS variable");
    const auto declaration = module.definitions.at(variable);
    Check(Module::Op(declaration) == spv::OpVariable && declaration[3] ==
        (expectedSpill ? spv::StorageClassStorageBuffer : spv::StorageClassWorkgroup), label + " wrong LDS storage class");
    if (expectedSpill) {
        Check(module.Decorated(variable, spv::DecorationCoherent), label + " spill buffer is not coherent");
        Check(module.Decorated(variable, spv::DecorationDescriptorSet, ShaderRecompiler::WorkgroupMemoryDescriptorSet) &&
              module.Decorated(variable, spv::DecorationBinding, 0u), label + " spill descriptor ABI changed");
    } else {
        Check(WorkgroupBytes(words) == static_cast<std::uint64_t>(stride) * 4u,
              label + " native LDS omitted the atomic lock word");
    }

    unsigned controls = 0u, adds = 0u, acquired = 0u, released = 0u, bounds = 0u;
    std::uint32_t lockIndex = 0u;
    const auto semantics = [&](std::uint32_t id, std::uint32_t ordering) {
        const auto mask = module.Constant(id);
        Check((mask & ordering) == ordering && (mask & spv::MemorySemanticsWorkgroupMemoryMask) != 0u,
              label + " LDS memory ordering/Workgroup semantics lost");
        Check(((mask & spv::MemorySemanticsUniformMemoryMask) != 0u) == expectedSpill,
              label + " LDS UniformMemory semantics disagree with backing storage");
    };
    for (const auto i : module.instructions) {
        const auto op = Module::Op(i);
        if (op == spv::OpControlBarrier &&
            (module.Constant(i[3]) & spv::MemorySemanticsWorkgroupMemoryMask) != 0u) {
            Check(module.Constant(i[2]) == spv::ScopeWorkgroup, label + " wrong LDS barrier memory scope");
            semantics(i[3], spv::MemorySemanticsAcquireReleaseMask);
            ++controls;
        }
        if (op == spv::OpMemoryBarrier &&
            (module.Constant(i[2]) & spv::MemorySemanticsWorkgroupMemoryMask) != 0u)
            semantics(i[2], spv::MemorySemanticsAcquireReleaseMask);
        if (op == spv::OpAtomicIAdd && module.PointerInto(i[3], variable)) {
            Check(module.Constant(i[4]) == spv::ScopeWorkgroup, label + " LDS atomic add changed scope");
            ++adds;
        }
        if (op == spv::OpAtomicCompareExchange && module.PointerInto(i[3], variable)) {
            Check(module.Constant(i[4]) == spv::ScopeWorkgroup && module.Constant(i[6]) == 0u,
                  label + " lock scope/failure ordering changed");
            semantics(i[5], spv::MemorySemanticsAcquireMask);
            const auto pointer = module.definitions.at(i[3]);
            lockIndex = pointer.back();
            ++acquired;
        }
        if (op == spv::OpAtomicStore && module.PointerInto(i[1], variable)) {
            Check(module.Constant(i[2]) == spv::ScopeWorkgroup && module.Constant(i[4]) == 0u,
                  label + " lock release changed scope/value");
            semantics(i[3], spv::MemorySemanticsReleaseMask);
            ++released;
        }
        if (op == spv::OpULessThan) {
            const auto found = module.definitions.find(i[4]);
            if (found != module.definitions.end() && Module::Op(found->second) == spv::OpConstant &&
                module.Constant(i[4]) == ldsBytes / 4u) ++bounds;
        }
    }
    Check(controls != 0u && adds != 0u && acquired != 0u && released != 0u && bounds != 0u,
          label + " lost barrier, atomic, lock or guest-range guard operations");
    if (expectedSpill) {
        for (const Triple counts : {Triple{1u,1u,1u}, Triple{3u,2u,1u}, Triple{2u,2u,2u}, Triple{7u,3u,2u}}) {
            std::set<std::uint32_t> slots;
            for (std::uint32_t z = 0; z < counts[2]; ++z)
                for (std::uint32_t y = 0; y < counts[1]; ++y)
                    for (std::uint32_t x = 0; x < counts[0]; ++x) {
                        const auto last = module.Eval(lockIndex, counts, {x,y,z});
                        const auto linear = x + counts[0] * y + counts[0] * counts[1] * z;
                        Check(last == linear * stride + ldsBytes / 4u, label + " emitted slice/lock address mismatch");
                        Check(last < counts[0] * counts[1] * counts[2] * stride && slots.insert(last).second,
                              label + " emitted workgroup slices alias or escape allocation");
                    }
        }
    }
}

} // namespace

int main(int argc, char** argv) {
    try {
        Check(argc <= 2, "usage: agc_lds_spill_cpu_tests [SPIR-V output directory]");
        const std::array<std::uint32_t, 9> capabilities{
            spv::CapabilityShader, spv::CapabilityInt64, spv::CapabilityStorageBuffer8BitAccess,
            spv::CapabilityPhysicalStorageBufferAddresses, spv::CapabilityGroupNonUniform,
            spv::CapabilityGroupNonUniformBallot, spv::CapabilityGroupNonUniformShuffle,
            spv::CapabilityGroupNonUniformArithmetic, spv::CapabilitySignedZeroInfNanPreserve};
        const std::array<std::string_view, 3> extensions{
            "SPV_KHR_8bit_storage", "SPV_KHR_physical_storage_buffer", "SPV_KHR_float_controls"};
        if (argc == 2) std::filesystem::create_directories(argv[1]);
        unsigned cases = 0;
        for (const auto profile : {std::pair{32u,32u}, std::pair{64u,32u}, std::pair{64u,64u}}) {
            for (const std::uint32_t limit : {2048u,32768u}) {
                const ShaderRecompiler::SpirvTarget target{
                    VK_API_VERSION_1_1, 0x00010300u, profile.second, ShaderRecompiler::BdaAbi::Version,
                    capabilities, extensions, false, {1024u,1024u,64u}, 1024u, limit, {}, {}};
                for (const auto bytes : {limit - 8u, limit - 4u, limit, limit + 4096u}) {
                    const auto label = "guest" + std::to_string(profile.first) + "-host" + std::to_string(profile.second) +
                        "-limit" + std::to_string(limit) + "-lds" + std::to_string(bytes);
                    const auto compiled = Compile(profile.first, bytes, target);
                    Inspect(compiled, bytes, limit, label);
                    if (argc == 2) {
                        std::ofstream output(std::filesystem::path(argv[1]) / (label + ".spv"), std::ios::binary);
                        const auto& words = compiled.spirv.Words();
                        output.write(reinterpret_cast<const char*>(words.data()), static_cast<std::streamsize>(words.size() * 4u));
                        Check(output.good(), "failed to write explicit SPIR-V output");
                    }
                    ++cases;
                    std::cout << "PASS " << label << '\n';
                }
            }
        }
        std::cout << "CPU_LDS_COMPILER_SPIRV_ONLY_PASS " << cases << "; GPU dispatch/output not executed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
