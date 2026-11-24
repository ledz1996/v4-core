// Build src/PoolManager.sol with the settings of foundry.toml, using the solc-js package of the pinned version.
// Usage: node compile.js <path to node_modules/solc> <repo root> <out.json>
const fs = require('fs'), path = require('path')
const [solcPath, root, out] = process.argv.slice(2)
const solc = require(solcPath)
const remap = fs.readFileSync(path.join(root, 'remappings.txt'), 'utf8').split('\n').filter(Boolean).map(l => l.split('='))
function resolve(p) {
  for (const [from, to] of remap) if (p.startsWith(from)) return path.join(root, to, p.slice(from.length))
  return path.join(root, p)
}
const input = {
  language: 'Solidity',
  sources: { 'src/PoolManager.sol': { content: fs.readFileSync(path.join(root, 'src/PoolManager.sol'), 'utf8') } },
  settings: {
    optimizer: { enabled: true, runs: 44444444 }, viaIR: true, evmVersion: 'cancun',
    metadata: { bytecodeHash: 'none' },
    outputSelection: { 'src/PoolManager.sol': { PoolManager: ['evm.bytecode.object', 'evm.deployedBytecode.object', 'evm.deployedBytecode.immutableReferences', 'evm.methodIdentifiers'] } },
  },
}
const t0 = Date.now()
const res = JSON.parse(solc.compile(JSON.stringify(input), { import: p => { try { return { contents: fs.readFileSync(resolve(p), 'utf8') } } catch (e) { return { error: String(e) } } } }))
const errs = (res.errors || []).filter(e => e.severity === 'error')
if (errs.length) { console.error(errs.map(e => e.formattedMessage).join('\n')); process.exit(1) }
const c = res.contracts['src/PoolManager.sol'].PoolManager
fs.writeFileSync(out, JSON.stringify({ compiler: solc.version(), settings: input.settings, creation: c.evm.bytecode.object, runtime: c.evm.deployedBytecode.object,
  immutableReferences: c.evm.deployedBytecode.immutableReferences, methodIdentifiers: c.evm.methodIdentifiers }, null, 1))
console.log('compiled in', Math.round((Date.now() - t0) / 1000), 's; runtime', c.evm.deployedBytecode.object.length / 2, 'bytes; creation', c.evm.bytecode.object.length / 2, 'bytes; warnings', (res.errors || []).length)
