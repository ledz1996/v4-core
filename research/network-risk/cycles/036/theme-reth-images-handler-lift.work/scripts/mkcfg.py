"""Write the arith.py configuration of one binary: lift the closure of every distinct arithmetic handler found by
tables.py (extract3.py), name the dynamic memcpy/memset/memmove/bcmp/memcmp slots, choose the table of the most
common EXP variant as the main table, and read the interpreter offsets from the handler text (stack pointer and
length from ADD, gas from EXP, host gas-parameter pointer and EXP byte cost offset from EXP).
usage: python3 -I mkcfg.py <name> <bin>"""
import collections, json, os, re, subprocess, sys
name, binf = sys.argv[1:3]
W = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/'
tab = json.load(open(W + 'out/tab-%s.json' % name))
addrs = sorted({x['addr'] for v in tab['handlers'].values() for x in v})
asm, aj = W + 'build/%s-arith.s' % name, W + 'build/%s-arith.json' % name
subprocess.run(['python3', '-I', W + 'scripts/extract3.py', binf, W + 'build/%s.fde' % name, W + 'build/%s.rel' % name,
                asm, aj] + addrs, check=True, capture_output=True)
ex = json.load(open(aj))
got = {}
for slot, v in ex['slots'].items():
    for k in ('memcpy', 'memset', 'memmove', 'bcmp', 'memcmp'):
        if v.startswith(k + '@'):
            got[slot] = k
for slot, v in ex['slots'].items():
    if v.startswith(('abort@', 'malloc@', 'free@', 'realloc@', 'posix_memalign@', '_Unwind')):
        got[slot] = 'panic'
cnt = collections.Counter()
for x in tab['handlers']['EXP']:
    cnt[x['addr']] = len(x['tables'])
main_exp = cnt.most_common(1)[0][0]
table = next(x for x in tab['handlers']['EXP'] if x['addr'] == main_exp)['tables'][0]
stride = dict((t, s) for t, s in tab['tables'])[table]


def text(a, n=0x180):
    a = int(a, 16)
    return subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % a,
                           '--stop-address=%#x' % (a + n), binf], capture_output=True, text=True).stdout
add = text(tab['handlers']['ADD'][0]['addr'], 0x48)
L = re.findall(r'(?:mov|cmp)\s+\w+,QWORD PTR \[rdi\+(0x[0-9a-f]+)\]', add)
exp = text(main_exp)
gas = re.search(r'mov\s+rdx,QWORD PTR \[rdi\+(0x[0-9a-f]+)\]', exp).group(1)
hp = re.search(r'mov\s+(\w+),QWORD PTR \[(?:rsi|rax)\+(0x[0-9a-f]+)\]', exp)
eb = re.search(r'mov\s+rax,QWORD PTR \[(?:rax|rdx)\+(0x[0-9a-f]+)\]', exp[exp.index(hp.group(0)):])
shl = text(tab['handlers']['SHL'][0]['addr'], 0x10)
spec = re.search(r'cmp\s+BYTE PTR \[rdi\+(0x[0-9a-f]+)\]', shl).group(1)
ret_status = bool(re.search(r'xor\s+eax,eax\s*\n\s*[0-9a-f]+:\s+ret', add))
cfg = {'bin': binf, 'arch': 'x86', 'asm': asm, 'table': table, 'stride': stride, 'rel': W + 'build/%s.rel' % name,
       'stack_ptr': [x for x in L if x != L[0]][0], 'stack_len': L[0], 'gas': gas, 'host_params': hp.group(2),
       'exp_byte_off': eb.group(1), 'spec_off': spec, 'spec_val': '0x12', 'void_return': not ret_status,
       'got': got, 'externs': {}, 'faults': {}, 'expVariants': list(cnt)}
json.dump(cfg, open(W + 'build/%s.cfg.json' % name, 'w'), indent=1)
print(name, {k: v for k, v in cfg.items() if k not in ('got', 'bin', 'asm', 'rel')}, len(ex['functions']), 'functions')
