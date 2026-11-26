// Differential harness: runs the same transactions through Monad's
// interpreter (interpreter::execute) and through native code produced by
// Monad's x86 emitter (native::compile), both from category-labs/monad
// v0.16.7 source, with the real runtime library, against one small in-memory
// host. Accounts other than code accounts are "virtual": a router that runs
// a script of calls inside unlockCallback, and an ERC20 token written in C++.
// Analysis harness only; it sends nothing to any network.
#include <category/vm/compiler/ir/x86.hpp>
#include <category/vm/evm/traits.hpp>
#include <category/vm/interpreter/execute.hpp>
#include <category/vm/interpreter/intercode.hpp>
#include <category/vm/runtime/types.hpp>
#include <asmjit/core/jitruntime.h>
#include <evmc/evmc.hpp>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#include "cov.hpp"

using namespace monad::vm;
#ifndef HX_STACK_T
#define HX_STACK_T monad::uint256_t
#endif
#ifdef HX_COV
namespace monad::vm::interpreter { uint8_t g_cov_hit[1 << 16]; }
#endif
using T = monad::MonadTraits<MONAD_TEN>;
using evmc::address;
using evmc::bytes32;

static std::vector<uint8_t> unhex(std::string const &h0)
{
    std::string h = h0.rfind("0x", 0) == 0 ? h0.substr(2) : h0;
    std::vector<uint8_t> v;
    for (size_t i = 0; i + 1 < h.size(); i += 2)
        v.push_back((uint8_t)std::stoul(h.substr(i, 2), nullptr, 16));
    return v;
}
static std::string hex(uint8_t const *p, size_t n)
{
    static char const *d = "0123456789abcdef";
    std::string s;
    for (size_t i = 0; i < n; i++) { s += d[p[i] >> 4]; s += d[p[i] & 15]; }
    return s;
}
static address addr_of(std::string const &h)
{
    auto v = unhex(h);
    address a{};
    std::memcpy(a.bytes + 20 - v.size(), v.data(), v.size());
    return a;
}
static std::string ah(address const &a) { return hex(a.bytes, 20); }
static std::string bh(bytes32 const &b) { return hex(b.bytes, 32); }

// 256-bit unsigned as 4 limbs little endian for token / native balances
struct U256 { uint64_t w[4]{}; };
static U256 from_be(uint8_t const *p)
{
    U256 r;
    for (int i = 0; i < 4; i++) {
        uint64_t x = 0;
        for (int j = 0; j < 8; j++) x = (x << 8) | p[(3 - i) * 8 + j];
        r.w[i] = x;
    }
    return r;
}
static void to_be(U256 const &x, uint8_t *p)
{
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 8; j++) p[(3 - i) * 8 + j] = (uint8_t)(x.w[i] >> (56 - 8 * j));
}
static bool lt(U256 const &a, U256 const &b)
{
    for (int i = 3; i >= 0; i--) if (a.w[i] != b.w[i]) return a.w[i] < b.w[i];
    return false;
}
static U256 add(U256 a, U256 const &b)
{
    unsigned __int128 c = 0;
    for (int i = 0; i < 4; i++) { c += (unsigned __int128)a.w[i] + b.w[i]; a.w[i] = (uint64_t)c; c >>= 64; }
    return a;
}
static U256 sub(U256 a, U256 const &b)
{
    __int128 c = 0;
    for (int i = 0; i < 4; i++) {
        __int128 t = (__int128)a.w[i] - b.w[i] + c;
        a.w[i] = (uint64_t)t; c = t < 0 ? -1 : 0;
    }
    return a;
}
static std::string uh(U256 const &x) { uint8_t b[32]; to_be(x, b); return hex(b, 32); }

// Exceptional halts are reported as one class: the compiled code reports a
// generic failure where the interpreter reports out of gas (both consume all
// gas, and a receipt or a caller sees only failure).
static char const *st(evmc_status_code c) { return c == EVMC_SUCCESS ? "success" : c == EVMC_REVERT ? "revert" : "halt"; }

