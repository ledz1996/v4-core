"""Task 3: for one reth-derived network, take PoolManager slots written in the newest blocks and compare
eth_getStorageAt with extsload(bytes32[]) through eth_call at the writing block B and at B+1, with a second
provider at B, and with the values the block's own Swap events state (sqrtPriceX96, tick, liquidity).

Read-only. Usage: python3 -I slotcmp.py <chainId> <primary> <second|-> <out.json> [nslots] [window]
"""
import sys, json, time, random, urllib.request, ssl, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import keccak  # noqa: E402

ctx = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt')
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
MODIFY = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
SEL = keccak(b'extsload(bytes32[])')[:4]
M = (1 << 256) - 1


def rpc(url, method, params, timeout=60, retries=3):
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                         headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                j = json.load(r)
            if 'error' in j:
                raise RuntimeError(json.dumps(j['error'])[:300])
            return j['result']
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (k + 1))
    raise last


def h32(x):
    return '0x' + (x & M).to_bytes(32, 'big').hex()


def sgn(x, bits):
    x &= (1 << bits) - 1
    return x - (1 << bits) if x >> (bits - 1) else x


def mapslot(key_word, base):
    return int.from_bytes(keccak((key_word & M).to_bytes(32, 'big') + (base & M).to_bytes(32, 'big')), 'big')


def slots_for(lg):
    pid = int(lg['topics'][1], 16)
    base = mapslot(pid, 6)
    out = [('slot0', base), ('feeGrowthGlobal0', base + 1), ('feeGrowthGlobal1', base + 2), ('liquidity', base + 3)]
    d = bytes.fromhex(lg['data'][2:])
    w = [int.from_bytes(d[i:i + 32], 'big') for i in range(0, len(d), 32)]
    if lg['topics'][0] == SWAP:
        tick = sgn(w[4], 24)
        ticks = [tick]
    else:
        tl, tu, salt = sgn(w[0], 24), sgn(w[1], 24), w[3]
        ticks = [tl, tu]
        owner = bytes.fromhex(lg['topics'][2][2:])[12:]
        pk = keccak(owner + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt.to_bytes(32, 'big'))
        ps = mapslot(int.from_bytes(pk, 'big'), base + 6)
        out += [('position.liquidity', ps), ('position.fgi0', ps + 1), ('position.fgi1', ps + 2)]
    for t in ticks:
        ts = mapslot(t & M, base + 4)
        out += [(f'tick{t}.gross_net', ts), (f'tick{t}.fgo0', ts + 1), (f'tick{t}.fgo1', ts + 2),
                (f'bitmap{t >> 8}', mapslot((t >> 8) & M, base + 5))]
    return [(n, s & M) for n, s in out]


