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
#include <functional>
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


// Replay of mined Monad PoolManager transactions through Monad's interpreter and through native code
// from Monad's x86 emitter (same build as harness.cpp). Only the PoolManager's frames execute; every call
// the PoolManager makes is answered from the block's call tree (callTracer), and the PoolManager frames
// recorded inside that call run first, in order, as in cycle 13's pmreplay.py. The PoolManager's storage
// starts from the prestate of the transaction. Analysis harness only; nothing is sent to any network.
static char const *st(evmc_status_code c) { return c == EVMC_SUCCESS ? "success" : c == EVMC_REVERT ? "revert" : "halt"; }
struct Node { int id, parent; bool pm; std::string type; address to, from; U256 value; int64_t gas, gasUsed; bool ok; bool oog; std::vector<uint8_t> in, out; std::vector<int> kids; };
struct Log { std::vector<bytes32> topics; std::vector<uint8_t> data; };
struct TxIn { std::string hash; int status; evmc_tx_context txc{}; std::map<bytes32, bytes32> pre; U256 bal; std::vector<Node> nodes; std::vector<Log> rlogs; std::map<bytes32, bytes32> post; bool has_post = false; std::set<address> acl; std::set<bytes32> acls; };
enum Mode { INTERP, NATIVE };
struct Engine { asmjit::JitRuntime rt; std::shared_ptr<compiler::native::Nativecode> nat; std::unique_ptr<interpreter::Intercode> ic; };
static address g_pm;
static int64_t g_gas = -1; // HX_GAS, or the current value of HX_GAS_SWEEP
static bool g_quiet = false;
static std::vector<uint8_t> g_code;
static evmc_host_interface g_iface;
struct Frame { int node; size_t next = 0; };
struct Host : evmc::Host
{
    TxIn const *tx; Mode mode; Engine *eng;
    std::map<bytes32, bytes32> s, orig, t;
    std::set<address> warm; std::set<bytes32> warms;
    U256 bal; std::vector<Log> logs;
    std::vector<Frame> stack;
    std::vector<std::string> fr; // per PoolManager frame: status, gas used, output
    std::string div; int forced = 0;
    // MIP-8 (active from MONAD_TEN): storage warmth and SSTORE page status are tracked per page of 128 slots,
    // as in category/execution/ethereum/state3/page_tracker.hpp at v0.16.7
    struct Page { bool accessed = false, dirty = false; int16_t peak = 0, cur = 0; };
    std::map<bytes32, Page> pages;
    static bytes32 pkey(bytes32 k) { U256 x = from_be(k.bytes); for (int i = 0; i < 4; i++) x.w[i] = (x.w[i] >> 7) | (i < 3 ? x.w[i + 1] << 57 : 0); bytes32 r; to_be(x, r.bytes); return r; }
    struct Snap { std::map<bytes32, bytes32> s, t; U256 bal; size_t nlogs; std::map<bytes32, Page> pages; std::set<bytes32> warms; std::set<address> warm; };
    Snap snap() { return {s, t, bal, logs.size(), pages, warms, warm}; }
    void restore(Snap const &x) { s = x.s; t = x.t; bal = x.bal; logs.resize(x.nlogs); pages = x.pages; warms = x.warms; warm = x.warm; }
    bool account_exists(address const &) const noexcept override { return true; }
    bytes32 get_storage(address const &a, bytes32 const &k) const noexcept override
    {
        if (a != g_pm) return {};
        auto it = s.find(k); return it == s.end() ? bytes32{} : it->second;
    }
    evmc_storage_status set_storage(address const &a, bytes32 const &k, bytes32 const &v) noexcept override
    {
        if (a != g_pm) return EVMC_STORAGE_ASSIGNED;
        bytes32 cur = get_storage(a, k);
        if (!orig.count(k)) orig[k] = cur;
        bytes32 o = orig[k], z{};
        s[k] = v;
        if (cur == v) return EVMC_STORAGE_ASSIGNED;
        if (o == cur) { if (o == z) return EVMC_STORAGE_ADDED; if (v == z) return EVMC_STORAGE_DELETED; return EVMC_STORAGE_MODIFIED; }
        if (o != z) { if (cur == z) return v == o ? EVMC_STORAGE_DELETED_RESTORED : EVMC_STORAGE_DELETED_ADDED; if (v == z) return EVMC_STORAGE_MODIFIED_DELETED; if (v == o) return EVMC_STORAGE_MODIFIED_RESTORED; }
        else if (v == z) return EVMC_STORAGE_ADDED_DELETED;
        return EVMC_STORAGE_ASSIGNED;
    }
    evmc::uint256be get_balance(address const &a) const noexcept override { evmc::uint256be r{}; if (a == g_pm) to_be(bal, r.bytes); return r; }
    size_t get_code_size(address const &a) const noexcept override { return a == g_pm ? g_code.size() : 1; }
    bytes32 get_code_hash(address const &) const noexcept override { return bytes32{}; }
    size_t copy_code(address const &, size_t, uint8_t *, size_t) const noexcept override { return 0; }
    bool selfdestruct(address const &, address const &) noexcept override { return false; }
    evmc::Result call(evmc_message const &m) noexcept override;
    evmc_tx_context const *get_tx_context() const noexcept override { return &tx->txc; }
    bytes32 get_block_hash(int64_t) const noexcept override { return bytes32{}; }
    void emit_log(address const &a, uint8_t const *d, size_t n, bytes32 const tp[], size_t nt) noexcept override
    { if (a == g_pm) logs.push_back({std::vector<bytes32>(tp, tp + nt), std::vector<uint8_t>(d, d + n)}); }
    evmc_access_status access_account(address const &a) noexcept override { return warm.insert(a).second ? EVMC_ACCESS_COLD : EVMC_ACCESS_WARM; }
    evmc_access_status access_storage(address const &a, bytes32 const &k) noexcept override
    {
        if (a != g_pm) return EVMC_ACCESS_WARM;
        warms.insert(k);
        auto &pg = pages[pkey(k)];
        if (pg.accessed) return EVMC_ACCESS_WARM;
        pg.accessed = true; return EVMC_ACCESS_COLD;
    }
    bytes32 get_transient_storage(address const &a, bytes32 const &k) const noexcept override
    { if (a != g_pm) return {}; auto it = t.find(k); return it == t.end() ? bytes32{} : it->second; }
    void set_transient_storage(address const &a, bytes32 const &k, bytes32 const &v) noexcept override { if (a == g_pm) t[k] = v; }
    evmc_page_storage_status update_page(address const &a, bytes32 const &k, evmc_storage_status status) noexcept override
    {
        if (a != g_pm) return {false, false};
        Page ps = pages.count(pkey(k)) ? pages[pkey(k)] : Page{};
        bool changed = status != EVMC_STORAGE_ASSIGNED, first = false;
        if (!ps.dirty) { first = changed; ps.dirty = changed; }
        switch (status) {
        case EVMC_STORAGE_ADDED: case EVMC_STORAGE_DELETED_ADDED: case EVMC_STORAGE_DELETED_RESTORED: ++ps.cur; break;
        case EVMC_STORAGE_DELETED: case EVMC_STORAGE_MODIFIED_DELETED: case EVMC_STORAGE_ADDED_DELETED: --ps.cur; break;
        default: break;
        }
        bool grew = ps.cur > ps.peak; if (grew) ps.peak = ps.cur;
        if (changed) pages[pkey(k)] = ps;
        return {first, grew};
    }
    evmc::Result run_pm(int nid, evmc_message const &m);
    void replay_children(int nid);
};
static Node const &N(TxIn const *tx, int i) { return tx->nodes[(size_t)i]; }
evmc::Result Host::run_pm(int nid, evmc_message const &m0)
{
    auto const &nd = N(tx, nid);
    if (nd.oog) { forced++; fr.push_back("forced-oog"); return evmc::Result{EVMC_OUT_OF_GAS, 0, 0, nullptr, 0}; }
    size_t slot = fr.size(); fr.push_back("");
    auto sn = snap();
    bal = add(bal, nd.value);
    evmc_message m = m0;
    if (std::getenv("HX_BIG_GAS")) m.gas = 30000000;
    if (g_gas >= 0) m.gas = g_gas;
    size_t cap = 1u << 24;
    uint8_t *buf = (uint8_t *)std::aligned_alloc(64, cap);
    std::memset(buf, 0, cap);
    m.memory_handle = buf; m.memory = buf; m.memory_capacity = (uint32_t)cap;
    stack.push_back({nid, 0});
    auto ctx = runtime::Context::from(&g_iface, to_context(), &m, std::span<uint8_t const>(g_code.data(), g_code.size()));
    auto *stk = (HX_STACK_T *)std::aligned_alloc(32, 1024 * 32);
    if (mode == NATIVE) {
        if (!eng->nat) {
            eng->nat = compiler::native::compile<T>(eng->rt, g_code.data(), interpreter::code_size_t::unsafe_from((uint32_t)g_code.size()), {});
            if (!eng->nat->entrypoint()) { std::fprintf(stderr, "native compile failed\n"); std::abort(); }
            if (std::getenv("HX_COVOUT")) cov::install();
        }
        eng->nat->entrypoint()(&ctx, stk);
    }
    else {
        if (!eng->ic) eng->ic = std::make_unique<interpreter::Intercode>(g_code.data(), g_code.size());
        interpreter::execute<T>(ctx, *eng->ic, stk);
    }
    auto r = ctx.copy_to_evmc_result<T>();
    ctx.return_to<T>(nullptr);
    std::free(stk); std::free(buf);
    auto f = stack.back(); stack.pop_back();
    size_t nk = 0; for (int k : nd.kids) { auto const &c = N(tx, k); if (c.type == "CALL" || c.type == "STATICCALL" || c.type == "DELEGATECALL" || c.type == "CALLCODE") nk++; }
    if (r.status_code == EVMC_SUCCESS && f.next != nk && div.empty()) div = "fewer outgoing calls";
    if (r.status_code != EVMC_SUCCESS) restore(sn);
    std::ostringstream os;
    os << st(r.status_code) << " " << (m.gas - r.gas_left) << " " << hex(r.output_data, r.output_size);
    fr[slot] = os.str();
    return r;
}
void Host::replay_children(int nid)
{
    for (int k : N(tx, nid).kids) {
        auto const &c = N(tx, k);
        if (c.type != "CALL" && c.type != "STATICCALL" && c.type != "DELEGATECALL" && c.type != "CALLCODE" && c.type != "CREATE" && c.type != "CREATE2") continue;
        if (c.pm) {
            evmc_message m{};
            m.kind = EVMC_CALL; m.flags = c.type == "STATICCALL" ? EVMC_STATIC : 0; m.depth = 1; m.gas = c.gas;
            m.recipient = g_pm; m.code_address = g_pm; m.sender = c.from; to_be(c.value, m.value.bytes);
            m.input_data = c.in.data(); m.input_size = c.in.size();
            run_pm(k, m);
        }
        else {
            auto sn = snap();
            replay_children(k);
            if (!c.ok) restore(sn);
        }
    }
}
evmc::Result Host::call(evmc_message const &m) noexcept
{
    // an outgoing call of the PoolManager: answer it from the recorded tree
    if (stack.empty()) { div = "call with no frame"; return evmc::Result{EVMC_REVERT, 0, 0, nullptr, 0}; }
    auto &top = stack.back();
    auto const &nd = N(tx, top.node);
    std::vector<int> kids;
    for (int k : nd.kids) { auto const &c = N(tx, k); if (c.type == "CALL" || c.type == "STATICCALL" || c.type == "DELEGATECALL" || c.type == "CALLCODE") kids.push_back(k); }
    if (top.next >= kids.size()) { if (div.empty()) div = "extra outgoing call"; return evmc::Result{EVMC_REVERT, 0, 0, nullptr, 0}; }
    int k = kids[top.next++];
    auto const &c = N(tx, k);
    U256 v = from_be(m.value.bytes);
    if (c.to != m.recipient || c.in != std::vector<uint8_t>(m.input_data, m.input_data + m.input_size) || std::memcmp(&c.value, &v, sizeof v)) {
        if (div.empty()) div = "outgoing call differs at node " + std::to_string(k) + (c.to != m.recipient ? " to" : "") + (c.in != std::vector<uint8_t>(m.input_data, m.input_data + m.input_size) ? " input" : "") + (std::memcmp(&c.value, &v, sizeof v) ? " value:" + uh(v) + "/" + uh(c.value) : "");
        return evmc::Result{EVMC_REVERT, 0, 0, nullptr, 0};
    }
    auto sn = snap();
    bal = sub(bal, v);
    if (c.pm) { // the PoolManager calling itself
        auto r = run_pm(k, m);
        if (r.status_code != EVMC_SUCCESS) restore(sn);
        return r;
    }
    replay_children(k);
    if (!c.ok) restore(sn);
    int64_t left = m.gas - c.gasUsed; if (left < 0) left = 0;
    return evmc::Result{c.ok ? EVMC_SUCCESS : EVMC_REVERT, c.ok || !c.out.empty() ? left : 0, 0, c.out.data(), c.out.size()};
}
static std::string digest(Host const &h)
{
    std::ostringstream os;
    os << "div=" << (h.div.empty() ? "-" : h.div) << " forced=" << h.forced << "\n";
    for (size_t i = 0; i < h.fr.size(); i++) os << "  frame " << i << " " << h.fr[i] << "\n";
    for (auto const &[k, v] : h.s) os << "  st " << bh(k) << " " << bh(v) << "\n";
    for (auto const &[k, v] : h.t) os << "  tst " << bh(k) << " " << bh(v) << "\n";
    os << "  bal " << uh(h.bal) << "\n";
    for (auto const &l : h.logs) { os << "  log"; for (auto const &t : l.topics) os << " " << bh(t); os << " " << hex(l.data.data(), l.data.size()) << "\n"; }
    return os.str();
}
static Host run(TxIn const &tx, Mode mode, Engine &eng)
{
    Host h; h.tx = &tx; h.mode = mode; h.eng = &eng; h.s = tx.pre; h.bal = tx.bal;
    h.warm = tx.acl; h.warms = tx.acls;
    for (auto const &k : tx.acls) h.pages[Host::pkey(k)].accessed = true;
    h.warm.insert(g_pm); h.warm.insert(tx.nodes[0].from); h.warm.insert(tx.nodes[0].to);
    for (int p = 1; p <= 0x11; p++) { address a{}; a.bytes[19] = (uint8_t)p; h.warm.insert(a); }
    if (tx.nodes[0].pm) {
        auto const &c = tx.nodes[0];
        evmc_message m{}; m.kind = EVMC_CALL; m.gas = c.gas; m.recipient = std::getenv("HX_SELF") ? addr_of(std::getenv("HX_SELF")) : g_pm; m.code_address = g_pm; m.sender = c.from; to_be(c.value, m.value.bytes);
        m.input_data = c.in.data(); m.input_size = c.in.size();
        h.run_pm(0, m);
    }
    else {
        h.replay_children(0);
        if (!tx.nodes[0].ok) { h.logs.clear(); h.s = tx.pre; h.t.clear(); }
    }
    return h;
}
static std::vector<uint8_t> uv(std::string const &x) { return x == "-" ? std::vector<uint8_t>{} : unhex(x); }
static U256 u256(std::string const &x) { auto b = uv(x); uint8_t p[32]{}; std::memcpy(p + 32 - b.size(), b.data(), b.size()); return from_be(p); }
static bytes32 b32(std::string const &x) { auto b = uv(x); bytes32 r{}; std::memcpy(r.bytes + 32 - b.size(), b.data(), b.size()); return r; }
int main(int argc, char **argv)
{
    g_iface = evmc::Host::get_interface();
    g_pm = addr_of(std::getenv("HX_PM") ? std::getenv("HX_PM") : "188d586ddcf52439676ca21a244753fa19f9ea8e");
    { std::ifstream f(argv[1]); std::string c; f >> c; g_code = unhex(c); }
    std::ifstream f(argv[2]);
    std::string line; std::vector<TxIn> txs;
    while (std::getline(f, line)) {
        std::istringstream is(line); std::string k; is >> k;
        if (k == "TX") {
            txs.emplace_back(); auto &t = txs.back(); std::string ts, num, bf, cb, org, gp, rnd, gl;
            is >> t.hash >> t.status >> num >> ts >> bf >> cb >> org >> gp >> rnd >> gl;
            t.txc.chain_id.bytes[31] = 143; t.txc.block_number = std::stoll(num); t.txc.block_timestamp = std::stoll(ts);
            to_be(u256(bf), t.txc.block_base_fee.bytes); t.txc.block_coinbase = addr_of(cb); t.txc.tx_origin = addr_of(org);
            to_be(u256(gp), t.txc.tx_gas_price.bytes); t.txc.block_prev_randao = b32(rnd); t.txc.block_gas_limit = std::stoll(gl);
        }
        else if (k == "PRE") { std::string a, b; is >> a >> b; txs.back().pre[b32(a)] = b32(b); }
        else if (k == "POST") { std::string a, b; is >> a >> b; txs.back().post[b32(a)] = b32(b); txs.back().has_post = true; }
        else if (k == "BAL") { std::string a; is >> a; txs.back().bal = u256(a); }
        else if (k == "ACL") { std::string a; is >> a; txs.back().acl.insert(addr_of(a)); }
        else if (k == "ACLS") { std::string a; is >> a; txs.back().acls.insert(b32(a)); }
        else if (k == "N") {
            Node n; std::string to, fr, v, g, gu, ok, oog, in, out, pm;
            is >> n.id >> n.parent >> pm >> n.type >> to >> fr >> v >> g >> gu >> ok >> oog >> in >> out;
            n.pm = pm == "1"; n.to = addr_of(to == "-" ? "00" : to); n.from = addr_of(fr); n.value = u256(v); n.gas = (int64_t)std::stoull(g); n.gasUsed = (int64_t)std::stoull(gu);
            n.ok = ok == "1"; n.oog = oog == "1"; n.in = uv(in); n.out = uv(out);
            auto &t = txs.back(); t.nodes.push_back(n);
            if (n.parent >= 0) t.nodes[(size_t)n.parent].kids.push_back(n.id);
        }
        else if (k == "LOG") {
            std::string d; int nt; is >> nt; Log l; for (int i = 0; i < nt; i++) { std::string x; is >> x; l.topics.push_back(b32(x)); } is >> d; l.data = uv(d);
            txs.back().rlogs.push_back(l);
        }
    }
    Engine eng;
    if (std::getenv("HX_GAS")) g_gas = std::stoll(std::getenv("HX_GAS"));
    int64_t sw0 = 0, sw1 = 0, sw2 = 1;
    if (std::getenv("HX_GAS_SWEEP")) { std::sscanf(std::getenv("HX_GAS_SWEEP"), "%ld:%ld:%ld", &sw0, &sw1, &sw2); g_quiet = true; }
    size_t sweep_runs = 0, sweep_diff = 0, sweep_halt_frames = 0;
    size_t postdiff = 0; size_t mism = 0, divs = 0, logok = 0, frok = 0, gasok = 0, nfr = 0, nfrgas = 0;
    for (int64_t gv = sw0; gv <= sw1; gv += sw2) {
    if (std::getenv("HX_GAS_SWEEP")) g_gas = gv;
    for (auto const &tx : txs) {
        auto a = run(tx, INTERP, eng);
        auto b = run(tx, NATIVE, eng);
        auto da = digest(a), db = digest(b);
        bool same = da == db;
        if (!same) mism++;
        if (!a.div.empty()) divs++;
        // against the block: PoolManager frames (status and output), receipt logs, frame gas
        std::vector<int> pmn; std::function<void(int)> walk;
        bool lg = (tx.status == 1 ? tx.rlogs.size() == a.logs.size() : a.logs.empty());
        if (lg && tx.status == 1) for (size_t i = 0; i < a.logs.size(); i++) if (a.logs[i].topics != tx.rlogs[i].topics || a.logs[i].data != tx.rlogs[i].data) lg = false;
        if (lg) logok++;
        // frames in execution order are the PoolManager nodes in tree order that actually ran
        std::vector<int> order; for (auto const &n : tx.nodes) if (n.pm) order.push_back(n.id);
        bool fok = a.fr.size() <= order.size() && a.div.empty();
        size_t gmatch = 0;
        for (size_t i = 0; fok && i < a.fr.size(); i++) {
            auto const &n = N(&tx, order[i]);
            if (a.fr[i] == "forced-oog") continue;
            std::istringstream fs(a.fr[i]); std::string s, gu, out; fs >> s >> gu; std::getline(fs, out); if (!out.empty() && out[0] == ' ') out = out.substr(1);
            bool ok = s == "success";
            if (ok != n.ok || (ok && out != hex(n.out.data(), n.out.size()))) fok = false;
            nfrgas++; if (std::stoll(gu) == n.gasUsed) { gmatch++; gasok++; }
        }
        nfr += a.fr.size();
        std::string pst = "-";
        if (tx.has_post) { std::map<bytes32, bytes32> x, y; bytes32 z{}; for (auto const &[k2, v2] : a.s) if (v2 != z) x[k2] = v2; for (auto const &[k2, v2] : tx.post) if (v2 != z) y[k2] = v2; pst = x == y ? "equal" : "differ"; if (x != y) postdiff++; }
        if (!g_quiet) std::printf("POSTSTORAGE %s %s\n", tx.hash.c_str(), pst.c_str());
        if (fok) frok++;
        sweep_runs++; if (!same) sweep_diff++;
        for (auto const &x : a.fr) if (x.rfind("halt", 0) == 0) sweep_halt_frames++;
        if (g_quiet && same) continue;
        if (g_quiet) std::printf("GAS %ld ", (long)g_gas);
        std::printf("%s %s interp_vs_native=%s frames=%zu vs_block_frames=%s vs_block_logs=%s frame_gas_equal=%zu/%zu div=%s\n", same ? "SAME" : "DIFF", tx.hash.c_str(), same ? "same" : "differ", a.fr.size(), fok ? "match" : "MISMATCH", lg ? "match" : "MISMATCH", gmatch, a.fr.size(), a.div.empty() ? "-" : a.div.c_str());
        if (!same || (argc > 3)) std::printf("--- interp\n%s--- native\n%s", da.c_str(), db.c_str());
        std::fflush(stdout);
    }
    }
    if (std::getenv("HX_GAS_SWEEP")) std::printf("sweep runs=%zu interp_native_differ=%zu halted_frames=%zu\n", sweep_runs, sweep_diff, sweep_halt_frames);
    cov::dump();
    std::printf("post_storage_differs=%zu\n", postdiff);
    std::printf("txs=%zu mismatches=%zu divergences=%zu frames_match=%zu logs_match=%zu frames=%zu frame_gas_equal=%zu/%zu\n", txs.size(), mism, divs, frok, logok, nfr, gasok, nfrgas);
}
