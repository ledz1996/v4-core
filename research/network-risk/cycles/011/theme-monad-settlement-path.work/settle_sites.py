"""List every settlement-path opcode of the PoolManager runtime with the operands that Monad's
compiler (v0.16.5) sees as literals at that point, using the block and literal rules of
cycles/010/theme-monad-compiled-mul.work/sites.py (a block starts at every JUMPDEST, literal
tracking restarts there, pure opcodes with literal inputs are folded).
Usage: python3 -I sites.py <build/PoolManager.json> <cycles/009/core-code-bytecode-map.work/instrs.json> <out.json>"""
import sys, json, collections
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '010', 'theme-monad-compiled-mul.work'))
import sites as S

TARGET = {0x0b: ('SIGNEXTEND', 2), 0x20: ('KECCAK256', 2), 0x33: ('CALLER', 0), 0x34: ('CALLVALUE', 0),
          0x35: ('CALLDATALOAD', 1), 0x37: ('CALLDATACOPY', 3), 0x3d: ('RETURNDATASIZE', 0), 0x3e: ('RETURNDATACOPY', 3),
          0x5c: ('TLOAD', 1), 0x5d: ('TSTORE', 2), 0x5e: ('MCOPY', 3), 0xf1: ('CALL', 7), 0xfa: ('STATICCALL', 6), 0x47: ('SELFBALANCE', 0)}

def main():
    code = bytes.fromhex(json.load(open(sys.argv[1]))['runtime'].removeprefix('0x'))
    instrs = {e['pc']: e for e in json.load(open(sys.argv[2]))}
    ins = []; i = 0
    while i < len(code):
        op = code[i]; k = op - 0x5f if 0x60 <= op <= 0x7f else 0
        ins.append((i, op, int.from_bytes(code[i + 1:i + 1 + k], 'big') if k else (0 if op == 0x5f else None)))
        i += 1 + k
    jd = {pc for pc, op, _ in ins if op == 0x5b}
    stack = []; sites = []
    def pop(): return stack.pop() if stack else None
    for idx, (pc, op, imm) in enumerate(ins):
        if op == 0x5b: stack = []
        if op in TARGET:
            name, n = TARGET[op]
            ops = [stack[-1 - j] if j < len(stack) else None for j in range(n)]
            e = instrs.get(pc, {})
            sites.append({'pc': pc, 'op': name, 'operandsTopFirst': [None if v is None else hex(v) for v in ops],
                          'src': e.get('src'), 'fn': e.get('fn')})
        if 0x5f <= op <= 0x7f: stack.append(imm)
        elif 0x80 <= op <= 0x8f:
            d = op - 0x7f; stack.append(stack[-d] if d <= len(stack) else None)
        elif 0x90 <= op <= 0x9f:
            d = op - 0x8f
            while len(stack) < d + 1: stack.insert(0, None)
            stack[-1], stack[-1 - d] = stack[-1 - d], stack[-1]
        elif op in S.FOLD:
            a = pop(); b = pop(); stack.append(S.FOLD[op](a, b) if a is not None and b is not None else None)
        elif op in S.UN:
            a = pop(); stack.append(S.UN[op](a) if a is not None else None)
        elif op == 0x56: pop(); stack = []
        elif op == 0x57:
            pop(); pop(); nxt = ins[idx + 1][0] if idx + 1 < len(ins) else None
            if nxt in jd: stack = []
        elif op in (0x00, 0xf3, 0xfd, 0xfe, 0xff): stack = []
        else:
            a, b = S.io(op)
            for _ in range(a): pop()
            for _ in range(b): stack.append(None)
    cnt = collections.Counter(s['op'] for s in sites)
    nonlit_se = [s for s in sites if s['op'] == 'SIGNEXTEND' and s['operandsTopFirst'][0] is None]
    json.dump({'codeBytes': len(code), 'counts': cnt, 'signextendNonLiteralIndex': len(nonlit_se), 'sites': sites},
              open(sys.argv[3], 'w'), indent=1)
    print(dict(cnt)); print('SIGNEXTEND with non-literal index:', len(nonlit_se))
    for s in sites:
        if s['op'] != 'SIGNEXTEND' or s['operandsTopFirst'][0] is None: print(s['pc'], s['op'], s['operandsTopFirst'], s['src'], s['fn'])

if __name__ == "__main__": main()
