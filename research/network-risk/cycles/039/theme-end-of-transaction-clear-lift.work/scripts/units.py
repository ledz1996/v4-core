"""Cycle 39: the end-of-transaction routines of the seven builds (from txpanic.py / txscan_loose.py, kinds read from
the disassembly: discard drains and reverts the journal, commit zeroes its length)."""
UNITS = [
    ('opreth2100', 'discard', 0x2d06750), ('opreth2100', 'commit', 0x2d08b50), ('opreth2100', 'discard', 0x44f07d0), ('opreth2100', 'commit', 0x44f0bd0),
    ('opreth281', 'discard', 0x2eada10), ('opreth281', 'commit', 0x2eafe10), ('opreth281', 'discard', 0x4682200), ('opreth281', 'commit', 0x4682600),
    ('base156', 'discard', 0x35bdab0), ('base156', 'commit', 0x35c17f0), ('base156', 'commit', 0x64313d0), ('base156', 'discard', 0x6432720),
    ('base156', 'commit', 0x722d180), ('base156', 'discard', 0x722d500),
    ('wc282', 'discard', 0x2daf270), ('wc282', 'commit', 0x2db17b0), ('wc282', 'discard', 0x46d9040), ('wc282', 'commit', 0x46d9440),
    ('conduit251', 'discard', 0x1e34850), ('conduit251', 'commit', 0x1e37820), ('conduit251', 'discard', 0x3b85ab0), ('conduit251', 'commit', 0x3b85eb0),
    ('xlayer0073', 'discard', 0x383ba70), ('xlayer0073', 'commit', 0x3840de0), ('xlayer0073', 'discard', 0x509e360), ('xlayer0073', 'commit', 0x50a0a20),
    ('arc086', 'discard', 0x19f9150), ('arc086', 'commit', 0x1a07a80),
    ('celo1010', 'finalize', 0x1d66c80),   # Task 3 (L-1350)
]