def extsload(url, pm, slots, block):
    data = SEL + (32).to_bytes(32, 'big') + len(slots).to_bytes(32, 'big') + b''.join(s.to_bytes(32, 'big') for s in slots)
    r = bytes.fromhex(rpc(url, 'eth_call', [{'to': pm, 'data': '0x' + data.hex()}, hex(block)])[2:])
    n = int.from_bytes(r[32:64], 'big')
    assert n == len(slots)
    return [int.from_bytes(r[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]


def gsa(url, pm, s, block):
    return int(rpc(url, 'eth_getStorageAt', [pm, h32(s), hex(block)]), 16)


def main():
    cid, url, url2, outp = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    nslots = int(sys.argv[5]) if len(sys.argv) > 5 else 200
    window = int(sys.argv[6]) if len(sys.argv) > 6 else 2000
    nets = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'state', 'networks.json')))['networks']
    pm = [n for n in nets if n['chainId'] == cid][0]['poolManager']
    rec = {'chainId': cid, 'primary': url, 'second': url2, 'pm': pm, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    rec['clientVersionBefore'] = rpc(url, 'web3_clientVersion', [])
    if url2 != '-':
        try:
            rec['secondClientVersionBefore'] = rpc(url2, 'web3_clientVersion', [])
        except Exception as e:  # noqa
            rec['secondError'] = str(e)[:300]; url2 = '-'
    head = int(rpc(url, 'eth_blockNumber', []), 16) - 2
    rec['head'] = head
    logs, hi, step = [], head, min(window, 500)
    tried = 0
    while len(logs) < 40 and tried < 40 and hi > 0:
        lo = max(0, hi - step + 1)
        try:
            got = rpc(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [[SWAP, MODIFY]]}], timeout=90)
            logs = got + logs
            hi = lo - 1
            if not got and step < 100000:
                step *= 2
        except Exception as e:  # noqa
            step = max(10, step // 2)
            rec.setdefault('logErrors', []).append(str(e)[:120])
        tried += 1
    rec['logRange'] = [hi + 1, head]
    rec['logCount'] = len(logs)
    # newest first; collect slots with their writing block
    logs.sort(key=lambda l: (int(l['blockNumber'], 16), int(l['logIndex'], 16)), reverse=True)
    items, seen = [], set()
    lastswap = {}
    for lg in logs:
        b = int(lg['blockNumber'], 16)
        if lg['topics'][0] == SWAP and (lg['topics'][1], b) not in lastswap:
            lastswap[(lg['topics'][1], b)] = lg
        for name, s in slots_for(lg):
            if s in seen:
                continue
            seen.add(s)
            items.append({'block': b, 'pool': lg['topics'][1], 'name': name, 'slot': h32(s), 'tx': lg['transactionHash']})
            if len(items) >= nslots:
                break
        if len(items) >= nslots:
            break
    byblock = {}
    for it in items:
        byblock.setdefault(it['block'], []).append(it)
    mism, ev_checks, ev_mism = [], 0, []
    for b, its in sorted(byblock.items()):
        sl = [int(it['slot'], 16) for it in its]
        e0 = extsload(url, pm, sl, b)
        e1 = extsload(url, pm, sl, b + 1) if b + 1 <= head + 2 else None
        e2 = None
        if url2 != '-':
            try:
                e2 = extsload(url2, pm, sl, b)
            except Exception as e:  # noqa
                rec['secondError'] = f'block {b}: ' + str(e)[:300]; url2 = '-'
        for i, it in enumerate(its):
            g0 = gsa(url, pm, sl[i], b)
            g1 = gsa(url, pm, sl[i], b + 1) if e1 is not None else None
            g2 = None
            if url2 != '-':
                try:
                    g2 = gsa(url2, pm, sl[i], b)
                except Exception as e:  # noqa
                    rec['secondError'] = f'block {b}: ' + str(e)[:300]; url2 = '-'
            it.update({'gsaB': h32(g0), 'extB': h32(e0[i]), 'gsaB1': None if g1 is None else h32(g1),
                       'extB1': None if e1 is None else h32(e1[i]), 'gsa2B': None if g2 is None else h32(g2),
                       'ext2B': None if e2 is None else h32(e2[i])})
            kinds = []
            if g0 != e0[i]: kinds.append('gsa!=ext@B')
            if e1 is not None and g1 != e1[i]: kinds.append('gsa!=ext@B+1')
            if g2 is not None and g2 != g0: kinds.append('provider2 gsa!=primary@B')
            if e2 is not None and e2[i] != e0[i]: kinds.append('provider2 ext!=primary@B')
            if kinds:
                it['kinds'] = kinds; mism.append(it)
            # event cross check: last Swap of this pool in block b fixes slot0 price/tick and liquidity
            sw = lastswap.get((it['pool'], b))
            if sw and it['name'] in ('slot0', 'liquidity'):
                d = bytes.fromhex(sw['data'][2:]); w = [int.from_bytes(d[k:k + 32], 'big') for k in range(0, len(d), 32)]
                later = [l for l in logs if l['topics'][1] == it['pool'] and int(l['blockNumber'], 16) == b and int(l['logIndex'], 16) > int(sw['logIndex'], 16)]
                if later:
                    continue
                ev_checks += 1
                if it['name'] == 'slot0':
                    ok = (e0[i] & ((1 << 160) - 1)) == w[2] and sgn(e0[i] >> 160, 24) == sgn(w[4], 24)
                else:
                    ok = (e0[i] & ((1 << 128) - 1)) == w[3]
                if not ok:
                    ev_mism.append({'item': it, 'swap': sw})
    rec['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [])
    if url2 != '-':
        try:
            rec['secondClientVersionAfter'] = rpc(url2, 'web3_clientVersion', [])
        except Exception as e:  # noqa
            rec['secondError'] = 'after: ' + str(e)[:300]
    rec['nslots'] = len(items); rec['blocks'] = len(byblock); rec['mismatches'] = mism
    rec['eventChecks'] = ev_checks; rec['eventMismatches'] = ev_mism
    rec['items'] = items
    rec['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(rec, open(outp, 'w'), indent=1)
    print(cid, rec['clientVersionBefore'], '|', rec.get('secondClientVersionBefore'), '| slots', len(items), 'blocks', len(byblock),
          'mism', len(mism), 'evchecks', ev_checks, 'evmism', len(ev_mism))


if __name__ == '__main__':
    main()
