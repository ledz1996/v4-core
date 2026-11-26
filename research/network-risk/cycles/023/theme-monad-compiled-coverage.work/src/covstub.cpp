// Plain (unpatched emitter) builds: the coverage symbols exist but stay empty; run plain builds without HX_COVOUT.
#include <cstdint>
#include <utility>
#include <vector>
namespace monad_cov { std::vector<std::pair<uint32_t, uint64_t>> blocks; std::vector<uint8_t> enterable; uint64_t base = 0, text_end = 0, error_addr = 0, epilogue_addr = 0; }
