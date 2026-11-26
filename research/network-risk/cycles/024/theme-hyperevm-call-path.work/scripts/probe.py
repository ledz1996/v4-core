#!/usr/bin/env python3
"""Task 1 (L-1031): non-arithmetic probe set, read-only eth_call / eth_estimateGas.
Usage: probe.py <label> <url> <out.json>
Every batch is bracketed with web3_clientVersion and eth_blockNumber.
No transactions are sent. Deterministic inputs, no random seed used.
"""
import json, sys, time, urllib.request

PROBE = "0x00000000000000000000000000000000c0de0001"
FROM = "0x00000000000000000000000000000000000a11ce"

def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json", "user-agent": "rpc-probe/1.0"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            code = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")[:500]; code = e.code
    except Exception as e:
        return {"transport_error": repr(e)}
    try:
        j = json.loads(raw)
    except Exception:
        return {"http": code, "raw": raw[:500]}
    j.pop("jsonrpc", None); j.pop("id", None)
    j["http"] = code; j["ms"] = int((time.time() - t) * 1000)
    return j

def h(b): return "0x" + b.hex()
def w(n): return n.to_bytes(32, "big")

# --- bytecode pieces (hand assembled, opcodes per the yellow paper) ---
STACK_UNDERFLOW = bytes([0x01])                     # ADD with empty stack
INVALID_JUMP = bytes([0x60, 0x05, 0x56, 0x00, 0x00, 0x00])   # PUSH1 5 JUMP -> not a JUMPDEST
JUMP_INTO_PUSH = bytes([0x60, 0x03, 0x56, 0x61, 0x5b, 0x5b, 0x00])  # target 3 is PUSH2 opcode; 4 is 0x5b inside push data
JUMP_INTO_PUSHDATA = bytes([0x60, 0x04, 0x56, 0x61, 0x5b, 0x5b, 0x00])
INFINITE_LOOP = bytes([0x5b, 0x60, 0x00, 0x56])     # JUMPDEST PUSH1 0 JUMP
INVALID_OP = bytes([0xfe])
REVERT_DATA = bytes([0x63, 0xde, 0xad, 0xbe, 0xef, 0x60, 0x00, 0x52, 0x60, 0x04, 0x60, 0x1c, 0xfd])  # revert 0xdeadbeef
UNDEFINED_OP = bytes([0x0c])                         # undefined opcode
TLOAD_UNDERFLOW = bytes([0x5c])
# GAS after cold SLOAD, warm SLOAD, CALL to an empty cold account, BALANCE of cold empty account
EMPTY = bytes.fromhex("000000000000000000000000000000000000dead01"[:40])
GAS_PROBE = (bytes([0x5a,                     # GAS g0
                    0x60, 0x00, 0x54, 0x50,   # SLOAD(0) POP (cold)
                    0x5a,                     # GAS g1
                    0x60, 0x00, 0x54, 0x50,   # SLOAD(0) POP (warm)
                    0x5a,                     # GAS g2
                    0x60, 0x00, 0x60, 0x00, 0x60, 0x00, 0x60, 0x00, 0x60, 0x00,
                    0x73]) + bytes.fromhex("00000000000000000000000000000000dead0001") +
             bytes([0x5a, 0xf1, 0x50,          # GAS CALL POP
                    0x5a,                      # GAS g3
                    0x73]) + bytes.fromhex("00000000000000000000000000000000dead0002") +
             bytes([0x31, 0x50,                # BALANCE POP (cold)
                    0x5a,                      # GAS g4
                    0x60, 0x80, 0x52, 0x60, 0x60, 0x52, 0x60, 0x40, 0x52, 0x60, 0x20, 0x52, 0x60, 0x00, 0x52,
                    0x60, 0xa0, 0x60, 0x00, 0xf3]))
# generic CALL forwarder: calldata = addr(32) | gas(32) | input
FWD = bytes([0x36, 0x60, 0x40, 0x90, 0x03,       # len = cds - 64
             0x80, 0x60, 0x40, 0x60, 0x00, 0x37,  # CALLDATACOPY(0, 64, len)
             0x5a,                                # gB
             0x60, 0x00, 0x60, 0x00, 0x83, 0x60, 0x00, 0x60, 0x00,
             0x60, 0x00, 0x35, 0x60, 0x20, 0x35, 0xf1,  # CALL
             0x5a,                                # gA
             0x90, 0x60, 0x00, 0x52,              # mem0 = success
             0x90, 0x03, 0x60, 0x20, 0x52,        # mem32 = gB - gA
             0x50,
             0x3d, 0x60, 0x40, 0x52,              # mem64 = returndatasize
             0x3d, 0x60, 0x00, 0x60, 0x60, 0x3e,  # RETURNDATACOPY(0x60, 0, rds)
             0x3d, 0x60, 0x60, 0x01, 0x60, 0x00, 0xf3])
