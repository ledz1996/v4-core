"""KECCAK256 vectors aimed at the bucket index of the alloy-primitives keccak cache.

Index function, from the sources read in this cycle:
  alloy-primitives 1.6.0/1.6.1/1.7.3 src/utils/keccak_cache.rs: Hasher::write sets the state to
    rapidhash::v3::rapidhash_v3_micro_inline::<false, false>(bytes, &RapidSecrets::seed(0));
    write_usize (the length prefix) is a no-op, so the hash is that of the input bytes only.
  fixed-cache 0.1.10 src/lib.rs calc(): bucket = hash & (capacity - 1), tag = hash & !(capacity - 1);
    the default capacity is 1 << 17 (keccak_cache.rs COUNT / DEFAULT_COUNT).
  rapidhash 4.4.1 / 4.5.1 src/v3/rapid_const.rs rapidhash_micro_core, src/v3/seed.rs seed(),
    premix_seed(), src/util/mix.rs rapid_mix / rapid_mum. Transcribed below. The transcription could not
    be compared with the compiled crate in this session (building a Rust harness was not permitted), so
    the index function is derived from source only; every vector is checked against the Python keccak
    whatever bucket it lands in.

Vectors: a pool of random inputs of every length 1..88 plus the exact shapes the PoolManager hashes
(64 bytes: address word then currency word, CurrencyDelta.sol:12-14; 64 bytes: key word then slot word for
mappings and TickBitmap.sol:69-70; 58 bytes: owner, tickLower, tickUpper, salt, Position.sol:55-60) is
grouped by bucket. Buckets that hold two or more inputs (same or different lengths) are sent in an
interleaved order A B A B ... so that each lookup evicts the previous entry and the next one misses,
refills and is read back. Every group also gets the one byte shorter and one byte longer variant of A
(the length is part of the key, the hash input differs only by a trailing byte). Requests are sent several
at a time in parallel threads so that readers and writers of the same buckets overlap on the node.

Contract (placed by state override): calldata is a list of 128 byte records, word 0 = length (<= 96),
then 96 bytes of data. For each record: calldatacopy(0, off + 32, 96); keccak256(0, len); store.
Usage: python3 keccak_buckets.py <out.json> <chainId> [...]
"""
import sys, os, json, random, time, concurrent.futures as cf
base = os.path.dirname(os.path.abspath(__file__)).rsplit('/', 3)[0]
sys.path.insert(0, base + '/tools/opdiff')
from evm import assemble, keccak, call_code, rpc

U64 = (1 << 64) - 1
DS = [0x2d358dccaa6c78a5, 0x8bb84b93962eacc9, 0x4b33a62ed433d4a3, 0x4d5a2da51de1aa47,
      0xa0761d6478bd642f, 0xe7037ed1a0b428db, 0x90ed1765281c388c]


def mix(a, b):
    r = (a & U64) * (b & U64)
    return (r & U64) ^ (r >> 64)


def mum(a, b):
    r = (a & U64) * (b & U64)
    return r & U64, r >> 64


def premix(seed, i):
    seed ^= mix(seed ^ DS[2], DS[i])
    if seed & (0xFFFF << 48) == 0: seed |= 1 << 63
    if seed & (0xFFFF << 24) == 0: seed |= 1 << 31
    if seed & 0xFFFF == 0: seed |= 1
    return seed


def secrets_seed(seed):
    seed = premix(seed, 0); s = [premix(seed, 0)]
    for i in range(1, 7): s.append(premix(s[-1], i))
    return seed, s


SEED, SEC = secrets_seed(0)


def r64(d, o): return int.from_bytes(d[o:o + 8], 'little')
def r32(d, o): return int.from_bytes(d[o:o + 4], 'little')


