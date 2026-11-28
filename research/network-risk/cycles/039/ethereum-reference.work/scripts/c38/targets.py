"""Cycle 39 copy: adds erigon-arm64 (erigon v3.8.2 linux arm64 release, read from the scratch download dir). Shipped binaries of cycle 38 (theme-ethereum-client-binaries-lift): geth v1.17.10 and erigon v3.8.2. Read as data only, never executed or loaded.
TARGET names <client>-<arch>. layout is the core/vm Stack layout read from opLt and opMulmod of each build."""
import os
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '038', 'theme-ethereum-client-binaries-lift.work')
T = {
    'geth-amd64': dict(bin='dl/geth/geth-linux-amd64-1.17.10-1df30b18/geth', vm='github.com/ethereum/go-ethereum/core/vm.', layout='arena', chain=1),
    'geth-arm64': dict(bin='dl/geth/geth-linux-arm64-1.17.10-1df30b18/geth', vm='github.com/ethereum/go-ethereum/core/vm.', layout='arena', chain=1),
    'erigon-arm64': dict(bin='/tmp/claude-0/-home-user-v4-core/0b315df9-4a6b-5032-a881-24bad3c79fc5/scratchpad/dl/erigon-a64/x/erigon_v3.8.2_linux_arm64/erigon', vm='github.com/erigontech/erigon/execution/vm.', layout='erigon', chain=1,
                         fns='/tmp/claude-0/-home-user-v4-core/0b315df9-4a6b-5032-a881-24bad3c79fc5/scratchpad/dl/erigon-a64/all-erigon-arm64.txt'),
    'erigon-amd64': dict(bin='dl/erigon/erigon_v3.8.2_linux_amd64/erigon', vm='github.com/erigontech/erigon/execution/vm.', layout='erigon', chain=1),
}


def get(name):
    t = dict(T[name])
    t['arch'] = name.split('-')[1]
    t['bin'] = os.path.join(W, t['bin'])
    t['fns'] = t.get('fns') or os.path.join(W, 'dl/build/all-%s.txt' % name)
    return t


def model(name, **kw):
    import goshim as G, models
    t = get(name)
    G.VM = t['vm']
    return models.Model(t['arch'], t['bin'], t['fns'], layout=t['layout'], **kw)