# block environment as seen inside eth_call
ENV = bytes([0x43, 0x42, 0x41, 0x48, 0x45, 0x46, 0x44, 0x4a, 0x3a, 0x47,
             0x60, 0x01, 0x43, 0x03, 0x40,       # BLOCKHASH(NUMBER-1)
             0x5a])                              # GAS
ENV_NAMES = ["gasleft", "blockhash_prev", "selfbalance", "gasprice", "blobbasefee", "prevrandao", "chainid", "gaslimit", "basefee", "coinbase", "timestamp", "number"]
# store 12 words: top of stack first at offset 0
for i in range(12):
    ENV += bytes([0x61]) + (i * 32).to_bytes(2, "big") + bytes([0x52])
ENV += bytes([0x61, 0x01, 0x80, 0x60, 0x00, 0xf3])
# non-monotonic: revert iff GAS at entry == V (V passed in calldata word 0)
GAS_EQ = bytes([0x5a, 0x60, 0x00, 0x35, 0x14, 0x60, 0x0a, 0x57, 0x00, 0x00, 0x5b, 0x60, 0x00, 0x60, 0x00, 0xfd])
# revert iff GAS at entry < V : monotonic reference
GAS_LT = bytes([0x60, 0x00, 0x35, 0x5a, 0x10, 0x60, 0x0a, 0x57, 0x00, 0x00, 0x5b, 0x60, 0x00, 0x60, 0x00, 0xfd])

def call(code, data=b"", gas=None, block="latest", extra_override=None, frm=FROM):
    tx = {"from": frm, "to": PROBE, "data": h(data)}
    if gas is not None: tx["gas"] = hex(gas)
    ov = {PROBE: {"code": h(code)}}
    if extra_override: ov.update(extra_override)
    return tx, ov, block

