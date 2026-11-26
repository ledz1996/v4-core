"""Shows that check.py can fail: plants a one-unit overpayment in every successful swap (output + 1 in the swap delta,
in the driver delta snapshot, and one unit less in the PoolManager balance, so only the exact relations can catch it) and a one-unit fee growth excess in every donate, and counts the cases flagged.
Usage: python3 plant.py <allcases.json> <ref.json> <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check as C
allc = json.load(open(sys.argv[1])); ref = json.load(open(sys.argv[2]))['results']
caught = tot = 0; dcaught = dtot = 0; miss = []
for c in allc['cases']:
    r = ref[str(c['id'])]
    if not r.get('ok') or c['kind'] not in (0, 1, 5): continue
    W = [int(x, 16) for x in r['w']]
    base = C.check_swap(c, W, c['kind']) if c['kind'] != 1 else C.check_donate(c, W)
    if base.get('status') != 'ok': continue
    W2 = list(W)
    if c['kind'] == 1:
        if c['p'][0] == 0: continue
        W2[15 + 3] = (W2[15 + 3] + 1) % (1 << 256); dtot += 1
        if C.check_donate(c, W2)['violations']: dcaught += 1
        continue
    i = 6 if c['kind'] == 0 else 9
    a0, a1 = C.unpack(W2[i + 7])
    if c['zfo']: a1 += 1
    else: a0 += 1
    W2[i + 7] = ((a0 & ((1 << 128) - 1)) << 128) | (a1 & ((1 << 128) - 1))
    # keep the snapshot delta and the PoolManager balance consistent, so only the exact relations can catch it
    k = 1 if c['zfo'] else 0
    W2[i + 9 + k] = (W2[i + 9 + k] + 1) % (1 << 256)
    W2[i + 15 + k] -= 1
    tot += 1
    if C.check_swap(c, W2, c['kind'])['violations']: caught += 1
    else: miss.append(c['id'])
json.dump({'swapsPlanted': tot, 'swapsCaught': caught, 'donatesPlanted': dtot, 'donatesCaught': dcaught, 'notCaught': miss}, open(sys.argv[3], 'w'))
print(tot, caught, dtot, dcaught, len(miss))