struct Log { address a; std::vector<bytes32> topics; std::vector<uint8_t> data; };
struct World
{
    std::map<address, std::vector<uint8_t>> code;
    std::map<address, U256> bal;
    std::map<std::pair<address, bytes32>, bytes32> st, tst, orig;
    std::map<std::pair<address, address>, U256> tok; // (token, holder)
    std::set<address> warm;
    std::set<std::pair<address, bytes32>> warms;
    std::vector<Log> logs;
};

enum Mode { INTERP, NATIVE };

struct Engine;
struct Host : evmc::Host
{
    World w;
    Mode mode;
    Engine *eng;
    std::set<address> tokens;
    std::vector<std::string> trace;
    evmc_tx_context txc{};

    bool account_exists(address const &a) const noexcept override { return w.code.count(a) || w.bal.count(a); }
    bytes32 get_storage(address const &a, bytes32 const &k) const noexcept override
    {
        auto it = w.st.find({a, k});
        return it == w.st.end() ? bytes32{} : it->second;
    }
    evmc_storage_status set_storage(address const &a, bytes32 const &k, bytes32 const &v) noexcept override
    {
        auto key = std::make_pair(a, k);
        bytes32 cur = get_storage(a, k);
        if (!w.orig.count(key)) w.orig[key] = cur;
        bytes32 o = w.orig[key];
        bytes32 z{};
        w.st[key] = v;
        if (cur == v) return EVMC_STORAGE_ASSIGNED;
        if (o == cur) {
            if (o == z) return EVMC_STORAGE_ADDED;
            if (v == z) return EVMC_STORAGE_DELETED;
            return EVMC_STORAGE_MODIFIED;
        }
        if (o != z) {
            if (cur == z) return v == o ? EVMC_STORAGE_DELETED_RESTORED : EVMC_STORAGE_DELETED_ADDED;
            if (v == z) return EVMC_STORAGE_MODIFIED_DELETED;
            if (v == o) return EVMC_STORAGE_MODIFIED_RESTORED;
        }
        else if (v == z) return EVMC_STORAGE_ADDED_DELETED;
        return EVMC_STORAGE_ASSIGNED;
    }
    evmc::uint256be get_balance(address const &a) const noexcept override
    {
        evmc::uint256be r{};
        auto it = w.bal.find(a);
        if (it != w.bal.end()) to_be(it->second, r.bytes);
        return r;
    }
    size_t get_code_size(address const &a) const noexcept override
    {
        auto it = w.code.find(a);
        if (it != w.code.end()) return it->second.size();
        return tokens.count(a) ? 1 : 0;
    }
    bytes32 get_code_hash(address const &) const noexcept override { return bytes32{}; }
    size_t copy_code(address const &, size_t, uint8_t *, size_t) const noexcept override { return 0; }
    bool selfdestruct(address const &, address const &) noexcept override { return false; }
    evmc::Result call(evmc_message const &m) noexcept override;
    evmc_tx_context const *get_tx_context() const noexcept override { return &txc; }
    bytes32 get_block_hash(int64_t) const noexcept override { return bytes32{}; }
    void emit_log(address const &a, uint8_t const *d, size_t n, bytes32 const t[], size_t nt) noexcept override
    {
        Log l{a, std::vector<bytes32>(t, t + nt), std::vector<uint8_t>(d, d + n)};
        w.logs.push_back(l);
    }
    evmc_access_status access_account(address const &a) noexcept override
    {
        return w.warm.insert(a).second ? EVMC_ACCESS_COLD : EVMC_ACCESS_WARM;
    }
    evmc_access_status access_storage(address const &a, bytes32 const &k) noexcept override
    {
        return w.warms.insert({a, k}).second ? EVMC_ACCESS_COLD : EVMC_ACCESS_WARM;
    }
    bytes32 get_transient_storage(address const &a, bytes32 const &k) const noexcept override
    {
        auto it = w.tst.find({a, k});
        return it == w.tst.end() ? bytes32{} : it->second;
    }
    void set_transient_storage(address const &a, bytes32 const &k, bytes32 const &v) noexcept override { w.tst[{a, k}] = v; }
    evmc_page_storage_status update_page(address const &, bytes32 const &, evmc_storage_status) noexcept override { return {false, false}; }