def rapid_micro(data, seed=SEED, s=SEC):
    """rapidhash_micro_core::<AVALANCHE=false, PROTECTED=false> (rapid_const.rs:236-310)."""
    a = b = 0; n = len(data)
    if n <= 16:
        if n >= 4:
            seed ^= n
            if n >= 8: a ^= r64(data, 0); b ^= r64(data, n - 8)
            else: a ^= r32(data, 0); b ^= r32(data, n - 4)
        elif n:
            a ^= (data[0] << 45) | data[n - 1]; b ^= data[n >> 1]
        rem = n
    else:
        sl = data
        if len(sl) > 80:
            s1 = s2 = s3 = s4 = seed
            while len(sl) > 80:
                seed = mix(r64(sl, 0) ^ s[0], r64(sl, 8) ^ seed)
                s1 = mix(r64(sl, 16) ^ s[1], r64(sl, 24) ^ s1)
                s2 = mix(r64(sl, 32) ^ s[2], r64(sl, 40) ^ s2)
                s3 = mix(r64(sl, 48) ^ s[3], r64(sl, 56) ^ s3)
                s4 = mix(r64(sl, 64) ^ s[4], r64(sl, 72) ^ s4)
                sl = sl[80:]
            seed ^= s1; s2 ^= s3; seed ^= s4; seed ^= s2
        if len(sl) > 16:
            seed = mix(r64(sl, 0) ^ s[2], r64(sl, 8) ^ seed)
            if len(sl) > 32:
                seed = mix(r64(sl, 16) ^ s[2], r64(sl, 24) ^ seed)
                if len(sl) > 48:
                    seed = mix(r64(sl, 32) ^ s[1], r64(sl, 40) ^ seed)
                    if len(sl) > 64:
                        seed = mix(r64(sl, 48) ^ s[1], r64(sl, 56) ^ seed)
        rem = len(sl)
        a ^= r64(data, n - 16) ^ rem; b ^= r64(data, n - 8)
    a ^= s[1]; b ^= seed
    a, b = mum(a, b)
    return a ^ b


COUNT = 1 << 17
MAXLEN = 87  # 128 - 32 - 1 - 8


def bucket(data): return rapid_micro(data) & (COUNT - 1)


def contract():
    p = [('PUSH', 0)]  # i
    p += [('LABEL', 'loop'), 'DUP1', ('PUSH', 128), 'MUL',  # off, i
          'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'done'), 'JUMPI',
          ('PUSH', 96), 'DUP2', ('PUSH', 32), 'ADD', ('PUSH', 0), 'CALLDATACOPY',  # off, i
          'CALLDATALOAD', ('PUSH', 0), 'KECCAK256',  # h, i
          'DUP2', ('PUSH', 32), 'MUL', ('PUSH', 0x1000), 'ADD', 'MSTORE',  # i
          ('PUSH', 1), 'ADD', ('REF', 'loop'), 'JUMP']
    p += [('LABEL', 'done'), 'POP', ('PUSH', 32), 'MUL', ('PUSH', 0x1000), 'RETURN']
    return assemble(p)


def encode(recs):
    out = bytearray()
    for d in recs:
        assert len(d) <= 96
        out += len(d).to_bytes(32, 'big') + d.ljust(96, b'\0')
    return bytes(out)


