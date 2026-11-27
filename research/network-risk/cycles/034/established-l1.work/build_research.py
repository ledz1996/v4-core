"""Build cycles/034/established-l1.research.json from the outputs in out/, dl/ and l1215/. Read-only apart from the output file."""
import json, os, glob, gzip, collections
W = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(W, '..', '..', '..'))
WD = 'research/network-risk/cycles/034/established-l1.work/'
def J(p):
    return json.load(open(os.path.join(W, p)))

def lastline(p, key):
    for l in open(os.path.join(W, p)):
        if key in l: yield ' '.join(l.split())

bat = list(lastline('out/battery.log', 'ran ')); tg = list(lastline('out/targeted.log', 'ran '))
pm1 = list(lastline('out/pmdiff.log', 'identical')); pm2 = list(lastline('out/pmdiff2.log', 'identical'))
sw = {r['chainId']: r for r in J('out/swaps.json')['results']}
rp = open(os.path.join(W, 'out/replay.log')).read().strip().splitlines()
rpp = open(os.path.join(W, 'out/replay-pol.log')).read().strip().splitlines() if os.path.exists(os.path.join(W, 'out/replay-pol.log')) else []
l1215 = J('l1215/raw/56/result.json')
clients = collections.Counter()
for f in glob.glob(os.path.join(W, 'l1215/raw/56/tx/*.json.gz')):
    rec = json.load(gzip.open(f))
    for c in rec.get('clientAround', []):
        clients[c] += 1
def swline(c):
    r = sw[c]
    return '%d swaps in blocks %d to %d, tick relation %s, %d pairs with amounts %s' % (r['swaps'], r['blocks'][0], r['blocks'][1], r['tick'], r['pairs'], r['amount'])

cv = open(os.path.join(W, 'out/clientversions.txt')).read()
EXTRA = json.load(open(os.path.join(W, 'extra.json')))
doc = {'unit': 'established-l1', '_lenses': ['L1', 'L2', 'L3', 'L5']}
doc.update(EXTRA)
# fill the run summaries into the cleared list
for c in doc['cleared']:
    c['result'] = c['result'].replace('{BAT}', '; '.join(bat)).replace('{TG}', '; '.join(tg)).replace('{PM1}', '; '.join(pm1)).replace('{PM2}', '; '.join(pm2)) \
        .replace('{SW137}', swline(137)).replace('{SW56}', swline(56)).replace('{SW43114}', swline(43114)).replace('{RP}', '; '.join(rp)).replace('{RPP}', '; '.join(rpp[-3:]) or 'no output') \
        .replace('{L1215}', 'txs %d, words compared %d, storage words changed %d, transactions with a mismatch %d, native mismatches %d, ERC-20 deficits %d, unmodelled %d, blocks %s' % (
            l1215['txs'], l1215['wordsCompared'], l1215['storageWordsChanged'], l1215['txWithMismatch'], l1215['nativeMismatch'], l1215['erc20Deficit'], l1215['unmodelled'], l1215['blocks'])) \
        .replace('{CLIENTS}', ', '.join('%s (%d)' % (k, v) for k, v in clients.most_common()))
for r in doc['leadResults']:
    r['answer'] = r['answer'].replace('{L1215}', 'txs %d, words compared %d, transactions with a mismatch %d, blocks %s' % (l1215['txs'], l1215['wordsCompared'], l1215['txWithMismatch'], l1215['blocks'])) \
        .replace('{CLIENTS}', ', '.join('%s (%d)' % (k, v) for k, v in clients.most_common()))
out = os.path.join(R, 'cycles/034/established-l1.research.json')
json.dump(doc, open(out, 'w'), indent=1)
print('wrote', out)
