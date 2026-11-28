"""Cycle 39 copy (theme-end-of-transaction-clear-lift), unchanged except this line. Cycle 37: X Layer profile for the celoj.py machine. The published xlayer-reth v0.0.7.3-rc.1 image's op-reth binary
(reth/v2.3.0-f60420a, xlayer/v0.0.7, revm-context 18.0.3, revm-context-interface 19.0.3, revm-interpreter 37.0.3,
jemalloc linked in, no symbols). All addresses below were found by reading the binary as data (objdump text,
relocations, byte search; see the research file for the chain from each handler). Nothing is executed or loaded.
"""
import celoj
from celoj import Machine, Stop, M, M64

XL_BIN = '/home/user/v4-core/research/network-risk/cycles/035/theme-reth-keccak-asm-image-lift.work/dl/xlayer-rc1/x/usr/local/bin/op-reth'
XL_FDE = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/build/xlayer.fde'

PROFILES = {
    'xlayer': dict(
        bin=XL_BIN, fde=XL_FDE, img='img-xlayer.bin', status_return=True,
        # memcpy, memset, memmove, bcmp, memcmp are imported (GLOB_DAT); the allocator is jemalloc linked in:
        # malloc 0x6b1f460 (exported), and the targets of the RELATIVE slots finish_grow 0x3c74470 calls
        # (0x71c1710 mallocx, 0x71c1708 realloc, 0x71c1700 rallocx) and checkpoint_revert calls (0x71c17a8 sdallocx)
        got={0x71c16e0: 'memcpy', 0x71c1730: 'memset', 0x71c1878: 'memmove', 0x71c1b60: 'bcmp', 0x71c1c80: 'memcmp'},
        alloc_fns={'malloc': 0x6b1f460, 'mallocx': 0x6b22510, 'realloc': 0x6b238e0, 'rallocx': 0x6b238d0,
                   'sdallocx': 0x6b26a20, 'free': 0x6b219d0, 'calloc': 0x6b20210},
        halts=[], halt_slots=[], panics=[],
        seed_word=0x8200a18, seed_once=None, empty_group=None,      # foldhash global seed (RELATIVE slot 0x71c1b50)
        layout=dict(target=0x80, gas=0x190, static=0x1b0, spec=0x1b1, gasparams=0x5c0, J=0x420, err=0x3e0, err_none=0,
                    db=0x548, txid=0x120, txid_size=4, jspec=0x126),
        acct_stride=0xa8, acct_off=0x18, acct_storage=0x0, acct_status=0x8c, acct_txid=0x88, slot_stride=0x68,
        families={
            # table 0x718b9e0 (the table cycle 36 ran): SLOAD 0x5fd82d0 -> sload_skip_cold_load 0x519e2f0 ->
            # sload_concrete_error 0x38877c0 (slot 0x71d0f20) -> database storage 0x3c37d30 (account_id none) or
            # 0x3c35500 (account_id some; never reached here, a Stop if it is)
            'A': dict(table=0x718b9e0, SLOAD=0x5fd82d0, SSTORE=0x5fda000, TLOAD=0x5fd9a80, TSTORE=0x5fe5470,
                      revert=0x3ca62f0, checkpoint=0x3cca520, commit=0x3ccac20, db=0x3c37d30, db_other=[0x3c35500],
                      db_ok=2, db_ok_size=8, sstore_hooks=None, sstore_out=None),
            # the same table with the second checkpoint_revert copy (0x509ef80, reached from the EvmInternals vtable
            # at 0x7150498) in place of 0x3ca62f0
            'A2': dict(table=0x718b9e0, SLOAD=0x5fd82d0, SSTORE=0x5fda000, TLOAD=0x5fd9a80, TSTORE=0x5fe5470,
                       revert=0x509ef80, checkpoint=0x520aaf0, commit=0x520c130, db=0x3c37d30, db_other=[0x3c35500],
                       db_ok=2, db_ok_size=8, sstore_hooks=None, sstore_out=None),
        }),
}
celoj.PROFILES.update(PROFILES)
PROFILES = celoj.PROFILES