def build(seed=11628):
    rnd = random.Random(seed)
    pool = []
    for ln in range(1, 89):
        for _ in range(300): pool.append(('rand', bytes(rnd.getrandbits(8) for _ in range(ln))))
    for _ in range(3000):  # delta slot: mstore(0, target), mstore(32, currency)
        pool.append(('delta64', bytes(12) + rnd.getrandbits(160).to_bytes(20, 'big') + bytes(12) + rnd.getrandbits(160).to_bytes(20, 'big')))
    for _ in range(2000):  # mapping slot: key word then small slot number
        pool.append(('map64', rnd.getrandbits(256).to_bytes(32, 'big') + rnd.randrange(0, 12).to_bytes(32, 'big')))
    for _ in range(3000):  # position key: owner(20) tickLower(3) tickUpper(3) salt(32)
        tl = rnd.randrange(-887272, 887272); tu = rnd.randrange(tl, 887273)
        pool.append(('pos58', rnd.getrandbits(160).to_bytes(20, 'big') + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + rnd.getrandbits(256).to_bytes(32, 'big')))
    by = {}
    for kind, d in pool:
        if len(d) <= MAXLEN: by.setdefault(bucket(d), []).append((kind, d))
    groups = [g for g in by.values() if len(g) >= 2]
    recs = []; meta = {'pool': len(pool), 'cachedLengthInputs': sum(len(v) for v in by.values()), 'collidingBuckets': len(groups),
                       'crossLength': sum(1 for g in groups if len({len(d) for _, d in g}) > 1),
                       'withPoolManagerShape': sum(1 for g in groups if any(k != 'rand' for k, _ in g))}
    for g in groups:
        ds = [d for _, d in g]
        seq = []
        for _ in range(3): seq += ds  # A B (C) A B (C) A B (C)
        a = ds[0]
        if len(a) > 1: seq.append(a[:-1])
        if len(a) < 96: seq.append(a + b'\0')
        seq.append(a)
        recs.append(seq)
    # inputs of 88 bytes bypass the cache (MAX_INPUT_LEN 87); add some next to cached 87 byte twins
    for _ in range(300):
        d = bytes(rnd.getrandbits(8) for _ in range(87))
        recs.append([d, d + b'\0', d, d + bytes([rnd.getrandbits(8)]), d])
    return recs, meta


_KC = {}


def kc(d):
    h = _KC.get(d)
    if h is None: h = _KC[d] = keccak(d)
    return h


def run_net(cid, url, recs, code, rounds=3, par=4, size=500):
    flat = [d for g in recs for d in g]
    chunks = [flat[i:i + size] for i in range(0, len(flat), size)]
    res = {'chainId': cid, 'records': len(flat), 'rounds': []}
    try: res['clientVersion'] = rpc(url, 'web3_clientVersion', [])
    except Exception as e: res['clientVersion'] = 'error ' + str(e)[:80]

    def one(ch):
        try:
            out = call_code(url, code, encode(ch))
        except Exception as e:
            return ('err', str(e)[:160], len(ch))
        if len(out) != 32 * len(ch): return ('err', f'short {len(out)}', len(ch))
        bad = []
        for k, d in enumerate(ch):
            if out[32 * k:32 * k + 32] != kc(d): bad.append({'len': len(d), 'input': d.hex(), 'got': out[32 * k:32 * k + 32].hex(), 'want': kc(d).hex()})
        return ('ok', bad, len(ch))

    for r in range(rounds):
        ran = 0; bad = []; errs = []
        with cf.ThreadPoolExecutor(par) as ex:
            for st, x, n in ex.map(one, chunks):
                if st == 'ok': ran += n; bad += x
                else: errs.append(x)
        res['rounds'].append({'ran': ran, 'mismatchCount': len(bad), 'mismatches': bad[:20], 'errors': errs[:5], 'errorCount': len(errs)})
        print(cid, 'round', r, 'ran', ran, 'of', len(flat), 'bad', len(bad), 'errors', len(errs), errs[:1], flush=True)
    return res


if __name__ == '__main__':
    out = sys.argv[1]; cids = [int(x) for x in sys.argv[2:]]
    nets = {n['chainId']: n for n in json.load(open(base + '/state/networks.json'))['networks']}
    recs, meta = build(); code = contract()
    for g in recs:
        for d in g: kc(d)
    print('meta', meta, 'records', sum(len(g) for g in recs), 'code', len(code), flush=True)
    results = {'meta': meta, 'codeHex': code.hex(), 'networks': []}
    with cf.ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(run_net, c, nets[c]['rpc'], recs, code) for c in cids]
        for f in futs: results['networks'].append(f.result())
    json.dump(results, open(out, 'w'), indent=1)
