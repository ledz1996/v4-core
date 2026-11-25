extern "C" void hx_mark(char const *);
// Copyright (C) 2025 Category Labs, Inc.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#include <category/core/assert.h>
#include <category/core/cases.hpp>
#include <category/core/int.hpp>
#include <category/core/likely.h>
#include <category/core/runtime/uint256.hpp>
#include <category/vm/compiler/ir/basic_blocks.hpp>
#include <category/vm/compiler/ir/x86/emitter.hpp>
#include <category/vm/compiler/ir/x86/types.hpp>
#include <category/vm/compiler/ir/x86/virtual_stack.hpp>
#include <category/vm/compiler/types.hpp>
#include <category/vm/interpreter/intercode.hpp>
#include <category/vm/runtime/math.hpp>
#include <category/vm/runtime/math/intrinsics.hpp>
#include <category/vm/runtime/storage.hpp>
#include <category/vm/runtime/transmute/intrinsics.hpp>
#include <category/vm/runtime/types.hpp>
#include <category/vm/utils/debug.hpp>

#include <asmjit/core/api-config.h>
#include <asmjit/core/codeholder.h>
#include <asmjit/core/emitter.h>
#include <asmjit/core/globals.h>
#include <asmjit/core/jitruntime.h>
#include <asmjit/core/operand.h>
#include <asmjit/x86/x86operand.h>

#include <evmc/evmc.h>

#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <format>
#include <functional>
#include <iostream>
#include <limits>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

namespace runtime = monad::vm::runtime;
namespace x86 = asmjit::x86;

using monad::Cases;

static_assert(ASMJIT_ARCH_X86 == 64);

namespace
{
    using namespace monad::vm::compiler::native;
    using monad::uint256_t;

    constexpr auto reg_context = x86::rbx;
    constexpr auto reg_stack = x86::rbp;

    constexpr auto sp_offset_arg1 = 0;
    constexpr auto sp_offset_arg2 = sp_offset_arg1 + 8;
    constexpr auto sp_offset_arg3 = sp_offset_arg2 + 8;
    constexpr auto sp_offset_arg4 = sp_offset_arg3 + 8;
    constexpr auto sp_offset_arg5 = sp_offset_arg4 + 8;
    constexpr auto sp_offset_arg6 = sp_offset_arg5 + 8;
    constexpr auto sp_offset_stack_size = sp_offset_arg6 + 8;
    constexpr auto sp_offset_temp_word1 = sp_offset_stack_size + 8;
    constexpr auto sp_offset_temp_word2 = sp_offset_temp_word1 + 32;

    constexpr auto stack_frame_size = sp_offset_temp_word2 + 32;

    constexpr GeneralReg volatile_general_reg{2};
    constexpr GeneralReg rdi_general_reg{volatile_general_reg};
    constexpr GeneralReg rsi_general_reg{volatile_general_reg};
    constexpr GeneralReg rcx_general_reg{volatile_general_reg};
    constexpr GeneralReg rdx_general_reg{volatile_general_reg};

    Emitter::Imm256 literal_to_imm256(Literal const &lit)
    {
        return {
            asmjit::Imm{static_cast<int32_t>(lit.value[0])},
            asmjit::Imm{static_cast<int32_t>(lit.value[1])},
            asmjit::Imm{static_cast<int32_t>(lit.value[2])},
            asmjit::Imm{static_cast<int32_t>(lit.value[3])}};
    }

    Emitter::Mem256 const stack_offset_to_mem256(StackOffset const offset)
    {
        return {
            x86::qword_ptr(x86::rbp, offset.offset * 32),
            x86::qword_ptr(x86::rbp, offset.offset * 32 + 8),
            x86::qword_ptr(x86::rbp, offset.offset * 32 + 16),
            x86::qword_ptr(x86::rbp, offset.offset * 32 + 24)};
    }

    x86::Mem stack_offset_to_mem(StackOffset const offset)
    {
        return x86::qword_ptr(x86::rbp, offset.offset * 32);
    }

    x86::Ymm avx_reg_to_ymm(AvxReg const reg)
    {
        MONAD_DEBUG_ASSERT(reg.reg < 32);
        return x86::Ymm(reg.reg);
    }

    x86::Xmm avx_reg_to_xmm(AvxReg const reg)
    {
        MONAD_DEBUG_ASSERT(reg.reg < 32);
        return x86::Xmm(reg.reg);
    }

    void runtime_print_gas_remaining_impl(
        char const *const msg, runtime::Context const *const ctx)
    {
        std::cout << msg << ": gas remaining: " << ctx->gas_remaining
                  << std::endl;
    }

    void runtime_print_input_stack_impl(
        char const *const msg, uint256_t *const stack,
        uint64_t const stack_size)
    {
        std::cout << msg << ": stack: ";
        for (size_t i = 0; i < stack_size; ++i) {
            std::cout << '(' << i << ": " << stack[-i - 1].to_string() << ')';
        }
        std::cout << std::endl;
    }

    uint64_t runtime_store_input_stack_impl(
        runtime::Context const *const ctx, uint256_t *const stack,
        uint64_t const stack_size, uint64_t const offset,
        uint64_t const base_offset)
    {
        return runtime::debug_tstore_stack(
            ctx, stack, stack_size, offset, base_offset);
    }

    void runtime_print_top2_impl(
        char const *const msg, uint256_t const *const x,
        uint256_t const *const y)
    {
        std::cout << msg << ": " << x->to_string() << " and " << y->to_string()
                  << std::endl;
    }

    void
    runtime_print_top1_impl(char const *const msg, uint256_t const *const x)
    {
        std::cout << msg << ": " << x->to_string() << std::endl;
    }
}

// For reducing noise
#define GENERAL_BIN_INSTR(i0, i1)                                              \
    general_bin_instr<                                                         \
        {&x86::Assembler::i0,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1},                                                 \
        {&x86::Assembler::i0,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1},                                                 \
        {&x86::Assembler::i0,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1},                                                 \
        {&x86::Assembler::i0,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1},                                                 \
        {&x86::Assembler::i0,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1,                                                  \
         &x86::Assembler::i1}>

// For reducing noise
#define AVX_OR_GENERAL_BIN_INSTR(i, v)                                         \
    avx_or_general_bin_instr<                                                  \
        {&x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i},                                                  \
        {&x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i},                                                  \
        {&x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i},                                                  \
        {&x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i},                                                  \
        {&x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i,                                                   \
         &x86::Assembler::i},                                                  \
        &x86::Assembler::v,                                                    \
        &x86::Assembler::v>

namespace monad::vm::compiler::native
{
    Emitter::Error::Error(std::string const &msg)
        : std::runtime_error{msg}
    {
    }

    Emitter::Error::Error(char const *const msg)
        : std::runtime_error{msg}
    {
    }

    void Emitter::EmitErrorHandler::handleError(
        asmjit::Error, char const *const msg, asmjit::BaseEmitter *)
    {
        throw Emitter::Error(std::format("x86 emitter error: {}", msg));
    }

    template <typename Int>
    bool Emitter::is_uint64_bounded(uint64_t x)
    {
        hx_mark("@F247 is_uint64_bounded");
        static_assert(sizeof(Int) < sizeof(uint64_t));
        if constexpr (std::is_signed_v<Int>) {
            hx_mark("@L249");
            int64_t const i = std::bit_cast<int64_t>(x);
            constexpr int64_t upper =
                static_cast<int64_t>(std::numeric_limits<Int>::max());
            constexpr int64_t lower =
                static_cast<int64_t>(std::numeric_limits<Int>::min());
            return i <= upper && i >= lower;
        }
        else {
            hx_mark("@L257");
            return x <= std::numeric_limits<Int>::max();
        }
    }

    template <typename Int>
    bool Emitter::is_literal_bounded(Literal const &lit)
    {
        hx_mark("@F264 is_literal_bounded");
        for (size_t i = 0; i < 4; ++i) {
            hx_mark("@L265");
            if (!is_uint64_bounded<Int>(lit.value[i])) {
                hx_mark("@L266");
                return false;
            }
        }
        return true;
    }

    char const *Emitter::location_type_to_string(LocationType const loc)
    {
        hx_mark("@F274 location_type_to_string");
        switch (loc) {
        case Emitter::LocationType::AvxReg:
            return "AvxReg";
        case Emitter::LocationType::GeneralReg:
            return "GeneralReg";
        case Emitter::LocationType::StackOffset:
            return "StackOffset";
        case Emitter::LocationType::Literal:
            return "Literal";
        }
        return ""; // unreachable
    }

    template <size_t N>
    size_t Emitter::RoSubdata<N>::DataHash::operator()(Data const &x) const
    {
        static_assert(N == 2 || N == 4 || N % 8 == 0);
        if constexpr (N == 2) {
            uint16_t d;
            std::memcpy(&d, x.data(), N);
            return std::hash<uint16_t>{}(d);
        }
        if constexpr (N == 4) {
            uint32_t d;
            std::memcpy(&d, x.data(), N);
            return std::hash<uint32_t>{}(d);
        }
        if constexpr (N > 4) {
            size_t h = 0;
            for (size_t i = 0; i < N; i += 8) {
                uint64_t d;
                std::memcpy(&d, x.data() + i, 8);
                h ^= std::hash<uint64_t>{}(d);
            }
            return h;
        }
    }

    Emitter::RoData::RoData(asmjit::Label const lbl)
        : label_{lbl}
    {
    }

    asmjit::Label const &Emitter::RoData::label() const
    {
        return label_;
    }

    std::vector<uint256_t> const &Emitter::RoData::data() const
    {
        return data_;
    }

    asmjit::x86::Mem Emitter::RoData::add_literal(Literal const &lit)
    {
        return add32(lit.value);
    }

    template <typename F>
    asmjit::x86::Mem Emitter::RoData::add_external_function(F f)
    {
        static_assert(sizeof(F) == sizeof(uint64_t));
        static_assert(alignof(F) == alignof(uint64_t));
        return add8(reinterpret_cast<uint64_t>(f));
    }

    asmjit::x86::Mem Emitter::RoData::add32(uint256_t const &x)
    {
        // We need `data_` size upper bounded to not overflow `int32_t`,
        // i.e. estimate_size() < std::numeric_limits<int32_t>::max()
        if (MONAD_UNLIKELY(data_.size() >= (1 << 26))) {
            throw Nativecode::SizeEstimateOutOfBounds{estimate_size()};
        }

        std::array<uint8_t, 32> a;
        store_le(a.data(), x);
        int32_t const next_offset = static_cast<int32_t>(data_.size()) << 5;
        auto const [it, is_new] = sub32_.offmap.emplace(a, next_offset);
        if (is_new) {
            data_.push_back(x);
        }
        int32_t const offset = it->second;
        return x86::qword_ptr(label_, offset);
    }

    // The three values are stored contiguously, so that a load may span
    // two of them, starting `line_offset` bytes into a 64 byte cache line.
    asmjit::x86::Mem Emitter::RoData::add96(
        uint256_t const &x0, uint256_t const &x1, uint256_t const &x2,
        int32_t const line_offset)
    {
        // The bound in `add32`, with room for a padding chunk and all three
        if (MONAD_UNLIKELY(data_.size() >= (1 << 26) - 3)) {
            throw Nativecode::SizeEstimateOutOfBounds{estimate_size()};
        }

        std::array<uint8_t, 96> a;
        store_le(a.data(), x0);
        store_le(a.data() + 32, x1);
        store_le(a.data() + 64, x2);
        auto const [it, is_new] = sub96_.offmap.try_emplace(a);
        if (is_new) {
            if (((static_cast<int32_t>(data_.size()) << 5) & 63) !=
                line_offset) {
                data_.emplace_back();
            }
            it->second = static_cast<int32_t>(data_.size()) << 5;
            data_.push_back(x0);
            data_.push_back(x1);
            data_.push_back(x2);
        }
        return x86::qword_ptr(label_, it->second);
    }

    asmjit::x86::Mem
    Emitter::RoData::add16(uint64_t const x0, uint64_t const x1)
    {
        std::array<uint8_t, 16> x;
        std::memcpy(x.data(), &x0, 8);
        std::memcpy(x.data() + 8, &x1, 8);
        return add<16>(x);
    }

    asmjit::x86::Mem Emitter::RoData::add8(uint64_t const x0)
    {
        std::array<uint8_t, 8> x;
        std::memcpy(x.data(), &x0, 8);
        return add<8>(x);
    }

    asmjit::x86::Mem Emitter::RoData::add4(uint32_t const x0)
    {
        std::array<uint8_t, 4> x;
        std::memcpy(x.data(), &x0, 4);
        auto m = add<4>(x);
        m.setSize(4);
        return m;
    }

    template <size_t N>
    asmjit::x86::Mem Emitter::RoData::add(std::array<uint8_t, N> const &x)
    {
        // We need `data_` size upper bounded to not overflow `int32_t`
        // i.e. estimate_size() < std::numeric_limits<int32_t>::max()
        if (MONAD_UNLIKELY(data_.size() >= (1 << 26))) {
            throw Nativecode::SizeEstimateOutOfBounds{estimate_size()};
        }

        static_assert(4 <= N && N <= 16);
        static_assert(std::popcount(N) == 1);
        static constexpr int32_t n = static_cast<int32_t>(N);
        static constexpr int32_t align = std::min(8, n);
        static constexpr int32_t align_mask = align - 1;

        RoSubdata<N> &sub = [this] -> RoSubdata<N> & {
            if constexpr (N == 4) {
                return sub4_;
            }
            if constexpr (N == 8) {
                return sub8_;
            }
            if constexpr (N == 16) {
                return sub16_;
            }
        }();

        int32_t next_partial_index = partial_index_;
        // Align `partial_sub_index_` by `align`:
        int32_t next_partial_sub_index =
            partial_sub_index_ +
            ((align - (partial_sub_index_ & align_mask)) & align_mask);
        if (next_partial_sub_index > 32 - n) {
            next_partial_index = static_cast<int32_t>(data_.size());
            next_partial_sub_index = 0;
        }
        int32_t const next_offset =
            (next_partial_index << 5) + next_partial_sub_index;
        auto const [it, is_new] = sub.offmap.emplace(x, next_offset);
        if (is_new) {
            if (next_partial_sub_index == 0) {
                data_.emplace_back();
            }
            MONAD_DEBUG_ASSERT(
                static_cast<size_t>(next_partial_index) < data_.size());
            static_assert(sizeof(size_t) >= sizeof(next_partial_index));
            auto &a = data_[static_cast<size_t>(next_partial_index)];
            std::memcpy(as_bytes(a) + next_partial_sub_index, &x, N);
            partial_index_ = next_partial_index;
            partial_sub_index_ = next_partial_sub_index + n;
        }
        int32_t const offset = it->second;
        return x86::qword_ptr(label_, offset);
    }

    size_t Emitter::RoData::estimate_size()
    {
        return data_.size() << 5;
    }

    Emitter::RuntimeImpl &Emitter::RuntimeImpl::pass(StackElemRef &&elem)
    {
        if (!elem->stack_offset() && !elem->literal()) {
            em_->mov_stack_elem_to_stack_offset(elem);
        }
        explicit_args_.push_back(std::move(elem));
        return *this;
    }

    void Emitter::RuntimeImpl::call_impl()
    {
        MONAD_ASSERT(
            explicit_args_.size() + implicit_arg_count() == arg_count_);
        MONAD_DEBUG_ASSERT(arg_count_ <= MAX_RUNTIME_ARGS);
        MONAD_DEBUG_ASSERT(
            !context_arg_.has_value() || context_arg_ != result_arg_);
        MONAD_DEBUG_ASSERT(
            !context_arg_.has_value() || context_arg_ != remaining_gas_arg_);
        MONAD_DEBUG_ASSERT(
            !result_arg_.has_value() || result_arg_ != remaining_gas_arg_);

        for (size_t a = 0, i = 0; i < arg_count_; ++i) {
            auto const u = std::optional{i};
            if (u == context_arg_ || u == result_arg_ ||
                u == remaining_gas_arg_) {
                continue;
            }
            StackElemRef const elem = explicit_args_[a++];
            if (elem->stack_offset()) {
                mov_arg(i, stack_offset_to_mem(*elem->stack_offset()));
            }
            else {
                MONAD_DEBUG_ASSERT(elem->literal().has_value());
                auto const m = em_->rodata_.add_literal(*elem->literal());
                mov_arg(i, m);
            }
        }

        // Clear stack elements to deallocate registers and stack offsets:
        explicit_args_.clear();

        if (context_arg_.has_value()) {
            mov_arg(*context_arg_, reg_context);
        }
        if (remaining_gas_arg_.has_value()) {
            mov_arg(*remaining_gas_arg_, remaining_base_gas_);
        }
        if (result_arg_.has_value()) {
            // Assumes that result will be written to memory from general
            // registers
            auto result = em_->stack_.alloc_stack_offset(
                em_->stack_.top_index() + 1, PrevLoc::GprReg);
            mov_arg(*result_arg_, stack_offset_to_mem(*result->stack_offset()));
            em_->stack_.push(std::move(result));
        }

        if (spill_avx_) {
            em_->as_.vzeroupper();
        }
        auto const fn_mem = em_->rodata_.add_external_function(runtime_fun_);
        em_->as_.call(fn_mem);
    }

    size_t Emitter::RuntimeImpl::implicit_arg_count()
    {
        return context_arg_.has_value() + result_arg_.has_value() +
               remaining_gas_arg_.has_value();
    }

    size_t Emitter::RuntimeImpl::explicit_arg_count()
    {
        MONAD_DEBUG_ASSERT(arg_count_ >= implicit_arg_count());
        return arg_count_ - implicit_arg_count();
    }

    bool Emitter::RuntimeImpl::spill_avx_regs()
    {
        return spill_avx_;
    }

    void Emitter::RuntimeImpl::mov_arg(size_t const arg_index, RuntimeArg &&arg)
    {
        static_assert(MAX_RUNTIME_ARGS == 12);
        switch (arg_index) {
        case 0:
            mov_reg_arg(x86::rdi, std::move(arg));
            break;
        case 1:
            mov_reg_arg(x86::rsi, std::move(arg));
            break;
        case 2:
            mov_reg_arg(x86::rdx, std::move(arg));
            break;
        case 3:
            mov_reg_arg(x86::rcx, std::move(arg));
            break;
        case 4:
            mov_reg_arg(x86::r8, std::move(arg));
            break;
        case 5:
            mov_reg_arg(x86::r9, std::move(arg));
            break;
        case 6:
            mov_stack_arg(sp_offset_arg1, std::move(arg));
            break;
        case 7:
            mov_stack_arg(sp_offset_arg2, std::move(arg));
            break;
        case 8:
            mov_stack_arg(sp_offset_arg3, std::move(arg));
            break;
        case 9:
            mov_stack_arg(sp_offset_arg4, std::move(arg));
            break;
        case 10:
            mov_stack_arg(sp_offset_arg5, std::move(arg));
            break;
        case 11:
            mov_stack_arg(sp_offset_arg6, std::move(arg));
            break;
        default:
            MONAD_ABORT();
        }
    }

    void Emitter::RuntimeImpl::mov_reg_arg(
        asmjit::x86::Gpq const &reg, RuntimeArg &&arg)
    {
        std::visit(
            Cases{
                [&](x86::Gpq const &x) { em_->as_.mov(reg, x); },
                [&](asmjit::Imm const &x) { em_->as_.mov(reg, x); },
                [&](x86::Mem const &x) { em_->as_.lea(reg, x); },
            },
            arg);
    }

    void Emitter::RuntimeImpl::mov_stack_arg(
        int32_t const sp_offset, RuntimeArg &&arg)
    {
        std::visit(
            Cases{
                [&](x86::Gpq const &x) {
                    em_->as_.mov(x86::qword_ptr(x86::rsp, sp_offset), x);
                },
                [&](asmjit::Imm const &x) {
                    em_->as_.mov(x86::qword_ptr(x86::rsp, sp_offset), x);
                },
                [&](x86::Mem const &x) {
                    em_->as_.lea(x86::rax, x);
                    em_->as_.mov(x86::qword_ptr(x86::rsp, sp_offset), x86::rax);
                },
            },
            arg);
    }

    Emitter::Emitter(
        asmjit::JitRuntime const &rt, interpreter::code_size_t const codesize,
        CompilerConfig const &config)
        : runtime_debug_trace_{config.runtime_debug_trace}
        , as_{init_code_holder(rt, config.asm_log_path)}
        , epilogue_label_{as_.newNamedLabel("ContractEpilogue")}
        , error_label_{as_.newNamedLabel("Error")}
        , jump_table_label_{std::nullopt}
        , keep_stack_in_next_block_{}
        , gpq256_regs_{Gpq256{x86::r12, x86::r13, x86::r14, x86::r15}, Gpq256{x86::r8, x86::r9, x86::r10, x86::r11}, Gpq256{x86::rcx, x86::rsi, x86::rdx, x86::rdi}}
        , bytecode_size_{codesize}
        , rodata_{as_.newNamedLabel("ROD")}
        , exponential_constant_fold_counter_{0}
        , accumulated_static_work_{0}
        , final_stack_dep_counts_{
              std::make_unique_for_overwrite<int32_t[]>(1024)}
    {
#ifdef MONAD_VM_TESTING
        as_.addDiagnosticOptions(kValidateAssembler);
#endif
        contract_prologue();
    }

    Emitter::~Emitter()
    {
        if (debug_logger_.file()) {
            hx_mark("@L655");
            int const err = fclose(debug_logger_.file());
            MONAD_ASSERT(err == 0);
        }
    }

    void Emitter::flush_debug_logger()
    {
        hx_mark("@F662 flush_debug_logger");
        if (debug_logger_.file()) {
            hx_mark("@L663");
            int const err = fflush(debug_logger_.file());
            MONAD_ASSERT(err == 0);
        }
    }

    entrypoint_t Emitter::finish_contract(asmjit::JitRuntime &rt)
    {
        hx_mark("@F670 finish_contract");
        contract_epilogue();

        for (auto const &[lbl, fn, back] : load_bounded_le_handlers_) {
            hx_mark("@L673");
            as_.bind(lbl);
            as_.call(fn);
            as_.jmp(back);
        }

        error_block(error_label_, runtime::StatusCode::Error);

        // By putting jump table in the text section, we can use the
        // `code_holder_.labelOffset` function to compute the relative
        // distance between the `error_label_` and the
        // `jump_table_label_` instead of using the built in
        // `as_.embedLabelDelta` functionality when emitting the jump
        // table. Saves significant compile time to calculate this
        // relative label distance ourselves, instead of asmjit doing the
        // same calculation again and again for `as_.embedLabelDelta`.
        as_.align(asmjit::AlignMode::kData, 4);
        if (jump_table_label_) {
            hx_mark("@L690");
            as_.bind(jump_table_label_.value());
            int32_t const error_offset = [&] {
                int64_t const x = std::bit_cast<int64_t>(
                    code_holder_.labelOffset(error_label_) -
                    code_holder_.labelOffset(jump_table_label_.value()));
                MONAD_DEBUG_ASSERT(
                    x <= std::numeric_limits<int32_t>::max() &&
                    x >= std::numeric_limits<int32_t>::min());
                return static_cast<int32_t>(x);
            }();
            size_t error_offset_repeat_count = 0;
            for (size_t bid = 0; bid < *bytecode_size_; ++bid) {
                hx_mark("@L702");
                auto const lbl = jump_dests_.find(bid);
                if (lbl != jump_dests_.end()) {
                    hx_mark("@L704");
                    as_.embedInt32(error_offset, error_offset_repeat_count);
                    error_offset_repeat_count = 0;
                    as_.embedLabelDelta(
                        lbl->second, jump_table_label_.value(), 4);
                }
                else {
                    hx_mark("@L710");
                    ++error_offset_repeat_count;
                }
            }
            as_.embedInt32(error_offset, error_offset_repeat_count);
        }

        static char const *const ro_section_name = "ro";
        static auto const ro_section_name_len = 2;
        static auto const ro_section_index = 1;

        bool const is_ro_section_empty =
            (rodata_.data().size() | debug_messages_.size()) == 0;

        // Inside asmjit, if a section is emitted with no actual data in it, a
        // call to memcpy with a null source is made. This is technically UB,
        // and will get flagged by ubsan as such, even if it is technically
        // harmless in practice. So only emit ro section if non-empty.
        if (!is_ro_section_empty) {
            hx_mark("@L728");
            asmjit::Section *ro_section;
            code_holder_.newSection(
                &ro_section,
                ro_section_name,
                ro_section_name_len,
                asmjit::SectionFlags::kReadOnly,
                64,
                ro_section_index);
            as_.section(ro_section);

            as_.bind(rodata_.label());
            as_.embed(&rodata_.data()[0], rodata_.data().size() << 5);

            for (auto const &[lbl, msg] : debug_messages_) {
                hx_mark("@L742");
                as_.bind(lbl);
                as_.embed(msg.c_str(), msg.size() + 1);
            }
        }

        entrypoint_t contract_main;
        auto const err = rt.add(&contract_main, &code_holder_);
        if (err != asmjit::kErrorOk) {
            hx_mark("@L750");
            fail_with_error(err);
        }

        return contract_main;
    }

    asmjit::CodeHolder *Emitter::init_code_holder(
        asmjit::JitRuntime const &rt, char const *const log_path)
    {
        hx_mark("@F759 init_code_holder");
        code_holder_.setErrorHandler(&error_handler_);
        if (log_path) {
            hx_mark("@L761");
            FILE *log_file = fopen(log_path, "w");
            MONAD_ASSERT(log_file);
            debug_logger_.setFile(log_file);
            code_holder_.setLogger(&debug_logger_);
        }
        code_holder_.init(rt.environment(), rt.cpuFeatures());
        return &code_holder_;
    }

    void Emitter::contract_prologue()
    {
        hx_mark("@F772 contract_prologue");
        // Arguments
        // rdi: context pointer
        // rsi: stack pointer

        as_.push(x86::rbp); // 16 byte aligned
        as_.push(x86::rbx); // unaligned
        as_.push(x86::r12); // 16 byte aligned
        as_.push(x86::r13); // unaligned
        as_.push(x86::r14); // 16 byte aligned
        as_.push(x86::r15); // unaligned

        as_.mov(reg_context, x86::rdi);
        as_.mov(reg_stack, x86::rsi);
        as_.mov(
            x86::ptr(reg_context, runtime::context_offset_exit_stack_ptr),
            x86::rsp);

        static_assert(stack_frame_size % 16 == 8);
        as_.sub(x86::rsp, stack_frame_size); // 16 byte aligned

        as_.mov(x86::qword_ptr(x86::rsp, sp_offset_stack_size), 0);
    }

    void Emitter::contract_epilogue()
    {
        hx_mark("@F797 contract_epilogue");
        as_.align(asmjit::AlignMode::kCode, 16);
        as_.bind(epilogue_label_);
        as_.vzeroupper();
        as_.add(x86::rsp, stack_frame_size);
        as_.pop(x86::r15);
        as_.pop(x86::r14);
        as_.pop(x86::r13);
        as_.pop(x86::r12);
        as_.pop(x86::rbx);
        as_.pop(x86::rbp);
        as_.ret();
    }

    void Emitter::runtime_print_gas_remaining(std::string const &msg)
    {
        hx_mark("@F812 runtime_print_gas_remaining");
        auto const msg_lbl = as_.newLabel();
        debug_messages_.emplace_back(msg_lbl, msg);
        auto const fn_mem =
            rodata_.add_external_function(runtime_print_gas_remaining_impl);

        discharge_deferred_comparison();
        spill_caller_save_regs(true);
        as_.lea(x86::rdi, x86::qword_ptr(msg_lbl));
        as_.mov(x86::rsi, reg_context);
        as_.vzeroupper();
        as_.call(fn_mem);
    }

    void Emitter::runtime_print_input_stack(std::string const &msg)
    {
        hx_mark("@F827 runtime_print_input_stack");
        auto const msg_lbl = as_.newLabel();
        debug_messages_.emplace_back(msg_lbl, msg);
        auto const fn_mem =
            rodata_.add_external_function(runtime_print_input_stack_impl);

        discharge_deferred_comparison();
        spill_caller_save_regs(true);
        as_.lea(x86::rdi, x86::qword_ptr(msg_lbl));
        as_.mov(x86::rsi, reg_stack);
        as_.mov(x86::rdx, x86::qword_ptr(x86::rsp, sp_offset_stack_size));
        as_.vzeroupper();
        as_.call(fn_mem);
    }

    /**
     * We call the runtime_store_input_stack_impl twice. The first time we
     * temporarily dump the virtual stack of the current block, at [rsp -
     * 32*current_stack_size,...rsp], which we use as scratch memory. Once we
     * call runtime_store_input_stack_impl and save the current block's partial
     * stack, we can dump the contents of the rest of the evm stack from
     * previous blocks by calling runtime_store_input_stack_impl again, this
     * time passing the pointer to the stack offset back by the current virtual
     * stack's min_delta, which ensures that we don't save stale values that
     * might have been modified by the current block.
     */
    void Emitter::runtime_store_input_stack(uint64_t const base_offset)
    {
        hx_mark("@F854 runtime_store_input_stack");
        if (!utils::is_fuzzing_monad_vm) {
            hx_mark("@L855");
            return;
        }

        checked_debug_comment("Store stack in transient storage");

        auto const fn_mem =
            rodata_.add_external_function(runtime_store_input_stack_impl);

        discharge_deferred_comparison();
        spill_caller_save_regs(true);

        auto const current_stack_size =
            stack_.top_index() - stack_.min_delta() + 1;
        as_.mov(x86::rsi, x86::rsp);
        as_.sub(x86::rsp, current_stack_size * 32);

        auto j = 0;
        for (int32_t i = stack_.min_delta(); i <= stack_.top_index(); ++i) {
            hx_mark("@L873");
            mov_stack_elem_to_unaligned_mem<false>(
                stack_.get(i), x86::qword_ptr(x86::rsp, j));
            j += 32;
        }

        as_.mov(x86::rdi, reg_context);
        as_.mov(x86::rdx, current_stack_size);
        as_.mov(x86::rcx, 0);
        as_.mov(x86::r8, base_offset);
        as_.vzeroupper();
        as_.call(fn_mem);

        as_.add(x86::rsp, current_stack_size * 32);

        auto const skip_lbl = as_.newLabel();
        as_.test(x86::eax, x86::eax);
        as_.jz(skip_lbl);

        as_.mov(x86::rdi, reg_context);
        as_.mov(x86::rsi, reg_stack);
        as_.add(x86::rsi, 32 * stack_.min_delta());

        as_.mov(x86::rdx, x86::qword_ptr(x86::rsp, sp_offset_stack_size));
        as_.add(x86::rdx, stack_.min_delta());

        as_.mov(x86::rcx, current_stack_size);
        as_.mov(x86::r8, base_offset);

        as_.call(fn_mem);

        as_.bind(skip_lbl);
    }

    void Emitter::runtime_print_top2(std::string const &msg)
    {
        hx_mark("@F908 runtime_print_top2");
        auto const msg_lbl = as_.newLabel();
        debug_messages_.emplace_back(msg_lbl, msg);
        auto const fn_mem =
            rodata_.add_external_function(runtime_print_top2_impl);

        discharge_deferred_comparison();
        spill_caller_save_regs(true);

        as_.lea(x86::rdi, x86::qword_ptr(msg_lbl));

        auto const e1 = stack_.get(stack_.top_index());
        if (!e1->stack_offset() && !e1->literal()) {
            hx_mark("@L920");
            mov_stack_elem_to_stack_offset(e1);
        }
        if (e1->stack_offset().has_value()) {
            hx_mark("@L923");
            as_.lea(x86::rsi, stack_offset_to_mem(e1->stack_offset().value()));
        }
        else {
            hx_mark("@L926");
            auto const m = rodata_.add_literal(e1->literal().value());
            as_.lea(x86::rsi, m);
        }
        auto const e2 = stack_.get(stack_.top_index() - 1);
        if (!e2->stack_offset() && !e2->literal()) {
            hx_mark("@L931");
            mov_stack_elem_to_stack_offset(e2);
        }
        if (e2->stack_offset().has_value()) {
            hx_mark("@L934");
            as_.lea(x86::rdx, stack_offset_to_mem(e2->stack_offset().value()));
        }
        else {
            hx_mark("@L937");
            auto const m = rodata_.add_literal(e2->literal().value());
            as_.lea(x86::rdx, m);
        }
        as_.vzeroupper();
        as_.call(fn_mem);
    }

    void Emitter::runtime_print_top1(std::string const &msg)
    {
        hx_mark("@F946 runtime_print_top1");
        auto const msg_lbl = as_.newLabel();
        debug_messages_.emplace_back(msg_lbl, msg);
        auto const fn_mem =
            rodata_.add_external_function(runtime_print_top1_impl);

        discharge_deferred_comparison();
        spill_caller_save_regs(true);

        as_.lea(x86::rdi, x86::qword_ptr(msg_lbl));

        auto const e1 = stack_.get(stack_.top_index());
        if (!e1->stack_offset() && !e1->literal()) {
            hx_mark("@L958");
            mov_stack_elem_to_stack_offset(e1);
        }
        if (e1->stack_offset().has_value()) {
            hx_mark("@L961");
            as_.lea(x86::rsi, stack_offset_to_mem(e1->stack_offset().value()));
        }
        else {
            hx_mark("@L964");
            auto const m = rodata_.add_literal(e1->literal().value());
            as_.lea(x86::rsi, m);
        }
        as_.vzeroupper();
        as_.call(fn_mem);
    }

    void Emitter::breakpoint()
    {
        hx_mark("@F973 breakpoint");
        as_.int3();
    }

    void Emitter::swap_general_regs(StackElem &x, StackElem &y)
    {
        hx_mark("@F978 swap_general_regs");
        MONAD_ASSERT(x.general_reg().has_value());
        MONAD_ASSERT(y.general_reg().has_value());
        auto xg = general_reg_to_gpq256(*x.general_reg());
        auto yg = general_reg_to_gpq256(*y.general_reg());
        for (size_t i = 0; i < 4; ++i) {
            hx_mark("@L983");
            as_.mov(x86::rax, xg[i]);
            as_.mov(xg[i], yg[i]);
            as_.mov(yg[i], x86::rax);
        }
        stack_.swap_general_regs(x, y);
    }

    void Emitter::swap_general_reg_indices(
        GeneralReg const r, uint8_t const i, uint8_t const j)
    {
        hx_mark("@F993 swap_general_reg_indices");
        MONAD_ASSERT(i < 4);
        MONAD_ASSERT(j < 4);
        if (i == j) {
            hx_mark("@L996");
            return;
        }
        auto &gpq = general_reg_to_gpq256(r);
        std::swap(gpq[i], gpq[j]);
        auto *e = stack_.general_reg_stack_elem(r);
        if (e) {
            hx_mark("@L1002");
            as_.mov(x86::rax, gpq[i]);
            as_.mov(gpq[i], gpq[j]);
            as_.mov(gpq[j], x86::rax);
        }
    }

    void Emitter::fail_with_error(asmjit::Error const e)
    {
        hx_mark("@F1010 fail_with_error");
        as_.reportError(e);
        std::unreachable();
    }

    Stack &Emitter::get_stack()
    {
        hx_mark("@F1016 get_stack");
        return stack_;
    }

    size_t Emitter::estimate_size()
    {
        hx_mark("@F1021 estimate_size");
        // current code size +
        // awaiting code gen for CALLDATALOAD instructions +
        // awaiting code gen for BYTE instructions +
        // size of read-only data section +
        // size of jump table
        return code_holder_.textSection()->realSize() +
               (load_bounded_le_handlers_.size() << 5) +
               rodata_.estimate_size() + (*bytecode_size_ << 2);
    }

    void Emitter::add_jump_dest(byte_offset const d)
    {
        hx_mark("@F1033 add_jump_dest");
        char name[2 * sizeof(byte_offset) + 2];
        static_assert(sizeof(byte_offset) <= sizeof(long));
        auto const isize = snprintf(name, sizeof(name), "B%lx", d);
        auto const size = static_cast<size_t>(isize);
        MONAD_DEBUG_ASSERT(size < sizeof(name));
        jump_dests_.emplace(d, as_.newNamedLabel(name, size));
    }

    bool Emitter::begin_new_block(basic_blocks::Block const &b)
    {
        hx_mark("@F1043 begin_new_block");
        checked_debug_comment("  0x{:02x}:", b.offset);
        if (keep_stack_in_next_block_) {
            hx_mark("@L1045");
            stack_.continue_block(b);
        }
        else {
            hx_mark("@L1048");
            stack_.begin_new_block(b);
        }
        return block_prologue(b);
    }

    void Emitter::gas_decrement_static_work(int64_t const gas)
    {
        hx_mark("@F1055 gas_decrement_static_work");
        if (gas) {
            hx_mark("@L1056");
            gas_decrement_no_check(gas);
            if (!accumulate_static_work(gas)) {
                hx_mark("@L1058");
                as_.jl(error_label_);
            }
        }
    }

    void Emitter::gas_decrement_unbounded_work(int64_t const gas)
    {
        hx_mark("@F1065 gas_decrement_unbounded_work");
        accumulated_static_work_ = 0;
        if (gas) {
            hx_mark("@L1067");
            gas_decrement_no_check(gas);
            as_.jl(error_label_);
        }
    }

    void Emitter::spill_caller_save_regs(bool const spill_avx)
    {
        hx_mark("@F1074 spill_caller_save_regs");
        // Spill general regs first, because if stack element is in both
        // general register and avx register then stack element will be
        // moved to stack using avx register.
        spill_all_caller_save_general_regs();
        if (spill_avx) {
            hx_mark("@L1079");
            spill_all_avx_regs();
        }
    }

    void Emitter::spill_all_caller_save_general_regs()
    {
        hx_mark("@F1085 spill_all_caller_save_general_regs");
        for (auto const &[reg, off] :
             stack_.spill_all_caller_save_general_regs()) {
                 hx_mark("@L1087");
            Gpq256 const &gpq = general_reg_to_gpq256(reg);
            x86::Mem m = stack_offset_to_mem(off);
            for (size_t i = 0; i < 4; ++i) {
                hx_mark("@L1090");
                as_.mov(m, gpq[i]);
                m.addOffset(8);
            }
        }
    }

    void Emitter::spill_avx_reg_range(uint8_t const start)
    {
        hx_mark("@F1098 spill_avx_reg_range");
        for (auto const &[reg, off] : stack_.spill_avx_reg_range(start)) {
            hx_mark("@L1099");
            as_.vmovaps(stack_offset_to_mem(off), avx_reg_to_ymm(reg));
        }
    }

    void Emitter::spill_all_avx_regs()
    {
        hx_mark("@F1105 spill_all_avx_regs");
        spill_avx_reg_range(0);
    }

    std::pair<StackElemRef, AvxRegReserv> Emitter::alloc_avx_reg()
    {
        hx_mark("@F1110 alloc_avx_reg");
        auto [elem, reserv, offset] = stack_.alloc_avx_reg();
        if (offset.has_value()) {
            hx_mark("@L1112");
            as_.vmovaps(
                stack_offset_to_mem(*offset), avx_reg_to_ymm(*elem->avx_reg()));
        }
        return {elem, reserv};
    }

    // Does not update eflags
    void Emitter::insert_avx_reg_without_reserv(StackElem &elem)
    {
        hx_mark("@F1121 insert_avx_reg_without_reserv");
        auto offset = stack_.insert_avx_reg_without_reserv(elem);
        if (offset.has_value()) {
            hx_mark("@L1123");
            as_.vmovaps(
                stack_offset_to_mem(*offset), avx_reg_to_ymm(*elem.avx_reg()));
        }
    }

    AvxRegReserv Emitter::insert_avx_reg(StackElemRef const elem)
    {
        hx_mark("@F1130 insert_avx_reg");
        auto [reserv, offset] = stack_.insert_avx_reg(elem);
        if (offset.has_value()) {
            hx_mark("@L1132");
            as_.vmovaps(
                stack_offset_to_mem(*offset), avx_reg_to_ymm(*elem->avx_reg()));
        }
        return reserv;
    }

    std::pair<StackElemRef, GeneralRegReserv> Emitter::alloc_general_reg()
    {
        hx_mark("@F1140 alloc_general_reg");
        auto [elem, reserv, offset] = stack_.alloc_general_reg();
        if (offset.has_value()) {
            hx_mark("@L1142");
            mov_general_reg_to_mem(
                *elem->general_reg(), stack_offset_to_mem(*offset));
        }
        return {elem, reserv};
    }

    GeneralRegReserv Emitter::insert_general_reg(StackElemRef const elem)
    {
        hx_mark("@F1150 insert_general_reg");
        auto [reserv, offset] = stack_.insert_general_reg(elem);
        if (offset.has_value()) {
            hx_mark("@L1152");
            mov_general_reg_to_mem(
                *elem->general_reg(), stack_offset_to_mem(*offset));
        }
        return reserv;
    }

    // Leaves the value of the general reg in `elem` unchanged.
    template <typename... LiveSet>
    StackElemRef Emitter::release_general_reg(
        StackElem &elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1163 release_general_reg");
        if (is_live(elem, live) && !elem.stack_offset() && !elem.literal() &&
            !elem.avx_reg()) {
                hx_mark("@L1165");
            if (stack_.has_free_general_reg()) {
                hx_mark("@L1166");
                elem.reserve_general_reg();
                auto [new_elem, reserv] = alloc_general_reg();
                elem.unreserve_general_reg();
                mov_general_reg_to_gpq256(
                    *elem.general_reg(),
                    general_reg_to_gpq256(*new_elem->general_reg()));
                stack_.swap_general_regs(elem, *new_elem);
                return new_elem;
            }
            else {
                hx_mark("@L1176");
                mov_general_reg_to_stack_offset(elem);
            }
        }
        return stack_.release_general_reg(elem);
    }

    // Leaves the value of the volatile general reg unchanged.
    template <typename... LiveSet>
    void
    Emitter::release_volatile_general_reg(std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1187 release_volatile_general_reg");
        auto *volatile_stack_elem =
            stack_.general_reg_stack_elem(volatile_general_reg);
        if (volatile_stack_elem) {
            hx_mark("@L1190");
            (void)release_general_reg(*volatile_stack_elem, live);
        }
    }

    template <typename... LiveSet>
    StackElemRef Emitter::release_general_reg(
        StackElemRef elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1198 release_general_reg");
        return release_general_reg(*elem, live);
    }

    template <typename... LiveSet>
    std::pair<StackElemRef, GeneralRegReserv>
    Emitter::alloc_or_release_general_reg(
        StackElemRef elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1206 alloc_or_release_general_reg");
        if (is_live(elem, live)) {
            hx_mark("@L1207");
            if (stack_.has_free_general_reg() ||
                (!elem->stack_offset() && !elem->avx_reg() &&
                 !elem->literal())) {
                     hx_mark("@L1210");
                GeneralRegReserv const reserv{elem};
                return alloc_general_reg();
            }
        }
        auto const r = stack_.release_general_reg(std::move(elem));
        return {r, GeneralRegReserv{r}};
    }

    template <typename... LiveSet>
    std::pair<StackElemRef, AvxRegReserv> Emitter::alloc_or_release_avx_reg(
        StackElemRef elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1222 alloc_or_release_avx_reg");
        if (is_live(elem, live)) {
            hx_mark("@L1223");
            if (stack_.has_free_avx_reg() ||
                (!elem->stack_offset() && !elem->general_reg() &&
                 !elem->literal())) {
                     hx_mark("@L1226");
                AvxRegReserv const reserv{elem};
                return alloc_avx_reg();
            }
        }
        auto const r = stack_.release_avx_reg(std::move(elem));
        return {r, AvxRegReserv{r}};
    }

    template <typename... LiveSet, size_t... Is>
    bool Emitter::is_live(
        StackElem const &elem, std::tuple<LiveSet...> const &live,
        std::index_sequence<Is...>)
    {
        hx_mark("@F1239 is_live");
        return elem.is_on_stack() ||
               (... || (&elem == std::get<Is>(live).get()));
    }

    template <typename... LiveSet>
    bool
    Emitter::is_live(StackElem const &elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1247 is_live");
        return is_live(elem, live, std::index_sequence_for<LiveSet...>{});
    }

    template <typename... LiveSet>
    bool Emitter::is_live(StackElemRef elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1253 is_live");
        return is_live(*elem, live, std::index_sequence_for<LiveSet...>{});
    }

    template <typename... LiveSet, size_t... Is>
    bool Emitter::is_live(
        GeneralReg reg, std::tuple<LiveSet...> const &live,
        std::index_sequence<Is...>)
    {
        hx_mark("@F1261 is_live");
        return stack_.is_general_reg_on_stack(reg) ||
               (... ||
                (std::optional{reg} == std::get<Is>(live)->general_reg()));
    }

    template <typename... LiveSet>
    bool Emitter::is_live(GeneralReg reg, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1269 is_live");
        return is_live(reg, live, std::index_sequence_for<LiveSet...>{});
    }

    void Emitter::gas_decrement_no_check(int64_t const gas)
    {
        hx_mark("@F1274 gas_decrement_no_check");
        MONAD_DEBUG_ASSERT(gas > 0);

        // This condition should never hold in practice, because the total gas
        // that can be included in a block for any supported chain is
        // substantially less than the maximum 32-bit signed integer.
        if (MONAD_UNLIKELY(gas > std::numeric_limits<int32_t>::max())) {
            hx_mark("@L1280");
            // TODO: To avoid hard-coding this value, we'd need to have access
            // to a Traits template parameter. Refactoring the Emitter class to
            // be trait-parameterized is a large refactoring that will need to
            // be done carefully, so for now just encode the current maximum
            // block size of any chain supported by the VM.
            static constexpr int64_t max_known_block_gas_limit = 200'000'000;
            static_assert(
                max_known_block_gas_limit <=
                std::numeric_limits<int32_t>::max());

            as_.jmp(error_label_);
            return;
        }

        as_.sub(
            x86::qword_ptr(reg_context, runtime::context_offset_gas_remaining),
            static_cast<int32_t>(gas));
    }

    void Emitter::gas_decrement_no_check(x86::Gpq const gas)
    {
        hx_mark("@F1301 gas_decrement_no_check");
        as_.sub(
            x86::qword_ptr(reg_context, runtime::context_offset_gas_remaining),
            gas);
    }

    bool Emitter::accumulate_static_work(int64_t const work)
    {
        hx_mark("@F1308 accumulate_static_work");
        MONAD_DEBUG_ASSERT(work >= 0);
        MONAD_DEBUG_ASSERT(
            work <= std::numeric_limits<int64_t>::max() -
                        STATIC_WORK_GAS_CHECK_THRESHOLD + 1);
        MONAD_DEBUG_ASSERT(
            accumulated_static_work_ < STATIC_WORK_GAS_CHECK_THRESHOLD);

        accumulated_static_work_ += work;

        if (accumulated_static_work_ >= STATIC_WORK_GAS_CHECK_THRESHOLD) {
            hx_mark("@L1318");
            accumulated_static_work_ = 0;
            return false;
        }
        return true;
    }

    bool Emitter::block_prologue(basic_blocks::Block const &b)
    {
        hx_mark("@F1326 block_prologue");
        bool const keep_stack = keep_stack_in_next_block_;
        keep_stack_in_next_block_ = false;

        auto const it = jump_dests_.find(b.offset);
        if (it != jump_dests_.end()) {
            hx_mark("@L1331");
            as_.bind(it->second);
        }

        if (MONAD_UNLIKELY(runtime_debug_trace_) && !keep_stack) {
            hx_mark("@L1335");
            runtime_print_gas_remaining(
                std::format("Block 0x{:02x}", b.offset));
        }

        auto const min_delta = stack_.min_delta();
        auto const max_delta = stack_.max_delta();
        if (max_delta - min_delta > 1024) {
            hx_mark("@L1342");
            // No stack size passes both of the checks below.
            as_.jmp(error_label_);
            return false;
        }
        auto const size_mem = x86::qword_ptr(x86::rsp, sp_offset_stack_size);
        if (stack_.did_min_delta_decrease()) {
            hx_mark("@L1348");
            as_.cmp(size_mem, -min_delta);
            as_.jb(error_label_);
        }
        if (stack_.did_max_delta_increase()) {
            hx_mark("@L1352");
            as_.cmp(size_mem, 1024 - max_delta);
            as_.ja(error_label_);
        }

        if (it != jump_dests_.end()) {
            hx_mark("@L1357");
            runtime_store_input_stack(b.offset);
        }

        return true;
    }

    template <bool preserve_eflags>
    void Emitter::adjust_by_stack_delta()
    {
        hx_mark("@F1366 adjust_by_stack_delta");
        auto const delta = stack_.delta();
        if (delta != 0) {
            hx_mark("@L1368");
            auto const ssm = x86::qword_ptr(x86::rsp, sp_offset_stack_size);
            if constexpr (preserve_eflags) {
                hx_mark("@L1370");
                as_.mov(x86::rax, ssm);
                as_.lea(x86::rax, x86::ptr(x86::rax, delta));
                as_.lea(x86::rbp, x86::ptr(x86::rbp, delta * 32));
                as_.mov(ssm, x86::rax);
            }
            else {
                hx_mark("@L1376");
                as_.add(ssm, delta);
                as_.add(x86::rbp, delta * 32);
            }
        }
    }

    // Does not update eflags
    void Emitter::write_to_final_stack_offsets()
    {
        hx_mark("@F1385 write_to_final_stack_offsets");
        // Write stack elements to their final stack offsets before
        // leaving basic block. If stack element `e` is currently at
        // stack indices `0`, `1` and only located in an AVX register,
        // then we need to move the AVX register to both stack offsets
        // `0` and `1`.

        MONAD_ASSERT(!stack_.has_deferred_comparison());

        int32_t const top_index = stack_.top_index();
        int32_t const min_delta = stack_.min_delta();
        if (top_index < min_delta) {
            hx_mark("@L1396");
            // Nothing on the stack.
            MONAD_DEBUG_ASSERT(stack_.missing_spill_count() == 0);
            return;
        }

        // The macros defined below are for counting the number of stack
        // elements written to final stack offset. This is later used to check
        // the invariant that the number of stack elements written to final
        // stack offset is the number returned by `Stack::missing_spill_count`.
#ifdef MONAD_COMPILER_TESTING
        size_t final_write_count = 0;
    #define MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT() ++final_write_count
    #define MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT_IF(b)                     \
        do {                                                                   \
            if (b) {                                                           \
                MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT();                    \
            }                                                                  \
        }                                                                      \
        while (0)
    #define MONAD_COMPILER_X86_FINAL_WRITE_COUNT final_write_count
#else
    #define MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT()
    #define MONAD_COMPILER_X86_FINAL_WRITE_COUNT 0
    #define MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT_IF(b) (void)sizeof(b)
#endif

        // Reserve an AVX register which we will use for temporary values.
        // Note that if `spill_elem` is not nullptr, then the spill needs
        // be reverted later to undo the state change to the stack.
        StackElem *spill_elem = nullptr;
        bool spill_elem_has_new_mem_location = false;
        if (!stack_.has_free_avx_reg()) {
            hx_mark("@L1428");
            spill_elem = stack_.find_stack_elem_for_avx_reg_spill();
            spill_elem_has_new_mem_location =
                stack_.spill_avx_reg(spill_elem) != nullptr;
        }
        auto [init1, init1_reserv, init1_spill] = stack_.alloc_avx_reg();
        MONAD_DEBUG_ASSERT(!init1_spill);
        auto const init_yx1 = avx_reg_to_ymm(*init1->avx_reg());
        auto yx1 = init_yx1;
        if (spill_elem_has_new_mem_location) {
            hx_mark("@L1437");
            MONAD_DEBUG_ASSERT(spill_elem->stack_offset().has_value());
            as_.vmovaps(
                stack_offset_to_mem(*spill_elem->stack_offset()), init_yx1);
            // The above mov was a write to a final stack offset if and only
            // if the new stack offset is a stack index of the stack element:
            MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT_IF(
                spill_elem->stack_indices().contains(
                    spill_elem->stack_offset()->offset));
        }

        // Definition. Stack element `e` depends on stack element `d` if
        //   * `d` is located on some stack offset `i` and
        //   * `i` is element of `e.stack_indices()` and
        //   * `d` is not located in AVX register and
        //   * `e != d`.
        //
        // Such a dependency means that `d` is occupying a final stack offset
        // to which stack element `e` needs to be located before leaving the
        // basic block. `dep_count(e)` is the number of dependencies of stack
        // element `e`, stored in `final_stack_dep_counts_` at the lowest stack
        // index of `e`. The vector `elems` holds the stack elements in stack
        // index order, which keeps the emitted code independent of heap
        // addresses.
        auto const n = static_cast<size_t>(top_index - min_delta) + 1;
        MONAD_DEBUG_ASSERT(n <= 1024);
        std::fill_n(final_stack_dep_counts_.get(), n, 0);
        auto const dep_count = [&](StackElem const *e) -> int32_t & {
            return final_stack_dep_counts_[static_cast<size_t>(
                *e->stack_indices().begin() - min_delta)];
        };
        std::vector<StackElem *> elems;
        elems.reserve(n);
        for (int32_t i = min_delta; i <= top_index; ++i) {
            hx_mark("@L1470");
            auto const d = stack_.get(i);

            MONAD_DEBUG_ASSERT(
                d->general_reg().has_value() || d->avx_reg().has_value() ||
                d->stack_offset().has_value() || d->literal().has_value());

            if (i != *d->stack_indices().begin()) {
                hx_mark("@L1477");
                // Already visited
                continue;
            }
            elems.push_back(d.get());
            if (!d->stack_offset().has_value()) {
                hx_mark("@L1482");
                continue;
            }
            int32_t const offset = d->stack_offset()->offset;
            if (offset > top_index) {
                hx_mark("@L1486");
                continue;
            }
            auto *e = stack_.get(offset).get();
            if (e == d.get()) {
                hx_mark("@L1490");
                continue;
            }
            if (d->avx_reg().has_value()) {
                hx_mark("@L1493");
                continue;
            }
            ++dep_count(e);
        }

        // The `non_dep` vector contains all the stack elements without
        // dependencies.
        std::vector<StackElem *> non_dep;
        for (StackElem *const e : elems) {
            hx_mark("@L1502");
            if (dep_count(e) == 0) {
                hx_mark("@L1503");
                non_dep.push_back(e);
            }
        }

        // A 256-bit load of words stored from general registers stalls store
        // forwarding, so if there is a free AVX register, then we use it to
        // put such stack elements in `yx1` word by word.
        auto const temp_x = [&]() -> std::optional<x86::Xmm> {
            if (!stack_.has_free_avx_reg()) {
                hx_mark("@L1512");
                return std::nullopt;
            }
            auto [t, _, spill] = stack_.alloc_avx_reg();
            MONAD_DEBUG_ASSERT(!spill);
            return avx_reg_to_xmm(*t->avx_reg());
        }();

        // Write all the stack elements without dependencies. Suppose stack
        // element `e` depends on stack element `d` and `d` does not have
        // any dependencies, i.e. is element of `non_dep`. After writing `d`
        // to its final stack offsets, we decrease `dep_count(e)`, because
        // it is now safe to write `e` to the stack offset which was occupied
        // by `d`. Insert `e` into `non_dep` if `dep_count(e)` becomes zero.
        while (!non_dep.empty()) {
            hx_mark("@L1526");
            StackElem *d = non_dep.back();
            non_dep.pop_back();
            auto const &is = d->stack_indices();
            MONAD_DEBUG_ASSERT(is.size() >= 1);
            auto it = is.begin();
            if (d->avx_reg()) {
                hx_mark("@L1532");
                // Stack element d is located in an AVX register we can use.
                yx1 = avx_reg_to_ymm(*d->avx_reg());
            }
            if (is.size() == 1 && d->stack_offset().has_value() &&
                d->stack_offset()->offset == *it) {
                    hx_mark("@L1537");
                // Stack element d is already located on the final stack offset.
                continue;
            }
            if (!d->avx_reg()) {
                hx_mark("@L1541");
                // Put stack element d in the `yx1` AVX register.
                if (d->stack_offset()) {
                    hx_mark("@L1543");
                    if (temp_x &&
                        d->stack_offset()->moved_from == PrevLoc::GprReg) {
                            hx_mark("@L1545");
                        mov_words_to_ymm(
                            stack_offset_to_mem256(*d->stack_offset()),
                            yx1,
                            *temp_x);
                    }
                    else {
                        hx_mark("@L1551");
                        as_.vmovaps(
                            yx1, stack_offset_to_mem(*d->stack_offset()));
                    }
                }
                else if (d->literal()) {
                    hx_mark("@L1556");
                    mov_literal_to_ymm(*d->literal(), yx1);
                }
                else if (temp_x && is.size() > 1) {
                    hx_mark("@L1559");
                    MONAD_DEBUG_ASSERT(d->general_reg().has_value());
                    mov_words_to_ymm(
                        general_reg_to_gpq256(*d->general_reg()), yx1, *temp_x);
                }
                else {
                    hx_mark("@L1564");
                    MONAD_DEBUG_ASSERT(d->general_reg().has_value());
                    auto const m =
                        stack_offset_to_mem(StackOffset{*it, PrevLoc::GprReg});
                    // Move to final stack offset:
                    mov_general_reg_to_mem(*d->general_reg(), m);
                    // Point to next stack offset:
                    ++it;
                    // Put in `yx1` if there are more final stack offsets:
                    if (it != is.end()) {
                        hx_mark("@L1573");
                        as_.vmovaps(yx1, m);
                    }
                    MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT();
                }
            }
            // Move to remaining final stack offsets:
            for (; it != is.end(); ++it) {
                hx_mark("@L1580");
                if (!d->stack_offset() || d->stack_offset()->offset != *it) {
                    hx_mark("@L1581");
                    as_.vmovaps(
                        stack_offset_to_mem(StackOffset{*it, PrevLoc::AvxReg}),
                        yx1);
                    MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT();
                }
            }
            // Decrease dependency count of the stack element which depends on
            // `d`, if such stack element exists.
            if (!d->avx_reg() && d->stack_offset()) {
                hx_mark("@L1590");
                int32_t const i = d->stack_offset()->offset;
                if (i > stack_.top_index()) {
                    hx_mark("@L1592");
                    continue;
                }
                StackElem *e = stack_.get(i).get();
                if (e == d) {
                    hx_mark("@L1596");
                    continue;
                }
                MONAD_DEBUG_ASSERT(dep_count(e) > 0);
                if (--dep_count(e) == 0) {
                    hx_mark("@L1600");
                    non_dep.push_back(e);
                }
            }
        }

        // We are not necessarily done, because there may remain cycles of
        // stack elements. E.g. stack element `e` depends on stack
        // element `d` and `d` depends on `e`. In this case, `e` and `d`
        // still have dependency count 1. It is not possible for a stack
        // element to have dependency count more than 1 at this point.

        // Later we will need two available AVX registers `yx2` and `yx1`.
        auto yx2 = yx1;
        // If there is a free avx register, then we can use it for `yx2`.
        // Otherwise we have necessarily updated `yx1` in the prior loop,
        // so the current value of `yx1` will work for `yx2`.
        if (stack_.has_free_avx_reg()) {
            hx_mark("@L1617");
            auto [y, _, spill] = stack_.alloc_avx_reg();
            MONAD_DEBUG_ASSERT(!spill);
            yx2 = avx_reg_to_ymm(*y->avx_reg());
        }
        yx1 = init_yx1;
        MONAD_DEBUG_ASSERT(yx1 != yx2);

        // Write the remaining stack elements in cycles to their final stack
        // offsets.
        for (StackElem *const e : elems) {
            hx_mark("@L1627");
            auto const ec = dep_count(e);
            MONAD_DEBUG_ASSERT(ec >= 0);
            if (ec == 0) {
                hx_mark("@L1630");
                // Since stack element e as no dependencies, it has
                // already been written it its final stack offsets.
                continue;
            }

            std::vector<StackElem *> cycle;
            cycle.reserve(2);
            StackElem *d = e;
            do {
                MONAD_DEBUG_ASSERT(dep_count(d) == 1);
                MONAD_DEBUG_ASSERT(!d->avx_reg().has_value());
                MONAD_DEBUG_ASSERT(d->stack_offset().has_value());
                dep_count(d) = 0;
                cycle.push_back(d);
                MONAD_DEBUG_ASSERT(
                    d->stack_offset()->offset <= stack_.top_index());
                d = stack_.get(d->stack_offset()->offset).get();
            }
            while (d != e);

            MONAD_DEBUG_ASSERT(cycle.size() >= 2);
            as_.vmovaps(
                yx1, stack_offset_to_mem(*cycle.back()->stack_offset()));

            // Write all the stack elements in the cycle containing e to
            // their final stack offsets.
            for (size_t k = cycle.size(); k > 1;) {
                hx_mark("@L1657");
                --k;
                // Invariant:
                // stack element `cycle[k]` is located in AVX register `yx1`.
                as_.vmovaps(
                    yx2, stack_offset_to_mem(*cycle[k - 1]->stack_offset()));
                for (int32_t const i : cycle[k]->stack_indices()) {
                    hx_mark("@L1663");
                    as_.vmovaps(
                        stack_offset_to_mem(StackOffset{i, PrevLoc::AvxReg}),
                        yx1);
                    MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT();
                }
                std::swap(yx1, yx2);
            }
            for (int32_t const i : e->stack_indices()) {
                hx_mark("@L1671");
                as_.vmovaps(
                    stack_offset_to_mem(StackOffset{i, PrevLoc::AvxReg}), yx1);
                MONAD_COMPILER_X86_INC_FINAL_WRITE_COUNT();
            }
        }

        if (spill_elem != nullptr) {
            hx_mark("@L1678");
            // Reset the state change to the stack caused by spilling the
            // avx register in `spill_elem`.
            stack_.move_avx_reg(*init1, *spill_elem);
            if (spill_elem_has_new_mem_location) {
                hx_mark("@L1682");
                stack_.remove_stack_offset(*spill_elem);
            }
        }

#ifdef MONAD_COMPILER_TESTING
        MONAD_ASSERT(
            MONAD_COMPILER_X86_FINAL_WRITE_COUNT ==
            stack_.missing_spill_count());
#endif
    }

    void Emitter::discharge_deferred_comparison()
    {
        hx_mark("@F1695 discharge_deferred_comparison");
        if (!stack_.has_deferred_comparison()) {
            hx_mark("@L1696");
            return;
        }
        auto const dc = stack_.discharge_deferred_comparison();
        if (dc.stack_elem) {
            hx_mark("@L1700");
            discharge_deferred_comparison(dc.stack_elem, dc.comparison());
        }
        if (dc.negated_stack_elem) {
            hx_mark("@L1703");
            auto const comp = negate_comparison(dc.comparison());
            discharge_deferred_comparison(dc.negated_stack_elem, comp);
        }
    }

    void Emitter::unchecked_debug_comment(std::string const &msg)
    {
        MONAD_ASSERT(debug_logger_.file());
        std::stringstream ss{msg};
        std::string line;
        while (std::getline(ss, line, '\n')) {
            hx_mark("@L1714");
            debug_logger_.log("// ");
            debug_logger_.log(line.c_str());
            debug_logger_.log("\n");
        }
    }

    void Emitter::unchecked_debug_comment(
        std::string_view const fmt, std::format_args const args)
    {
        unchecked_debug_comment(std::vformat(fmt, args));
    }

    // Does not update eflags
    void Emitter::discharge_deferred_comparison(
        StackElem *const elem, Comparison const comp)
    {
        hx_mark("@F1730 discharge_deferred_comparison");
        MONAD_DEBUG_ASSERT(
            !elem->general_reg() && !elem->avx_reg() && !elem->literal() &&
            !elem->stack_offset());
        insert_avx_reg_without_reserv(*elem);
        auto const x = avx_reg_to_xmm(*elem->avx_reg());
        switch (comp) {
        case Comparison::Below:
            as_.setb(x86::al);
            break;
        case Comparison::AboveEqual:
            as_.setae(x86::al);
            break;
        case Comparison::Above:
            as_.seta(x86::al);
            break;
        case Comparison::BelowEqual:
            as_.setbe(x86::al);
            break;
        case Comparison::Less:
            as_.setl(x86::al);
            break;
        case Comparison::GreaterEqual:
            as_.setge(x86::al);
            break;
        case Comparison::Greater:
            as_.setg(x86::al);
            break;
        case Comparison::LessEqual:
            as_.setle(x86::al);
            break;
        case Comparison::Equal:
            as_.sete(x86::al);
            break;
        case Comparison::NotEqual:
            as_.setne(x86::al);
            break;
        }
        as_.movzx(x86::eax, x86::al);
        as_.vmovd(x, x86::eax);
    }

    Emitter::Gpq256 &Emitter::general_reg_to_gpq256(GeneralReg const reg)
    {
        hx_mark("@F1773 general_reg_to_gpq256");
        MONAD_DEBUG_ASSERT(reg.reg <= 2);
        return gpq256_regs_[reg.reg];
    }

    // Low order index means `e` is suitable as destination operand.
    // High order index means `e` is suitable as source operand.
    template <typename... LiveSet>
    unsigned Emitter::get_stack_elem_general_order_index(
        StackElemRef e, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F1783 get_stack_elem_general_order_index");
        if (e->general_reg()) {
            hx_mark("@L1784");
            // General reg is perfect dst operand, so low order index.
            bool const e_is_live = is_live(e, live);
            if (e->literal()) {
                hx_mark("@L1787");
                // If also literal, then it might also be good src candidate,
                // therefore the order index is higher when literal.
                if (!e_is_live) {
                    hx_mark("@L1790");
                    // Not live and not literal is the lowest possible order
                    // index with `e` also literal.
                    return 2;
                }
                if (e->avx_reg() || e->stack_offset()) {
                    hx_mark("@L1795");
                    // We can release the general reg without a spill, so this
                    // is relatively good.
                    return 3;
                }
                // Releasing the general requires a spill.
                return 5;
            }
            if (!e->literal()) {
                hx_mark("@L1803");
                if (!e_is_live) {
                    hx_mark("@L1804");
                    // Not live and not literal is the lowest order index.
                    return 0;
                }
                if (e->avx_reg() || e->stack_offset()) {
                    hx_mark("@L1808");
                    // We can release the general reg without a spill, so this
                    // is relatively good.
                    return 1;
                }
                // Releasing the general requires a spill.
                return 4;
            }
        }
        if (e->literal()) {
            hx_mark("@L1817");
            if (is_literal_bounded(*e->literal())) {
                hx_mark("@L1818");
                // Bounded literal is a perfect src operand and it may trigger
                // optimizations later. Therefore the highest order index.
                return 9;
            }
            // Unbounded literal is not too bad as dst operand, because moving
            // to GPR has no dependencies and no memory load is necessary.
            return 6;
        }
        if (e->stack_offset()) {
            hx_mark("@L1827");
            return 7;
        }
        MONAD_DEBUG_ASSERT(e->avx_reg().has_value());
        return 8;
    }

    template <asmjit::x86::Gpq gpq>
    uint8_t Emitter::volatile_gpq_index()
    {
        hx_mark("@F1836 volatile_gpq_index");
        static_assert(
            gpq == x86::rdi || gpq == x86::rsi || gpq == x86::rcx ||
            gpq == x86::rdx);
        MONAD_DEBUG_ASSERT(volatile_general_reg == rdi_general_reg);
        MONAD_DEBUG_ASSERT(volatile_general_reg == rsi_general_reg);
        MONAD_DEBUG_ASSERT(volatile_general_reg == rcx_general_reg);
        MONAD_DEBUG_ASSERT(volatile_general_reg == rdx_general_reg);
        auto const &gpq256 = general_reg_to_gpq256(volatile_general_reg);
        for (uint8_t i = 0; i < 4; ++i) {
            hx_mark("@L1845");
            if (gpq256[i] == gpq) {
                hx_mark("@L1846");
                return i;
            }
        }
        MONAD_ABORT();
    }

    void Emitter::mov_stack_index_to_avx_reg(int32_t const stack_index)
    {
        hx_mark("@F1854 mov_stack_index_to_avx_reg");
        mov_stack_elem_to_avx_reg(stack_.get(stack_index));
    }

    void Emitter::mov_stack_index_to_general_reg(int32_t const stack_index)
    {
        hx_mark("@F1859 mov_stack_index_to_general_reg");
        mov_stack_elem_to_general_reg(stack_.get(stack_index));
    }

    void Emitter::mov_stack_index_to_stack_offset(int32_t const stack_index)
    {
        hx_mark("@F1864 mov_stack_index_to_stack_offset");
        mov_stack_elem_to_stack_offset(stack_.get(stack_index));
    }

    template <bool remember_intermediate, bool assume_aligned>
    void
    Emitter::mov_literal_to_mem(StackElemRef elem, asmjit::x86::Mem const &mem)
    {
        hx_mark("@F1871 mov_literal_to_mem");
        MONAD_ASSERT(elem->literal().has_value());

        auto const &lit = *elem->literal();

        AvxReg reg;
        if constexpr (remember_intermediate) {
            hx_mark("@L1877");
            mov_literal_to_avx_reg(elem);
            reg = *elem->avx_reg();
        }
        else {
            hx_mark("@L1881");
            auto [t, _] = alloc_avx_reg();
            reg = *t->avx_reg();
            mov_literal_to_ymm(lit, avx_reg_to_ymm(reg));
            elem = std::move(t);
        }
        if constexpr (assume_aligned) {
            hx_mark("@L1887");
            as_.vmovaps(mem, avx_reg_to_ymm(reg));
        }
        else {
            hx_mark("@L1890");
            as_.vmovups(mem, avx_reg_to_ymm(reg));
        }
    }

    template <bool assume_aligned>
    void
    Emitter::mov_literal_to_mem(Literal const &lit, asmjit::x86::Mem const &mem)
    {
        hx_mark("@F1898 mov_literal_to_mem");
        mov_literal_to_mem<true, assume_aligned>(
            stack_.alloc_literal(lit), mem);
    }

    void Emitter::mov_general_reg_to_mem(
        GeneralReg const reg, asmjit::x86::Mem const &mem)
    {
        hx_mark("@F1905 mov_general_reg_to_mem");
        x86::Mem temp{mem};
        for (auto const &r : general_reg_to_gpq256(reg)) {
            hx_mark("@L1907");
            as_.mov(temp, r);
            temp.addOffset(8);
        }
    }

    template <bool remember_intermediate>
    void Emitter::mov_stack_elem_to_unaligned_mem(
        StackElemRef elem, asmjit::x86::Mem const &mem)
    {
        hx_mark("@F1916 mov_stack_elem_to_unaligned_mem");
        if (elem->avx_reg()) {
            hx_mark("@L1917");
            as_.vmovups(mem, avx_reg_to_ymm(*elem->avx_reg()));
        }
        else if (elem->general_reg()) {
            hx_mark("@L1920");
            mov_general_reg_to_mem(*elem->general_reg(), mem);
        }
        else if constexpr (remember_intermediate) {
            hx_mark("@L1923");
            mov_stack_elem_to_avx_reg(elem);
            as_.vmovups(mem, avx_reg_to_ymm(*elem->avx_reg()));
        }
        else if (elem->literal()) {
            hx_mark("@L1927");
            mov_literal_to_mem<false, false>(elem, mem);
        }
        else {
            hx_mark("@L1930");
            MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
            auto [t, reserv] = alloc_avx_reg();
            auto const ymm = avx_reg_to_ymm(*t->avx_reg());
            as_.vmovaps(ymm, stack_offset_to_mem(*elem->stack_offset()));
            as_.vmovups(mem, ymm);
        }
    }

    void
    Emitter::mov_general_reg_to_gpq256(GeneralReg const reg, Gpq256 const &gpq)
    {
        hx_mark("@F1941 mov_general_reg_to_gpq256");
        Gpq256 const &temp = general_reg_to_gpq256(reg);
        if (&temp != &gpq) {
            hx_mark("@L1943");
            for (size_t i = 0; i < 4; ++i) {
                hx_mark("@L1944");
                as_.mov(gpq[i], temp[i]);
            }
        }
    }

    void Emitter::mov_literal_to_gpq256(Literal const &lit, Gpq256 const &gpq)
    {
        hx_mark("@F1951 mov_literal_to_gpq256");
        if (stack_.has_deferred_comparison()) {
            hx_mark("@L1952");
            for (size_t i = 0; i < 4; ++i) {
                hx_mark("@L1953");
                as_.mov(gpq[i], lit.value[i]);
            }
        }
        else {
            hx_mark("@L1957");
            for (size_t i = 0; i < 4; ++i) {
                hx_mark("@L1958");
                auto const &r = gpq[i];
                if (lit.value[i] == 0) {
                    hx_mark("@L1960");
                    as_.xor_(r.r32(), r.r32());
                }
                else {
                    hx_mark("@L1963");
                    as_.mov(r, lit.value[i]);
                }
            }
        }
    }

    void Emitter::mov_mem_to_gpq256(x86::Mem mem, Gpq256 const &gpq)
    {
        hx_mark("@F1971 mov_mem_to_gpq256");
        for (size_t i = 0; i < 4; ++i) {
            hx_mark("@L1972");
            as_.mov(gpq[i], mem);
            mem.addOffset(8);
        }
    }

    void Emitter::mov_stack_offset_to_gpq256(
        StackOffset const offset, Gpq256 const &gpq)
    {
        hx_mark("@F1980 mov_stack_offset_to_gpq256");
        mov_mem_to_gpq256(stack_offset_to_mem(offset), gpq);
    }

    template <bool remember_intermediate>
    void Emitter::mov_stack_elem_to_gpq256(StackElemRef elem, Gpq256 const &gpq)
    {
        hx_mark("@F1986 mov_stack_elem_to_gpq256");
        if (elem->general_reg()) {
            hx_mark("@L1987");
            mov_general_reg_to_gpq256(*elem->general_reg(), gpq);
        }
        else if (elem->literal()) {
            hx_mark("@L1990");
            mov_literal_to_gpq256(*elem->literal(), gpq);
        }
        else if (elem->stack_offset()) {
            hx_mark("@L1993");
            mov_stack_offset_to_gpq256(*elem->stack_offset(), gpq);
        }
        else {
            hx_mark("@L1996");
            MONAD_ASSERT(elem->avx_reg().has_value());
            if constexpr (remember_intermediate) {
                hx_mark("@L1998");
                mov_stack_elem_to_stack_offset(elem);
                mov_stack_offset_to_gpq256(*elem->stack_offset(), gpq);
            }
            else {
                hx_mark("@L2002");
                auto const m = x86::qword_ptr(x86::rsp, sp_offset_temp_word1);
                as_.vmovups(m, avx_reg_to_ymm(*elem->avx_reg()));
                mov_mem_to_gpq256(m, gpq);
            }
        }
    }

    void Emitter::mov_stack_elem_low64_to_gpq(
        StackElemRef const elem, x86::Gpq const gp)
    {
        hx_mark("@F2012 mov_stack_elem_low64_to_gpq");
        if (elem->general_reg()) {
            hx_mark("@L2013");
            auto const &gp256 = general_reg_to_gpq256(*elem->general_reg());
            if (gp256[0] != gp) {
                hx_mark("@L2015");
                as_.mov(gp, gp256[0]);
            }
        }
        else if (elem->literal()) {
            hx_mark("@L2019");
            as_.mov(gp, static_cast<uint64_t>(elem->literal()->value));
        }
        else if (elem->avx_reg()) {
            hx_mark("@L2022");
            as_.vmovq(gp, avx_reg_to_xmm(*elem->avx_reg()));
        }
        else {
            hx_mark("@L2025");
            MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
            as_.mov(gp, stack_offset_to_mem(*elem->stack_offset()));
        }
    }

    void Emitter::mov_literal_to_ymm(Literal const &lit, x86::Ymm const &y)
    {
        hx_mark("@F2032 mov_literal_to_ymm");
        if (lit.value == 0) {
            hx_mark("@L2033");
            as_.vpxor(y, y, y);
        }
        else if (lit.value == std::numeric_limits<uint256_t>::max()) {
            hx_mark("@L2036");
            as_.vpcmpeqd(y, y, y);
        }
        else if (lit.value == (std::numeric_limits<uint256_t>::max() >> 128)) {
            hx_mark("@L2039");
            as_.vpcmpeqd(y.xmm(), y.xmm(), y.xmm());
        }
        else if (lit.value <= std::numeric_limits<uint32_t>::max()) {
            hx_mark("@L2042");
            auto const m = rodata_.add4(static_cast<uint32_t>(lit.value));
            as_.vmovd(y.xmm(), m);
        }
        else if (lit.value <= std::numeric_limits<uint64_t>::max()) {
            hx_mark("@L2046");
            auto const m = rodata_.add8(static_cast<uint64_t>(lit.value));
            as_.vmovq(y.xmm(), m);
        }
        else if ((lit.value[2] | lit.value[3]) == 0) {
            hx_mark("@L2050");
            auto const m = rodata_.add16(lit.value[0], lit.value[1]);
            as_.vmovups(y.xmm(), m);
        }
        else {
            hx_mark("@L2054");
            auto const m = rodata_.add_literal(lit);
            as_.vmovaps(y, m);
        }
    }

    template <typename Word>
    void Emitter::mov_words_to_ymm(
        std::array<Word, 4> const &words, x86::Ymm const &y,
        x86::Xmm const &temp)
    {
        hx_mark("@F2064 mov_words_to_ymm");
        MONAD_DEBUG_ASSERT(y.id() != temp.id());
        as_.vmovq(y.xmm(), words[0]);
        as_.vmovq(temp, words[2]);
        as_.vpinsrq(y.xmm(), y.xmm(), words[1], 1);
        as_.vpinsrq(temp, temp, words[3], 1);
        as_.vinserti128(y, y, temp, 1);
    }

    void Emitter::mov_stack_elem_to_avx_reg(StackElemRef elem)
    {
        hx_mark("@F2074 mov_stack_elem_to_avx_reg");
        if (elem->avx_reg()) {
            hx_mark("@L2075");
            return;
        }
        if (elem->literal()) {
            hx_mark("@L2078");
            mov_literal_to_avx_reg(std::move(elem));
        }
        else if (elem->stack_offset()) {
            hx_mark("@L2081");
            mov_stack_offset_to_avx_reg(std::move(elem));
        }
        else {
            hx_mark("@L2084");
            MONAD_ASSERT(elem->general_reg().has_value());
            mov_general_reg_to_avx_reg(std::move(elem));
        }
    }

    void Emitter::mov_stack_elem_to_general_reg(StackElemRef elem)
    {
        hx_mark("@F2091 mov_stack_elem_to_general_reg");
        if (elem->general_reg()) {
            hx_mark("@L2092");
            return;
        }
        if (elem->literal()) {
            hx_mark("@L2095");
            mov_literal_to_general_reg(std::move(elem));
        }
        else if (elem->stack_offset()) {
            hx_mark("@L2098");
            mov_stack_offset_to_general_reg(std::move(elem));
        }
        else {
            hx_mark("@L2101");
            MONAD_ASSERT(elem->avx_reg().has_value());
            mov_avx_reg_to_general_reg(std::move(elem));
        }
    }

    void Emitter::mov_stack_elem_to_general_reg(
        StackElemRef elem, int32_t const preferred)
    {
        hx_mark("@F2109 mov_stack_elem_to_general_reg");
        if (elem->general_reg()) {
            hx_mark("@L2110");
            return;
        }
        if (elem->literal()) {
            hx_mark("@L2113");
            mov_literal_to_general_reg(std::move(elem));
        }
        else if (elem->stack_offset()) {
            hx_mark("@L2116");
            mov_stack_offset_to_general_reg(std::move(elem));
        }
        else {
            hx_mark("@L2119");
            MONAD_ASSERT(elem->avx_reg().has_value());
            mov_avx_reg_to_general_reg(std::move(elem), preferred);
        }
    }

    void Emitter::mov_stack_elem_to_stack_offset(StackElemRef elem)
    {
        hx_mark("@F2126 mov_stack_elem_to_stack_offset");
        if (elem->stack_offset()) {
            hx_mark("@L2127");
            return;
        }
        if (elem->avx_reg()) {
            hx_mark("@L2130");
            mov_avx_reg_to_stack_offset(std::move(elem));
        }
        else if (elem->general_reg()) {
            hx_mark("@L2133");
            mov_general_reg_to_stack_offset(std::move(elem));
        }
        else {
            hx_mark("@L2136");
            MONAD_ASSERT(elem->literal().has_value());
            mov_literal_to_stack_offset(std::move(elem));
        }
    }

    void Emitter::mov_stack_elem_to_stack_offset(
        StackElemRef elem, int32_t const preferred_offset)
    {
        hx_mark("@F2144 mov_stack_elem_to_stack_offset");
        if (elem->stack_offset()) {
            hx_mark("@L2145");
            return;
        }
        if (elem->avx_reg()) {
            hx_mark("@L2148");
            mov_avx_reg_to_stack_offset(std::move(elem), preferred_offset);
        }
        else if (elem->general_reg()) {
            hx_mark("@L2151");
            mov_general_reg_to_stack_offset(std::move(elem), preferred_offset);
        }
        else {
            hx_mark("@L2154");
            MONAD_ASSERT(elem->literal().has_value());
            mov_literal_to_stack_offset(std::move(elem), preferred_offset);
        }
    }

    void Emitter::mov_general_reg_to_avx_reg(StackElemRef const elem)
    {
        hx_mark("@F2161 mov_general_reg_to_avx_reg");
        MONAD_DEBUG_ASSERT(elem->general_reg().has_value());
        Gpq256 const &gpq = general_reg_to_gpq256(*elem->general_reg());
        auto const reserv0 = insert_avx_reg(elem);
        auto const ymm0 = avx_reg_to_ymm(*elem->avx_reg());

        auto [temp_reg, reserv1] = alloc_avx_reg();
        auto const xmm1 = avx_reg_to_xmm(*temp_reg->avx_reg());

        mov_words_to_ymm(gpq, ymm0, xmm1);
    }

    void Emitter::mov_literal_to_avx_reg(StackElemRef const elem)
    {
        hx_mark("@F2174 mov_literal_to_avx_reg");
        MONAD_DEBUG_ASSERT(elem->literal().has_value());
        auto const reserv = insert_avx_reg(elem);
        mov_literal_to_ymm(*elem->literal(), avx_reg_to_ymm(*elem->avx_reg()));
    }

    void Emitter::mov_stack_offset_to_avx_reg(StackElemRef const elem)
    {
        hx_mark("@F2181 mov_stack_offset_to_avx_reg");
        MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
        auto const reserv = insert_avx_reg(elem);
        as_.vmovaps(
            avx_reg_to_ymm(*elem->avx_reg()),
            stack_offset_to_mem(*elem->stack_offset()));
    }

    void Emitter::mov_avx_reg_to_stack_offset(StackElemRef elem)
    {
        hx_mark("@F2190 mov_avx_reg_to_stack_offset");
        int32_t const preferred = elem->preferred_stack_offset();
        mov_avx_reg_to_stack_offset(std::move(elem), preferred);
    }

    void Emitter::mov_avx_reg_to_stack_offset(
        StackElemRef const elem, int32_t const preferred)
    {
        hx_mark("@F2197 mov_avx_reg_to_stack_offset");
        MONAD_DEBUG_ASSERT(elem->avx_reg().has_value());
        stack_.insert_stack_offset(elem, preferred, PrevLoc::AvxReg);
        auto const y = avx_reg_to_ymm(*elem->avx_reg());
        as_.vmovaps(stack_offset_to_mem(*elem->stack_offset()), y);
    }

    void Emitter::mov_general_reg_to_stack_offset(StackElem &elem)
    {
        hx_mark("@F2205 mov_general_reg_to_stack_offset");
        int32_t const preferred = elem.preferred_stack_offset();
        mov_general_reg_to_stack_offset(elem, preferred);
    }

    void Emitter::mov_general_reg_to_stack_offset(StackElemRef const elem)
    {
        hx_mark("@F2211 mov_general_reg_to_stack_offset");
        int32_t const preferred = elem->preferred_stack_offset();
        mov_general_reg_to_stack_offset(*elem, preferred);
    }

    void Emitter::mov_general_reg_to_stack_offset(
        StackElem &elem, int32_t const preferred)
    {
        hx_mark("@F2218 mov_general_reg_to_stack_offset");
        MONAD_DEBUG_ASSERT(elem.general_reg().has_value());
        stack_.insert_stack_offset(elem, preferred, PrevLoc::GprReg);
        mov_general_reg_to_mem(
            *elem.general_reg(), stack_offset_to_mem(*elem.stack_offset()));
    }

    void Emitter::mov_general_reg_to_stack_offset(
        StackElemRef const elem, int32_t const preferred)
    {
        hx_mark("@F2227 mov_general_reg_to_stack_offset");
        return mov_general_reg_to_stack_offset(*elem, preferred);
    }

    void Emitter::mov_literal_to_stack_offset(StackElemRef elem)
    {
        hx_mark("@F2232 mov_literal_to_stack_offset");
        int32_t const preferred = elem->preferred_stack_offset();
        mov_literal_to_stack_offset(std::move(elem), preferred);
    }

    void Emitter::mov_literal_to_stack_offset(
        StackElemRef const elem, int32_t const preferred)
    {
        hx_mark("@F2239 mov_literal_to_stack_offset");
        MONAD_DEBUG_ASSERT(elem->literal().has_value());
        // mov_literal_to_mem stores literals by first loading them into an avx
        // register, hence we set it as the previous location
        stack_.insert_stack_offset(elem, preferred, PrevLoc::AvxReg);
        mov_literal_to_mem<true, true>(
            elem, stack_offset_to_mem(*elem->stack_offset()));
        MONAD_DEBUG_ASSERT(elem->avx_reg().has_value());
    }

    void Emitter::mov_avx_reg_to_general_reg(StackElemRef elem)
    {
        hx_mark("@F2250 mov_avx_reg_to_general_reg");
        int32_t const preferred = elem->preferred_stack_offset();
        mov_avx_reg_to_general_reg(std::move(elem), preferred);
    }

    void Emitter::mov_avx_reg_to_general_reg(
        StackElemRef const elem, int32_t const preferred)
    {
        hx_mark("@F2257 mov_avx_reg_to_general_reg");
        mov_avx_reg_to_stack_offset(elem, preferred);
        mov_stack_offset_to_general_reg(elem);
    }

    void Emitter::mov_literal_to_general_reg(StackElemRef const elem)
    {
        hx_mark("@F2263 mov_literal_to_general_reg");
        MONAD_DEBUG_ASSERT(elem->literal().has_value());
        auto const reserv = insert_general_reg(elem);
        mov_literal_to_gpq256(
            *elem->literal(), general_reg_to_gpq256(*elem->general_reg()));
    }

    void Emitter::mov_stack_offset_to_general_reg(StackElemRef const elem)
    {
        hx_mark("@F2271 mov_stack_offset_to_general_reg");
        MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
        auto const reserv = insert_general_reg(elem);
        mov_stack_offset_to_gpq256(
            *elem->stack_offset(), general_reg_to_gpq256(*elem->general_reg()));
    }

    StackElem *
    Emitter::revertible_mov_stack_offset_to_general_reg(StackElemRef const elem)
    {
        hx_mark("@F2280 revertible_mov_stack_offset_to_general_reg");
        MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
        StackElem *spill_elem = stack_.has_free_general_reg()
                                    ? nullptr
                                    : stack_.spill_general_reg();

        auto reg_elem = [this] {
            auto [x, _, spill] = stack_.alloc_general_reg();
            MONAD_DEBUG_ASSERT(!spill.has_value());
            return x;
        };
        stack_.move_general_reg(*reg_elem(), *elem);

        if (spill_elem != nullptr) {
            hx_mark("@L2293");
            MONAD_DEBUG_ASSERT(spill_elem->stack_offset().has_value());
            mov_general_reg_to_mem(
                *elem->general_reg(),
                stack_offset_to_mem(*spill_elem->stack_offset()));
        }
        mov_stack_offset_to_gpq256(
            *elem->stack_offset(), general_reg_to_gpq256(*elem->general_reg()));

        return spill_elem;
    }

    void Emitter::mov_mem_be_to_general_reg(x86::Mem m, StackElemRef const e)
    {
        hx_mark("@F2306 mov_mem_be_to_general_reg");
        MONAD_DEBUG_ASSERT(e->general_reg().has_value());
        auto const &gpq = general_reg_to_gpq256(*e->general_reg());
        for (size_t i = 0; i < 4; ++i) {
            hx_mark("@L2309");
            as_.movbe(gpq[3 - i], m);
            m.addOffset(8);
        }
    }

    void Emitter::bswap_to_ymm(
        std::variant<asmjit::x86::Ymm, asmjit::x86::Mem> const src,
        asmjit::x86::Ymm const dst)
    {
        hx_mark("@F2318 bswap_to_ymm");
        // Permute qwords:
        // {b0, ..., b7, b8, ..., b15, b16, ..., b23, b24, ..., b31} ->
        // {b24, ..., b31, b16, ..., b23, b8, ..., b15, b0, ..., b7}
        if (auto const *y = std::get_if<x86::Ymm>(&src)) {
            hx_mark("@L2322");
            as_.vpermq(dst, *y, 27);
        }
        else {
            hx_mark("@L2325");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(src));
            as_.vpermq(dst, std::get<x86::Mem>(src), 27);
        }
        auto const t = rodata_.add32(
            {0x0001020304050607,
             0x08090a0b0c0d0e0f,
             0x0001020304050607,
             0x08090a0b0c0d0e0f});
        // Permute bytes:
        // {b24, ..., b31, b16, ..., b23, b8, ..., b15, b0, ..., b7} ->
        // {b31, ..., b24, b23, ..., b16, b15, ..., b8, b7, ..., b0}
        as_.vpshufb(dst, dst, t);
    }

    void Emitter::mov_mem_be_to_avx_reg(x86::Mem const m, StackElemRef const e)
    {
        hx_mark("@F2341 mov_mem_be_to_avx_reg");
        MONAD_DEBUG_ASSERT(e->avx_reg().has_value());
        bswap_to_ymm(m, avx_reg_to_ymm(*e->avx_reg()));
    }

    StackElemRef Emitter::read_mem_be(x86::Mem const m)
    {
        hx_mark("@F2347 read_mem_be");
        if (stack_.has_free_general_reg()) {
            hx_mark("@L2348");
            auto [dst, _] = alloc_general_reg();
            mov_mem_be_to_general_reg(m, dst);
            return dst;
        }
        else {
            hx_mark("@L2353");
            auto [dst, _] = alloc_avx_reg();
            mov_mem_be_to_avx_reg(m, dst);
            return dst;
        }
    }

    void Emitter::mov_stack_elem_to_mem_be(StackElemRef const e, x86::Mem m)
    {
        hx_mark("@F2361 mov_stack_elem_to_mem_be");
        if (e->literal()) {
            hx_mark("@L2362");
            auto const x = bswap(e->literal()->value);
            mov_literal_to_mem<false>(Literal{x}, m);
        }
        else if (e->general_reg()) {
            hx_mark("@L2366");
            auto const &gpq = general_reg_to_gpq256(*e->general_reg());
            for (size_t i = 0; i < 4; ++i) {
                hx_mark("@L2368");
                as_.movbe(m, gpq[3 - i]);
                m.addOffset(8);
            }
        }
        else {
            hx_mark("@L2373");
            AvxRegReserv const e_reserv{e};
            auto [tmp_elem, reserv] = alloc_avx_reg();
            auto const y = avx_reg_to_ymm(*tmp_elem->avx_reg());
            if (e->avx_reg()) {
                hx_mark("@L2377");
                bswap_to_ymm(avx_reg_to_ymm(*e->avx_reg()), y);
            }
            else {
                hx_mark("@L2380");
                MONAD_DEBUG_ASSERT(e->stack_offset().has_value());
                bswap_to_ymm(stack_offset_to_mem(*e->stack_offset()), y);
            }
            as_.vmovups(m, y);
        }
    }

    // No discharge
    void Emitter::push(uint256_t const &x)
    {
        hx_mark("@F2390 push");
        stack_.push_literal(x);
    }

    // No discharge
    void Emitter::pop()
    {
        hx_mark("@F2396 pop");
        stack_.pop();
    }

    // No discharge
    void Emitter::dup(uint8_t const dup_ix)
    {
        hx_mark("@F2402 dup");
        MONAD_ASSERT(dup_ix > 0);
        stack_.dup(stack_.top_index() + 1 - static_cast<int32_t>(dup_ix));
    }

    // No discharge
    void Emitter::swap(uint8_t const swap_ix)
    {
        hx_mark("@F2409 swap");
        MONAD_ASSERT(swap_ix > 0);
        stack_.swap(stack_.top_index() - static_cast<int32_t>(swap_ix));
    }

    // Discharge through `lt` overload
    void Emitter::lt()
    {
        hx_mark("@F2416 lt");
        auto left = stack_.pop();
        auto right = stack_.pop();
        lt(std::move(left), std::move(right));
    }

    // Discharge through `lt` overload
    void Emitter::gt()
    {
        hx_mark("@F2424 gt");
        auto left = stack_.pop();
        auto right = stack_.pop();
        lt(std::move(right), std::move(left));
    }

    // Discharge through `slt` overload
    void Emitter::slt()
    {
        hx_mark("@F2432 slt");
        auto left = stack_.pop();
        auto right = stack_.pop();
        slt(std::move(left), std::move(right));
    }

    // Discharge through `slt` overload
    void Emitter::sgt()
    {
        hx_mark("@F2440 sgt");
        auto left = stack_.pop();
        auto right = stack_.pop();
        slt(std::move(right), std::move(left));
    }

    // Discharge through `sub` overload
    void Emitter::sub()
    {
        hx_mark("@F2448 sub");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(sub(std::move(left), std::move(right), {}));
    }

    // Discharge
    template <typename... LiveSet>
    StackElemRef Emitter::sub(
        StackElemRef pre_dst, StackElemRef pre_src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2459 sub");
        if (pre_dst->literal()) {
            hx_mark("@L2460");
            if (pre_src->literal()) {
                hx_mark("@L2461");
                auto const &x = pre_dst->literal()->value;
                auto const &y = pre_src->literal()->value;
                return stack_.alloc_literal({x - y});
            }
        }
        else if (pre_src->literal() && pre_src->literal()->value == 0) {
            hx_mark("@L2467");
            return pre_dst;
        }

        {
            hx_mark("@L2471");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, dst_loc, src, src_loc] = get_general_dest_and_source(
            false, std::move(pre_dst), std::move(pre_src), live);

        GENERAL_BIN_INSTR(sub, sbb)
        (dst, dst_loc, src, src_loc, [](size_t i, uint64_t x) {
            return i == 0 && x == 0;
        });

        return dst;
    }

    // Discharge through `add` overload
    void Emitter::add()
    {
        hx_mark("@F2491 add");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(add(std::move(left), std::move(right), {}));
    }

    // Discharge
    template <typename... LiveSet>
    StackElemRef Emitter::add(
        StackElemRef pre_dst, StackElemRef pre_src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2502 add");
        if (pre_dst->literal()) {
            hx_mark("@L2503");
            if (pre_src->literal()) {
                hx_mark("@L2504");
                auto const &x = pre_dst->literal()->value;
                auto const &y = pre_src->literal()->value;
                return stack_.alloc_literal({x + y});
            }
            else if (pre_dst->literal()->value == 0) {
                hx_mark("@L2509");
                return pre_src;
            }
        }
        else if (pre_src->literal() && pre_src->literal()->value == 0) {
            hx_mark("@L2513");
            return pre_dst;
        }

        {
            hx_mark("@L2517");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, dst_loc, src, src_loc] = get_general_dest_and_source(
            true, std::move(pre_dst), std::move(pre_src), live);

        GENERAL_BIN_INSTR(add, adc)
        (dst, dst_loc, src, src_loc, [](size_t i, uint64_t x) {
            return i == 0 && x == 0;
        });

        return dst;
    }

    // Discharge
    void Emitter::byte()
    {
        hx_mark("@F2537 byte");
        auto ix = stack_.pop();
        auto src = stack_.pop();

        if (ix->literal()) {
            hx_mark("@L2541");
            auto const &i = ix->literal()->value;
            if (i >= 32) {
                hx_mark("@L2543");
                push(0);
                return;
            }
            if (src->literal()) {
                hx_mark("@L2547");
                auto const &x = src->literal()->value;
                push(monad::byte(i, x));
                return;
            }
        }

        {
            hx_mark("@L2554");
            RegReserv const ix_reserv{ix};
            RegReserv const src_reserv{src};
            discharge_deferred_comparison();
        }

        if (src->general_reg()) {
            hx_mark("@L2560");
            if (ix->literal()) {
                hx_mark("@L2561");
                byte_literal_ix_general_reg_src(
                    std::move(ix), std::move(src), {});
            }
            else {
                hx_mark("@L2565");
                byte_non_literal_ix_general_reg_src(
                    std::move(ix), std::move(src), {});
            }
        }
        else if (src->avx_reg()) {
            hx_mark("@L2570");
            if (ix->literal()) {
                hx_mark("@L2571");
                byte_literal_ix_avx_reg_src(std::move(ix), std::move(src));
            }
            else {
                hx_mark("@L2574");
                byte_non_literal_ix_avx_reg_src(
                    std::move(ix), std::move(src), {});
            }
        }
        else {
            hx_mark("@L2579");
            if (ix->literal()) {
                hx_mark("@L2580");
                MONAD_DEBUG_ASSERT(src->stack_offset().has_value());
                byte_literal_ix_stack_offset_src(std::move(ix), std::move(src));
            }
            else {
                hx_mark("@L2584");
                byte_non_literal_ix_literal_or_stack_offset_src(
                    std::move(ix), std::move(src), {});
            }
        }
    }

    // Discharge
    void Emitter::signextend()
    {
        hx_mark("@F2593 signextend");
        auto ix = stack_.pop();
        auto src = stack_.pop();

        if (ix->literal() && src->literal()) {
            hx_mark("@L2597");
            auto const &i = ix->literal()->value;
            auto const &x = src->literal()->value;
            push(monad::signextend(i, x));
            return;
        }

        {
            hx_mark("@L2604");
            RegReserv const ix_reserv{ix};
            RegReserv const src_reserv{src};
            discharge_deferred_comparison();
        }

        if (ix->literal()) {
            hx_mark("@L2610");
            auto const lit = ix->literal()->value;
            ix.reset(); // Potentially Clear locations
            signextend_by_literal_ix(lit, std::move(src), {});
        }
        else {
            hx_mark("@L2615");
            signextend_by_non_literal(std::move(ix), std::move(src), {});
        }
    }

    // Discharge through `shl` overload
    void Emitter::shl()
    {
        hx_mark("@F2622 shl");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(shl(std::move(left), std::move(right), {}));
    }

    // Discharge through `shift_by_stack_elem`
    template <typename... LiveSet>
    StackElemRef Emitter::shl(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2633 shl");
        if (shift->literal() && value->literal()) {
            hx_mark("@L2634");
            auto const &i = shift->literal()->value;
            auto const &x = value->literal()->value;
            return stack_.alloc_literal({x << i});
        }

        return shift_by_stack_elem<ShiftType::SHL>(
            std::move(shift), std::move(value), live);
    }

    // Discharge through `shr` overload
    void Emitter::shr()
    {
        hx_mark("@F2646 shr");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(shr(std::move(left), std::move(right), {}));
    }

    // Discharge through `shift_by_stack_elem`
    template <typename... LiveSet>
    StackElemRef Emitter::shr(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2657 shr");
        if (shift->literal() && value->literal()) {
            hx_mark("@L2658");
            auto const &i = shift->literal()->value;
            auto const &x = value->literal()->value;
            return stack_.alloc_literal({x >> i});
        }

        return shift_by_stack_elem<ShiftType::SHR>(
            std::move(shift), std::move(value), live);
    }

    // Discharge through `sar` overload
    void Emitter::sar()
    {
        hx_mark("@F2670 sar");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(sar(std::move(left), std::move(right), {}));
    }

    // Discharge through `shift_by_stack_elem`
    template <typename... LiveSet>
    StackElemRef Emitter::sar(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2681 sar");
        if (shift->literal() && value->literal()) {
            hx_mark("@L2682");
            auto const &i = shift->literal()->value;
            auto const &x = value->literal()->value;
            return stack_.alloc_literal({monad::sar(i, x)});
        }
        return shift_by_stack_elem<ShiftType::SAR>(
            std::move(shift), std::move(value), live);
    }

    // Discharge
    void Emitter::clz()
    {
        hx_mark("@F2693 clz");
        auto elem = stack_.pop();

        if (elem->literal()) {
            hx_mark("@L2696");
            auto const &x = elem->literal()->value;
            push(countl_zero(x));
            return;
        }

        discharge_deferred_comparison();

        if (elem->general_reg()) {
            hx_mark("@L2704");
            Gpq256 const &src = general_reg_to_gpq256(*elem->general_reg());
            auto [dst, _] = alloc_or_release_general_reg(std::move(elem), {});
            array_leading_zeros(
                src, general_reg_to_gpq256(*dst->general_reg()));
            stack_.push(std::move(dst));
        }
        else if (elem->stack_offset()) {
            hx_mark("@L2711");
            auto [dst, _] = alloc_general_reg();
            array_leading_zeros(
                stack_offset_to_mem256(*elem->stack_offset()),
                general_reg_to_gpq256(*dst->general_reg()));
            stack_.push(std::move(dst));
        }
        else {
            hx_mark("@L2718");
            MONAD_ASSERT(elem->avx_reg().has_value());
            AvxRegReserv const elem_reserv{elem};
            auto [dst, dst_reserv] = alloc_general_reg();
            auto [tmp, tmp_reserv] = alloc_avx_reg();
            Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
            auto const x = avx_reg_to_xmm(*elem->avx_reg());
            auto const t = avx_reg_to_xmm(*tmp->avx_reg());
            // Faster than spilling and reloading the words
            as_.vmovq(gpq[0], x);
            as_.vpextrq(gpq[1], x, 1);
            as_.vextracti128(t, avx_reg_to_ymm(*elem->avx_reg()), 1);
            as_.vmovq(gpq[2], t);
            as_.vpextrq(gpq[3], t, 1);
            array_leading_zeros(gpq, gpq);
            stack_.push(std::move(dst));
        }
    }

    // Discharge through `and_` overload
    void Emitter::and_()
    {
        hx_mark("@F2739 and_");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(and_(std::move(left), std::move(right), {}));
    }

    // Discharge
    template <typename... LiveSet>
    StackElemRef Emitter::and_(
        StackElemRef pre_dst, StackElemRef pre_src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2750 and_");
        if (pre_dst->literal()) {
            hx_mark("@L2751");
            if (pre_src->literal()) {
                hx_mark("@L2752");
                auto const &x = pre_dst->literal()->value;
                auto const &y = pre_src->literal()->value;
                return stack_.alloc_literal({x & y});
            }
            // a & 1...1 ==> a
            if (pre_dst->literal()->value ==
                std::numeric_limits<uint256_t>::max()) {
                    hx_mark("@L2759");
                return pre_src;
            }
            // a & 0...0 ==> 0
            if (pre_dst->literal()->value == 0) {
                hx_mark("@L2763");
                return stack_.alloc_literal({0});
            }
        }
        else if (pre_src->literal()) {
            hx_mark("@L2767");
            // 1...1 & b ==> b
            if (pre_src->literal()->value ==
                std::numeric_limits<uint256_t>::max()) {
                    hx_mark("@L2770");
                return pre_dst;
            }
            // 0...0 & b ==> 0
            if (pre_src->literal()->value == 0) {
                hx_mark("@L2774");
                return stack_.alloc_literal({0});
            }
        }

        {
            hx_mark("@L2779");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, left, left_loc, right, right_loc] =
            get_avx_or_general_arguments_commutative(
                std::move(pre_dst), std::move(pre_src), live);

        AVX_OR_GENERAL_BIN_INSTR(and_, vpand)
        (dst, left, left_loc, right, right_loc, [](size_t, uint64_t x) {
            return x == std::numeric_limits<uint64_t>::max();
        });

        return dst;
    }

    // Discharge through `or_` overload
    void Emitter::or_()
    {
        hx_mark("@F2800 or_");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(or_(std::move(left), std::move(right), {}));
    }

    // Discharge
    template <typename... LiveSet>
    StackElemRef Emitter::or_(
        StackElemRef pre_dst, StackElemRef pre_src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2811 or_");
        if (pre_dst->literal()) {
            hx_mark("@L2812");
            if (pre_src->literal()) {
                hx_mark("@L2813");
                auto const &x = pre_dst->literal()->value;
                auto const &y = pre_src->literal()->value;
                return stack_.alloc_literal({x | y});
            }
            // a | 0...0 ==> a
            if (pre_dst->literal()->value == 0) {
                hx_mark("@L2819");
                return pre_src;
            }
            // a | 1...1 ==> 1...1
            if (pre_dst->literal()->value ==
                std::numeric_limits<uint256_t>::max()) {
                    hx_mark("@L2824");
                return stack_.alloc_literal(
                    {std::numeric_limits<uint256_t>::max()});
            }
        }
        else if (pre_src->literal()) {
            hx_mark("@L2829");
            // 0...0 & b ==> b
            if (pre_src->literal()->value == 0) {
                hx_mark("@L2831");
                return pre_dst;
            }
            // 1...1 | b ==> 1...1
            if (pre_src->literal()->value ==
                std::numeric_limits<uint256_t>::max()) {
                    hx_mark("@L2836");
                return stack_.alloc_literal(
                    {std::numeric_limits<uint256_t>::max()});
            }
        }

        {
            hx_mark("@L2842");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, left, left_loc, right, right_loc] =
            get_avx_or_general_arguments_commutative(
                std::move(pre_dst), std::move(pre_src), live);

        AVX_OR_GENERAL_BIN_INSTR(or_, vpor)
        (dst, left, left_loc, right, right_loc, [](size_t, uint64_t x) {
            return x == 0;
        });

        return dst;
    }

    // Discharge through `xor_` overload
    void Emitter::xor_()
    {
        hx_mark("@F2863 xor_");
        auto left = stack_.pop();
        auto right = stack_.pop();
        stack_.push(xor_(std::move(left), std::move(right), {}));
    }

    // Discharge
    template <typename... LiveSet>
    StackElemRef Emitter::xor_(
        StackElemRef pre_dst, StackElemRef pre_src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F2874 xor_");
        if (pre_dst == pre_src) {
            hx_mark("@L2875");
            return stack_.alloc_literal({0});
        }
        if (pre_dst->literal()) {
            hx_mark("@L2878");
            if (pre_src->literal()) {
                hx_mark("@L2879");
                auto const &x = pre_dst->literal()->value;
                auto const &y = pre_src->literal()->value;
                return stack_.alloc_literal({x ^ y});
            }
            if (!pre_dst->literal()->value) {
                hx_mark("@L2884");
                return pre_src;
            }
        }
        if (pre_src->literal() && !pre_src->literal()->value) {
            hx_mark("@L2888");
            return pre_dst;
        }

        {
            hx_mark("@L2892");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, left, left_loc, right, right_loc] =
            get_avx_or_general_arguments_commutative(
                std::move(pre_dst), std::move(pre_src), live);

        AVX_OR_GENERAL_BIN_INSTR(xor_, vpxor)
        (dst, left, left_loc, right, right_loc, [](size_t, uint64_t x) {
            return x == 0;
        });

        return dst;
    }

    // Discharge
    void Emitter::eq()
    {
        hx_mark("@F2913 eq");
        auto pre_dst = stack_.pop();
        auto pre_src = stack_.pop();

        if (pre_dst == pre_src) {
            hx_mark("@L2917");
            push(1);
            return;
        }
        if (pre_dst->literal() && pre_src->literal()) {
            hx_mark("@L2921");
            auto const &x = pre_dst->literal()->value;
            auto const &y = pre_src->literal()->value;
            push(x == y);
            return;
        }
        if (pre_dst->literal() && !pre_dst->literal()->value) {
            hx_mark("@L2927");
            push_iszero(std::move(pre_src));
            return;
        }
        if (pre_src->literal() && !pre_src->literal()->value) {
            hx_mark("@L2931");
            push_iszero(std::move(pre_dst));
            return;
        }

        {
            hx_mark("@L2936");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, left, left_loc, right, right_loc] =
            get_avx_or_general_arguments_commutative(
                std::move(pre_dst), std::move(pre_src), {});

        AVX_OR_GENERAL_BIN_INSTR(xor_, vpxor)
        (dst, left, left_loc, right, right_loc, [](size_t, uint64_t x) {
            return x == 0;
        });

        if (left_loc == LocationType::AvxReg) {
            hx_mark("@L2952");
            x86::Ymm const &y = avx_reg_to_ymm(*dst->avx_reg());
            as_.vptest(y, y);
        }
        else {
            hx_mark("@L2956");
            MONAD_DEBUG_ASSERT(left_loc == LocationType::GeneralReg);
            Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
            as_.or_(gpq[0], gpq[1]);
            as_.or_(gpq[2], gpq[3]);
            as_.or_(gpq[0], gpq[2]);
        }
        stack_.push_deferred_comparison(Comparison::Equal);
    }

    // Discharge through push_iszero
    void Emitter::iszero()
    {
        hx_mark("@F2968 iszero");
        auto elem = stack_.pop();
        push_iszero(std::move(elem));
    }

    // Discharge when returning Comparison
    std::variant<Comparison, StackElemRef>
    Emitter::iszero(StackElemRef const elem)
    {
        hx_mark("@F2976 iszero");
        if (elem->literal()) {
            hx_mark("@L2977");
            return stack_.alloc_literal({!elem->literal()->value});
        }
        if (auto neg = stack_.negate_if_deferred_comparison(elem)) {
            hx_mark("@L2980");
            return neg;
        }

        {
            hx_mark("@L2984");
            RegReserv const elem_reserv{elem};
            discharge_deferred_comparison();
        }

        auto [left, right, loc] = get_una_arguments(false, elem, {});
        MONAD_DEBUG_ASSERT(left == right);
        if (loc == LocationType::AvxReg) {
            hx_mark("@L2991");
            x86::Ymm const y = avx_reg_to_ymm(*left->avx_reg());
            as_.vptest(y, y);
        }
        else {
            hx_mark("@L2995");
            MONAD_DEBUG_ASSERT(loc == LocationType::GeneralReg);
            Gpq256 const &gpq = general_reg_to_gpq256(*left->general_reg());
            if (is_live(left, {})) {
                hx_mark("@L2998");
                as_.mov(x86::rax, gpq[0]);
                for (size_t i = 1; i < 4; ++i) {
                    hx_mark("@L3000");
                    as_.or_(x86::rax, gpq[i]);
                }
            }
            else {
                hx_mark("@L3004");
                as_.or_(gpq[0], gpq[1]);
                as_.or_(gpq[2], gpq[3]);
                as_.or_(gpq[0], gpq[2]);
            }
        }

        return Comparison::Equal;
    }

    // Discharge through iszero
    void Emitter::push_iszero(StackElemRef elem)
    {
        hx_mark("@F3016 push_iszero");
        auto res = iszero(std::move(elem));
        if (std::holds_alternative<Comparison>(res)) {
            hx_mark("@L3018");
            stack_.push_deferred_comparison(std::get<Comparison>(res));
        }
        else {
            hx_mark("@L3021");
            MONAD_DEBUG_ASSERT(std::holds_alternative<StackElemRef>(res));
            stack_.push(std::get<StackElemRef>(res));
        }
    }

    // Discharge
    // Returns null without discharging when `e` is deferred comparison,
    // which cannot be signed.
    std::optional<Comparison> Emitter::issigned(StackElemRef const e)
    {
        hx_mark("@F3031 issigned");
        // Unimplemented for literal, because it is not needed.
        MONAD_DEBUG_ASSERT(!e->literal().has_value());

        auto const dc = stack_.peek_deferred_comparison();
        if (e.get() == dc.stack_elem || e.get() == dc.negated_stack_elem) {
            hx_mark("@L3036");
            return std::nullopt;
        }

        {
            hx_mark("@L3040");
            RegReserv const e_reserv{e};
            discharge_deferred_comparison();
        }

        if (e->general_reg()) {
            hx_mark("@L3045");
            auto const &gpq = general_reg_to_gpq256(*e->general_reg());
            as_.test(gpq[3], gpq[3]);
            return Comparison::Less;
        }
        if (e->avx_reg()) {
            hx_mark("@L3050");
            auto const y = avx_reg_to_ymm(*e->avx_reg());
            as_.vmovmskpd(x86::eax, y);
            as_.test(x86::eax, 8);
            return Comparison::NotEqual;
        }
        MONAD_DEBUG_ASSERT(e->stack_offset().has_value());
        auto m = stack_offset_to_mem(*e->stack_offset());
        m.addOffset(24);
        as_.mov(x86::rax, m);
        as_.test(x86::rax, x86::rax);
        return Comparison::Less;
    }

    // Discharge
    void Emitter::not_()
    {
        hx_mark("@F3066 not_");
        auto const elem = stack_.pop();
        if (elem->literal()) {
            hx_mark("@L3068");
            push(~elem->literal()->value);
            return;
        }

        {
            hx_mark("@L3073");
            RegReserv const elem_reserv{elem};
            discharge_deferred_comparison();
        }

        auto [left, right, loc] = get_una_arguments(true, elem, {});
        if (loc == LocationType::AvxReg) {
            hx_mark("@L3079");
            x86::Ymm const y_left = avx_reg_to_ymm(*left->avx_reg());
            x86::Ymm const y_right = avx_reg_to_ymm(*right->avx_reg());
            if (stack_.has_free_avx_reg()) {
                hx_mark("@L3082");
                auto [tmp, tmp_reserv] = alloc_avx_reg();
                x86::Ymm const y_tmp = avx_reg_to_ymm(*tmp->avx_reg());
                as_.vpcmpeqd(y_tmp, y_tmp, y_tmp);
                as_.vpxor(y_left, y_right, y_tmp);
            }
            else {
                hx_mark("@L3088");
                auto const m =
                    rodata_.add32(std::numeric_limits<uint256_t>::max());
                as_.vpxor(y_left, y_right, m);
            }
        }
        else {
            hx_mark("@L3094");
            MONAD_DEBUG_ASSERT(loc == LocationType::GeneralReg);
            MONAD_DEBUG_ASSERT(left == right);
            Gpq256 const &gpq = general_reg_to_gpq256(*left->general_reg());
            for (size_t i = 0; i < 4; ++i) {
                hx_mark("@L3098");
                as_.not_(gpq[i]);
            }
        }
        stack_.push(std::move(left));
    }

    // Discharge
    void Emitter::gas(int64_t const remaining_base_gas)
    {
        hx_mark("@F3107 gas");
        MONAD_DEBUG_ASSERT(remaining_base_gas >= 0);
        discharge_deferred_comparison();
        auto [dst, _] = alloc_general_reg();
        Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
        as_.mov(
            gpq[0],
            x86::qword_ptr(reg_context, runtime::context_offset_gas_remaining));
        if (remaining_base_gas != 0) {
            hx_mark("@L3115");
            as_.add(gpq[0], remaining_base_gas);
        }
        as_.xor_(gpq[1].r32(), gpq[1].r32());
        as_.xor_(gpq[2].r32(), gpq[2].r32());
        as_.xor_(gpq[3].r32(), gpq[3].r32());
        stack_.push(std::move(dst));
    }

    // No discharge
    void Emitter::address()
    {
        hx_mark("@F3126 address");
        read_context_address(runtime::context_offset_env_recipient);
    }

    // No discharge
    void Emitter::caller()
    {
        hx_mark("@F3132 caller");
        read_context_address(runtime::context_offset_env_sender);
    }

    // No discharge
    void Emitter::callvalue()
    {
        hx_mark("@F3138 callvalue");
        read_context_word(runtime::context_offset_env_value);
    }

    // No discharge
    void Emitter::calldatasize()
    {
        hx_mark("@F3144 calldatasize");
        static_assert(
            sizeof(runtime::Environment::input_data_size) == sizeof(uint32_t));
        read_context_uint32_to_word(
            runtime::context_offset_env_input_data_size);
    }

    // No discharge
    void Emitter::returndatasize()
    {
        hx_mark("@F3153 returndatasize");
        static_assert(
            sizeof(runtime::Environment::return_data_size) == sizeof(uint64_t));
        read_context_uint32_to_word(
            runtime::context_offset_env_return_data_size);
    }

    // No discharge
    void Emitter::msize()
    {
        hx_mark("@F3162 msize");
        static_assert(sizeof(runtime::Memory::size) == sizeof(uint32_t));
        read_context_uint32_to_word(runtime::context_offset_memory_size);
    }

    // No discharge
    void Emitter::codesize()
    {
        hx_mark("@F3169 codesize");
        stack_.push_literal(*bytecode_size_);
    }

    // No discharge
    void Emitter::origin()
    {
        hx_mark("@F3175 origin");
        read_evmc_tx_context_address(offsetof(evmc_tx_context, tx_origin));
    }

    // No discharge
    void Emitter::gasprice()
    {
        hx_mark("@F3181 gasprice");
        read_evmc_tx_context_word(offsetof(evmc_tx_context, tx_gas_price));
    }

    // No discharge
    void Emitter::gaslimit()
    {
        hx_mark("@F3187 gaslimit");
        read_evmc_tx_context_uint64_to_word(
            offsetof(evmc_tx_context, block_gas_limit));
    }

    // No discharge
    void Emitter::coinbase()
    {
        hx_mark("@F3194 coinbase");
        read_evmc_tx_context_address(offsetof(evmc_tx_context, block_coinbase));
    }

    // No discharge
    void Emitter::timestamp()
    {
        hx_mark("@F3200 timestamp");
        read_evmc_tx_context_uint64_to_word(
            offsetof(evmc_tx_context, block_timestamp));
    }

    // No discharge
    void Emitter::number()
    {
        hx_mark("@F3207 number");
        read_evmc_tx_context_uint64_to_word(
            offsetof(evmc_tx_context, block_number));
    }

    // No discharge
    void Emitter::prevrandao()
    {
        hx_mark("@F3214 prevrandao");
        read_evmc_tx_context_word(offsetof(evmc_tx_context, block_prev_randao));
    }

    // No discharge
    void Emitter::chainid()
    {
        hx_mark("@F3220 chainid");
        read_evmc_tx_context_word(offsetof(evmc_tx_context, chain_id));
    }

    // No discharge
    void Emitter::basefee()
    {
        hx_mark("@F3226 basefee");
        read_evmc_tx_context_word(offsetof(evmc_tx_context, block_base_fee));
    }

    // No discharge
    void Emitter::blobbasefee()
    {
        hx_mark("@F3232 blobbasefee");
        read_evmc_tx_context_word(offsetof(evmc_tx_context, blob_base_fee));
    }

    // Discharge
    void Emitter::calldataload()
    {
        hx_mark("@F3238 calldataload");
        {
            hx_mark("@L3239");
            RegReserv const offset_reserv{stack_.get(stack_.top_index())};
            discharge_deferred_comparison();
        }
        spill_avx_reg_range(14);

        auto *const volatile_elem =
            stack_.general_reg_stack_elem(volatile_general_reg);

        auto offset = stack_.pop();

        if (volatile_elem) {
            hx_mark("@L3250");
            // The `volatile_elem` is still pointing to a live stack elem,
            // because `offset` is live.
            auto e = release_general_reg(*volatile_elem, {});
            if (offset.get() == volatile_elem && !offset->general_reg()) {
                hx_mark("@L3254");
                // The offset may be the volatile general reg:
                offset = std::move(e);
            }
        }

        // Make sure reg_context is rbx, because the function
        // monad_vm_runtime_load_bounded_le_raw expects context to be passed
        // in rbx.
        static_assert(reg_context == x86::rbx);

        // It is later assumed that volatile_general_reg coincides with
        // rdi_general_reg and rsi_general_reg.
        MONAD_DEBUG_ASSERT(rdi_general_reg == volatile_general_reg);
        MONAD_DEBUG_ASSERT(rsi_general_reg == volatile_general_reg);

        auto const done_label = as_.newLabel();

        offset->reserve_avx_reg();
        auto [result, reserv] = alloc_avx_reg();
        offset->unreserve_avx_reg();
        auto const result_y = avx_reg_to_ymm(*result->avx_reg());
        as_.vpxor(result_y, result_y, result_y);

        auto const offset_op =
            is_bounded_by_bits<32>(std::move(offset), done_label, {});

        auto const data_offset = runtime::context_offset_env_input_data;
        auto const size_offset = runtime::context_offset_env_input_data_size;

        if (auto const *lit = std::get_if<uint64_t>(&offset_op)) {
            hx_mark("@L3284");
            as_.mov(x86::rdi, x86::qword_ptr(reg_context, data_offset));
            as_.mov(x86::esi, x86::dword_ptr(reg_context, size_offset));

            if (*lit <= std::numeric_limits<int32_t>::max()) {
                hx_mark("@L3288");
                if (*lit != 0) {
                    hx_mark("@L3289");
                    as_.add(x86::rdi, *lit);
                    as_.sub(x86::rsi, *lit);
                }
            }
            else {
                hx_mark("@L3294");
                as_.mov(x86::rax, rodata_.add8(*lit));
                as_.add(x86::rdi, x86::rax);
                as_.sub(x86::rsi, x86::rax);
            }
        }
        else if (std::holds_alternative<x86::Gpq>(offset_op)) {
            hx_mark("@L3300");
            auto const r = std::get<x86::Gpq>(offset_op);
            // We always have `r` not part of the volatile general reg:
            // According to `is_bounded_by_bits`, if `r` is part of volatile
            // general reg, then the stack elem `offset` is live (the case
            // where `gpq[0]` is returned by `is_bounded_by_bits`). But
            // `offset` can only hold the volatile general reg in case the
            // `offset` was updated to be the released stack elem `e`. This
            // stack elem is not on the stack and therefore `is_live` was false
            // in `is_bounded_by_bits`. Hence `r` cannot be part of the volatile
            // general reg and in particular cannot be rdi or rsi, so no need to
            // worry about overwriting the value of `r` here.
            MONAD_DEBUG_ASSERT(r != x86::rdi && r != x86::rsi);
            as_.mov(x86::rdi, x86::qword_ptr(reg_context, data_offset));
            as_.mov(x86::esi, x86::dword_ptr(reg_context, size_offset));
            as_.add(x86::rdi, r);
            as_.sub(x86::rsi, r);
        }
        else {
            hx_mark("@L3318");
            MONAD_DEBUG_ASSERT(
                std::holds_alternative<std::monostate>(offset_op));
            as_.mov(x86::rdi, x86::qword_ptr(reg_context, data_offset));
            as_.mov(x86::esi, x86::dword_ptr(reg_context, size_offset));
        }

        auto const load_bounded_label = as_.newLabel();
        auto const load_bounded_fn =
            rodata_.add_external_function(monad_vm_runtime_load_bounded_le_raw);
        auto const bswap_label = as_.newLabel();
        load_bounded_le_handlers_.emplace_back(
            load_bounded_label, load_bounded_fn, bswap_label);

        as_.cmp(x86::rsi, 32);
        as_.jl(load_bounded_label);
        as_.vmovups(x86::ymm15, x86::byte_ptr(x86::rdi));

        as_.bind(bswap_label);
        bswap_to_ymm(x86::ymm15, result_y);

        as_.bind(done_label);
        stack_.push(std::move(result));
    }

    // Discharge through `touch_memory`.
    template <runtime::Memory::Version memory_version>
    void Emitter::mload()
    {
        hx_mark("@F3346 mload");
        auto offset = stack_.pop();
        auto mem = touch_memory<memory_version>(std::move(offset), 32, {});
        if (mem) {
            hx_mark("@L3349");
            stack_.push(read_mem_be(*mem));
        }
        else {
            hx_mark("@L3352");
            stack_.push_literal(0);
        }
    }

    template void Emitter::mload<runtime::Memory::Version::V1>();
    template void Emitter::mload<runtime::Memory::Version::MIP3>();

    // Discharge through `touch_memory`.
    template <runtime::Memory::Version memory_version>
    void Emitter::mstore()
    {
        hx_mark("@F3363 mstore");
        auto offset = stack_.pop();
        auto mem = touch_memory<memory_version>(std::move(offset), 32, {});
        auto value = stack_.pop();
        if (mem) {
            hx_mark("@L3367");
            mov_stack_elem_to_mem_be(std::move(value), *mem);
        }
    }

    template void Emitter::mstore<runtime::Memory::Version::V1>();
    template void Emitter::mstore<runtime::Memory::Version::MIP3>();

    // Discharge through `touch_memory`.
    template <runtime::Memory::Version memory_version>
    void Emitter::mstore8()
    {
        hx_mark("@F3378 mstore8");
        auto offset = stack_.pop();
        auto mem = touch_memory<memory_version>(std::move(offset), 1, {});
        auto const value = stack_.pop();
        if (!mem) {
            hx_mark("@L3382");
            return;
        }
        mem->setSize(1);
        if (value->general_reg()) {
            hx_mark("@L3386");
            auto const &gpq = general_reg_to_gpq256(*value->general_reg());
            as_.mov(*mem, gpq[0].r8());
        }
        else if (value->literal()) {
            hx_mark("@L3390");
            uint8_t const b = static_cast<uint8_t>(value->literal()->value);
            as_.mov(*mem, b);
        }
        else if (value->avx_reg()) {
            hx_mark("@L3394");
            as_.vpextrb(*mem, avx_reg_to_xmm(*value->avx_reg()), 0);
        }
        else {
            hx_mark("@L3397");
            MONAD_DEBUG_ASSERT(value->stack_offset().has_value());
            auto src = stack_offset_to_mem(*value->stack_offset());
            src.setSize(4);
            if (stack_.has_free_general_reg()) {
                hx_mark("@L3401");
                auto [tmp, tmp_reserv] = alloc_general_reg();
                auto const &gpq = general_reg_to_gpq256(*tmp->general_reg());
                as_.mov(gpq[0].r32(), src);
                as_.mov(*mem, gpq[0].r8());
            }
            else {
                hx_mark("@L3407");
                auto [tmp, tmp_reserv] = alloc_avx_reg();
                auto const tmp_x = avx_reg_to_xmm(*tmp->avx_reg());
                as_.vmovd(tmp_x, src);
                as_.vpextrb(*mem, tmp_x, 0);
            }
        }
    }

    template void Emitter::mstore8<runtime::Memory::Version::V1>();
    template void Emitter::mstore8<runtime::Memory::Version::MIP3>();

    void Emitter::mul(int64_t const remaining_base_gas)
    {
        hx_mark("@F3420 mul");
        if (mul_optimized()) {
            hx_mark("@L3421");
            return;
        }
        call_runtime(remaining_base_gas, false, runtime::mul);
    }

    void Emitter::udiv(int64_t const remaining_base_gas)
    {
        hx_mark("@F3428 udiv");
        if (div_optimized<false>()) {
            hx_mark("@L3429");
            return;
        }
        call_runtime(remaining_base_gas, true, runtime::udiv);
    }

    void Emitter::sdiv(int64_t const remaining_base_gas)
    {
        hx_mark("@F3436 sdiv");
        if (div_optimized<true>()) {
            hx_mark("@L3437");
            return;
        }
        call_runtime(remaining_base_gas, true, runtime::sdiv);
    }

    void Emitter::umod(int64_t const remaining_base_gas)
    {
        hx_mark("@F3444 umod");
        if (mod_optimized<false>()) {
            hx_mark("@L3445");
            return;
        }
        call_runtime(remaining_base_gas, true, runtime::umod);
    }

    void Emitter::smod(int64_t const remaining_base_gas)
    {
        hx_mark("@F3452 smod");
        if (mod_optimized<true>()) {
            hx_mark("@L3453");
            return;
        }
        call_runtime(remaining_base_gas, true, runtime::smod);
    }

    void Emitter::addmod(int64_t const remaining_base_gas)
    {
        hx_mark("@F3460 addmod");
        if (addmod_opt()) {
            hx_mark("@L3461");
            return;
        }
        call_runtime(remaining_base_gas, true, runtime::addmod);
    }

    void Emitter::mulmod(int64_t const remaining_base_gas)
    {
        hx_mark("@F3468 mulmod");
        if (mulmod_opt()) {
            hx_mark("@L3469");
            return;
        }
        call_runtime(remaining_base_gas, true, runtime::mulmod);
    }

    // Discharge
    void Emitter::call_runtime_impl(RuntimeImpl &rt)
    {
        hx_mark("@F3477 call_runtime_impl");
        discharge_deferred_comparison();
        spill_caller_save_regs(rt.spill_avx_regs());
        size_t const n = rt.explicit_arg_count();
        for (size_t i = 0; i < n; ++i) {
            hx_mark("@L3481");
            rt.pass(stack_.pop());
        }
        rt.call_impl();
    }

    // Discharge
    void Emitter::jump()
    {
        hx_mark("@F3489 jump");
        auto e = stack_.pop();
        {
            hx_mark("@L3491");
            RegReserv const e_reserv{e};
            discharge_deferred_comparison();
        }
        jump_stack_elem_dest(std::move(e), {});
    }

    // Discharge indirectly with `jumpi_comparison`
    void Emitter::jumpi(basic_blocks::Block const &ft)
    {
        hx_mark("@F3500 jumpi");
        MONAD_DEBUG_ASSERT(ft.offset <= *bytecode_size_);
        // We spill the stack if the fall through block is a jumpdest, but also
        // in case the number of spills is not proportional to the number of
        // instructions in the fall through block and the fallthrough block
        // is terminated with `JUMPI`. This latter condition is to preserve
        // linear compile time, which would otherwise be quadratic, due to the
        // `JUMPI` instruction potentially spilling the same stack elements as
        // the predecessor block.
        bool const spill_stack =
            jump_dests_.contains(static_cast<byte_offset>(ft.offset)) ||
            (ft.terminator == basic_blocks::Terminator::JumpI &&
             stack_.missing_spill_count() > 3 + ft.instrs.size());
        if (spill_stack) {
            hx_mark("@L3513");
            jumpi_spill_fallthrough_stack();
        }
        else {
            hx_mark("@L3516");
            jumpi_keep_fallthrough_stack();
        }
    }

    // Discharge
    void Emitter::fallthrough()
    {
        hx_mark("@F3523 fallthrough");
        discharge_deferred_comparison();
        write_to_final_stack_offsets();
        adjust_by_stack_delta<false>();
    }

    // No discharge
    void Emitter::stop()
    {
        hx_mark("@F3531 stop");
        runtime_store_input_stack(*bytecode_size_);
        status_code(runtime::StatusCode::Success);
        as_.jmp(epilogue_label_);
    }

    // No discharge
    void Emitter::invalid_instruction()
    {
        hx_mark("@F3539 invalid_instruction");
        as_.jmp(error_label_);
    }

    // Discharge through `return_with_status_code`
    void Emitter::return_()
    {
        hx_mark("@F3545 return_");
        runtime_store_input_stack(*bytecode_size_);
        return_with_status_code(runtime::StatusCode::Success);
    }

    // Discharge through `return_with_status_code`
    void Emitter::revert()
    {
        hx_mark("@F3552 revert");
        return_with_status_code(runtime::StatusCode::Revert);
    }

    void Emitter::status_code(runtime::StatusCode const status)
    {
        hx_mark("@F3557 status_code");
        int32_t const c = static_cast<int32_t>(status);
        as_.mov(
            x86::qword_ptr(reg_context, runtime::context_offset_result_status),
            c);
    }

    void
    Emitter::error_block(asmjit::Label &lbl, runtime::StatusCode const status)
    {
        hx_mark("@F3566 error_block");
        as_.align(asmjit::AlignMode::kCode, 16);
        as_.bind(lbl);
        status_code(status);
        as_.jmp(epilogue_label_);
    }

    void Emitter::return_with_status_code(runtime::StatusCode const status)
    {
        hx_mark("@F3574 return_with_status_code");
        auto const offset = stack_.pop();
        RegReserv const offset_avx_reserv{offset};
        auto const size = stack_.pop();
        RegReserv const size_avx_reserv{size};
        discharge_deferred_comparison();
        status_code(status);
        mov_stack_elem_to_unaligned_mem<true>(
            offset,
            qword_ptr(reg_context, runtime::context_offset_result_offset));
        mov_stack_elem_to_unaligned_mem<true>(
            size, qword_ptr(reg_context, runtime::context_offset_result_size));
        as_.jmp(epilogue_label_);
    }

    template <typename... LiveSet>
    void Emitter::jump_stack_elem_dest(
        StackElemRef dest, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F3592 jump_stack_elem_dest");
        if (dest->literal()) {
            hx_mark("@L3593");
            auto const lit = literal_jump_dest_operand(std::move(dest));
            write_to_final_stack_offsets();
            adjust_by_stack_delta<false>();
            jump_literal_dest(lit);
        }
        else {
            hx_mark("@L3599");
            auto [op, spill_elem] = non_literal_jump_dest_operand(dest, live);
            write_to_final_stack_offsets();
            adjust_by_stack_delta<false>();
            jump_non_literal_dest(dest, op, spill_elem);
        }
    }

    uint256_t Emitter::literal_jump_dest_operand(StackElemRef const dest)
    {
        hx_mark("@F3608 literal_jump_dest_operand");
        return dest->literal()->value;
    }

    asmjit::Label const &Emitter::jump_dest_label(uint256_t const &dest)
    {
        hx_mark("@F3613 jump_dest_label");
        if (dest >= *bytecode_size_) {
            hx_mark("@L3614");
            return error_label_;
        }
        else {
            hx_mark("@L3617");
            auto const it = jump_dests_.find(dest[0]);
            if (it == jump_dests_.end()) {
                hx_mark("@L3619");
                return error_label_;
            }
            else {
                hx_mark("@L3622");
                return it->second;
            }
        }
    }

    void Emitter::jump_literal_dest(uint256_t const &dest)
    {
        hx_mark("@F3629 jump_literal_dest");
        as_.jmp(jump_dest_label(dest));
    }

    template <typename... LiveSet>
    std::pair<Emitter::Operand, std::optional<StackElem *>>
    Emitter::non_literal_jump_dest_operand(
        StackElemRef const &dest, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F3637 non_literal_jump_dest_operand");
        Operand op;
        std::optional<StackElem *> spill_elem;
        if (dest->stack_offset()) {
            hx_mark("@L3640");
            if (is_live(dest, live)) {
                hx_mark("@L3641");
                if (!dest->general_reg()) {
                    hx_mark("@L3642");
                    spill_elem =
                        revertible_mov_stack_offset_to_general_reg(dest);
                }
            }
            else if (dest->stack_offset()->offset <= stack_.top_index()) {
                hx_mark("@L3647");
                if (!dest->general_reg()) {
                    hx_mark("@L3648");
                    spill_elem =
                        revertible_mov_stack_offset_to_general_reg(dest);
                }
            }
            else {
                hx_mark("@L3653");
                op = stack_offset_to_mem(*dest->stack_offset());
            }
        }
        if (dest->general_reg()) {
            hx_mark("@L3657");
            op = general_reg_to_gpq256(*dest->general_reg());
        }
        else if (!dest->stack_offset()) {
            hx_mark("@L3660");
            MONAD_DEBUG_ASSERT(dest->avx_reg().has_value());
            x86::Mem const m = x86::qword_ptr(x86::rsp, sp_offset_temp_word1);
            as_.vmovups(m, avx_reg_to_ymm(*dest->avx_reg()));
            op = m;
        }
        return {op, spill_elem};
    }

    void Emitter::jump_non_literal_dest(
        StackElemRef const dest, Operand const &dest_op,
        std::optional<StackElem *> const spill_elem)
    {
        hx_mark("@F3672 jump_non_literal_dest");
        if (spill_elem.has_value()) {
            hx_mark("@L3673");
            MONAD_DEBUG_ASSERT(dest->general_reg().has_value());
            // Restore `stack_` back to the state before calling
            // `non_literal_jump_dest_operand`.
            auto *e = *spill_elem;
            if (e != nullptr) {
                hx_mark("@L3678");
                MONAD_DEBUG_ASSERT(e->is_on_stack());
                stack_.move_general_reg(*dest, *e);
                stack_.remove_stack_offset(*e);
            }
            else {
                hx_mark("@L3683");
                stack_.remove_general_reg(*dest);
            }
        }
        jump_table_label_ = jump_table_label_ ? jump_table_label_
                                              : as_.newNamedLabel("JumpTable");
        if (std::holds_alternative<Gpq256>(dest_op)) {
            hx_mark("@L3689");
            Gpq256 const &gpq = std::get<Gpq256>(dest_op);
            as_.cmp(gpq[0], *bytecode_size_);
            as_.jnb(error_label_);
            as_.or_(gpq[1], gpq[2]);
            as_.or_(gpq[1], gpq[3]);
            as_.jnz(error_label_);

            as_.lea(x86::rax, x86::ptr(jump_table_label_.value()));
            as_.movsxd(x86::rcx, x86::dword_ptr(x86::rax, gpq[0], 2));
            as_.add(x86::rax, x86::rcx);
            as_.jmp(x86::rax);
        }
        else {
            hx_mark("@L3702");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(dest_op));
            x86::Mem m = std::get<x86::Mem>(dest_op);
            if (m.baseReg() == x86::rbp) {
                hx_mark("@L3705");
                // Since `adjust_by_stack_delta` has been called before this
                // function, we need to adjust when accessing EVM stack memory.
                m.addOffset(-(stack_.delta() * 32));
            }
            // Registers rcx and rdx are available, because `block_prologue` has
            // already written stack elements to their final stack offsets.
            as_.mov(x86::rcx, m);
            as_.cmp(x86::rcx, *bytecode_size_);
            as_.jnb(error_label_);
            m.addOffset(8);
            as_.mov(x86::rdx, m);
            m.addOffset(8);
            as_.or_(x86::rdx, m);
            m.addOffset(8);
            as_.or_(x86::rdx, m);
            as_.jnz(error_label_);

            as_.lea(x86::rax, x86::ptr(jump_table_label_.value()));
            as_.movsxd(x86::rcx, x86::dword_ptr(x86::rax, x86::rcx, 2));
            as_.add(x86::rax, x86::rcx);
            as_.jmp(x86::rax);
        }
    }

    void
    Emitter::conditional_jmp(asmjit::Label const &lbl, Comparison const comp)
    {
        hx_mark("@F3732 conditional_jmp");
        switch (comp) {
        case Comparison::Below:
            as_.jb(lbl);
            break;
        case Comparison::AboveEqual:
            as_.jae(lbl);
            break;
        case Comparison::Above:
            as_.ja(lbl);
            break;
        case Comparison::BelowEqual:
            as_.jbe(lbl);
            break;
        case Comparison::Less:
            as_.jl(lbl);
            break;
        case Comparison::GreaterEqual:
            as_.jge(lbl);
            break;
        case Comparison::Greater:
            as_.jg(lbl);
            break;
        case Comparison::LessEqual:
            as_.jle(lbl);
            break;
        case Comparison::Equal:
            as_.je(lbl);
            break;
        case Comparison::NotEqual:
            as_.jne(lbl);
            break;
        }
    }

    Comparison
    Emitter::jumpi_comparison(StackElemRef const cond, StackElemRef const dest)
    {
        hx_mark("@F3769 jumpi_comparison");
        auto const dc = stack_.discharge_deferred_comparison();
        if (dc.stack_elem && (dc.stack_elem == dest.get() ||
                              !dc.stack_elem->stack_indices().empty())) {
                                  hx_mark("@L3772");
            RegReserv const cond_reserv{cond};
            RegReserv const dest_reserv{dest};
            discharge_deferred_comparison(dc.stack_elem, dc.comparison());
        }
        if (dc.negated_stack_elem &&
            (dc.negated_stack_elem == dest.get() ||
             !dc.negated_stack_elem->stack_indices().empty())) {
                 hx_mark("@L3779");
            RegReserv const cond_reserv{cond};
            RegReserv const dest_reserv{dest};
            discharge_deferred_comparison(
                dc.negated_stack_elem, negate_comparison(dc.comparison()));
        }

        Comparison comp;
        if (cond.get() == dc.stack_elem) {
            hx_mark("@L3787");
            comp = dc.comparison();
        }
        else if (cond.get() == dc.negated_stack_elem) {
            hx_mark("@L3790");
            comp = negate_comparison(dc.comparison());
        }
        else {
            hx_mark("@L3793");
            comp = Comparison::NotEqual;
            if (cond->avx_reg()) {
                hx_mark("@L3795");
                auto const y = avx_reg_to_ymm(*cond->avx_reg());
                as_.vptest(y, y);
            }
            else if (cond->general_reg()) {
                hx_mark("@L3799");
                Gpq256 const &gpq = general_reg_to_gpq256(*cond->general_reg());
                if (!is_live(cond, std::make_tuple(dest))) {
                    hx_mark("@L3801");
                    as_.or_(gpq[1], gpq[0]);
                    as_.or_(gpq[2], gpq[3]);
                    as_.or_(gpq[1], gpq[2]);
                }
                else {
                    hx_mark("@L3806");
                    as_.mov(x86::rax, gpq[0]);
                    as_.or_(x86::rax, gpq[1]);
                    as_.or_(x86::rax, gpq[2]);
                    as_.or_(x86::rax, gpq[3]);
                }
            }
            else {
                hx_mark("@L3813");
                MONAD_DEBUG_ASSERT(cond->stack_offset().has_value());
                RegReserv const dest_reserv{dest};
                mov_stack_offset_to_avx_reg(cond);
                auto const y = avx_reg_to_ymm(*cond->avx_reg());
                as_.vptest(y, y);
            }
        }
        return comp;
    }

    void Emitter::jumpi_spill_fallthrough_stack()
    {
        hx_mark("@F3825 jumpi_spill_fallthrough_stack");
        auto dest = stack_.pop();
        auto cond = stack_.pop();
        if (cond->literal()) {
            hx_mark("@L3828");
            {
                hx_mark("@L3829");
                RegReserv const dest_reserv{dest};
                discharge_deferred_comparison();
            }
            if (cond->literal()->value == 0) {
                hx_mark("@L3833");
                // Clear to remove locations, if not on stack:
                cond = nullptr;
                dest = nullptr;
                write_to_final_stack_offsets();
                adjust_by_stack_delta<false>();
            }
            else {
                hx_mark("@L3840");
                // Clear to remove locations, if not on stack:
                cond = nullptr;
                jump_stack_elem_dest(std::move(dest), {});
            }
            return;
        }

        Comparison const comp = jumpi_comparison(std::move(cond), dest);

        if (dest->literal()) {
            hx_mark("@L3850");
            auto const lit = literal_jump_dest_operand(std::move(dest));
            write_to_final_stack_offsets();
            adjust_by_stack_delta<true>();
            conditional_jmp(jump_dest_label(lit), comp);
        }
        else {
            hx_mark("@L3856");
            auto const fallthrough_lbl = as_.newLabel();
            // Note that `cond` is not live here.
            auto [op, spill_elem] = non_literal_jump_dest_operand(dest, {});
            write_to_final_stack_offsets();
            conditional_jmp(fallthrough_lbl, negate_comparison(comp));
            adjust_by_stack_delta<false>();
            jump_non_literal_dest(std::move(dest), op, spill_elem);
            as_.bind(fallthrough_lbl);
            adjust_by_stack_delta<false>();
        }
    }

    void Emitter::jumpi_keep_fallthrough_stack()
    {
        hx_mark("@F3870 jumpi_keep_fallthrough_stack");
        keep_stack_in_next_block_ = true;

        auto dest = stack_.pop();
        auto cond = stack_.pop();

        if (cond->literal()) {
            hx_mark("@L3876");
            {
                hx_mark("@L3877");
                RegReserv const dest_reserv{dest};
                discharge_deferred_comparison();
            }
            if (cond->literal()->value != 0) {
                hx_mark("@L3881");
                // Clear to remove locations, if not on stack:
                cond = nullptr;
                jump_stack_elem_dest(std::move(dest), {});
            }
            return;
        }

        Comparison const comp = jumpi_comparison(std::move(cond), dest);
        if (dest->literal() && stack_.delta() == 0 &&
            stack_.missing_spill_count() == 0) {
                hx_mark("@L3891");
            // We do not need to spill stack elements and we do not need
            // to adjust by stack delta, so only need conditional jump.
            auto const lit = literal_jump_dest_operand(std::move(dest));
            conditional_jmp(jump_dest_label(lit), comp);
        }
        else {
            hx_mark("@L3897");
            asmjit::Label const fallthrough_lbl = as_.newLabel();
            conditional_jmp(fallthrough_lbl, negate_comparison(comp));
            // The jump_stack_elem_dest function will spill to stack
            // and/or adjust by stack delta.
            jump_stack_elem_dest(std::move(dest), {});
            as_.bind(fallthrough_lbl);
        }
    }

    void Emitter::read_context_address(int32_t const offset)
    {
        hx_mark("@F3908 read_context_address");
        x86::Mem m = x86::qword_ptr(reg_context, offset);
        auto [dst, _] = alloc_general_reg();
        Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
        m.setSize(4);
        as_.movbe(gpq[2].r32(), m);
        m.addOffset(4);
        m.setSize(8);
        as_.movbe(gpq[1], m);
        m.addOffset(8);
        as_.movbe(gpq[0], m);
        if (stack_.has_deferred_comparison()) {
            hx_mark("@L3919");
            as_.mov(gpq[3], 0);
        }
        else {
            hx_mark("@L3922");
            as_.xor_(gpq[3].r32(), gpq[3].r32());
        }
        stack_.push(std::move(dst));
    }

    void Emitter::read_evmc_tx_context_address(int32_t const offset)
    {
        hx_mark("@F3929 read_evmc_tx_context_address");
        auto [dst, _] = alloc_general_reg();
        Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
        as_.mov(
            gpq[3],
            x86::qword_ptr(
                reg_context, runtime::context_offset_env_tx_context));
        x86::Mem m = x86::qword_ptr(gpq[3], offset);
        m.setSize(4);
        as_.movbe(gpq[2].r32(), m);
        m.addOffset(4);
        m.setSize(8);
        as_.movbe(gpq[1], m);
        m.addOffset(8);
        as_.movbe(gpq[0], m);
        if (stack_.has_deferred_comparison()) {
            hx_mark("@L3944");
            as_.mov(gpq[3], 0);
        }
        else {
            hx_mark("@L3947");
            as_.xor_(gpq[3].r32(), gpq[3].r32());
        }
        stack_.push(std::move(dst));
    }

    void Emitter::read_context_word(int32_t const offset)
    {
        hx_mark("@F3954 read_context_word");
        stack_.push(read_mem_be(x86::qword_ptr(reg_context, offset)));
    }

    void Emitter::read_evmc_tx_context_word(int32_t const offset)
    {
        hx_mark("@F3959 read_evmc_tx_context_word");
        as_.mov(
            x86::rax,
            x86::qword_ptr(
                reg_context, runtime::context_offset_env_tx_context));
        stack_.push(read_mem_be(x86::qword_ptr(x86::rax, offset)));
    }

    void Emitter::read_context_uint32_to_word(int32_t const offset)
    {
        hx_mark("@F3968 read_context_uint32_to_word");
        auto [dst, _] = alloc_general_reg();
        Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
        as_.mov(gpq[0].r32(), x86::dword_ptr(reg_context, offset));
        if (stack_.has_deferred_comparison()) {
            hx_mark("@L3972");
            as_.mov(gpq[1].r32(), 0);
            as_.mov(gpq[2].r32(), 0);
            as_.mov(gpq[3].r32(), 0);
        }
        else {
            hx_mark("@L3977");
            as_.xor_(gpq[1].r32(), gpq[1].r32());
            as_.xor_(gpq[2].r32(), gpq[2].r32());
            as_.xor_(gpq[3].r32(), gpq[3].r32());
        }
        stack_.push(std::move(dst));
    }

    void Emitter::read_evmc_tx_context_uint64_to_word(int32_t const offset)
    {
        hx_mark("@F3986 read_evmc_tx_context_uint64_to_word");
        auto [dst, _] = alloc_general_reg();
        Gpq256 const &gpq = general_reg_to_gpq256(*dst->general_reg());
        as_.mov(
            gpq[0],
            x86::qword_ptr(
                reg_context, runtime::context_offset_env_tx_context));
        as_.mov(gpq[0], x86::qword_ptr(gpq[0], offset));
        if (stack_.has_deferred_comparison()) {
            hx_mark("@L3994");
            as_.mov(gpq[1].r32(), 0);
            as_.mov(gpq[2].r32(), 0);
            as_.mov(gpq[3].r32(), 0);
        }
        else {
            hx_mark("@L3999");
            as_.xor_(gpq[1].r32(), gpq[1].r32());
            as_.xor_(gpq[2].r32(), gpq[2].r32());
            as_.xor_(gpq[3].r32(), gpq[3].r32());
        }
        stack_.push(std::move(dst));
    }

    // Discharge
    void Emitter::lt(StackElemRef pre_dst, StackElemRef pre_src)
    {
        hx_mark("@F4009 lt");
        if (pre_dst == pre_src) {
            hx_mark("@L4010");
            push(0);
            return;
        }
        if (pre_dst->literal() && pre_src->literal()) {
            hx_mark("@L4014");
            auto const &x = pre_dst->literal()->value;
            auto const &y = pre_src->literal()->value;
            push(x < y);
            return;
        }
        {
            hx_mark("@L4020");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        bool negate = false;
        if (pre_dst->literal()) {
            hx_mark("@L4027");
            // Unsigned overflow to `0` is fine:
            pre_dst = stack_.alloc_literal({pre_dst->literal()->value + 1});
            std::swap(pre_dst, pre_src);
            negate = true;
        }
        if (pre_src->literal() && !pre_src->literal()->value) {
            hx_mark("@L4033");
            push(0);
            return;
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, dst_loc, src, src_loc] = get_general_dest_and_source(
            false, std::move(pre_dst), std::move(pre_src), {});
        GENERAL_BIN_INSTR(cmp, sbb)
        (dst, dst_loc, src, src_loc, [](size_t i, uint64_t x) {
            return i == 0 && x == 0;
        });
        if (negate) {
            hx_mark("@L4045");
            stack_.push_deferred_comparison(Comparison::AboveEqual);
        }
        else {
            hx_mark("@L4048");
            stack_.push_deferred_comparison(Comparison::Below);
        }
    }

    // Discharge
    void Emitter::slt(StackElemRef pre_dst, StackElemRef pre_src)
    {
        hx_mark("@F4055 slt");
        if (pre_dst == pre_src) {
            hx_mark("@L4056");
            push(0);
            return;
        }
        if (pre_dst->literal() && pre_src->literal()) {
            hx_mark("@L4060");
            auto const &x = pre_dst->literal()->value;
            auto const &y = pre_src->literal()->value;
            push(monad::slt(x, y));
            return;
        }

        bool negate = false;
        if (pre_dst->literal()) {
            hx_mark("@L4068");
            // Signed overflow to `1 << 255` is fine:
            pre_dst = stack_.alloc_literal({pre_dst->literal()->value + 1});
            std::swap(pre_dst, pre_src);
            negate = true;
        }
        if (pre_src->literal() && pre_src->literal()->value == uint256_t{1}
                                                                   << 255) {
                                                                       hx_mark("@L4075");
            push(0);
            return;
        }

        if (pre_src->literal() && !pre_src->literal()->value) {
            hx_mark("@L4080");
            pre_src.reset(); // Clear locations
            if (auto const r = issigned(std::move(pre_dst))) {
                hx_mark("@L4082");
                auto comparison = *r;
                if (negate) {
                    hx_mark("@L4084");
                    comparison = negate_comparison(comparison);
                }
                stack_.push_deferred_comparison(comparison);
            }
            else {
                hx_mark("@L4089");
                if (negate) {
                    hx_mark("@L4090");
                    push(1);
                }
                else {
                    hx_mark("@L4093");
                    push(0);
                }
            }
            return;
        }

        {
            hx_mark("@L4100");
            RegReserv const pre_dst_reserv{pre_dst};
            RegReserv const pre_src_reserv{pre_src};
            discharge_deferred_comparison();
        }

        // Empty live set, because only `pre_dst` and `pre_src` are live:
        auto [dst, dst_loc, src, src_loc] = get_general_dest_and_source(
            false, std::move(pre_dst), std::move(pre_src), {});
        GENERAL_BIN_INSTR(cmp, sbb)
        (dst, dst_loc, src, src_loc, [](size_t i, uint64_t x) {
            return i == 0 && x == 0;
        });
        if (negate) {
            hx_mark("@L4113");
            stack_.push_deferred_comparison(Comparison::GreaterEqual);
        }
        else {
            hx_mark("@L4116");
            stack_.push_deferred_comparison(Comparison::Less);
        }
    }

    template <typename... LiveSet>
    void Emitter::destructive_mov_stack_elem_to_bounded_rax(
        StackElemRef e, uint16_t bound, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4124 destructive_mov_stack_elem_to_bounded_rax");
        MONAD_DEBUG_ASSERT(bound > 0);
        MONAD_DEBUG_ASSERT(!e->literal().has_value());
        if (e->general_reg()) {
            hx_mark("@L4127");
            auto const &gpq = general_reg_to_gpq256(*e->general_reg());
            as_.cmp(gpq[0], bound);
            if (!is_live(e, live)) {
                hx_mark("@L4130");
                as_.cmova(gpq[1], gpq[0]);
                as_.or_(gpq[2], gpq[3]);
                as_.or_(gpq[2], gpq[1]);
            }
            else {
                hx_mark("@L4135");
                as_.mov(x86::rax, gpq[1]);
                as_.cmova(x86::rax, gpq[0]);
                as_.or_(x86::rax, gpq[2]);
                as_.or_(x86::rax, gpq[3]);
            }
            as_.mov(x86::eax, bound);
            as_.cmovz(x86::eax, gpq[0].r32());
        }
        else if (e->avx_reg()) {
            hx_mark("@L4144");
            AvxRegReserv const e_reserv{e};
            auto const y = avx_reg_to_ymm(*e->avx_reg());
            if (std::popcount(uint32_t{bound} + 1) == 1) {
                hx_mark("@L4147");
                auto const shift = std::bit_width(bound);
                auto const mask = std::numeric_limits<uint256_t>::max()
                                  << shift;
                as_.vptest(y, rodata_.add32(mask));
            }
            else {
                hx_mark("@L4153");
                auto const [tmp_e, reserv] = alloc_avx_reg();
                auto const tmp_y = avx_reg_to_ymm(*tmp_e->avx_reg());
                as_.vpsubusw(tmp_y, y, rodata_.add32(bound - 1));
                // `tmp_y` zero iff `y <= bound-1`, so zero iff `y < bound`
                as_.vptest(tmp_y, tmp_y);
            }
            as_.vmovd(x86::eax, y.xmm());
            if (stack_.has_free_general_reg()) {
                hx_mark("@L4161");
                auto [e, reserv] = alloc_general_reg();
                auto const q = general_reg_to_gpq256(*e->general_reg())[0];
                as_.mov(q.r32(), bound);
                as_.cmovnz(x86::eax, q.r32());
            }
            else {
                hx_mark("@L4167");
                as_.cmovnz(x86::eax, rodata_.add4(bound));
            }
        }
        else {
            hx_mark("@L4171");
            MONAD_ASSERT(e->stack_offset().has_value());
            x86::Mem mem = stack_offset_to_mem(*e->stack_offset());
            mem.addOffset(8);
            as_.mov(x86::rax, mem);
            mem.addOffset(8);
            as_.or_(x86::rax, mem);
            mem.addOffset(8);
            as_.or_(x86::rax, mem);
            as_.mov(x86::eax, bound);
            mem.addOffset(-24);
            if (stack_.has_free_general_reg()) {
                hx_mark("@L4182");
                auto [e, reserv] = alloc_general_reg();
                auto const q = general_reg_to_gpq256(*e->general_reg())[0];
                as_.mov(q.r32(), x86::eax);
                as_.cmovz(x86::rax, mem);
                as_.cmp(x86::rax, q);
                as_.cmova(x86::eax, q.r32());
            }
            else {
                hx_mark("@L4190");
                as_.cmovz(x86::rax, mem);
                as_.cmp(x86::rax, bound);
                as_.cmova(x86::eax, rodata_.add4(bound));
            }
        }
    }

    void Emitter::byte_literal_ix_stack_offset_src(
        StackElemRef ix, StackElemRef const src)
    {
        hx_mark("@F4200 byte_literal_ix_stack_offset_src");
        MONAD_DEBUG_ASSERT(ix->literal().has_value());
        MONAD_DEBUG_ASSERT(src->stack_offset().has_value());

        auto const i = ix->literal()->value;
        ix.reset(); // Potentially release locations
        MONAD_DEBUG_ASSERT(i < 32);

        auto [dst, dst_reserv] = alloc_general_reg();
        Gpq256 const &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        auto src_mem = stack_offset_to_mem(*src->stack_offset());
        // we set the size to 1 so that asmjit generates a
        // movzx dst BYTE PTR [src_mem]
        // instruction and only copies a single byte
        src_mem.setSize(1);

        as_.xor_(dst_gpq[1].r32(), dst_gpq[1].r32());
        as_.xor_(dst_gpq[2].r32(), dst_gpq[2].r32());
        as_.xor_(dst_gpq[3].r32(), dst_gpq[3].r32());

        src_mem.addOffset(31 - static_cast<int64_t>(i[0]));
        as_.movzx(dst_gpq[0].r32(), src_mem);

        stack_.push(std::move(dst));
    }

    template <typename... LiveSet>
    void Emitter::byte_non_literal_ix_literal_or_stack_offset_src(
        StackElemRef ix, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4230 byte_non_literal_ix_literal_or_stack_offset_src");
        MONAD_DEBUG_ASSERT(!ix->literal().has_value());
        MONAD_DEBUG_ASSERT(
            src->literal().has_value() || src->stack_offset().has_value());

        RegReserv const ix_reserv{ix};

        auto [dst, dst_reserv] = alloc_general_reg();
        Gpq256 const &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        as_.xor_(dst_gpq[1].r32(), dst_gpq[1].r32());
        as_.xor_(dst_gpq[2].r32(), dst_gpq[2].r32());
        as_.xor_(dst_gpq[3].r32(), dst_gpq[3].r32());

        auto const zero_reg = dst_gpq[1];
        as_.mov(dst_gpq[0].r32(), 31);

        if (ix->general_reg()) {
            hx_mark("@L4247");
            Gpq256 const &ix_gpq = general_reg_to_gpq256(*ix->general_reg());
            as_.sub(dst_gpq[0], ix_gpq[0]);
        }
        else if (ix->stack_offset()) {
            hx_mark("@L4251");
            auto const ix_mem = stack_offset_to_mem(*ix->stack_offset());
            as_.sub(dst_gpq[0], ix_mem);
        }
        else {
            hx_mark("@L4255");
            auto const ix_ymm = avx_reg_to_ymm(*ix->avx_reg());
            as_.vmovq(x86::rax, ix_ymm.xmm());
            as_.sub(dst_gpq[0], x86::rax);
        }
        as_.cmovb(dst_gpq[0], zero_reg);

        if (src->stack_offset()) {
            hx_mark("@L4262");
            auto src_mem = stack_offset_to_mem(*src->stack_offset());
            // we set the size to 1 so that asmjit generates a
            // movzx dst BYTE PTR [src_mem]
            // instruction and only copies a single byte
            src_mem.setSize(1);

            src_mem.setIndex(dst_gpq[0]);
            as_.movzx(dst_gpq[0], src_mem);
        }
        else {
            hx_mark("@L4272");
            // x86 does not permit a [base_label + index_register + offset]
            // memory operand, so in the case of src being in rodata, we move
            // the address of the literal to rax and then emit a
            // [base_register + index_register] version of movzx
            as_.lea(x86::rax, rodata_.add32(src->literal()->value));
            as_.movzx(dst_gpq[0], x86::byte_ptr(x86::rax, dst_gpq[0]));
        }

        as_.cmovb(dst_gpq[0], zero_reg); // Clear when 31 < ix[0]
        test_high_bits192(
            std::move(ix), std::tuple_cat(std::make_tuple(dst), live));
        as_.cmovnz(dst_gpq[0], zero_reg);

        stack_.push(std::move(dst));
    }

    template <typename... LiveSet>
    void Emitter::byte_literal_ix_general_reg_src(
        StackElemRef ix, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4292 byte_literal_ix_general_reg_src");
        MONAD_DEBUG_ASSERT(ix->literal().has_value());
        MONAD_DEBUG_ASSERT(src->general_reg().has_value());

        auto const i = ix->literal()->value;
        MONAD_DEBUG_ASSERT(i < 32);
        ix.reset(); // Potentially release locations

        Gpq256 const &src_gpq = general_reg_to_gpq256(*src->general_reg());
        auto [dst, dst_reserv] =
            alloc_or_release_general_reg(std::move(src), live);
        Gpq256 &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        uint64_t const byte_index = 31 - i[0];
        uint64_t const word_index = byte_index >> 3;
        x86::Gpq const s = src_gpq[word_index];
        if (&src_gpq == &dst_gpq) {
            hx_mark("@L4308");
            std::swap(dst_gpq[0], dst_gpq[word_index]);
        }

        uint64_t const shift = (byte_index & 7) << 3;
        if (shift) {
            hx_mark("@L4313");
            if (s != dst_gpq[0]) {
                hx_mark("@L4314");
                as_.mov(dst_gpq[0], s);
            }
            as_.shr(dst_gpq[0], shift);
            if (shift < 56) {
                hx_mark("@L4318");
                as_.movzx(dst_gpq[0].r32(), dst_gpq[0].r8Lo());
            }
        }
        else {
            hx_mark("@L4322");
            as_.movzx(dst_gpq[0].r32(), s.r8Lo());
        }

        as_.xor_(dst_gpq[1].r32(), dst_gpq[1].r32());
        as_.xor_(dst_gpq[2].r32(), dst_gpq[2].r32());
        as_.xor_(dst_gpq[3].r32(), dst_gpq[3].r32());

        stack_.push(std::move(dst));
    }

    template <typename... LiveSet>
    void Emitter::byte_non_literal_ix_general_reg_src(
        StackElemRef ix, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4336 byte_non_literal_ix_general_reg_src");
        MONAD_DEBUG_ASSERT(!ix->literal().has_value());
        MONAD_DEBUG_ASSERT(src->general_reg().has_value());

        RegReserv const ix_reserv{ix};

        Gpq256 const &src_gpq = general_reg_to_gpq256(*src->general_reg());
        auto [dst, dst_reserv] = alloc_or_release_general_reg(
            std::move(src), std::tuple_cat(std::make_tuple(ix), live));
        Gpq256 const &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        x86::Gpq ix0;
        if (ix->general_reg()) {
            hx_mark("@L4348");
            Gpq256 const &ix_gpq = general_reg_to_gpq256(*ix->general_reg());
            ix0 = ix_gpq[0];
        }
        else if (ix->stack_offset()) {
            hx_mark("@L4352");
            auto const ix_mem = stack_offset_to_mem(*ix->stack_offset());
            as_.mov(x86::rax, ix_mem);
            ix0 = x86::rax;
        }
        else {
            hx_mark("@L4357");
            MONAD_DEBUG_ASSERT(ix->avx_reg().has_value());
            auto const ix_ymm = avx_reg_to_ymm(*ix->avx_reg());
            as_.vmovq(x86::rax, ix_ymm.xmm());
            ix0 = x86::rax;
        }

        if (src_gpq[0] != dst_gpq[0]) {
            hx_mark("@L4364");
            as_.mov(dst_gpq[0], src_gpq[0]);
        }
        as_.cmp(ix0, 24);
        as_.cmovb(dst_gpq[0], src_gpq[1]);
        as_.cmp(ix0, 16);
        as_.cmovb(dst_gpq[0], src_gpq[2]);
        as_.cmp(ix0, 8);
        as_.cmovb(dst_gpq[0], src_gpq[3]);

        as_.mov(dst_gpq[1].r32(), 31);
        as_.xor_(dst_gpq[2].r32(), dst_gpq[2].r32());
        as_.xor_(dst_gpq[3].r32(), dst_gpq[3].r32());

        as_.sub(dst_gpq[1], ix0);
        // zero out result if ix[0] > 31
        as_.cmovb(dst_gpq[0], dst_gpq[2]);

        test_high_bits192(ix, std::tuple_cat(std::make_tuple(dst), live));
        // zero out result if any of the upper 192 bits of ix are set
        as_.cmovnz(dst_gpq[0], dst_gpq[2]);

        as_.and_(dst_gpq[1], 7);
        as_.shl(dst_gpq[1], 3);

        as_.shrx(dst_gpq[0], dst_gpq[0], dst_gpq[1]);
        as_.movzx(dst_gpq[0].r32(), dst_gpq[0].r8Lo());
        as_.xor_(dst_gpq[1].r32(), dst_gpq[1].r32());

        stack_.push(std::move(dst));
    }

    void Emitter::byte_literal_ix_avx_reg_src(
        StackElemRef ix, StackElemRef const src)
    {
        hx_mark("@F4398 byte_literal_ix_avx_reg_src");
        MONAD_DEBUG_ASSERT(ix->literal().has_value());
        MONAD_DEBUG_ASSERT(src->avx_reg().has_value());

        auto const i = ix->literal()->value;
        ix.reset(); // Potentially release locations
        MONAD_DEBUG_ASSERT(i < 32);

        AvxRegReserv const src_reserv{src};
        auto const src_ymm = avx_reg_to_ymm(*src->avx_reg());
        auto [dst, dst_reserv] = alloc_avx_reg();
        auto const dst_ymm = avx_reg_to_ymm(*dst->avx_reg());

        uint64_t const byte_index = 31 - i[0];
        uint64_t const yword_index = byte_index >> 4;
        uint64_t const sub_byte_index = byte_index & 15;

        auto shuf_ymm = src_ymm;
        if (yword_index) {
            hx_mark("@L4416");
            // Put upper yword of src in lower yword of dst:
            as_.vperm2i128(dst_ymm, src_ymm, src_ymm, 0x81);
            shuf_ymm = dst_ymm;
        }
        if (sub_byte_index) {
            hx_mark("@L4421");
            constexpr uint64_t hi = std::numeric_limits<uint64_t>::max();
            uint64_t const lo = (hi << 8) | sub_byte_index;
            as_.vpshufb(dst_ymm.xmm(), shuf_ymm.xmm(), rodata_.add16(lo, hi));
        }
        else {
            hx_mark("@L4426");
            as_.vpand(dst_ymm.xmm(), shuf_ymm.xmm(), rodata_.add16(0xff, 0));
        }

        stack_.push(std::move(dst));
    }

    template <typename... LiveSet>
    void Emitter::byte_non_literal_ix_avx_reg_src(
        StackElemRef ix, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4436 byte_non_literal_ix_avx_reg_src");
        MONAD_DEBUG_ASSERT(!ix->literal().has_value());
        MONAD_DEBUG_ASSERT(src->avx_reg().has_value());

        RegReserv const ix_reserv{ix};
        AvxRegReserv const src_reserv{src};

        auto const src_ymm = avx_reg_to_ymm(*src->avx_reg());
        test_high_bits192(ix, std::tuple_cat(std::make_tuple(src), live));

        auto [dst, dst_reserv] = alloc_or_release_avx_reg(
            std::move(src), std::tuple_cat(std::make_tuple(ix), live));
        auto const dst_ymm = avx_reg_to_ymm(*dst->avx_reg());
        auto [scratch, scratch_reserv] = alloc_avx_reg();
        auto const scratch_ymm = avx_reg_to_ymm(*scratch->avx_reg());

        if (ix->general_reg()) {
            hx_mark("@L4452");
            Gpq256 const &ix_gpq = general_reg_to_gpq256(*ix->general_reg());
            as_.mov(x86::rax, ix_gpq[0]);
        }
        else if (ix->stack_offset()) {
            hx_mark("@L4456");
            auto const ix_mem = stack_offset_to_mem(*ix->stack_offset());
            as_.mov(x86::rax, ix_mem);
        }
        else {
            hx_mark("@L4460");
            MONAD_DEBUG_ASSERT(ix->avx_reg().has_value());
            auto const ix_ymm = avx_reg_to_ymm(*ix->avx_reg());
            as_.vmovq(x86::rax, ix_ymm.xmm());
        }

        // set rax to 0xffffffff if any of the upper 192 bits of ix are set or
        // ix[0] > 31
        as_.cmovnz(x86::rax, rodata_.add8(32));
        as_.sub(x86::rax, 31);
        as_.cmova(x86::rax, rodata_.add8(1));
        as_.neg(x86::rax);
        as_.vmovd(scratch_ymm.xmm(), x86::rax);
        as_.vpsrld(scratch_ymm.xmm(), scratch_ymm.xmm(), 2);
        as_.vpermps(dst_ymm, scratch_ymm, src_ymm);

        // setting scratch_ymm to all 1s will set all dst_ymm bytes to 0
        // when used as vpshufb control mask
        as_.vpcmpeqd(scratch_ymm.xmm(), scratch_ymm.xmm(), scratch_ymm.xmm());
        // if ix <= 31, eax & 0xe3 is equivalent to eax % 4,
        // which will be used to move the correct byte within the previously
        // copied double word from src_ymm to 0th position
        // if ix > 31, eax & 0xe3 == 0x3e will be inserted instead and since
        // the MSB of 0xe3 is 1, vpshufb will zero the lowest byte of dst_ymm
        as_.and_(x86::eax, 0xe3);
        as_.vpinsrb(scratch_ymm.xmm(), scratch_ymm.xmm(), x86::eax, 0x0);
        as_.vpshufb(dst_ymm.xmm(), dst_ymm.xmm(), scratch_ymm.xmm());

        stack_.push(std::move(dst));
    }

    void
    Emitter::signextend_avx_reg_by_int8(int8_t const ix, StackElemRef const src)
    {
        hx_mark("@F4493 signextend_avx_reg_by_int8");
        MONAD_DEBUG_ASSERT(ix >= 0 && ix < 31);
        MONAD_DEBUG_ASSERT(src->avx_reg().has_value());

        AvxRegReserv const src_reserv{src};
        auto [dst, dst_reserv] = alloc_avx_reg();
        auto [tmp, tmp_reserv] = alloc_avx_reg();

        auto const src_y = avx_reg_to_ymm(*src->avx_reg());
        auto const dst_y = avx_reg_to_ymm(*dst->avx_reg());
        auto const tmp_y = avx_reg_to_ymm(*tmp->avx_reg());

        uint256_t shuf = std::numeric_limits<uint256_t>::max();
        std::memset(as_bytes(shuf) + ix + 1, ix, static_cast<size_t>(31 - ix));
        as_.vmovaps(tmp_y, rodata_.add32(shuf));
        // tmp_y[0] = -1
        // tmp_y[1] = -1
        // ...
        // tmp_y[ix] = -1
        // tmp_y[ix + 1] = ix
        // tmp_y[ix + 2] = ix
        // ...
        // tmp_y[31] = ix
        if (ix >= 16) {
            hx_mark("@L4516");
            as_.vpshufb(dst_y, src_y, tmp_y);
        }
        else {
            hx_mark("@L4519");
            as_.vperm2i128(dst_y, src_y, src_y, 0);
            as_.vpshufb(dst_y, dst_y, tmp_y);
        }
        // dst_y[0] = 0
        // dst_y[1] = 0
        // ...
        // dst_y[ix] = 0
        // dst_y[ix + 1] = src_y[ix]
        // dst_y[ix + 2] = src_y[ix]
        // ...
        // dst_y[31] = src_y[ix]
        as_.vpsraw(dst_y, dst_y, 15);
        // dst_y[0] = 0
        // dst_y[1] = 0
        // ...
        // dst_y[ix] = if (ix & 1) then 0 else sign
        // dst_y[ix + 1] = sign
        // dst_y[ix + 2] = sign
        // ...
        // dst_y[31] = sign
        // where sign = shift src_y[ix] arithmetic right by 7
        as_.vpblendvb(dst_y, dst_y, src_y, tmp_y);
        // dst_y[0] = src[0]
        // dst_y[1] = src[1]
        // ...
        // dst_y[ix] = src[ix]
        // dst_y[ix + 1] = sign
        // dst_y[ix + 2] = sign
        // ...
        // dst_y[31] = sign

        stack_.push(std::move(dst));
    }

    template <typename... LiveSet>
    void Emitter::signextend_general_reg_or_stack_offset_by_int8(
        int8_t ix, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4557 signextend_general_reg_or_stack_offset_by_int8");
        auto const sign_reg_ix = static_cast<size_t>(ix) / 8;
        auto const sign_reg_offset = static_cast<size_t>(ix) % 8;

        Gpq256 const *dst_gpq;
        x86::Gpq dst_sign_reg;

        if (src->general_reg()) {
            hx_mark("@L4564");
            auto const &src_gpq = general_reg_to_gpq256(*src->general_reg());
            auto const src_sign_reg = src_gpq[sign_reg_ix];

            auto [dst, dst_reserv] =
                alloc_or_release_general_reg(std::move(src), live);
            dst_gpq = &general_reg_to_gpq256(*dst->general_reg());
            dst_sign_reg = (*dst_gpq)[sign_reg_ix];

            // First we copy the part of the src and dst registers that are
            // not sign-extended
            if (&src_gpq != dst_gpq) {
                hx_mark("@L4575");
                for (size_t i = 0; i < sign_reg_ix; ++i) {
                    hx_mark("@L4576");
                    as_.mov((*dst_gpq)[i], src_gpq[i]);
                }
            }

            // Then we sign extend the register with the sign bit (so called
            // `sign_reg`).
            if (sign_reg_offset == 0) {
                hx_mark("@L4583");
                as_.movsx(dst_sign_reg, src_sign_reg.r8Lo());
            }
            else if (sign_reg_offset == 1) {
                hx_mark("@L4586");
                as_.movsx(dst_sign_reg, src_sign_reg.r16());
            }
            else if (sign_reg_offset == 3) {
                hx_mark("@L4589");
                as_.movsxd(dst_sign_reg, src_sign_reg.r32());
            }
            else if (sign_reg_offset == 7) {
                hx_mark("@L4592");
                if (&src_gpq != dst_gpq) {
                    hx_mark("@L4593");
                    as_.mov(dst_sign_reg, src_sign_reg);
                }
            }
            else {
                hx_mark("@L4597");
                if (&src_gpq != dst_gpq) {
                    hx_mark("@L4598");
                    as_.mov(dst_sign_reg.r64(), src_sign_reg.r64());
                }
                // we use left then right shifts to sign-extend
                as_.shl(dst_sign_reg.r64(), (7 - sign_reg_offset) * 8);
                as_.sar(dst_sign_reg.r64(), (7 - sign_reg_offset) * 8);
            }

            stack_.push(std::move(dst));
        }
        else {
            hx_mark("@L4608");
            MONAD_DEBUG_ASSERT(src->stack_offset());

            auto src_mem = stack_offset_to_mem(*src->stack_offset());

            auto [dst, dst_reserv] = alloc_general_reg();
            dst_gpq = &general_reg_to_gpq256(*dst->general_reg());
            dst_sign_reg = (*dst_gpq)[sign_reg_ix];

            for (size_t i = 0; i < sign_reg_ix; ++i) {
                hx_mark("@L4617");
                as_.mov((*dst_gpq)[i], src_mem);
                src_mem.addOffset(8);
            }

            if (sign_reg_offset == 0) {
                hx_mark("@L4622");
                src_mem.setSize(1);
                as_.movsx(dst_sign_reg, src_mem);
            }
            else if (sign_reg_offset == 1) {
                hx_mark("@L4626");
                src_mem.setSize(2);
                as_.movsx(dst_sign_reg, src_mem);
            }
            else if (sign_reg_offset == 3) {
                hx_mark("@L4630");
                src_mem.setSize(4);
                as_.movsxd(dst_sign_reg, src_mem);
            }
            else if (sign_reg_offset == 7) {
                hx_mark("@L4634");
                as_.mov(dst_sign_reg, src_mem);
            }
            else {
                hx_mark("@L4637");
                as_.mov(dst_sign_reg, src_mem);
                // we use left then right shifts to sign-extend
                as_.shl(dst_sign_reg, (7 - sign_reg_offset) * 8);
                as_.sar(dst_sign_reg, (7 - sign_reg_offset) * 8);
            }

            stack_.push(std::move(dst));
        }

        // Propagate the sign bit to the other registers.
        size_t reg_ix = sign_reg_ix + 1;
        if (reg_ix < 4) {
            hx_mark("@L4649");
            auto const &dst_ones = (*dst_gpq)[reg_ix];
            as_.mov(dst_ones, dst_sign_reg);
            as_.sar(dst_ones, 63);
            while (++reg_ix < 4) {
                hx_mark("@L4653");
                as_.mov((*dst_gpq)[reg_ix], dst_ones);
            }
        }
    }

    template <typename... LiveSet>
    void Emitter::signextend_by_literal_ix(
        uint256_t const &pre_ix, StackElemRef src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4663 signextend_by_literal_ix");
        MONAD_DEBUG_ASSERT(!src->literal().has_value());
        if (pre_ix >= 31) {
            hx_mark("@L4665");
            return stack_.push(std::move(src));
        }
        int8_t const ix = static_cast<int8_t>(pre_ix);
        if (src->avx_reg()) {
            hx_mark("@L4669");
            signextend_avx_reg_by_int8(ix, std::move(src));
        }
        else {
            hx_mark("@L4672");
            signextend_general_reg_or_stack_offset_by_int8(
                ix, std::move(src), live);
        }
    }

    void Emitter::signextend_avx_reg_by_bounded_rax(StackElemRef const src)
    {
        hx_mark("@F4679 signextend_avx_reg_by_bounded_rax");
        MONAD_DEBUG_ASSERT(src->avx_reg().has_value());

        AvxRegReserv const src_reserv{src};
        auto [dst, dst_reserv] = alloc_avx_reg();
        auto [tmp, tmp_reserv] = alloc_avx_reg();

        auto const src_y = avx_reg_to_ymm(*src->avx_reg());
        auto const dst_y = avx_reg_to_ymm(*dst->avx_reg());
        auto const tmp_y = avx_reg_to_ymm(*tmp->avx_reg());

        static constexpr uint256_t mem{
            0x06050403020100ff,
            0x0e0d0c0b0a090807,
            0x161514131211100f,
            0x1e1d1c1b1a191817};

        as_.vmovd(dst_y.xmm(), x86::eax);
        as_.vpbroadcastb(dst_y, dst_y.xmm());
        // dst_y = {byte_ix, byte_ix, ...}
        as_.vpsrld(tmp_y.xmm(), dst_y.xmm(), 2);
        as_.vpbroadcastd(tmp_y, tmp_y.xmm());
        // tmp_y = {dword_ix, dword_ix, ...}
        as_.vpermd(tmp_y, tmp_y, src_y);
        as_.vpshufb(tmp_y, tmp_y, dst_y);
        // tmp_y = {sign_byte, sign_byte, ...}
        as_.vpsraw(tmp_y, tmp_y, 15);
        // tmp_y = {sign, sign, ...}
        as_.vpcmpgtb(dst_y, dst_y, rodata_.add32(mem));
        // dst_y = {f(-1), f(0), f(1), ..., f(30)}
        // where f(i) = if byte_ix > i then -1 else 0
        as_.vpblendvb(dst_y, tmp_y, src_y, dst_y);
        // dst_y = {g(0), g(1), ..., g(31)}
        // where g(i) = if byte_ix >= i then src_y[i] else tmp_y[i]

        stack_.push(std::move(dst));
    }

    void Emitter::signextend_general_reg_by_bounded_rax(StackElemRef const src)
    {
        hx_mark("@F4718 signextend_general_reg_by_bounded_rax");
        MONAD_DEBUG_ASSERT(src->general_reg().has_value());

        GeneralRegReserv const src_reserv{src};
        auto [dst, dst_reserv] = alloc_general_reg();

        x86::Gpq shift;
        std::variant<x86::Gpd, x86::Mem> shift63;
        if (stack_.has_free_general_reg()) {
            hx_mark("@L4726");
            auto [e, reserv] = alloc_general_reg();
            auto const &gpq = general_reg_to_gpq256(*e->general_reg());
            shift = gpq[0];
            shift63 = gpq[1].r32();
            as_.mov(gpq[1].r32(), 63);
        }
        else {
            hx_mark("@L4733");
            as_.push(reg_context);
            shift = reg_context;
            shift63 = rodata_.add4(63);
        }

        auto cmovb_shift = [&, this] {
            if (std::holds_alternative<x86::Gpd>(shift63)) {
                hx_mark("@L4740");
                as_.cmovb(shift.r32(), std::get<x86::Gpd>(shift63));
            }
            else {
                hx_mark("@L4743");
                as_.cmovb(shift.r32(), std::get<x86::Mem>(shift63));
            }
        };

        auto const &src_gpq = general_reg_to_gpq256(*src->general_reg());
        auto const &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        // It is a pre-condition that rax is bounded, rax <= 31.

        as_.lea(
            shift.r32(),
            x86::byte_ptr(std::bit_cast<uint32_t>(int32_t{-56}), x86::eax, 3));
        // shift.r32() = -56 + eax * 8
        as_.neg(shift.r32());
        // shift.r32() = 56 - eax * 8
        as_.and_(shift.r32(), 63);
        // shift.r32()
        //   = (56 - eax * 8) % 64
        //   = (56 % 64 - (eax * 8) % 64) % 64
        //   = (56 - (eax * 8) % 64) % 64
        //   = 56 - (eax * 8) % 64, because (eax * 8) % 64 <= 56
        //   = 56 - (eax % 8) * 8
        //   where the last equality follows from
        //     8 * (eax / 8) + (eax % 8) = eax iff
        //     64 * (eax / 8) + 8 * (eax % 8) = 8 * eax iff
        //     64 * ((8 * eax) / 64) + 8 * (eax % 8) = 8 * eax
        //   which implies that 8 * (eax % 8) = (8 * eax) % 64,
        //   because 8 * (eax % 8) < 64.

        // For demostration purposes, suppose
        // * eax = 9
        // * src_gpq[0] = {0x80, 0x81, ..., 0x87}
        // * src_gpq[1] = {0x88, 0x89, ..., 0x8f}
        // * src_gpq[2] = {0x90, 0x91, ..., 0x90}
        // * src_gpq[2] = {0x98, 0x99, ..., 0x9f}
        // The byte to signextend is 0x89 at index eax == 9 in src_gpq,
        // which is the byte at index eax % 8 == 1 in src_gpq[1].

        // So at this point
        // shift = 56 - (eax % 8) * 8 = 48

        as_.shlx(dst_gpq[0], src_gpq[0], shift);
        as_.shlx(dst_gpq[1], src_gpq[1], shift);
        as_.shlx(dst_gpq[2], src_gpq[2], shift);
        as_.shlx(dst_gpq[3], src_gpq[3], shift);

        // dst_gpq[0] = {0, ..., 0, 0x80, 0x81}
        // dst_gpq[1] = {0, ..., 0, 0x88, 0x89}
        // dst_gpq[2] = {0, ..., 0, 0x90, 0x91}
        // dst_gpq[3] = {0, ..., 0, 0x98, 0x99}

        as_.cmp(x86::eax, 8);
        as_.cmovb(dst_gpq[1], dst_gpq[0]);
        // eax < 8 is false:
        //   dst_gpq[1] = {0, ..., 0, 0x88, 0x89}
        as_.sarx(dst_gpq[0], dst_gpq[0], shift);
        // shift == 48:
        //   dst_gpq[0] = {0x88, 0x89, 0xff, ..., 0xff}
        cmovb_shift();
        // eax < 8 is false:
        //   shift = 48
        as_.cmovae(dst_gpq[0], src_gpq[0]);
        // eax >= 8 is true:
        //   dst_gpq[0] = {0x80, 0x81, 0x82, ..., 0x87}

        as_.cmp(x86::eax, 16);
        as_.cmovb(dst_gpq[2], dst_gpq[1]);
        // eax < 16 is true:
        //   dst_gpq[2] = {0, ..., 0, 0x88, 0x89}
        as_.sarx(dst_gpq[1], dst_gpq[1], shift);
        // dst_gpq[1] = {0x88, 0x89, 0xff, ..., 0xff}
        cmovb_shift();
        // eax < 16 is true:
        //   shift = 63
        as_.cmovae(dst_gpq[1], src_gpq[1]);
        // eax >= 16 is false:
        //   dst_gpq[1] = {0x88, 0x89, 0xff, ..., 0xff}

        as_.cmp(x86::eax, 24);
        as_.cmovb(dst_gpq[3], dst_gpq[2]);
        // eax < 24 is true:
        //   dst_gpq[3] = {0, ..., 0, 0x88, 0x89}
        as_.sarx(dst_gpq[2], dst_gpq[2], shift);
        // shift == 63:
        //   dst_gpq[2] = {0xff, 0xff, ..., 0xff}
        cmovb_shift();
        // eax < 24 is true:
        //   shift = 63
        as_.cmovae(dst_gpq[2], src_gpq[2]);
        // eax >= 24 is false:
        //   dst_gpq[2] = {0xff, 0xff, ..., 0xff}

        as_.sarx(dst_gpq[3], dst_gpq[3], shift);
        // dst_gpq[3] = {0xff, 0xff, ..., 0xff}

        if (shift == reg_context) {
            hx_mark("@L4839");
            as_.pop(reg_context);
        }

        stack_.push(std::move(dst));
    }

    void Emitter::signextend_stack_offset_or_literal_by_bounded_rax(
        StackElemRef const src)
    {
        hx_mark("@F4848 signextend_stack_offset_or_literal_by_bounded_rax");
        MONAD_DEBUG_ASSERT(
            src->stack_offset().has_value() || src->literal().has_value());

        auto [dst, dst_reserv] = alloc_avx_reg();
        auto [tmp, tmp_reserv] = alloc_avx_reg();

        auto const dst_y = avx_reg_to_ymm(*dst->avx_reg());
        auto const tmp_y = avx_reg_to_ymm(*tmp->avx_reg());

        static constexpr uint256_t mem{
            0x06050403020100ff,
            0x0e0d0c0b0a090807,
            0x161514131211100f,
            0x1e1d1c1b1a191817};

        x86::Mem base_mem;
        if (src->stack_offset()) {
            hx_mark("@L4865");
            base_mem = stack_offset_to_mem(*src->stack_offset());
        }
        else if (stack_.has_free_general_reg()) {
            hx_mark("@L4868");
            auto [e, reserv] = alloc_general_reg();
            auto const &gpq = general_reg_to_gpq256(*e->general_reg());
            as_.lea(gpq[0], rodata_.add32(src->literal()->value));
            base_mem = x86::qword_ptr(gpq[0]);
        }
        else {
            hx_mark("@L4874");
            as_.push(reg_context);
            as_.lea(reg_context, rodata_.add32(src->literal()->value));
            base_mem = x86::qword_ptr(reg_context);
        }
        auto byte_mem = base_mem;
        byte_mem.setSize(1);
        byte_mem.setIndex(x86::rax);
        as_.vpbroadcastb(tmp_y, byte_mem);
        // tmp_y = {sign_byte, sign_byte, ...}
        as_.vpsraw(tmp_y, tmp_y, 15);
        // tmp_y = {sign, sign, ...}
        as_.vmovd(dst_y.xmm(), x86::eax);
        as_.vpbroadcastb(dst_y, dst_y.xmm());
        // dst_y = {byte_ix, byte_ix, ...}
        as_.vpcmpgtb(dst_y, dst_y, rodata_.add32(mem));
        // dst_y = {f(-1), f(0), f(1), ..., f(30)}
        // where f(i) = if byte_ix > i then -1 else 0
        as_.vpblendvb(dst_y, tmp_y, base_mem, dst_y);
        // dst_y = {g(0), g(1), ..., g(31)}
        // where g(i) = if byte_ix >= i then base_mem[i] else tmp_y[i]

        if (base_mem.baseReg() == reg_context) {
            hx_mark("@L4896");
            as_.pop(reg_context);
        }

        stack_.push(std::move(dst));
    }

    template <typename... LiveSet>
    void Emitter::signextend_by_non_literal(
        StackElemRef ix, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4906 signextend_by_non_literal");
        MONAD_DEBUG_ASSERT(!stack_.has_deferred_comparison());
        MONAD_DEBUG_ASSERT(!ix->literal().has_value());

        {
            hx_mark("@L4910");
            RegReserv const src_reserv{src};
            destructive_mov_stack_elem_to_bounded_rax(
                std::move(ix), 31, std::tuple_cat(std::make_tuple(src), live));
        }

        if (src->avx_reg()) {
            hx_mark("@L4916");
            signextend_avx_reg_by_bounded_rax(std::move(src));
        }
        else if (src->general_reg()) {
            hx_mark("@L4919");
            signextend_general_reg_by_bounded_rax(std::move(src));
        }
        else {
            hx_mark("@L4922");
            signextend_stack_offset_or_literal_by_bounded_rax(std::move(src));
        }
    }

    // Discharge directly or through `shift_by_literal`.
    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_by_stack_elem(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4932 shift_by_stack_elem");
        if (shift->literal()) {
            hx_mark("@L4933");
            auto const shift_value = shift->literal()->value;
            shift.reset(); // Potentially clear locations
            return shift_by_literal<shift_type>(
                shift_value, std::move(value), live);
        }
        return shift_by_non_literal<shift_type>(
            std::move(shift), std::move(value), live);
    }

    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_general_reg_or_stack_offset_by_literal(
        unsigned shift, StackElemRef value, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F4946 shift_general_reg_or_stack_offset_by_literal");
        MONAD_DEBUG_ASSERT(!stack_.has_deferred_comparison());
        MONAD_DEBUG_ASSERT(shift <= 256);
        MONAD_DEBUG_ASSERT(
            value->general_reg().has_value() ||
            value->stack_offset().has_value());

        unsigned const dword_shift = shift >> 6;
        unsigned const bit_shift = shift & 63;

        std::variant<Gpq256 const *, x86::Mem> value_op;
        StackElemRef dst;
        if (value->general_reg()) {
            hx_mark("@L4958");
            value_op = &general_reg_to_gpq256(*value->general_reg());
            auto [tmp, _] =
                alloc_or_release_general_reg(std::move(value), live);
            dst = std::move(tmp);
        }
        else {
            hx_mark("@L4964");
            value_op = stack_offset_to_mem(*value->stack_offset());
            auto [tmp, _] = alloc_general_reg();
            dst = std::move(tmp);
        }
        Gpq256 &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        if (shift == 256) {
            hx_mark("@L4971");
            MONAD_DEBUG_ASSERT(shift_type == ShiftType::SAR);
            if (std::holds_alternative<Gpq256 const *>(value_op)) {
                hx_mark("@L4973");
                Gpq256 const &value_gpq = *std::get<Gpq256 const *>(value_op);
                if (&dst_gpq != &value_gpq) {
                    hx_mark("@L4975");
                    as_.mov(dst_gpq[3], value_gpq[3]);
                }
            }
            else {
                hx_mark("@L4979");
                x86::Mem value_mem = std::get<x86::Mem>(value_op);
                value_mem.addOffset(24);
                as_.mov(dst_gpq[3], value_mem);
            }
            as_.sar(dst_gpq[3], 63);
            as_.mov(dst_gpq[0], dst_gpq[3]);
            as_.mov(dst_gpq[1], dst_gpq[3]);
            as_.mov(dst_gpq[2], dst_gpq[3]);
            return dst;
        }

        if (std::holds_alternative<Gpq256 const *>(value_op)) {
            hx_mark("@L4991");
            Gpq256 const &value_gpq = *std::get<Gpq256 const *>(value_op);
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L4993");
                if (dword_shift != 0) {
                    hx_mark("@L4994");
                    as_.mov(x86::rax, value_gpq[3]);
                    as_.sar(x86::rax, 63);
                }
            }
            if (&dst_gpq == &value_gpq) {
                hx_mark("@L4999");
                for (unsigned i = 0; i < 4 - dword_shift; ++i) {
                    hx_mark("@L5000");
                    if constexpr (shift_type == ShiftType::SHL) {
                        hx_mark("@L5001");
                        std::swap(dst_gpq[3 - i], dst_gpq[3 - dword_shift - i]);
                    }
                    else {
                        hx_mark("@L5004");
                        std::swap(dst_gpq[i], dst_gpq[dword_shift + i]);
                    }
                }
            }
            else {
                hx_mark("@L5009");
                for (unsigned i = 0; i < 4 - dword_shift; ++i) {
                    hx_mark("@L5010");
                    if constexpr (shift_type == ShiftType::SHL) {
                        hx_mark("@L5011");
                        as_.mov(dst_gpq[3 - i], value_gpq[3 - dword_shift - i]);
                    }
                    else {
                        hx_mark("@L5014");
                        as_.mov(dst_gpq[i], value_gpq[dword_shift + i]);
                    }
                }
            }
        }
        else {
            hx_mark("@L5020");
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5021");
                if (dword_shift != 0) {
                    hx_mark("@L5022");
                    x86::Mem tmp = std::get<x86::Mem>(value_op);
                    tmp.addOffset(24);
                    as_.mov(x86::rax, tmp);
                    as_.sar(x86::rax, 63);
                }
            }
            for (unsigned i = 0; i < 4 - dword_shift; ++i) {
                hx_mark("@L5029");
                x86::Mem tmp = std::get<x86::Mem>(value_op);
                if constexpr (shift_type == ShiftType::SHL) {
                    hx_mark("@L5031");
                    tmp.addOffset((3 - dword_shift - i) << 3);
                    as_.mov(dst_gpq[3 - i], tmp);
                }
                else {
                    hx_mark("@L5035");
                    tmp.addOffset((dword_shift + i) << 3);
                    as_.mov(dst_gpq[i], tmp);
                }
            }
        }

        for (unsigned i = 4 - dword_shift; i < 4; ++i) {
            hx_mark("@L5042");
            if constexpr (shift_type == ShiftType::SHL) {
                hx_mark("@L5043");
                as_.xor_(dst_gpq[3 - i].r32(), dst_gpq[3 - i].r32());
            }
            else if constexpr (shift_type == ShiftType::SHR) {
                hx_mark("@L5046");
                as_.xor_(dst_gpq[i].r32(), dst_gpq[i].r32());
            }
            else {
                hx_mark("@L5049");
                as_.mov(dst_gpq[i], x86::rax);
            }
        }

        if (bit_shift != 0) {
            hx_mark("@L5054");
            for (unsigned i = 0; i < 3 - dword_shift; ++i) {
                hx_mark("@L5055");
                if constexpr (shift_type == ShiftType::SHL) {
                    hx_mark("@L5056");
                    as_.shld(dst_gpq[3 - i], dst_gpq[3 - i - 1], bit_shift);
                }
                else {
                    hx_mark("@L5059");
                    as_.shrd(dst_gpq[i], dst_gpq[i + 1], bit_shift);
                }
            }
            if constexpr (shift_type == ShiftType::SHL) {
                hx_mark("@L5063");
                as_.shl(dst_gpq[dword_shift], bit_shift);
            }
            else if constexpr (shift_type == ShiftType::SHR) {
                hx_mark("@L5066");
                as_.shr(dst_gpq[3 - dword_shift], bit_shift);
            }
            else if (dword_shift == 0) {
                hx_mark("@L5069");
                as_.sar(dst_gpq[3], bit_shift);
            }
            else {
                hx_mark("@L5072");
                as_.shrd(dst_gpq[3 - dword_shift], x86::rax, bit_shift);
            }
        }

        return dst;
    }

    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef
    Emitter::shift_avx_reg_by_literal(unsigned shift, StackElemRef value)
    {
        hx_mark("@F5083 shift_avx_reg_by_literal");
        // See `shift_avx_reg_by_non_literal` for the general algorithm.

        MONAD_DEBUG_ASSERT(!stack_.has_deferred_comparison());
        MONAD_DEBUG_ASSERT(shift <= 256);
        MONAD_DEBUG_ASSERT(value->avx_reg().has_value());

        unsigned const dword_shift = shift >> 6;
        unsigned const bit_shift = shift & 63;

        AvxRegReserv const value_reserv{value};
        auto const in = avx_reg_to_ymm(*value->avx_reg());

        auto [result, result_reserv] = alloc_avx_reg();
        auto const out = avx_reg_to_ymm(*result->avx_reg());

        if (shift == 256) {
            hx_mark("@L5099");
            MONAD_DEBUG_ASSERT(shift_type == ShiftType::SAR);
            as_.vpxor(out, out, out);
            as_.vpcmpgtq(out, out, in);
            as_.vpermq(out, out, 0xff);
            return result;
        }

        auto [tmp1_elem, tmp1_reserv] = alloc_avx_reg();
        auto const tmp1 = avx_reg_to_ymm(*tmp1_elem->avx_reg());

        auto [zero_elem, zero_reserv] = alloc_avx_reg();
        auto const zero = avx_reg_to_ymm(*zero_elem->avx_reg());

        as_.vpxor(zero, zero, zero);

        if constexpr (shift_type == ShiftType::SHL) {
            hx_mark("@L5115");
            uint8_t const perm1 =
                static_cast<uint8_t>(0b11100100 << dword_shift * 2);
            uint8_t const mask1 = static_cast<uint8_t>(0xff << dword_shift * 2);
            as_.vpermq(out, in, perm1);
            as_.vblendps(out, zero, out, mask1);
            as_.vpsllq(out, out, bit_shift);
            if (dword_shift < 3) {
                hx_mark("@L5122");
                uint8_t const perm2 = static_cast<uint8_t>(perm1 << 2);
                uint8_t const mask2 = static_cast<uint8_t>(mask1 << 2);
                as_.vpermq(tmp1, in, perm2);
                as_.vblendps(tmp1, zero, tmp1, mask2);
                as_.vpsrlq(tmp1, tmp1, 64 - bit_shift);
                as_.vpor(out, out, tmp1);
            }
        }
        else {
            hx_mark("@L5131");
            uint8_t const perm1 =
                static_cast<uint8_t>(0b11100100 >> dword_shift * 2);
            uint8_t const mask1 = static_cast<uint8_t>(0xff >> dword_shift * 2);
            as_.vpermq(out, in, perm1);
            as_.vblendps(out, zero, out, mask1);
            as_.vpsrlq(out, out, bit_shift);
            uint8_t const mask2 = static_cast<uint8_t>(mask1 >> 2);
            if (dword_shift < 3) {
                hx_mark("@L5139");
                uint8_t const perm2 = static_cast<uint8_t>(perm1 >> 2);
                as_.vpermq(tmp1, in, perm2);
                as_.vblendps(tmp1, zero, tmp1, mask2);
                as_.vpsllq(tmp1, tmp1, 64 - bit_shift);
                as_.vpor(out, out, tmp1);
            }
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5146");
                auto [tmp2_elem, tmp2_reserv] = alloc_avx_reg();
                auto const tmp2 = avx_reg_to_ymm(*tmp2_elem->avx_reg());
                as_.vpcmpgtq(tmp1, zero, in);
                as_.vpermq(tmp1, tmp1, 0xff);
                if (dword_shift < 3) {
                    hx_mark("@L5151");
                    as_.vblendps(tmp2, tmp1, zero, mask2);
                    as_.vpsllq(tmp2, tmp2, 64 - bit_shift);
                }
                else {
                    hx_mark("@L5155");
                    as_.vpsllq(tmp2, tmp1, 64 - bit_shift);
                }
                as_.vblendps(tmp1, tmp1, zero, mask1);
                as_.vpor(tmp1, tmp2, tmp1);
                as_.vpor(out, out, tmp1);
            }
        }

        return result;
    }

    // Discharge
    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_by_literal(
        uint256_t const &shift_literal, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5172 shift_by_literal");
        MONAD_DEBUG_ASSERT(!value->literal().has_value());

        auto shift = static_cast<unsigned>(shift_literal);
        if (shift_literal >= 256) {
            hx_mark("@L5176");
            if constexpr (
                shift_type == ShiftType::SHL || shift_type == ShiftType::SHR) {
                    hx_mark("@L5178");
                return stack_.alloc_literal({0});
            }
            else {
                hx_mark("@L5181");
                shift = 256;
            }
        }
        else if (shift_literal == 0) {
            hx_mark("@L5185");
            return value;
        }

        {
            hx_mark("@L5189");
            RegReserv const value_reserv{value};
            discharge_deferred_comparison();
        }

        if (value->avx_reg()) {
            hx_mark("@L5194");
            return shift_avx_reg_by_literal<shift_type>(
                static_cast<unsigned>(shift), std::move(value));
        }
        return shift_general_reg_or_stack_offset_by_literal<shift_type>(
            static_cast<unsigned>(shift), std::move(value), live);
    }

    // Discharge
    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_by_non_literal(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5207 shift_by_non_literal");
        MONAD_DEBUG_ASSERT(
            gpq256_regs_[rcx_general_reg.reg][volatile_gpq_index<x86::rcx>()] ==
            x86::rcx);

        if (value->literal()) {
            hx_mark("@L5212");
            MONAD_DEBUG_ASSERT(!shift->literal().has_value());
            if (value->literal()->value == 0) {
                hx_mark("@L5214");
                return value;
            }
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5217");
                if (value->literal()->value ==
                    std::numeric_limits<uint256_t>::max()) {
                        hx_mark("@L5219");
                    return value;
                }
            }
        }

        {
            hx_mark("@L5225");
            RegReserv const shift_reserv{shift};
            RegReserv const value_reserv{value};
            discharge_deferred_comparison();
        }

        if (value->literal()) {
            hx_mark("@L5231");
            auto const value_literal = value->literal()->value;
            value.reset(); // Potentially clear locations
            return shift_literal_by_non_literal<shift_type>(
                std::move(shift), value_literal, live);
        }
        else if (value->avx_reg()) {
            hx_mark("@L5237");
            return shift_avx_reg_by_non_literal<shift_type>(
                std::move(shift), std::move(value), live);
        }
        else if (value->general_reg()) {
            hx_mark("@L5241");
            return shift_general_reg_by_non_literal<shift_type>(
                std::move(shift), std::move(value), live);
        }
        else {
            hx_mark("@L5245");
            MONAD_DEBUG_ASSERT(value->stack_offset().has_value());
            mov_stack_offset_to_general_reg(value);
            return shift_general_reg_by_non_literal<shift_type>(
                std::move(shift), std::move(value), live);
        }
    }

    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_literal_by_non_literal(
        StackElemRef shift, uint256_t const &value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5257 shift_literal_by_non_literal");
        destructive_mov_stack_elem_to_bounded_rax(std::move(shift), 256, live);

        // With `value` stored next to 64 bytes of fill, shifting by 8 * k + b
        // bits is a load at byte offset k shifted by b bits, combined with
        // the bits carried in from a load one byte further into the fill.
        // Neither load crosses a cache line for shifts below 256, and the
        // mask for b sits in 16 bytes of the table neither load reaches.
        x86::Mem window;
        x86::Mem bit_mask;
        if constexpr (shift_type == ShiftType::SHL) {
            hx_mark("@L5267");
            window = rodata_.add96({7, 0, 0, 0}, 0, value, 32);
            bit_mask = window;
            window.addOffset(64);
        }
        else {
            hx_mark("@L5272");
            bool const negative =
                shift_type == ShiftType::SAR && (value[3] >> 63);
            uint256_t const fill =
                negative ? std::numeric_limits<uint256_t>::max() : 0;
            window = rodata_.add96(value, fill, {fill[0], fill[1], 7, 0}, 0);
            bit_mask = window;
            bit_mask.addOffset(80);
        }

        auto [dst, dst_reserv] = alloc_avx_reg();
        auto [tmp1_elem, tmp1_reserv] = alloc_avx_reg();
        auto [tmp2_elem, tmp2_reserv] = alloc_avx_reg();
        auto const out = avx_reg_to_ymm(*dst->avx_reg());
        auto const tmp1 = avx_reg_to_ymm(*tmp1_elem->avx_reg());
        auto const tmp2 = avx_reg_to_ymm(*tmp2_elem->avx_reg());

        x86::Gpq base = reg_context;
        if (stack_.has_free_general_reg()) {
            hx_mark("@L5290");
            auto [e, reserv] = alloc_general_reg();
            // Safe because we are done allocating registers:
            base = general_reg_to_gpq256(*e->general_reg())[0];
        }
        else {
            hx_mark("@L5295");
            as_.push(reg_context);
        }

        as_.lea(base, window);
        as_.vmovd(tmp1.xmm(), x86::eax);
        as_.vpand(tmp1.xmm(), tmp1.xmm(), bit_mask);
        as_.shr(x86::eax, 3);
        if constexpr (shift_type == ShiftType::SHL) {
            hx_mark("@L5303");
            as_.neg(x86::rax);
        }
        int32_t const carry_offset = shift_type == ShiftType::SHL ? -1 : 1;
        as_.vmovups(out, x86::ptr(base, x86::rax));
        as_.vmovups(tmp2, x86::ptr(base, x86::rax, 0, carry_offset));
        if constexpr (shift_type == ShiftType::SHL) {
            hx_mark("@L5309");
            as_.vpsllq(out, out, tmp1.xmm());
            as_.vpsllq(tmp2, tmp2, tmp1.xmm());
            as_.vpsrlq(tmp2, tmp2, 8);
        }
        else {
            hx_mark("@L5314");
            as_.vpsrlq(out, out, tmp1.xmm());
            as_.vpsrlq(tmp2, tmp2, tmp1.xmm());
            as_.vpsllq(tmp2, tmp2, 8);
        }
        as_.vpor(out, out, tmp2);

        if (base == reg_context) {
            hx_mark("@L5321");
            as_.pop(reg_context);
        }

        return dst;
    }

    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_general_reg_by_non_literal(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5332 shift_general_reg_by_non_literal");
        MONAD_DEBUG_ASSERT(value->general_reg().has_value());

        bool restore_rcx_from_rax =
            stack_.is_general_reg_on_stack(rcx_general_reg);

        test_high_bits192(shift, std::tuple_cat(std::make_tuple(value), live));
        if (restore_rcx_from_rax || *value->general_reg() == rcx_general_reg) {
            hx_mark("@L5339");
            as_.mov(x86::rax, x86::rcx);
        }
        mov_stack_elem_low64_to_gpq(std::move(shift), x86::rcx);
        as_.cmovnz(x86::rcx, rodata_.add8(256));

        auto const rcx_gpq_ix = volatile_gpq_index<x86::rcx>();
        auto &rcx_gpq = general_reg_to_gpq256(rcx_general_reg);
        rcx_gpq[rcx_gpq_ix] = x86::rax;

        auto const &tmp_value_gpq =
            general_reg_to_gpq256(*value->general_reg());

        auto const [dst, dst_reserv] =
            alloc_or_release_general_reg(std::move(value), live);
        auto &dst_gpq = general_reg_to_gpq256(*dst->general_reg());
        if (*dst->general_reg() == rcx_general_reg) {
            hx_mark("@L5355");
            restore_rcx_from_rax = true;
        }
        if (&dst_gpq != &tmp_value_gpq) {
            hx_mark("@L5358");
            as_.mov(dst_gpq[0], tmp_value_gpq[0]);
            as_.mov(dst_gpq[1], tmp_value_gpq[1]);
            as_.mov(dst_gpq[2], tmp_value_gpq[2]);
            as_.mov(dst_gpq[3], tmp_value_gpq[3]);
        }

        bool restore_reg_context{};
        std::variant<x86::Gpq, x86::Mem> sign{x86::rax};
        if (restore_rcx_from_rax) {
            hx_mark("@L5367");
            if (stack_.has_free_general_reg()) {
                hx_mark("@L5368");
                auto [tmp, _] = alloc_general_reg();
                auto const &tmp_gpq =
                    general_reg_to_gpq256(*tmp->general_reg());
                // Safe because we are done allocating registers:
                sign = tmp_gpq[0];
                if constexpr (shift_type == ShiftType::SAR) {
                    hx_mark("@L5374");
                    as_.mov(tmp_gpq[0], dst_gpq[3]);
                    as_.sar(tmp_gpq[0], 63);
                }
                else {
                    hx_mark("@L5378");
                    as_.xor_(tmp_gpq[0].r32(), tmp_gpq[0].r32());
                }
            }
            else {
                hx_mark("@L5382");
                if constexpr (shift_type == ShiftType::SAR) {
                    hx_mark("@L5383");
                    restore_reg_context = true;
                    as_.push(reg_context);
                    sign = reg_context;
                    as_.mov(reg_context, dst_gpq[3]);
                    as_.sar(reg_context, 63);
                }
                else {
                    hx_mark("@L5390");
                    restore_reg_context = false; // silence clang tidy
                    sign = rodata_.add8(0);
                }
            }
        }
        else {
            hx_mark("@L5396");
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5397");
                as_.mov(x86::rax, dst_gpq[3]);
                as_.sar(x86::rax, 63);
            }
            else {
                hx_mark("@L5401");
                as_.xor_(x86::eax, x86::eax);
            }
        }

        if constexpr (shift_type == ShiftType::SHL) {
            hx_mark("@L5406");
            as_.cmp(x86::rcx, 64);
            as_.cmovae(dst_gpq[3], dst_gpq[2]);
            as_.cmovae(dst_gpq[2], dst_gpq[1]);
            as_.cmovae(dst_gpq[1], dst_gpq[0]);
            auto sign_gpq = dst_gpq[0];
            if (std::holds_alternative<x86::Gpq>(sign)) {
                hx_mark("@L5412");
                sign_gpq = std::get<x86::Gpq>(sign);
                as_.cmovae(dst_gpq[0], sign_gpq);
            }
            else {
                hx_mark("@L5416");
                as_.cmovae(dst_gpq[0], std::get<x86::Mem>(sign));
            }
            as_.cmp(x86::rcx, 128);
            as_.cmovae(dst_gpq[3], dst_gpq[2]);
            as_.cmovae(dst_gpq[2], dst_gpq[1]);
            as_.cmovae(dst_gpq[1], sign_gpq);
            as_.cmp(x86::rcx, 192);
            as_.cmovae(dst_gpq[3], dst_gpq[2]);
            as_.cmovae(dst_gpq[2], sign_gpq);
            as_.cmp(x86::rcx, 256);
            as_.cmovae(dst_gpq[3], sign_gpq);
            as_.shld(dst_gpq[3], dst_gpq[2], x86::cl);
            as_.shld(dst_gpq[2], dst_gpq[1], x86::cl);
            as_.shld(dst_gpq[1], dst_gpq[0], x86::cl);
            as_.shlx(dst_gpq[0], dst_gpq[0], x86::rcx);
        }
        else {
            hx_mark("@L5433");
            as_.cmp(x86::rcx, 64);
            as_.cmovae(dst_gpq[0], dst_gpq[1]);
            as_.cmovae(dst_gpq[1], dst_gpq[2]);
            as_.cmovae(dst_gpq[2], dst_gpq[3]);
            auto sign_gpq = dst_gpq[3];
            if (std::holds_alternative<x86::Gpq>(sign)) {
                hx_mark("@L5439");
                sign_gpq = std::get<x86::Gpq>(sign);
                as_.cmovae(dst_gpq[3], sign_gpq);
            }
            else {
                hx_mark("@L5443");
                as_.cmovae(dst_gpq[3], std::get<x86::Mem>(sign));
            }
            as_.cmp(x86::rcx, 128);
            as_.cmovae(dst_gpq[0], dst_gpq[1]);
            as_.cmovae(dst_gpq[1], dst_gpq[2]);
            as_.cmovae(dst_gpq[2], sign_gpq);
            as_.cmp(x86::rcx, 192);
            as_.cmovae(dst_gpq[0], dst_gpq[1]);
            as_.cmovae(dst_gpq[1], sign_gpq);
            as_.cmp(x86::rcx, 256);
            as_.cmovae(dst_gpq[0], sign_gpq);
            as_.shrd(dst_gpq[0], dst_gpq[1], x86::cl);
            as_.shrd(dst_gpq[1], dst_gpq[2], x86::cl);
            as_.shrd(dst_gpq[2], dst_gpq[3], x86::cl);
            if constexpr (shift_type == ShiftType::SHR) {
                hx_mark("@L5458");
                as_.shrx(dst_gpq[3], dst_gpq[3], x86::rcx);
            }
            else {
                hx_mark("@L5461");
                as_.sarx(dst_gpq[3], dst_gpq[3], x86::rcx);
            }
        }

        if (restore_reg_context) {
            hx_mark("@L5466");
            as_.pop(reg_context);
        }
        if (restore_rcx_from_rax) {
            hx_mark("@L5469");
            as_.mov(x86::rcx, x86::rax);
        }
        MONAD_DEBUG_ASSERT(rcx_gpq[rcx_gpq_ix] == x86::rax);
        rcx_gpq[rcx_gpq_ix] = x86::rcx;

        return dst;
    }

    template <Emitter::ShiftType shift_type, typename... LiveSet>
    StackElemRef Emitter::shift_avx_reg_by_non_literal(
        StackElemRef shift, StackElemRef value,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5482 shift_avx_reg_by_non_literal");
        MONAD_DEBUG_ASSERT(value->avx_reg().has_value());

        AvxRegReserv const value_reserv{value};
        auto const in = avx_reg_to_ymm(*value->avx_reg());

        destructive_mov_stack_elem_to_bounded_rax(
            std::move(shift),
            256,
            std::tuple_cat(std::make_tuple(value), live));

        // Allocate result before temporary avx registers, so that result
        // is likely to have lower avx reg, which better avoids spill.
        auto [result, result_reserv] = alloc_avx_reg();
        auto const out = avx_reg_to_ymm(*result->avx_reg());

        auto [tmp1_elem, tmp1_reserv] = alloc_avx_reg();
        auto const tmp1 = avx_reg_to_ymm(*tmp1_elem->avx_reg());

        auto [tmp2_elem, tmp2_reserv] = alloc_avx_reg();
        auto const tmp2 = avx_reg_to_ymm(*tmp2_elem->avx_reg());

        // For demostration purposes, suppose
        //   * eax = 67 and
        //   * in = {v0, v1, v2, v3, v4, v5, v6, v7},
        // where each component of value_y is a dword value (4 bytes).

        as_.vmovd(tmp1.xmm(), x86::eax);
        // tmp1 = 67
        as_.vpsrld(tmp1.xmm(), tmp1.xmm(), 5);
        // tmp1 = 2
        as_.vpbroadcastd(tmp1, tmp1.xmm());
        // tmp1 = {2, 2, 2, 2, 2, 2, 2, 2}

        if constexpr (shift_type == ShiftType::SHL) {
            hx_mark("@L5516");
            as_.vpmovzxbd(tmp2, rodata_.add8(0x0706050403020100));
            // tmp2 = {0, 1, 2, 3, 4, 5, 6, 7}
            as_.vpsubd(out, tmp2, tmp1);
            // out = {-2, -1, 0, 1, 2, 3, 4, 5}
            as_.vpsrad(tmp2, out, 31);
            // tmp2 = {-1, -1, 0, 0, 0, 0, 0, 0}
            as_.vpermd(out, out, in);
            // out = {v6, v7, v0, v1, v2, v3, v4, v5}
            as_.vpandn(tmp2, tmp2, out);
            // tmp2 = {0, 0, v0, v1, v2, v3, v4, v5}

            as_.vpmovsxbd(out, rodata_.add8(0x06050403020100ff));
            // out = {-1, 0, 1, 2, 3, 4, 5, 6}
            as_.vpsubd(tmp1, out, tmp1);
            // tmp1 = {-3, -2, -1, 0, 1, 2, 3, 4}
            as_.vpsrad(out, tmp1, 31);
            // out = {-1, -1, -1, 0, 0, 0, 0, 0}
            as_.vpermd(tmp1, tmp1, in);
            // tmp1 = {v5, v6, v7, v0, v1, v2, v3, v4}
            as_.vpandn(out, out, tmp1);
            // out = {0, 0, 0, v0, v1, v2, v3, v4}

            as_.and_(x86::eax, 31);
            // eax = 3
            as_.vmovd(tmp1.xmm(), x86::eax);
            // tmp1 = 3
            as_.vpslld(tmp2, tmp2, tmp1.xmm());
            // tmp2 = {0, 0, v0<<3, v1<<3, v2<<3, v3<<3, v4<<3, v5<<3}

            as_.neg(x86::eax);
            // eax = -3
            as_.add(x86::eax, 32);
            // eax = 29
            as_.vmovd(tmp1.xmm(), x86::eax);
            // tmp1 = 29
            as_.vpsrld(out, out, tmp1.xmm());
            // out = {0, 0, 0, v0>>29, v1>>29, v2>>29, v3>>29, v4>>29}

            as_.vpor(out, out, tmp2);
        }
        else {
            hx_mark("@L5557");
            auto [tmp3_elem, tmp3_reserv] = alloc_avx_reg();
            auto const tmp3 = avx_reg_to_ymm(*tmp3_elem->avx_reg());

            auto mask_elem = result;
            auto mask_reserv = result_reserv;
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5563");
                auto [e, r] = alloc_avx_reg();
                mask_elem = e;
                mask_reserv = r;
            }

            // Beware that mask = out iff shift type is SHR.
            auto const mask = avx_reg_to_ymm(*mask_elem->avx_reg());

            as_.vpbroadcastd(tmp3, rodata_.add4(7));
            // tmp3 = {7, 7, 7, 7, 7, 7, 7, 7}

            uint256_t const perm1_off{
                0x0100000000, 0x0300000002, 0x0500000004, 0x0700000006};
            as_.vpaddd(out, tmp1, rodata_.add32(perm1_off));
            // out = {2, 3, 4, 5, 6, 7, 8, 9}
            as_.vpermd(tmp2, out, in);
            // tmp2 = {v2, v3, v4, v5, v6, v7, v0, v1}
            as_.vpcmpgtd(mask, out, tmp3);
            // mask = {0, 0, 0, 0, 0, 0, -1, -1}
            as_.vpandn(tmp2, mask, tmp2);
            // tmp2 = {v2, v3, v4, v5, v6, v7, 0, 0}

            // The mask/out register is not live here if shift type is SHR

            uint256_t const perm2_off{
                0x0200000001, 0x0400000003, 0x0600000005, 0x0800000007};
            as_.vpaddd(out, tmp1, rodata_.add32(perm2_off));
            // out = {3, 4, 5, 6, 7, 8, 9, 10}
            as_.vpermd(tmp1, out, in);
            // tmp1 = {v3, v4, v5, v6, v7, v0, v1, v2}
            as_.vpcmpgtd(out, out, tmp3);
            // out = {0, 0, 0, 0, 0, -1, -1, -1}
            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5596");
                as_.vpermd(tmp3, tmp3, in);
                // tmp3 = {v7, v7, ..., v7}
                as_.vpsrad(tmp3, tmp3, 31);
                // tmp3 = {sign, sign, ..., sign}
                as_.vpand(tmp3, out, tmp3);
                // tmp3 = {0, 0, 0, 0, 0, sign, sign, sign}
            }
            as_.vpandn(out, out, tmp1);
            // result_y = {v3, v4, v5, v6, v7, 0, 0, 0}

            as_.and_(x86::eax, 31);
            // eax = 3
            as_.vmovd(tmp1.xmm(), x86::eax);
            // tmp1 = 3
            as_.vpsrld(tmp2, tmp2, tmp1.xmm());
            // tmp2 = {v2>>3, v3>>3, v4>>3, v5>>3, v6>>3, v7>>3, 0, 0}

            as_.neg(x86::eax);
            // eax = -3
            as_.add(x86::eax, 32);
            // eax = 29
            as_.vmovd(tmp1.xmm(), x86::eax);
            // tmp1 = 29
            as_.vpslld(out, out, tmp1.xmm());
            // out = {v3<<29, v4<<29, v5<<29, v6<<29, v7<<29, 0, 0, 0}

            as_.vpor(out, out, tmp2);

            if constexpr (shift_type == ShiftType::SAR) {
                hx_mark("@L5625");
                as_.vpslld(tmp1, tmp3, tmp1.xmm());
                // tmp1 = {0, 0, 0, 0, 0, sign<<29, sign<<29, sign<<29}
                as_.vpand(tmp2, tmp3, mask);
                // tmp2 = {0, 0, 0, 0, 0, 0, sign, sign}
                as_.vpor(tmp1, tmp1, tmp2);
                // tmp1 = {0, 0, 0, 0, 0, sign<<29, sign, sign}
                as_.vpor(out, out, tmp1);
            }
        }

        return result;
    }

    template <typename... LiveSet>
    std::tuple<
        StackElemRef, Emitter::LocationType, StackElemRef,
        Emitter::LocationType>
    Emitter::prepare_general_dest_and_source(
        bool commutative, StackElemRef dst, StackElemRef src,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5646 prepare_general_dest_and_source");
        RegReserv const dst_reserv{dst};
        RegReserv const src_reserv{src};

        if (dst == src) {
            hx_mark("@L5650");
            if (!dst->general_reg()) {
                hx_mark("@L5651");
                mov_stack_elem_to_general_reg(dst);
            }
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::GeneralReg};
        }

        if (commutative) {
            hx_mark("@L5661");
            auto const src_ord = get_stack_elem_general_order_index(src, live);
            auto const dst_ord = get_stack_elem_general_order_index(dst, live);
            if (src_ord < dst_ord) {
                hx_mark("@L5664");
                std::swap(dst, src);
            }
        }

        if (!dst->general_reg()) {
            hx_mark("@L5669");
            if (dst->literal()) {
                hx_mark("@L5670");
                mov_literal_to_general_reg(dst);
            }
            else if (dst->stack_offset()) {
                hx_mark("@L5673");
                mov_stack_offset_to_general_reg(dst);
            }
            else {
                hx_mark("@L5676");
                MONAD_DEBUG_ASSERT(dst->avx_reg().has_value());
                mov_avx_reg_to_general_reg(dst);
            }
        }

        if (src->general_reg()) {
            hx_mark("@L5682");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::GeneralReg};
        }
        if (src->literal() && is_literal_bounded(*src->literal())) {
            hx_mark("@L5689");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::Literal};
        }
        if (src->stack_offset()) {
            hx_mark("@L5696");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::StackOffset};
        }
        if (src->literal()) {
            hx_mark("@L5703");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::Literal};
        }
        MONAD_DEBUG_ASSERT(src->avx_reg().has_value());
        mov_avx_reg_to_stack_offset(src);
        return {
            std::move(dst),
            LocationType::GeneralReg,
            std::move(src),
            LocationType::StackOffset};
    }

    template <typename... LiveSet>
    std::tuple<
        StackElemRef, Emitter::LocationType, StackElemRef,
        Emitter::LocationType>
    Emitter::get_general_dest_and_source(
        bool commutative, StackElemRef dst_in, StackElemRef src_in,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5726 get_general_dest_and_source");
        auto [dst, dst_loc, src, src_loc] = prepare_general_dest_and_source(
            commutative, std::move(dst_in), std::move(src_in), live);
        RegReserv const dst_reserv{dst};
        RegReserv const src_reserv{src};

        MONAD_DEBUG_ASSERT(dst_loc == LocationType::GeneralReg);
        auto new_dst = release_general_reg(dst, live);
        if (dst == src) {
            hx_mark("@L5734");
            return {new_dst, dst_loc, new_dst, src_loc};
        }
        else {
            hx_mark("@L5737");
            return {std::move(new_dst), dst_loc, std::move(src), src_loc};
        }
    }

    Emitter::Operand Emitter::get_operand(
        StackElemRef const elem, LocationType const loc,
        bool const always_add_literal)
    {
        hx_mark("@F5745 get_operand");
        switch (loc) {
        case LocationType::StackOffset:
            return stack_offset_to_mem(*elem->stack_offset());
        case LocationType::GeneralReg:
            return general_reg_to_gpq256(*elem->general_reg());
        case LocationType::Literal:
            if (!always_add_literal && is_literal_bounded(*elem->literal())) {
                hx_mark("@L5752");
                return literal_to_imm256(*elem->literal());
            }
            else {
                hx_mark("@L5755");
                return rodata_.add_literal(*elem->literal());
            }
        case LocationType::AvxReg:
            return avx_reg_to_ymm(*elem->avx_reg());
        }

        std::unreachable();
    }

    template <
        Emitter::GeneralBinInstr<x86::Gp, x86::Gp> GG,
        Emitter::GeneralBinInstr<x86::Gp, x86::Mem> GM,
        Emitter::GeneralBinInstr<x86::Gp, asmjit::Imm> GI,
        Emitter::GeneralBinInstr<x86::Mem, x86::Gp> MG,
        Emitter::GeneralBinInstr<x86::Mem, asmjit::Imm> MI>
    void Emitter::general_bin_instr(
        StackElemRef dst, LocationType dst_loc, StackElemRef src,
        LocationType src_loc,
        std::function<bool(size_t, uint64_t)> is_no_operation)
    {
        hx_mark("@F5775 general_bin_instr");
        auto dst_op = get_operand(dst, dst_loc);
        auto src_op = get_operand(src, src_loc);
        MONAD_DEBUG_ASSERT(!std::holds_alternative<x86::Ymm>(src_op));

        size_t instr_ix = 0;
        auto isnop = [&] -> std::function<bool(size_t, size_t)> {
            if (src->literal()) {
                hx_mark("@L5782");
                return [&](size_t ins, size_t i) {
                    return is_no_operation(ins, src->literal()->value[i]);
                };
            }
            else {
                hx_mark("@L5787");
                return [](size_t, size_t) { return false; };
            }
        }();

        if (std::holds_alternative<Gpq256>(dst_op)) {
            hx_mark("@L5792");
            Gpq256 const &dst_gpq = std::get<Gpq256>(dst_op);
            std::visit(
                Cases{
                    [&](Gpq256 const &src_gpq) {
                        for (size_t i = 0; i < 4; ++i) {
                            hx_mark("@L5797");
                            if (!isnop(instr_ix, i)) {
                                hx_mark("@L5798");
                                (as_.*GG[instr_ix++])(dst_gpq[i], src_gpq[i]);
                            }
                        }
                    },
                    [&](x86::Mem const &src_mem) {
                        x86::Mem temp{src_mem};
                        if (!src->literal()) {
                            hx_mark("@L5805");
                            for (size_t i = 0; i < 4; ++i) {
                                hx_mark("@L5806");
                                (as_.*GM[instr_ix++])(dst_gpq[i], temp);
                                temp.addOffset(8);
                            }
                            return;
                        }
                        for (size_t i = 0; i < 4; ++i) {
                            hx_mark("@L5812");
                            uint64_t const x = src->literal()->value[i];
                            if (!is_no_operation(instr_ix, x)) {
                                hx_mark("@L5814");
                                if (is_uint64_bounded(x)) {
                                    hx_mark("@L5815");
                                    (as_.*GI[instr_ix++])(dst_gpq[i], x);
                                }
                                else {
                                    hx_mark("@L5818");
                                    (as_.*GM[instr_ix++])(dst_gpq[i], temp);
                                }
                            }
                            temp.addOffset(8);
                        }
                    },
                    [&](Imm256 const &src_imm) {
                        for (size_t i = 0; i < 4; ++i) {
                            hx_mark("@L5826");
                            if (!isnop(instr_ix, i)) {
                                hx_mark("@L5827");
                                (as_.*GI[instr_ix++])(dst_gpq[i], src_imm[i]);
                            }
                        }
                    },
                    [](x86::Ymm const &) { std::unreachable(); },
                },
                src_op);
        }
        else {
            hx_mark("@L5836");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(dst_op));
            MONAD_DEBUG_ASSERT(!std::holds_alternative<x86::Mem>(src_op));

            x86::Mem const &dst_mem = std::get<x86::Mem>(dst_op);
            std::visit(
                Cases{
                    [&](Gpq256 const &src_gpq) {
                        x86::Mem temp{dst_mem};
                        for (size_t i = 0; i < 4; ++i) {
                            hx_mark("@L5845");
                            if (!isnop(instr_ix, i)) {
                                hx_mark("@L5846");
                                (as_.*MG[instr_ix++])(temp, src_gpq[i]);
                            }
                            temp.addOffset(8);
                        }
                    },
                    [&](Imm256 const &src_imm) {
                        x86::Mem temp{dst_mem};
                        for (size_t i = 0; i < 4; ++i) {
                            hx_mark("@L5854");
                            if (!isnop(instr_ix, i)) {
                                hx_mark("@L5855");
                                (as_.*MI[instr_ix++])(temp, src_imm[i]);
                            }
                            temp.addOffset(8);
                        }
                    },
                    [](auto const &) { std::unreachable(); },
                },
                src_op);
        }

        // This is not required to be an invariant, but it currently is:
        MONAD_DEBUG_ASSERT(instr_ix > 0);
    }

    template <typename... LiveSet>
    std::tuple<StackElemRef, StackElemRef, Emitter::LocationType>
    Emitter::get_una_arguments(
        bool is_dst_mutated, StackElemRef dst,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5875 get_una_arguments");
        MONAD_DEBUG_ASSERT(!dst->literal());
        RegReserv const dst_reserv{dst};

        if (!dst->avx_reg()) {
            hx_mark("@L5879");
            if (dst->general_reg()) {
                hx_mark("@L5880");
                if (!is_dst_mutated) {
                    hx_mark("@L5881");
                    return {dst, dst, LocationType::GeneralReg};
                }
                auto const new_dst = release_general_reg(std::move(dst), live);
                return {new_dst, new_dst, LocationType::GeneralReg};
            }
            MONAD_DEBUG_ASSERT(dst->stack_offset().has_value());
            // to prevent a store forwarding stall, load the stack offset back
            // into gpr if we know it was previously stored there from another
            // gpr
            if (dst->stack_offset()->moved_from == PrevLoc::GprReg) {
                hx_mark("@L5891");
                mov_stack_offset_to_general_reg(dst);
                if (!is_dst_mutated) {
                    hx_mark("@L5893");
                    return {dst, dst, LocationType::GeneralReg};
                }
                auto const new_dst = release_general_reg(std::move(dst), live);
                return {new_dst, new_dst, LocationType::GeneralReg};
            }
            mov_stack_offset_to_avx_reg(dst);
        }

        if (!is_dst_mutated) {
            hx_mark("@L5902");
            return {dst, dst, LocationType::AvxReg};
        }
        if (!is_live(dst, live)) {
            hx_mark("@L5905");
            auto const n = stack_.release_avx_reg(std::move(dst));
            return {n, n, LocationType::AvxReg};
        }
        auto [n, _] = alloc_avx_reg();
        return {n, dst, LocationType::AvxReg};
    }

    template <typename... LiveSet>
    std::tuple<
        StackElemRef, Emitter::LocationType, StackElemRef,
        Emitter::LocationType>
    Emitter::prepare_avx_or_general_arguments_commutative(
        StackElemRef dst, StackElemRef src, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F5919 prepare_avx_or_general_arguments_commutative");
        RegReserv const dst_reserv{dst};
        RegReserv const src_reserv{src};

        if (dst.get() == src.get()) {
            hx_mark("@L5923");
            if (dst->avx_reg()) {
                hx_mark("@L5924");
                return {
                    std::move(dst),
                    LocationType::AvxReg,
                    std::move(src),
                    LocationType::AvxReg};
            }
            if (dst->general_reg()) {
                hx_mark("@L5931");
                return {
                    std::move(dst),
                    LocationType::GeneralReg,
                    std::move(src),
                    LocationType::GeneralReg};
            }
            if (dst->literal()) {
                hx_mark("@L5938");
                mov_literal_to_avx_reg(dst);
                return {
                    std::move(dst),
                    LocationType::AvxReg,
                    std::move(src),
                    LocationType::AvxReg};
            }
            MONAD_DEBUG_ASSERT(dst->stack_offset().has_value());
            if (dst->stack_offset()->moved_from == PrevLoc::GprReg) {
                hx_mark("@L5947");
                mov_stack_offset_to_general_reg(dst);
                return {
                    std::move(dst),
                    LocationType::GeneralReg,
                    std::move(src),
                    LocationType::GeneralReg};
            }
            mov_stack_offset_to_avx_reg(dst);
            return {
                std::move(dst),
                LocationType::AvxReg,
                std::move(src),
                LocationType::AvxReg};
        }

        // We need to consider 15 cases for the pair (dst, src).
        // The case (literal, literal) is not possible.
        MONAD_DEBUG_ASSERT(
            !dst->literal().has_value() || !src->literal().has_value());

        // Case 1: (avx, avx)
        if (dst->avx_reg() && src->avx_reg()) {
            hx_mark("@L5969");
            return {
                std::move(dst),
                LocationType::AvxReg,
                std::move(src),
                LocationType::AvxReg};
        }
        // Case 2: (avx, literal)
        if (dst->avx_reg() && src->literal()) {
            hx_mark("@L5977");
            return {
                std::move(dst),
                LocationType::AvxReg,
                std::move(src),
                LocationType::Literal};
        }
        // Case 3: (literal, avx)
        if (dst->literal() && src->avx_reg()) {
            hx_mark("@L5985");
            return {
                std::move(src),
                LocationType::AvxReg,
                std::move(dst),
                LocationType::Literal};
        }
        // Case 4: (avx, stack)
        if (dst->avx_reg() && src->stack_offset()) {
            hx_mark("@L5993");
            return {
                std::move(dst),
                LocationType::AvxReg,
                std::move(src),
                LocationType::StackOffset};
        }
        // Case 5: (stack, avx)
        if (dst->stack_offset() && src->avx_reg()) {
            hx_mark("@L6001");
            return {
                std::move(src),
                LocationType::AvxReg,
                std::move(dst),
                LocationType::StackOffset};
        }
        // Case 6: (literal, stack)
        if (dst->literal() && src->stack_offset()) {
            hx_mark("@L6009");
            mov_literal_to_avx_reg(dst);
            return {
                std::move(dst),
                LocationType::AvxReg,
                std::move(src),
                LocationType::StackOffset};
        }
        // Case 7: (stack, literal)
        if (dst->stack_offset() && src->literal()) {
            hx_mark("@L6018");
            mov_literal_to_avx_reg(src);
            return {
                std::move(src),
                LocationType::AvxReg,
                std::move(dst),
                LocationType::StackOffset};
        }
        // Case 8: (stack, stack)
        if (dst->stack_offset() && src->stack_offset()) {
            hx_mark("@L6027");
            if (dst->stack_offset()->moved_from == PrevLoc::GprReg ||
                src->stack_offset()->moved_from == PrevLoc::GprReg) {
                    hx_mark("@L6029");
                mov_stack_offset_to_general_reg(dst);
                return {
                    std::move(dst),
                    LocationType::GeneralReg,
                    std::move(src),
                    LocationType::StackOffset};
            }
            mov_stack_offset_to_avx_reg(dst);
            return {
                std::move(dst),
                LocationType::AvxReg,
                std::move(src),
                LocationType::StackOffset};
        }
        // Case 9-15:
        //  (general, general)
        //  (general, stack)
        //  (stack, general)
        //  (general, literal)
        //  (literal, general)
        //  (general, avx)
        //  (avx, general)
        MONAD_DEBUG_ASSERT(dst->general_reg() || src->general_reg());
        return prepare_general_dest_and_source(
            true, std::move(dst), std::move(src), live);
    }

    template <typename... LiveSet>
    std::tuple<
        StackElemRef, StackElemRef, Emitter::LocationType, StackElemRef,
        Emitter::LocationType>
    Emitter::get_avx_or_general_arguments_commutative(
        StackElemRef dst_in, StackElemRef src_in,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F6064 get_avx_or_general_arguments_commutative");
        auto [dst, dst_loc, src, src_loc] =
            prepare_avx_or_general_arguments_commutative(
                std::move(dst_in), std::move(src_in), live);
        RegReserv const dst_reserv{dst};
        RegReserv const src_reserv{src};

        if (dst_loc == LocationType::GeneralReg) {
            hx_mark("@L6071");
            auto const new_dst = release_general_reg(dst, live);
            if (dst == src) {
                hx_mark("@L6073");
                return {new_dst, new_dst, dst_loc, new_dst, src_loc};
            }
            else {
                hx_mark("@L6076");
                return {new_dst, new_dst, dst_loc, std::move(src), src_loc};
            }
        }
        else {
            hx_mark("@L6080");
            MONAD_DEBUG_ASSERT(dst_loc == LocationType::AvxReg);
            if (is_live(dst, live)) {
                hx_mark("@L6082");
                if (!is_live(src, live) && src_loc == LocationType::AvxReg) {
                    hx_mark("@L6083");
                    auto const n = stack_.release_avx_reg(src);
                    return {n, std::move(dst), dst_loc, n, src_loc};
                }
                else {
                    hx_mark("@L6087");
                    auto [n, _] = alloc_avx_reg();
                    return {
                        n, std::move(dst), dst_loc, std::move(src), src_loc};
                }
            }

            auto const n = stack_.release_avx_reg(dst);
            if (dst == src) {
                hx_mark("@L6095");
                return {n, n, dst_loc, n, src_loc};
            }
            else {
                hx_mark("@L6098");
                return {n, n, dst_loc, std::move(src), src_loc};
            }
        }
    }

    template <
        Emitter::GeneralBinInstr<x86::Gp, x86::Gp> GG,
        Emitter::GeneralBinInstr<x86::Gp, x86::Mem> GM,
        Emitter::GeneralBinInstr<x86::Gp, asmjit::Imm> GI,
        Emitter::GeneralBinInstr<x86::Mem, x86::Gp> MG,
        Emitter::GeneralBinInstr<x86::Mem, asmjit::Imm> MI,
        Emitter::AvxBinInstr<x86::Vec> VV, Emitter::AvxBinInstr<x86::Mem> VM>
    void Emitter::avx_or_general_bin_instr(
        StackElemRef dst, StackElemRef left, LocationType left_loc,
        StackElemRef right, LocationType right_loc,
        std::function<bool(size_t, uint64_t)> is_no_operation)
    {
        hx_mark("@F6115 avx_or_general_bin_instr");
        if (left_loc == LocationType::GeneralReg) {
            hx_mark("@L6116");
            general_bin_instr<GG, GM, GI, MG, MI>(
                std::move(left),
                left_loc,
                std::move(right),
                right_loc,
                std::move(is_no_operation));
            return;
        }
        auto left_op = get_operand(left, left_loc);
        auto right_op = get_operand(
            right, right_loc, std::holds_alternative<x86::Ymm>(left_op));
        MONAD_DEBUG_ASSERT(dst->avx_reg().has_value());
        MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Ymm>(left_op));
        if (std::holds_alternative<x86::Ymm>(right_op)) {
            hx_mark("@L6130");
            (as_.*VV)(
                avx_reg_to_ymm(*dst->avx_reg()),
                std::get<x86::Ymm>(left_op),
                std::get<x86::Ymm>(right_op));
        }
        else {
            hx_mark("@L6136");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(right_op));
            (as_.*VM)(
                avx_reg_to_ymm(*dst->avx_reg()),
                std::get<x86::Ymm>(left_op),
                std::get<x86::Mem>(right_op));
        }
    }

    void Emitter::negate_gpq256(Gpq256 const &gpq)
    {
        hx_mark("@F6146 negate_gpq256");
        for (auto const &r : gpq) {
            hx_mark("@L6147");
            as_.not_(r);
        }
        as_.add(gpq[0], 1);
        as_.adc(gpq[1], 0);
        as_.adc(gpq[2], 0);
        as_.adc(gpq[3], 0);
    }

    // Will not mutate the lower 64 bits, even when `elem` is not live.
    template <typename... LiveSet>
    void Emitter::test_high_bits192(
        StackElemRef elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F6160 test_high_bits192");
        MONAD_DEBUG_ASSERT(!stack_.has_deferred_comparison());
        MONAD_DEBUG_ASSERT(!elem->literal());
        if (elem->general_reg()) {
            hx_mark("@L6163");
            auto const &gpq = general_reg_to_gpq256(*elem->general_reg());
            if (is_live(elem, live)) {
                hx_mark("@L6165");
                as_.mov(x86::rax, gpq[1]);
                as_.or_(x86::rax, gpq[2]);
                as_.or_(x86::rax, gpq[3]);
            }
            else {
                hx_mark("@L6170");
                as_.or_(gpq[1], gpq[2]);
                as_.or_(gpq[1], gpq[3]);
            }
        }
        else if (elem->avx_reg()) {
            hx_mark("@L6175");
            uint256_t const mask{
                0,
                std::numeric_limits<uint64_t>::max(),
                std::numeric_limits<uint64_t>::max(),
                std::numeric_limits<uint64_t>::max()};
            as_.vptest(avx_reg_to_ymm(*elem->avx_reg()), rodata_.add32(mask));
        }
        else {
            hx_mark("@L6183");
            MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
            auto mem = stack_offset_to_mem(*elem->stack_offset());
            mem.addOffset(8);
            as_.mov(x86::rax, mem);
            mem.addOffset(8);
            as_.or_(x86::rax, mem);
            mem.addOffset(8);
            as_.or_(x86::rax, mem);
        }
    }

    template <uint8_t bits, typename... LiveSet>
    std::variant<std::monostate, asmjit::x86::Gpq, uint64_t>
    Emitter::is_bounded_by_bits(
        StackElemRef elem, asmjit::Label const &skip_label,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F6200 is_bounded_by_bits");
        static_assert(bits < 64);

        if (elem->literal()) {
            hx_mark("@L6203");
            auto const &lit = elem->literal()->value;
            if (lit >= uint64_t{1} << bits) {
                hx_mark("@L6205");
                as_.jmp(skip_label);
                return {};
            }
            return static_cast<uint64_t>(lit);
        }

        static constexpr auto mask = std::numeric_limits<uint64_t>::max()
                                     << bits;

        if (elem->general_reg()) {
            hx_mark("@L6215");
            auto const &gpq = general_reg_to_gpq256(*elem->general_reg());
            if (is_live(elem, live)) {
                hx_mark("@L6217");
                as_.mov(x86::rax, gpq[0]);
                if constexpr (bits < 32) {
                    hx_mark("@L6219");
                    as_.and_(x86::rax, mask);
                }
                else {
                    hx_mark("@L6222");
                    as_.and_(x86::rax, rodata_.add8(mask));
                }
                as_.or_(x86::rax, gpq[1]);
                as_.or_(x86::rax, gpq[2]);
                as_.or_(x86::rax, gpq[3]);
                as_.jnz(skip_label);
                return gpq[0];
            }
            as_.mov(x86::rax, gpq[0]);
            if constexpr (bits < 32) {
                hx_mark("@L6232");
                as_.and_(gpq[0], mask);
            }
            else {
                hx_mark("@L6235");
                as_.and_(gpq[0], rodata_.add8(mask));
            }
            as_.or_(gpq[3], gpq[2]);
            as_.or_(gpq[1], gpq[0]);
            as_.or_(gpq[3], gpq[1]);
            as_.jnz(skip_label);
            return x86::rax;
        }

        if (elem->avx_reg()) {
            hx_mark("@L6245");
            auto const y = avx_reg_to_ymm(*elem->avx_reg());
            auto const mask = std::numeric_limits<uint256_t>::max() << bits;
            as_.vptest(y, rodata_.add32(mask));
            as_.jnz(skip_label);
            as_.vmovd(x86::eax, y.xmm());
            return x86::rax;
        }

        MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());

        auto mem = stack_offset_to_mem(*elem->stack_offset());
        mem.addOffset(8);
        as_.mov(x86::rax, mem);
        mem.addOffset(8);
        as_.or_(x86::rax, mem);
        mem.addOffset(8);
        as_.or_(x86::rax, mem);
        as_.jnz(skip_label);
        mem.addOffset(-24);
        as_.mov(x86::rax, mem);
        if constexpr (bits < 32) {
            hx_mark("@L6266");
            as_.test(x86::rax, mask);
        }
        else {
            hx_mark("@L6269");
            as_.test(rodata_.add8(mask), x86::rax);
        }
        as_.jnz(skip_label);
        return x86::rax;
    }

    template <runtime::Memory::Version memory_version, typename... LiveSet>
    std::optional<asmjit::x86::Mem> Emitter::touch_memory(
        StackElemRef offset, int32_t read_size,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F6280 touch_memory");
        {
            hx_mark("@L6281");
            RegReserv const offset_reserv{offset};
            discharge_deferred_comparison();
        }

        MONAD_DEBUG_ASSERT(read_size <= 32);

        // Make sure offset bits are sufficiently small to
        // not overflow a runtime::Bin<30> after incrementing by `read_size`.
        static_assert(runtime::Memory::offset_bits <= 29);

        // Make sure reg_context is rbx, because the functions
        // monad_vm_runtime_increase_memory_raw_* expect context to be passed
        // in rbx.
        static_assert(reg_context == x86::rbx);

        // It is later assumed that volatile_general_reg coincides with
        // rdi_general_reg.
        MONAD_DEBUG_ASSERT(rdi_general_reg == volatile_general_reg);

        if (!offset->literal()) {
            hx_mark("@L6301");
            // Memory never shrinks, so these checks need to pass only once.
            if (offset->touched_memory_size() >= read_size) {
                hx_mark("@L6303");
                mov_stack_elem_low64_to_gpq(offset, x86::rax);
                as_.add(
                    x86::rax,
                    x86::qword_ptr(
                        reg_context, runtime::context_offset_memory_data));
                return x86::qword_ptr(x86::rax);
            }
            offset->set_touched_memory_size(read_size);
        }

        auto const after_increase_label = as_.newLabel();

        auto const offset_op = is_bounded_by_bits<runtime::Memory::offset_bits>(
            std::move(offset), error_label_, live);

        if (std::holds_alternative<std::monostate>(offset_op)) {
            hx_mark("@L6319");
            return std::nullopt;
        }

        if (std::holds_alternative<uint64_t>(offset_op)) {
            hx_mark("@L6323");
            release_volatile_general_reg(live);
            spill_avx_reg_range(5);

            auto const lit = std::get<uint64_t>(offset_op);
            auto const read_end = static_cast<int32_t>(lit) + read_size;
            static_assert(sizeof(runtime::Memory::size) == sizeof(uint32_t));
            as_.cmp(
                x86::dword_ptr(
                    reg_context, runtime::context_offset_memory_size),
                read_end);
            as_.jae(after_increase_label);
            as_.mov(x86::rdi, read_end);
        }
        else {
            hx_mark("@L6337");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Gpq>(offset_op));
            auto const r = std::get<x86::Gpq>(offset_op);
            if (r != x86::rax) {
                hx_mark("@L6340");
                as_.mov(x86::rax, r);
            }
            release_volatile_general_reg(live);
            spill_avx_reg_range(5);

            as_.lea(x86::rdi, x86::byte_ptr(x86::rax, read_size));
            static_assert(sizeof(runtime::Memory::size) == sizeof(uint32_t));
            as_.cmp(
                x86::dword_ptr(
                    reg_context, runtime::context_offset_memory_size),
                x86::edi);
            as_.jae(after_increase_label);
        }

        auto const increase_memory_fn =
            memory_version == runtime::Memory::Version::V1
                ? rodata_.add_external_function(
                      monad_vm_runtime_increase_memory_raw_v1)
                : rodata_.add_external_function(
                      monad_vm_runtime_increase_memory_raw_mip3);

        as_.call(increase_memory_fn);

        as_.bind(after_increase_label);

        if (std::holds_alternative<uint64_t>(offset_op)) {
            hx_mark("@L6366");
            as_.mov(
                x86::rax,
                x86::qword_ptr(
                    reg_context, runtime::context_offset_memory_data));
            auto const lit = std::get<uint64_t>(offset_op);
            return x86::qword_ptr(x86::rax, static_cast<int32_t>(lit));
        }
        else {
            hx_mark("@L6374");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Gpq>(offset_op));
            static_assert(sizeof(runtime::Memory::data) == sizeof(uint64_t));
            as_.add(
                x86::rax,
                x86::qword_ptr(
                    reg_context, runtime::context_offset_memory_data));
            return x86::qword_ptr(x86::rax);
        }
    }

    StackElemRef Emitter::negate_by_sub(StackElemRef const elem)
    {
        hx_mark("@F6386 negate_by_sub");
        MONAD_DEBUG_ASSERT(!elem->literal().has_value());

        GeneralRegReserv const reserv{elem};

        auto [dst, dst_reserv] = alloc_general_reg();
        mov_literal_to_gpq256(
            Literal{0}, general_reg_to_gpq256(*dst->general_reg()));

        auto const &d = general_reg_to_gpq256(*dst->general_reg());
        if (elem->general_reg()) {
            hx_mark("@L6396");
            auto const &e = general_reg_to_gpq256(*elem->general_reg());
            as_.sub(d[0], e[0]);
            for (size_t i = 1; i < 4; ++i) {
                hx_mark("@L6399");
                as_.sbb(d[i], e[i]);
            }
        }
        else {
            hx_mark("@L6403");
            if (!elem->stack_offset()) {
                hx_mark("@L6404");
                MONAD_DEBUG_ASSERT(elem->avx_reg().has_value());
                mov_avx_reg_to_stack_offset(elem);
            }
            auto m = stack_offset_to_mem(*elem->stack_offset());
            as_.sub(d[0], m);
            for (size_t i = 1; i < 4; ++i) {
                hx_mark("@L6410");
                m.addOffset(8);
                as_.sbb(d[i], m);
            }
        }

        return dst;
    }

    template <typename... LiveSet>
    StackElemRef
    Emitter::negate(StackElemRef elem, std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F6422 negate");
        if (elem->literal()) {
            hx_mark("@L6423");
            auto const &v = elem->literal()->value;
            return stack_.alloc_literal({-v});
        }
        {
            hx_mark("@L6427");
            RegReserv const elem_reserv{elem};
            discharge_deferred_comparison();
        }
        if (!elem->general_reg() ||
            (is_live(elem, live) && !elem->stack_offset() &&
             !elem->avx_reg())) {
                 hx_mark("@L6433");
            return negate_by_sub(std::move(elem));
        }
        auto dst = stack_.release_general_reg(std::move(elem));
        negate_gpq256(general_reg_to_gpq256(*dst->general_reg()));
        return dst;
    }

    // Scrambles rdx
    // Does not update eflags
    template <typename LeftOpType>
    void
    Emitter::mulx(x86::Gpq dst1, x86::Gpq dst2, LeftOpType left, x86::Gpq right)
    {
        hx_mark("@F6446 mulx");
        as_.mov(x86::rdx, left);
        as_.mulx(dst1, dst2, right);
    }

    template <bool Is32Bit, typename LeftOpType>
    void Emitter::gpr_mul_by_gpq(x86::Gpq dst, LeftOpType left, x86::Gpq right)
    {
        hx_mark("@F6453 gpr_mul_by_gpq");
        as_.mov(dst, right);
        if constexpr (Is32Bit) {
            hx_mark("@L6455");
            if constexpr (std::is_same_v<LeftOpType, x86::Gpq>) {
                hx_mark("@L6456");
                as_.imul(dst.r32(), left.r32());
            }
            else {
                hx_mark("@L6459");
                as_.imul(dst.r32(), left);
            }
        }
        else {
            hx_mark("@L6463");
            as_.imul(dst, left);
        }
    }

    // Sets overflow and carry flags according to imul
    template <bool Is32Bit, typename LeftOpType>
    void Emitter::gpr_mul_by_int32_via_imul(
        x86::Gpq dst, LeftOpType left, int32_t right)
    {
        hx_mark("@F6472 gpr_mul_by_int32_via_imul");
        MONAD_DEBUG_ASSERT(right != 0 && right != 1);
        if constexpr (Is32Bit) {
            hx_mark("@L6474");
            if constexpr (std::is_same_v<LeftOpType, x86::Gpq>) {
                hx_mark("@L6475");
                as_.imul(dst.r32(), left.r32(), right);
            }
            else {
                hx_mark("@L6478");
                as_.imul(dst.r32(), left, right);
            }
        }
        else {
            hx_mark("@L6482");
            as_.imul(dst, left, right);
        }
    }

    template <bool Is32Bit, typename LeftOpType>
    void Emitter::gpr_mul_by_uint64_via_shl(
        x86::Gpq dst, LeftOpType left, uint64_t right)
    {
        hx_mark("@F6490 gpr_mul_by_uint64_via_shl");
        MONAD_DEBUG_ASSERT(std::popcount(right) == 1);
        if constexpr (Is32Bit) {
            hx_mark("@L6492");
            MONAD_DEBUG_ASSERT(right <= std::numeric_limits<uint32_t>::max());
            if constexpr (std::is_same_v<LeftOpType, x86::Gpq>) {
                hx_mark("@L6494");
                // Always mov when right == 1 to clear upper 32 bits of dst:
                if (dst != left || right == 1) {
                    hx_mark("@L6496");
                    as_.mov(dst.r32(), left.r32());
                }
            }
            else {
                hx_mark("@L6500");
                as_.mov(dst.r32(), left);
            }
            if (right > 1) {
                hx_mark("@L6503");
                as_.shl(dst.r32(), std::bit_width(right) - 1);
            }
        }
        else {
            hx_mark("@L6507");
            if constexpr (std::is_same_v<LeftOpType, x86::Gpq>) {
                hx_mark("@L6508");
                if (dst != left) {
                    hx_mark("@L6509");
                    as_.mov(dst, left);
                }
            }
            else {
                hx_mark("@L6513");
                as_.mov(dst, left);
            }
            if (right > 1) {
                hx_mark("@L6516");
                as_.shl(dst, std::bit_width(right) - 1);
            }
        }
    }

    template <bool Is32Bit, typename LeftOpType>
    void Emitter::gpr_mul_by_uint64(
        x86::Gpq dst, LeftOpType left, uint64_t pre_right)
    {
        hx_mark("@F6525 gpr_mul_by_uint64");
        uint64_t right = pre_right;
        if constexpr (Is32Bit) {
            hx_mark("@L6527");
            right = static_cast<uint32_t>(pre_right);
        }
        if (right == 0) {
            hx_mark("@L6530");
            as_.xor_(dst.r32(), dst.r32());
        }
        else if (std::popcount(right) == 1) {
            hx_mark("@L6533");
            gpr_mul_by_uint64_via_shl<Is32Bit>(dst, left, right);
        }
        else {
            hx_mark("@L6536");
            MONAD_DEBUG_ASSERT(Is32Bit || is_uint64_bounded(right));
            int32_t r;
            std::memcpy(&r, &right, sizeof(r));
            gpr_mul_by_int32_via_imul<Is32Bit>(dst, left, r);
        }
    }

    template <bool Is32Bit, typename LeftOpType>
    void Emitter::gpr_mul_by_rax_or_uint64(
        asmjit::x86::Gpq dst, LeftOpType left, std::optional<uint64_t> i)
    {
        hx_mark("@F6547 gpr_mul_by_rax_or_uint64");
        if constexpr (Is32Bit) {
            hx_mark("@L6548");
            if (i) {
                hx_mark("@L6549");
                gpr_mul_by_uint64<Is32Bit>(dst, left, *i);
                return;
            }
        }
        else if (i && (is_uint64_bounded(*i) || std::popcount(*i) == 1)) {
            hx_mark("@L6554");
            gpr_mul_by_uint64<Is32Bit>(dst, left, *i);
            return;
        }
        gpr_mul_by_gpq<Is32Bit>(dst, left, x86::rax);
    }

    void Emitter::mul_with_bit_size_by_rax(
        size_t const bit_size, x86::Gpq const *const dst, Operand const &left,
        std::optional<uint64_t> const value_of_rax)
    {
        hx_mark("@F6564 mul_with_bit_size_by_rax");
        if ((bit_size & 63) && (bit_size & 63) <= 32) {
            hx_mark("@L6565");
            mul_with_bit_size_and_has_32_bit_by_rax<true>(
                bit_size, dst, left, value_of_rax);
        }
        else {
            hx_mark("@L6569");
            mul_with_bit_size_and_has_32_bit_by_rax<false>(
                bit_size, dst, left, value_of_rax);
        }
    }

    // Scrambles rdx
    template <bool Has32Bit>
    void Emitter::mul_with_bit_size_and_has_32_bit_by_rax(
        size_t bit_size, x86::Gpq const *dst, Operand const &left,
        std::optional<uint64_t> value_of_rax)
    {
        hx_mark("@F6580 mul_with_bit_size_and_has_32_bit_by_rax");
        MONAD_DEBUG_ASSERT(bit_size > 0 && bit_size <= 256);

        constexpr auto right = x86::rax;

        auto const last_ix = div64_ceil(bit_size) - 1;

        auto next_dst_pair = [&](size_t i) -> std::pair<x86::Gpq, x86::Gpq> {
            auto const dst1 = i == last_ix - 1 ? x86::rax : dst[i + 1];
            auto const dst2 = i == 0 ? dst[0] : x86::rdx;
            return {dst1, dst2};
        };

        auto post_add = [&](size_t i) {
            if (last_ix == 1) {
                hx_mark("@L6594");
                if constexpr (Has32Bit) {
                    hx_mark("@L6595");
                    as_.add(dst[1].r32(), x86::eax);
                }
                else {
                    hx_mark("@L6598");
                    as_.add(dst[1], x86::rax);
                }
            }
            else if (i > 0) {
                hx_mark("@L6602");
                if (i == 1) {
                    hx_mark("@L6603");
                    as_.add(dst[1], x86::rdx);
                }
                else {
                    hx_mark("@L6606");
                    as_.adc(dst[i], x86::rdx);
                }
                if (i == last_ix - 1) {
                    hx_mark("@L6609");
                    if constexpr (Has32Bit) {
                        hx_mark("@L6610");
                        as_.adc(dst[last_ix].r32(), x86::eax);
                    }
                    else {
                        hx_mark("@L6613");
                        as_.adc(dst[last_ix], x86::rax);
                    }
                }
            }
        };

        if (std::holds_alternative<Gpq256>(left)) {
            hx_mark("@L6620");
            auto const &lgpq = std::get<Gpq256>(left);
            gpr_mul_by_rax_or_uint64<Has32Bit>(
                dst[last_ix], lgpq[last_ix], value_of_rax);
            for (size_t i = 0; i < last_ix; ++i) {
                hx_mark("@L6624");
                auto [dst1, dst2] = next_dst_pair(i);
                mulx(dst1, dst2, lgpq[i], right);
                post_add(i);
            }
        }
        else {
            hx_mark("@L6630");
            MONAD_ASSERT(std::holds_alternative<x86::Mem>(left));
            auto mem = std::get<x86::Mem>(left);
            mem.addOffset(static_cast<int64_t>(last_ix) * 8);
            gpr_mul_by_rax_or_uint64<Has32Bit>(dst[last_ix], mem, value_of_rax);
            mem.addOffset(-(static_cast<int64_t>(last_ix) * 8));
            for (size_t i = 0; i < last_ix; ++i) {
                hx_mark("@L6636");
                auto [dst1, dst2] = next_dst_pair(i);
                mulx(dst1, dst2, mem, right);
                post_add(i);
                mem.addOffset(8);
            }
        }
    }

    Emitter::MulEmitter::MulEmitter(
        size_t const bit_size, Emitter &em, Operand const &left,
        RightMulArg const &right, x86::Gpq const *const dst,
        x86::Gpq const *const tmp)
        : bit_size_{bit_size}
        , em_{em}
        , left_{left}
        , right_{right}
        , dst_{dst}
        , tmp_{tmp}
        , is_dst_initialized_{}
    {
        hx_mark("@F6656 MulEmitter");
    }

    void Emitter::MulEmitter::init_mul_dst(
        size_t const sub_size, x86::Gpq *const mul_dst)
    {
        hx_mark("@F6661 init_mul_dst");
        size_t const N = div64_ceil(sub_size);
        if (is_dst_initialized_) {
            hx_mark("@L6663");
            for (size_t i = 0; i < N; ++i) {
                hx_mark("@L6664");
                mul_dst[i] = tmp_[i];
            }
        }
        else {
            hx_mark("@L6668");
            size_t const c = div64_ceil(bit_size_);
            for (size_t i = c - N, n = 0; i < c; ++i) {
                hx_mark("@L6670");
                mul_dst[n++] = dst_[i];
            }
        }
    }

    template <bool Has32Bit>
    void
    Emitter::MulEmitter::mul_sequence(size_t sub_size, x86::Gpq const *mul_dst)
    {
        hx_mark("@F6679 mul_sequence");
        size_t const word_count = div64_ceil(bit_size_);
        size_t const N = div64_ceil(sub_size);
        if (std::holds_alternative<uint256_t>(right_) &&
            std::get<uint256_t>(right_)[word_count - N] == 1) {
                hx_mark("@L6683");
            if (std::holds_alternative<Gpq256>(left_)) {
                hx_mark("@L6684");
                auto const &lgpq = std::get<Gpq256>(left_);
                size_t i = 0;
                for (; i < N - 1; ++i) {
                    hx_mark("@L6687");
                    em_.as_.mov(mul_dst[i], lgpq[i]);
                }
                if constexpr (Has32Bit) {
                    hx_mark("@L6690");
                    em_.as_.mov(mul_dst[i].r32(), lgpq[i].r32());
                }
                else {
                    hx_mark("@L6693");
                    em_.as_.mov(mul_dst[i], lgpq[i]);
                }
            }
            else {
                hx_mark("@L6697");
                MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(left_));
                auto lmem = std::get<x86::Mem>(left_);
                size_t i = 0;
                for (; i < N - 1; ++i) {
                    hx_mark("@L6701");
                    em_.as_.mov(mul_dst[i], lmem);
                    lmem.addOffset(8);
                }
                if constexpr (Has32Bit) {
                    hx_mark("@L6705");
                    em_.as_.mov(mul_dst[i].r32(), lmem);
                }
                else {
                    hx_mark("@L6708");
                    em_.as_.mov(mul_dst[i], lmem);
                }
            }
        }
        else if (N > 1) {
            hx_mark("@L6713");
            auto const known_value = std::visit(
                Cases{
                    [&](uint256_t const &r) {
                        auto x = r[word_count - N];
                        em_.as_.mov(x86::rax, x);
                        return std::optional{x};
                    },
                    [&](Gpq256 const &r) {
                        em_.as_.mov(x86::rax, r[word_count - N]);
                        return std::optional<uint64_t>{};
                    },
                    [&](x86::Mem r) {
                        r.addOffset(static_cast<int64_t>((word_count - N) * 8));
                        em_.as_.mov(x86::rax, r);
                        return std::optional<uint64_t>{};
                    },
                },
                right_);
            em_.mul_with_bit_size_by_rax(sub_size, mul_dst, left_, known_value);
        }
        else if (std::holds_alternative<Gpq256>(left_)) {
            hx_mark("@L6734");
            auto const &lgpq = std::get<Gpq256>(left_);
            std::visit(
                Cases{
                    [&](uint256_t const &r) {
                        auto const x = r[word_count - N];
                        if constexpr (Has32Bit) {
                            hx_mark("@L6740");
                            em_.gpr_mul_by_uint64<true>(mul_dst[0], lgpq[0], x);
                        }
                        else if (
                            is_uint64_bounded(x) || std::popcount(x) == 1) {
                                hx_mark("@L6744");
                            em_.gpr_mul_by_uint64<false>(
                                mul_dst[0], lgpq[0], x);
                        }
                        else {
                            hx_mark("@L6748");
                            em_.as_.mov(mul_dst[0], x);
                            em_.as_.imul(mul_dst[0], lgpq[0]);
                        }
                    },
                    [&](Gpq256 const &r) {
                        if constexpr (Has32Bit) {
                            hx_mark("@L6754");
                            em_.as_.mov(
                                mul_dst[0].r32(), r[word_count - N].r32());
                            em_.as_.imul(mul_dst[0].r32(), lgpq[0].r32());
                        }
                        else {
                            hx_mark("@L6759");
                            em_.as_.mov(mul_dst[0], r[word_count - N]);
                            em_.as_.imul(mul_dst[0], lgpq[0]);
                        }
                    },
                    [&](x86::Mem r) {
                        r.addOffset(static_cast<int64_t>((word_count - N) * 8));
                        if constexpr (Has32Bit) {
                            hx_mark("@L6766");
                            em_.as_.mov(mul_dst[0].r32(), r);
                            em_.as_.imul(mul_dst[0].r32(), lgpq[0].r32());
                        }
                        else {
                            hx_mark("@L6770");
                            em_.as_.mov(mul_dst[0], r);
                            em_.as_.imul(mul_dst[0], lgpq[0]);
                        }
                    },
                },
                right_);
        }
        else {
            hx_mark("@L6778");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(left_));
            auto const &lmem = std::get<x86::Mem>(left_);
            std::visit(
                Cases{
                    [&](uint256_t const &r) {
                        auto const x = r[word_count - N];
                        if constexpr (Has32Bit) {
                            hx_mark("@L6785");
                            em_.gpr_mul_by_uint64<true>(mul_dst[0], lmem, x);
                        }
                        else if (
                            is_uint64_bounded(x) || std::popcount(x) == 1) {
                                hx_mark("@L6789");
                            em_.gpr_mul_by_uint64<false>(mul_dst[0], lmem, x);
                        }
                        else {
                            hx_mark("@L6792");
                            em_.as_.mov(mul_dst[0], x);
                            em_.as_.imul(mul_dst[0], lmem);
                        }
                    },
                    [&](Gpq256 const &r) {
                        if constexpr (Has32Bit) {
                            hx_mark("@L6798");
                            em_.as_.mov(
                                mul_dst[0].r32(), r[word_count - N].r32());
                            em_.as_.imul(mul_dst[0].r32(), lmem);
                        }
                        else {
                            hx_mark("@L6803");
                            em_.as_.mov(mul_dst[0], r[word_count - N]);
                            em_.as_.imul(mul_dst[0], lmem);
                        }
                    },
                    [&](x86::Mem r) {
                        r.addOffset(static_cast<int64_t>((word_count - N) * 8));
                        if constexpr (Has32Bit) {
                            hx_mark("@L6810");
                            em_.as_.mov(mul_dst[0].r32(), r);
                            em_.as_.imul(mul_dst[0].r32(), lmem);
                        }
                        else {
                            hx_mark("@L6814");
                            em_.as_.mov(mul_dst[0], r);
                            em_.as_.imul(mul_dst[0], lmem);
                        }
                    },
                },
                right_);
        }
    }

    template <bool Has32Bit>
    void
    Emitter::MulEmitter::update_dst(size_t sub_size, x86::Gpq const *mul_dst)
    {
        hx_mark("@F6827 update_dst");
        if (is_dst_initialized_) {
            hx_mark("@L6828");
            size_t const word_count = div64_ceil(bit_size_);
            size_t i = word_count - div64_ceil(sub_size);
            size_t j = 0;
            if constexpr (Has32Bit) {
                hx_mark("@L6832");
                if (i == word_count - 1) {
                    hx_mark("@L6833");
                    em_.as_.add(dst_[i++].r32(), mul_dst[j++].r32());
                }
                else {
                    hx_mark("@L6836");
                    em_.as_.add(dst_[i++], mul_dst[j++]);
                }
                while (i < word_count) {
                    hx_mark("@L6839");
                    if (i == word_count - 1) {
                        hx_mark("@L6840");
                        em_.as_.adc(dst_[i++].r32(), mul_dst[j++].r32());
                    }
                    else {
                        hx_mark("@L6843");
                        em_.as_.adc(dst_[i++], mul_dst[j++]);
                    }
                }
            }
            else {
                hx_mark("@L6848");
                em_.as_.add(dst_[i++], mul_dst[j++]);
                while (i < word_count) {
                    hx_mark("@L6850");
                    em_.as_.adc(dst_[i++], mul_dst[j++]);
                }
            }
        }
        else {
            hx_mark("@L6855");
            is_dst_initialized_ = true;
        }
    }

    template <bool Has32Bit>
    void Emitter::MulEmitter::compose(size_t sub_size, x86::Gpq *mul_dst)
    {
        hx_mark("@F6862 compose");
        size_t const i = div64_ceil(bit_size_) - div64_ceil(sub_size);
        if (!std::holds_alternative<uint256_t>(right_) ||
            std::get<uint256_t>(right_)[i] != 0) {
                hx_mark("@L6865");
            init_mul_dst(sub_size, mul_dst);
            mul_sequence<Has32Bit>(sub_size, mul_dst);
            update_dst<Has32Bit>(sub_size, mul_dst);
        }
        else if (!is_dst_initialized_) {
            hx_mark("@L6870");
            em_.as_.xor_(dst_[i].r32(), dst_[i].r32());
        }
    }

    template <bool Has32Bit>
    void Emitter::MulEmitter::emit_loop()
    {
        hx_mark("@F6877 emit_loop");
        x86::Gpq mul_dst[4];
        auto sub_size = bit_size_;
        while (sub_size > 64) {
            hx_mark("@L6880");
            compose<Has32Bit>(sub_size, mul_dst);
            sub_size -= 64;
        }
        compose<Has32Bit>(sub_size, mul_dst);
    }

    void Emitter::MulEmitter::emit()
    {
        hx_mark("@F6888 emit");
        if ((bit_size_ & 63) && (bit_size_ & 63) <= 32) {
            hx_mark("@L6889");
            emit_loop<true>();
        }
        else {
            hx_mark("@L6892");
            emit_loop<false>();
        }
    }

    // If right is `Gpq256`, then make sure the general register is
    // reserved with `GeneralRegReserv`.
    template <typename... LiveSet>
    StackElemRef Emitter::mul_with_bit_size(
        size_t bit_size, StackElemRef left, MulEmitter::RightMulArg right,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F6903 mul_with_bit_size");
        auto const rdx_general_reg_index = volatile_gpq_index<x86::rdx>();

        MONAD_DEBUG_ASSERT(bit_size > 0 && bit_size <= 256);
        MONAD_DEBUG_ASSERT(
            gpq256_regs_[rdx_general_reg.reg][rdx_general_reg_index] ==
            x86::rdx);

        size_t const dst_word_count = div64_ceil(bit_size);

        // This is currently assumed to simplify register allocations:
        MONAD_DEBUG_ASSERT(
            !std::holds_alternative<Gpq256>(right) || dst_word_count <= 2);

        MONAD_DEBUG_ASSERT(!left->literal().has_value());

        {
            hx_mark("@L6919");
            GeneralRegReserv const left_reserv{left};
            discharge_deferred_comparison();
        }

        size_t required_reg_count = 0;
        bool needs_mulx = true;
        for (size_t i = 0; i < dst_word_count; ++i) {
            hx_mark("@L6926");
            if (!std::holds_alternative<uint256_t>(right) ||
                std::get<uint256_t>(right)[i] != 0) {
                    hx_mark("@L6928");
                if (required_reg_count == 0) {
                    hx_mark("@L6929");
                    required_reg_count = dst_word_count;
                    needs_mulx = i != dst_word_count - 1;
                }
                else {
                    hx_mark("@L6933");
                    required_reg_count += (dst_word_count - i);
                    break;
                }
            }
        }

        if (required_reg_count == 0) {
            hx_mark("@L6940");
            return stack_.alloc_literal({0});
        }

        MONAD_DEBUG_ASSERT(
            required_reg_count >= dst_word_count && required_reg_count < 8);

        GeneralRegReserv const left_reserv{left};
        if (required_reg_count > dst_word_count) {
            hx_mark("@L6948");
            if (!left->general_reg()) {
                hx_mark("@L6949");
                mov_stack_elem_to_general_reg(left);
            }
        }
        else {
            hx_mark("@L6953");
            if (!left->general_reg() && !left->stack_offset()) {
                hx_mark("@L6954");
                MONAD_DEBUG_ASSERT(left->avx_reg().has_value());
                mov_avx_reg_to_stack_offset(left);
            }
        }

        auto [dst, dst_reserv] = alloc_general_reg();

        auto tmp = dst;
        auto tmp_reserv = dst_reserv;
        if (required_reg_count > 4) {
            hx_mark("@L6964");
            auto [t, r] = alloc_general_reg();
            tmp = t;
            tmp_reserv = r;
        }

        auto spill_elem = tmp;
        auto spill_elem_reserv = tmp_reserv;
        std::optional<x86::Gpq> spill_gpq;
        if (needs_mulx && stack_.has_free_general_reg()) {
            hx_mark("@L6973");
            auto [s, r] = alloc_general_reg();
            spill_elem = s;
            spill_elem_reserv = r;
            auto const &gpq = general_reg_to_gpq256(*spill_elem->general_reg());
            spill_gpq = gpq[rdx_general_reg_index];
        }

        bool preserve_dst_rdx = false;
        bool preserve_left_rdx = false;
        bool preserve_right_rdx = false;
        bool preserve_stack_rdx = false;

        if (needs_mulx) {
            hx_mark("@L6986");
            auto &dst_gpq = general_reg_to_gpq256(*dst->general_reg());
            auto &tmp_gpq = general_reg_to_gpq256(*tmp->general_reg());
            if (dst_gpq[rdx_general_reg_index] == x86::rdx) {
                hx_mark("@L6989");
                MONAD_DEBUG_ASSERT(*dst->general_reg() == rdx_general_reg);
                preserve_dst_rdx = true;
            }
            if (preserve_dst_rdx) {
                hx_mark("@L6993");
                if (tmp != dst) {
                    hx_mark("@L6994");
                    std::swap(tmp, dst);
                    preserve_dst_rdx = false;
                }
                else {
                    hx_mark("@L6998");
                    if (spill_gpq) {
                        hx_mark("@L6999");
                        dst_gpq[rdx_general_reg_index] = *spill_gpq;
                    }
                    else {
                        hx_mark("@L7002");
                        as_.push(reg_context);
                        dst_gpq[rdx_general_reg_index] = reg_context;
                    }
                }
            }
            else {
                hx_mark("@L7008");
                if (left->general_reg()) {
                    hx_mark("@L7009");
                    auto &left_gpq =
                        general_reg_to_gpq256(*left->general_reg());
                    if (left_gpq[rdx_general_reg_index] == x86::rdx) {
                        hx_mark("@L7012");
                        MONAD_DEBUG_ASSERT(
                            *left->general_reg() == rdx_general_reg);
                        if (tmp != dst) {
                            hx_mark("@L7015");
                            spill_gpq = tmp_gpq[rdx_general_reg_index];
                        }
                        preserve_left_rdx = true;
                        if (spill_gpq) {
                            hx_mark("@L7019");
                            as_.mov(*spill_gpq, x86::rdx);
                            left_gpq[rdx_general_reg_index] = *spill_gpq;
                        }
                        else {
                            hx_mark("@L7023");
                            as_.push(reg_context);
                            as_.mov(reg_context, x86::rdx);
                            left_gpq[rdx_general_reg_index] = reg_context;
                        }
                    }
                }
                if (std::holds_alternative<Gpq256>(right) &&
                    dst_word_count > rdx_general_reg_index) {
                        hx_mark("@L7031");
                    auto &right_gpq = std::get<Gpq256>(right);
                    if (right_gpq[rdx_general_reg_index] == x86::rdx) {
                        hx_mark("@L7033");
                        // Due to the limited size of `dst_word_count <= 2`
                        // when `right` holds register, we have the
                        // following two invariants.
                        MONAD_DEBUG_ASSERT(tmp == dst);
                        MONAD_DEBUG_ASSERT(
                            preserve_left_rdx || !spill_gpq.has_value());
                        // If left and right are the same register, then
                        // we only need to emit the `rdx` perserving
                        // instructions once. So if `preserve_left_rdx`
                        // is true, we do not need to emit the instructions
                        // to preserve `rdx` again here, and therefore can
                        // set `preserve_right_rdx` to false in this case.
                        preserve_right_rdx = !preserve_left_rdx;
                        if (preserve_right_rdx) {
                            hx_mark("@L7047");
                            as_.push(reg_context);
                            as_.mov(reg_context, x86::rdx);
                        }
                        if (spill_gpq) {
                            hx_mark("@L7051");
                            right_gpq[rdx_general_reg_index] = *spill_gpq;
                        }
                        else {
                            hx_mark("@L7054");
                            right_gpq[rdx_general_reg_index] = reg_context;
                        }
                    }
                }
                if (!preserve_left_rdx && !preserve_right_rdx &&
                    is_live(rdx_general_reg, live)) {
                        hx_mark("@L7060");
                    auto const &q = general_reg_to_gpq256(rdx_general_reg);
                    MONAD_DEBUG_ASSERT(q[rdx_general_reg_index] == x86::rdx);
                    preserve_stack_rdx = true;
                    if (spill_gpq) {
                        hx_mark("@L7064");
                        as_.mov(*spill_gpq, x86::rdx);
                    }
                    else {
                        hx_mark("@L7067");
                        as_.push(x86::rdx);
                    }
                }
            }
        }

        auto &dst_gpq = general_reg_to_gpq256(*dst->general_reg());
        auto const left_op =
            left->general_reg()
                ? Operand{general_reg_to_gpq256(*left->general_reg())}
                : Operand{stack_offset_to_mem(*left->stack_offset())};
        MONAD_DEBUG_ASSERT(dst_word_count <= 4);
        x86::Gpq emit_tmp[3];
        if (tmp != dst) {
            hx_mark("@L7081");
            auto &tmp_gpq = general_reg_to_gpq256(*tmp->general_reg());
            for (size_t i = 0, n = 0; n < dst_word_count - 1; ++i) {
                hx_mark("@L7083");
                if (i != rdx_general_reg_index) {
                    hx_mark("@L7084");
                    emit_tmp[n++] = tmp_gpq[i];
                }
            }
        }
        else {
            hx_mark("@L7089");
            for (size_t i = 0, n = dst_word_count;
                 n < 4 && i < dst_word_count - 1;
                 ++i) {
                     hx_mark("@L7092");
                emit_tmp[i] = dst_gpq[n++];
            }
        }

        MulEmitter{bit_size, *this, left_op, right, dst_gpq.data(), emit_tmp}
            .emit();

        if (bit_size & 31) {
            hx_mark("@L7100");
            auto const mask = (uint64_t{1} << (bit_size & 63)) - 1;
            if (std::bit_width(mask) <= 32) {
                hx_mark("@L7102");
                as_.and_(dst_gpq[dst_word_count - 1].r32(), mask);
            }
            else {
                hx_mark("@L7105");
                as_.mov(x86::rax, mask);
                as_.and_(dst_gpq[dst_word_count - 1], x86::rax);
            }
        }
        for (size_t i = dst_word_count; i < 4; ++i) {
            hx_mark("@L7110");
            as_.xor_(dst_gpq[i].r32(), dst_gpq[i].r32());
        }

        MONAD_DEBUG_ASSERT(
            preserve_stack_rdx + preserve_dst_rdx + preserve_left_rdx +
                preserve_right_rdx <=
            1);

        if (preserve_stack_rdx) {
            hx_mark("@L7119");
            if (spill_gpq) {
                hx_mark("@L7120");
                as_.mov(x86::rdx, *spill_gpq);
            }
            else {
                hx_mark("@L7123");
                as_.pop(x86::rdx);
            }
        }
        else if (preserve_dst_rdx) {
            hx_mark("@L7127");
            if (spill_gpq) {
                hx_mark("@L7128");
                as_.mov(x86::rdx, *spill_gpq);
                dst_gpq[rdx_general_reg_index] = x86::rdx;
            }
            else {
                hx_mark("@L7132");
                as_.mov(x86::rdx, reg_context);
                dst_gpq[rdx_general_reg_index] = x86::rdx;
                as_.pop(reg_context);
            }
        }
        else if (preserve_left_rdx) {
            hx_mark("@L7138");
            auto &left_gpq = general_reg_to_gpq256(*left->general_reg());
            if (spill_gpq) {
                hx_mark("@L7140");
                as_.mov(x86::rdx, *spill_gpq);
                left_gpq[rdx_general_reg_index] = x86::rdx;
            }
            else {
                hx_mark("@L7144");
                as_.mov(x86::rdx, reg_context);
                left_gpq[rdx_general_reg_index] = x86::rdx;
                as_.pop(reg_context);
            }
        }
        else if (preserve_right_rdx) {
            hx_mark("@L7150");
            if (spill_gpq) {
                hx_mark("@L7151");
                as_.mov(x86::rdx, *spill_gpq);
            }
            else {
                hx_mark("@L7154");
                as_.mov(x86::rdx, reg_context);
                as_.pop(reg_context);
            }
        }

        return dst;
    }

    bool Emitter::mul_optimized()
    {
        hx_mark("@F7164 mul_optimized");
        auto a_elem = stack_.get(stack_.top_index());
        auto b_elem = stack_.get(stack_.top_index() - 1);

        if (b_elem->literal()) {
            hx_mark("@L7168");
            if (a_elem->literal()) {
                hx_mark("@L7169");
                auto const &a = a_elem->literal()->value;
                auto const &b = b_elem->literal()->value;
                stack_.pop();
                stack_.pop();
                stack_.push_literal(a * b);
                return true;
            }
            else {
                hx_mark("@L7177");
                std::swap(a_elem, b_elem);
            }
        }
        else if (!a_elem->literal()) {
            hx_mark("@L7181");
            return false;
        }

        auto a = a_elem->literal()->value;
        a_elem.reset(); // Clear locations
        if (a == 0) {
            hx_mark("@L7187");
            stack_.pop();
            stack_.pop();
            stack_.push_literal(0);
            return true;
        }

        auto a_shift = a;
        if (a[3] & (static_cast<uint64_t>(1) << 63)) {
            hx_mark("@L7195");
            a_shift = -a;
        }

        if (popcount(a_shift) == 1) {
            hx_mark("@L7199");
            stack_.pop();
            stack_.pop();
            auto x = shift_by_literal<ShiftType::SHL>(
                countr_zero(a_shift), std::move(b_elem), {});
            if (a_shift[3] != a[3]) {
                hx_mark("@L7204");
                // The shift was negated. Negate result for correct sign:
                stack_.push(negate(std::move(x), {}));
            }
            else {
                hx_mark("@L7208");
                stack_.push(std::move(x));
            }
            return true;
        }
        else if (!a[0] || !a[1] || !a[2] || !a[3]) {
            hx_mark("@L7213");
            // If one of the qwords in `a` is zero, then we will inline
            // the multiplication. This will save at least one x86
            // multiplication instruction.
            stack_.pop();
            stack_.pop();
            stack_.push(mul_with_bit_size(256, std::move(b_elem), a, {}));
            return true;
        }

        return false;
    }

    // Discharge through `shift_by_literal`.
    // Note that this function assumes that there is an available
    // stack offset in the stack. This is the case when calling
    // from `div_optimized`, because lifetime of the divisor has
    // ended before calling this function.
    template <typename... LiveSet>
    StackElemRef Emitter::sdiv_by_sar(
        StackElemRef elem, uint256_t const &shift_in,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F7235 sdiv_by_sar");
        MONAD_DEBUG_ASSERT(!elem->literal().has_value());
        MONAD_DEBUG_ASSERT(shift_in <= 255);

        auto const shift = static_cast<uint64_t>(shift_in);

        if (shift == 0) {
            hx_mark("@L7241");
            return elem;
        }

        size_t index = 3;
        for (auto c = 256 - shift;;) {
            hx_mark("@L7246");
            if (c <= 64) {
                hx_mark("@L7247");
                break;
            }
            c -= 64;
            --index;
        }
        auto const mask = (static_cast<uint64_t>(1) << (shift & 63)) - 1;

        StackElemRef sh;
        {
            hx_mark("@L7256");
            GeneralRegReserv const elem_reserv{elem};
            sh = shift_by_literal<ShiftType::SAR>(
                shift, elem, std::tuple_cat(std::make_tuple(elem), live));
        }

        GeneralRegReserv const sh_reserv{sh};

        if (!elem->general_reg() && stack_.has_free_general_reg()) {
            hx_mark("@L7264");
            mov_stack_elem_to_general_reg(elem);
        }

        if (elem->general_reg()) {
            hx_mark("@L7268");
            auto const &gpq = general_reg_to_gpq256(*elem->general_reg());
            if (mask != 0) {
                hx_mark("@L7270");
                as_.mov(x86::rax, mask);
                as_.and_(x86::rax, gpq[index]);
            }
            else {
                hx_mark("@L7274");
                as_.xor_(x86::eax, x86::eax);
            }
            while (index--) {
                hx_mark("@L7277");
                as_.or_(x86::rax, gpq[index]);
            }
            as_.setnz(x86::al);

            auto const cond_mem = rodata_.add8(static_cast<uint64_t>(1) << 63);
            as_.test(cond_mem, gpq[3]);
            as_.setnz(x86::ah);

            as_.and_(x86::al, x86::ah);
            as_.movzx(x86::eax, x86::al);
        }
        else {
            hx_mark("@L7289");
            if (!elem->stack_offset()) {
                hx_mark("@L7290");
                MONAD_DEBUG_ASSERT(elem->avx_reg().has_value());
                mov_avx_reg_to_stack_offset(elem);
            }
            MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());
            auto mem = stack_offset_to_mem(*elem->stack_offset());
            mem.addOffset(24);
            as_.mov(x86::rax, static_cast<uint64_t>(1) << 63);
            as_.test(mem, x86::rax);
            as_.setnz(x86::byte_ptr(x86::rsp, sp_offset_temp_word1));

            MONAD_DEBUG_ASSERT(index <= 3);
            mem.addOffset(static_cast<int64_t>(index) * 8 - 24);
            as_.mov(x86::rax, mask);
            as_.and_(x86::rax, mem);
            while (index--) {
                hx_mark("@L7305");
                mem.addOffset(-8);
                as_.or_(x86::rax, mem);
            }
            as_.setnz(x86::al);

            as_.and_(x86::al, x86::byte_ptr(x86::rsp, sp_offset_temp_word1));
            as_.movzx(x86::eax, x86::al);
        }

        elem.reset(); // Release registers and stack offset.

        MONAD_DEBUG_ASSERT(!sh->literal().has_value());

        StackElemRef dst;
        if (is_live(sh, live)) {
            hx_mark("@L7320");
            if (sh->general_reg() && (sh->stack_offset() || sh->avx_reg())) {
                hx_mark("@L7321");
                dst = stack_.release_general_reg(sh);
            }
            else if (sh->stack_offset() && sh->avx_reg()) {
                hx_mark("@L7324");
                dst = stack_.release_stack_offset(sh);
            }
            else {
                hx_mark("@L7327");
                if (sh->general_reg() || sh->stack_offset()) {
                    hx_mark("@L7328");
                    auto [r, _] = alloc_general_reg();
                    dst = std::move(r);
                    mov_stack_elem_to_gpq256<true>(
                        sh, general_reg_to_gpq256(*dst->general_reg()));
                }
                else {
                    hx_mark("@L7334");
                    mov_avx_reg_to_stack_offset(sh);
                    dst = stack_.release_stack_offset(sh);
                }
            }
        }
        else if (sh->general_reg()) {
            hx_mark("@L7340");
            dst = stack_.release_general_reg(sh);
        }
        else if (sh->stack_offset()) {
            hx_mark("@L7343");
            dst = stack_.release_stack_offset(sh);
        }
        else {
            hx_mark("@L7346");
            MONAD_DEBUG_ASSERT(sh->avx_reg().has_value());
            mov_avx_reg_to_stack_offset(sh);
            dst = stack_.release_stack_offset(sh);
        }

        if (dst->general_reg()) {
            hx_mark("@L7352");
            auto const &gpq = general_reg_to_gpq256(*dst->general_reg());
            as_.add(gpq[0], x86::rax);
            for (size_t i = 1; i < 4; ++i) {
                hx_mark("@L7355");
                as_.adc(gpq[i], 0);
            }
        }
        else {
            hx_mark("@L7359");
            MONAD_DEBUG_ASSERT(dst->stack_offset().has_value());
            auto mem = stack_offset_to_mem(*dst->stack_offset());
            as_.add(mem, x86::rax);
            for (size_t i = 1; i < 4; ++i) {
                hx_mark("@L7363");
                mem.addOffset(8);
                as_.adc(mem, 0);
            }
        }

        return dst;
    }

    template <bool is_sdiv>
    bool Emitter::div_optimized()
    {
        hx_mark("@F7374 div_optimized");
        auto a_elem = stack_.get(stack_.top_index());
        auto b_elem = stack_.get(stack_.top_index() - 1);

        if (a_elem->literal()) {
            hx_mark("@L7378");
            auto const &a = a_elem->literal()->value;
            if (a == 0) {
                hx_mark("@L7380");
                stack_.pop();
                stack_.pop();
                stack_.push_literal(0);
                return true;
            }
            if (b_elem->literal()) {
                hx_mark("@L7386");
                auto const &b = b_elem->literal()->value;
                stack_.pop();
                stack_.pop();
                if constexpr (is_sdiv) {
                    hx_mark("@L7390");
                    stack_.push_literal(b == 0 ? 0 : sdivrem(a, b).quot);
                }
                else {
                    hx_mark("@L7393");
                    stack_.push_literal(b == 0 ? 0 : a / b);
                }
                return true;
            }
            return false;
        }
        else if (!b_elem->literal()) {
            hx_mark("@L7400");
            return false;
        }

        auto b = b_elem->literal()->value;
        b_elem.reset(); // Clear locations
        if (b == 0) {
            hx_mark("@L7406");
            stack_.pop();
            stack_.pop();
            stack_.push_literal(0);
            return true;
        }

        bool const needs_negation = [&] {
            if constexpr (is_sdiv) {
                hx_mark("@L7414");
                if (b[3] & (static_cast<uint64_t>(1) << 63)) {
                    hx_mark("@L7415");
                    b = -b;
                    return true;
                }
            }
            return false;
        }();

        if (popcount(b) == 1) {
            hx_mark("@L7423");
            stack_.pop();
            stack_.pop();
            auto const shift = countr_zero(b);
            auto dst = [&] {
                if constexpr (is_sdiv) {
                    hx_mark("@L7428");
                    return sdiv_by_sar(std::move(a_elem), shift, {});
                }
                else {
                    hx_mark("@L7431");
                    return shift_by_literal<ShiftType::SHR>(
                        shift, std::move(a_elem), {});
                }
            }();
            if (needs_negation) {
                hx_mark("@L7436");
                stack_.push(negate(std::move(dst), {}));
            }
            else {
                hx_mark("@L7439");
                stack_.push(std::move(dst));
            }
            return true;
        }

        return false;
    }

    template bool Emitter::div_optimized<true>();
    template bool Emitter::div_optimized<false>();

    // Discharge
    template <typename... LiveSet>
    StackElemRef Emitter::smod_by_mask(
        StackElemRef elem, uint256_t const &mask,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F7456 smod_by_mask");
        MONAD_DEBUG_ASSERT(!elem->literal().has_value());

        {
            hx_mark("@L7459");
            RegReserv const elem_reserv{elem};
            discharge_deferred_comparison();
        }

        StackElemRef dst;
        if (elem->general_reg() && !is_live(elem, live)) {
            hx_mark("@L7465");
            dst = stack_.release_general_reg(elem);
        }
        else {
            hx_mark("@L7468");
            GeneralRegReserv const elem_reserv{elem};
            auto [r, _] = alloc_general_reg();
            dst = std::move(r);
            mov_stack_elem_to_gpq256<true>(
                elem, general_reg_to_gpq256(*dst->general_reg()));
        }

        auto const &dst_gpq = general_reg_to_gpq256(*dst->general_reg());

        auto const sign_mem = rodata_.add8(static_cast<uint64_t>(1) << 63);
        auto const non_negative_lbl = as_.newLabel();
        auto const after_lbl = as_.newLabel();

        auto emit_mask = [&] {
            if (is_literal_bounded({mask})) {
                hx_mark("@L7483");
                for (size_t i = 0; i < 4; ++i) {
                    hx_mark("@L7484");
                    as_.and_(dst_gpq[i], mask[i]);
                }
            }
            else {
                hx_mark("@L7488");
                auto m = rodata_.add_literal({mask});
                for (size_t i = 0; i < 4; ++i) {
                    hx_mark("@L7490");
                    as_.and_(dst_gpq[i], m);
                    m.addOffset(8);
                }
            }
        };

        as_.test(sign_mem, dst_gpq[3]);
        as_.jz(non_negative_lbl);
        negate_gpq256(dst_gpq);
        emit_mask();
        negate_gpq256(dst_gpq);
        as_.jmp(after_lbl);
        as_.bind(non_negative_lbl);
        emit_mask();
        as_.bind(after_lbl);

        return dst;
    }

    template <bool is_smod>
    bool Emitter::mod_optimized()
    {
        hx_mark("@F7512 mod_optimized");
        auto a_elem = stack_.get(stack_.top_index());
        auto b_elem = stack_.get(stack_.top_index() - 1);

        if (a_elem->literal()) {
            hx_mark("@L7516");
            auto const &a = a_elem->literal()->value;
            if (a == 0) {
                hx_mark("@L7518");
                stack_.pop();
                stack_.pop();
                stack_.push(std::move(a_elem));
                return true;
            }
            if (b_elem->literal()) {
                hx_mark("@L7524");
                auto const &b = b_elem->literal()->value;
                stack_.pop();
                stack_.pop();
                if constexpr (is_smod) {
                    hx_mark("@L7528");
                    stack_.push_literal(b == 0 ? 0 : sdivrem(a, b).rem);
                }
                else {
                    hx_mark("@L7531");
                    stack_.push_literal(b == 0 ? 0 : a % b);
                }
                return true;
            }
            return false;
        }
        else if (!b_elem->literal()) {
            hx_mark("@L7538");
            return false;
        }

        auto b = b_elem->literal()->value;
        b_elem.reset(); // Clear locations
        if constexpr (is_smod) {
            hx_mark("@L7544");
            if (b[3] & (static_cast<uint64_t>(1) << 63)) {
                hx_mark("@L7545");
                b = -b;
            }
        }
        if (b <= 1) {
            hx_mark("@L7549");
            stack_.pop();
            stack_.pop();
            stack_.push_literal(0);
            return true;
        }
        if (popcount(b) == 1) {
            hx_mark("@L7555");
            stack_.pop();
            stack_.pop();
            if constexpr (is_smod) {
                hx_mark("@L7558");
                stack_.push(smod_by_mask(std::move(a_elem), b - 1, {}));
            }
            else {
                hx_mark("@L7561");
                stack_.push(
                    and_(std::move(a_elem), stack_.alloc_literal({b - 1}), {}));
                return true;
            }
            return true;
        }

        return false;
    }

    template bool Emitter::mod_optimized<true>();
    template bool Emitter::mod_optimized<false>();

    template <typename... LiveSet>
    std::tuple<
        StackElemRef, Emitter::LocationType, StackElemRef,
        Emitter::LocationType>
    Emitter::prepare_mod2_bin_dest_and_source(
        StackElemRef dst, StackElemRef src, size_t exp,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F7582 prepare_mod2_bin_dest_and_source");
        RegReserv const dst_reserv{dst};
        RegReserv const src_reserv{src};

        if (dst.get() == src.get()) {
            hx_mark("@L7586");
            if (!dst->general_reg()) {
                hx_mark("@L7587");
                mov_stack_elem_to_general_reg_mod2(dst, exp);
            }
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::GeneralReg};
        }

        auto const src_ord = get_stack_elem_general_order_index(src, live);
        auto const dst_ord = get_stack_elem_general_order_index(dst, live);
        if (src_ord < dst_ord) {
            hx_mark("@L7599");
            std::swap(dst, src);
        }

        if (!dst->general_reg()) {
            hx_mark("@L7603");
            if (dst->literal()) {
                hx_mark("@L7604");
                mov_literal_to_general_reg_mod2(dst, exp);
            }
            else if (dst->stack_offset()) {
                hx_mark("@L7607");
                mov_stack_offset_to_general_reg_mod2(dst, exp);
            }
            else {
                hx_mark("@L7610");
                MONAD_DEBUG_ASSERT(dst->avx_reg().has_value());
                mov_avx_reg_to_stack_offset(dst);
                mov_stack_offset_to_general_reg_mod2(dst, exp);
            }
        }

        if (src->general_reg()) {
            hx_mark("@L7617");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::GeneralReg};
        }
        if (src->literal() && is_literal_bounded(*src->literal())) {
            hx_mark("@L7624");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::Literal};
        }
        if (src->stack_offset()) {
            hx_mark("@L7631");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::StackOffset};
        }
        if (src->literal()) {
            hx_mark("@L7638");
            return {
                std::move(dst),
                LocationType::GeneralReg,
                std::move(src),
                LocationType::Literal};
        }
        MONAD_DEBUG_ASSERT(src->avx_reg().has_value());
        mov_avx_reg_to_stack_offset(src);
        return {
            std::move(dst),
            LocationType::GeneralReg,
            std::move(src),
            LocationType::StackOffset};
    }

    void Emitter::mov_stack_offset_to_general_reg_mod2(
        StackElemRef const elem, size_t const exp)
    {
        hx_mark("@F7656 mov_stack_offset_to_general_reg_mod2");
        MONAD_DEBUG_ASSERT(exp > 0);
        MONAD_DEBUG_ASSERT(elem->stack_offset().has_value());

        x86::Mem mem{stack_offset_to_mem(*elem->stack_offset())};
        auto const reserv = insert_general_reg(elem);
        MONAD_DEBUG_ASSERT(elem->general_reg());
        auto const &gpq = general_reg_to_gpq256(*elem->general_reg());

        size_t const numQwords = div64_ceil(exp);
        for (size_t i = 0; i < numQwords; i++) {
            hx_mark("@L7666");
            size_t const occupied_bits =
                i + 1 == numQwords ? exp - (i * 64) : 64;
            if (occupied_bits <= 32) {
                hx_mark("@L7669");
                as_.mov(gpq[i].r32(), mem);
            }
            else {
                hx_mark("@L7672");
                as_.mov(gpq[i].r64(), mem);
            }
            mem.addOffset(8);
        }
    }

    void Emitter::mov_literal_to_general_reg_mod2(
        StackElemRef const elem, size_t const exp)
    {
        hx_mark("@F7681 mov_literal_to_general_reg_mod2");
        MONAD_DEBUG_ASSERT(exp > 0);
        MONAD_DEBUG_ASSERT(elem->literal().has_value());

        auto const reserv = insert_general_reg(elem);
        auto const &gpq = general_reg_to_gpq256(*elem->general_reg());
        auto const &lit =
            *elem->literal(); // literal_to_imm256(*elem->literal());
        size_t const numQwords = div64_ceil(exp);
        for (size_t i = 0; i < numQwords; i++) {
            hx_mark("@L7690");
            if (!lit.value[i] && !stack_.has_deferred_comparison()) {
                hx_mark("@L7691");
                as_.xor_(gpq[i].r32(), gpq[i].r32());
                continue;
            }
            size_t const occupied_bits =
                i + 1 == numQwords ? exp - (i * 64) : 64;
            if (occupied_bits <= 32) {
                hx_mark("@L7697");
                as_.mov(gpq[i].r32(), lit.value[i]);
            }
            else {
                hx_mark("@L7700");
                as_.mov(gpq[i].r64(), lit.value[i]);
            }
        }
    }

    void Emitter::mov_stack_elem_to_general_reg_mod2(
        StackElemRef elem, size_t const exp)
    {
        hx_mark("@F7708 mov_stack_elem_to_general_reg_mod2");
        MONAD_DEBUG_ASSERT(exp > 0);
        if (elem->general_reg()) {
            hx_mark("@L7710");
            return;
        }
        if (elem->literal()) {
            hx_mark("@L7713");
            mov_literal_to_general_reg_mod2(std::move(elem), exp);
        }
        else if (elem->stack_offset()) {
            hx_mark("@L7716");
            mov_stack_offset_to_general_reg_mod2(std::move(elem), exp);
        }
        else {
            hx_mark("@L7719");
            MONAD_ASSERT(elem->avx_reg().has_value());
            mov_avx_reg_to_stack_offset(elem);
            mov_stack_offset_to_general_reg_mod2(std::move(elem), exp);
        }
    }

    template <typename... LiveSet>
    std::tuple<
        StackElemRef, Emitter::LocationType, StackElemRef,
        Emitter::LocationType>
    Emitter::get_mod2_bin_dest_and_source(
        StackElemRef dst_in, StackElemRef src_in, size_t exp,
        std::tuple<LiveSet...> const &live)
    {
        hx_mark("@F7733 get_mod2_bin_dest_and_source");
        auto [dst, dst_loc, src, src_loc] = prepare_mod2_bin_dest_and_source(
            std::move(dst_in), std::move(src_in), exp, live);
        RegReserv const dst_reserv{dst};
        RegReserv const src_reserv{src};

        MONAD_DEBUG_ASSERT(dst_loc == LocationType::GeneralReg);
        if (is_live(dst, live) && !dst->stack_offset() && !dst->literal() &&
            !dst->avx_reg()) {
                hx_mark("@L7741");
            if (stack_.has_free_general_reg()) {
                hx_mark("@L7742");
                auto [new_dst, reserv] = alloc_general_reg();
                size_t const numQwords = div64_ceil(exp);
                auto const &n = general_reg_to_gpq256(*new_dst->general_reg());
                auto const &d = general_reg_to_gpq256(*dst->general_reg());
                for (size_t i = 0; i < numQwords; i++) {
                    hx_mark("@L7747");
                    size_t const occupied_bits =
                        i + 1 == numQwords ? exp - (i * 64) : 64;
                    if (occupied_bits <= 32) {
                        hx_mark("@L7750");
                        as_.mov(n[i].r32(), d[i].r32());
                    }
                    else {
                        hx_mark("@L7753");
                        as_.mov(n[i], d[i]);
                    }
                }
                return {std::move(new_dst), dst_loc, std::move(src), src_loc};
            }
            mov_general_reg_to_stack_offset(dst);
        }
        auto new_dst = stack_.release_general_reg(dst);
        if (dst == src) {
            hx_mark("@L7762");
            return {new_dst, dst_loc, new_dst, src_loc};
        }
        else {
            hx_mark("@L7765");
            return {std::move(new_dst), dst_loc, std::move(src), src_loc};
        }
    }

    // Discharge
    template <
        Emitter::ModOpType ModOp, uint64_t Unit, uint64_t Absorb,
        Emitter::ModOpByMaskType ModOpByMask>
    bool Emitter::modop_optimized()
    {
        hx_mark("@F7775 modop_optimized");
        // required stack shape: [a b m]
        auto m_elem = stack_.get(stack_.top_index() - 2);
        if (!m_elem->literal()) {
            hx_mark("@L7778");
            return false;
        }
        auto const m = m_elem->literal()->value;
        m_elem.reset(); // Clear locations

        // The trivial group
        if (m == 0 || m == 1) {
            hx_mark("@L7785");
            stack_.pop();
            stack_.pop();
            stack_.pop();
            stack_.push_literal(0);
            return true;
        }

        auto a_elem = stack_.get(stack_.top_index());
        auto b_elem = stack_.get(stack_.top_index() - 1);

        static_assert(Absorb <= 1);
        static_assert(Unit <= 1);

        // Check whether we can constant fold the entire expression.
        if (a_elem->literal()) {
            hx_mark("@L7800");
            if constexpr (Absorb != Unit) {
                hx_mark("@L7801");
                if (a_elem->literal()->value == Absorb) {
                    hx_mark("@L7802");
                    stack_.pop();
                    stack_.pop();
                    stack_.pop();
                    push(Absorb);
                    return true;
                }
            }
            if (b_elem->literal()) {
                hx_mark("@L7810");
                stack_.pop();
                stack_.pop();
                stack_.pop();
                auto const &a = a_elem->literal()->value;
                auto const &b = b_elem->literal()->value;
                push(ModOp(a, b, m));
                return true;
            }
        }
        else if (b_elem->literal()) {
            hx_mark("@L7820");
            if constexpr (Absorb != Unit) {
                hx_mark("@L7821");
                if (b_elem->literal()->value == Absorb) {
                    hx_mark("@L7822");
                    stack_.pop();
                    stack_.pop();
                    stack_.pop();
                    push(Absorb);
                    return true;
                }
            }
        }

        // Only proceed if we can rewrite
        // (a + b) % m, where m = 2^n
        // as
        // (a + b) & (n - 1)
        if (popcount(m) != 1) {
            hx_mark("@L7836");
            return false;
        }

        // Pop the operands
        stack_.pop();
        stack_.pop();
        stack_.pop();

        // Check whether we can elide the addition.
        if (b_elem->literal() && b_elem->literal()->value == Unit) {
            hx_mark("@L7846");
            b_elem.reset(); // Clear to free registers and stack offset.
            auto mask = stack_.alloc_literal(Literal{m - 1});
            stack_.push(and_(std::move(a_elem), std::move(mask), {}));
        }
        else if (a_elem->literal() && a_elem->literal()->value == Unit) {
            hx_mark("@L7851");
            a_elem.reset(); // Clear to free registers and stack offset.
            auto mask = stack_.alloc_literal(Literal{m - 1});
            stack_.push(and_(std::move(b_elem), std::move(mask), {}));
        }
        else {
            hx_mark("@L7856");
            size_t const exp = bit_width(m) - 1;
            // The heavy lifting is done by the following function.
            (this->*ModOpByMask)(std::move(a_elem), std::move(b_elem), exp);
        }

        return true;
    }

    // Discharge
    bool Emitter::addmod_opt()
    {
        hx_mark("@F7867 addmod_opt");
        return modop_optimized<monad::addmod, 0, 0, &Emitter::add_mod2>();
    }

    void Emitter::add_mod2(
        StackElemRef const a_elem, StackElemRef const b_elem, size_t const exp)
    {
        hx_mark("@F7873 add_mod2");
        {
            hx_mark("@L7874");
            RegReserv const a_reserv{a_elem};
            RegReserv const b_reserv{b_elem};
            discharge_deferred_comparison();
        }

        auto [left, left_loc, right, right_loc] =
            get_mod2_bin_dest_and_source(a_elem, b_elem, exp, {});
        auto left_op = get_operand(left, left_loc);
        auto right_op = get_operand(right, right_loc);
        MONAD_DEBUG_ASSERT(!std::holds_alternative<x86::Ymm>(right_op));

        size_t const numQwords = div64_ceil(exp);

        // Skip initial additions by zero.
        size_t start_offset = 0;
        if (right->literal()) {
            hx_mark("@L7890");
            while (start_offset < numQwords) {
                hx_mark("@L7891");
                uint64_t const mask =
                    start_offset + 1 == numQwords && (exp & 63) != 0
                        ? (uint64_t{1} << (exp & 63)) - 1
                        : std::numeric_limits<uint64_t>::max();
                if ((right->literal()->value[start_offset] & mask) != 0) {
                    hx_mark("@L7896");
                    break;
                }
                ++start_offset;
            }
        }

        // Common logic for emitting masks for a single destination
        // register or destination memory.
        auto emit_mask = [&](std::variant<x86::Gp, x86::Mem> const &dst) {
            std::visit(
                Cases{
                    [&](x86::Gp const &dst) {
                        if ((exp & 63) == 8) {
                            hx_mark("@L7909");
                            as_.movzx(dst.r32(), dst.r8Lo());
                            return;
                        }

                        if ((exp & 63) == 16) {
                            hx_mark("@L7914");
                            as_.movzx(dst.r32(), dst.r16());
                            return;
                        }

                        if (start_offset == numQwords) {
                            hx_mark("@L7919");
                            if ((exp & 63) == 0) {
                                hx_mark("@L7920");
                                return;
                            }
                        }
                        else {
                            hx_mark("@L7924");
                            if ((exp & 31) == 0) {
                                hx_mark("@L7925");
                                return;
                            }
                        }

                        uint64_t const mask =
                            (1ULL << uint64_t(exp % 64)) - 1ULL;
                        if (std::bit_width(mask) <= 32) {
                            hx_mark("@L7932");
                            as_.and_(dst.r32(), mask);
                        }
                        else {
                            hx_mark("@L7935");
                            as_.movabs(x86::rax, mask);
                            as_.and_(dst, x86::rax);
                        }
                    },
                    [&](x86::Mem const &dst) {
                        if ((exp & 63) == 0) {
                            hx_mark("@L7941");
                            return;
                        }
                        uint64_t const mask =
                            (1ULL << uint64_t(exp % 64)) - 1ULL;
                        if (std::bit_width(mask) < 32) {
                            hx_mark("@L7946");
                            as_.and_(dst, mask);
                        }
                        else {
                            hx_mark("@L7949");
                            as_.movabs(x86::rax, mask);
                            as_.and_(dst, x86::rax);
                        }
                    }},
                dst);
        };

        // Common logic for clearing the upper destination register(s)
        // or part(s) of the destination memory.
        auto clear_upper_dest = [&](std::variant<Gpq256, x86::Mem> const &dst) {
            std::visit(
                Cases{
                    [&](Gpq256 const &c) {
                        for (size_t i = numQwords; i < 4; i++) {
                            hx_mark("@L7963");
                            if (!stack_.has_deferred_comparison()) {
                                hx_mark("@L7964");
                                as_.xor_(c[i].r32(), c[i].r32());
                            }
                            else {
                                hx_mark("@L7967");
                                as_.mov(c[i], 0);
                            }
                        }
                    },
                    [&](x86::Mem const &c) {
                        x86::Mem temp{c};
                        for (size_t i = numQwords; i < 4; i++) {
                            hx_mark("@L7974");
                            temp.addOffset(8);
                            as_.mov(temp, 0);
                        }
                    }},
                dst);
        };

        // The general logic for computing (a + b) & (n - 1)
        if (std::holds_alternative<Gpq256>(left_op)) {
            hx_mark("@L7983");
            Gpq256 const &a = std::get<Gpq256>(left_op);
            std::visit(
                Cases{
                    [&](Gpq256 const &b) {
                        for (size_t i = start_offset; i < numQwords; i++) {
                            hx_mark("@L7988");
                            size_t const bits_occupied =
                                i + 1 == numQwords ? exp - (i * 64) : 64;
                            if (i == start_offset) {
                                hx_mark("@L7991");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L7992");
                                    as_.add(a[i].r32(), b[i].r32());
                                }
                                else {
                                    hx_mark("@L7995");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.add(a[i].r64(), b[i].r64());
                                }
                            }
                            else {
                                hx_mark("@L8000");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8001");
                                    as_.adc(a[i].r32(), b[i].r32());
                                }
                                else {
                                    hx_mark("@L8004");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.adc(a[i].r64(), b[i].r64());
                                }
                            }
                        }
                        emit_mask(a[numQwords - 1]);
                        clear_upper_dest(a);
                    },
                    [&](x86::Mem const &b) {
                        x86::Mem temp{b};
                        temp.addOffset(static_cast<int64_t>(start_offset) * 8);
                        for (size_t i = start_offset; i < numQwords; i++) {
                            hx_mark("@L8016");
                            size_t const bits_occupied =
                                i + 1 == numQwords ? exp - (i * 64) : 64;
                            if (i == start_offset) {
                                hx_mark("@L8019");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8020");
                                    as_.add(a[i].r32(), temp);
                                }
                                else {
                                    hx_mark("@L8023");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.add(a[i].r64(), temp);
                                }
                            }
                            else {
                                hx_mark("@L8028");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8029");
                                    as_.adc(a[i].r32(), temp);
                                }
                                else {
                                    hx_mark("@L8032");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.adc(a[i].r64(), temp);
                                }
                            }
                            temp.addOffset(8);
                        }
                        emit_mask(a[numQwords - 1]);
                        clear_upper_dest(a);
                    },
                    [&](Imm256 const &b) {
                        for (size_t i = start_offset; i < numQwords; i++) {
                            hx_mark("@L8043");
                            size_t const bits_occupied =
                                i + 1 == numQwords ? exp - (i * 64) : 64;
                            if (i == start_offset) {
                                hx_mark("@L8046");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8047");
                                    as_.add(a[i].r32(), b[i]);
                                }
                                else {
                                    hx_mark("@L8050");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.add(a[i].r64(), b[i]);
                                }
                            }
                            else {
                                hx_mark("@L8055");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8056");
                                    as_.adc(a[i].r32(), b[i]);
                                }
                                else {
                                    hx_mark("@L8059");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.adc(a[i].r64(), b[i]);
                                }
                            }
                        }
                        emit_mask(a[numQwords - 1]);
                        clear_upper_dest(a);
                    },
                    [](x86::Ymm const &) { std::unreachable(); },
                },
                right_op);
        }
        else {
            hx_mark("@L8072");
            MONAD_DEBUG_ASSERT(std::holds_alternative<x86::Mem>(left_op));
            MONAD_DEBUG_ASSERT(!std::holds_alternative<x86::Mem>(right_op));

            x86::Mem const &a = std::get<x86::Mem>(left_op);
            std::visit(
                Cases{
                    [&](Gpq256 const &b) {
                        x86::Mem temp{a};
                        temp.addOffset(
                            static_cast<int64_t>(start_offset) * 8 - 8);
                        for (size_t i = start_offset; i < numQwords; i++) {
                            hx_mark("@L8083");
                            temp.addOffset(8);
                            size_t const bits_occupied =
                                i + 1 == numQwords ? exp - (i * 64) : 64;
                            if (i == start_offset) {
                                hx_mark("@L8087");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8088");
                                    as_.add(temp, b[i].r32());
                                }
                                else {
                                    hx_mark("@L8091");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.add(temp, b[i].r64());
                                }
                            }
                            else {
                                hx_mark("@L8096");
                                if (bits_occupied <= 32) {
                                    hx_mark("@L8097");
                                    as_.adc(temp, b[i].r32());
                                }
                                else {
                                    hx_mark("@L8100");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.adc(temp, b[i].r64());
                                }
                            }
                        };
                        emit_mask(temp);
                        clear_upper_dest(temp);
                    },
                    [&](Imm256 const &b) {
                        x86::Mem temp{a};
                        temp.addOffset(
                            static_cast<int64_t>(start_offset) * 8 - 8);
                        for (size_t i = start_offset; i < numQwords; i++) {
                            hx_mark("@L8113");
                            temp.addOffset(8);
                            size_t const bits_occupied =
                                i + 1 == numQwords ? exp - (i * 64) : 64;
                            if (i == start_offset) {
                                hx_mark("@L8117");
                                if (bits_occupied <= 8) {
                                    hx_mark("@L8118");
                                    temp.setSize(1);
                                    as_.add(temp, b[i]);
                                }
                                else if (bits_occupied <= 16) {
                                    hx_mark("@L8122");
                                    temp.setSize(2);
                                    as_.add(temp, b[i]);
                                }
                                else if (bits_occupied <= 32) {
                                    hx_mark("@L8126");
                                    temp.setSize(4);
                                    as_.add(temp, b[i]);
                                }
                                else {
                                    hx_mark("@L8130");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.add(temp, b[i]);
                                }
                            }
                            else {
                                hx_mark("@L8135");
                                if (bits_occupied <= 8) {
                                    hx_mark("@L8136");
                                    temp.setSize(1);
                                    as_.adc(temp, b[i]);
                                }
                                else if (bits_occupied <= 16) {
                                    hx_mark("@L8140");
                                    temp.setSize(2);
                                    as_.adc(temp, b[i]);
                                }
                                else if (bits_occupied <= 32) {
                                    hx_mark("@L8144");
                                    temp.setSize(4);
                                    as_.adc(temp, b[i]);
                                }
                                else {
                                    hx_mark("@L8148");
                                    MONAD_DEBUG_ASSERT(bits_occupied <= 64);
                                    as_.adc(temp, b[i]);
                                }
                            }
                        };
                        temp.setSize(8);
                        emit_mask(temp);
                        clear_upper_dest(temp);
                    },
                    [](auto const &) { std::unreachable(); },
                },
                right_op);
        }
        stack_.push(std::move(left));
    }

    // Discharge
    bool Emitter::mulmod_opt()
    {
        hx_mark("@F8167 mulmod_opt");
        return modop_optimized<monad::mulmod, 1, 0, &Emitter::mul_mod2>();
    }

    void Emitter::mul_mod2(
        StackElemRef a_elem, StackElemRef b_elem, size_t const exp)
    {
        hx_mark("@F8173 mul_mod2");
        {
            hx_mark("@L8174");
            RegReserv const a_reserv{a_elem};
            RegReserv const b_reserv{b_elem};
            discharge_deferred_comparison();
        }

        MONAD_DEBUG_ASSERT(exp >= 1 && exp < 256);
        if (a_elem->literal()) {
            hx_mark("@L8181");
            std::swap(a_elem, b_elem);
        }
        MONAD_DEBUG_ASSERT(!a_elem->literal().has_value());

        auto mask = (1 << uint256_t{exp}) - 1;
        auto const last_ix = (exp - 1) >> 6;
        static constexpr size_t inline_threshold = 1;

        // We will inline the multiplication in two cases.
        // 1. If the number of qwords is at most `inline_threshold + 1`,
        //    then inline the multiplication to avoid overhead of a
        //    runtime call.
        // 2. If multiplying by a known literal and one qword of the
        //    literal is zero, then inline to save at least one x86
        //    multiplication instruction.
        if (b_elem->literal()) {
            hx_mark("@L8197");
            auto b = b_elem->literal()->value & mask;
            bool has_zero = false;
            for (size_t i = 0; i <= last_ix; ++i) {
                hx_mark("@L8200");
                has_zero |= b[i] == 0;
            }
            if (last_ix <= inline_threshold || has_zero) {
                hx_mark("@L8203");
                b_elem.reset(); // Clear registers.
                stack_.push(mul_with_bit_size(exp, std::move(a_elem), b, {}));
                return;
            }
        }
        else if (last_ix <= inline_threshold) {
            hx_mark("@L8209");
            if (b_elem->general_reg()) {
                hx_mark("@L8210");
                auto const &b = general_reg_to_gpq256(*b_elem->general_reg());
                GeneralRegReserv const b_reserv{b_elem};
                stack_.push(mul_with_bit_size(
                    exp, std::move(a_elem), b, std::make_tuple(b_elem)));
            }
            else {
                hx_mark("@L8216");
                if (!b_elem->stack_offset()) {
                    hx_mark("@L8217");
                    mov_avx_reg_to_stack_offset(b_elem);
                }
                auto const &b = stack_offset_to_mem(*b_elem->stack_offset());
                stack_.push(mul_with_bit_size(
                    exp, std::move(a_elem), b, std::make_tuple(b_elem)));
            }
            return;
        }

        MONAD_DEBUG_ASSERT(exp > 128);
        spill_caller_save_regs(false);

        auto call_runtime_mul = [&](RuntimeImpl &&rt) {
            rt.pass(std::move(a_elem));
            rt.pass(std::move(b_elem));
            rt.call_impl();
        };
        if (exp <= 192) {
            hx_mark("@L8235");
            call_runtime_mul(
                Runtime<uint256_t *, uint256_t const *, uint256_t const *>(
                    this, false, monad_vm_runtime_mul_192));
        }
        else {
            hx_mark("@L8240");
            call_runtime_mul(
                Runtime<uint256_t *, uint256_t const *, uint256_t const *>(
                    this, false, runtime::mul));
        }

        MONAD_DEBUG_ASSERT(stack_.top()->stack_offset().has_value());
        auto res_mem = stack_offset_to_mem(*stack_.top()->stack_offset());
        res_mem.addOffset(static_cast<int64_t>(last_ix * 8));
        if (exp & 63) {
            hx_mark("@L8249");
            auto const last_mask = mask[last_ix];
            if (std::bit_width(last_mask) < 32) {
                hx_mark("@L8251");
                as_.and_(res_mem, last_mask);
            }
            else {
                hx_mark("@L8254");
                as_.mov(x86::rax, last_mask);
                as_.and_(res_mem, x86::rax);
            }
        }
        if (last_ix < 3) {
            hx_mark("@L8259");
            res_mem.addOffset(8);
            MONAD_DEBUG_ASSERT(last_ix == 2);
            as_.mov(res_mem, 0);
        }
    }

    // Count the number of leading zeros of `src` into `dst`.
    // The operands in `src` must be ordered from least to most significant.
    // The registers of `src` may coincide with the registers of `dst`.
    template <typename T>
    void
    Emitter::array_leading_zeros(std::array<T, 4> const &src, Gpq256 const &dst)
    {
        hx_mark("@F8272 array_leading_zeros");
        // The operands are traversed from least significant to most significant
        // so that the last non-zero operand determines the result.
        for (size_t i = 0; i < 4; ++i) {
            hx_mark("@L8275");
            auto const word_offset = static_cast<int32_t>(64 * (3 - i));
            // Compute number of leading zeros. CF == 1 iff src[i] == 0
            as_.lzcnt(dst[i], src[i]);
            if (word_offset != 0) {
                hx_mark("@L8279");
                // Leave flags unchanged
                as_.lea(dst[i].r32(), x86::ptr(dst[i], word_offset));
            }
            if (i != 0) {
                hx_mark("@L8283");
                as_.cmovnc(dst[0].r32(), dst[i].r32()); // if src[i] != 0
            }
        }
        for (size_t i = 1; i < 4; ++i) {
            hx_mark("@L8287");
            as_.xor_(dst[i].r32(), dst[i].r32());
        }
    }

    // Count the byte width (number of significant bytes) of the value.
    // The operands in `arr` must be ordered from least to most significant.
    template <typename T, size_t N>
    void Emitter::array_byte_width(std::array<T, N> const &arr)
    {
        hx_mark("@F8296 array_byte_width");
        auto const scratch_reg = [this] {
            if (stack_.has_free_general_reg()) {
                hx_mark("@L8298");
                auto [e, _] = alloc_general_reg();
                return general_reg_to_gpq256(*e->general_reg())[0];
            }
            else {
                hx_mark("@L8302");
                as_.push(reg_context);
                return reg_context;
            }
        }();

        // The operands are traversed from least significant to most significant
        // so that the last non-zero operand determines the bit width.
        for (size_t i = 0; i < N; ++i) {
            hx_mark("@L8310");
            auto const word_offset = static_cast<int32_t>(64 * (i + 1));
            // Compute operand bit width (negative). CF == 1 iff arr[i] == 0
            as_.lzcnt(scratch_reg, arr[i]);
            as_.lea(
                scratch_reg.r32(), x86::ptr(scratch_reg.r32(), -word_offset));
            if (i == 0) {
                hx_mark("@L8316");
                as_.mov(x86::eax, scratch_reg.r32()); // init accumulator
            }
            else {
                hx_mark("@L8319");
                as_.cmovnc(x86::eax, scratch_reg.r32()); // if arr[i] != 0
            }
        }

        // eax = bit width (negative), byte width = (-eax + 7) / 8
        as_.neg(x86::eax);
        as_.add(x86::eax, 7);
        as_.sar(x86::eax, 3);

        if (scratch_reg == reg_context) {
            hx_mark("@L8329");
            as_.pop(reg_context);
        }
    }

    // Compute byte width of stack element, stores the result in x86::eax.
    void Emitter::stack_elem_byte_width(StackElemRef const elem)
    {
        hx_mark("@F8336 stack_elem_byte_width");
        if (elem->general_reg()) {
            hx_mark("@L8337");
            auto const &gpq = general_reg_to_gpq256(*elem->general_reg());
            std::array<asmjit::x86::Gpq, 4> const &gpq_r64 = {
                gpq[0].r64(), gpq[1].r64(), gpq[2].r64(), gpq[3].r64()};
            array_byte_width(gpq_r64);
        }
        else if (elem->stack_offset()) {
            hx_mark("@L8343");
            array_byte_width(stack_offset_to_mem256(*elem->stack_offset()));
        }
        else if (elem->avx_reg()) {
            hx_mark("@L8346");
            auto const avx_reg = avx_reg_to_ymm(*elem->avx_reg());
            auto [avx_tmp_elem, _] = alloc_avx_reg();
            auto const avx_tmp = avx_reg_to_ymm(*avx_tmp_elem->avx_reg());
            as_.vpxor(avx_tmp, avx_tmp, avx_tmp);
            as_.vpcmpeqb(avx_tmp, avx_reg, avx_tmp); // tmp.b = (reg.b == 0)
            as_.vpmovmskb(x86::eax, avx_tmp); // eax = mask of zero bytes
            as_.not_(x86::eax); // eax = mask of non-zero bytes
            as_.lzcnt(x86::eax, x86::eax);
            as_.sub(x86::eax, 32);
            as_.neg(x86::eax); // eax = 32 - lzcnt(mask)
        }
        else {
            hx_mark("@L8358");
            MONAD_ASSERT(!elem->literal().has_value());
        }
    }

    void Emitter::exp_emit_gas_decrement_by_literal(
        uint256_t const exp, uint32_t const gas_factor)
    {
        hx_mark("@F8365 exp_emit_gas_decrement_by_literal");
        discharge_deferred_comparison();

        auto const exponent_byte_size = count_significant_bytes(exp);
        // The static work cost of EXP is already sufficient to cover for
        // the accumulated static work by an optimized EXP, so no gas check:
        auto const gas = static_cast<int32_t>(exponent_byte_size * gas_factor);
        if (gas) {
            hx_mark("@L8372");
            gas_decrement_no_check(gas);
        }
    }

    void Emitter::exp_emit_gas_decrement_by_stack_elem(
        StackElemRef const exponent_elem, uint32_t const gas_factor)
    {
        hx_mark("@F8379 exp_emit_gas_decrement_by_stack_elem");
        MONAD_ASSERT(!exponent_elem->literal().has_value());

        RegReserv const reserv{exponent_elem};

        discharge_deferred_comparison();

        stack_elem_byte_width(exponent_elem);
        gpr_mul_by_uint64<true>(x86::rax, x86::rax, gas_factor);
        // The static work cost of EXP is already sufficient to cover for
        // the accumulated static work by an optimized EXP, so no gas check:
        gas_decrement_no_check(x86::rax);
    }

    // Discharge via exp_emit_gas_decrement_*.
    // It is assumed that the work of optimized EXP does not exceed the static
    // work cost of the EXP instruction. See `static_assert` in `Emitter::exp`.
    bool Emitter::exp_optimized(
        int64_t const remaining_base_gas, uint32_t const gas_factor)
    {
        hx_mark("@F8398 exp_optimized");
        auto base_elem = stack_.get(stack_.top_index());
        auto exp_elem = stack_.get(stack_.top_index() - 1);

        if (base_elem->literal() && exp_elem->literal()) {
            hx_mark("@L8402");
            auto const base = base_elem->literal()->value;
            auto const exp = exp_elem->literal()->value;
            base_elem.reset(); // Locations not needed anymore
            exp_elem.reset(); // Locations not needed anymore

            // Evaluating exponentiation can be slow, so it's only done in
            // cases where we can bound the work required.
            // If the base is a power of 2, exponentiation is a simple shift.
            // Otherwise, if exponent is not too large.
            if (popcount(base) == 1) {
                hx_mark("@L8412");
                stack_.pop();
                stack_.pop();
                exp_emit_gas_decrement_by_literal(exp, gas_factor);
                uint256_t shift{0};
                uint64_t const b{bit_width(base) - 1};
                if (MONAD_LIKELY(b)) {
                    hx_mark("@L8418");
                    static constexpr uint64_t mask =
                        std::numeric_limits<uint32_t>::max();
                    shift = exp;
                    shift[0] = (exp[0] & ~mask) | b * (exp[0] & mask);
                }
                push(uint256_t{1} << shift);
                return true;
            }
            else if (exp <= 512) {
                hx_mark("@L8427");
                stack_.pop();
                stack_.pop();
                exp_emit_gas_decrement_by_literal(exp, gas_factor);
                push(monad::exp(base, exp));
                return true;
            }
            else if (exponential_constant_fold_counter_ < 500) {
                hx_mark("@L8434");
                // Limit number of reduction of large exponentiation to guard
                // against contracts taking too long to compile. In practice,
                // EXP with large exponents are more or less unexistent, so any
                // contract hitting this limit is likely malicious.
                // A limit of 500 limits the time spent on these cases to ~1ms.
                exponential_constant_fold_counter_ += 1;
                stack_.pop();
                stack_.pop();
                exp_emit_gas_decrement_by_literal(exp, gas_factor);
                push(monad::exp(base, exp));
                return true;
            }
        }
        else if (base_elem->literal()) {
            hx_mark("@L8448");
            auto const base = base_elem->literal()->value;
            base_elem.reset(); // Locations are not needed anymore
            if (base == 0) { // O ** exp semantic: 1 if exp = 0 else 0
                hx_mark("@L8451");
                stack_.pop();
                stack_.pop();
                {
                    hx_mark("@L8454");
                    RegReserv const exp_reserv{exp_elem};
                    exp_emit_gas_decrement_by_stack_elem(exp_elem, gas_factor);
                }
                push_iszero(std::move(exp_elem));
                return true;
            }
            else if (base == 1) { // 1 ** exp == 1
                hx_mark("@L8461");
                stack_.pop();
                stack_.pop();
                exp_emit_gas_decrement_by_stack_elem(
                    std::move(exp_elem), gas_factor);
                stack_.push_literal({1});
                return true;
            }
            else if (popcount(base) == 1) { // (2 ** k) ** n == 1 << (k * n)
                hx_mark("@L8469");
                stack_.pop();
                stack_.pop();
                {
                    hx_mark("@L8472");
                    RegReserv const exp_reserv{exp_elem};
                    exp_emit_gas_decrement_by_stack_elem(exp_elem, gas_factor);
                }
                if (base == 2) {
                    hx_mark("@L8476");
                    stack_.push(shl(
                        std::move(exp_elem), stack_.alloc_literal({1}), {}));
                    return true;
                }
                mov_stack_elem_to_general_reg(exp_elem);
                auto mul_elem = release_general_reg(std::move(exp_elem), {});
                auto const &gp =
                    general_reg_to_gpq256(*mul_elem->general_reg());
                as_.mov(x86::rax, gp[0]);
                uint8_t const b = static_cast<uint8_t>(bit_width(base) - 1);
                if (std::popcount(b) == 1) {
                    hx_mark("@L8487");
                    MONAD_DEBUG_ASSERT(b >= 2 && b <= 128);
                    gpr_mul_by_uint64_via_shl<false>(gp[0], gp[0], b);
                    constexpr auto mask = std::numeric_limits<int32_t>::min();
                    as_.test(x86::rax, mask);
                    as_.cmovnz(gp[0], x86::rax);
                }
                else {
                    hx_mark("@L8494");
                    gpr_mul_by_int32_via_imul<false>(gp[0], gp[0], b);
                    as_.cmovo(gp[0], x86::rax);
                }
                stack_.push(
                    shl(std::move(mul_elem), stack_.alloc_literal({1}), {}));
                return true;
            }
        }
        else if (exp_elem->literal()) {
            hx_mark("@L8503");
            auto const exp = exp_elem->literal()->value;
            exp_elem.reset(); // Locations are not needed anymore
            if (exp == 0) { // x ** 0 = 1
                hx_mark("@L8506");
                stack_.pop();
                stack_.pop();
                exp_emit_gas_decrement_by_literal(0, gas_factor);
                stack_.push_literal({1});
                return true;
            }
            else if (exp == 1) { // x ** 1 = x
                hx_mark("@L8513");
                stack_.pop();
                stack_.pop();
                {
                    hx_mark("@L8516");
                    RegReserv const base_reserv{base_elem};
                    exp_emit_gas_decrement_by_literal(1, gas_factor);
                }
                stack_.push(std::move(base_elem));
                return true;
            }
            else if (exp == 2) { // x ** 2 = x * x
                hx_mark("@L8523");
                stack_.pop();
                stack_.pop();
                {
                    hx_mark("@L8526");
                    RegReserv const base_reserv{base_elem};
                    exp_emit_gas_decrement_by_literal(2, gas_factor);
                }
                stack_.push(std::move(base_elem));
                dup(1);
                mul(remaining_base_gas);
                return true;
            }
        }

        return false;
    }
}
