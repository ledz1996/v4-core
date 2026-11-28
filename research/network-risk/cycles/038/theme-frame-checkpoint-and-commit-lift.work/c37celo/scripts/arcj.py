"""Cycle 37: Arc profile for the celoj.py machine. The published arc-execution v0.8.6 image's arc-node-execution binary
(sha256 97ad5a38...0b84f, reth/v2.2.0-508cbdf, revm-context 16.0.1, revm-context-interface 17.0.1, revm-interpreter
35.0.1, jemalloc linked in, no symbols). Addresses were found by reading the binary as data (objdump text, relocations,
byte search). Nothing is executed or loaded.
"""
import celoj
from celoj import Machine, Stop, M, M64

ARC_BIN = '/home/user/v4-core/research/network-risk/cycles/035/stablecoin-l1.work/dl/images/img-0.8.6/usr/local/bin/arc-node-execution'
ARC_FDE = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/build/arc086.fde'

PROFILES = {
    'arc': dict(
        bin=ARC_BIN, fde=ARC_FDE, img='img-arc086.bin',
        got={0x5149510: 'memcpy', 0x5149590: 'memset', 0x51496d8: 'memmove', 0x5149a18: 'bcmp', 0x5149b98: 'memcmp',
             0x514cc80: 'malloc', 0x5153f00: 'free', 0x515a0c8: 'realloc'},
        # jemalloc linked in: targets of the RELATIVE slots finish_grow 0x26c2a20 calls (0x5149550 malloc, 0x51495d0
        # mallocx, 0x5149560 realloc, 0x51495c8 rallocx) and the one checkpoint_revert frees through (0x5149610 sdallocx)
        alloc_fns={'malloc': 0x41c9ff0, 'mallocx': 0x41cad50, 'realloc': 0x41cc120, 'rallocx': 0x41cc110, 'sdallocx': 0x41cdc70},
        # interpreter halt tails the handlers jump or call to
        halts=[0x1f54700, 0x1f546f0, 0x1f54710, 0x1f548d0, 0x1f54530], halt_slots=[], panics=[],
        seed_word=0x6184af0, seed_once=None, empty_group=None,      # foldhash global seed (RELATIVE slot 0x5149a68)
        layout=dict(target=0x80, gas=0x190, static=0x1b0, spec=0x1b1, gasparams=0x258, J=0x2d0, err=0x2a0, err_none=0,
                    db=0x400, txid=0x120),
        acct_stride=0xb8, acct_off=0x18, acct_storage=0x68, acct_status=0x98, acct_txid=0x90, slot_stride=0x70,
        families={
            # table 0x4f62ef0 (the table cycle 36 ran): SLOAD 0x1f69040 -> 0x1a06980 -> journal sload 0x22aeb50 ->
            # State storage 0x22c07c0 (stubbed); SSTORE 0x1f6bcf0 -> 0x1b26a40; TSTORE -> JournalInner::tstore 0x1a07570
            'A': dict(table=0x4f62ef0, SLOAD=0x1f69040, SSTORE=0x1f6bcf0, TLOAD=0x1f6ad00, TSTORE=0x1f6f4a0,
                      revert=0x19ffce0, checkpoint=0x2b9c3f0, commit=0x2b9d360, db=0x22c07c0, db_ok=0x2d, db_self_direct=True,
                      sstore_hooks=[0x1f6be5f, 0x1f6bf0e], sstore_out=0x80),
        }),
}
celoj.PROFILES.update(PROFILES)
PROFILES = celoj.PROFILES
