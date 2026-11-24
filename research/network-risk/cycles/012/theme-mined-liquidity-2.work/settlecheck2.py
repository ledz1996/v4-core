"""Monad (143): the settlement path as block execution ran it, checked against src/ from the recorded
call frames alone. Read-only.

debug_traceTransaction with callTracer returns the frames block execution recorded (see
frames_monad.py). For each transaction the frames are walked in execution order with a model of
the PoolManager's synced currency and reserves (src/libraries/CurrencyReserves.sol), which a
reverted frame rolls back like transient storage, and every settlement call is checked:
  sync(X), X != 0      one STATICCALL X.balanceOf(PoolManager); reserves := its 32 byte result
                       (src/PoolManager.sol:279-288, src/types/Currency.sol:90-95)
  sync(0)              no call; synced currency := 0
  settle / settleFor   synced X != 0: no value, one STATICCALL X.balanceOf(PoolManager) = B, and a
                       successful frame returns B - reserves and resets the synced currency;
                       synced currency 0: returns msg.value and makes no call
                       (src/PoolManager.sol:349-364)
  take(X, to, a)       X != 0: one CALL X.transfer(to, a) with value 0; X = 0: one CALL to with
                       value a and empty input (src/PoolManager.sol:291-297, src/types/Currency.sol:40-88)
  mint / burn / clear  no external call (src/PoolManager.sol:310-336)
A frame that succeeded where the model says it must have failed, or returned another amount, is a
mismatch.

Usage: python3 -I settlecheck.py <scan.json> <out.json> [limit] [threads]
"""
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/011/theme-monad-settlement-path.work')
from rpcq import rpc

PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
TR = {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}
SEL = {'0xa5841194': 'sync', '0x11da60b4': 'settle', '0x3dd45adb': 'settleFor', '0x0b0d9c09': 'take',
       '0x156e29f6': 'mint', '0xf5298aca': 'burn', '0x80f0b44c': 'clear', '0x48c89491': 'unlock'}
BAL = '0x70a08231' + PM[2:].rjust(64, '0')
U = 1 << 256


def word(h, i): return int(h[2 + 64 * i: 2 + 64 * (i + 1)] or '0', 16)
def addr(h, i): return '0x' + h[2 + 64 * i + 24: 2 + 64 * (i + 1)]