    bool move(address const &from, address const &to, U256 const &v)
    {
        U256 fb = w.bal[from];
        if (lt(fb, v)) return false;
        w.bal[from] = sub(fb, v);
        w.bal[to] = add(w.bal[to], v);
        return true;
    }
    evmc::Result token_call(evmc_message const &m);
    evmc::Result router_call(evmc_message const &m);
    void close_delta(address const &router, evmc_message const &s0, int step, bool clear_exact);
    evmc::Result exec_code(evmc_message const &m);
};

static evmc_page_storage_status update_page_fn(evmc_host_context *, evmc_address const *, evmc_bytes32 const *, evmc_storage_status)
{
    return {false, false};
}
static evmc_host_interface g_iface;
static address g_pm;

struct Engine
{
    asmjit::JitRuntime rt;
    std::map<address, std::shared_ptr<compiler::native::Nativecode>> nat;
    std::map<address, std::unique_ptr<interpreter::Intercode>> ic;
};

static evmc::Result ok_result(std::vector<uint8_t> const &out, int64_t gas)
{
    return evmc::Result{EVMC_SUCCESS, gas, 0, out.data(), out.size()};
}

evmc::Result Host::exec_code(evmc_message const &m0)
{
    auto const &code = w.code[m0.recipient];
    evmc_message m = m0;
    size_t cap = 1u << 22;
    uint8_t *buf = (uint8_t *)std::aligned_alloc(64, cap);
    std::memset(buf, 0, cap);
    m.memory_handle = buf;
    m.memory = buf;
    m.memory_capacity = (uint32_t)cap;
    auto ctx = runtime::Context::from(&g_iface, to_context(), &m, std::span<uint8_t const>(code.data(), code.size()));
    auto *stack = (HX_STACK_T *)std::aligned_alloc(32, 1024 * 32);
    if (mode == NATIVE) {
        auto &nc = eng->nat[m.recipient];
        if (!nc) {
            nc = compiler::native::compile<T>(eng->rt, code.data(), interpreter::code_size_t::unsafe_from((uint32_t)code.size()), {});
            if (!nc->entrypoint()) { std::fprintf(stderr, "native compile failed\n"); std::abort(); }
            if (std::getenv("HX_COVOUT") && m.recipient == g_pm) cov::install();
        }
        nc->entrypoint()(&ctx, stack);
    }
    else {
        auto &icp = eng->ic[m.recipient];
        if (!icp) icp = std::make_unique<interpreter::Intercode>(code.data(), code.size());
        interpreter::execute<T>(ctx, *icp, stack);
    }
    auto r = ctx.copy_to_evmc_result<T>();
    ctx.return_to<T>(nullptr);
    std::free(stack);
    std::free(buf);
    return r;
}

static uint32_t sel(evmc_message const &m)
{
    if (m.input_size < 4) return 0;
    return (uint32_t)m.input_data[0] << 24 | (uint32_t)m.input_data[1] << 16 | (uint32_t)m.input_data[2] << 8 | m.input_data[3];
}
static address arg_addr(evmc_message const &m, int i)
{
    address a{};
    if (m.input_size >= 4 + 32 * (size_t)(i + 1)) std::memcpy(a.bytes, m.input_data + 4 + 32 * i + 12, 20);
    return a;
}
static U256 arg_u(evmc_message const &m, int i)
{
    uint8_t b[32]{};
    if (m.input_size >= 4 + 32 * (size_t)(i + 1)) std::memcpy(b, m.input_data + 4 + 32 * i, 32);
    return from_be(b);
}

evmc::Result Host::token_call(evmc_message const &m)
{
    address tk = m.recipient;
    std::vector<uint8_t> out(32, 0);
    uint32_t s = sel(m);
    if (s == 0x70a08231) { // balanceOf
        to_be(w.tok[{tk, arg_addr(m, 0)}], out.data());
        return ok_result(out, m.gas - 2600);
    }
    if (s == 0xa9059cbb || s == 0x23b872dd) { // transfer / transferFrom
        address from = s == 0xa9059cbb ? m.sender : arg_addr(m, 0);
        address to = s == 0xa9059cbb ? arg_addr(m, 0) : arg_addr(m, 1);
        U256 v = s == 0xa9059cbb ? arg_u(m, 1) : arg_u(m, 2);
        U256 fb = w.tok[{tk, from}];
        if (lt(fb, v)) return evmc::Result{EVMC_REVERT, m.gas - 5000, 0, nullptr, 0};
        w.tok[{tk, from}] = sub(fb, v);
        w.tok[{tk, to}] = add(w.tok[{tk, to}], v);
        out[31] = 1;
        return ok_result(out, m.gas - 30000);
    }
    return evmc::Result{EVMC_REVERT, m.gas, 0, nullptr, 0};
}

