// Backtrace capture is not needed by the harness; return an empty pointer.
#include <category/core/backtrace.hpp>
namespace monad { stack_backtrace::ptr stack_backtrace::capture(std::span<std::byte>) noexcept { return {}; } }
