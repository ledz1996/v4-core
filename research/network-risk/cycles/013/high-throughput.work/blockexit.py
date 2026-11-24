"""Model of Monad Emitter::write_to_final_stack_offsets as written at v0.16.7
(category/vm/compiler/ir/x86/emitter.cpp, the dep_count / elems / non_dep / cycle code)
and at v0.16.5 (same algorithm, dep counts in an unordered_map iterated in arbitrary order).
Random block-exit stack states are built: every stack index in [min_delta, top] belongs to
one element; an element lives in any mix of {stack offset, general reg, avx reg, literal}.
Memory holds, at each occupied stack offset, the value of the element located there.
The model executes the moves the emitter emits and checks that every final stack index
holds the value of its element, and that the v0.16.7 order (stack index order) and a
shuffled order (standing for the v0.16.5 heap-address order) both reach it.
Also checks countl_zero of category/core/runtime/uint256.hpp at v0.16.7 against Python.
Usage: python3 blockexit.py [cases]"""
import random, sys, json

def countl_zero_v0167(x):
    w = [(x >> (64 * i)) & ((1 << 64) - 1) for i in range(4)]
    cnt = 256
    for i in range(4):
        if w[i] != 0:
            cnt = 192 - 64 * i + (64 - w[i].bit_length())
    return cnt

def run(state, order_mode, rnd):
    mn, top, elems, mem = state
    mem = dict(mem)
    by_index = {}
    for e in elems:
        for i in e['idx']:
            by_index[i] = e
    # dependency counts, exactly as the loop over i = min_delta..top
    dep = {id(e): 0 for e in elems}
    visit = []
    for i in range(mn, top + 1):
        d = by_index[i]
        if i != min(d['idx']):
            continue
        visit.append(d)
        if d.get('off') is None: continue
        o = d['off']
        if o > top: continue
        e = by_index[o]
        if e is d: continue
        if d.get('avx'): continue
        dep[id(e)] += 1
    if order_mode == 'shuffle':
        rnd.shuffle(visit)
    non_dep = [e for e in visit if dep[id(e)] == 0]
    while non_dep:
        d = non_dep.pop()
        idx = sorted(d['idx'])
        if len(idx) == 1 and d.get('off') == idx[0]:
            continue
        if d.get('avx'):
            y = d['val']
        elif d.get('off') is not None:
            y = mem[d['off']]
        elif d.get('lit'):
            y = d['val']
        else:
            y = d['val']  # general register
        for i in idx:
            if d.get('off') != i:
                mem[i] = y
        if not d.get('avx') and d.get('off') is not None:
            i = d['off']
            if i > top: continue
            e = by_index[i]
            if e is d: continue
            dep[id(e)] -= 1
            assert dep[id(e)] >= 0
            if dep[id(e)] == 0:
                non_dep.append(e)
    for e in visit:
        if dep[id(e)] == 0: continue
        cycle = []; d = e
        while True:
            assert dep[id(d)] == 1 and not d.get('avx') and d.get('off') is not None
            dep[id(d)] = 0; cycle.append(d); d = by_index[d['off']]
            if d is e: break
        yx1 = mem[cycle[-1]['off']]
        for k in range(len(cycle) - 1, 0, -1):
            yx2 = mem[cycle[k - 1]['off']]
            for i in cycle[k]['idx']:
                mem[i] = yx1
            yx1 = yx2
        for i in e['idx']:
            mem[i] = yx1
    for e in elems:
        for i in e['idx']:
            if mem.get(i) != e['val']:
                return False
    return True

def make(rnd):
    mn = -rnd.randint(0, 6); top = mn + rnd.randint(0, 9)
    positions = list(range(mn, top + 1))
    rnd.shuffle(positions)
    elems = []
    while positions:
        k = rnd.choice([1, 1, 1, 2, 3])
        idx, positions = positions[:k], positions[k:]
        elems.append({'idx': set(idx), 'val': rnd.getrandbits(256)})
    # assign locations: each elem gets an offset with some probability, offsets distinct
    free = list(range(mn, top + 4)); rnd.shuffle(free)
    mem = {}
    for e in elems:
        r = rnd.random()
        if r < 0.55 and free:
            e['off'] = free.pop(); mem[e['off']] = e['val']
            if rnd.random() < 0.3: e['avx'] = True
        elif r < 0.75:
            e['avx'] = True
        elif r < 0.9:
            e['gpr'] = True
        else:
            e['lit'] = True
    # junk in unoccupied memory
    for i in range(mn, top + 4):
        mem.setdefault(i, rnd.getrandbits(256))
    return (mn, top, elems, mem)

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    rnd = random.Random(13_143)
    bad = {'stack': 0, 'shuffle': 0}
    for _ in range(n):
        st = make(rnd)
        for m in bad:
            if not run(st, m, rnd): bad[m] += 1
    clz_bad = 0
    for _ in range(200000):
        x = rnd.getrandbits(rnd.choice([0, 1, 63, 64, 65, 128, 191, 192, 200, 256]))
        if countl_zero_v0167(x) != 256 - x.bit_length(): clz_bad += 1
    for x in [0, 1, (1 << 256) - 1, 1 << 64, 1 << 128, 1 << 192, 1 << 255]:
        if countl_zero_v0167(x) != 256 - x.bit_length(): clz_bad += 1
    print(json.dumps({'cases': n, 'wrong_final_stack': bad, 'countl_zero_cases': 200007, 'countl_zero_wrong': clz_bad}))
