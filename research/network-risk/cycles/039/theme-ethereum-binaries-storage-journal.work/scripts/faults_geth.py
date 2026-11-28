"""Planted faults for the geth v1.17.10 amd64 model (pc -> replacement instruction(s), ';' separated).
Addresses read from the disassembly of the release binary (dis/geth/*.s)."""
FAULTS = {
    # (*transientStorageChange).revert (0x9de1e0, the pointer-receiver wrapper the journal's itab calls; it inlines
    # journal.go:588 and transientStorage.Set): the restored value is zero instead of prevalue
    'ts-revert-zero': {0x9de39d: 'pxor xmm14,xmm14', 0x9de3a5: 'pxor xmm14,xmm14'},
    # storageChange.revert (0x9b6a20, journal.go:571): setState gets origvalue as the value (restores the committed value)
    'st-revert-committed': {0x9b6a88: 'lea rcx,[rsp+0xec]'},
    # (*StateDB).SetTransientState (0x9c1f80, statedb.go:558): the call to journal.append is skipped
    'ts-skip-journal': {0x9c21e0: 'nop'},
    # (*StateDB).Snapshot with journal.snapshot inlined (0x9c4280, journal.go:214): journalIndex = len(entries)+1
    'snap-index-plus1': {0x9c42b4: 'mov r9,QWORD PTR [rdx+0x8]; inc r9'},
}
