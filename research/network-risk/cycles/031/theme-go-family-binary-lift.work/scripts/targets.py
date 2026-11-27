"""Shipped binaries of cycle 31 (theme-go-family-binary-lift). Read as data only, never executed or loaded.
TARGET names <client>-<arch>. layout is the core/vm Stack layout read from opLt and opMulmod of each build."""
import os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = {
    'bsc-amd64': dict(bin='dl/bsc/geth_linux', vm='github.com/ethereum/go-ethereum/core/vm.', layout='arena', chain=56),
    'bsc-arm64': dict(bin='dl/bsc/geth-linux-arm64', vm='github.com/ethereum/go-ethereum/core/vm.', layout='arena', chain=56),
    'bor-amd64': dict(bin='dl/bor/x-amd64/usr/bin/bor', vm='github.com/ethereum/go-ethereum/core/vm.', layout='fixed', chain=137),
    'bor-arm64': dict(bin='dl/bor/x-arm64/usr/bin/bor', vm='github.com/ethereum/go-ethereum/core/vm.', layout='fixed', chain=137),
    'avax-amd64': dict(bin='dl/avax/x-amd64/avalanchego-v1.15.3/avalanchego', vm='github.com/ava-labs/libevm/core/vm.', layout='slice', chain=43114),
    'avax-arm64': dict(bin='dl/avax/x-arm64/avalanchego-v1.15.3/avalanchego', vm='github.com/ava-labs/libevm/core/vm.', layout='slice', chain=43114),
}


def get(name):
    t = dict(T[name])
    t['arch'] = name.split('-')[1]
    t['bin'] = os.path.join(W, t['bin'])
    t['fns'] = os.path.join(W, 'dl/build/all-%s.txt' % name)
    return t


def model(name, **kw):
    import goshim as G, models
    t = get(name)
    G.VM = t['vm']
    return models.Model(t['arch'], t['bin'], t['fns'], layout=t['layout'], **kw)
