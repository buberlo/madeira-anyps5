#pragma once
#include <cstddef>
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace LibcException::RawLogOutput {
namespace {

inline constexpr std::size_t MaximumTextBytes = 1024 * 1024;
inline constexpr std::size_t MaximumChunkBytes = 4096;
inline constexpr std::size_t MaximumWriteCalls = 65536;
inline constexpr char TruncationMarker[] = "\n[libc] exception text truncated at 1048576 bytes\n";

enum class Result { Complete, Truncated, WriteFailed };

class StderrWriter {
#ifdef _WIN32
    HANDLE handle = GetStdHandle(STD_ERROR_HANDLE);
#endif
public:
    std::ptrdiff_t operator()(const char* data, std::size_t size) noexcept {
#ifdef _WIN32
        DWORD written = 0;
        if (!WriteFile(handle, data, static_cast<DWORD>(size), &written, nullptr)) return -1;
        return static_cast<std::ptrdiff_t>(written);
#else
        return ::write(STDERR_FILENO, data, size);
#endif
    }
};

template<class TWrite>
static bool WriteBytes(TWrite& write, const char* data, std::size_t size, std::size_t& calls) noexcept {
    while (size) {
        if (calls == MaximumWriteCalls) return false;
        ++calls;
        const std::size_t request = size < MaximumChunkBytes ? size : MaximumChunkBytes;
        const auto written = write(data, request);
        if (written <= 0 || static_cast<std::size_t>(written) > request) return false;
        data += written;
        size -= static_cast<std::size_t>(written);
    }
    return true;
}

template<class TWrite>
static Result WriteText(TWrite& write, const char* text) noexcept {
    if (!text) text = "(null)";
    std::size_t offset = 0;
    std::size_t calls = 0;
    while (offset < MaximumTextBytes) {
        const std::size_t remaining = MaximumTextBytes - offset;
        const std::size_t limit = remaining < MaximumChunkBytes ? remaining : MaximumChunkBytes;
        std::size_t length = 0;
        while (length < limit && text[offset + length]) ++length;
        if (!WriteBytes(write, text + offset, length, calls)) return Result::WriteFailed;
        offset += length;
        if (length < limit) return Result::Complete;
    }
    if (!text[offset]) return Result::Complete;
    if (!WriteBytes(write, TruncationMarker, sizeof(TruncationMarker) - 1, calls)) return Result::WriteFailed;
    return Result::Truncated;
}

template<class TWrite>
static Result WriteException(TWrite& write, const char* type, const char* what) noexcept {
    const char* parts[] = {"terminate called after throwing an instance of '", type, "'\n"};
    for (const char* part : parts) {
        const auto result = WriteText(write, part);
        if (result != Result::Complete) return result;
    }
    if (!what) return Result::Complete;
    const auto prefix = WriteText(write, "  what():  ");
    if (prefix != Result::Complete) return prefix;
    const auto result = WriteText(write, what);
    if (result == Result::WriteFailed) return result;
    if (WriteText(write, "\n") != Result::Complete) return Result::WriteFailed;
    return result;
}

}

}
