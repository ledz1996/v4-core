"""Cycle 24 copy of cycles/021/theme-arc-running-code.work/lazyreplay.py (theme-replay-eleven, L-1014, L-1044). Changes:
(0) the code cache is used only for blocks at or after the block a code was read at (cycle 21 reused it for
earlier blocks too, which makes an account created later look already deployed); (a) the interpreter is pyevm_tx24.py (pyevm_tx17 plus CREATE and CREATE2 decoding); (b) World.create below: address from
RLP(sender, nonce) or 0xff||sender||salt||keccak(initcode), sender nonce raised, collision when the target has code or a
nonce, new account nonce 1, initcode run with empty calldata, code size limit 24576 and the 0xEF first-byte rule, return
data empty on success; on Arc a value-carrying CREATE gets the same EIP-7708 log and zero-address and blocklist checks as
a CALL (crates/evm/src/evm.rs v0.8.6 lines 462-512, 516-605, 828-888); (c) NativeCoinAuthority.mint(address,uint256)
from crates/precompiles/src/native_coin_authority.rs v0.8.6 lines 103-191: caller must be the USDC contract 0x3600..00,
no static call, to != 0, to not blocklisted, amount != 0, total supply at slot 2 of 0x1800..00 raised with overflow check,
balance of to raised, Transfer(0, to, amount) logged by 0xff..fe; (d) the P256VERIFY precompile at 0x100 (RIP-7212 and
EIP-7951: 160 byte input hash,r,s,x,y; 32 byte 1 on a valid signature, empty output otherwise), written from SEC 1 4.1.4
with the NIST P-256 parameters; (e) ARC flag: the Arc-only parts can be switched off for an OP Stack chain; (f) CELO flag: the Celo transfer
precompile at 0xfd (celo-kona crates/celo-revm/src/precompiles/transfer.rs); for a fee currency transaction (type 0x7b) the native
balance is not charged and debitGasFees(from, gas * price) is run on the fee currency from address 0 before the call.

Rerun a mined Arc transaction whole in the cycle 17 reference interpreter (cycles/017/theme-reference-interpreter-audit.work/
pyevm_tx17.py, read and imported, not changed), with state read lazily from the parent block through eth_getStorageAt,
eth_getCode, eth_getBalance and eth_getTransactionCount (Arc endpoints serve no traces). Every key the run touches is
fetched in batches and the run is repeated until no key is missing. Arc additions in the model, from
crates/evm/src/evm.rs of arc-node v0.8.6 (lines 515-605 and 798-895): an EIP-7708 Transfer log from the system emitter
0xff..fe for every CALL frame (or the top frame) that carries nonzero value between two distinct addresses, emitted at
frame start and removed when the frame fails; a value frame from or to address(0) fails. Blocklist reads are not
modelled (no mined transaction in the sample names a listed account; a mismatch would show it). Calls into the Arc
precompile range 0x1800..00-0x1800..ff and into node contracts raise and set the transaction aside.
Compared with the chain: status, every receipt log in order (contract logs and system emitter logs), the post-block
value of every PoolManager storage slot the run read or wrote, the PoolManager native balance change, and the native
balance change of each recipient of a PoolManager payout, when no other transaction of the block touches that account."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); NR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff')); sys.path.insert(0, HERE)
import pyevm_tx24 as P
from rpc import batch
I = lambda x: int(x, 16) if isinstance(x, str) else int(x or 0)
EM = (1 << 160) - 2; T = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
PM = 0x8366a39cc670b4001a1121b8f6a443a643e40951

class Missing(Exception): pass
NCA = 0x18 << 152; NCC = NCA + 1; USDC = 0x36 << 152
SEL_ISBL = P.keccak(b'isBlocklisted(address)')[:4]
def blslot(a): return int.from_bytes(P.keccak(a.to_bytes(32, 'big') + (2).to_bytes(32, 'big')), 'big')
SEL_NCA_TRANSFER = P.keccak(b'transfer(address,address,uint256)')[:4]
SEL_MINT = P.keccak(b'mint(address,uint256)')[:4]
ARC = True
CELO = False; CELO_TOKEN = 0x471ece3750da237f93b8e339c536989b8978a438
# NIST P-256 (SEC 2 section 2.4.2, FIPS 186-4 D.1.2.3)
_PP = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff; _PA = _PP - 3
_PB = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
_PN = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
_PG = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296, 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
def _padd(p, q):
    if p is None: return q
    if q is None: return p
    if p[0] == q[0] and (p[1] + q[1]) % _PP == 0: return None
    if p == q: l = (3 * p[0] * p[0] + _PA) * pow(2 * p[1], -1, _PP) % _PP
    else: l = (q[1] - p[1]) * pow(q[0] - p[0], -1, _PP) % _PP
    x = (l * l - p[0] - q[0]) % _PP; return (x, (l * (p[0] - x) - p[1]) % _PP)
def _pmul(k, p):
    r = None
    while k:
        if k & 1: r = _padd(r, p)
        p = _padd(p, p); k >>= 1
    return r
def p256verify(d):
    if len(d) != 160: return b''
    h, r, s, x, y = (int.from_bytes(d[i:i + 32], 'big') for i in range(0, 160, 32))
    if not (0 < r < _PN and 0 < s < _PN) or x >= _PP or y >= _PP: return b''
    if (x, y) == (0, 0) or (y * y - x * x * x - _PA * x - _PB) % _PP: return b''
    w = pow(s, -1, _PN); R = _padd(_pmul(h * w % _PN, _PG), _pmul(r * w % _PN, (x, y)))
    if R is None or R[0] % _PN != r: return b''
    return (1).to_bytes(32, 'big')

CODE_CACHE = {}  # contract code (longer than an EIP-7702 designator) does not change between blocks, so it is shared across transactions
class Base:
    def __init__(self, url, block):
        self.url = url; self.block = hex(block); self.c = {}; self.miss = set(); self.w = None
    def get(self, kind, a, k=None):
        key = (kind, a, k)
        if key in self.c: return self.c[key]
        if kind == 'code' and a in CODE_CACHE and CODE_CACHE[a][1] <= int(self.block, 16): self.c[key] = CODE_CACHE[a][0]; return CODE_CACHE[a][0]
        if not self.miss and self.w is not None: self.w.max_steps = min(self.w.max_steps or 1 << 60, self.w.steps + 30000)
        self.miss.add(key)
        return b'' if kind == 'code' else 0
    def fetch(self):
        keys = sorted(self.miss, key=str); self.miss = set()
        reqs = []
        for kind, a, k in keys:
            A = '0x%040x' % a
            if kind == 'code': reqs.append(('eth_getCode', [A, self.block]))
            elif kind == 'bal': reqs.append(('eth_getBalance', [A, self.block]))
            elif kind == 'nonce': reqs.append(('eth_getTransactionCount', [A, self.block]))
            else: reqs.append(('eth_getStorageAt', [A, hex(k), self.block]))
        for i in range(0, len(reqs), 10):
            r = batch(self.url, reqs[i:i + 10])
            for key, v in zip(keys[i:i + 10], r):
                self.c[key] = bytes.fromhex(v[2:]) if key[0] == 'code' else int(v, 16)
                if key[0] == 'code' and len(self.c[key]) > 23: CODE_CACHE[key[1]] = (self.c[key], int(self.block, 16))  # cycle 24: reused only for blocks at or after the block it was read at, since a later-created account has no code earlier
        return len(keys)

class LStore(dict):
    def __init__(self, base, kind, init=()):
        super().__init__(init); self.base = base; self.kind = kind; self.read = set()
    def _b(self, key):
        if self.kind == 'st': return self.base.get('st', key[0], key[1])
        return self.base.get(self.kind, key)
    def get(self, key, default=None):
        if dict.__contains__(self, key): return dict.__getitem__(self, key)
        self.read.add(key)
        v = self._b(key)
        if self.kind == 'code' and v == b'': return default
        return v
    def __getitem__(self, key): 
        v = self.get(key)
        if v is None: raise KeyError(key)
        return v
    def __contains__(self, key): return self.get(key) is not None if self.kind == 'code' else True

class W(P.World):
    def __init__(self, base):
        super().__init__({}, {})
        self.base = base
        self.codes = LStore(base, 'code'); self.balances = LStore(base, 'bal'); self.storage = LStore(base, 'st')
        self.reads = set(); self.vlogs = []
    def listed(self, a): return self.base.get('st', NCC, blslot(a)) != 0
    nonce_over = None; created = None
    def nonce(self, a):
        if self.nonce_over is None: self.nonce_over = {}; self.created = []
        return self.nonce_over[a] if a in self.nonce_over else self.ctx['nonces'].get(a)
    def snapshot(self):
        if self.nonce_over is None: self.nonce_over = {}; self.created = []
        return (dict(self.storage), dict(self.transient), dict(self.balances), len(self.logs), dict(self.nonce_over), len(self.created))
    def create(self, caller, value, init, salt, depth):
        if self.nonce_over is None: self.nonce_over = {}; self.created = []
        self.creates = getattr(self, 'creates', 0) + 1
        if self.balances.get(caller, 0) < value: return False, b'', 0
        n = self.nonce(caller)
        if n >= (1 << 64) - 1: return False, b'', 0
        self.nonce_over[caller] = n + 1
        if salt is None: adr = int.from_bytes(P.keccak(rlp([caller.to_bytes(20, 'big'), n]))[12:], 'big')
        else: adr = int.from_bytes(P.keccak(b'\xff' + caller.to_bytes(20, 'big') + salt.to_bytes(32, 'big') + P.keccak(init))[12:], 'big')
        if (self.codes.get(adr) or b'') or self.nonce(adr) != 0: self.collisions = getattr(self, 'collisions', 0) + 1; return False, b'', 0
        snap = self.snapshot()
        if ARC and value:
            if caller == 0 or self.listed(caller) or self.listed(adr): return False, b'', 0
        self.nonce_over[adr] = 1
        if value:
            self.balances[caller] = self.balances.get(caller, 0) - value; self.balances[adr] = self.balances.get(adr, 0) + value
            if ARC and caller != adr: self.logs.append((EM, (T, caller, adr), value.to_bytes(32, 'big')))
        self.codes[adr] = init; self.jd[adr] = P.jumpdests(init); self.created.append(adr)
        if adr in self.watch: self.frames.append([depth, adr, 'create', None])
        try:
            ok, ret = self.run(adr, adr, caller, value, b'', False, depth)
        except P.Halt:
            ok, ret = False, b''
        if ok and (len(ret) > 24576 or (ret and ret[0] == 0xef)): ok, ret = False, b''
        if ok:
            self.codes[adr] = ret; self.jd[adr] = P.jumpdests(ret); CODE_CACHE.pop(adr, None); return True, b'', adr
        self.restore(snap); return False, ret, 0
    def restore(self, snap):
        if len(snap) > 4:
            self.nonce_over = snap[4]
            for a in self.created[snap[5]:]:
                dict.__setitem__(self.codes, a, b''); self.jd.pop(a, None)
            del self.created[snap[5]:]
        r1, r2 = self.storage.read, self.balances.read
        self.storage = LStore(self.base, 'st', snap[0]); self.storage.read = r1
        self.balances = LStore(self.base, 'bal', snap[2]); self.balances.read = r2
        self.transient = snap[1]; del self.logs[snap[3]:]
    def _call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
        ca = to if code_addr is None else code_addr
        if ARC and ca == NCA and storage_addr is None and bytes(data[:4]) == SEL_NCA_TRANSFER and len(data) == 100 and not value:
            # NativeCoinAuthority.transfer(from, to, amount), crates/precompiles/src/native_coin_authority.rs:286-345 (v0.8.6)
            if caller != USDC or static: return False, b'nca refused'
            f = int.from_bytes(data[4:36], 'big'); t = int.from_bytes(data[36:68], 'big'); amt = int.from_bytes(data[68:100], 'big')
            if f >> 160 or t >> 160: return False, b'nca bad address'
            if f == 0 or t == 0: return False, b'nca zero'
            if self.listed(f) or self.listed(t): return False, b'nca blocklisted'
            self.ncaCalls = getattr(self, 'ncaCalls', 0) + 1
            if amt:
                if self.balances.get(f, 0) < amt: return False, b'nca insufficient'
                self.balances[f] = self.balances.get(f, 0) - amt; self.balances[t] = self.balances.get(t, 0) + amt
                if f != t: self.logs.append((EM, (T, f, t), amt.to_bytes(32, 'big')))
            return True, (1).to_bytes(32, 'big')
        if ARC and ca == NCC and storage_addr is None and bytes(data[:4]) == SEL_ISBL and len(data) == 36 and not value:
            self.ncaCalls = getattr(self, 'ncaCalls', 0) + 1
            return True, int(self.listed(int.from_bytes(data[4:36], 'big') & ((1 << 160) - 1))).to_bytes(32, 'big')
        if ARC and ca == NCA and storage_addr is None and bytes(data[:4]) == SEL_MINT and not value:
            if caller != USDC or static or len(data) < 68: return False, b'nca mint refused'
            t = int.from_bytes(data[4:36], 'big'); amt = int.from_bytes(data[36:68], 'big')
            if t >> 160: return False, b'nca bad address'
            if t == 0 or self.listed(t) or amt == 0: return False, b'nca mint refused'
            ts = self.storage.get((NCA, 2), 0)
            if ts + amt >> 256: return False, b'overflow'
            self.storage[(NCA, 2)] = ts + amt; self.balances[t] = self.balances.get(t, 0) + amt
            self.logs.append((EM, (T, 0, t), amt.to_bytes(32, 'big'))); self.ncaCalls = getattr(self, 'ncaCalls', 0) + 1; self.mints = getattr(self, 'mints', 0) + 1
            return True, (1).to_bytes(32, 'big')
        if CELO and ca == 0xfd and storage_addr is None:
            # Celo transfer precompile, celo-kona crates/celo-revm/src/precompiles/transfer.rs (HEAD, read in cycle 24): no static call,
            # caller must be the CELO token, 96 byte input (from, to, value), journal transfer, empty output; any failure halts the frame
            self.celoTransfers = getattr(self, 'celoTransfers', 0) + 1
            if static or caller != CELO_TOKEN or len(data) != 96 or value: return False, b''
            f = int.from_bytes(data[12:32], 'big'); t = int.from_bytes(data[44:64], 'big'); v = int.from_bytes(data[64:96], 'big')
            if self.balances.get(f, 0) < v: return False, b''
            if v and f != t: self.balances[f] = self.balances.get(f, 0) - v; self.balances[t] = self.balances.get(t, 0) + v
            return True, b''
        if ca == 0x100 and not (self.codes.get(0x100) or b''):
            self.p256 = getattr(self, 'p256', 0) + 1
            return True, p256verify(bytes(data))
        if ARC and (ca >> 8) == (0x18 << 152) >> 8: raise NotImplementedError('arc precompile %#x %s' % (ca, bytes(data[:4]).hex()))
        if ARC and value and storage_addr is None:
            if caller == 0 or to == 0: return False, b'arc zero address'
            if self.listed(caller) or self.listed(to): self.blockedFrames = getattr(self, 'blockedFrames', 0) + 1; return False, b'arc blocklisted'
            if self.balances.get(caller, 0) < value: return False, b''
            snap = self.snapshot()
            if caller != to: self.logs.append((EM, (T, caller, to), value.to_bytes(32, 'big')))
            ok, ret = super()._call(caller, to, value, data, static, depth, code_addr, storage_addr)
            if not ok: self.restore(snap)
            return ok, ret
        return super()._call(caller, to, value, data, static, depth, code_addr, storage_addr)

def _rb(b):
    if len(b) == 1 and b[0] < 0x80: return b
    return (bytes([0x80 + len(b)]) if len(b) < 56 else bytes([0xb7 + len(len(b).to_bytes(8, 'big').lstrip(b'\0'))]) + len(b).to_bytes(8, 'big').lstrip(b'\0')) + b
def rlp(items):
    enc = b''.join(_rb(x if isinstance(x, bytes) else (x.to_bytes((x.bit_length() + 7) // 8, 'big') if x else b'')) for x in items)
    return (bytes([0xc0 + len(enc)]) if len(enc) < 56 else bytes([0xf7 + len(len(enc).to_bytes(8, 'big').lstrip(b'\0'))]) + len(enc).to_bytes(8, 'big').lstrip(b'\0')) + enc

CID = 5042
MAX_STEPS = 40_000_000
MAX_ROUNDS = 60  # fetch rounds of one replay (cycle 21 value); steplimit.py raises it
def run_once(base, tx, rec, blk, cid=None, pre=None):
    cid = cid or CID
    w = W(base); base.w = w
    pre = pre or {'st': {}, 'bal': {}, 'code': {}, 'nonce': {}}
    w.storage.update(pre['st']); w.balances.update(pre['bal']); w.codes.update(pre['code'])
    class N(dict):
        def get(s, a, d=0): return pre['nonce'].get(a, base.get('nonce', a))
    w.ctx = {'origin': int(tx['from'], 16), 'gasprice': I(rec.get('effectiveGasPrice') or tx.get('gasPrice')), 'coinbase': int(blk['miner'], 16),
             'timestamp': I(blk['timestamp']), 'number': I(blk['number']), 'prevrandao': int(blk.get('mixHash') or '0x0', 16),
             'gaslimit': I(blk['gasLimit']), 'chainid': cid, 'basefee': I(blk.get('baseFeePerGas') or '0x0'), 'nonces': N(), 'gas': I(tx['gas']), 'osaka': True}
    w.watch = {PM}; w.max_steps = MAX_STEPS
    frm = int(tx['from'], 16)
    # the sender pays gas before execution; the reference only needs a balance that covers the value
    fc = tx.get('feeCurrency') if CELO and tx.get('type') == '0x7b' else None
    if fc:
        # Celo CIP-64: the fee is taken in the fee currency by a system call debitGasFees(from, amount) from address 0 before
        # execution, and the native balance is not charged (cycle 22 reading of celo-kona). Run that call in the reference.
        amt = I(tx['gas']) * I(rec.get('effectiveGasPrice') or tx.get('maxFeePerGas') or tx.get('gasPrice'))
        okf, _ = w.call(0, int(fc, 16), 0, P.keccak(b'debitGasFees(address,uint256)')[:4] + frm.to_bytes(32, 'big') + amt.to_bytes(32, 'big'), False, 0)
        w.feeDebit = okf
    else:
        w.balances[frm] = w.balances.get(frm, 0) - I(tx['gas']) * I(rec.get('effectiveGasPrice') or tx.get('gasPrice'))
    # EIP-7702 authorizations of a type 4 transaction set code before execution
    for au in tx.get('authorizationList') or []:
        cidA, adr, non = I(au['chainId']), int(au['address'], 16), I(au['nonce'])
        msg = b'\x05' + rlp([cidA, adr.to_bytes(20, 'big'), non])
        auth = P.ecrecover(P.keccak(msg) + (I(au['yParity']) + 27).to_bytes(32, 'big') + I(au['r']).to_bytes(32, 'big') + I(au['s']).to_bytes(32, 'big'))
        if not auth or cidA not in (0, cid): continue
        a = int.from_bytes(auth, 'big')
        if w.ctx['nonces'].get(a) + (1 if a == frm else 0) != non: continue  # the sender's nonce is raised before authorizations are applied
        pre['nonce'][a] = w.ctx['nonces'].get(a) + 1 + (1 if a == frm else 0) - (1 if a == frm else 0)
        w.codes[a] = (b'\xef\x01\x00' + adr.to_bytes(20, 'big')) if adr else b''
        w.authApplied = getattr(w, 'authApplied', 0) + 1
    to = int(tx['to'], 16)
    ok, ret = w.call(frm, to, I(tx['value']), bytes.fromhex(tx['input'][2:]), False, 0)
    return w, ok, ret

def replay(url, tx, rec, blk):
    base = Base(url, I(tx['blockNumber']) - 1)
    rounds = 0
    while True:
        rounds += 1
        try:
            w, ok, ret = run_once(base, tx, rec, blk)
            err = None
        except (NotImplementedError, TimeoutError) as e:
            w, ok, ret, err = None, None, None, str(e)[:200]
        if base.miss and rounds < MAX_ROUNDS:
            base.fetch(); continue
        break
    return base, w, ok, ret, err, rounds


def replay_prefix(url, txs, blk):
    """txs: list of (tx, rec) in block order; the last is the one compared. Earlier ones are run on the same state first."""
    base = Base(url, I(txs[-1][0]['blockNumber']) - 1)
    rounds = 0
    while True:
        rounds += 1; pre = {'st': {}, 'bal': {}, 'code': {}, 'nonce': {}}; notes = []; err = None; w = ok = ret = None
        for k, (tx, rec) in enumerate(txs):
            try:
                w, ok, ret = run_once(base, tx, rec, blk, pre=pre)
            except (NotImplementedError, TimeoutError) as e:
                if k == len(txs) - 1: err = 'tx %d: %s' % (k, str(e)[:160]); w = None; break
                notes.append([k, tx['hash'], 'skipped, not modelled: ' + str(e)[:100]]); continue
            frm = int(tx['from'], 16)
            if k < len(txs) - 1:
                if bool(ok) != bool(I(rec['status'])): notes.append([k, tx['hash'], 'status differs', int(ok)])
                if ok:
                    pre['st'] = dict(w.storage); pre['code'] = {a: c for a, c in dict(w.codes).items()}
                    pre['bal'] = dict(w.balances)
                # gas actually paid (the run debited the limit)
                pre['bal'][frm] = w.balances.get(frm, 0) + (I(tx['gas']) - I(rec['gasUsed'])) * I(rec.get('effectiveGasPrice') or tx.get('gasPrice'))
                pre['nonce'][frm] = w.ctx['nonces'].get(frm) + 1
        if base.miss and rounds < max(80, MAX_ROUNDS):
            base.fetch(); continue
        break
    return base, w, ok, ret, err, rounds, notes