class Check:
    def __init__(self):
        self.st = {'cur': '0x' + '0' * 40, 'res': 0}
        self.n = {}; self.bad = []

    def count(self, k): self.n[k] = self.n.get(k, 0) + 1

    def walk(self, node, tx):
        snap = dict(self.st)
        to = (node.get('to') or '').lower(); inp = (node.get('input') or '0x').lower(); err = node.get('error')
        calls = node.get('calls', []) or []
        if to == PM and node.get('type') in ('CALL',) and inp[:10] in SEL:
            self.pm(SEL[inp[:10]], node, inp, err, calls, tx)
        for c in calls: self.walk(c, tx)
        if err: self.st = snap

    def fail(self, tx, kind, why, node):
        self.bad.append({'tx': tx, 'kind': kind, 'why': why, 'input': (node.get('input') or '')[:140], 'output': (node.get('output') or '')[:140], 'error': node.get('error')})

    def pm(self, k, node, inp, err, calls, tx):
        ext = [c for c in calls]
        if k == 'sync':
            x = addr(inp[8:], 0) if False else '0x' + inp[10 + 24:10 + 64]
            if int(x, 16) == 0:
                self.count('sync0')
                if ext: self.fail(tx, k, 'native sync made a call', node)
                if not err: self.st['cur'] = '0x' + '0' * 40
                return
            self.count('syncToken')
            if err: self.count('syncToken.failed'); return
            if len(ext) != 1 or ext[0].get('type') != 'STATICCALL' or (ext[0].get('to') or '').lower() != x or (ext[0].get('input') or '').lower() != BAL:
                return self.fail(tx, k, 'expected one balanceOf staticcall to the currency', node)
            out = (ext[0].get('output') or '0x')
            if 'error' in ext[0] or len(out) < 66: return self.fail(tx, k, 'sync succeeded although balanceOf failed or returned under 32 bytes', node)
            self.st['cur'] = x; self.st['res'] = int(out[2:66], 16)
            if (node.get('output') or '0x') not in ('0x', ''): self.fail(tx, k, 'sync returned data', node)
            return
        if k in ('settle', 'settleFor'):
            val = int(node.get('value') or '0x0', 16)
            if int(self.st['cur'], 16) == 0:
                self.count(k + '.native')
                if err: self.count(k + '.native.failed'); return
                if ext: return self.fail(tx, k, 'native settle made a call', node)
                if word(node.get('output') or '0x', 0) != val: return self.fail(tx, k, f'returned {word(node.get("output") or "0x", 0)} for msg.value {val}', node)
                self.count(k + '.native.ok'); return
            self.count(k + '.token')
            if err:
                self.count(k + '.token.failed')
                if val == 0 and ext and 'error' not in ext[0] and len(ext[0].get('output') or '') >= 66:
                    b = int(ext[0]['output'][2:66], 16)
                    if b >= self.st['res'] and b - self.st['res'] < (1 << 127): self.count(k + '.token.failedWithValidPayment')
                return
            if val: return self.fail(tx, k, 'token settle with value succeeded', node)
            if len(ext) != 1 or ext[0].get('type') != 'STATICCALL' or (ext[0].get('to') or '').lower() != self.st['cur'] or (ext[0].get('input') or '').lower() != BAL:
                return self.fail(tx, k, 'expected one balanceOf staticcall to the synced currency', node)
            b = int((ext[0].get('output') or '0x' + '0' * 64)[2:66], 16)
            paid = b - self.st['res']
            if paid < 0: return self.fail(tx, k, 'succeeded although balance fell below reserves', node)
            if paid >= 1 << 127: return self.fail(tx, k, 'succeeded although paid does not fit int128', node)
            if word(node.get('output') or '0x', 0) != paid: return self.fail(tx, k, f'returned {word(node.get("output") or "0x", 0)}, balance {b} minus reserves {self.st["res"]} is {paid}', node)
            self.count(k + '.token.ok'); self.count(k + '.token.paidNonzero' if paid else k + '.token.paidZero')
            self.st['cur'] = '0x' + '0' * 40
            return
        if k == 'take':
            x = '0x' + inp[10 + 24:10 + 64]; to = '0x' + inp[10 + 64 + 24:10 + 128]; a = int(inp[10 + 128:10 + 192], 16)
            self.count('take.native' if int(x, 16) == 0 else 'take.token')
            if err: self.count('take.failed'); return
            if a >= 1 << 127: return self.fail(tx, k, 'take above int128 succeeded', node)
            if len(ext) != 1: return self.fail(tx, k, f'{len(ext)} calls', node)
            c = ext[0]
            if 'error' in c: return self.fail(tx, k, 'take succeeded although the transfer call failed', node)
            if int(x, 16) == 0:
                if (c.get('to') or '').lower() != to or int(c.get('value') or '0x0', 16) != a or (c.get('input') or '0x') not in ('0x', ''):
                    return self.fail(tx, k, 'native payout differs', node)
            else:
                want = '0xa9059cbb' + to[2:].rjust(64, '0') + hex(a)[2:].rjust(64, '0')
                if (c.get('to') or '').lower() != x or (c.get('input') or '').lower() != want or int(c.get('value') or '0x0', 16):
                    return self.fail(tx, k, 'transfer call differs from take arguments', node)
                o = (c.get('output') or '0x')
                if not (o in ('0x', '') or (len(o) >= 66 and int(o[2:66], 16) == 1)):
                    return self.fail(tx, k, f'take succeeded with transfer return {o[:80]}', node)
            self.count('take.ok'); return
        if k in ('mint', 'burn', 'clear'):
            self.count(k)
            if ext: self.fail(tx, k, 'made an external call', node)
            return
        if k == 'unlock':
            self.count('unlock' + ('.failed' if err else '.ok'))


def one(h):
    try:
        t = rpc('debug_traceTransaction', [h, TR])
    except Exception as e:
        return h, None, str(e)[:200]
    c = Check(); c.walk(t, h)
    return h, c, None


def main():
    scan = json.load(open(sys.argv[1])); out = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9; th = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    sel = scan['txs'][:limit]; txs = {h: {'b': b} for h, b in zip(scan['txs'], scan['blocks'])}
    tot = {}; bad = []; errs = 0
    with cf.ThreadPoolExecutor(th) as ex:
        for i, (h, c, e) in enumerate(ex.map(one, sel)):
            if c is None: errs += 1; continue
            for k, v in c.n.items(): tot[k] = tot.get(k, 0) + v
            bad += c.bad
            if i % 500 == 0: print(i, len(bad), flush=True)
    blocks = [txs[h]['b'] for h in sel]
    res = {'transactions': len(sel), 'errors': errs, 'blocks': [min(blocks), max(blocks)], 'counts': dict(sorted(tot.items())), 'mismatches': len(bad), 'firstMismatches': bad[:40]}
    json.dump(res, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'firstMismatches'}, indent=1)); print(bad[:5])


main()