// unlockCallback(bytes): data is a script of steps, each
// [to 20][value 32][gas 8][len 4][calldata]
extern "C" void monad_keccak256(void const *, size_t, uint8_t *);
static std::vector<uint8_t> enc_call(char const *selhex, std::vector<std::vector<uint8_t>> const &words)
{
    auto v = unhex(selhex);
    for (auto const &x : words) { std::vector<uint8_t> wd(32, 0); std::memcpy(wd.data() + 32 - x.size(), x.data(), x.size()); v.insert(v.end(), wd.begin(), wd.end()); }
    return v;
}
void Host::close_delta(address const &router, evmc_message const &s0, int step, bool clear_exact)
{
    // read the router's delta for one currency through PM.exttload, then pay a debt or mint a credit
    address cur{};
    std::memcpy(cur.bytes, s0.input_data, 20);
    uint8_t pre[64]{};
    std::memcpy(pre + 12, router.bytes, 20);
    std::memcpy(pre + 44, cur.bytes, 20);
    uint8_t slot[32];
    monad_keccak256(pre, 64, slot);
    auto mk = [&](address to, std::vector<uint8_t> const &d, U256 v) {
        evmc_message s{};
        s.kind = EVMC_CALL; s.depth = s0.depth; s.gas = 3000000; s.recipient = to; s.code_address = to; s.sender = router;
        to_be(v, s.value.bytes);
        auto keep = std::make_shared<std::vector<uint8_t>>(d);
        s.input_data = keep->data(); s.input_size = keep->size();
        auto r = call(s);
        std::ostringstream os;
        os << "  close " << step << " to=" << ah(to) << " status=" << st(r.status_code) << " gasleft=" << r.gas_left << " out=" << hex(r.output_data, r.output_size);
        trace.push_back(os.str());
        return std::vector<uint8_t>(r.output_data, r.output_data + r.output_size);
    };
    auto out = mk(g_pm, enc_call("f135baaa", {std::vector<uint8_t>(slot, slot + 32)}), U256{});
    if (out.size() != 32) return;
    U256 d = from_be(out.data());
    bool neg = d.w[3] >> 63;
    std::vector<uint8_t> cb(cur.bytes, cur.bytes + 20), rb(router.bytes, router.bytes + 20);
    if (!(d.w[0] | d.w[1] | d.w[2] | d.w[3])) return;
    if (clear_exact) {
        // clear(currency, delta) with the exact current delta, positive or not
        uint8_t db[32]; to_be(d, db);
        mk(g_pm, enc_call("80f0b44c", {cb, std::vector<uint8_t>(db, db + 32)}), U256{});
        return;
    }
    if (neg) {
        U256 need = sub(U256{}, d);
        uint8_t nb[32]; to_be(need, nb);
        bool native = cur == address{};
        if (native) { mk(g_pm, enc_call("11da60b4", {}), need); }
        else {
            mk(g_pm, enc_call("a5841194", {cb}), U256{});
            std::vector<uint8_t> pmb(g_pm.bytes, g_pm.bytes + 20);
            mk(cur, enc_call("a9059cbb", {pmb, std::vector<uint8_t>(nb, nb + 32)}), U256{});
            mk(g_pm, enc_call("11da60b4", {}), U256{});
        }
    }
    else {
        uint8_t db[32]; to_be(d, db);
        mk(g_pm, enc_call("156e29f6", {rb, cb, std::vector<uint8_t>(db, db + 32)}), U256{});
    }
}

