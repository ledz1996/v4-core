"""Rerun a mined Arc transaction whole in the cycle 17 reference interpreter (cycles/017/theme-reference-interpreter-audit.work/
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
HERE = os.path.dirname(os.path.abspath(__file__)); NR = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff')); sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(NR, 'cycles', '017', 'theme-reference-interpreter-audit.work'))
import pyevm_tx17 as P
from rpc import batch
I = lambda x: int(x, 16) if isinstance(x, str) else int(x or 0)
EM = (1 << 160) - 2; T = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
PM = 0x8366a39cc670b4001a1121b8f6a443a643e40951

class Missing(Exception): pass
NCA = 0x18 << 152; NCC = NCA + 1; USDC = 0x36 << 152
SEL_ISBL = P.keccak(b'isBlocklisted(address)')[:4]
def blslot(a): return int.from_bytes(P.keccak(a.to_bytes(32, 'big') + (2).to_bytes(32, 'big')), 'big')
SEL_NCA_TRANSFER = P.keccak(b'transfer(address,address,uint256)')[:4]

CODE_CACHE = {}  # contract code (longer than an EIP-7702 designator) does not change between blocks, so it is shared across transactions
class Base:
    def __init__(self, url, block):
        self.url = url; self.block = hex(block); self.c = {}; self.miss = set(); self.w = None
    def get(self, kind, a, k=None):
        key = (kind, a, k)
        if key in self.c: return self.c[key]
        if kind == 'code' and a in CODE_CACHE: self.c[key] = CODE_CACHE[a]; return CODE_CACHE[a]
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
                if key[0] == 'code' and len(self.c[key]) > 23: CODE_CACHE[key[1]] = self.c[key]
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
    def snapshot(self): return (dict(self.storage), dict(self.transient), dict(self.balances), len(self.logs))
    def restore(self, snap):
        r1, r2 = self.storage.read, self.balances.read
        self.storage = LStore(self.base, 'st', snap[0]); self.storage.read = r1
        self.balances = LStore(self.base, 'bal', snap[2]); self.balances.read = r2
        self.transient = snap[1]; del self.logs[snap[3]:]
    def _call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
        ca = to if code_addr is None else code_addr
        if ca == NCA and storage_addr is None and bytes(data[:4]) == SEL_NCA_TRANSFER and len(data) == 100 and not value:
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
        if ca == NCC and storage_addr is None and bytes(data[:4]) == SEL_ISBL and len(data) == 36 and not value:
            self.ncaCalls = getattr(self, 'ncaCalls', 0) + 1
            return True, int(self.listed(int.from_bytes(data[4:36], 'big') & ((1 << 160) - 1))).to_bytes(32, 'big')
        if (ca >> 8) == (0x18 << 152) >> 8: raise NotImplementedError('arc precompile %#x %s' % (ca, bytes(data[:4]).hex()))
        if value and storage_addr is None:
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

def run_once(base, tx, rec, blk, cid=5042, pre=None):
    w = W(base); base.w = w
    pre = pre or {'st': {}, 'bal': {}, 'code': {}, 'nonce': {}}
    w.storage.update(pre['st']); w.balances.update(pre['bal']); w.codes.update(pre['code'])
    class N(dict):
        def get(s, a, d=0): return pre['nonce'].get(a, base.get('nonce', a))
    w.ctx = {'origin': int(tx['from'], 16), 'gasprice': I(rec.get('effectiveGasPrice') or tx.get('gasPrice')), 'coinbase': int(blk['miner'], 16),
             'timestamp': I(blk['timestamp']), 'number': I(blk['number']), 'prevrandao': int(blk.get('mixHash') or '0x0', 16),
             'gaslimit': I(blk['gasLimit']), 'chainid': cid, 'basefee': I(blk.get('baseFeePerGas') or '0x0'), 'nonces': N(), 'gas': I(tx['gas']), 'osaka': True}
    w.watch = {PM}; w.max_steps = 40_000_000
    frm = int(tx['from'], 16)
    # the sender pays gas before execution; the reference only needs a balance that covers the value
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
        if base.miss and rounds < 60:
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
        if base.miss and rounds < 80:
            base.fetch(); continue
        break
    return base, w, ok, ret, err, rounds, notes
