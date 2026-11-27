"""Cycle 33 task 5: planted faults in in-memory copies of the model text (the disassembly the emulator parses; the
files are never changed). Each fault names the instruction address of the shipped amd64 build, asserts the text that
is there, and replaces it; the run must then report mismatches or model errors. Sites were read from
dis/fault-sites.txt (scripts listed there) and the closures of the models.

Faults (amd64 builds):
  revert_zero       the store of the restored word after mapassign in the storage revert takes the zero register
                    xmm15 (Go ABI zero) in place of xmm14: a revert that does not land on the original value restores 0
  revert_committed  the branch that skips the delete in the storage revert is removed (or made unconditional towards
                    the delete): every revert drops the dirty or local entry, so the slot reads its committed value
                    in place of the pre-frame value (not on avalanche, whose 1.13 journal entry holds no original)
  skip_journal      the call (or the inline length store) that appends the storage journal entry in SetState is a nop
  snap_off_by_one   the exit test of the journal revert loop admits one entry fewer (jg->jge, jl->jle)
  key_limb          the first byte swap of the SLOAD key in opSload is a nop: one 64-bit limb of the key keeps the
                    stack word's little-endian order
  transform_off     (avalanche only) the 'and edx,0xfffffffe' of partitionStateKeysHook.TransformStateKey is a nop,
                    so bit 248 is kept in the key
usage: python3 -I plant2.py <nitro|bor|borpar|avax> <nseq> <outdir>
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SITES = {
    'nitro': {
        'revert_zero': [(0x12083fa, 'movups XMMWORD PTR [rax],xmm14', 'movups XMMWORD PTR [rax],xmm15'),
                        (0x1208403, 'movups XMMWORD PTR [rax+0x10],xmm14', 'movups XMMWORD PTR [rax+0x10],xmm15')],
        'revert_committed': [(0x12083ad, 'je ', 'nop')],
        'skip_journal': [(0x120e3ab, 'call ', 'nop')],
        'snap_off_by_one': [(0x1206bf8, 'jg ', 'jge    1206ede')],
        'key_limb': [(0x127f4c6, 'bswap ', 'nop')],
    },
    'bor': {
        'revert_zero': [(0xab481a, 'movups XMMWORD PTR [rax],xmm14', 'movups XMMWORD PTR [rax],xmm15'),
                        (0xab4823, 'movups XMMWORD PTR [rax+0x10],xmm14', 'movups XMMWORD PTR [rax+0x10],xmm15')],
        'revert_committed': [(0xab47cd, 'je ', 'nop')],
        'skip_journal': [(0xac9f4b, 'call ', 'nop')],
        'snap_off_by_one': [(0xab3364, 'jg ', 'jge    ab342e')],
        'key_limb': [(0xb5097e, 'bswap ', 'nop')],
    },
    'borpar': {
        'revert_zero': [(0xabe0b4, 'movups XMMWORD PTR [rax],xmm14', 'movups XMMWORD PTR [rax],xmm15'),
                        (0xabe0bd, 'movups XMMWORD PTR [rax+0x10],xmm14', 'movups XMMWORD PTR [rax+0x10],xmm15')],
        'revert_committed': [(0xabe057, 'je ', 'jmp    abe0c7')],
        'skip_journal': [(0xabb370, 'call ', 'nop')],
        'snap_off_by_one': [(0xabd20d, 'jl ', 'jle    abd225')],
        'key_limb': [(0xb5097e, 'bswap ', 'nop')],
    },
    'avax': {
        'revert_zero': [(0x1477ed1, 'movups XMMWORD PTR [rax],xmm14', 'movups XMMWORD PTR [rax],xmm15'),
                        (0x1477eda, 'movups XMMWORD PTR [rax+0x10],xmm14', 'movups XMMWORD PTR [rax+0x10],xmm15')],
        'skip_journal': [(0x14618a2, 'mov    QWORD PTR [rcx+0x8],rbx', 'nop')],
        'snap_off_by_one': [(0x145ea24, 'jg ', 'jge    145eaee')],
        'key_limb': [(0x14b1b83, 'bswap ', 'nop')],
        'transform_off': [(0x152f8fa, 'and    edx,0xfffffffe', 'nop')],
    },
}


def patcher(sites, log):
    def p(text):
        for a, old, new in sites:
            m = re.search(r'^( *%x:\s+)(.*)$' % a, text, re.M)
            assert m, hex(a)
            ins = m.group(2)
            assert ins.startswith(old) or old in ins, (hex(a), ins, old)
            text = text[:m.start(2)] + new + text[m.end(2):]
            log.append({'address': hex(a), 'replaced': ins.strip(), 'with': new})
        return text
    return p


def main():
    tgt, n, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    summary = []
    for f, sites in SITES[tgt].items():
        log = []
        out = os.path.join(outdir, '%s-amd64-%s.json' % (tgt, f))
        if tgt == 'nitro':
            import stnitro
            r = stnitro.run('amd64', n, out, text_patch=patcher(sites, log), fault=f)
        else:
            import stgo2
            name = tgt + '-amd64'
            fnr = stgo2.run_par if tgt == 'borpar' else stgo2.run_avax if tgt == 'avax' else stgo2.run
            r = fnr(name, n, out, text_patch=patcher(sites, log), fault=f)
        summary.append({'target': tgt + '-amd64', 'fault': f, 'site': log, 'sequences': r['sequences'],
                        'mismatchSeqs': len(r['mismatches']), 'errorSeqs': len(r['errors']),
                        'firstMismatch': (r['mismatches'] or [None])[0], 'firstError': (r['errors'] or [None])[0]})
        print(summary[-1]['target'], f, 'mismatchSeqs', summary[-1]['mismatchSeqs'], 'errorSeqs', summary[-1]['errorSeqs'])
    json.dump(summary, open(os.path.join(outdir, '%s-summary.json' % tgt), 'w'), indent=1)


if __name__ == '__main__':
    main()