evmc::Result Host::router_call(evmc_message const &m)
{
    std::vector<uint8_t> out;
    if (sel(m) == 0x91dd7346 && m.input_size >= 4 + 64) {
        U256 off = arg_u(m, 0);
        size_t o = 4 + off.w[0];
        uint8_t lb[32]; std::memcpy(lb, m.input_data + o, 32);
        size_t len = from_be(lb).w[0];
        uint8_t const *p = m.input_data + o + 32;
        std::vector<uint8_t> script(p, p + len);
        size_t i = 0;
        int step = 0;
        while (i + 64 <= script.size()) {
            evmc_message s{};
            s.kind = EVMC_CALL;
            s.depth = m.depth + 1;
            std::memcpy(s.recipient.bytes, &script[i], 20);
            std::memcpy(s.value.bytes, &script[i + 20], 32);
            uint64_t g = 0; for (int k = 0; k < 8; k++) g = g << 8 | script[i + 52 + k];
            uint32_t n = 0; for (int k = 0; k < 4; k++) n = n << 8 | script[i + 60 + k];
            i += 64;
            s.gas = (int64_t)g;
            s.sender = m.recipient;
            s.code_address = s.recipient;
            s.input_data = script.data() + i;
            s.input_size = n;
            i += n;
            if (s.recipient == addr_of("ffff")) { close_delta(m.recipient, s, step++, false); continue; }
            if (s.recipient == addr_of("fffe")) { close_delta(m.recipient, s, step++, true); continue; }
            auto r = call(s);
            std::ostringstream os;
            os << "  step " << step++ << " to=" << ah(s.recipient) << " status=" << st(r.status_code) << " gasleft=" << r.gas_left
               << " out=" << hex(r.output_data, r.output_size);
            trace.push_back(os.str());
        }
        out.assign(64, 0);
        out[31] = 0x20;
        return ok_result(out, m.gas > 1000 ? m.gas - 1000 : 0);
    }
    return ok_result(out, m.gas);
}

evmc::Result Host::call(evmc_message const &m) noexcept
{
    World snap = w;
    U256 v = from_be(m.value.bytes);
    bool has_v = v.w[0] | v.w[1] | v.w[2] | v.w[3];
    if (has_v && !move(m.sender, m.recipient, v)) {
        w = snap;
        return evmc::Result{EVMC_INSUFFICIENT_BALANCE, m.gas, 0, nullptr, 0};
    }
    evmc::Result r{EVMC_SUCCESS, m.gas, 0, nullptr, 0};
    if (w.code.count(m.recipient)) r = exec_code(m);
    else if (tokens.count(m.recipient)) r = token_call(m);
    else r = router_call(m);
    if (r.status_code != EVMC_SUCCESS) w = snap;
    return r;
}

static std::string dump(Host const &h)
{
    std::ostringstream os;
    for (auto const &t : h.trace) os << t << "\n";
    for (auto const &[k, v] : h.w.st) os << "  st " << ah(k.first) << " " << bh(k.second) << " " << bh(v) << "\n";
    for (auto const &[k, v] : h.w.tst) os << "  tst " << ah(k.first) << " " << bh(k.second) << " " << bh(v) << "\n";
    for (auto const &[k, v] : h.w.bal) os << "  bal " << ah(k) << " " << uh(v) << "\n";
    for (auto const &[k, v] : h.w.tok) os << "  tok " << ah(k.first) << " " << ah(k.second) << " " << uh(v) << "\n";
    for (auto const &l : h.w.logs) {
        os << "  log " << ah(l.a);
        for (auto const &t : l.topics) os << " " << bh(t);
        os << " " << hex(l.data.data(), l.data.size()) << "\n";
    }
    return os.str();
}

struct Tx { address from, to; U256 value; int64_t gas; std::vector<uint8_t> data; };
struct Scen { std::string name; std::vector<Tx> txs; };

static std::string run(Scen const &sc, Mode mode, Engine &eng, World const &init, std::set<address> const &tokens)
{
    Host h;
    h.w = init;
    h.mode = mode;
    h.eng = &eng;
    h.tokens = tokens;
    h.txc.chain_id.bytes[31] = 143;
    h.txc.block_number = 125000000;
    h.txc.block_timestamp = 1790000000;
    h.txc.block_gas_limit = 200000000;
    int n = 0;
    for (auto const &tx : sc.txs) {
        h.w.tst.clear();
        h.w.orig.clear();
        h.w.warm.clear();
        h.w.warms.clear();
        h.w.warm.insert(tx.from);
        h.w.warm.insert(tx.to);
        evmc_message m{};
        m.kind = EVMC_CALL;
        m.gas = tx.gas;
        m.recipient = tx.to;
        m.sender = tx.from;
        m.code_address = tx.to;
        to_be(tx.value, m.value.bytes);
        m.input_data = tx.data.data();
        m.input_size = tx.data.size();
        auto r = h.call(m);
        std::ostringstream os;
        os << "tx " << n++ << " status=" << st(r.status_code) << " gasleft=" << r.gas_left << " out=" << hex(r.output_data, r.output_size);
        h.trace.push_back(os.str());
    }
    return dump(h);
}

