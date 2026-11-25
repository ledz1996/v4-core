# Writes theme-monad-harness-exact.research.json from the result files in this work directory.
import json, glob, os, re, collections
W = os.path.dirname(os.path.abspath(__file__))
os.chdir(W)
OUT = '../theme-monad-harness-exact.research.json'
WD = 'research/network-risk/cycles/016/theme-monad-harness-exact.work'
ALL = [n['chainId'] for n in json.load(open('../../../state/networks.json'))['networks']]
OTHER = [c for c in ALL if c != 143]

def summ(path):
    return [l.strip() for l in open(path)]

def mined(path):
    t = collections.Counter(); g = [0, 0]
    for l in open(path):
        for kv in l.split():
            k, v = kv.split('=')
            if k == 'frame_gas_equal':
                a, b = v.split('/'); g[0] += int(a); g[1] += int(b)
            else:
                t[k] += int(v)
    return t, g

v167 = summ('out-v167/summary.txt'); v165 = summ('out-v165/summary.txt')
m167, g167 = mined('mined/out-v167/summary.txt'); m165, g165 = mined('mined/out-v165/summary.txt')
mf5, _ = mined('mined/out-f5/summary.txt')
m512, g512 = mined('mined/out-v167-512/summary.txt') if os.path.exists('mined/out-v167-512/summary.txt') else (None, None)
gd = json.load(open('mined/gasdiff.json')) if os.path.exists('mined/gasdiff.json') else {}
t4 = json.load(open('task4.json'))
micro167 = open('micro/out-v167.txt').read().strip().split('\n')[-1]
micro165 = open('micro/out-v165.txt').read().strip().split('\n')[-1]
micro512 = open('micro/out-v167-512.txt').read().strip().split('\n')[-1] if os.path.exists('micro/out-v167-512.txt') else 'not run'

def faults(d):
    r = {}
    for f in glob.glob(f'{d}/*.out'):
        last = [l for l in open(f) if l.startswith('scenarios=')]
        r[os.path.basename(f)[:-4]] = last[-1].strip() if last else 'no summary'
    return r
f3 = faults('fault/out-f3'); f5 = faults('fault/out-f5')
r512 = {}
for f in glob.glob('out-v167-512/*.out'):
    last = [l for l in open(f) if l.startswith('scenarios=')]
    r512[os.path.basename(f)[:-4]] = last[-1].strip() if last else 'none'
n512 = sum(int(re.search(r'scenarios=(\d+)', v).group(1)) for v in r512.values() if 'scenarios=' in v)
mm512 = sum(int(re.search(r'mismatches=(\d+)', v).group(1)) for v in r512.values() if 'mismatches=' in v)

def fsum(d):
    s = m = 0
    for v in d.values():
        a = re.search(r'scenarios=(\d+) mismatches=(\d+)', v)
        if a: s += int(a.group(1)); m += int(a.group(2))
    return s, m

shape_lines = []
for r in t4['coarse']:
    shape_lines.append(f"{r['op']} [{r['shape']}]: {len(r['pcs'])} sites, {r['pcsExecutedByPoolManagerScenarios']} executed by the PoolManager scenarios, {r['microPrograms']} micro programs")
notrun = t4['fineVariantsNotExecuted']
notrun_txt = '; '.join(f"{x['op']} at pc {x['pcs'][0]} ({x['source'][0]}, shape {x['shape'].split(' > ')[-1]}, {x['microPrograms']} micro programs of the same shape)" for x in notrun)

research = {
    'unit': 'theme-monad-harness-exact',
    'profiles': [],
    'findings': [],
    'cleared': [],
    'leads': [],
    'leadResults': [],
}
C = research['cleared']
exec(open('research_text.py').read())
json.dump(research, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('written', OUT, len(C), 'cleared', len(research['leads']), 'leads')