def probes(chain):
    P = []
    def add(name, method, params):
        P.append((name, method, params))
    def ec(name, code, data=b"", gas=None, block="latest", ov=None):
        tx, o, b = call(code, data, gas, block, ov)
        add(name, "eth_call", [tx, b, o])
    ec("stack_underflow", STACK_UNDERFLOW, gas=100000)
    ec("invalid_jump", INVALID_JUMP, gas=100000)
    ec("jump_into_push_opcode", JUMP_INTO_PUSH, gas=100000)
    ec("jump_into_pushdata", JUMP_INTO_PUSHDATA, gas=100000)
    ec("out_of_gas_loop", INFINITE_LOOP, gas=100000)
    ec("invalid_fe", INVALID_OP, gas=100000)
    ec("undefined_0c", UNDEFINED_OP, gas=100000)
    ec("tload_underflow", TLOAD_UNDERFLOW, gas=100000)
    ec("revert_data", REVERT_DATA, gas=100000)
    ec("gas_probe", GAS_PROBE, gas=1000000)
    ec("env", ENV, gas=1000000)
    ec("env_nogas", ENV)
    def pc(name, addr, g, inp):
        ec(name, FWD, w(addr) + w(g) + inp, gas=2000000)
    # ecrecover with v = 29
    pc("ecrecover_bad_v", 1, 100000, b"\x11" * 32 + w(29) + b"\x22" * 32 + b"\x33" * 32)
    pc("ecrecover_short", 1, 100000, b"\x11" * 32)
    # modexp: baseLen 1, expLen 2^64, modLen 1
    pc("modexp_huge_explen", 5, 100000, w(1) + w(2**64) + w(1) + b"\x02" + b"\x03" * 8 + b"\x05")
    # modexp: baseLen 2^255
    pc("modexp_huge_baselen", 5, 100000, w(2**255) + w(1) + w(1))
    # modexp with modLen 1025 (EIP-7823 bound) zero data
    pc("modexp_len_1025", 5, 1000000, w(1) + w(1) + w(1025) + b"\x02\x03")
    # point evaluation with a well formed length and a bad proof
    pc("point_eval_bad", 10, 100000, b"\x01" + b"\x00" * 31 + b"\x00" * 32 + b"\x00" * 32 + b"\xc0" + b"\x00" * 47 + b"\xc0" + b"\x00" * 47)
    pc("point_eval_short", 10, 100000, b"\x00" * 100)
    pc("bls_g1add_0b", 11, 100000, b"\x00" * 256)
    pc("p256_0x100", 0x100, 100000, b"\x00" * 160)
    pc("blake2f_bad", 9, 100000, b"\x00" * 212)
    # HyperEVM read precompile: oracle px of perp 0, and invalid index
    pc("l1read_807_idx0", 0x807, 100000, w(0))
    pc("l1read_807_idx_bad", 0x807, 100000, w(2**32 - 1))
    # estimateGas: non-monotonic (revert iff entry gas == V) and monotonic reference
    for V in (21000 + 50000, 29000):
        add("estimate_gas_eq_%d" % V, "eth_estimateGas", [{"from": FROM, "to": PROBE, "data": h(w(V))}, "latest", {PROBE: {"code": h(GAS_EQ)}}])
    add("estimate_gas_lt_50000", "eth_estimateGas", [{"from": FROM, "to": PROBE, "data": h(w(50000))}, "latest", {PROBE: {"code": h(GAS_LT)}}])
    add("estimate_gas_revert_data", "eth_estimateGas", [{"from": FROM, "to": PROBE}, "latest", {PROBE: {"code": h(REVERT_DATA)}}])
    # eth_call at an exact gas: the GAS_EQ code reverts only when entry gas == V
    # (intrinsic 21000 + calldata; entry gas is gas - intrinsic)
    # state override: state vs stateDiff against the local PoolManager
    pm = chain["pm"]
    owner_sel = "0x8da5cb5b"
    add("pm_owner_plain", "eth_call", [{"from": FROM, "to": pm, "data": owner_sel}, "latest"])
    add("pm_owner_state_slot1", "eth_call", [{"from": FROM, "to": pm, "data": owner_sel}, "latest", {pm: {"state": {"0x" + "00" * 31 + "01": "0x" + "00" * 31 + "07"}}}])
    add("pm_owner_statediff_slot1", "eth_call", [{"from": FROM, "to": pm, "data": owner_sel}, "latest", {pm: {"stateDiff": {"0x" + "00" * 31 + "01": "0x" + "00" * 31 + "07"}}}])
    add("pm_owner_both", "eth_call", [{"from": FROM, "to": pm, "data": owner_sel}, "latest", {pm: {"state": {"0x" + "00" * 32: "0x" + "00" * 31 + "09"}, "stateDiff": {"0x" + "00" * 32: "0x" + "00" * 31 + "08"}}}])
    # extsload(0) via state override, reads slot 0 directly (selector of extsload(bytes32) = 0x1e2eaeaf)
    add("pm_extsload0_statediff", "eth_call", [{"from": FROM, "to": pm, "data": "0x1e2eaeaf" + "00" * 32}, "latest", {pm: {"stateDiff": {"0x" + "00" * 32: "0x" + "00" * 31 + "08"}}}])
    # block argument forms
    add("block_number_now", "eth_blockNumber", [])
    return P

def main():
    label, url, out = sys.argv[1], sys.argv[2], sys.argv[3]
    pm = sys.argv[4] if len(sys.argv) > 4 else "0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F"
    res = {"label": label, "url": url, "pm": pm, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    res["clientVersion_before"] = rpc(url, "web3_clientVersion", [])
    bn = rpc(url, "eth_blockNumber", [])
    res["blockNumber_before"] = bn
    out_rows = []
    for name, m, p in probes({"pm": pm}):
        r = rpc(url, m, p)
        out_rows.append({"name": name, "method": m, "params": p, "response": r})
        time.sleep(float(__import__("os").environ.get("PROBE_SLEEP","0.25")))
    # block-hash and old-block eth_call forms, using the block before 'before'
    try:
        n = int(bn["result"], 16)
        blk = rpc(url, "eth_getBlockByNumber", [hex(n - 5), False])
        bh = blk["result"]["hash"]
        tx, o, _ = call(ENV, gas=1000000)
        for name, b in (("env_at_blockhash", {"blockHash": bh}), ("env_at_number_minus5", hex(n - 5)), ("env_at_number_minus100000", hex(n - 100000)), ("env_at_pending", "pending"), ("env_at_bad_hash", {"blockHash": "0x" + "ab" * 32})):
            r = rpc(url, "eth_call", [tx, b, o])
            out_rows.append({"name": name, "method": "eth_call", "params": [tx, b, o], "response": r, "refBlock": n - 5, "refHash": bh})
    except Exception as e:
        out_rows.append({"name": "blockhash_forms", "error": repr(e)})
    res["rows"] = out_rows
    res["blockNumber_after"] = rpc(url, "eth_blockNumber", [])
    res["clientVersion_after"] = rpc(url, "web3_clientVersion", [])
    json.dump(res, open(out, "w"), indent=1)

if __name__ == "__main__":
    main()