int main(int argc, char **argv)
{
    g_iface = evmc::Host::get_interface();
    g_iface.update_page = update_page_fn;
    g_pm = addr_of("188d586ddcf52439676ca21a244753fa19f9ea8e");
    // argv[1]: world file, argv[2]: scenario file
    World init;
    std::set<address> tokens;
    {
        std::ifstream f(argv[1]);
        std::string kind;
        while (f >> kind) {
            if (kind == "code") { std::string a, c; f >> a >> c; init.code[addr_of(a)] = unhex(c); }
            else if (kind == "bal") { std::string a, v; f >> a >> v; auto b = unhex(v); uint8_t x[32]{}; std::memcpy(x + 32 - b.size(), b.data(), b.size()); init.bal[addr_of(a)] = from_be(x); }
            else if (kind == "token") { std::string a; f >> a; tokens.insert(addr_of(a)); }
            else if (kind == "tok") { std::string t, a, v; f >> t >> a >> v; auto b = unhex(v); uint8_t x[32]{}; std::memcpy(x + 32 - b.size(), b.data(), b.size()); init.tok[{addr_of(t), addr_of(a)}] = from_be(x); }
            else if (kind == "st") { std::string a, k, v; f >> a >> k >> v; bytes32 kk{}, vv{}; auto kb = unhex(k), vb = unhex(v); std::memcpy(kk.bytes + 32 - kb.size(), kb.data(), kb.size()); std::memcpy(vv.bytes + 32 - vb.size(), vb.data(), vb.size()); init.st[{addr_of(a), kk}] = vv; }
        }
    }
    std::vector<Scen> scens;
    {
        std::ifstream f(argv[2]);
        std::string line;
        while (std::getline(f, line)) {
            std::istringstream is(line);
            std::string kind;
            is >> kind;
            if (kind == "SCEN") { scens.push_back({}); is >> scens.back().name; }
            else if (kind == "TX") {
                std::string fr, to, v, g, d;
                is >> fr >> to >> v >> g >> d;
                Tx t{addr_of(fr), addr_of(to), {}, std::stoll(g), unhex(d)};
                auto b = unhex(v); uint8_t x[32]{}; std::memcpy(x + 32 - b.size(), b.data(), b.size()); t.value = from_be(x);
                scens.back().txs.push_back(t);
            }
        }
    }
    bool verbose = argc > 3 && std::string(argv[3]) == "-v";
    Engine eng;
    size_t mism = 0;
    for (auto const &sc : scens) {
        auto a = run(sc, INTERP, eng, init, tokens);
        auto b = run(sc, NATIVE, eng, init, tokens);
        bool same = a == b;
        if (!same) mism++;
        if (std::getenv("HX_DIGEST")) {
            uint8_t da[32], db[32];
            monad_keccak256(a.data(), a.size(), da);
            monad_keccak256(b.data(), b.size(), db);
            std::printf("%s %s %s %s\n", same ? "SAME" : "DIFF", sc.name.c_str(), hex(da, 8).c_str(), hex(db, 8).c_str());
        }
        else
        std::printf("%s %s\n", same ? "SAME" : "DIFF", sc.name.c_str());
        if (verbose || !same) {
            std::printf("--- interp\n%s--- native\n%s", a.c_str(), b.c_str());
        }
        std::fflush(stdout);
    }
    std::printf("scenarios=%zu mismatches=%zu\n", scens.size(), mism);
    cov::dump();
#ifdef HX_COV
    if (std::getenv("HX_COV_OUT")) {
        std::ofstream c(std::getenv("HX_COV_OUT"));
        for (int i = 0; i < (1 << 16); i++) if (interpreter::g_cov_hit[i]) c << i << "\n";
    }
#endif
    return 0;
}
